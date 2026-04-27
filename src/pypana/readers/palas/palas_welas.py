"""Implementation of a Reader for the PALAS Welas.

This module provides the corresponding reader for the produced files of a PALAS Welas.
It provides the number concentration as dCn, while many others do directly as dN.
The pypana standard name is dN, therefore it is mapped here.

References:
    https://www.palas.de/en/product/welasdigital2000
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
from pypana.readers.palas.utils import _split_measurements


class PALASWelasInstrumentReader(BaseInstrumentReader):
    """Instrument reader for PALAS Welas."""

    _encoding = "iso-8859-1"
    _device_name = "PALAS Welas"
    _input_type = InputType.FILE

    _LINES_PER_MEASUREMENT = 42

    @classmethod
    def can_read(cls, path: Path) -> bool:
        """Checks whether a given path may include a PALAS Welas output file that can be read.

        Args:
            path: The path to the input file.

        Returns:
            Whether the read test succeeded when applying the PALAS Welas format.

        Raises:
            ReadError: If confident enough that the input is from PALAS Welas, but the data suggests otherwise.
                This may happen because the input files were manually edited in unsafe places or this package
                does not yet fully implement this device's formats.
                Note: the absence of ReadError in this method does not guarantee the input is parseable.
        """
        anchors: set = {"N analysed", "Xuk [µm]", "X [µm]", "Sum(dN) [P]"}
        found_anchors: set = set()

        if not path.is_file():
            return False

        with Path.open(path, "r", encoding=cls._encoding) as f:
            lines = f.readlines()

            for line in lines:
                for anchor in anchors:
                    if line.strip().startswith(anchor):
                        found_anchors.add(anchor)

            if len(anchors - found_anchors) > 0:
                return False

        return True

    def read(self) -> InstrumentData:
        """Read the given file and convert its data into the pypana format.

        Returns:
            InstrumentData: The pypana instrument on which further analysis can be conducted.

        Raises:
            ReadError: If an error occurs while reading the file.
        """
        measurements: dict = {}

        with Path.open(self._path, "r", encoding=self._encoding) as f:
            raw_measurements = _split_measurements(f.readlines())

        for scan_nr, raw_measurement in enumerate(raw_measurements, start=1):
            try:
                if not len(raw_measurement) == self._LINES_PER_MEASUREMENT:
                    raise ReadError(
                        message=f"Measurement {scan_nr} appears to be malformed",
                        path=self._path,
                    )

                measurements.update(
                    {scan_nr: self._read_measurement(scan_nr, raw_measurement)}
                )
            except (KeyError, AttributeError, ValueError) as e:
                raise ReadError(f"{e}") from e
            except ReadError as e:
                raise e

        if len(measurements) == 0:
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
            raw_measurement: The raw measurement from the PALAS Welas file.

        Returns:
            Measurement: The parsed data.
        """
        extracted_data: dict = {}
        other_extracted_data: dict = {}

        scan_time = datetime.strptime(raw_measurement[0][:19], "%Y/%m/%d %H:%M:%S")
        sample_time = raw_measurement[0].split("particle distribution")[1][:4].strip()

        other_extracted_data.update(
            {
                "sample_time": sample_time,
            }
        )

        for line in raw_measurement:
            if line.startswith("N analysed:"):
                other_extracted_data.update(
                    {
                        "N analysed": line.split("\t")[1].strip(),
                        "Sum(dCn)": line.split("\t")[4].strip(),
                    }
                )
            elif line.startswith("N total:"):
                extracted_data.update(
                    {
                        "n_total": line.split("\t")[1].strip(),
                    }
                )
                other_extracted_data.update(
                    {
                        "Sum(dCm)": line.split(":")[2].strip(),
                    }
                )
            elif line.startswith("M1,0"):
                extracted_data.update(
                    {
                        "mean": float(line.split("\t")[1])
                        * UnitScale.get_from_str(line),
                    }
                )
                other_extracted_data.update(
                    {
                        "surface_area": " ".join(line.split("\t")[4:6]),
                    }
                )
            elif line.startswith("M2,0"):
                other_extracted_data.update(
                    {
                        "second_moment": " ".join(line.split("\t")[1:3]),
                        "volume": " ".join(line.split("\t")[4:6]),
                    }
                )
            elif line.startswith("M3,0"):
                other_extracted_data.update(
                    {
                        "third_moment": float(line.split("\t")[1])
                        * UnitScale.get_from_str(line),
                    }
                )
            elif line.startswith("X50(N):"):
                extracted_data.update(
                    {
                        "median": float(line.split("\t")[1])
                        * UnitScale.get_from_str(line.split("\t")[2]),
                    }
                )

            elif line.startswith("Xuk"):
                extracted_data.update(
                    {
                        "d_p_lower": np.array(line.split("\t")[1:-1], dtype=float)
                        * UnitScale.get_from_str(line),
                    }
                )
            elif line.startswith("X [µm]"):
                extracted_data.update(
                    {
                        "d_p": np.array(line.split("\t")[1:-1], dtype=float)
                        * UnitScale.get_from_str(line),
                    }
                )
            elif line.startswith("Xok"):
                extracted_data.update(
                    {
                        "d_p_upper": np.array(line.split("\t")[1:-1], dtype=float)
                        * UnitScale.get_from_str(line),
                    }
                )
            elif line.startswith("dX [µm]"):
                extracted_data.update(
                    {
                        "delta_d_p": np.array(line.split("\t")[1:-1], dtype=float)
                        * UnitScale.get_from_str(line),
                    }
                )
            elif line.startswith("dCn [P/cm³]"):  # see comment in module docstring
                extracted_data.update(
                    {
                        "delta_n": np.array(line.split("\t")[1:-1], dtype=float)
                        * UnitScale.get_from_str(line),
                    }
                )

        delta_log_d_p = np.log10(extracted_data["d_p_upper"]) - np.log10(
            extracted_data["d_p_lower"]
        )
        bin_boundaries: FloatArray = np.append(
            extracted_data["d_p_lower"], extracted_data["d_p_upper"][-1]
        )

        return Measurement(
            scan_nr=scan_nr,
            time=scan_time,
            d_p=extracted_data["d_p"],
            delta_n=extracted_data["delta_n"],
            delta_d_p=extracted_data["delta_d_p"],
            delta_log_d_p=delta_log_d_p,
            bin_boundaries=bin_boundaries,
            median=extracted_data["median"],
            mean=extracted_data["mean"],
            other=other_extracted_data,
        )
