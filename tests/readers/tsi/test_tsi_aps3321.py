import numpy as np

from pypana.data.defs import Quantity
from pypana.readers.tsi.tsi_aps3321 import TSIAPS3321InstrumentReader
from readers.defs import TSIAPS3321_FILE1, TSIAPS3321_FILE2

MEASUREMENTS_FILE1 = 32
MEASUREMENTS_FILE2 = 107
BINS = 52
CHANNELS_PER_DECADE = 32


class TestTSIAPS3321InstrumentReader:
    """Test suite for the TSIAPS3321InstrumentReader class."""

    def test_read_file1(self) -> None:
        """Reads all scans from the first APS 3321 fixture."""
        data = TSIAPS3321InstrumentReader(TSIAPS3321_FILE1).read()
        assert len(data.measurements) == MEASUREMENTS_FILE1

    def test_read_file2(self) -> None:
        """Reads all scans from the second APS 3321 fixture."""
        TSIAPS3321InstrumentReader(TSIAPS3321_FILE2).read()

    def test_measurement_fields(self) -> None:
        """A parsed scan stores an aerodynamic dN/dlogdp distribution on an exact grid."""
        data = TSIAPS3321InstrumentReader(TSIAPS3321_FILE1).read()
        m = data.measurements[0]

        assert Quantity.NUMBER in m
        assert m.n_bins == BINS
        assert m.diameter_type == "aerodynamic"
        assert len(m["dN/dlogdp"]) == BINS
        assert np.allclose(m.delta_log_d_p[1:], 1 / CHANNELS_PER_DECADE)
        assert np.all(np.diff(m.bin_boundaries) > 0)
