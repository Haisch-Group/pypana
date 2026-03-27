"""Definition of the intelligent SmartReader.

This module provides a class for automatically choosing the correct reader and therefore provides a real
instrument-agnostic interface to the user.
"""

from pypana.readers.base import BaseInstrumentReader


class SmartReader(BaseInstrumentReader):
    """Smart Reader for automatically detecting and choosing the correct reader for a given input file."""

    pass
