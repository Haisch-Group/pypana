"""The Measurement class.

This module provides a class to stores a scan of any supported aerosol measurement instrument.
This data can then be used for further unified analysis.
"""

from collections.abc import Hashable
from datetime import datetime
from typing import Any, Self, overload

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from pypana.data.bin_axis import BinAxis, DiameterTypes
from pypana.data.defs import DataType, DataTypeLike, FloatArray, Normalization, Quantity
from pypana.data.defs.data_type_str import DataTypeStr
from pypana.data.size_distribution import SizeDistribution
from pypana.data.time_series import TimeSeries
from pypana.utils.debug import Debuggable


class Measurement(BaseModel, Debuggable):
    """A single scan of an instrument: one shared BinAxis and the distributions measured on it."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        validate_assignment=True,
    )

    scan_nr: int = Field(description="Scan number as reported by the instrument")
    time: datetime = Field(description="Start time of the measurement")
    axis: BinAxis | None = Field(
        default=None,
        frozen=True,
        description="The diameter axis shared by all size distributions; None for time-series-only scans.",
    )
    distributions: dict[Quantity, SizeDistribution] = Field(
        default_factory=dict,
        description="Size distributions, keyed by their quantity.",
    )
    series: dict[Quantity, TimeSeries] = Field(
        default_factory=dict,
        description="Time series, keyed by their quantity.",
    )

    other: dict[Hashable, Any] = Field(
        default_factory=dict,
        description="Other measurement data that is currently not directly supported in other fields.",
    )

    @model_validator(mode="after")
    def _check_payloads(self) -> Self:
        """Checks payloads are present, correctly keyed, and that size distributions share the axis."""
        if not self.distributions and not self.series:
            raise ValueError(
                "A measurement needs at least one size distribution or time series."
            )

        if self.distributions and self.axis is None:
            raise ValueError("Size distributions require an `axis`.")

        for quantity, dist in self.distributions.items():
            if dist.quantity is not quantity:
                raise ValueError(
                    f"Distribution keyed {quantity!r} has quantity {dist.quantity!r}."
                )

            if dist.axis is not self.axis:
                raise ValueError(
                    "All distributions must share the measurement's axis (the same BinAxis object)."
                )

        for quantity, ts in self.series.items():
            if ts.quantity is not quantity:
                raise ValueError(
                    f"Time series keyed {quantity!r} has quantity {ts.quantity!r}."
                )

        return self

    @overload
    def __getitem__(self, key: Quantity) -> Self: ...

    @overload
    def __getitem__(self, key: DataType) -> FloatArray: ...

    @overload
    def __getitem__(self, key: DataTypeStr) -> FloatArray: ...

    @overload
    def __getitem__(self, key: str) -> FloatArray | Self: ...

    def __getitem__(self, key: DataTypeLike | str) -> "FloatArray | Measurement":
        """Filter by quantity or read binned values.

        Args:
            key: A bare quantity ("N", ``Quantity.NUMBER``) filters to that quantity's payloads
                (distribution and/or series) and returns a Measurement. A data type ("dN",
                "dV/dlogdp", ``DataType``) returns the binned value array (size distributions only).

        Raises:
            ValueError: If a data-type string is unknown.
            KeyError: If a data type is requested on a time-series-only measurement.
            NotImplementedError: If the quantity is not stored and would need deriving.
        """
        quantity: Quantity | None

        try:
            quantity = Quantity(str(key))
        except ValueError:
            quantity = None

        if quantity is not None:
            distributions: dict[Quantity, SizeDistribution] = {}
            series: dict[Quantity, TimeSeries] = {}

            if quantity in self.distributions:
                distributions[quantity] = self.distributions[quantity]

            if quantity in self.series:
                series[quantity] = self.series[quantity]

            if not distributions and not series:
                distributions[quantity] = self._derive(
                    quantity
                )  # raises NotImplementedError for now

            return type(self)(
                scan_nr=self.scan_nr,
                time=self.time,
                axis=self.axis if distributions else None,
                distributions=distributions,
                series=series,
                other=self.other,
            )

        requested = DataType.parse(key)
        return self._distribution(requested.quantity)[requested]

    def __contains__(self, key: object) -> bool:
        """Whether a quantity is present as a distribution or a series."""
        return key in self.distributions or key in self.series

    def _distribution(self, quantity: Quantity) -> SizeDistribution:
        """The stored distribution for a quantity.

        Args:
            quantity: The quantity to resolve.

        Raises:
            KeyError: If this measurement has no size distributions at all (time-series only).
            NotImplementedError: If the quantity would need deriving from another.
        """
        if not self.distributions:
            raise KeyError(
                "This measurement has no size distributions (it is time-series only); "
                "access its series via `m.series[quantity]`."
            )

        if quantity in self.distributions:
            return self.distributions[quantity]

        return self._derive(quantity)

    def _derive(self, quantity: Quantity) -> SizeDistribution:
        """Derive a quantity the instrument did not measure from one it did (not implemented).

        The home for cross-quantity derivation (e.g. dV from dN via the moment rule).
        The structure is in place; the math is intentionally not built yet.

        Args:
            quantity: The quantity that would have to be derived.

        Raises:
            NotImplementedError: Always, for now.
        """
        available = ", ".join(f"{q.full_name} ({q})" for q in self.distributions)

        raise NotImplementedError(
            f"Deriving the {quantity.full_name} distribution from another quantity is "
            f"not implemented yet. This measurement has: {available}."
        )

    @property
    def _sole(self) -> SizeDistribution | TimeSeries:
        """The single payload; errors if there isn't exactly one."""
        payloads: list[SizeDistribution | TimeSeries] = [
            *self.distributions.values(),
            *self.series.values(),
        ]

        if len(payloads) != 1:
            names = ", ".join(str(q) for q in (*self.distributions, *self.series))
            raise AttributeError(
                f"Ambiguous: this measurement holds {len(payloads)} payloads ({names})."
            )

        return payloads[0]

    def _grid(self) -> BinAxis:
        """The shared size axis, or error for time-series-only measurements."""
        if self.axis is None:
            raise AttributeError("This measurement is time-series only.")

        return self.axis

    @property
    def n_bins(self) -> int:
        """Number of bins on the shared axis."""
        return self._grid().n_bins

    @property
    def diameter_type(self) -> DiameterTypes:
        """Physical diameter basis of the shared axis."""
        return self._grid().diameter_type

    @property
    def delta_log_d_p(self) -> FloatArray:
        """Logarithmic bin width Δlog₁₀(d_p) (from the shared axis)."""
        return self._grid().delta_log_d_p

    @property
    def d_p(self) -> FloatArray:
        """Midpoint diameter of each bin [m] (from the shared axis)."""
        return self._grid().d_p

    @property
    def delta_d_p(self) -> FloatArray:
        """Absolute bin width Δd_p [m] (from the shared axis)."""
        return self._grid().delta_d_p

    @property
    def bin_boundaries(self) -> FloatArray:
        """The n+1 bin boundaries [m] (from the shared axis)."""
        return self._grid().bin_boundaries

    def cut(self, d: tuple[float, float]) -> Self:
        """Zeroes bins whose midpoint lies outside ``(lower, upper)``, in place, on every distribution.

        Args:
            d: The (lower, upper) diameter bounds [m].

        Returns:
            Itself, after cutting.
        """
        for dist in self.distributions.values():
            dist.cut(d)

        return self

    @property
    def quantities(self) -> tuple[Quantity, ...]:
        """The quantities stored in this measurement (distributions and series)."""
        return tuple(dict.fromkeys([*self.distributions, *self.series]))

    @property
    def total(self) -> float:
        """Total concentration of the sole size distribution.

        Only works when the measurement holds exactly one size distribution.
        """
        sole = self._sole
        if not isinstance(sole, SizeDistribution):
            raise AttributeError("`total` is only defined for a size distribution.")

        return sole.total

    @property
    def geo_mean(self) -> float:
        """Geometric mean diameter of the sole size distribution [m].

        Only works when the measurement holds exactly one size distribution.
        """
        sole = self._sole
        if not isinstance(sole, SizeDistribution):
            raise AttributeError("`geo_mean` is only defined for a size distribution.")

        return sole.geo_mean

    def summary(self) -> dict[str, object]:
        """Summary of this measurement and its distributions.

        Returns:
            A dict overview.
        """
        return {
            "scan_nr": self.scan_nr,
            "time": self.time,
            "n_bins": self.axis.n_bins if self.axis is not None else None,
            "distributions": {
                str(q): d.summary() for q, d in self.distributions.items()
            },
            "other": f"[{', '.join(f'{k}: {v}' for k, v in (self.other or {}).items())}]",
        }
