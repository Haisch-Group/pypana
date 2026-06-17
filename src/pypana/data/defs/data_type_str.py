"""Data Type spellings, written out.

These are all available data types as strings to the public methods.
"""

from typing import Literal, get_args

type DataTypeStr = Literal[
    "dN",
    "dS",
    "dV",
    "dN/dlogdp",
    "dS/dlogdp",
    "dV/dlogdp",
]

VALID_DATA_TYPES: tuple[str, ...] = get_args(DataTypeStr.__value__)
