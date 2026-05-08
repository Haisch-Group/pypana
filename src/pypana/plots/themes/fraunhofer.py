"""Matplotlib visualization theme."""

from pypana.plots.themes.base import BaseTheme


class FraunhoferTheme(BaseTheme, name="fhg"):
    """The Fraunhofer Theme."""

    color_cycle = {
        "fhg-green": "#179c7d",
        "steel-blue": "#005b7f",
        "orange": "#f58220",
        "silver-grey": "#a6bbc8",
        "weinrot": "#7c154d",
        "petrol": "#008598",
        "aqua": "#39c1cd",
        "lime": "#b2d235",
    }
