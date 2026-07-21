"""Base definition for instrument data readers.

This module provides the abstract base class for all instrument-specific readers.
It includes a registry of all subclasses to enable automatic format discovery.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Unpack

from pypana.data.instrument_data import InstrumentData
from pypana.readers.base_reader import BaseReader, ReaderKwargs
from pypana.readers.select_path import pick_path

type InstrumentReaderSet = set[type[BaseInstrumentReader]]


class BaseInstrumentReader(BaseReader, ABC):
    """Base instrument reader for all devices.

    Attributes:
        _subclass_registry (InstrumentReaderList): Internal registry of all available instrument reader classes.
    """

    _device_name: ClassVar[str]
    _subclass_registry: InstrumentReaderSet = set()

    def __init__(
        self,
        path: Path | str | None = None,
        **kwargs: Unpack[ReaderKwargs],
    ) -> None:
        """Default constructor for all readers.

        Args:
            path: The path to the input file. Defaults to None, in which case a selection dialogue is opened.
        """
        super().__init__()
        self._reader_options = kwargs

        _path: Path

        if not path:
            _path = pick_path(self._input_type)  # pragma: no branch
        elif isinstance(path, str):
            _path = Path(path)
        else:
            _path = path

        self._path = _path

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__()
        BaseInstrumentReader._subclass_registry.add(cls)

    @classmethod
    def _deregister(cls, target: type[BaseInstrumentReader]) -> None:
        """Remove a reader from the subclass registry. Internal use for testing."""
        cls._subclass_registry.discard(target)

    @classmethod
    def registered_readers(cls) -> InstrumentReaderSet:
        """Returns a copy of all registered readers.

        Returns:
            InstrumentReaderList: A list of classes that can be used for file type discovery.
        """
        return cls._subclass_registry.copy()

    @classmethod
    @abstractmethod
    def can_read(cls, path: Path) -> bool:
        """Check if this reader can read a given file. It indicates that this class is the correct reader.

        Args:
            path: The Path to the input file.

        Returns:
            Whether the read test succeeded.
        """

    @abstractmethod
    def read(self) -> InstrumentData:
        """Read the given file and convert its data into the pypana format.

        Returns:
            InstrumentData: The pypana instrument on which further analysis can be conducted.

        Raises:
            ReadError: If an error occurs while reading the file.
        """
