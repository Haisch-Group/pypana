"""The BinAxis, the diameter axis shared by all distributions of one scan.

The grid is defined by its ``n + 1`` bin boundaries; the midpoints and bin widths are derived from them.
All diameters are in meters, see :class:`~pypana.data.defs.quantity.Quantity`.
"""
from functools import cached_property
from typing import Literal, Self

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from pypana.data.defs import FloatArray
from pypana.utils.debug import Debuggable


class BinAxis(BaseModel, Debuggable):
    """A logarithmic particle-size axis, defined by its boundaries."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        ignored_types=(cached_property,),
        populate_by_name=True,
        frozen=True,  # decision for now, as False would allow changing the boundaries for all related SizeDistributions
    )

    bin_boundaries: FloatArray = Field(
        description="The n+1 bin boundaries in meters, strictly increasing.",
    )

    raw_d_p: FloatArray | None = Field(
        default=None,
        alias="d_p",
        description="Reported midpoint diameter per bin [m]. "
                    "If omitted, it is derived from the boundaries via `midpoint`.",
    )

    midpoint: Literal["geometric", "arithmetic"] = Field(
        default="geometric",
        description="How to derive the midpoint when d_p is not supplied. Ignored if d_p is given."
    )
    diameter_type: Literal["mobility", "optical", "aerodynamic"] = Field(
        description="Physical basis of the measured diameter. Gates whether cross-quantity "
                    "derivation (e.g. dV from dN) is physically valid. Unused for now",
    )

    @field_validator("bin_boundaries")
    @classmethod
    def _check_boundaries(cls, value: FloatArray) -> FloatArray:
        """Ensures that the boundaries form a valid, log axis.

        Args:
            value: The input bin_boundaries from constructing the BinAxis.

        Returns:
            The input, if valid.

        Raises:
            ValueError: If the input is invalid.

        Note:
            Explicit check, since FloatArray is a pypana type and no runtime checks are made by pydantic.
            It does not enforce constant log-size bins (constant channels per decade).
        """
        if value.ndim != 1:
            raise ValueError("bin_boundaries must be 1D.")

        if value.size < 2:
            raise ValueError("bin_boundaries needs at least 2 entries (one bin).")

        if not np.all(value > 0):
            raise ValueError("bin_boundaries must be positive.")

        if not np.all(np.diff(value) > 0):
            raise ValueError("bin_boundaries must be strictly increasing.")

        return value

    @model_validator(mode="after")
    def _check_d_p(self) -> Self:
        """Enforce stated conditions on d_p."""
        if self.raw_d_p is None:
            return self

        if self.raw_d_p.shape != (self.n_bins,):
            raise ValueError("Wrong d_p shape.")

        if not np.all((self.d_lower <= self.raw_d_p) & (self.raw_d_p <= self.d_upper)):
            raise ValueError("At least one d_p lies outside its corresponding boundaries.")

        return self

    @cached_property
    def n_bins(self) -> int:
        """The number of bins in the axis."""
        return self.bin_boundaries.size - 1

    @cached_property
    def d_lower(self) -> FloatArray:
        """Lower boundary of each bin in [m]."""
        return self.bin_boundaries[:-1]

    @cached_property
    def d_upper(self) -> FloatArray:
        """Upper boundary of each bin in [m]."""
        return self.bin_boundaries[1:]

    @cached_property
    def d_p(self) -> FloatArray:
        """Midpoint diameter of each bin [m].

        Either supplied from the instrument, otherwise derived from the boundaries.
        """
        if self.raw_d_p is not None:
            return self.raw_d_p

        if self.midpoint == "geometric":
            return np.sqrt(self.d_lower * self.d_upper)

        return (self.d_lower + self.d_upper) / 2

    @cached_property
    def delta_d_p(self) -> FloatArray:
        """Absolute bin width Δd_p = d_upper − d_lower [m]."""
        return self.d_upper - self.d_lower

    @cached_property
    def delta_log_d_p(self) -> FloatArray:
        """Logarithmic bin width Δlog₁₀(d_p) = log₁₀(d_upper / d_lower)."""
        return np.log10(self.d_upper / self.d_lower)
