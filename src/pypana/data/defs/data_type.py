"""The DataType object; one quantity in one representation.

This is purely used for requests from the user.
"""

from __future__ import annotations

from dataclasses import dataclass

from pypana.data.defs.data_type_str import VALID_DATA_TYPES, DataTypeStr
from pypana.data.defs.normalization import Normalization
from pypana.data.defs.quantity import Quantity
from pypana.utils.debug import Debuggable


@dataclass(frozen=True, slots=True)
class DataType(Debuggable):
    """A parsed request of a data type from a string, including quantity and normalization."""

    quantity: Quantity
    normalization: Normalization

    @classmethod
    def parse(cls, value: DataTypeLike | str) -> DataType:
        """Parses a string into a DataType object.

        Args:
            value: The input, can be the string representation, DataType, or Quantity (without normalization).

        Raises:
            ValueError: If the input matches no known data type.
        """
        if isinstance(value, DataType):
            return value

        if isinstance(value, Quantity):
            return cls(quantity=value, normalization=Normalization.NONE)

        head, slash, tail = value.strip().partition("/")
        head = head.strip().lower()

        if len(head) > 1 and head.startswith("d"):
            head = head.removeprefix("d")

        try:
            q = Quantity(head)
            n = Normalization(tail) if slash else Normalization.NONE
        except ValueError:
            raise ValueError(
                f"Unknown data type {value!r}. "
                f"Expected one of: {', '.join(VALID_DATA_TYPES)}"
            ) from None

        return cls(quantity=q, normalization=n)

    def __str__(self) -> str:
        """The spelling."""
        return f"d{self.quantity.value}{self.normalization.value}"

    @property
    def base_unit(self) -> str:
        """Unit of stored values, see module docstring.

        Display prefixes are chosen at plot time but don't influence the stored data.
        """
        return self.quantity.base_unit

    def axis_label(self, display_unit: str | None = None) -> str:
        """Plot axis label.

        Args:
            display_unit: The display unit of the axis label, chosen at plot time.
        """
        return f"{self} [{display_unit or self.base_unit}]"


type DataTypeLike = DataType | Quantity | DataTypeStr
"""What public methods accept."""
