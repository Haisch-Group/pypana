"""Implementation of a Reader for the TSI Aerodynamic Particle Sizer Spectrometer 3321.

This module provides the corresponding reader for the produced files of a TSI APS 3321.

References:
    https://tsi.com/products/particle-sizers/supermicron-capable-particle-sizer-spectrometers/aerodynamic-particle-sizer-aps-3321
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from pandas import DataFrame

from pypana.config import UnitScale
from pypana.data.instrument_data import InstrumentData
from pypana.data._measurement import FloatArray, Measurement
from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.base_reader import InputType
from pypana.readers.exceptions.read_error import ReaderNotImplementedError, ReadError
from pypana.readers.tsi.utils import is_basic_tsi_format_file
from pypana.readers.utils import other_columns_to_dict
from pypana.utils.measurement_data_type import MeasurementDataType


class TSIAPS3321InstrumentReader(BaseInstrumentReader):
    """Instrument reader for TSI APS 3321."""

    _device_name = "TSI APS 3321"
    _encoding = "iso-8859-1"
    _input_type = InputType.FILE

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

            d_p, delta_d_p, delta_log_d_p, bin_boundaries = self._read_bin_metadata(
                d_p_start_column, data
            )

            bin_columns = data.columns[
                d_p_start_column : d_p_start_column + self._D_P_COLUMNS_COUNT
            ]
        except (FileNotFoundError, ValueError) as e:
            raise ReadError(f"{e}") from e

        float_cols = data.select_dtypes(include=["float"]).columns
        data[float_cols] = data[float_cols].astype(float)

        measurements: dict[int, Measurement] = {}

        for row in data.to_dict("records"):
            try:
                if row["Aerodynamic Diameter"] != MeasurementDataType.dndlogdp.value:
                    raise ReaderNotImplementedError(
                        "Other types than dN/dlogDp are not yet implemented for TSI APS 3321."
                    )

                scan_nr = int(row["Sample #"])
                time = datetime.strptime(
                    f"{row['Date']} {row['Start Time']}", "%m/%d/%y %H:%M:%S"
                )
                delta_n_dlog_dp: FloatArray = np.array(
                    [row[col] for col in bin_columns],
                    dtype=float,
                )
                median = row["Median(µm)"]
                mean = row["Mean(µm)"]
                geo_mean = row["Geo. Mean(µm)"]
                mode = row["Mode(µm)"]
                geo_std_dev = row["Geo. Std. Dev."]

                other_info = other_columns_to_dict(
                    row,
                    data.columns[
                        d_p_start_column + self._D_P_COLUMNS_COUNT : -6
                    ].to_list(),
                )

                measurement = Measurement(
                    scan_nr=scan_nr,
                    time=time,
                    d_p=d_p.copy(),
                    delta_d_p=delta_d_p.copy(),
                    delta_log_d_p=delta_log_d_p.copy(),
                    delta_n_dlog_dp=delta_n_dlog_dp,
                    bin_boundaries=bin_boundaries.copy(),
                    median=median,
                    mean=mean,
                    geo_mean=geo_mean,
                    mode=mode,
                    geo_std_dev=geo_std_dev,
                    other=other_info,
                )
                measurements[scan_nr - 1] = measurement  # 0-based indexing
            except (ValueError, AttributeError, KeyError) as e:
                raise ReadError(f"{e}") from e
            except ReadError as e:
                raise e

        other_info = {
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

    def _read_bin_metadata(
        self, d_p_start_column: int, data: DataFrame
    ) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
        """Reads the metadata arrays that are constant for all measurements.

        Args:
            d_p_start_column (int): Column index of the start position of the bins.
            data (DataFrame): The original dataframe with all metadata.

        Returns:
            tuple[FloatArray, FloatArray, FloatArray]: A tuple containing:
                - d_p, delta_d_p, delta_log_d_p
        """
        d_p = (
            np.array(
                data.columns[
                    d_p_start_column : d_p_start_column + self._D_P_COLUMNS_COUNT
                ].str.replace("<", ""),
                dtype=float,
            )
            * self._SIZE_SCALING_FACTOR
        )
        delta_log_d_p_constant = 1 / self._CHANNELS_PER_DECADE
        delta_log_d_p = np.full(self._D_P_COLUMNS_COUNT, delta_log_d_p_constant)

        logarithmic_bin_step = 10 ** (delta_log_d_p_constant / 2)

        # re-center lowest bin (machine cut off) to look like normal bin, but may be later cut off
        d_p[0] = d_p[1] / (logarithmic_bin_step**2)

        d_p_lower = d_p / logarithmic_bin_step
        d_p_upper = d_p * logarithmic_bin_step
        delta_d_p = d_p_upper - d_p_lower
        bin_boundaries = np.append(d_p_lower, d_p_upper[-1])

        return d_p, delta_d_p, delta_log_d_p, bin_boundaries
