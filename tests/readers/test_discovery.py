from collections.abc import Callable
from pathlib import Path

import pytest

from pypana.readers.base_instrument_reader import BaseInstrumentReader
from pypana.readers.discovery import SmartReader
from pypana.readers.exceptions.read_error import ReadError
from pypana.readers.exceptions.too_many_options import TooManyOptionsError
from readers.defs import (
    INSTRUMENT_READER_TEST_CASES,
    NON_EXISTING_FILE,
    NON_INSTRUMENT_FILE,
)


class TestSmartReader:
    """Test suite for the SmartReader class."""

    @pytest.mark.parametrize(
        "file_path, expected_reader_class", INSTRUMENT_READER_TEST_CASES
    )
    def test_discovers_correct_reader(
        self, file_path: Path, expected_reader_class: type[BaseInstrumentReader]
    ) -> None:
        smart_reader = SmartReader(file_path)
        smart_reader_from_str = SmartReader(str(file_path))

        assert type(smart_reader) is expected_reader_class
        assert type(smart_reader_from_str) is expected_reader_class

    def test_error_for_non_existing_file(self) -> None:
        path = Path(NON_EXISTING_FILE)

        with pytest.raises(ReadError, match=str(path)):
            SmartReader(path)

    def test_error_for_non_instrument_file(self) -> None:
        path = Path(NON_INSTRUMENT_FILE)

        with pytest.raises(ReadError, match=str(path)):
            SmartReader(path)

    def test_error_when_multiple_matches(
        self,
        base_instrument_reader_factory: Callable[
            [str, bool], type[BaseInstrumentReader]
        ],
    ) -> None:
        class_names = ["DummyReader1", "DummyReader2"]
        path = NON_INSTRUMENT_FILE

        base_instrument_reader_factory(class_names[0], True)
        base_instrument_reader_factory(class_names[1], True)

        with pytest.raises(TooManyOptionsError) as exec_info:
            SmartReader(path)

        error_msg = str(exec_info.value)

        assert class_names[0] in error_msg
        assert class_names[1] in error_msg
        assert str(path) in error_msg
