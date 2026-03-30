from collections.abc import Generator
from pathlib import Path

import pytest

from pypana.readers.base_instrument_reader import BaseInstrumentReader


class TestBaseInstrumentReader:
    """Test suite for the BaseInstrumentReader abstract base class."""

    @pytest.fixture
    def dummy_reader_class(self) -> Generator[type[BaseInstrumentReader], None, None]:
        """Fixture that yields a dummy reader class that inherits from BaseInstrumentReader and cleans it up
        afterward.
        """

        class DummyReader(BaseInstrumentReader):
            _device_name = "DummyDevice"

            @classmethod
            def can_read(cls, path: Path | None) -> bool:
                return True

        yield DummyReader

        BaseInstrumentReader._deregister(DummyReader)  # noqa

    def test_subclass_is_registered(
        self, dummy_reader_class: type[BaseInstrumentReader]
    ) -> None:
        """Test that the subclass is registered automatically."""
        registered = BaseInstrumentReader.registered_readers()

        assert dummy_reader_class in registered
