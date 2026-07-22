"""Implementation of a Reader for the TSI Condensation Particle Counter 3775.

This module provides the corresponding reader for the produced files of a TSI CPC 3775.

References:
    https://tsi.com/discontinued-products/condensation-particle-counter-3775
"""

import re
from collections.abc import Hashable
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from pypana.data.defs import Quantity
from pypana.data.instrument_data import InstrumentData
from pypana.data.measurement import Measurement
from pypana.data.time_series import TimeSeries
from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.base_reader import InputType
from pypana.readers.exceptions.read_error import ReadError
from pypana.readers.tsi.utils import is_basic_tsi_format_file


class TSICPC3775InstrumentReader(BaseInstrumentReader):
    """Instrument reader for TSI CPC 3775."""

    _device_name = "TSI CPC 3775"
    _encoding = "iso-8859-1"
    _input_type = InputType.FILE

    _HEADER_START = (
        "Sample #\tStart Date\tStart Time\tSample Length\tAveraging Interval (s)"
    )
    _DATETIME_FORMAT = "%m/%d/%y %H:%M:%S"

    _CONC_COLUMN_PATTERN = re.compile(r"\[\d+(\.\d+)?\]\s+Conc")
    _COUNT_COLUMN_PATTERN = re.compile(r"\[\d+(\.\d+)?\]\s+Count")

    _OTHER_COLUMNS = {
        "instrument_id": "Instrument ID",
        "instrument_errors": "Instrument Errors",
        "conc_mean": "Conc Mean",
        "conc_min": "Conc Min",
        "conc_max": "Conc Max",
        "conc_std_dev": "Conc Std Dev",
    }

    @classmethod
    def can_read(cls, path: Path) -> bool:
        """Checks whether a given path may include a TSI CPC 3775 output file that can be read.

        Args:
            path: The path to the input file.

        Returns:
            Whether the read test succeeded when applying the TSI CPC 3775 format.

        Raises:
            ReadError: If confident enough that the input is from TSI CPC 3775, but the data suggests otherwise.
                This may happen because the input files were manually edited in unsafe places or this package
                does not yet fully implement this device's formats.
                Note: the absence of ReadError in this method does not guarantee the input is parseable.
        """
        anchors = ["Sample File", "Model\t3775", cls._HEADER_START]

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
        other_info: dict[Hashable, Any] = {}
        header_line = 0

        try:
            with Path.open(self._path, "r", encoding=self._encoding) as f:
                for i, line in enumerate(f):
                    if line.startswith("Sample File"):
                        other_info["sample_file"] = line[12:].strip()
                    elif line.startswith("Model"):
                        other_info["model"] = line[6:].strip()
                    elif line.startswith(self._HEADER_START):
                        header_line = i
                        break

        except (FileNotFoundError, UnicodeDecodeError) as e:
            raise ReadError(f"{e}", path=self._path) from e

        if header_line == 0:
            raise ReadError(
                message="The file does not contain the start of the TSI CPC 3775 header.",
                path=self._path,
            )

        try:
            data = pd.read_table(
                self._path,
                sep="\t",
                skiprows=header_line,
                index_col=False,
                encoding=self._encoding,
            )

            conc_columns = [
                c for c in data.columns if self._CONC_COLUMN_PATTERN.match(c)
            ]
            count_columns = [
                c for c in data.columns if self._COUNT_COLUMN_PATTERN.match(c)
            ]

            if not conc_columns:
                raise ReadError(
                    message="No concentration columns found.", path=self._path
                )

        except (FileNotFoundError, ValueError) as e:
            raise ReadError(f"{e}", path=self._path) from e

        measurements: dict[int, Measurement] = {}

        for row in data.to_dict("records"):
            try:
                scan_nr, measurement = self._row_to_measurement(
                    row, conc_columns, count_columns
                )
                measurements[scan_nr - 1] = measurement

            except (ValueError, KeyError) as e:
                raise ReadError(f"{e}", path=self._path) from e

        if not measurements:
            raise ReadError(message="No valid measurements to import!", path=self._path)

        return InstrumentData(
            measurements=measurements,
            device_name=self._device_name,
            file_path=self._path,
            other_info=other_info,
        )

    def _row_to_measurement(
        self,
        row: dict[Hashable, Any],
        conc_columns: list[str],
        count_columns: list[str],
    ) -> tuple[int, Measurement]:
        """Build one Measurement from a parsed CPC sample row.

        Args:
            row: One record from the parsed dataframe.
            conc_columns: Column labels holding the per-interval concentrations.
            count_columns: Column labels holding the per-interval raw counts (may be empty).

        Returns:
            The 1-based sample number and its Measurement.
        """
        scan_nr = int(row["Sample #"])
        start = datetime.strptime(
            f"{row['Start Date']} {row['Start Time']}", self._DATETIME_FORMAT
        )
        interval = int(row["Averaging Interval (s)"])
        sample_length = int(row["Sample Length"])

        # Samples shorter than the widest row in the file leave the trailing columns empty
        n_samples = min(sample_length // interval, len(conc_columns))

        timestamps = np.datetime64(start, "ms") + np.arange(n_samples) * np.timedelta64(
            interval, "s"
        )

        number = TimeSeries(
            quantity=Quantity.NUMBER,
            timestamps=timestamps,
            values=np.array([row[c] for c in conc_columns[:n_samples]], dtype=float),
        )

        other: dict[Hashable, Any] = {
            "title": "" if pd.isna(row["Title"]) else str(row["Title"]),
            "sample_length": sample_length,
            "averaging_interval": interval,
        }
        for key, column in self._OTHER_COLUMNS.items():
            other[key] = row[column]

        if count_columns:
            other["counts"] = np.array(
                [row[c] for c in count_columns[:n_samples]], dtype=float
            )

        measurement = Measurement(
            scan_nr=scan_nr,
            time=start,
            series={Quantity.NUMBER: number},
            other=other,
        )

        return scan_nr, measurement
