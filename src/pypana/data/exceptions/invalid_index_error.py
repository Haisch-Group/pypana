"""Exception related to selecting measurements.

This module provides a specific error type for when a subset of measurements is selected,
but the selection input is invalid.
"""

from pypana._pana_error import ParticleAnalysisError


class InvalidIndexError(ParticleAnalysisError, ValueError):
    """Raised when a particular measurement index is invalid."""

    def __init__(
        self,
        message: str = "Invalid indices selected",
        *,
        invalid_indices: list[int] | None = None,
    ) -> None:
        """Initializes the error.

        Args:
            message (str, optional): A descriptive error message.
            invalid_indices (list[int], optional): A list of invalid indices.
        """
        self.invalid_indices = invalid_indices

        if self.invalid_indices:
            message = f"{message} [Invalid indices: {', '.join(str(i) for i in self.invalid_indices)}]"

        super().__init__(message)
