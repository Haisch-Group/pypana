"""Utility functions for reading specific to TSI."""

from pathlib import Path

from pypana.readers.exceptions.read_error import ReadError
from pypana.readers.utils import (
    check_anchors_in_file,
    check_samples_in_integer_order_in_file,
)


def is_basic_tsi_format_file(
    path: Path, anchors: list[str], *, encoding: str = "utf-8"
) -> bool:
    """Check if a TSI file is basic format.

    Returns:
        bool: True if basic format, False otherwise.

    Raises:
        ReadError: if likely TSI format but something is wrong.
    """
    if not path.is_file():
        return False

    all_anchors_found, last_line = check_anchors_in_file(
        path,
        anchors,
        encoding=encoding,
    )

    if not all_anchors_found:
        return False

    if not check_samples_in_integer_order_in_file(
        path,
        last_line + 1,  # start in line after header
        encoding=encoding,
    ):
        raise ReadError(
            message="The scans appear to not be in order",
            path=path,
        )

    return True
