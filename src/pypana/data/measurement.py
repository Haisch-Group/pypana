"""The Measurement class.

This module provides a class to store a single scan of any supported aerosol measurement instrument.
This data can then be used for further unified analysis.
"""

from collections.abc import Hashable
from datetime import datetime
from functools import cached_property
from typing import Any

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, ConfigDict, Field, model_validator

FloatArray = npt.NDArray[np.floating[Any]]


class Measurement(BaseModel):
    """A single measurement or scan of an instrument with all its data."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        ignored_types=(cached_property,),
        populate_by_name=True,
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
    raw_median: np.floating[Any] | None = Field(
        default=None,
        alias="median",
        description="Median size [m]",
    )
    raw_mean: np.floating[Any] | None = Field(
        default=None,
        alias="mean",
        description="Mean size [m]",
    )
    raw_geo_mean: np.floating[Any] | None = Field(
        default=None,
        alias="geo_mean",
        description="Geometric Mean size [m]",
    )
    raw_mode: np.floating[Any] | None = Field(
        default=None,
        alias="mode",
        description="Mode [m]",
    )
    raw_geo_std_dev: np.floating[Any] | None = Field(
        default=None,
        alias="geo_std_dev",
        description="Geometric Standard Deviation [m]",
    )

    other: dict[Hashable, Any] | None = Field(
        default_factory=dict,
        description="Other measurement data that is currently not directly supported in other fields.",
    )

    @model_validator(mode="after")
    def check_concentration_provided(self) -> "Measurement":
        """Checks that at least one type of number size distribution was supplied in the constructor."""
        if self.raw_delta_n is None and self.raw_delta_n_dlog_dp is None:
            raise ValueError("At least one of delta_n")

        return self

    @cached_property
    def n_total(self) -> np.floating[Any]:
        """Total number concentration, integrated over all bins [1/cm³]."""
        assert self.raw_delta_n is not None  # mypy doesnt track it correctly
        return np.floating(self.raw_delta_n.sum())

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
