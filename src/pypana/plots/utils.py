"""Utils for plotting the data."""

from collections import defaultdict

from matplotlib import ticker


def split_kwargs(*args: str, **kwargs: object) -> tuple[defaultdict[str, object], ...]:
    """Splits the given args into subkwargs by their prefix given in args.

    Args:
        *args: Positional prefixes.
        **kwargs: Keyword arguments to split by prefix.

    Returns:
        A tuple with each Keyword Argument sorted into its position given by the args prefix.
    """
    subkwargs: list[defaultdict[str, object]] = []

    for arg in args:
        argkwargs: defaultdict[str, object] = defaultdict(lambda: None)

        for kwarg, value in kwargs.items():
            if kwarg.startswith(arg):
                argkwargs.update({kwarg.split(arg, 1)[-1]: value})

        subkwargs.append(argkwargs)

    return tuple(subkwargs)


class SciUnitFormatter(ticker.ScalarFormatter):
    """A matplotlib formatter that shows a unit."""

    def __init__(self, unit: str = "", **kwargs) -> None:
        """Initializes a SciUnitFormatter object.

        Args:
            unit: The unit to display.
            kwargs: Keyword arguments for super initialization.
        """
        super().__init__(**kwargs)
        self._unit = unit

    def get_offset(self) -> str:
        """Returns the offset string for the unit."""
        offset = str(super().get_offset())

        if not self._unit:
            return offset

        return f"{offset}\u2009{self._unit}" if offset else self._unit


class LogSciUnitFormatter(ticker.LogFormatterSciNotation):
    """A matplotlib formatter that shows a unit and in log space."""

    def __init__(self, unit: str = "", **kwargs) -> None:
        """Initializes a SciUnitFormatter object.

        Args:
            unit: The unit to display.
            kwargs: Keyword arguments for super initialization.
        """
        super().__init__(**kwargs)
        self._unit = unit

    def __call__(self, x: float, pos: int | None = None) -> str:
        """Return the format for tick value x at position pos. pos=None indicates an unspecified location.

        Args:
            x: Tick value.
            pos: Position.

        Returns:
            The format.
        """
        s = str(super().__call__(x, pos))

        if not self._unit or not s:
            return s

        return (
            rf"{s}\,$\mathrm{{{self._unit}}}$" if "$" in s else f"{s}\u2009{self._unit}"
        )


def sci_unit_formatter(unit: str = "1/cm³") -> SciUnitFormatter:
    """Returns a SciUnitFormatter for the given unit.

    Args:
        unit: The unit to display.
    """
    fmt = SciUnitFormatter(unit=unit, useMathText=True)
    fmt.set_scientific(True)
    fmt.set_powerlimits((0, 0))

    return fmt


def linear_sci_formatter() -> ticker.ScalarFormatter:
    """Returns the default pypana linear scientific formatter."""
    fmt = ticker.ScalarFormatter(useMathText=True)
    fmt.set_scientific(True)
    fmt.set_powerlimits((-2, 0))
    return fmt
