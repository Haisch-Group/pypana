"""Implementation of a Reader for the PALAS U-SMPS.

This module provides the corresponding reader for the produced files of a PALAS U-SMPS.
The U-SMPS reports number concentration per bin as dCn (= dN per bin) in three
processing stages: raw, inverted, and inverted + diffusion-corrected. The most
processed stage (dCn_inv_diff) is mapped to the pypana standard delta_n.

References:
    https://www.palas.de/en/product/usmps
"""

from datetime import datetime
from pathlib import Path

import numpy as np

from pypana.config import UnitScale
from pypana.data.instrument_data import InstrumentData
from pypana.data.measurement import FloatArray, Measurement
from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.base_reader import InputType
from pypana.readers.exceptions.read_error import ReadError
from pypana.readers.palas.utils import _split_usmps_measurements


class PALASUSMPSInstrumentReader(BaseInstrumentReader):
    """Instrument reader for PALAS U-SMPS."""

    _encoding = "iso-8859-1"
    _device_name = "PALAS U-SMPS"
    _input_type = InputType.FILE

    _LINES_PER_MEASUREMENT = 7
    _SIZE_SCALE = UnitScale.NANO  # U-SMPS reports sizes in nm (range 4-1200 nm)
    _ROW_ANCHORS = {"Xu", "Xo", "X", "dCn_raw", "dCn_inv", "dCn_inv_diff"}

    @classmethod
    def can_read(cls, path: Path) -> bool:
        """Checks whether a given path may include a PALAS U-SMPS output file that can be read.

        Current checks include:
            - whether the path is a file
            - all expected data row labels (Xu, Xo, X, dCn_raw, dCn_inv, dCn_inv_diff) are present.

        Args:
            path: The path to the input file.

        Returns:
            Whether the read test succeeded when applying the PALAS U-SMPS format.
        """
        found: set[str] = set()

        if not path.is_file():
            return False

        with Path.open(path, "r", encoding=cls._encoding) as f:
            for line in f:
                fields = line.split("\t")
                if len(fields) > 1 and fields[1].strip() in cls._ROW_ANCHORS:
                    found.add(fields[1].strip())

        return cls._ROW_ANCHORS.issubset(found)

    def read(self) -> InstrumentData:
        """Read the given file and convert its data into the pypana format.

        Returns:
            InstrumentData: The pypana instrument on which further analysis can be conducted.

        Raises:
            ReadError: If an error occurs while reading the file.
        """
        with Path.open(self._path, "r", encoding=self._encoding) as f:
            raw_measurements = _split_usmps_measurements(f.readlines())

        measurements: dict[int, Measurement] = {}

        for scan_nr, raw_measurement in enumerate(raw_measurements):
            try:
                if len(raw_measurement) != self._LINES_PER_MEASUREMENT:
                    raise ReadError(
                        message=f"Measurement {scan_nr} appears to be malformed",
                        path=self._path,
                    )

                measurements[scan_nr] = self._read_measurement(scan_nr, raw_measurement)
            except (KeyError, IndexError, ValueError) as e:
                raise ReadError(f"{e}", path=self._path) from e

        if not measurements:
            raise ReadError(message="No valid measurements to import!", path=self._path)

        return InstrumentData(
            measurements=measurements,
            device_name=self._device_name,
            file_path=self._path,
            other_info={},
        )

    def _read_measurement(
        self, scan_nr: int, raw_measurement: list[str]
    ) -> Measurement:
        """Parses a single measurement into the pypana format.

        Args:
            scan_nr: The scan number to assign to this measurement.
            raw_measurement: The raw measurement block from the PALAS U-SMPS file.

        Returns:
            Measurement: The parsed data.
        """
        params = raw_measurement[0].split("\t")
        rows = {
            line.split("\t")[1].strip(): line.split("\t")[2:]
            for line in raw_measurement[1:]
        }

        scan_time = datetime.strptime(
            f"{params[0].strip()} {params[1].strip()}", "%m/%d/%Y %I:%M %p"
        )

        d_lower = np.array(rows["Xu"], dtype=float) * self._SIZE_SCALE
        d_upper = np.array(rows["Xo"], dtype=float) * self._SIZE_SCALE
        d_p = np.array(rows["X"], dtype=float) * self._SIZE_SCALE

        delta_log_d_p = np.log10(d_upper) - np.log10(d_lower)
        bin_boundaries: FloatArray = np.append(d_lower, d_upper[-1])

        return Measurement(
            scan_nr=scan_nr,
            time=scan_time,
            d_p=d_p,
            delta_n=np.array(rows["dCn_inv_diff"], dtype=float),
            delta_d_p=d_upper - d_lower,
            delta_log_d_p=delta_log_d_p,
            bin_boundaries=bin_boundaries,
            other={"comment": params[2].strip()},
        )
