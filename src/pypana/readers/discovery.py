"""Definition of the intelligent SmartReader.

This module provides a class for automatically choosing the correct reader and therefore provides a real
instrument-agnostic interface to the user.
"""

from typing import TYPE_CHECKING

from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.base_reader import BaseReader
from pypana.readers.reader_redirector import ReaderRedirector


class _SmartReader(BaseReader, metaclass=ReaderRedirector):
    """Smart Reader for automatically detecting and choosing the correct reader for a given input file.

    It will create an instance (or child) of BaseInstrumentReader, depending on what is the correct reader.
    """


# This is the only way to make the `BaseInstrumentReader.__init__` docstring show on hover
# for both VS Code and PyCharm. The else block is the actual definition, but it shows the correct docstring.
if TYPE_CHECKING:  # pragma: no cover
    from functools import wraps

    # noinspection PyPep8Naming
    @wraps(BaseInstrumentReader.__init__)
    def SmartReader(*args, **kwargs) -> BaseInstrumentReader: ...  # noqa: N802, D103, ANN002
else:
    # this is the actual definition
    SmartReader = _SmartReader
