"""Constants and Settings for pypana.

This module provides all global constants and settings to be used. Most can be changed at runtime to alter specific
behavior.
"""

from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from pypana.plots.themes import BaseTheme


class _Constants(BaseSettings):
    """General constants for the pypana package.

    This class automatically loads and validates constants from environmental variables.
    Entries can be changed at runtime.
    """

    ELEMENTARY_CHARGE: float = Field(
        default=1.602176634e-19,
        title="Elementary Charge",
        description="The elementary charge (e) in coulomb (C), as per https://physics.nist.gov/cgi-bin/cuu/Value?e. ",
    )

    STP: tuple[float, float] = Field(
        default=(273.15, 100.0),
        title="Standard Temperature and Pressure",
        description="The Standard Temperature (in K) and Pressure (in kPa). ",
    )

    NTP: tuple[float, float] = Field(
        default=(293.15, 101.325),
        title="Normal Temperature and Pressure",
        description="The Normal Temperature (in K) and Pressure (in kPa). ",
    )

    TSI_NTP: tuple[float, float] = Field(
        default=(294.16, 101.3),
        title="TSI Normal Temperature and Pressure",
        description="The TSI specific Normal Temperature (in K) and Pressure (in kPa) as per "
        "https://tsi.com/getmedia/a28dbc6d-ac11-4305-8501-3ce3f0163bbf/GenPurp"
        "-Standard_vs_Volumetric_FLOW-004_US.",
    )


class _Settings(BaseSettings):
    """General settings for the pypana package.

    This class automatically loads and validates settings from environmental variables.
    Entries can be changed at runtime.
    """

    model_config = SettingsConfigDict(
        arbitrary_types_allowed=True,
    )

    # ----- VISUALIZATION ----- #
    THEME: type[BaseTheme] = Field(
        default=BaseTheme,
        title="Visualization theme",
        description="The theme to use for matplotlib visualizations. Can be overriden per visualization call as kwarg.",
    )

    # ----- EXPORT ----- #
    EXPORT_DPI: int = Field(
        default=600,
        title="Export DPI for matplotlib.pyplot",
        description="The DPI for matplotlib.pyplot image exports. The standard figure is then 3840x2880 pixels.",
    )


class UnitScale(float, Enum):
    """Scaling factor for sizes."""

    IDENTITY = 1
    MILLI = 1e-3
    MICRO = 1e-6
    NANO = 1e-9

    @classmethod
    def get_from_str(cls, text: str) -> float:
        """Get the appropriate scaling factor for a string of text.

        Args:
            text (str): The string that contains a scaling factor symbol.

        Returns:
            the appropriate scaling factor.

        Raises:
            ValueError
        """
        found_symbols: list[UnitScale] = []

        if "mm" in text:
            found_symbols.append(cls.MILLI)
        if "µm" in text:
            found_symbols.append(cls.MICRO)
        if "nm" in text:
            found_symbols.append(cls.NANO)

        if len(found_symbols) > 1:
            raise ValueError()  # TODO: create significant exception for this case

        if len(found_symbols) == 1:
            return found_symbols.pop()

        return cls.IDENTITY


constants = _Constants()
settings = _Settings()
