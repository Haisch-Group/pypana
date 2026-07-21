import numpy as np

from pypana.data.defs import Quantity
from pypana.readers.tsi.tsi_cpc3775 import TSICPC3775InstrumentReader
from readers.defs import TSICPC3775_FILE1, TSICPC3775_FILE2, TSICPC3775_FILE3

MEASUREMENTS_FILE1 = 86
MEASUREMENTS_FILE2 = 17
MEASUREMENTS_FILE3 = 12
SAMPLES_PER_MEASUREMENT_FILE1 = 60
TOTAL_SAMPLES_FILE3 = 4804
LENGTHS_FILE3_START = (544, 544, 476, 360)


class TestTSICPC3775InstrumentReader:
    """Test suite for the TSICPC3775InstrumentReader class."""

    def test_read_file1(self) -> None:
        """Reads all samples from the fixture without count columns."""
        data = TSICPC3775InstrumentReader(TSICPC3775_FILE1).read()
        assert len(data.measurements) == MEASUREMENTS_FILE1

    def test_read_file2(self) -> None:
        """Reads all samples from the fixture with interleaved count columns."""
        data = TSICPC3775InstrumentReader(TSICPC3775_FILE2).read()
        assert len(data.measurements) == MEASUREMENTS_FILE2

    def test_is_time_series_only(self) -> None:
        """A CPC sample carries a Number TimeSeries and no size distribution."""
        data = TSICPC3775InstrumentReader(TSICPC3775_FILE1).read()
        m = data.measurements[0]

        assert m.axis is None
        assert not m.distributions
        assert Quantity.NUMBER in m.series
        assert m.series[Quantity.NUMBER].n_samples == SAMPLES_PER_MEASUREMENT_FILE1

    def test_timestamps_follow_averaging_interval(self) -> None:
        """Sample timestamps start at the row's start time and step by the averaging interval."""
        data = TSICPC3775InstrumentReader(TSICPC3775_FILE1).read()
        m = data.measurements[0]
        series = m.series[Quantity.NUMBER]

        assert series.timestamps[0] == np.datetime64(m.time, "ms")
        assert np.all(np.diff(series.timestamps) == np.timedelta64(1, "s"))

    def test_variable_sample_lengths(self) -> None:
        """Rows shorter than the widest one only yield their own number of samples."""
        data = TSICPC3775InstrumentReader(TSICPC3775_FILE3).read()
        assert len(data.measurements) == MEASUREMENTS_FILE3

        lengths = tuple(
            data.measurements[i].series[Quantity.NUMBER].n_samples
            for i in range(len(LENGTHS_FILE3_START))
        )
        assert lengths == LENGTHS_FILE3_START

        total = sum(
            m.series[Quantity.NUMBER].n_samples for m in data.measurements.values()
        )
        assert total == TOTAL_SAMPLES_FILE3

    def test_counts_aligned_when_present(self) -> None:
        """The raw count columns are stored aligned with the TimeSeries samples."""
        data = TSICPC3775InstrumentReader(TSICPC3775_FILE2).read()
        m = data.measurements[0]

        assert len(m.other["counts"]) == m.series[Quantity.NUMBER].n_samples

    def test_counts_absent_without_count_columns(self) -> None:
        """Files exported without count columns store no counts array."""
        data = TSICPC3775InstrumentReader(TSICPC3775_FILE1).read()
        assert "counts" not in data.measurements[0].other
