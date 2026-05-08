"""Definition of the intelligent SmartReader.

This module provides a class for automatically choosing the correct reader and therefore provides a real
instrument-agnostic interface to the user.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Unpack

from pypana.data.instrument_data import InstrumentData
from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.base_reader import BaseReader, ReaderKwargs
from pypana.readers.reader_redirector import ReaderRedirector


class _SmartReader(BaseReader, metaclass=ReaderRedirector):
    """Smart Reader for automatically detecting and choosing the correct reader for a given input file.

    It will create an instance (or child) of BaseInstrumentReader, depending on what is the correct reader.
    """


# Makes IntelliSense show the correct docstring of __init__ for SmartReader.
# _SmartReader is still there to have a minimal footprint at runtime,
# the extensive stub is only implemented for typechecking
if TYPE_CHECKING:  # pragma: no cover

    class SmartReader(BaseInstrumentReader):
        """Smart Reader for automatically detecting and choosing the correct reader for a given input file.

        It will create an instance (or child) of BaseInstrumentReader, depending on what is the correct reader.
        """

        # noinspection PyUnusedLocal
        def __init__(
            self,
            path: Path | str | None = None,
            **kwargs: Unpack[ReaderKwargs],
        ) -> None:  # noqa: ARG001
            """Default constructor for all readers.

            Args:
                path: The path to the input file. Defaults to None, in which case a selection dialogue is opened.
            """
            super().__init__(**kwargs)

        @classmethod
        def can_read(cls, path: Path) -> bool:
            """Check if this reader can read a given file. It indicates that this class is the correct reader.

            Args:
                path: The Path to the input file.

            Returns:
                Whether the read test succeeded.
            """
            pass

        def read(self) -> InstrumentData:
            """Read the given file and convert its data into the pypana format.

            Returns:
                InstrumentData: The pypana instrument on which further analysis can be conducted.

            Raises:
                ReadError: If an error occurs while reading the file.
            """
            pass
else:
    # this is the actual definition
    SmartReader = _SmartReader
