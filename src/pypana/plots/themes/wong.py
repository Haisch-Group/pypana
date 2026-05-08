"""Matplotlib visualization theme."""

from pypana.plots.themes.base import BaseTheme


class WongTheme(BaseTheme, name="wong"):
    """The color-blind safe palette by Bang Wong (2011).

    This palette should be used for publishable visualizations.
    https://www.nature.com/articles/nmeth.1618
    """

    color_cycle = {
        "orange": "#e69f00",
        "sky blue": "#56b4e9",
        "bluish green": "#009e73",
        "yellow": "#f0e442",
        "blue": "#0072b2",
        "vermillion": "#d55e00",
        "reddish purple": "#cc79a7",
        "black": "#000000",
    }
