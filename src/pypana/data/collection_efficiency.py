"""Result container for a collection efficiency calculation."""

import math
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field
from scipy.stats import t

from pypana.analysis.types import FitModel
from pypana.data.measurement import FloatArray

_D_50_ETA = 0.5


class CollectionEfficiency(BaseModel):
    """The result of a collection efficiency calculation."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    d_p: FloatArray = Field(
        description="Geometric mean diameter of each upstream measurement [m]."
    )
    eta: FloatArray = Field(
        description="Collection efficiency η = 1 − n_down / n_up per pair [0..1]."
    )
    upstream_scan_nrs: list[int] = Field(
        description="Scan numbers of the upstream measurements, in pair order."
    )
    downstream_scan_nrs: list[int] = Field(
        description="Scan numbers of the downstream measurements, in pair order."
    )

    fit_model: FitModel | None = Field(
        default=None, description="Name of the model used for fitting, if any."
    )
    fit_popt: FloatArray | None = Field(
        default=None, description="Fitted parameter vector, if any."
    )
    fit_function: Callable[[FloatArray], FloatArray] | None = Field(
        default=None,
        exclude=True,
        description="Fitted model evaluated at x, if any.",
    )

    fit_perr: FloatArray | None = Field(
        default=None,
        description="1σ standard errors for fit_popt (sqrt of pcov diagonal).",
    )
    fit_r_squared: float | None = Field(
        default=None,
        description="Coefficient of determination R² of the fit (1.0 = perfect).",
    )
    fit_rmse: float | None = Field(
        default=None,
        description="Root-mean-square residual of the fit in η-units.",
    )

    def __len__(self) -> int:
        return len(self.d_p)

    @property
    def d_50(self) -> float:
        """The 50%-collection diameter, derived from the active fit (if any)."""
        if self.fit_popt is None:
            raise ValueError

        if self.fit_model == "sigmoid":
            return float(self.fit_popt[0])

        if self.fit_model == "gompertz":
            x0, a, _b, d = (float(p) for p in self.fit_popt)
            if not (d < _D_50_ETA < a):
                raise ValueError  # asymptotes don't bracket 0.5
            inner = (_D_50_ETA - d) / (a - d)
            return x0 - math.log(-math.log(inner)) / _b

        raise ValueError

    def fit_ci(self, alpha: float = 0.05) -> list[tuple[float, float]] | None:
        """Per-parameter confidence intervals at confidence level ``1 - alpha``.

        Returns:
            One ``(lower, upper)`` tuple per parameter in ``fit_popt`` order,

        Raises:
            Valuerror: If the fit hasn't run ye.

        Uses the t-distribution with ``n - p`` degrees of freedom, where ``n`` is
        the number of data points and ``p`` is the number of fitted parameters.
        """
        if self.fit_popt is None or self.fit_perr is None:
            raise ValueError

        dof = len(self) - len(self.fit_popt)
        if dof <= 0:
            raise ValueError

        t_crit = float(t.ppf(1.0 - alpha / 2.0, dof))
        return [
            (float(p - t_crit * e), float(p + t_crit * e))
            for p, e in zip(self.fit_popt, self.fit_perr, strict=True)
        ]
