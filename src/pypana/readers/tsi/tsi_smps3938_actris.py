"""Readers for the ACTRIS Level 0 / Level 1 exports of the TSI SMPS 3938."""

from datetime import datetime, timedelta
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
from pypana.readers.exceptions.read_error import ReadError

_ENCODING = "iso-8859-1"
_TABLE_HEADER_START = "Start Date"
_CHANNELS_KEY = "Channels/Decade"
_INVALID_VALUE = 999.0
_SIZE_SCALING_FACTOR = UnitScale.NANO.value


def _can_read_actris(path: Path, table_header_anchor: str) -> bool:
    """Whether the file is an ACTRIS SMPS 3938 export of the variant carrying ``table_header_anchor``."""
    if not path.is_file():
        return False

    has_channels = False
    with Path.open(path, "r", encoding=_ENCODING) as f:
        for line in f:
            if line.startswith(_CHANNELS_KEY):
                has_channels = True

            elif line.startswith(_TABLE_HEADER_START):
                return has_channels and table_header_anchor in line

    return False


def _read_actris_metadata(path: Path) -> tuple[int, int, list[str]]:
    """Returns the table-header line index, the channel resolution, and the header fields."""
    channels_per_decade: int | None = None
    header_pos: int | None = None
    header_fields: list[str] | None = None

    with Path.open(path, "r", encoding=_ENCODING) as f:
        for i, line in enumerate(f):
            if line.startswith(_CHANNELS_KEY):
                channels_per_decade = int(line.split("\t")[1])

            elif line.startswith(_TABLE_HEADER_START):
                header_pos = i
                header_fields = line.rstrip("\n").split("\t")
                break

    if header_pos is None or header_fields is None:
        raise ReadError(
            message="The file does not contain the ACTRIS table header.", path=path
        )

    if channels_per_decade is None:
        raise ReadError(
            message="The file does not report 'Channels/Decade'.", path=path
        )

    return header_pos, channels_per_decade, header_fields


def _build_bin_boundaries(
    midpoints: FloatArray, channels_per_decade: int
) -> FloatArray:
    """Reconstructs an exact, constant-channels-per-decade boundary grid in meters (see tsi_smps3938)."""
    delta_log = 1 / channels_per_decade
    relative = np.arange(len(midpoints)) * delta_log
    offset = float(np.mean(np.log10(midpoints) - relative))
    d_p = 10.0 ** (relative + offset)
    half_step = 10.0 ** (delta_log / 2)

    return np.append(d_p / half_step, d_p[-1] * half_step)


def _decode_time(day_of_year: float, year: int) -> datetime:
    """ACTRIS fractional day-of-year (1-based) + year -> datetime."""
    return datetime(year, 1, 1) + timedelta(days=day_of_year - 1.0)


def _read_actris_file(
    path: Path,
    device_name: str,
    *,
    bin_count_index: int,
    data_block_offset_bins: int,
) -> InstrumentData:
    """Parses an ACTRIS SMPS 3938 export into the pypana format.

    Args:
        path: The input file.
        device_name: The device name to stamp on the InstrumentData.
        bin_count_index: Column index of the bin-count field ("# Bins" / "# of size bins").
        data_block_offset_bins: Number of n_bins-wide blocks between the bin-count column and the
            dN/dlogDp block (Level 0 has the per-row 'D Midpt.' block in between -> 1; Level 1 -> 0).
    """
    header_pos, channels_per_decade, header_fields = _read_actris_metadata(path)

    try:
        data = pd.read_table(
            path, header=header_pos, encoding=_ENCODING, skip_blank_lines=True
        )

        n_bins = int(float(str(data.iloc[0, bin_count_index])))
        data_start = bin_count_index + 1 + data_block_offset_bins * n_bins

        midpoints = (
            np.array([float(header_fields[data_start + k]) for k in range(n_bins)])
            * _SIZE_SCALING_FACTOR
        )
        bin_boundaries = _build_bin_boundaries(midpoints, channels_per_decade)
        axis = BinAxis(bin_boundaries=bin_boundaries.copy(), diameter_type="mobility")

    except (FileNotFoundError, ValueError, KeyError, IndexError) as e:
        raise ReadError(f"{e}", path=path) from e

    measurements: dict[int, Measurement] = {}

    for scan_nr in range(len(data)):
        try:
            row = data.iloc[scan_nr]
            time = _decode_time(float(row.iloc[0]), int(row.iloc[2]))

            values = np.array(
                [float(row.iloc[data_start + k]) for k in range(n_bins)], dtype=float
            )
            values = np.where(
                (values == _INVALID_VALUE) | np.isnan(values), 0.0, values
            )

            number = SizeDistribution(
                quantity=Quantity.NUMBER, axis=axis, delta_dlogdp=values
            )
            measurements[scan_nr] = Measurement(
                scan_nr=scan_nr,
                time=time,
                axis=axis,
                distributions={Quantity.NUMBER: number},
                other={},
            )

        except (ValueError, KeyError, IndexError) as e:
            raise ReadError(f"{e}", path=path) from e

    if not measurements:
        raise ReadError(message="No valid measurements to import!", path=path)

    return InstrumentData(
        measurements=measurements,
        device_name=device_name,
        file_path=path,
        other_info={"channels_per_decade": channels_per_decade},
    )


class TSISMPS3938ACTRISLevel0InstrumentReader(BaseInstrumentReader):
    """Instrument reader for the TSI SMPS 3938 ACTRIS Level 0 (raw) export."""

    _encoding = _ENCODING
    _device_name = "TSI SMPS 3938 (ACTRIS Level 0)"
    _input_type = InputType.FILE

    @classmethod
    def can_read(cls, path: Path) -> bool:
        """Whether the path is a TSI SMPS 3938 ACTRIS Level 0 export."""
        return _can_read_actris(path, table_header_anchor="D Midpt. 0")

    def read(self) -> InstrumentData:
        """Read the ACTRIS Level 0 file into the pypana format."""
        return _read_actris_file(
            self._path,
            self._device_name,
            bin_count_index=10,
            data_block_offset_bins=1,
        )


class TSISMPS3938ACTRISLevel1InstrumentReader(BaseInstrumentReader):
    """Instrument reader for the TSI SMPS 3938 ACTRIS Level 1 (inverted) export."""

    _encoding = _ENCODING
    _device_name = "TSI SMPS 3938 (ACTRIS Level 1)"
    _input_type = InputType.FILE

    @classmethod
    def can_read(cls, path: Path) -> bool:
        """Whether the path is a TSI SMPS 3938 ACTRIS Level 1 export."""
        return _can_read_actris(path, table_header_anchor="# of size bins")

    def read(self) -> InstrumentData:
        """Read the ACTRIS Level 1 file into the pypana format."""
        return _read_actris_file(
            self._path,
            self._device_name,
            bin_count_index=6,
            data_block_offset_bins=0,
        )
