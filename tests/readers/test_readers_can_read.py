from pathlib import Path

import pytest

from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.tsi.tsi_las3340a import TSILAS3340AInstrumentReader

EXAMPLE_FILES_DIR = Path(__file__).resolve().parents[2] / "ExampleFiles"
TEST_CASES = [
    (EXAMPLE_FILES_DIR / "20240704_TSI_LAS3340A", TSILAS3340AInstrumentReader),
]


@pytest.mark.parametrize("file_path, expected_reader_class", TEST_CASES)
@pytest.mark.parametrize("reader_class", BaseInstrumentReader.registered_readers())
def test_can_read_example_exclusive(
    file_path: Path,
    expected_reader_class: type[BaseInstrumentReader],
    reader_class: type[BaseInstrumentReader],
) -> None:
    assert file_path.exists(), f"Test file not found: {file_path}"

    instance = reader_class(file_path)
    result = instance.can_read(file_path)

    if reader_class is expected_reader_class:
        assert result is True, (
            f"Expected {reader_class.__name__} to successfully read '{file_path.name}'"
        )
    else:
        assert result is False, (
            f"Expected {reader_class.__name__} to reject '{file_path.name}'"
        )
