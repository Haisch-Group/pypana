"""Matplotlib visualization theme."""

from pypana.plots.themes.base import BaseTheme


class ColorfulTheme(BaseTheme, name="colorful"):
    """A rainbow-like theme."""

    color_cycle = {
        "purple": "#69085A",
        "dark blue": "#0F1B5F",
        "light blue": "#00778A",
        "green": "#007C30",
        "grass green": "#679A1D",
        "yellow": "#FFDC00",
        "dark yellow": "#F9BA00",
        "orange": "#D64C13",
        "red": "#C4071B",
        "dark red": "#9C0D16",
    }
