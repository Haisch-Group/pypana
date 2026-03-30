"""Implementation of a Reader for the TSI Scanning Mobility Particle Sizer (SMPS) 3071.

This module provides the corresponding reader for the produced files of a TSI SMPS 3071.

References:
    https://tsi.com/discontinued-products/electrostatic-classifier-3071a
"""

from pathlib import Path

from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.exceptions.read_error import ReadError


class TSISMPS3071InstrumentReader(BaseInstrumentReader):
    """Instrument reader for TSI SMPS 3071."""

    _device_name = "TSI SMPS 3071"

    @classmethod
    def can_read(cls, path: Path) -> bool:
        """Checks whether a given path may include TSI SMPS 3071 output files that can be read.

        Current checks include:
            - whether the path is a file
            - Units and Weight are given
            - the scan lines start with continuous integers

        Args:
            path: The path to the input file.

        Returns:
            Whether the read test succeeded when applying the TSI SMPS 3071 format.

        Raises:
            ReadError: If confident enough that the input is from TSI SMPS 3071, but the data suggests otherwise.
                This may happen because the input files were manually edited in unsafe places or this package
                does not yet fully implement this device's formats.
                Note: the absence of ReadError in this method does not guarantee the input is parseable.
        """
        anchors = {"Classifier Model\t3071", "Units", "Weight", "Sample #"}
        found_anchors = set()
        data_started = False
        last_index = 0

        if not path.is_file():
            return False

        with Path.open(path, "r", encoding="iso-8859-1") as f:
            for _, line in enumerate(f, start=1):
                cleaned_line = line.strip()

                if not cleaned_line:
                    continue

                for anchor in anchors:
                    if cleaned_line.startswith(anchor):
                        found_anchors.add(anchor)

                if cleaned_line.startswith("Sample #") and not data_started:
                    data_started = True
                    continue

                if not data_started:
                    continue

                first_column = cleaned_line.split("\t")[0]

                if first_column.isdigit():
                    current_index = int(first_column)

                    if current_index == last_index + 1:
                        last_index += 1
                        continue

                raise ReadError(
                    message=f"Scan {last_index + 1} appears to be missing",
                    path=path,
                )

        return anchors.issubset(found_anchors)
