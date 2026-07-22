from pathlib import Path

import pytest

from pypana.readers.exceptions.read_error import ReadError
from pypana.readers.tsi.tsi_las3340a import TSILAS3340AInstrumentReader
from readers.defs import TSILAS3340A_FILE

VALID_SCAN_NR = 7000

MEASUREMENTS_IN_DIR = 1583
BINS = 99


class TestTSILAS3340AInstrumentReader:
    """Test suite for the TSILAS3340AInstrumentReader class."""

    def test_can_read_degenerated(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "empty_dir"
        input_dir.mkdir()
        assert TSILAS3340AInstrumentReader(input_dir).can_read(input_dir) is False

        test_file = input_dir / "degenerated_name"  # noqa: F841
        test_file.touch()
        assert TSILAS3340AInstrumentReader(input_dir).can_read(input_dir) is False

        test_file = test_file.rename(input_dir / "20240704_1")
        test_file.write_text("Degenerated content\n")

        with pytest.raises(ReadError):
            TSILAS3340AInstrumentReader.can_read(input_dir)

    def test_read(self) -> None:
        """Reads every time-resolved row across all files in the directory."""
        data = TSILAS3340AInstrumentReader(TSILAS3340A_FILE).read()

        assert len(data.measurements) == MEASUREMENTS_IN_DIR

    def test_scan_nr_encodes_file_and_row(self) -> None:
        """scan_nr is <file number> * 1000 + <row index>; file 7 -> 7000."""
        data = TSILAS3340AInstrumentReader(TSILAS3340A_FILE).read()

        assert VALID_SCAN_NR in data.measurements
        m = data.measurements[VALID_SCAN_NR]

        assert m.other["file"] == "20240704_7"
        assert m.n_bins == BINS
        assert m.diameter_type == "optical"
