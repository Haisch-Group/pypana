"""Metaclass definition for the SmartReader.

This module provides the MetaClass necessary for the SmartReader to dynamically find
and return the correct BaseInstrumentReader.
"""

from abc import ABCMeta
from pathlib import Path
from typing import Unpack

from pypana.readers.base_instrument_reader import (
    BaseInstrumentReader,
    InstrumentReaderList,
)
from pypana.readers.base_reader import ReaderKwargs
from pypana.readers.exceptions.read_error import ReadError
from pypana.readers.exceptions.too_many_options import TooManyOptionsError


class ReaderRedirector(ABCMeta):
    """MetaClass definition for SmartReader."""

    def __call__(
        cls, path: Path, **kwargs: Unpack[ReaderKwargs]
    ) -> BaseInstrumentReader:
        """Routes to the correct reader for a given input file and returns an instance of this class.

        This uses some unintuitive black magic that defies the principles of OOP.
        However, this is the only way to provide seamless initialization without further calls to a factory before
        the pipeline can continue like when the correct reader is initialized in the first place.

        Args:
            path: The path to the input file.
            **kwargs: kwargs
        """
        possible_readers: InstrumentReaderList = []

        if not Path.exists(path):
            raise ReadError(
                message="The input does not exist.",
                path=path,
            )

        for reader in BaseInstrumentReader.registered_readers():
            if reader.can_read(path):
                possible_readers.append(reader)

        if len(possible_readers) == 0:
            raise ReadError(
                message="No reader found for the input file.",
                path=path,
            )

        if len(possible_readers) > 1:
            raise TooManyOptionsError(path=path)

        # suppress PyCharm type checking, since everything is correctly typed. **kwargs not yet used,
        # but maybe in the future
        # noinspection PyArgumentList
        return possible_readers[0](path, **kwargs)
