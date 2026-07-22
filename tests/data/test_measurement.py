import numpy as np
import pytest
from hypothesis import assume, given, settings

from data.strategies import populated_measurement
from pypana.data.defs import Quantity
from pypana.data.measurement import Measurement


@settings(max_examples=10)
@given(m=populated_measurement())
def test_requires_a_payload(m: Measurement) -> None:
    """A Measurement with neither distributions nor series raises."""
    with pytest.raises(ValueError):
        Measurement(scan_nr=m.scan_nr, time=m.time, axis=m.axis)


@settings(max_examples=10)
@given(m=populated_measurement())
def test_distributions_require_axis(m: Measurement) -> None:
    """Size distributions without the shared axis raise."""
    dist = m.distributions[Quantity.NUMBER]
    with pytest.raises(ValueError):
        Measurement(
            scan_nr=m.scan_nr, time=m.time, distributions={Quantity.NUMBER: dist}
        )


@settings(max_examples=10)
@given(m=populated_measurement())
def test_getitem_quantity_filters_to_submeasurement(m: Measurement) -> None:
    """Indexing with a bare quantity returns a single-quantity Measurement sharing the axis."""
    sub = m["N"]
    assert isinstance(sub, Measurement)
    assert tuple(sub.quantities) == (Quantity.NUMBER,)
    assert sub.axis is m.axis


@settings(max_examples=10)
@given(m=populated_measurement(seed="delta"))
def test_getitem_datatype_returns_values(m: Measurement) -> None:
    """Indexing with a data type returns the matching value array."""
    dist = m.distributions[Quantity.NUMBER]
    assert np.array_equal(m["dN"], dist.delta)
    assert np.allclose(m["dN/dlogdp"], dist.delta_dlogdp)


@settings(max_examples=10)
@given(m=populated_measurement())
def test_getitem_unknown_key_raises(m: Measurement) -> None:
    """An unknown data-type string raises."""
    with pytest.raises((ValueError, KeyError)):
        _ = m["nonsense"]


@settings(max_examples=10)
@given(m=populated_measurement())
def test_contains_quantity(m: Measurement) -> None:
    """A stored quantity is reported by __contains__."""
    assert Quantity.NUMBER in m
    assert "N" in m


@settings(max_examples=25)
@given(m=populated_measurement(seed="delta", nonzero_total=True))
def test_transparent_total_and_geo_mean(m: Measurement) -> None:
    """total/geo_mean delegate to the sole distribution."""
    dist = m.distributions[Quantity.NUMBER]
    assert m.total == dist.total
    assert m.geo_mean == dist.geo_mean


@settings(max_examples=10)
@given(m=populated_measurement())
def test_grid_passthroughs_match_axis(m: Measurement) -> None:
    """d_p / delta_d_p / bin_boundaries come from the shared axis."""
    assert m.axis is not None
    assert np.array_equal(m.d_p, m.axis.d_p)
    assert np.array_equal(m.delta_d_p, m.axis.delta_d_p)
    assert np.array_equal(m.bin_boundaries, m.axis.bin_boundaries)


@settings(max_examples=15)
@given(m=populated_measurement(seed="delta", min_bins=2))
def test_cut_delegates_and_returns_self(m: Measurement) -> None:
    """cut() zeroes bins outside the range on every distribution and returns self."""
    lo, hi = float(m.d_p.min()), float(m.d_p.max())
    d_lo, d_hi = lo + (hi - lo) * 0.25, lo + (hi - lo) * 0.75
    assume(d_lo < d_hi)
    outside = (m.d_p < d_lo) | (m.d_p > d_hi)

    assert m.cut((d_lo, d_hi)) is m
    assert np.all(m.distributions[Quantity.NUMBER]["dN"][outside] == 0.0)


@settings(max_examples=10)
@given(m=populated_measurement())
def test_quantities_lists_stored(m: Measurement) -> None:
    """quantities reflects the stored payloads."""
    assert tuple(m.quantities) == (Quantity.NUMBER,)


@settings(max_examples=10)
@given(m=populated_measurement())
def test_summary_exposes_expected_keys(m: Measurement) -> None:
    """summary() returns the documented overview keys."""
    summary = m.summary()

    assert summary["scan_nr"] == m.scan_nr
    assert summary["n_bins"] == m.n_bins
    assert {"scan_nr", "time", "n_bins", "distributions", "other"} <= set(summary)
