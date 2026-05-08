from collections.abc import Callable, Generator
from pathlib import Path

import pytest

from pypana.data.instrument_data import InstrumentData
from pypana.readers.base_instrument_reader import BaseInstrumentReader


@pytest.fixture(scope="function")
def base_instrument_reader_factory() -> Generator[
    Callable[..., type[BaseInstrumentReader]], None, None
]:
    """Factory to create unique BaseInstrumentReader classes."""
    created_classes: list = []

    def _create_reader(
        name: str, can_read_val: bool = True
    ) -> type[BaseInstrumentReader]:
        class DynamicReader(BaseInstrumentReader):
            _device_name = name

            @classmethod
            def can_read(cls, path: Path | None) -> bool:
                return can_read_val

            def read(self) -> InstrumentData:
                raise NotImplementedError()

        DynamicReader.__name__ = name
        DynamicReader.__qualname__ = name

        created_classes.append(DynamicReader)
        return DynamicReader

    yield _create_reader

    for cls in created_classes:
        BaseInstrumentReader._deregister(cls)  # noqa

    created_classes.clear()
