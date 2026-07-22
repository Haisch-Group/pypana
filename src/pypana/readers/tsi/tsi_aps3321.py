"""Implementation of a Reader for the TSI Aerodynamic Particle Sizer Spectrometer 3321.

This module provides the corresponding reader for the produced files of a TSI APS 3321.

References:
    https://tsi.com/products/particle-sizers/supermicron-capable-particle-sizer-spectrometers/aerodynamic-particle-sizer-aps-3321
"""

from collections.abc import Hashable
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame

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


class TSIAPS3321InstrumentReader(BaseInstrumentReader):
    """Instrument reader for TSI APS 3321."""

    _device_name = "TSI APS 3321"
    _encoding = "iso-8859-1"
    _input_type = InputType.FILE

    _REPORTED_DATA_TYPE = "dN/dlogDp"
    _BINS = 52
    _D_P_COLUMNS_COUNT = 52
    _SIZE_SCALING_FACTOR = UnitScale.MICRO.value
    _CHANNELS_PER_DECADE = 32

    @classmethod
    def can_read(cls, path: Path) -> bool:
        """Checks whether a given path may include a TSI APS 3321 output file that can be read.

        Args:
            path: The path to the input file.

        Returns:
            Whether the read test succeeded when applying the TSI APS 3321 format.

        Raises:
            ReadError: If confident enough that the input is from TSI APS 3321, but the data suggests otherwise.
                This may happen because the input files were manually edited in unsafe places or this package
                does not yet fully implement this device's formats.
                Note: the absence of ReadError in this method does not guarantee the input is parseable.
        """
        anchors = ["Sample Time", "Density", "Stokes Correction", "Sample"]

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
            ReadError: If an error occurs while reading the file, or if the Aerodynamic Diameter is not set to dN/dlogDp.
        """
        header_start_characters = "Sample #\tDate\tStart Time\tAerodynamic Diameter"
        header_pos = 0

        sample_time: int = 0
        density: int = 0
        stokes_corrected: bool = False

        with Path.open(self._path, "r", encoding=self._encoding) as f:
            for i, line in enumerate(f):
                if line.startswith("Sample Time"):
                    sample_time = int(line[12:].strip())
                elif line.startswith("Density"):
                    density = int(line[8:].strip())
                elif line.startswith("Stokes Correction"):
                    stokes_corrected = line[18:].strip() == "on"
                elif line.startswith(header_start_characters):
                    header_pos = i
                    break

        if header_pos == 0:
            raise ReadError(
                message="The file does not contain the start of the TSI APS 3321 header.",
                path=self._path,
            )

        try:
            data = pd.read_table(
                self._path,
                header=header_pos,
                encoding=self._encoding,
                skip_blank_lines=True,
            )

            d_p_start_loc = data.columns.get_loc("Aerodynamic Diameter")
            assert isinstance(d_p_start_loc, int)
            d_p_start_column = int(d_p_start_loc) + 1

            bin_boundaries = self._read_bin_metadata(d_p_start_column, data)
            axis = BinAxis(
                bin_boundaries=bin_boundaries.copy(),
                diameter_type="aerodynamic",
            )
            bin_columns = data.columns[
                d_p_start_column : d_p_start_column + self._D_P_COLUMNS_COUNT
            ]

        except (FileNotFoundError, ValueError) as e:
            raise ReadError(f"{e}") from e

        float_cols = data.select_dtypes(include=["float"]).columns
        data[float_cols] = data[float_cols].astype(float)

        other_columns = data.columns[
            d_p_start_column + self._D_P_COLUMNS_COUNT : -6
        ].to_list()

        measurements: dict[int, Measurement] = {}
        for row in data.to_dict("records"):
            try:
                key, measurement = self._row_to_measurement(
                    row, axis, bin_columns, other_columns
                )
                measurements[key] = measurement

            except (ValueError, AttributeError, KeyError) as e:
                raise ReadError(f"{e}") from e

            except ReadError as e:
                raise e

        other_info: dict[Hashable, Any] = {
            "sample_time": sample_time,
            "density": density,
            "stokes_corrected": stokes_corrected,
        }

        return InstrumentData(
            measurements=measurements,
            device_name=self._device_name,
            file_path=self._path,
            other_info=other_info,
        )

    def _row_to_measurement(
        self,
        row: dict[Hashable, Any],
        axis: BinAxis,
        bin_columns: pd.Index,
        other_columns: list[str],
    ) -> tuple[int, Measurement]:
        """Build one Measurement from a parsed APS data row.

        Args:
            row: One record from the parsed dataframe.
            axis: The shared diameter axis.
            bin_columns: Column labels holding the per-bin dN/dlogDp values.
            other_columns: Column labels carried verbatim into ``other``.

        Returns:
            The 0-based measurement key and its Measurement.

        Raises:
            ReaderNotImplementedError: If the row reports anything other than dN/dlogDp.
        """
        if row["Aerodynamic Diameter"] != self._REPORTED_DATA_TYPE:
            raise ReaderNotImplementedError(
                "Other types than dN/dlogDp are not yet implemented for TSI APS 3321."
            )

        scan_nr = int(row["Sample #"])
        time = datetime.strptime(
            f"{row['Date']} {row['Start Time']}", "%m/%d/%y %H:%M:%S"
        )
        delta_n_dlog_dp = np.array([row[col] for col in bin_columns], dtype=float)
        delta_n_dlog_dp[0] = 0.25  # https://github.com/Haisch-Group/pypana/issues/20

        number = SizeDistribution(
            quantity=Quantity.NUMBER,
            axis=axis,
            delta_dlogdp=delta_n_dlog_dp,
        )

        other_info = other_columns_to_dict(row, other_columns)
        other_info["median"] = row["Median(µm)"]
        other_info["mean"] = row["Mean(µm)"]
        other_info["mode"] = row["Mode(µm)"]
        other_info["geo_std_dev"] = row["Geo. Std. Dev."]

        measurement = Measurement(
            scan_nr=scan_nr,
            time=time,
            axis=axis,
            distributions={Quantity.NUMBER: number},
            other=other_info,
        )

        return scan_nr - 1, measurement

    def _read_bin_metadata(self, d_p_start_column: int, data: DataFrame) -> FloatArray:
        """Reads the metadata arrays that are constant for all measurements.

        Args:
            d_p_start_column (int): Column index of the start position of the bins.
            data (DataFrame): The parsed APS dataframe.

        Returns:
            The ``n + 1`` bin boundaries in meters.
        """
        d_p_file = (
            np.array(
                data.columns[
                    d_p_start_column : d_p_start_column + self._D_P_COLUMNS_COUNT
                ].str.replace("<", ""),
                dtype=float,
            )
            * self._SIZE_SCALING_FACTOR
        )

        delta_log = 1 / self._CHANNELS_PER_DECADE
        relative = np.arange(self._D_P_COLUMNS_COUNT) * delta_log
        offset = float(np.mean(np.log10(d_p_file[1:]) - relative[1:]))
        d_p = 10.0 ** (relative + offset)

        half_step = 10.0 ** (delta_log / 2)
        boundaries = np.asarray(
            np.append(d_p / half_step, d_p[-1] * half_step), dtype=float
        )
        boundaries[0] = 10 ** (
            np.log10(boundaries[1]) - 0.25
        )  # https://github.com/Haisch-Group/pypana/issues/20

        return boundaries
