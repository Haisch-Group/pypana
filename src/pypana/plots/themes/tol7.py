"""Matplotlib visualization theme."""

from pypana.plots.themes.base import BaseTheme


class Tol7Theme(BaseTheme, name="tol7"):
    """The light qualitative color scheme that is color-blind safe of Paul Tol.

    https://sronpersonalpages.nl/~pault/data/colourschemes.pdf
    """

    color_cycle = {
        "light blue": "#77aadd",
        "light cyan": "#99ddff",
        "mint": "#44bb99",
        "pear": "#bbcc33",
        "olive": "#aaaa00",
        "light yellow": "#eedd88",
        "orange": "#ee8866",
        "pink": "#ffaabb",
    }
