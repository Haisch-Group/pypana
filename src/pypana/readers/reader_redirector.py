"""Metaclass definition for the SmartReader.

This module provides the MetaClass necessary for the SmartReader to dynamically find
and return the correct BaseInstrumentReader.
"""

from abc import ABCMeta
from pathlib import Path
from typing import Unpack

from pypana.readers.base_instrument_reader import (
    BaseInstrumentReader,
    InstrumentReaderSet,
)
from pypana.readers.base_reader import InputType, ReaderKwargs
from pypana.readers.exceptions.read_error import ReadError
from pypana.readers.exceptions.too_many_options import TooManyOptionsError
from pypana.readers.select_path import pick_path


class ReaderRedirector(ABCMeta):
    """MetaClass definition for SmartReader."""

    def __call__(
        cls, path: Path | str | None = None, **kwargs: Unpack[ReaderKwargs]
    ) -> BaseInstrumentReader:
        """Routes to the correct reader for a given input file and returns an instance of this class.

        This uses some unintuitive black magic that defies the principles of OOP.
        However, this is the only way to provide seamless initialization without further calls to a factory before
        the pipeline can continue like when the correct reader is initialized in the first place.

        Args:
            path: The path to the input file.
            **kwargs: kwargs
        """
        _path: Path

        if not path:
            _path = pick_path(InputType.UNDEFINED)  # pragma: no branch
        elif isinstance(path, str):
            _path = Path(path)
        else:
            _path = path

        possible_readers: InstrumentReaderSet = set()

        if not Path.exists(_path):
            raise ReadError(
                message="The input does not exist.",
                path=_path,
            )

        for reader in BaseInstrumentReader.registered_readers():
            if reader.can_read(_path):
                possible_readers.add(reader)

        if len(possible_readers) == 0:
            raise ReadError(
                message="No reader found for the input file.",
                path=_path,
            )

        if len(possible_readers) > 1:
            raise TooManyOptionsError(path=_path, possible_readers=possible_readers)

        # suppress PyCharm type checking, since everything is correctly typed. **kwargs not yet used,
        # but maybe in the future
        # noinspection PyArgumentList
        return possible_readers.pop()(_path, **kwargs)
