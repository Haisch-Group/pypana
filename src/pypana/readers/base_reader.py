"""Base definition for all pypana readers.

This module provides the abstract base class for all readers for any purpose.
"""

from typing import ClassVar, TypedDict

type ReaderList = list[type[BaseReader]]


class BaseReader:
    """Base reader class for all purposes."""

    _device_name: ClassVar[str]


class ReaderKwargs(TypedDict, total=False):
    """The kwargs passed to the reader class."""
