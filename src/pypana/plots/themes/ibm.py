"""Matplotlib visualization theme."""

from pypana.plots.themes.base import BaseTheme


class IBMTheme(BaseTheme, name="ibm"):
    """The IBM Color Blind Safe palette.

    'Designed by IBM the intention of being accessible to people who are colorblind.
    Credit: IBM Design Library. https://www.ibm.com/design/language/resources/color-library'
    https://www.color-hex.com/color-palette/1044488
    """

    color_cycle = {
        "1st": "#648fff",
        "2nd": "#ffb000",
        "3rd": "#dc267f",
        "4th": "#fe6100",
        "5th": "#785ef0",
        "black": "#000000",
    }
