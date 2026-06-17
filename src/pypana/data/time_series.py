"""The TimeSeries; one quantity sampled over time by counter/photometer instruments."""
from functools import cached_property
from typing import Literal, Self

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from pypana.data.defs import FloatArray, Quantity
from pypana.data.defs.arrays import DateTime64Array
from pypana.utils.debug import Debuggable

TimeUnit = Literal["h", "m", "s", "ms", "us", "ns"]


class TimeSeries(BaseModel, Debuggable):
    """One quantity sampled over time.

    The quantity is purely a label for what the values represent.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        ignored_types=(cached_property,),
        populate_by_name=True,
        validate_assignment=True,
    )

    quantity: Quantity = Field(
        frozen=True,
        description="The interpretation of the sampled values.",
    )
    timestamps: DateTime64Array = Field(
        description="Absolute wall-clock time of each sample, strictly increasing.",
    )
    values: FloatArray = Field(
        description="Sampled values in the quantity's canonical unit, one per sample.",
    )

    @field_validator("timestamps", mode="before")
    @classmethod
    def _coerce_ms(cls, value: object) -> DateTime64Array:
        """Normalizes any datetime-like input to ``datetime64[ms]``."""
        return np.asarray(value, dtype="datetime64[ms]")  # noqa: type

    @model_validator(mode="after")
    def _check_values(self) -> Self:
        """Checks the time and value arrays are 1D, aligned, non-empty, and time is increasing."""
        for name, arr in (("timestamps", self.timestamps), ("values", self.values)):
            if arr.ndim != 1:
                raise ValueError(f"`{name}` must be one-dimensional.")

        if self.values.size == 0:
            raise ValueError("A TimeSeries needs at least one sample.")

        if self.timestamps.shape != self.values.shape:
            raise ValueError(
                f"`timestamps` ({self.timestamps.size}) and `values` ({self.values.size}) "
                f"must have the same length."
            )

        if not np.all(np.diff(self.timestamps) > np.timedelta64(0, "ms")):
            raise ValueError("`timestamps` must be strictly increasing.")

        return self

    @cached_property
    def n_samples(self) -> int:
        """Number of samples."""
        return self.values.size

    def elapsed(self, unit: TimeUnit = "s") -> FloatArray:
        """Time of each sample since the first one, in the given unit.

        Args:
            unit: Resolution, "h", "m", "s" (seconds), "ms", "us", or "ns". Defaults to seconds.

        Returns:
            One value per sample.
        """
        return (self.timestamps - self.timestamps[0]) / np.timedelta64(1, unit)

    def duration(self, unit: TimeUnit = "s") -> float:
        """Elapsed time between the first and last sample, in the given unit.

        Args:
            unit: Resolution, "h", "m", "s" (seconds), "ms", "us", or "ns". Defaults to seconds.

        Returns:
            The total duration of the measurement.
        """
        if self.timestamps.size < 2:
            return 0.0

        return float((self.timestamps[-1] - self.timestamps[0]) / np.timedelta64(1, unit))

    @cached_property
    def mean(self) -> float:
        """Mean of the sampled values."""
        return float(np.nanmean(self.values))

    @cached_property
    def vmin(self) -> float:
        """Minimum sampled value."""
        return float(np.nanmin(self.values))

    @cached_property
    def vmax(self) -> float:
        """Maximum sampled value."""
        return float(np.nanmax(self.values))

    @cached_property
    def std(self) -> float:
        """Standard deviation of the sampled values."""
        return float(np.nanstd(self.values))
