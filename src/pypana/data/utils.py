"""Utils for data processing."""

from typing import Any

import numpy as np
from matplotlib import ticker

from pypana.data.measurement import Measurement


def is_full_rectangular_matrix(matrix: list[list[Any]]) -> bool:
    """Checks whether the given input is a full rectangular matrix.

    Args:
        matrix (list[list[Any]]): The row-major input matrix.

    Returns:
        Whether it is a full rectangular matrix.
    """
    if len(matrix) == 0:
        return False

    _l = len(matrix[0])

    return all(len(row) == _l for row in matrix)


def get_xlims(measurements: list[Measurement], space: float) -> tuple[float, float]:
    """Calculates the lowest and uppermost limits occupying everything but the given space percentage.

    Args:
        measurements (list[Measurement]): The measurement list.
        space (float): The space percentage.

    Returns:
        The lower and upper bound.
    """
    lowest_bound = np.inf
    highest_bound = -np.inf

    for measurement in measurements:
        lowest_bound = min(lowest_bound, measurement.bin_boundaries[0])

        highest_bound = max(highest_bound, measurement.bin_boundaries[-1])

    log_lowest_bound = np.log10(lowest_bound)
    log_highest_bound = np.log10(highest_bound)
    log_bound_diff = log_highest_bound - log_lowest_bound
    log_space_each_side = (log_bound_diff / (1 - space) - log_bound_diff) / 2

    xlim_low = float(10 ** (log_lowest_bound - log_space_each_side))
    xlim_high = float(10 ** (log_highest_bound + log_space_each_side))

    return xlim_low, xlim_high


def linear_sci_formatter() -> ticker.ScalarFormatter:
    """Returns the default pypana linear scientific formatter."""
    fmt = ticker.ScalarFormatter(useMathText=True)
    fmt.set_scientific(True)
    fmt.set_powerlimits((-2, 0))
    return fmt
