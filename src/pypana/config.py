"""Constants and Settings for pypana.

This module provides all global constants and settings to be used. Most can be changed at runtime to alter specific
behavior.
"""

from typing import Annotated

import numpy as np
import numpy.typing as npt
from pydantic import Field, SkipValidation
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Constants(BaseSettings):
    """General constants for the pypana package.

    This class automatically loads and validates constants from environmental variables.
    Entries can be changed at runtime.
    """

    ELEMENTARY_CHARGE: float = Field(
        default=1.602176634e-19,
        title="Elementary Charge",
        description="The elementary charge (e) in coulomb (C), as per https://physics.nist.gov/cgi-bin/cuu/Value?e. "
        "Weakly typed to respect settings.DTYPE",
    )

    STP: tuple[float, float] = Field(
        default=(273.15, 100.0),
        title="Standard Temperature and Pressure",
        description="The Standard Temperature (in K) and Pressure (in kPa). "
        "Weakly typed to respect settings.DTYPE",
    )

    NTP: tuple[float, float] = Field(
        default=(293.15, 101.325),
        title="Normal Temperature and Pressure",
        description="The Normal Temperature (in K) and Pressure (in kPa). "
        "Weakly typed to respect settings.DTYPE",
    )

    TSI_NTP: tuple[float, float] = Field(
        default=(294.16, 101.3),
        title="TSI Normal Temperature and Pressure",
        description="The TSI specific Normal Temperature (in K) and Pressure (in kPa) as per "
        "https://tsi.com/getmedia/a28dbc6d-ac11-4305-8501-3ce3f0163bbf/GenPurp"
        "-Standard_vs_Volumetric_FLOW-004_US."
        "Weakly typed to respect settings.DTYPE",
    )


class _Settings(BaseSettings):
    """General settings for the pypana package.

    This class automatically loads and validates settings from environmental variables.
    Entries can be changed at runtime.
    """

    model_config = SettingsConfigDict(
        arbitrary_types_allowed=True,
    )

    # ----- DATA ----- #
    DTYPE: Annotated[npt.DTypeLike, SkipValidation()] = Field(
        default=np.float32,
        title="NumPy data type for imported data",
        description="The default NumPy data type (dtype) used throughout the data pipeline. Should not be changed ",
    )

    # ----- VISUALIZATION ----- #

    # ----- EXPORT ----- #
    EXPORT_DPI: int = Field(
        default=600,
        title="Export DPI for matplotlib.pyplot",
        description="The DPI for matplotlib.pyplot image exports. The standard figure is then 3840x2880 pixels.",
    )


Constants = _Constants()
Settings = _Settings()
