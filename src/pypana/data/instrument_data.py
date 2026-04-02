"""Definition of a dataclass for instrument output.

This module provides a class to store the data and perform calculations on it
"""

from pydantic import BaseModel

from pypana.data.measurement import Measurement


class InstrumentData(BaseModel):
    """Data class for instrument data."""

    model_config = {"arbitrary_types_allowed": True}

    measurements: list[Measurement]
