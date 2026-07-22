"""The SizeDistribution, it holds the data of the chosen :class:`~pypana.data.defs.quantity.Quantity`."""

from collections.abc import Callable
from functools import cached_property
from typing import ClassVar, Literal, Self

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from pypana.data.bin_axis import BinAxis
from pypana.data.defs import DataType, DataTypeLike, FloatArray, Normalization, Quantity
from pypana.utils.debug import Debuggable


class SizeDistribution(BaseModel, Debuggable):
    """One :class:`~pypana.data.defs.quantity.Quantity`'s value arrays."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        ignored_types=(cached_property,),
        populate_by_name=True,
        validate_assignment=True,
    )

    quantity: Quantity = Field(
        frozen=True,
        description="The interpretation of the stored values.",
    )
    axis: BinAxis = Field(
        description="The axis for this quantity. Cannot be changed after instantiation.",
        frozen=True,
    )
    raw_delta: FloatArray | None = Field(
        default=None,
        alias="delta",
        description="Δ per bin in the quantity's canonical unit (e.g. ΔN [1/cm³]).",
    )
    raw_delta_dlogdp: FloatArray | None = Field(
        default=None,
        alias="delta_dlogdp",
        description="Normalized dX/dlog₁₀(d_p); same unit as `delta`.",
    )
    provenance: Literal["measured", "derived"] = Field(
        default="measured",
        frozen=True,
        description="Whether this distribution was reported by the instrument or derived "
        "from another quantity (e.g. dV from dN). Normalization conversion "
        "(Δ ↔ Δ/dlogdp) does not count as derivation.",
    )  # unsupported now, for when conversions are implemented.

    _action_log: list[str] = PrivateAttr(default_factory=list)

    _PAIRS: ClassVar[dict[str, str]] = {
        "raw_delta": "raw_delta_dlogdp",
        "raw_delta_dlogdp": "raw_delta",
    }

    # public names that map onto a raw_* field. Assigning to
    # one of these writes the source-of-truth field instead of the read-only cached_property.
    _WRITABLE_ALIASES: ClassVar[dict[str, str]] = {
        "delta": "raw_delta",
        "delta_dlogdp": "raw_delta_dlogdp",
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
    def _check_values(self) -> Self:
        """Checks that at least one representation is present and fits the axis."""
        if self.raw_delta is None and self.raw_delta_dlogdp is None:
            raise ValueError(
                "At least one of `delta` or `delta_dlogdp` must be supplied."
            )

        for values in (self.raw_delta, self.raw_delta_dlogdp):
            if values is None:
                continue

            if values.ndim != 1:
                raise ValueError("Values must be 1D.")

            if values.size != self.axis.n_bins:
                raise ValueError(
                    f"Got {values.size} values but the axis has {self.axis.n_bins} bins."
                )

        return self

    def __getitem__(self, key: DataTypeLike) -> FloatArray:
        """Read this distribution's values in the requested representation.

        Args:
            key: A data type whose quantity matches this distribution. ``"dN"`` (per-bin)
                or ``"dN/dlogdp"`` (normalized). A bare quantity defaults to the per-bin form.

        Returns:
            The per-bin (``delta``) or normalized (``delta_dlogdp``) values.

        Raises:
            KeyError: If the requested quantity differs from this distribution's quantity.
        """
        requested = DataType.parse(key)

        if requested.quantity is not self.quantity:
            raise KeyError(
                f"This is a {self.quantity.full_name} distribution; "
                f"cannot read {requested.quantity.full_name} values from it."
            )

        if requested.normalization is Normalization.DLOG_DP:
            return self.delta_dlogdp

        return self.delta

    @cached_property
    def delta(self) -> FloatArray:
        """Concentration per bin, lazily converted if only the normalized form was supplied."""
        if self.raw_delta is not None:
            return self.raw_delta

        assert self.raw_delta_dlogdp is not None
        return (self.raw_delta_dlogdp * self.axis.delta_log_d_p).astype(float)

    @cached_property
    def delta_dlogdp(self) -> FloatArray:
        """Normalized distribution, lazily converted if only the per-bin form was supplied."""
        if self.raw_delta_dlogdp is not None:
            return self.raw_delta_dlogdp

        assert self.raw_delta is not None
        return (self.raw_delta / self.axis.delta_log_d_p).astype(float)

    @cached_property
    def total(self) -> float:
        """Total concentration, integrated over all bins, in the quantity's canonical unit."""
        return float(np.nansum(self.delta))

    @cached_property
    def geo_mean(self) -> float:
        """Geometric mean diameter, weighted by this quantity [m]."""
        if self.total == 0:
            return 0.0

        return float(
            10 ** (np.nansum(np.log10(self.axis.d_p) * self.delta) / self.total)
        )

    @cached_property
    def geo_std_dev(self) -> float:
        """Geometric standard deviation, weighted by this quantity."""
        if self.total == 0:
            return 1.0

        log_dg = np.log10(self.geo_mean)
        var = (
            np.nansum(self.delta * (np.log10(self.axis.d_p) - log_dg) ** 2) / self.total
        )

        return float(10 ** np.sqrt(var))

    @cached_property
    def mean(self) -> float:
        """Mean diameter, weighted by this quantity [m]."""
        if self.total == 0:
            return 0.0

        return float(np.nansum(self.axis.d_p * self.delta) / self.total)

    @cached_property
    def median(self) -> float:
        """Median diameter, weighted by this quantity [m]."""
        if self.total == 0:
            return 0.0

        cum = np.cumsum(self.delta)
        return float(np.interp(0.5 * self.total, cum, self.axis.d_p))

    @cached_property
    def mode(self) -> float:
        """Diameter of the maximum of the normalized distribution [m]."""
        return float(self.axis.d_p[int(np.argmax(self.delta_dlogdp))])

    def apply(self, func: Callable[[FloatArray], FloatArray]) -> Self:
        """Applies a function to the stored values, in place.

        The function is applied to the source-of-truth representation (whichever
        raw array is present); the other representation is re-derived from the result.

        Args:
            func: Maps the current values to new values of the same shape.

        Returns:
            Itself, after applying the changes.
        """
        if self.raw_delta is not None:
            self.raw_delta = func(self.raw_delta)
        elif self.raw_delta_dlogdp is not None:  # pragma: no branch
            self.raw_delta_dlogdp = func(self.raw_delta_dlogdp)

        return self

    def cut(self, d: tuple[float, float]) -> Self:
        """Sets bins with midpoint diameter outside the lower and higher bound to zero, in place.

        Args:
            d: The boundaries as (lower, higher) [m].

        Returns:
            Itself, after applying the changes.
        """
        d_lo, d_hi = d

        if d_lo >= d_hi:
            raise ValueError(f"d_lo ({d_lo}) must be less than d_hi ({d_hi})")

        outside = (self.axis.d_p < d_lo) | (self.axis.d_p > d_hi)

        def zero_outside(values: FloatArray) -> FloatArray:
            new = values.copy()
            new[outside] = 0.0
            return new

        return self.apply(zero_outside)

    def summary(self) -> dict[str, object]:
        """Summary of this distribution's key derived quantities.

        Returns:
            A dict overview.
        """
        return {
            "quantity": self.quantity.full_name,
            "provenance": self.provenance,
            "n_bins": self.axis.n_bins,
            "d_p_min": float(self.axis.d_p.min()),
            "d_p_max": float(self.axis.d_p.max()),
            "total": self.total,
            "geo_mean": self.geo_mean,
            "geo_std_dev": self.geo_std_dev,
            "mean": self.mean,
            "median": self.median,
            "mode": self.mode,
        }
