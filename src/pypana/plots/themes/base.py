from __future__ import annotations
from typing import ClassVar, Callable, Any

import matplotlib
from cycler import cycler
from pydantic.dataclasses import dataclass


@dataclass
class _Field:
    keys: str | list[str]
    transform: Callable[..., Any] | None = None

_FIELDS: dict[str, _Field] = {
  "color_cycle": _Field("axes.prop_cycle", transform=lambda v: cycler(color=v)),
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
}

type ThemeSet = set[type[PlotTheme]]

class PlotTheme:
    """Base class for all plotting themes.

    Subclass and override only the attributes you need.
    All attributes default to None, meaning that rcParam is left unchanged.
    """

    # ----- COLORS ----- #
    color_cycle: ClassVar[list[str] | None] = None
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


    # ----- PRIVATE ----- #
    _subclass_registry: ThemeSet = set()

    def __init_subclass__(cls, name: str | None = None, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        cls.name = name or cls.__name__
        PlotTheme._subclass_registry.add(cls)

    @classmethod
    def _deregister(cls, target: type[PlotTheme]) -> None:
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
        params: dict[str, Any] = {}

        for attr, field in _FIELDS.items():
            value = getattr(cls, attr, None)

            if value is None:
                continue

            value = field.transform(value) if field.transform else value

            for key in ([field.keys] if isinstance(field.keys, str) else field.keys):
                params[key] = value

        return params

    @classmethod
    def apply(cls) -> None:
        matplotlib.rcParams.update(cls.to_rcparams())
