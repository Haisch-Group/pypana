import numpy as np

from pypana.data.defs import Quantity
from pypana.readers.tsi.tsi_smps3938_actris import (
    TSISMPS3938ACTRISLevel0InstrumentReader,
    TSISMPS3938ACTRISLevel1InstrumentReader,
)
from readers.defs import TSISMPS3938_FILE1, TSISMPS3938_FILE2

MEASUREMENTS = 6
BINS = 192
CHANNELS_PER_DECADE = 64
INVALID_SENTINEL = 999.0


class TestTSISMPS3938ACTRISReaders:
    """Test suite for the ACTRIS Level 0 / Level 1 SMPS 3938 readers."""

    def test_read_level1(self) -> None:
        """Level 1 yields one mobility Measurement per row on the 64/decade grid."""
        data = TSISMPS3938ACTRISLevel1InstrumentReader(TSISMPS3938_FILE1).read()
        assert len(data.measurements) == MEASUREMENTS

        m = data.measurements[0]
        assert Quantity.NUMBER in m
        assert m.n_bins == BINS
        assert m.diameter_type == "mobility"
        assert np.allclose(m.delta_log_d_p, 1 / CHANNELS_PER_DECADE)

    def test_read_level0(self) -> None:
        """Level 0 parses the same grid from a different column layout."""
        data = TSISMPS3938ACTRISLevel0InstrumentReader(TSISMPS3938_FILE2).read()
        assert len(data.measurements) == MEASUREMENTS

        m = data.measurements[0]
        assert m.n_bins == BINS
        assert m.diameter_type == "mobility"

    def test_invalid_sentinel_is_zeroed(self) -> None:
        """The ACTRIS 999 invalid-bin sentinel is replaced by 0 (finite spectrum)."""
        data = TSISMPS3938ACTRISLevel1InstrumentReader(TSISMPS3938_FILE1).read()

        for m in data.measurements.values():
            values = m["dN/dlogdp"]

            assert not np.any(values == INVALID_SENTINEL)
            assert np.all(np.isfinite(values))
