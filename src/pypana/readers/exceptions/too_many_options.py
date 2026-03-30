"""Exception related to reading of instrument data from a file.

This module provides a specific error type for when a reader cannot be selected automatically,
because the given file's contents are not uniquely parseable by only one implemented reader.
"""

from pathlib import Path

from pypana.pana_error import ParticleAnalysisError
from pypana.readers.base_instrument_reader import InstrumentReaderList


class TooManyOptionsError(ParticleAnalysisError):
    """Raised when the SmartReader cannot uniquely identify a file's format."""

    def __init__(
        self,
        message: str = "Too many options when selecting reader.",
        *,
        path: Path | None = None,
        possible_readers: InstrumentReaderList | None = None,
    ) -> None:
        """Initializes the error.

        Args:
            message (str, optional): A descriptive error message.
            path (Path, optional): The path to the file.
            possible_readers (InstrumentReaderList, optional):
                Which conflicting BaseInstrumentReaders can parse this file.
        """
        super().__init__(message)
        self.path = path
        self.possible_readers = possible_readers

    def __str__(self) -> str:
        msg = super().__str__()

        if self.path:
            msg = f"{msg} [File: {self.path}]."

        if self.possible_readers:
            reader_names = [cls.__name__ for cls in self.possible_readers]
            msg = (
                f"{msg}\nPossible InstrumentReaders can parse the given file: "
                f"{', '.join(reader_names)}."
            )

        return msg
