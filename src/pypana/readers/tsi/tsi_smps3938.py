"""Implementation of a Reader for the TSI Universal-Scanning Mobility Particle Sizer (SMPS) 3938.

This module provides the corresponding reader for the produced files of a TSI SMPS 3938.

References:
    https://tsi.com/products/particle-sizers/scanning-mobility-particle-sizer-spectrometers/general-scanning-mobility-particle-sizer-smps-3938
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from pandas import Index

from pypana.config import UnitScale
from pypana.data.bin_axis import BinAxis
from pypana.data.defs import FloatArray, Quantity
from pypana.data.instrument_data import InstrumentData
from pypana.data.measurement import Measurement
from pypana.data.size_distribution import SizeDistribution
from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.base_reader import InputType
from pypana.readers.exceptions.read_error import ReaderNotImplementedError, ReadError
from pypana.readers.tsi.utils import is_basic_tsi_format_file
from pypana.readers.utils import other_columns_to_dict


class TSISMPS3938InstrumentReader(BaseInstrumentReader):
    """Instrument reader for TSI SMPS 3938."""

    _encoding = "iso-8859-1"
    _device_name = "TSI SMPS 3938"
    _input_type = InputType.FILE

    _REPORTED_UNITS = "dw/dlogDp"
    _REPORTED_WEIGHT = "Number"
    _SIZE_SCALING_FACTOR = UnitScale.NANO.value
    _HEADER_START = "Sample #\tDate\tStart Time"
    _DIAMETER_LABEL = "Diameter Midpoint (nm)"
    _FIRST_TRAILING_COLUMN = "Scan Time (s)"
    _DATETIME_FORMAT = "%m/%d/%Y %H:%M:%S"

    @classmethod
    def can_read(cls, path: Path) -> bool:
        """Checks whether a given path may include a TSI SMPS 3938 output file that can be read.

        Current checks include:
            - whether the path is a file
            - the 3082 classifier, channel resolution, Units and Weight are given
            - the scan lines start with continuous integers

        Args:
            path: The path to the input file.

        Returns:
            Whether the read test succeeded when applying the TSI SMPS 3938 format.

        Raises:
            ReadError: If confident enough that the input is from TSI SMPS 3938, but the data suggests otherwise.
                This may happen because the input files were manually edited in unsafe places or this package
                does not yet fully implement this device's formats.
                Note: the absence of ReadError in this method does not guarantee the input is parseable.
        """
        anchors = [
            "Classifier Model\t3082",
            "Channels/Decade",
            "Units",
            "Weight",
            "Sample #",
        ]

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
            ReaderNotImplementedError: If the file does not report Number-weighted dN/dlogDp data.
        """
        header_pos, channels_per_decade, units, weight = self._read_file_metadata()

        if units != self._REPORTED_UNITS or weight != self._REPORTED_WEIGHT:
            raise ReaderNotImplementedError(
                f"Only {self._REPORTED_WEIGHT}-weighted {self._REPORTED_UNITS} data is implemented "
                f"for TSI SMPS 3938 (got weight={weight!r}, units={units!r})."
            )

        try:
            data = pd.read_table(
                self._path,
                header=header_pos,
                encoding=self._encoding,
                skip_blank_lines=True,
            )

            diameter_loc = data.columns.get_loc(self._DIAMETER_LABEL)
            assert isinstance(diameter_loc, int)
            trailing_loc = data.columns.get_loc(self._FIRST_TRAILING_COLUMN)
            assert isinstance(trailing_loc, int)

            bin_columns = data.columns[diameter_loc + 1 : trailing_loc]
            bin_boundaries = self._build_bin_boundaries(
                bin_columns, channels_per_decade
            )
            axis = BinAxis(
                bin_boundaries=bin_boundaries.copy(), diameter_type="mobility"
            )

            trailing_columns = data.columns[trailing_loc:].to_list()

        except (FileNotFoundError, ValueError, KeyError) as e:
            raise ReadError(f"{e}") from e

        measurements: dict[int, Measurement] = {}

        for row in data.to_dict("records"):
            try:
                scan_nr = int(row["Sample #"])
                time = datetime.strptime(
                    f"{row['Date']} {row['Start Time']}", self._DATETIME_FORMAT
                )
                delta_n_dlog_dp = np.array(
                    [row[col] for col in bin_columns],
                    dtype=float,
                )

                number = SizeDistribution(
                    quantity=Quantity.NUMBER,
                    axis=axis,
                    delta_dlogdp=delta_n_dlog_dp,
                )

                other_info = other_columns_to_dict(row, trailing_columns)

                measurements[scan_nr - 1] = Measurement(  # 0-based indexing
                    scan_nr=scan_nr,
                    time=time,
                    axis=axis,
                    distributions={Quantity.NUMBER: number},
                    other=other_info,
                )
            except (ValueError, AttributeError, KeyError) as e:
                raise ReadError(f"{e}") from e

        return InstrumentData(
            measurements=measurements,
            device_name=self._device_name,
            file_path=self._path,
            other_info={
                "channels_per_decade": channels_per_decade,
                "units": units,
                "weight": weight,
            },
        )

    def _read_file_metadata(self) -> tuple[int, int, str | None, str | None]:
        """Scans the metadata block above the table for the values the reader needs.

        Returns:
            The header line index, the channel resolution, and the reported units and weight.

        Raises:
            ReadError: If the table header or the channel resolution cannot be found.
        """
        header_pos: int | None = None
        channels_per_decade: int | None = None
        units: str | None = None
        weight: str | None = None

        with Path.open(self._path, "r", encoding=self._encoding) as f:
            for i, line in enumerate(f):
                if line.startswith("Channels/Decade"):
                    channels_per_decade = int(line.split("\t")[1])

                elif line.startswith("Units"):
                    units = line.split("\t")[1].strip()

                elif line.startswith("Weight"):
                    weight = line.split("\t")[1].strip()

                elif line.startswith(self._HEADER_START):
                    header_pos = i
                    break

        if header_pos is None:
            raise ReadError(
                message="The file does not contain the start of the TSI SMPS 3938 table header.",
                path=self._path,
            )

        if channels_per_decade is None:
            raise ReadError(
                message="The file does not report 'Channels/Decade'.",
                path=self._path,
            )

        return header_pos, channels_per_decade, units, weight

    @classmethod
    def _build_bin_boundaries(
        cls, bin_columns: Index, channels_per_decade: int
    ) -> FloatArray:
        """Reconstructs an exact, constant-channels-per-decade boundary grid in meters.

        The reported midpoints are rounded to one decimal,
        so they are only used to fix the grid's offset; the spacing is taken from the file's
        channel resolution. This yields a constant logarithmic bin width that the instrument
        actually uses.

        Args:
            bin_columns: The concentration column headers.
            channels_per_decade: The instrument's channel resolution.

        Returns:
            The ``n + 1`` bin boundaries in meters.
        """
        midpoints_file = np.array(bin_columns, dtype=float) * cls._SIZE_SCALING_FACTOR

        delta_log = 1 / channels_per_decade
        relative = np.arange(len(midpoints_file)) * delta_log
        offset = float(np.mean(np.log10(midpoints_file) - relative))
        d_p = 10.0 ** (relative + offset)

        half_step = 10.0 ** (delta_log / 2)

        return np.append(d_p / half_step, d_p[-1] * half_step)
