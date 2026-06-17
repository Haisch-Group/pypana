"""The Quantity; which physical weighting a value array contains.

The member value is the notation prefix, so canonical data type strings ca be built as ``f"d{quantity}{normalization}"``

Storage units:
    All pypana arrays hold values in the canonical unit of their quantity,
    independent of what the instrument reported. Readers convert on import, the plot code scales this accordingly.
    Particle diameters are always stored in meters.

    ===========  ============
    Quantity     Stored unit
    ===========  ============
    NUMBER       1/cm³
    SURFACE      m²/cm³
    VOLUME       m³/cm³
    MASS         µg/m³
    ===========  ============
"""

from enum import StrEnum

from pypana.utils.debug import Debuggable


class Quantity(Debuggable, StrEnum):
    """The physical weighting of a measured aerosol concentration."""

    NUMBER = "N"
    SURFACE = "S"
    VOLUME = "V"

    @classmethod
    def _missing_(cls, value: object) -> "Quantity | None":
        """Case-insensitive lookup of symbols and full names."""
        if not isinstance(value, str):
            return None

        aliases = {
            "n": cls.NUMBER,
            "s": cls.SURFACE,
            "v": cls.VOLUME,
        }

        return aliases.get(value.strip().lower())

    @property
    def full_name(self) -> str:
        """Readable name for legends."""
        return self.name.capitalize()

    @property
    def base_unit(self) -> str:
        """Unit of stored values, see module docstring.

        Display prefixes are chosen at plot time but don't influence the stored data.
        """
        match self:
            case Quantity.NUMBER:
                return "1/cm³"
            case Quantity.SURFACE:
                return "m²/cm³"
            case Quantity.VOLUME:
                return "m³/cm³"

    @property
    def moment(self) -> int:
        """Exponent of d_p in the per-particle weighting."""
        match self:
            case Quantity.NUMBER:
                return 0
            case Quantity.SURFACE:
                return 2
            case Quantity.VOLUME:
                return 3
