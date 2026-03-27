"""Base definition for instrument data readers.

This module provides the abstract base class for all instrument-specific readers.
It includes a registry of all subclasses to enable automatic format discovery.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

type InstrumentReaderList = list[type[BaseInstrumentReader]]


class BaseInstrumentReader(ABC):
    """Base instrument reader for all devices.

    Attributes:
        _subclasses (InstrumentReaderList): Internal registry of all available instrument reader classes.
    """

    _subclasses: InstrumentReaderList = []

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__()
        if cls not in BaseInstrumentReader._subclasses:
            BaseInstrumentReader._subclasses.append(cls)

    @classmethod
    def _deregister(cls, target: type[BaseInstrumentReader]) -> None:
        """Remove a reader from the subclass registry. Internal use for testing."""
        if target in cls._subclasses:
            cls._subclasses.remove(target)

    @classmethod
    def registered_readers(cls) -> InstrumentReaderList:
        """Returns a copy of all registered readers.

        Returns:
            InstrumentReaderList: A list of classes that can be used for file type discovery.
        """
        return cls._subclasses.copy()

    @classmethod
    @abstractmethod
    def can_read(cls, path: Path) -> bool:
        """Check if this reader can read a given file. It indicates that this class is the correct reader.

        Args:
            path: The Path to the input file.

        Returns:
            Whether the read test succeeded.
        """
        pass
