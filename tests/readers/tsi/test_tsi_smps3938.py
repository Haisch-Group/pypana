import numpy as np

from pypana.data.defs import Quantity
from pypana.readers.tsi.tsi_smps3938 import TSISMPS3938InstrumentReader
from readers.defs import TSISMPS3938_FILE3, TSISMPS3938_FILE4, TSISMPS3938_FILE5

CHANNELS_PER_DECADE = 64
TOTAL_CONC_COLUMN = "Total Conc. (#/cm\u00b3)"


class TestTSISMPS3938InstrumentReader:
    """Test suite for the native TSISMPS3938InstrumentReader."""

    def test_read_counts(self) -> None:
        """Each native fixture yields one Measurement per row."""
        for file_path, expected in (
            (TSISMPS3938_FILE3, 6),
            (TSISMPS3938_FILE4, 23),
            (TSISMPS3938_FILE5, 14),
        ):
            data = TSISMPS3938InstrumentReader(file_path).read()
            assert len(data.measurements) == expected

        """A scan stores a mobility dN/dlogdp distribution on an exact 64/decade grid."""
        data = TSISMPS3938InstrumentReader(TSISMPS3938_FILE5).read()
        m = data.measurements[0]

        assert Quantity.NUMBER in m
        assert m.diameter_type == "mobility"
        assert np.allclose(m.delta_log_d_p, 1 / CHANNELS_PER_DECADE)

    def test_total_matches_reported(self) -> None:
        """The integrated total matches the instrument's own reported Total Conc."""
        data = TSISMPS3938InstrumentReader(TSISMPS3938_FILE5).read()
        m = max(data.measurements.values(), key=lambda x: x.total)

        reported = float(m.other[TOTAL_CONC_COLUMN])
        assert np.isclose(m.total, reported, rtol=1e-3)
