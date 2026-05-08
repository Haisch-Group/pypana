"""Implementation of a Reader for the TSI Scanning Mobility Particle Sizer (SMPS) 3071.

This module provides the corresponding reader for the produced files of a TSI SMPS 3071.

References:
    https://tsi.com/discontinued-products/electrostatic-classifier-3071a
"""

from pathlib import Path

from pypana.data.instrument_data import InstrumentData
from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.base_reader import InputType
from pypana.readers.exceptions.read_error import ReaderNotImplementedError
from pypana.readers.tsi.utils import is_basic_tsi_format_file


class TSISMPS3071InstrumentReader(BaseInstrumentReader):
    """Instrument reader for TSI SMPS 3071."""

    _encoding = "iso-8859-1"
    _device_name = "TSI SMPS 3071"
    _input_type = InputType.FILE

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
        anchors = ["Classifier Model\t3071", "Units", "Weight", "Sample #"]

        return is_basic_tsi_format_file(
            path,
            anchors,
            encoding=cls._encoding,
        )

    def read(self) -> InstrumentData:
        """Read the given file and convert its data into the pypana format.

        Returns:
            InstrumentData: The pypana instrument on which further analysis can be conducted.

        Raises:
            ReadError: If an error occurs while reading the file.
        """
        raise ReaderNotImplementedError()
