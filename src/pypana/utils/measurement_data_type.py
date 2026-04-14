"""Measurement data type."""

from enum import Enum


class MeasurementDataType(Enum):
    """The two basic types of measurements. Best when making distinctions."""

    dndlogdp = "dN/dlogdp"
    dn = "dN"

    @classmethod
    def _missing_(cls, value: object) -> "MeasurementDataType | None":
        if isinstance(value, str):
            for member in cls:
                cleaned_member = member.value.replace("/", "").lower()
                cleaned_value = value.replace("/", "").lower()

                if cleaned_member == cleaned_value:
                    return member

        return None
