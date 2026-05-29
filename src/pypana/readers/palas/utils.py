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


def _split_usmps_measurements(lines: list[str]) -> list[list[str]]:
    """Split a PALAS U-SMPS file into per-scan blocks.

    A new block begins at each parameter line, identified by a non-empty first
    tab-field (the measurement date); the data rows that follow have an empty
    first field. Blank lines are ignored.

    Args:
        lines: All lines of a file to split.

    Returns:
        A list of measurements. Each list corresponds with one measurement.
    """
    measurements: list[list[str]] = []
    current_measurement: list[str] = []

    for line in lines:
        if not line.strip():
            continue

        if line.split("\t")[0].strip():  # parameter line starts a new block
            if current_measurement:
                measurements.append(current_measurement)
            current_measurement = []

        current_measurement.append(line)

    if current_measurement:
        measurements.append(current_measurement)

    return measurements
