"""Exception related to reading of instrument data from a file.

This module provides a specific error type for when a file is unreadable, corrupted,
the reader encounters data that does not match its expected internal scheme,
or when no reader can be determined automatically.
"""

from pathlib import Path

from pypana._pana_error import ParticleAnalysisError


class ReadError(ParticleAnalysisError):
    """Raised when the reader cannot read the file. E.g. because of corrupted files or incorrect reader."""

    def __init__(
        self,
        message: str = "An unspecified error occurred while reading the file.",
        *,
        path: Path | None = None,
    ) -> None:
        """Initializes the error.

        Args:
            message (str, optional): A descriptive error message.
            path (Path, optional): The path to the file.
        """
        self.path = path

        if self.path:
            message = f"{message} [File: {self.path}]."

        super().__init__(message)


class ReaderNotImplementedError(ReadError):
    """Raised when class is not yet implemented."""

    def __init__(
        self, message: str = "This specific reader is not yet implemented."
    ) -> None:
        """Initializes the error.

        Args:
            message (str, optional): A descriptive error message.
        """
        super().__init__(message)
