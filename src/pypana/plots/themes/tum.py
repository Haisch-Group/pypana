"""Matplotlib visualization theme."""

from pypana.plots.themes.base import BaseTheme


class TUMTheme(BaseTheme, name="tum"):
    """The TUM Color palette.

    https://portal.mytum.de/corporatedesign/index_html/vorlagen/index_farben
    """

    color_cycle = {
        "TUMBlue": "#0065BD",
        "TUMAccentGreen": "#a2ad00",
        "TUMAccentOrange": "#e37222",
        "TUMDarkBlue": "#003359",
        "TUMLighterBlue": "#98c6ea",
        "Black": "#000000",
    }
