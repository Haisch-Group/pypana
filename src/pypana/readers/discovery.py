"""Definition of the intelligent SmartReader.

This module provides a class for automatically choosing the correct reader and therefore provides a real
instrument-agnostic interface to the user.
"""

from typing import TYPE_CHECKING

from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.base_reader import BaseReader
from pypana.readers.reader_redirector import ReaderRedirector


class _SmartReader(BaseReader, metaclass=ReaderRedirector):
    """Smart Reader for automatically detecting and choosing the correct reader for a given input file."""

    _device_name = "-/-"


if TYPE_CHECKING:
    SmartReader = BaseInstrumentReader
else:
    SmartReader = _SmartReader
