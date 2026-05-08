"""Matplotlib visualization theme."""

from pypana.plots.themes.base import BaseTheme


class Tol3Theme(BaseTheme, name="tol3"):
    """The vibrant qualitative color scheme that is color-blind safe of Paul Tol.

    https://sronpersonalpages.nl/~pault/data/colourschemes.pdf
    """

    color_cycle = {
        "blue": "#0077bb",
        "cyan": "#33bbee",
        "teal": "#009988",
        "orange": "#ee7733",
        "red": "#cc3311",
        "magenta": "#ee3377",
    }
