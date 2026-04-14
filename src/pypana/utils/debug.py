"""A debug interface."""

from abc import ABC, abstractmethod


class Debuggable(ABC):
    """Class for debugging."""

    @abstractmethod
    def info(self, *, verbose: bool = False) -> None:
        """Print the state of the object."""
