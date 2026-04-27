"""Utils for reading files of PALAS instruments."""


def _split_measurements(lines: list[str]) -> list[list[str]]:
    """Splits all measurements in the line list into separate lists.

    Args:
        lines: All lines of a file to split.

    Returns:
        A list of measurements. Each list corresponds with one measurement.
    """
    measurements: list[list[str]] = []
    current_measurement: list[str] = []
    split: bool = False

    for line in lines:
        if not line.strip():
            continue

        if split:
            measurements.append(current_measurement)
            current_measurement = []
            split = False

        current_measurement.append(line)

        if line.strip().startswith("Sum(dA)/A [-]"):
            split = True

    measurements.append(current_measurement)

    return measurements
