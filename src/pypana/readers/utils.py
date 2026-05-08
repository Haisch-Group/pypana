"""Utility functions for reading."""

import itertools
from collections.abc import Hashable
from pathlib import Path
from typing import Any

from pypana.readers.exceptions.read_error import ReadError


def check_anchors_in_file(
    path: Path, anchors: list[str], *, encoding: str = "utf-8"
) -> tuple[bool, int]:
    """Check whether all anchors are present.

    If all anchors are present, the second value will be line of the last anchor

    Args:
        path (Path): Path to the file to check.
        anchors (set[str]): Set of anchors to check.
        encoding (str, optional): Encoding of the file.

    Returns:
        tuple[bool, int]: Tuple containing: whether all anchors are present and the last anchor's line.
    """
    anchor_set = set(anchors)
    found_anchors = set()

    if not path.is_file():
        return False, 0

    with Path.open(path, "r", encoding=encoding) as f:
        for i, line in enumerate(f):
            cleaned_line = line.strip()

            if not cleaned_line:
                continue

            for anchor in anchors:
                if cleaned_line.startswith(anchor):
                    found_anchors.add(anchor)

            if anchor_set.issubset(found_anchors) and cleaned_line.startswith(
                anchors[-1]
            ):
                return True, i

    return False, 0


def check_samples_in_integer_order_in_file(
    path: Path, start_line: int, *, encoding: str = "utf-8"
) -> bool:
    """Check whether samples are in numerical order to ensure temporal order.

    Args:
        path (Path): Path to the file to check.
        start_line (int): Start line to check.
        encoding (str, optional): Encoding of the file.

    Returns:
        bool: Whether samples are in numerical order.

    Raises:
        ReadError: if sample line does not start with an integer
    """
    last_index = 0

    if not path.is_file():
        return False

    with Path.open(path, "r", encoding=encoding) as f:
        for line in itertools.islice(f, start_line, None):
            cleaned_line = line.strip()

            if not cleaned_line:
                continue

            first_column = cleaned_line.split("\t")[0]

            if not first_column.isdigit():
                raise ReadError(
                    message=f"Line '{cleaned_line} does not start with a sample number'",
                    path=path,
                )

            current_index = int(first_column)

            if current_index > last_index:
                last_index = current_index
                continue

            return False

    return True


def other_columns_to_dict(
    row: dict[Hashable, Any], columns: list[str]
) -> dict[Hashable, Any]:
    """Extract currently unused columns as dict.

    Args:
        row (dict[str, str]): Row to extract unused columns from.
        columns (list[str]): List of unused columns.

    Returns:
        dict[str, str]: Dictionary of unused columns.
    """
    return {col: row[col] for col in columns if col in row}
