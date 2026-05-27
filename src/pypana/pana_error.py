"""Base exception definition for the pypana package.

This module provides the root Exception class from which all package-specific errors must inherit.
No further logic is implemented, but all pypana related errors can be caught with one type.
"""


class ParticleAnalysisError(Exception):
    """Base Exception for this package."""

    pass


class IncompatibleArgumentError(ParticleAnalysisError):
    """Raised when a particular argument is incompatible with another given argument.."""

    def __init__(
        self,
        message: str = "Invalid indices selected",
        *,
        incompatible_with: list[tuple[str, object]] | None = None,
    ) -> None:
        """Initializes the error.

        Args:
            message (str, optional): A descriptive error message.
            incompatible_with (list[dict[str, object]], optional):
                A list of arguments and their values the argument is incompatible with
        """
        self.incompatible_with = incompatible_with

        if self.incompatible_with:
            message = f"{message} [Incompatible with: {', '.join(str(i) for i in self.incompatible_with)}]"

        super().__init__(message)
