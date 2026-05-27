"""Fit models for collection-efficiency curves."""

from collections.abc import Callable

import numpy as np
from scipy.optimize import curve_fit

from pypana.analysis.types import FitModel
from pypana.data.collection_efficiency import CollectionEfficiency
from pypana.data.measurement import FloatArray

_D_50_ETA = 0.5


def _sigmoid(x: FloatArray, x0: float, k: float) -> FloatArray:
    return np.asarray(1.0 / (1.0 + np.exp(-k * (x - x0))), dtype=float)


def _gompertz(x: FloatArray, x0: float, a: float, b: float, d: float) -> FloatArray:
    return np.asarray(d + (a - d) * np.exp(-np.exp(-b * (x - x0))), dtype=float)


_MODELS: dict[FitModel, Callable[..., FloatArray]] = {
    "sigmoid": _sigmoid,
    "gompertz": _gompertz,
}


def _initial_guess(model: FitModel, d_p: FloatArray, eta: FloatArray) -> list[float]:
    """Returns a data-driven ``p0`` for ``curve_fit``.

    The sigmoid (and gompertz inflection) is centred at the diameter whose η
    is closest to 0.5, with a slope scaled by the data's diameter span so the
    transition spans roughly the observed range.
    """
    x0 = float(d_p[int(np.argmin(np.abs(eta - _D_50_ETA)))])
    span = float(d_p.max() - d_p.min()) or x0 or 1.0
    k = 4.0 / span

    if model == "sigmoid":
        return [x0, k]

    if model == "gompertz":
        a = float(np.clip(eta.max(), 0.0, 1.0)) or 1.0
        d = float(np.clip(eta.min(), 0.0, 1.0))
        return [x0, a, k, d]

    raise ValueError(f"Unknown fit model {model!r}.")


def fit_collection_efficiency(
    ce: CollectionEfficiency,
    *,
    model: FitModel = "sigmoid",
    refit: bool = False,
) -> CollectionEfficiency:
    """Fits a model to ``ce`` in place and returns it for chaining.

    Populates ``ce.fit_model``, ``ce.fit_popt`` and ``ce.fit_function``.
    If ``ce`` already carries a fit for the same ``model``, this is a no-op
    unless ``refit=True``.
    """
    if model not in _MODELS:
        raise ValueError(
            f"Unknown fit model {model!r}; expected one of {list(_MODELS)}."
        )

    if (
        not refit
        and ce.fit_model == model
        and ce.fit_popt is not None
        and ce.fit_function is not None
    ):
        return ce

    func = _MODELS[model]
    p0 = _initial_guess(model, ce.d_p, ce.eta)
    popt, pcov = curve_fit(func, ce.d_p, ce.eta, p0=p0, maxfev=10_000)

    def _fit_function(x: FloatArray) -> FloatArray:
        return np.asarray(func(x, *popt), dtype=float)

    residuals = ce.eta - func(ce.d_p, *popt)
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((ce.eta - ce.eta.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    rmse = float(np.sqrt(ss_res / len(ce.eta)))
    perr = (
        np.sqrt(np.diag(pcov))
        if np.all(np.isfinite(pcov))
        else np.full_like(popt, np.nan)
    )

    ce.fit_model = model
    ce.fit_popt = np.asarray(popt, dtype=float)
    ce.fit_perr = np.asarray(perr, dtype=float)
    ce.fit_r_squared = r_squared
    ce.fit_rmse = rmse
    ce.fit_function = _fit_function

    return ce
