"""Exception related to reading of instrument data from a file.

This module provides a specific error type for when a reader cannot be selected automatically,
because the given file's contents are not uniquely parseable by only one implemented reader.
"""

from __future__ import annotations

from pathlib import Path

from pypana._pana_error import ParticleAnalysisError
from pypana.readers.base_instrument_reader import InstrumentReaderSet


class TooManyOptionsError(ParticleAnalysisError):
    """Raised when the SmartReader cannot uniquely identify a file's format."""

    def __init__(
        self,
        message: str = "Too many options when selecting reader.",
        *,
        path: Path | None = None,
        possible_readers: InstrumentReaderSet | None = None,
    ) -> None:
        """Initializes the error.

        Args:
            message (str, optional): A descriptive error message.
            path (Path, optional): The path to the file.
            possible_readers (InstrumentReaderList, optional):
                Which conflicting BaseInstrumentReaders can parse this file.
        """
        self.path = path
        self.possible_readers = possible_readers

        if self.path:  # pragma: no cover
            message = f"{message} [File: {self.path}]."

        if self.possible_readers:  # pragma: no cover
            reader_names = [
                f"{cls._device_name} / {cls.__name__}" for cls in self.possible_readers
            ]
            message = (
                f"{message}\nPossible InstrumentReaders can parse the given file: "
                f"{',\n'.join(reader_names)}."
            )

        super().__init__(message)
