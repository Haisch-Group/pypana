"""Tests for pypana.analysis.fits."""

import numpy as np
import pytest
from scipy.optimize import OptimizeWarning

from pypana.analysis.fits import (
    _gompertz,
    _initial_guess,
    _sigmoid,
    fit_collection_efficiency,
)
from pypana.data.collection_efficiency import CollectionEfficiency

D_P = np.linspace(10e-9, 200e-9, 25)
X0 = 80e-9
K = 5e7

SIGMOID_N_PARAMS = 2
GOMPERTZ_N_PARAMS = 4
MIN_GOOD_R2 = 0.99

SIGMOID_ETA = _sigmoid(D_P, X0, K)
GOMPERTZ_ETA = _gompertz(D_P, X0, 1.0, K, 0.0)


def make_ce(d_p: np.ndarray, eta: np.ndarray) -> CollectionEfficiency:
    """Build a fit-less CollectionEfficiency from diameter/efficiency arrays."""
    n = len(d_p)
    return CollectionEfficiency(
        d_p=np.asarray(d_p, dtype=float),
        eta=np.asarray(eta, dtype=float),
        upstream_scan_nrs=list(range(0, 2 * n, 2)),
        downstream_scan_nrs=list(range(1, 2 * n, 2)),
    )


def test_fit_sigmoid_populates_fit_fields() -> None:
    """A sigmoid fit recovers the curve and fills all fit_* fields."""
    ce = make_ce(D_P, SIGMOID_ETA)
    out = fit_collection_efficiency(ce, model="sigmoid")

    assert out is ce
    assert ce.fit_model == "sigmoid"
    assert ce.fit_popt is not None and len(ce.fit_popt) == SIGMOID_N_PARAMS
    assert ce.fit_function is not None
    assert ce.fit_perr is not None and np.all(np.isfinite(ce.fit_perr))
    assert ce.fit_r_squared is not None and ce.fit_r_squared > MIN_GOOD_R2
    assert ce.fit_rmse is not None and ce.fit_rmse >= 0.0
    assert ce.fit_function(D_P).shape == D_P.shape


def test_fit_gompertz_populates_fit_fields() -> None:
    """A gompertz fit recovers the curve and fills a 4-parameter fit."""
    ce = make_ce(D_P, GOMPERTZ_ETA)
    out = fit_collection_efficiency(ce, model="gompertz")

    assert out is ce
    assert ce.fit_model == "gompertz"
    assert ce.fit_popt is not None and len(ce.fit_popt) == GOMPERTZ_N_PARAMS
    assert ce.fit_r_squared is not None and ce.fit_r_squared > MIN_GOOD_R2


def test_fit_unknown_model_raises() -> None:
    """An unsupported model name is rejected before fitting."""
    ce = make_ce(D_P, SIGMOID_ETA)
    with pytest.raises(ValueError):
        fit_collection_efficiency(ce, model="bogus")  # type: ignore[arg-type]


def test_initial_guess_unknown_model_raises() -> None:
    """_initial_guess rejects an unsupported model directly."""
    with pytest.raises(ValueError):
        _initial_guess("bogus", D_P, SIGMOID_ETA)  # type: ignore[arg-type]


def test_initial_guess_param_counts() -> None:
    """_initial_guess returns 2 params for sigmoid and 4 for gompertz."""
    assert len(_initial_guess("sigmoid", D_P, SIGMOID_ETA)) == SIGMOID_N_PARAMS
    assert len(_initial_guess("gompertz", D_P, GOMPERTZ_ETA)) == GOMPERTZ_N_PARAMS


def test_fit_returns_early_when_already_fitted() -> None:
    """Re-fitting the same model without refit is a no-op."""
    ce = make_ce(D_P, SIGMOID_ETA)
    sentinel = ce.fit_function = lambda x: x  # pre-existing fit
    ce.fit_model = "sigmoid"
    ce.fit_popt = np.array([1.0, 2.0])

    out = fit_collection_efficiency(ce, model="sigmoid", refit=False)

    assert out is ce
    assert ce.fit_function is sentinel  # not recomputed


def test_refit_overrides_existing_fit() -> None:
    """refit=True re-runs the fit even when a fit is already present."""
    ce = make_ce(D_P, SIGMOID_ETA)
    sentinel = ce.fit_function = lambda x: x
    ce.fit_model = "sigmoid"
    ce.fit_popt = np.array([1.0, 2.0])

    fit_collection_efficiency(ce, model="sigmoid", refit=True)

    assert ce.fit_function is not sentinel
    assert ce.fit_r_squared is not None and ce.fit_r_squared > MIN_GOOD_R2


def test_fit_flat_eta_yields_nan_r_squared_and_perr() -> None:
    """A flat target has zero total variance and an unidentifiable covariance."""
    ce = make_ce(D_P, np.full_like(D_P, 0.5))
    with pytest.warns(OptimizeWarning):
        fit_collection_efficiency(ce, model="sigmoid")

    assert ce.fit_r_squared is not None and np.isnan(ce.fit_r_squared)
    assert ce.fit_perr is not None and np.all(np.isnan(ce.fit_perr))
