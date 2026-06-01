"""Tests for pypana.data.collection_efficiency.CollectionEfficiency."""

import math

import numpy as np
import pytest
from hypothesis import given, settings

from data.strategies import collection_efficiency
from pypana.data.collection_efficiency import CollectionEfficiency


@settings(max_examples=10)
@given(ce=collection_efficiency())
def test_len_matches_d_p(ce: CollectionEfficiency) -> None:
    """__len__ returns the number of diameter points."""
    assert len(ce) == len(ce.d_p)


@settings(max_examples=10)
@given(ce=collection_efficiency())
def test_d_50_without_fit_raises(ce: CollectionEfficiency) -> None:
    """d_50 requires a fit, without fit_popt it raises."""
    assert ce.fit_popt is None
    with pytest.raises(ValueError):
        _ = ce.d_50


@settings(max_examples=10)
@given(ce=collection_efficiency())
def test_d_50_sigmoid_returns_centre(ce: CollectionEfficiency) -> None:
    """For a sigmoid fit, d_50 is the first parameter (the inflection x0)."""
    ce.fit_model = "sigmoid"
    ce.fit_popt = np.array([3.2e-8, 1.0e8])

    assert ce.d_50 == pytest.approx(3.2e-8)


@settings(max_examples=10)
@given(ce=collection_efficiency())
def test_d_50_gompertz_valid(ce: CollectionEfficiency) -> None:
    """For a bracketing gompertz fit, d_50 is the inverted-Gompertz diameter."""
    x0, a, b, d = 3.0e-8, 1.0, 5.0e7, 0.0
    ce.fit_model = "gompertz"
    ce.fit_popt = np.array([x0, a, b, d])

    inner = (0.5 - d) / (a - d)
    expected = x0 - math.log(-math.log(inner)) / b

    assert ce.d_50 == pytest.approx(expected)


@settings(max_examples=10)
@given(ce=collection_efficiency())
def test_d_50_gompertz_non_bracketing_raises(ce: CollectionEfficiency) -> None:
    """A gompertz fit whose asymptotes don't bracket 0.5 has no defined d_50."""
    ce.fit_model = "gompertz"
    ce.fit_popt = np.array([3.0e-8, 0.4, 5.0e7, 0.0])  # a = 0.4 < 0.5

    with pytest.raises(ValueError):
        _ = ce.d_50


@settings(max_examples=10)
@given(ce=collection_efficiency())
def test_d_50_unknown_model_raises(ce: CollectionEfficiency) -> None:
    """A populated fit_popt with no recognised model falls through to ValueError."""
    ce.fit_popt = np.array([3.0e-8, 1.0])
    ce.fit_model = None

    with pytest.raises(ValueError):
        _ = ce.d_50


@settings(max_examples=10)
@given(ce=collection_efficiency())
def test_fit_ci_without_popt_raises(ce: CollectionEfficiency) -> None:
    """fit_ci requires a fit; without fit_popt it raises."""
    with pytest.raises(ValueError):
        ce.fit_ci()


@settings(max_examples=10)
@given(ce=collection_efficiency())
def test_fit_ci_with_popt_but_no_perr_raises(ce: CollectionEfficiency) -> None:
    """fit_ci needs the parameter errors too; popt without perr raises."""
    ce.fit_popt = np.array([3.0e-8, 1.0])
    ce.fit_perr = None

    with pytest.raises(ValueError):
        ce.fit_ci()


@settings(max_examples=10)
@given(ce=collection_efficiency(max_points=2))
def test_fit_ci_non_positive_dof_raises(ce: CollectionEfficiency) -> None:
    """When points <= parameters the degrees of freedom are non-positive -> raises."""
    ce.fit_popt = np.array([3.0e-8, 1.0])
    ce.fit_perr = np.array([1e-9, 0.1])

    with pytest.raises(ValueError):
        ce.fit_ci()


@settings(max_examples=10)
@given(ce=collection_efficiency(min_points=3))
def test_fit_ci_valid_returns_one_interval_per_param(ce: CollectionEfficiency) -> None:
    """A valid fit yields one ordered (lower, upper) interval per parameter."""
    ce.fit_popt = np.array([3.0e-8, 1.0])
    ce.fit_perr = np.array([1e-9, 0.1])

    ci = ce.fit_ci(alpha=0.05)

    assert ci is not None
    assert len(ci) == len(ce.fit_popt)
    for lower, upper in ci:
        assert lower < upper
