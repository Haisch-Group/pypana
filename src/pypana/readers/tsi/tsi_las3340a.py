"""Implementation of a Reader for the TSI Laser Aerosol Spectrometer (LAS) 3340A.

This module provides the corresponding reader for the produced files of a TSI LAS 3340A.

References:
    https://tsi.com/products/particle-sizers/supermicron-capable-particle-sizer-spectrometers/laser-aerosol-spectrometer-(las)-3340a
"""

import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from pypana.config import UnitScale
from pypana.data.bin_axis import BinAxis
from pypana.data.defs import FloatArray, Quantity
from pypana.data.instrument_data import InstrumentData
from pypana.data.measurement import Measurement
from pypana.data.size_distribution import SizeDistribution
from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.base_reader import InputType
from pypana.readers.defs import IGNORED_FILES
from pypana.readers.exceptions.read_error import ReadError


class TSILAS3340AInstrumentReader(BaseInstrumentReader):
    """Instrument reader for TSI LAS 3340A."""

    _device_name = "TSI LAS 3340A"
    _input_type = InputType.DIRECTORY

    _META_COLUMNS = 15
    _SIZE_SCALE = UnitScale.NANO
    _DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S.%f %p"
    _SCAN_NR_STRIDE = 1_000

    # Reference conditions for the standard -> volumetric flow correction (TSI App. Note FLOW-004).
    _STANDARD_TEMPERATURE_K = 294.26
    _STANDARD_PRESSURE_KPA = 101.3

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
        files = [f for f in path.iterdir() if f.name not in IGNORED_FILES]

        if not files:
            return False

        for file in files:
            if not file_pattern.match(file.name):
                return False

            with Path.open(file, "r") as f:
                header = f.readline().split()

                if not all(a in header[:15] for a in anchors):
                    raise ReadError(
                        message="The column names do not match specified anchors. "
                        "Please open a GitHub issue if this is a false positive.",
                        path=file,
                    )

        return True

    def read(self) -> InstrumentData:
        """Read the given file and convert its data into the pypana format.

        Returns:
            InstrumentData: The pypana instrument on which further analysis can be conducted.

        Raises:
            ReadError: If an error occurs while reading the file.
        """
        files = sorted(
            (f for f in self._path.iterdir() if f.name not in IGNORED_FILES),
            key=lambda f: int(f.name.split("_")[1]),
        )

        measurements: dict[int, Measurement] = {}

        for file in files:
            try:
                file_number = int(file.name.split("_")[1])
                file_measurements = self._read_file(
                    file, file_number * self._SCAN_NR_STRIDE
                )

            except (FileNotFoundError, ValueError, KeyError, IndexError) as e:
                raise ReadError(f"{e}", path=file) from e

            measurements.update(file_measurements)

        if not measurements:
            raise ReadError(message="No valid measurements to import!", path=self._path)

        return InstrumentData(
            measurements=measurements,
            device_name=self._device_name,
            file_path=self._path,
            other_info={},
        )

    def _read_file(self, file: Path, base_scan_nr: int) -> dict[int, Measurement]:
        """Parses one LAS file into one Measurement per time-resolved row.

        Args:
            file: The single recording file to parse.
            base_scan_nr: The scan number assigned to this file's first row; subsequent rows
                  increment by one (kept below ``_SCAN_NR_STRIDE`` so files never collide).


        Returns:
            The measurements parsed from this file, keyed by their global scan number.
        """
        data = pd.read_table(file, sep="\t", header=0, engine="python")

        bin_columns = data.columns[self._META_COLUMNS :]
        d_lower = np.array(bin_columns, dtype=float) * self._SIZE_SCALE
        d_upper = (
            data.iloc[0, self._META_COLUMNS :].to_numpy(dtype=float) * self._SIZE_SCALE
        )
        bin_boundaries: FloatArray = np.append(d_lower, d_upper[-1])

        axis = BinAxis(
            bin_boundaries=bin_boundaries,
            midpoint="arithmetic",
            diameter_type="optical",
        )

        measurements: dict[int, Measurement] = {}

        # Row 0 is the units and upper-edge row
        for offset, (_, row) in enumerate(data.iloc[1:].iterrows()):
            time = datetime.strptime(
                f"{row['Date']} {row['Time']}", self._DATETIME_FORMAT
            )

            counts = row.iloc[self._META_COLUMNS :].to_numpy(dtype=float)
            volumetric_flow = self._volumetric_flow(
                standard_flow=float(row["Sample"]),
                temperature=float(row["Box"]),
                pressure=float(row["Pres."]),
            )
            delta_n = counts * (60.0 / float(row["Accum."])) / volumetric_flow

            number = SizeDistribution(
                quantity=Quantity.NUMBER, axis=axis, delta=delta_n
            )

            scan_nr = base_scan_nr + offset
            measurements[scan_nr] = Measurement(
                scan_nr=scan_nr,
                time=time,
                axis=axis,
                distributions={Quantity.NUMBER: number},
                other={"file": file.name, "subscan_nr": offset + 1},
            )

        return measurements

    @classmethod
    def _volumetric_flow(
        cls, standard_flow: float, temperature: float, pressure: float
    ) -> float:
        """Converts a standard (mass-controller) flow to the actual volumetric flow.

        Applies the ideal gas law to map a standard flow [scm³/min] to the volumetric flow
        [cm³/min] at the measurement temperature and pressure (TSI Application Note FLOW-004).

        Args:
            standard_flow: The reported standard aerosol flow [scm³/min].
            temperature: The measurement temperature [K] (the "Box" column).
            pressure: The measurement pressure [kPa] (the "Pres." column).

        Returns:
            The volumetric flow [cm³/min].
        """
        return (
            standard_flow
            * (temperature / cls._STANDARD_TEMPERATURE_K)
            * (cls._STANDARD_PRESSURE_KPA / pressure)
        )
