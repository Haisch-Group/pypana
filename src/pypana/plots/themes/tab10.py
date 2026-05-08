"""Matplotlib visualization theme."""

import matplotlib.colors as mcolors

from pypana.plots.themes.base import BaseTheme


class Tab10Theme(BaseTheme, name="tab10"):
    """The Tab10 palette.

    This is the default color palette of matplotlib. By default, pypana does not overwrite the matplotlib colors,
    but if done, this class can be used to momentarily revert to the default theme in a
    """

    color_cycle = mcolors.TABLEAU_COLORS
