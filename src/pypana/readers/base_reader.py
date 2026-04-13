"""Base definition for all pypana readers.

This module provides the abstract base class for all readers for any purpose.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import ClassVar, TypedDict

type ReaderList = list[type[BaseReader]]


class InputType(Enum):
    """Enumeration defining the input type.

    Supports files and directories.
    """

    UNDEFINED = 0
    FILE = 1
    DIRECTORY = 2


class ReaderKwargs(TypedDict, total=False):
    """The kwargs passed to the reader class."""


class BaseReader:
    """Base reader class for all purposes."""

    _encoding: ClassVar[str] = "utf-8"
    _input_type: ClassVar[InputType] = InputType.UNDEFINED
    _path: Path
