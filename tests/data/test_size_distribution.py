"""Tests for pypana.data.size_distribution.SizeDistribution."""

import numpy as np
import pytest
from hypothesis import assume, given, settings

from data.strategies import size_distribution
from pypana.data.size_distribution import SizeDistribution


@settings(max_examples=10)
@given(sd=size_distribution())
def test_requires_a_representation(sd: SizeDistribution) -> None:
    """Constructing without delta or delta_dlogdp raises."""
    with pytest.raises(ValueError):
        SizeDistribution(quantity=sd.quantity, axis=sd.axis)


@settings(max_examples=10)
@given(sd=size_distribution(seed="delta"))
def test_dlogdp_derived_from_delta(sd: SizeDistribution) -> None:
    """Seeded with delta, delta is direct and delta_dlogdp is derived."""
    assert sd.raw_delta is not None
    assert np.array_equal(sd.delta, sd.raw_delta)
    assert np.allclose(sd.delta_dlogdp, sd.delta / sd.axis.delta_log_d_p)


@settings(max_examples=10)
@given(sd=size_distribution(seed="delta_dlogdp"))
def test_delta_derived_from_dlogdp(sd: SizeDistribution) -> None:
    """Seeded with delta_dlogdp, that is direct and delta is derived."""
    assert sd.raw_delta_dlogdp is not None
    assert np.array_equal(sd.delta_dlogdp, sd.raw_delta_dlogdp)
    assert np.allclose(sd.delta, sd.delta_dlogdp * sd.axis.delta_log_d_p)


@settings(max_examples=10)
@given(sd=size_distribution(seed="delta"))
def test_total_sums_delta(sd: SizeDistribution) -> None:
    """total is the sum over all bins of delta."""
    assert sd.total == float(np.nansum(sd.delta))


@settings(max_examples=25)
@given(sd=size_distribution(seed="delta"))
def test_stats_in_range(sd: SizeDistribution) -> None:
    """Derived statistics are well-defined and within the diameter range."""
    assume(sd.total > 0)

    d_p = sd.axis.d_p
    lo, hi = float(d_p.min()), float(d_p.max())
    rtol = 1e-9
    lo_b, hi_b = lo * (1 - rtol), hi * (1 + rtol)

    assert lo_b <= sd.geo_mean <= hi_b
    assert sd.geo_std_dev >= 1.0
    assert lo_b <= sd.mean <= hi_b
    assert lo_b <= sd.median <= hi_b
    assert sd.mode in d_p


@settings(max_examples=10)
@given(sd=size_distribution(seed="delta", zero=True))
def test_stats_zero_fallbacks(sd: SizeDistribution) -> None:
    """When total == 0 every statistic falls back to its neutral value."""
    assert sd.total == 0.0
    assert sd.geo_mean == 0.0
    assert sd.geo_std_dev == 1.0
    assert sd.mean == 0.0
    assert sd.median == 0.0
    assert sd.mode == sd.axis.d_p[0]  # argmax of an all-zero array -> first bin


@settings(max_examples=15)
@given(sd=size_distribution(seed="delta", min_bins=2))
def test_cut_zeroes_outside_delta(sd: SizeDistribution) -> None:
    """cut() zeroes bins outside the range when backed by raw_delta."""
    d_p = sd.axis.d_p
    lo, hi = float(d_p.min()), float(d_p.max())
    d_lo, d_hi = lo + (hi - lo) * 0.25, lo + (hi - lo) * 0.75
    assume(d_lo < d_hi)
    outside = (d_p < d_lo) | (d_p > d_hi)

    sd.cut((d_lo, d_hi))

    assert np.all(sd.delta[outside] == 0.0)


@settings(max_examples=15)
@given(sd=size_distribution(seed="delta_dlogdp", min_bins=2))
def test_cut_zeroes_outside_dlogdp(sd: SizeDistribution) -> None:
    """cut() zeroes bins outside the range when backed by raw_delta_dlogdp."""
    d_p = sd.axis.d_p
    lo, hi = float(d_p.min()), float(d_p.max())
    d_lo, d_hi = lo + (hi - lo) * 0.25, lo + (hi - lo) * 0.75
    assume(d_lo < d_hi)
    outside = (d_p < d_lo) | (d_p > d_hi)

    sd.cut((d_lo, d_hi))

    assert np.all(sd.delta_dlogdp[outside] == 0.0)


@settings(max_examples=10)
@given(sd=size_distribution(min_bins=2))
def test_cut_returns_self(sd: SizeDistribution) -> None:
    """cut() is chainable and returns the same instance."""
    d_p = sd.axis.d_p
    lo, hi = float(d_p.min()), float(d_p.max())
    assume(lo < hi)
    assert sd.cut((lo, hi)) is sd


@settings(max_examples=10)
@given(sd=size_distribution(min_bins=2))
def test_cut_rejects_inverted_bounds(sd: SizeDistribution) -> None:
    """cut() raises when the lower bound is not below the upper bound."""
    d_p = sd.axis.d_p
    lo, hi = float(d_p.min()), float(d_p.max())
    assume(lo < hi)
    with pytest.raises(ValueError):
        sd.cut((hi, lo))


@settings(max_examples=10)
@given(sd=size_distribution(seed="delta"))
def test_writing_delta_alias_updates_source_and_invalidates_cache(
    sd: SizeDistribution,
) -> None:
    """Assigning the public delta alias writes raw_delta and clears the cache."""
    _ = sd.total  # populate a cached property so invalidation has work to do
    new = sd.delta * 2.0

    sd.delta = new

    assert sd.raw_delta_dlogdp is None  # paired field nulled
    assert np.allclose(sd.delta, new)
    assert sd.total == float(np.nansum(new))  # recomputed from the new values


@settings(max_examples=10)
@given(sd=size_distribution(seed="delta"))
def test_writing_dlogdp_alias_routes_to_raw(sd: SizeDistribution) -> None:
    """Assigning delta_dlogdp routes to raw_delta_dlogdp and nulls the pair."""
    _ = sd.delta_dlogdp
    new = np.full(sd.axis.n_bins, 5.0)

    sd.delta_dlogdp = new

    assert sd.raw_delta is None
    assert np.array_equal(sd.delta_dlogdp, new)


@settings(max_examples=10)
@given(sd=size_distribution())
def test_summary_exposes_expected_keys(sd: SizeDistribution) -> None:
    """summary() returns the documented overview keys."""
    summary = sd.summary()
    assert {
        "quantity",
        "provenance",
        "n_bins",
        "d_p_min",
        "d_p_max",
        "total",
        "geo_mean",
        "geo_std_dev",
        "mean",
        "median",
        "mode",
    } <= set(summary)
