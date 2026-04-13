"""Matplotlib visualization theme utils."""

from pypana.plots.themes.base import BaseTheme, ThemeSet


def print_themes() -> None:  # pragma: no cover
    """Print all available themes in a human-readable format."""
    for theme in BaseTheme.registered_themes():
        theme.print_theme()


def available_themes() -> ThemeSet:  # pragma: no cover
    """Get all available themes."""
    return BaseTheme.registered_themes()
