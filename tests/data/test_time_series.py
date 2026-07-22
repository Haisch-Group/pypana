"""Tests for pypana.data.time_series.TimeSeries."""

import numpy as np
import pytest
from hypothesis import given, settings

from data.strategies import series_measurement, time_series
from pypana.data.defs import Quantity
from pypana.data.measurement import Measurement
from pypana.data.time_series import TimeSeries


class TestTimeSeriesStats:
    """Cached statistics over the sampled values."""

    @settings(max_examples=10)
    @given(ts=time_series())
    def test_n_samples_matches_values(self, ts: TimeSeries) -> None:
        """`n_samples` equals the number of stored values."""
        assert ts.n_samples == ts.values.size

    @settings(max_examples=10)
    @given(ts=time_series())
    def test_stats_match_numpy(self, ts: TimeSeries) -> None:
        """mean/vmin/vmax/std mirror numpy over the values."""
        assert ts.mean == pytest.approx(float(np.nanmean(ts.values)))
        assert ts.vmin == pytest.approx(float(np.nanmin(ts.values)))
        assert ts.vmax == pytest.approx(float(np.nanmax(ts.values)))
        assert ts.std == pytest.approx(float(np.nanstd(ts.values)))


class TestTimeSeriesTime:
    """Elapsed-time and duration helpers."""

    @settings(max_examples=10)
    @given(ts=time_series())
    def test_elapsed_starts_at_zero(self, ts: TimeSeries) -> None:
        """One elapsed value per sample, the first being zero."""
        elapsed = ts.elapsed()

        assert elapsed.size == ts.n_samples
        assert elapsed[0] == 0.0

    @settings(max_examples=10)
    @given(ts=time_series())
    def test_elapsed_strictly_increasing(self, ts: TimeSeries) -> None:
        """Elapsed time rises monotonically (timestamps strictly increase)."""
        assert np.all(np.diff(ts.elapsed()) > 0)

    @settings(max_examples=10)
    @given(ts=time_series())
    def test_elapsed_unit_scaling(self, ts: TimeSeries) -> None:
        """Seconds are milliseconds divided by 1000."""
        np.testing.assert_allclose(ts.elapsed("s") * 1000.0, ts.elapsed("ms"))

    @settings(max_examples=10)
    @given(ts=time_series())
    def test_duration_matches_last_elapsed(self, ts: TimeSeries) -> None:
        """Duration equals the last sample's elapsed time."""
        assert ts.duration("s") == pytest.approx(float(ts.elapsed("s")[-1]))


class TestTimeSeriesValidation:
    """Construction-time guards (explicit bad inputs)."""

    @staticmethod
    def _times(n: int) -> np.ndarray:
        start = np.datetime64("2026-05-29T12:00:00", "ms")

        return start + np.arange(n).astype("timedelta64[s]")

    def test_length_mismatch_rejected(self) -> None:
        """Timestamps and values must align."""
        with pytest.raises(ValueError, match="same length"):
            TimeSeries(
                quantity=Quantity.NUMBER,
                timestamps=self._times(3),
                values=np.array([1.0, 2.0]),
            )

    def test_non_increasing_rejected(self) -> None:
        """Equal (non-strictly-increasing) timestamps are rejected."""
        start = np.datetime64("2026-05-29T12:00:00", "ms")

        with pytest.raises(ValueError, match="strictly increasing"):
            TimeSeries(
                quantity=Quantity.NUMBER,
                timestamps=np.array([start, start]),
                values=np.array([1.0, 2.0]),
            )

    def test_empty_rejected(self) -> None:
        """A TimeSeries needs at least one sample."""
        with pytest.raises(ValueError):
            TimeSeries(
                quantity=Quantity.NUMBER,
                timestamps=np.array([], dtype="datetime64[ms]"),
                values=np.array([]),
            )

    def test_timestamps_coerced_to_ms(self) -> None:
        """Non-`datetime64[ms]` inputs are coerced on construction."""
        ts = TimeSeries(
            quantity=Quantity.NUMBER,
            timestamps=["2026-05-29T12:00:00", "2026-05-29T12:00:01"],
            values=np.array([1.0, 2.0]),
        )

        assert ts.timestamps.dtype == np.dtype("datetime64[ms]")


class TestSeriesMeasurement:
    """A time-series-only Measurement behaves as a series leaf."""

    @settings(max_examples=10)
    @given(m=series_measurement())
    def test_no_axis_no_distributions(self, m: Measurement) -> None:
        """It carries a series and neither an axis nor distributions."""
        assert m.axis is None
        assert not m.distributions
        assert Quantity.NUMBER in m.series

    @settings(max_examples=10)
    @given(m=series_measurement())
    def test_grid_access_errors(self, m: Measurement) -> None:
        """Grid passthroughs raise on a series-only measurement."""
        with pytest.raises(AttributeError):
            _ = m.n_bins

    @settings(max_examples=10)
    @given(m=series_measurement())
    def test_data_type_access_errors(self, m: Measurement) -> None:
        """Reading a binned value array errors when there are no distributions."""
        with pytest.raises(KeyError):
            _ = m["dN"]
