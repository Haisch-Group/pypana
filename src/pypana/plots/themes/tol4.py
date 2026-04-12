"""Matplotlib visualization theme."""

from pypana.plots.themes.base import BaseTheme


class Tol4Theme(BaseTheme, name="tol4"):
    """The muted qualitative color scheme that is color-blind safe of Paul Tol.

    https://sronpersonalpages.nl/~pault/data/colourschemes.pdf
    """

    color_cycle = {
        "indigo": "#332288",
        "cyan": "#88ccee",
        "teal": "#44aa99",
        "green": "#117733",
        "olive": "#999933",
        "sand": "#ddcc77",
        "rose": "#cc6677",
        "wine": "#882255",
        "purple": "#aa4499",
    }
