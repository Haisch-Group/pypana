"""Exception for incompatible arguments."""

from __future__ import annotations

from pypana._pana_error import ParticleAnalysisError


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
