"""Implementation of a Reader for the PALAS UFCPC.

This module provides the corresponding reader for the produced files of a PALAS UFCPC
(Ultrafine Condensation Particle Counter). The instrument is a counter: it reports a
particle number concentration over time, not a size distribution. Each file holds one
or more measurements that are delimited by a change of the user-set comment; each becomes
a Measurement carrying a single Number TimeSeries.

The file is headerless, tab-separated. Column order follows the PALAS CPC manual
(4597-de_V1.0_06/17, p. 23). The "1s Mean Particle Concentration / 1/cm³" column is the
number concentration and is already in the canonical unit (1/cm³).

References:
  https://www.palas.de/en/product/ufcpc50
"""

from pathlib import Path

import pandas as pd

from pypana.data.defs import Quantity
from pypana.data.instrument_data import InstrumentData
from pypana.data.measurement import Measurement
from pypana.data.time_series import TimeSeries
from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.base_reader import InputType
from pypana.readers.exceptions.read_error import ReadError


class PALASUFCPCInstrumentReader(BaseInstrumentReader):
    """Instrument reader for PALAS UFCPC."""

    _encoding = "iso-8859-1"
    _device_name = "PALAS UFCPC"
    _input_type = InputType.FILE

    _COLUMN_NAMES = [
        "Date",
        "Time",
        "Comment",
        "1s Mean Particle Concentration / 1/cm\u00b3",
        "10s Mean Particle Concentration / 1/cm\u00b3",
        "Mean Droplet size / \u00b5m",
        "Aerosol Flow / L/min",
        "Empty Field",
        "T Condenser / \u00b0C",
        "T Saturator / \u00b0C",
        "Operating Mode DSI",
        "Target Relative Humidity %",
        "Target Differential Pressure / Pa",
        "Actual Differential Pressure / Pa",
        "Power of Pump %",
        "Relative Humidity %",
        "Absolute Pressure / mbar",
        "T Aerosol Inlet / \u00b0C",
        "Error Notification",
        "Position of Valve in MSS 08",
    ]
    _AUX_COLUMNS = {
        "concentration_10s_mean": 4,
        "droplet_size_mean": 5,
        "aerosol_flow": 6,
        "temperature_condenser": 8,
        "temperature_saturator": 9,
        "pressure_absolute": 16,
    }

    _CONCENTRATION_COLUMN = "1s Mean Particle Concentration / 1/cm\u00b3"
    _DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p"
    _NAN_FIELD_INDEX = 7

    @classmethod
    def can_read(cls, path: Path) -> bool:
        """Checks whether a given path may include a PALAS UFCPC output file that can be read.

        Args:
            path: The path to the input file.

        Returns:
            Whether the read test succeeded when applying the PALAS UFCPC format.
        """
        if not path.is_file():
            return False

        checked = 0

        with Path.open(path, "r", encoding=cls._encoding) as f:
            for line in f:
                if not line.strip():
                    continue

                fields = line.rstrip("\n").split("\t")

                if len(fields) < len(cls._COLUMN_NAMES):
                    return False

                if not fields[1].strip().endswith(("AM", "PM")):
                    return False

                if fields[cls._NAN_FIELD_INDEX].strip() != "NaN":
                    return False

                checked += 1
                break

        return checked > 0

    def read(self) -> InstrumentData:
        """Read the given file and convert its data into the pypana format.

        Returns:
            InstrumentData: The pypana instrument on which further analysis can be conducted.

        Raises:
            ReadError: If an error occurs while reading the file.
        """
        try:
            data = pd.read_table(
                self._path,
                sep="\t",
                names=self._COLUMN_NAMES,
                index_col=False,
                engine="python",
                encoding=self._encoding,
            )

            timestamps = pd.to_datetime(
                data["Date"] + " " + data["Time"],
                format=self._DATETIME_FORMAT,
            )

            # A new measurement begins whenever the comment changes
            scan_id = (data["Comment"] != data["Comment"].shift()).cumsum()

        except (FileNotFoundError, ValueError, KeyError) as e:
            raise ReadError(f"{e}", path=self._path) from e

        measurements: dict[int, Measurement] = {}

        for scan_nr, (_, rows) in enumerate(data.groupby(scan_id, sort=False)):
            try:
                scan_timestamps = timestamps.loc[rows.index]

                number = TimeSeries(
                    quantity=Quantity.NUMBER,
                    timestamps=scan_timestamps.to_numpy(),
                    values=rows[self._CONCENTRATION_COLUMN].to_numpy(dtype=float),
                )

                other: dict[str, object] = {"comment": rows["Comment"].iloc[0]}
                for key, column_index in self._AUX_COLUMNS.items():
                    other[key] = rows.iloc[:, column_index].to_numpy(dtype=float)

                measurements[scan_nr] = Measurement(
                    scan_nr=scan_nr,
                    time=scan_timestamps.iloc[0].to_pydatetime(),
                    series={Quantity.NUMBER: number},
                    other=other,
                )

            except (ValueError, KeyError) as e:
                raise ReadError(f"{e}", path=self._path) from e

        if not measurements:
            raise ReadError(message="No valid measurements to import!", path=self._path)

        return InstrumentData(
            measurements=measurements,
            device_name=self._device_name,
            file_path=self._path,
            other_info={},
        )
