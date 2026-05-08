from pypana.readers.palas.palas_welas import PALASWelasInstrumentReader
from readers.defs import PALASWELAS_FILE1

MEASUREMENTS_IN_FILE = 14


class TestPalasWelasInstrumentReader:
    """Test suite for the PalasWelasInstrumentReader class."""

    def test_read(self) -> None:
        """Tests that the Palas Welas Instrument Reader can read a Palas Welas file."""
        data = PALASWelasInstrumentReader(PALASWELAS_FILE1).read()

        assert len(data.measurements) == MEASUREMENTS_IN_FILE
