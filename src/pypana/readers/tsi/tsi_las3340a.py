"""Implementation of a Reader for the TSI Laser Aerosol Spectrometer (LAS) 3340A.

This module provides the corresponding reader for the produced files of a TSI LAS 3340A.

References:
    https://tsi.com/products/particle-sizers/supermicron-capable-particle-sizer-spectrometers/laser-aerosol-spectrometer-(las)-3340a
"""

import re
from pathlib import Path

from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.exceptions.read_error import ReadError


class TSILAS3340AInstrumentReader(BaseInstrumentReader):
    """Instrument reader for TSI LAS 3340A."""

    _device_name = "TSI LAS 3340A"

    @classmethod
    def can_read(cls, path: Path) -> bool:
        """Checks whether a given path may include TSI LAS 3340A output files that can be read.

        Current checks include:
            - whether the path is a directory
            - the file names inside the directory are all numeric with underscore
            - no extra files not following the naming scheme were added to the path.

        Args:
            path: The path to the input directory.

        Returns:
            Whether the read test succeeded when applying the TSI LAS 3340A format.

        Raises:
            ReadError: If confident enough that the input is from TSI LAS 3340A, but the data suggests otherwise.
                This may happen because the input files were manually edited in unsafe places or this package
                does not yet fully implement this device's formats.
                Note: the absence of ReadError in this method does not guarantee the input is parseable.
        """
        anchors = ["Date", "Time", "Accum.", "Scatter", "Current", "Temp.", "Flow"]

        if not path.is_dir():
            return False

        file_pattern = re.compile(r"^\d{8}_[1-9]\d*")
        files = list(path.iterdir())

        if not files:
            return False

        for file in files:
            if not file_pattern.match(file.name):
                return False

            with Path.open(file) as f:
                header = f.readline().split()

                if not all(a in header[:15] for a in anchors):
                    raise ReadError(
                        message="The column names do not match specified anchors. "
                        "Please open a GitHub issue if this is a false positive.",
                        path=file,
                    )

        return True
