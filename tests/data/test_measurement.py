"""Tests for pypana.data.measurement.Measurement."""

import numpy as np
import pytest
from hypothesis import assume, given, settings

from data.strategies import populated_measurement
from pypana.data.measurement import Measurement


@settings(max_examples=10)
@given(m=populated_measurement())
def test_requires_a_concentration(m: Measurement) -> None:
    """Constructing without delta_n or delta_n_dlog_dp raises."""
    with pytest.raises(ValueError):
        Measurement(
            scan_nr=m.scan_nr,
            time=m.time,
            d_p=m.d_p,
            delta_d_p=m.delta_d_p,
            delta_log_d_p=m.delta_log_d_p,
            bin_boundaries=m.bin_boundaries,
        )


@settings(max_examples=10)
@given(m=populated_measurement(seed="delta_n"))
def test_dlog_dp_derived_from_delta_n(m: Measurement) -> None:
    """When seeded with delta_n, delta_n is direct and delta_n_dlog_dp is derived."""
    assert m.raw_delta_n is not None
    assert np.array_equal(m.delta_n, m.raw_delta_n)
    assert np.allclose(m.delta_n_dlog_dp, m.delta_n / m.delta_log_d_p)


@settings(max_examples=10)
@given(m=populated_measurement(seed="delta_n_dlog_dp"))
def test_delta_n_derived_from_dlog_dp(m: Measurement) -> None:
    """When seeded with delta_n_dlog_dp, that is direct and delta_n is derived."""
    assert m.raw_delta_n_dlog_dp is not None
    assert np.array_equal(m.delta_n_dlog_dp, m.raw_delta_n_dlog_dp)
    assert np.allclose(m.delta_n, m.delta_n_dlog_dp * m.delta_log_d_p)


@settings(max_examples=10)
@given(m=populated_measurement(seed="delta_n"))
def test_n_total_sums_delta_n(m: Measurement) -> None:
    """n_total is the sum over all bins of delta_n."""
    assert m.n_total == float(m.delta_n.sum())


@settings(max_examples=25)
@given(m=populated_measurement(seed="delta_n"))
def test_stats_on_signal_are_in_range(m: Measurement) -> None:
    """Derived statistics are well-defined and within the diameter range."""
    assume(m.n_total > 0)

    lo, hi = float(m.d_p.min()), float(m.d_p.max())
    # needs margin
    rtol = 1e-9
    lo_b, hi_b = lo * (1 - rtol), hi * (1 + rtol)

    assert lo_b <= m.geo_mean <= hi_b
    assert m.geo_std_dev >= 1.0
    assert lo_b <= m.mean <= hi_b
    assert lo_b <= m.median <= hi_b
    assert m.mode in m.d_p


@settings(max_examples=10)
@given(m=populated_measurement(seed="delta_n", zero=True))
def test_stats_on_zero_distribution_use_fallbacks(m: Measurement) -> None:
    """When n_total == 0 every statistic falls back to its neutral value."""
    assert m.n_total == 0.0
    assert m.geo_mean == 0.0
    assert m.geo_std_dev == 1.0
    assert m.mean == 0.0
    assert m.median == 0.0
    assert m.mode == m.d_p[0]  # argmax of an all-zero array -> first bin


@settings(max_examples=15)
@given(m=populated_measurement(seed="delta_n", min_bins=2))
def test_cut_zeroes_outside_bins_delta_n(m: Measurement) -> None:
    """cut() zeroes bins outside the range when backed by raw_delta_n."""
    lo, hi = float(m.d_p.min()), float(m.d_p.max())
    d_lo, d_hi = lo + (hi - lo) * 0.25, lo + (hi - lo) * 0.75
    assume(d_lo < d_hi)

    outside = (m.d_p < d_lo) | (m.d_p > d_hi)
    m.cut((d_lo, d_hi))

    assert np.all(m.delta_n[outside] == 0.0)


@settings(max_examples=15)
@given(m=populated_measurement(seed="delta_n_dlog_dp", min_bins=2))
def test_cut_zeroes_outside_bins_dlog_dp(m: Measurement) -> None:
    """cut() zeroes bins outside the range when backed by raw_delta_n_dlog_dp."""
    lo, hi = float(m.d_p.min()), float(m.d_p.max())
    d_lo, d_hi = lo + (hi - lo) * 0.25, lo + (hi - lo) * 0.75
    assume(d_lo < d_hi)

    outside = (m.d_p < d_lo) | (m.d_p > d_hi)
    m.cut((d_lo, d_hi))

    assert np.all(m.delta_n_dlog_dp[outside] == 0.0)


@settings(max_examples=10)
@given(m=populated_measurement(min_bins=2))
def test_cut_returns_self(m: Measurement) -> None:
    """cut() is chainable and returns the same instance."""
    lo, hi = float(m.d_p.min()), float(m.d_p.max())
    assume(lo < hi)
    assert m.cut((lo, hi)) is m


@settings(max_examples=10)
@given(m=populated_measurement(min_bins=2))
def test_cut_rejects_inverted_bounds(m: Measurement) -> None:
    """cut() raises when the lower bound is not below the upper bound."""
    lo, hi = float(m.d_p.min()), float(m.d_p.max())
    assume(lo < hi)
    with pytest.raises(ValueError):
        m.cut((hi, lo))


@settings(max_examples=10)
@given(m=populated_measurement())
def test_summary_exposes_expected_keys(m: Measurement) -> None:
    """summary() returns the documented overview keys."""
    summary = m.summary()

    assert summary["scan_nr"] == m.scan_nr
    assert summary["n_bins"] == len(m.d_p)
    assert {
        "scan_nr",
        "n_bins",
        "d_p_min",
        "d_p_max",
        "n_total",
        "geo_mean",
        "geo_std_dev",
        "mean",
        "median",
        "mode",
        "other",
    } <= set(summary)


@settings(max_examples=10)
@given(m=populated_measurement(seed="delta_n"))
def test_writing_delta_n_alias_updates_source_and_invalidates_cache(
    m: Measurement,
) -> None:
    """Assigning the public delta_n alias writes raw_delta_n and clears the cache."""
    _ = m.n_total  # populate a cached property so invalidation has work to do
    new = m.delta_n * 2.0

    m.delta_n = new

    assert m.raw_delta_n_dlog_dp is None  # paired field nulled
    assert np.allclose(m.delta_n, new)
    assert m.n_total == float(new.sum())  # recomputed from the new values


@settings(max_examples=10)
@given(m=populated_measurement(seed="delta_n"))
def test_writing_dlog_dp_alias_routes_to_raw(m: Measurement) -> None:
    """Assigning delta_n_dlog_dp routes to raw_delta_n_dlog_dp and nulls the pair."""
    _ = m.delta_n_dlog_dp
    new = np.full(len(m.d_p), 5.0)

    m.delta_n_dlog_dp = new

    assert m.raw_delta_n is None
    assert np.array_equal(m.delta_n_dlog_dp, new)
