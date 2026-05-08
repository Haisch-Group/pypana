from pathlib import Path

import pytest

from pypana.readers.exceptions.read_error import ReadError
from pypana.readers.tsi.tsi_las3340a import TSILAS3340AInstrumentReader


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
