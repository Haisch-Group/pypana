"""A debug interface."""

from rich import inspect


class Debuggable:
    """Class for debugging."""

    def info(self, *, verbose: bool = False) -> None:  # pragma: no cover
        """Print the state of the object.

        Args:
            verbose: Verbose output.
        """
        inspect(self)
