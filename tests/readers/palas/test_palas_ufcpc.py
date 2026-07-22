from pypana.data.defs import Quantity
from pypana.readers.palas.palas_ufcpc import PALASUFCPCInstrumentReader
from readers.defs import PALASUFCPC_FILE

MEASUREMENTS_IN_FILE = 30
TOTAL_SAMPLES = 11060
AUX_KEYS = (
    "concentration_10s_mean",
    "droplet_size_mean",
    "aerosol_flow",
    "temperature_condenser",
    "temperature_saturator",
    "pressure_absolute",
)


class TestPALASUFCPCInstrumentReader:
    """Test suite for the PALASUFCPCInstrumentReader class."""

    def test_read(self) -> None:
        """Splits the file into one Measurement per comment-delimited scan."""
        data = PALASUFCPCInstrumentReader(PALASUFCPC_FILE).read()
        assert len(data.measurements) == MEASUREMENTS_IN_FILE

    def test_is_time_series_only(self) -> None:
        """A UFCPC scan carries a Number TimeSeries and no size distribution."""
        data = PALASUFCPCInstrumentReader(PALASUFCPC_FILE).read()
        m = data.measurements[0]

        assert m.axis is None
        assert not m.distributions
        assert Quantity.NUMBER in m.series

    def test_all_rows_retained(self) -> None:
        """Every file row lands in exactly one scan's TimeSeries."""
        data = PALASUFCPCInstrumentReader(PALASUFCPC_FILE).read()
        total = 0

        for m in data.measurements.values():
            total += m.series[Quantity.NUMBER].n_samples

        assert total == TOTAL_SAMPLES

    def test_aux_arrays_aligned(self) -> None:
        """The auxiliary columns are stored aligned with the TimeSeries samples."""
        data = PALASUFCPCInstrumentReader(PALASUFCPC_FILE).read()
        m = data.measurements[0]
        n = m.series[Quantity.NUMBER].n_samples

        for key in AUX_KEYS:
            assert len(m.other[key]) == n
