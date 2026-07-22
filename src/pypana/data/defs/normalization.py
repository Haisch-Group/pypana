"""The Normalization/denominantor of a binned representation.

The member value is the notation suffix, so canonical data type strings ca be built as ``f"d{quantity}{normalization}"``
"""

from __future__ import annotations

from enum import StrEnum

from pypana.utils.debug import Debuggable


class Normalization(Debuggable, StrEnum):
    """The denominator a binned value array is divided by."""

    NONE = ""
    DLOG_DP = "/dlogdp"

    @classmethod
    def _missing_(cls, value: object) -> Normalization:
        """Case-insensitive lookup of symbols and full names."""
        if isinstance(value, str):
            member = {
                "none": cls.NONE,
                "raw": cls.NONE,
                "dlogdp": cls.DLOG_DP,
            }.get(value.strip().lower())

            if member is not None:
                return member

        raise ValueError(f"{value!r} is not a valid {cls.__name__}!")

    @property
    def full_name(self) -> str:
        """Readable name for legends."""
        match self:
            case Normalization.NONE:
                return "per bin"
            case Normalization.DLOG_DP:
                return "per Δlog d_p"
