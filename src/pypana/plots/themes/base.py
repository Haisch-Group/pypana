"""Matplotlib visualization theme."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar

import matplotlib
from cycler import cycler
from rich.text import Text

from pypana.console import console

LUMINANCE_THRESHOLD = 0.35


@dataclass
class _Field:
    keys: str | list[str]
    transform: Callable[..., Any] | None = None


_FIELDS: dict[str, _Field] = {
    "color_cycle": _Field(
        "axes.prop_cycle", transform=lambda v: cycler(color=[c for c in v.values()])
    ),
    "colormap": _Field("image.cmap"),
    "grid_color": _Field("grid.color"),
    "font_family": _Field("font.family"),
    "font_size": _Field("font.size"),
    "title_size": _Field("axes.titlesize"),
    "label_size": _Field("axes.labelsize"),
    "tick_size": _Field(["xtick.labelsize", "ytick.labelsize"]),
    "legend_size": _Field("legend.fontsize"),
    "line_width": _Field("lines.linewidth"),
    "marker_size": _Field("lines.markersize"),
    "grid_visible": _Field("axes.grid"),
    "grid_alpha": _Field("grid.alpha"),
    "grid_linestyle": _Field("grid.linestyle"),
    "tick_direction": _Field(["xtick.direction", "ytick.direction"]),
    "spine_width": _Field("axes.linewidth"),
    "figure_size": _Field("figure.figsize", transform=list),
    "dpi": _Field("savefig.dpi"),
}

type ThemeSet = set[type[BaseTheme]]


class BaseTheme:
    """Base class for all plotting themes.

    Subclass and override only the attributes you need.
    All attributes default to None, meaning that rcParam is left unchanged.
    """

    extra_rc: ClassVar[dict[str, Any]] = {}

    # ----- COLORS ----- #
    color_cycle: ClassVar[dict[str, str] | None] = None
    colormap: ClassVar[str | None] = None
    grid_color: ClassVar[str | None] = None

    # ----- FONT ----- #
    font_family: ClassVar[str | None] = None
    font_size: ClassVar[float | None] = None
    title_size: ClassVar[float | None] = None
    label_size: ClassVar[float | None] = None
    tick_size: ClassVar[float | None] = None
    legend_size: ClassVar[float | None] = None

    # ----- LINES ----- #
    line_width: ClassVar[float | None] = None
    marker_size: ClassVar[float | None] = None

    # ----- GRID ----- #
    grid_visible: ClassVar[bool | None] = None
    grid_alpha: ClassVar[float | None] = None
    grid_linestyle: ClassVar[str | None] = None

    # ----- AXES ----- #
    tick_direction: ClassVar[str | None] = None
    spine_width: ClassVar[float | None] = None

    # ----- FIGURE ----- #
    figure_size: ClassVar[tuple[float, float] | None] = None
    dpi: ClassVar[int | None] = (
        None  # precedence: method dpi > theme dpi > settings dpi
    )

    # ----- PRIVATE ----- #
    _subclass_registry: ThemeSet = set()
    name: str | None = None

    def __init_subclass__(cls, name: str | None = None, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        cls.name = name or cls.__name__
        BaseTheme._subclass_registry.add(cls)

    @classmethod
    def _deregister(cls, target: type[BaseTheme]) -> None:
        """Remove a theme from the subclass registry. Internal use for testing."""
        cls._subclass_registry.discard(target)

    @classmethod
    def registered_themes(cls) -> ThemeSet:
        """Returns a copy of all registered themes.

        Returns:
            ThemeSet: A list of classes that can be used as theme.
        """
        return cls._subclass_registry.copy()

    @classmethod
    def to_rcparams(cls) -> dict[str, Any]:
        """Transforms the theme to be loadable with matplotlib rcparams."""
        params: dict[str, Any] = {}

        for attr, field in _FIELDS.items():
            value = getattr(cls, attr, None)

            if value is None:
                continue

            value = field.transform(value) if field.transform else value

            for key in [field.keys] if isinstance(field.keys, str) else field.keys:
                params[key] = value

        params.update(cls.extra_rc)
        return params

    @classmethod
    def apply(cls) -> None:
        """Load theme into matplotlib."""
        matplotlib.rcParams.update(cls.to_rcparams())

    @classmethod
    def print_theme(cls) -> None:
        """Print theme in a human-readable format."""
        output = Text()
        output.append(
            Text(
                f"{(str(cls.name) if cls.name else '') + '    (' + cls.__name__ + ')':─<52.52}",
                style="bold",
            )
        )
        output.append("\n")
        output.append(cls.__doc__)
        output.append("\n")

        if cls.color_cycle:
            for i, (color_name, hex_color) in enumerate(cls.color_cycle.items(), 1):
                foreground = (
                    "black" if _luminance(hex_color) > LUMINANCE_THRESHOLD else "white"
                )
                output.append(f"  {i:2}.    {color_name:12.12}  ")
                output.append(f"  {hex_color}  ", style=f"{foreground} on {hex_color}")
                output.append("\n")

        output.append("\n")

        for attr, field in _FIELDS.items():
            if attr == "color_cycle":
                continue

            value = getattr(cls, attr, None)

            if value is None:
                continue

            keys = [field.keys] if isinstance(field.keys, str) else field.keys

            for key in keys:
                output.append(f"  {key:<30}  {value}", style="")

        console.print(output)


def _luminance(hex_color: str) -> float:
    """The luminance of the color."""
    h = hex_color.lstrip("#")
    r, g, b = tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
