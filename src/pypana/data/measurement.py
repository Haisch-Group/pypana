"""The Measurement class.

This module provides a class to store a single scan of any supported aerosol measurement instrument.
This data can then be used for further unified analysis.
"""

from collections.abc import Hashable
from datetime import datetime
from functools import cached_property
from typing import Any, ClassVar, Self

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from pypana.utils.debug import Debuggable

FloatArray = npt.NDArray[np.floating]


class Measurement(BaseModel, Debuggable):
    """A single measurement or scan of an instrument with all its data."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        ignored_types=(cached_property,),
        populate_by_name=True,
        validate_assignment=True,
    )

    scan_nr: int = Field(description="Scan number as reported by the instrument")
    time: datetime = Field(description="Start time of the measurement")
    d_p: FloatArray = Field(
        description="Midpoint particle diameter / Channel center per bin [m]"
    )
    delta_d_p: FloatArray = Field(
        description="Absolute bin width Δd_p = d_upper − d_lower [m]"
    )
    delta_log_d_p: FloatArray = Field(
        description="Logarithmic bin width Δlog(d_p) = log10(d_upper / d_lower)"
    )
    bin_boundaries: FloatArray = Field(description="The n+1 bin boundaries")
    raw_delta_n: FloatArray | None = Field(
        default=None,
        alias="delta_n",
        description="Number concentration per bin ΔN[1/cm³]",
    )
    raw_delta_n_dlog_dp: FloatArray | None = Field(
        default=None,
        alias="delta_n_dlog_dp",
        description="Normalized number size distribution dN/dlog(d_p) [1/cm³]",
    )
    raw_median: float | None = Field(
        default=None,
        alias="median",
        description="Median size [m]",
    )
    raw_mean: float | None = Field(
        default=None,
        alias="mean",
        description="Mean size [m]",
    )
    raw_geo_mean: float | None = Field(
        default=None,
        alias="geo_mean",
        description="Geometric Mean size [m]",
    )
    raw_mode: float | None = Field(
        default=None,
        alias="mode",
        description="Mode [m]",
    )
    raw_geo_std_dev: float | None = Field(
        default=None,
        alias="geo_std_dev",
        description="Geometric Standard Deviation [m]",
    )

    other: dict[Hashable, Any] | None = Field(
        default_factory=dict,
        description="Other measurement data that is currently not directly supported in other fields.",
    )

    _action_log: list[str] = PrivateAttr(default_factory=list)

    _PAIRS: ClassVar[dict[str, str]] = {
        "raw_delta_n": "raw_delta_n_dlog_dp",
        "raw_delta_n_dlog_dp": "raw_delta_n",
    }

    # public names that map onto a raw_* field. Assigning to
    # one of these writes the source-of-truth field instead of the read-only cached_property.
    _WRITABLE_ALIASES: ClassVar[dict[str, str]] = {
        "delta_n": "raw_delta_n",
        "delta_n_dlog_dp": "raw_delta_n_dlog_dp",
    }

    def __setattr__(self, name: str, value: object) -> None:
        name = self._WRITABLE_ALIASES.get(name, name)
        super().__setattr__(name, value)
        self._action_log.append(f"set {name} to {value}")

        paired = self._PAIRS.get(name, None)
        if paired is not None and value is not None:
            super().__setattr__(paired, None)

        self._invalidate_caches()

    def _invalidate_caches(self) -> None:
        """Invalidates values for cached properties."""
        for key in list(self.__dict__):
            if key not in type(self).model_fields:
                self.__dict__.pop(key)
                self._action_log.append(f"invalidated {key}")

    @model_validator(mode="after")
    def check_concentration_provided(self) -> "Measurement":
        """Checks that at least one type of number size distribution was supplied in the constructor."""
        if self.raw_delta_n is None and self.raw_delta_n_dlog_dp is None:
            raise ValueError("At least one of delta_n")

        return self

    def summary(self) -> dict[str, object]:
        """Summary of this measurement's key derived quantities.

        Returns:
            A dict overview.
        """
        return {
            "scan_nr": self.scan_nr,
            "n_bins": len(self.d_p),
            "d_p_min": float(self.d_p.min()),
            "d_p_max": float(self.d_p.max()),
            "n_total": self.n_total,
            "geo_mean": self.geo_mean,
            "geo_std_dev": self.geo_std_dev,
            "mean": self.mean,
            "median": self.median,
            "mode": self.mode,
            "other": f"[{', '.join(f'{k}: {v}' for k, v in (self.other or {}).items())}]",
        }

    @cached_property
    def n_total(self) -> float:
        """Total number concentration, integrated over all bins [1/cm³]."""
        return float(self.delta_n.sum())

    @cached_property
    def delta_n(self) -> FloatArray:
        """Provides access to the delta_n property, lazily calculated if not supplied in constructor."""
        if self.raw_delta_n is not None:
            return self.raw_delta_n

        assert self.raw_delta_n_dlog_dp is not None
        return (self.raw_delta_n_dlog_dp * self.delta_log_d_p).astype(float)

    @cached_property
    def delta_n_dlog_dp(self) -> FloatArray:
        """Provides access to the delta_n_dlog_dp property, lazily calculated if not supplied in constructor."""
        if self.raw_delta_n_dlog_dp is not None:
            return self.raw_delta_n_dlog_dp

        assert self.raw_delta_n is not None
        return (self.raw_delta_n / self.delta_log_d_p).astype(float)

    @cached_property
    def geo_mean(self) -> float:
        """Geometric mean diameter."""
        if self.n_total == 0:
            return 0.0

        return float(
            10 ** (np.nansum(np.log10(self.d_p) * self.delta_n) / self.n_total)
        )

    @cached_property
    def geo_std_dev(self) -> float:
        """Geometric standard deviation."""
        if self.n_total == 0:
            return 1.0

        log_dg = np.log10(self.geo_mean)
        var = (
            np.nansum(self.delta_n * (np.log10(self.d_p) - log_dg) ** 2) / self.n_total
        )

        return float(10 ** np.sqrt(var))

    @cached_property
    def mean(self) -> float:
        """Mean diameter."""
        if self.n_total == 0:
            return 0.0

        return float(np.nansum(self.d_p * self.delta_n) / self.n_total)

    @cached_property
    def median(self) -> float:
        """Median diameter."""
        if self.n_total == 0:
            return 0.0

        cum = np.cumsum(self.delta_n)
        return float(np.interp(0.5 * self.n_total, cum, self.d_p))

    @cached_property
    def mode(self) -> float:
        """The mode of the distribution."""
        return float(self.d_p[int(np.argmax(self.delta_n_dlog_dp))])

    def cut(self, d: tuple[float, float]) -> Self:
        """Sets bins with midpoint diameter outside the lower and higher bound to zero.

        Args:
            d (tuple[float, float]): The boundaries in (lower, higher)

        Returns:
            Itself, after applying the changes


        Note:
            This operation is inplace.
        """
        d_lo, d_hi = d

        if d_lo >= d_hi:
            raise ValueError(f"d_lo ({d_lo}) must be less than d_hi ({d_hi})")

        outside = (self.d_p < d_lo) | (self.d_p > d_hi)
        if self.raw_delta_n is not None:
            new = self.raw_delta_n.copy()
            new[outside] = 0.0
            self.raw_delta_n = new
        elif self.raw_delta_n_dlog_dp is not None:  # pragma: no branch
            new = self.raw_delta_n_dlog_dp.copy()
            new[outside] = 0.0
            self.raw_delta_n_dlog_dp = new

        return self
