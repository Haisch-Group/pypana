"""Base definition for instrument data readers.

This module provides the abstract base class for all instrument-specific readers.
It includes a registry of all subclasses to enable automatic format discovery.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Unpack

from pypana.readers.base_reader import BaseReader, ReaderKwargs

type InstrumentReaderList = list[type[BaseInstrumentReader]]


class BaseInstrumentReader(BaseReader, ABC):
    """Base instrument reader for all devices.

    Attributes:
        _subclass_registry (InstrumentReaderList): Internal registry of all available instrument reader classes.
    """

    _subclass_registry: InstrumentReaderList = []

    def __init__(self, path: Path, **kwargs: Unpack[ReaderKwargs]) -> None:
        """Default constructor for all readers.

        Args:
            path: The path to the input file.
        """
        super().__init__(**kwargs)
        self.path = path

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__()
        if cls not in BaseInstrumentReader._subclass_registry:
            BaseInstrumentReader._subclass_registry.append(cls)

    @classmethod
    def _deregister(cls, target: type[BaseInstrumentReader]) -> None:
        """Remove a reader from the subclass registry. Internal use for testing."""
        if target in cls._subclass_registry:
            cls._subclass_registry.remove(target)

    @classmethod
    def registered_readers(cls) -> InstrumentReaderList:
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
