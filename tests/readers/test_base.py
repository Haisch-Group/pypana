from collections.abc import Callable

from pypana.readers.base_instrument_reader import BaseInstrumentReader


class TestBaseInstrumentReader:
    """Test suite for the BaseInstrumentReader abstract base class."""

    def test_subclass_is_registered(
        self,
        base_instrument_reader_factory: Callable[
            [str, bool], type[BaseInstrumentReader]
        ],
    ) -> None:
        """Test that the subclass is registered automatically."""
        dummy_reader = base_instrument_reader_factory("DummyReader", True)
        registered = BaseInstrumentReader.registered_readers()

        assert dummy_reader in registered
