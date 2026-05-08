"""Matplotlib visualization theme utils."""

from pypana.plots.themes.base import BaseTheme, ThemeSet


def print_themes() -> None:  # pragma: no cover
    """Print all available themes in a human-readable format."""
    for theme in BaseTheme.registered_themes():
        theme.print_theme()


def available_themes() -> ThemeSet:  # pragma: no cover
    """Get all available themes."""
    return BaseTheme.registered_themes()


def resolve_color(spec: int | object, theme: type[BaseTheme]) -> str:
    """Get the color code or index for the specified input, compatible with matplotlib and plotly."""
    if isinstance(spec, int):
        cycle = list(theme.color_cycle.values()) if theme.color_cycle else []
        return cycle[spec % len(cycle)] if cycle else "#000000"
    return str(spec)
