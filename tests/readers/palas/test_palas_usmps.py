import numpy as np

from pypana.readers.palas.palas_usmps import PALASUSMPSInstrumentReader
from readers.defs import PALASUSMPS_FILE1

MEASUREMENTS_IN_FILE = 45

# device size range is 4-1200 nm, generous margins
MIN_EXPECTED_D_P = 1e-9
MAX_EXPECTED_D_P = 1.3e-6


class TestPalasUSMPSInstrumentReader:
    """Test suite for the PALASUSMPSInstrumentReader class."""

    def test_read(self) -> None:
        """Tests that the PALAS U-SMPS Instrument Reader can read a PALAS U-SMPS file."""
        data = PALASUSMPSInstrumentReader(PALASUSMPS_FILE1).read()

        assert len(data.measurements) == MEASUREMENTS_IN_FILE

    def test_measurement_fields(self) -> None:
        """Tests that a parsed measurement has consistent, physically sensible fields."""
        data = PALASUSMPSInstrumentReader(PALASUSMPS_FILE1).read()
        measurement = data.measurements[0]

        n_bins = len(measurement.d_p)

        assert len(measurement["dN"]) == n_bins
        assert len(measurement.delta_d_p) == n_bins
        assert len(measurement.delta_log_d_p) == n_bins
        assert len(measurement.bin_boundaries) == n_bins + 1

        assert np.all(measurement.d_p > MIN_EXPECTED_D_P)
        assert np.all(measurement.d_p < MAX_EXPECTED_D_P)

        assert np.all(np.diff(measurement.bin_boundaries) > 0)
        assert np.all(measurement.delta_d_p > 0)
