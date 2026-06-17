"""Scatter plot with optional fit overlay for collection efficiency."""

from collections.abc import Callable, Iterator
from itertools import cycle
from typing import Any, Literal, cast

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.ticker import Formatter

from pypana.analysis.fits import FitModel, fit_collection_efficiency
from pypana.config import settings
from pypana.data.collection_efficiency import CollectionEfficiency
from pypana.data._measurement import FloatArray
from pypana.plots.themes import BaseTheme
from pypana.plots.utils import coerce_formatter, split_kwargs

STANDARD_COLLECTION_EFFICIENCY_KWARGS: dict[str, Any] = {
    "scatter_marker": "o",
    "scatter_label": lambda ce: f"Data (n={len(ce)})",
    "fit_linestyle": "-",
    "fit_n_points": 1000,
    "fit_label": lambda ce: (
        f"{ce.fit_model} fit (d₅₀ = {ce.d_50:.2g}, R² = {ce.fit_r_squared:.3f})"
        if ce.d_50 is not None and ce.fit_r_squared is not None
        else (f"{ce.fit_model} fit" if ce.fit_model else "fit")
    ),
    "legend_frameon": False,
}
"""Standard kwargs for an out-of-the-box collection efficiency plot.

These parameters may change with newer versions of pypana.
"""


def plot_collection_efficiency(  # pragma: no cover  # noqa: PLR0912, PLR0915
    ce: CollectionEfficiency,
    *,
    fit: FitModel | None = "sigmoid",
    refit: bool = False,
    theme: type[BaseTheme] | None = None,
    save_as: str | None = None,
    legend: Literal[
        "best",
        "upper right",
        "upper left",
        "lower left",
        "lower right",
        "right",
        "center left",
        "center right",
        "lower center",
        "upper center",
        "center",
    ]
    | None = "best",
    spines_invisible: list[Literal["left", "right", "top", "bottom"]] | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    xlim: tuple[float, float] | None = None,
    xmajor_formatter: Formatter | str | None = None,
    xscale: Literal["linear", "log"] = "log",
    ylabel: str | None = None,
    ylim: tuple[float, float] | None = None,
    ymajor_formatter: Formatter | str | None = None,
    yscale: Literal["linear", "log"] = "linear",
    **kwargs,
) -> None:
    """Plots a ``CollectionEfficiency`` object as scatter with optional fitted curve.

    The fit (if any) is computed in-place: ``ce.fit_model``, ``ce.fit_popt`` and
    ``ce.fit_function`` are populated on the supplied object.

    Note:
        Not all possible matplotlib kwargs are specified in the Keyword Args section.
        Additional kwargs can be passed to matplotlib with their respective name prepended
        by the following prefixes that indicates the target:

        - ``scatter_`` for the data points,
        - ``fit_`` for the fitted curve,
        - ``grid_`` for the background grid (only visible, if grid_visible=True in theme),
        - ``legend_`` for the legend.

        For matplotlib kwargs, please consult the matplotlib documentation: https://matplotlib.org/stable/ .

    Args:
        ce (CollectionEfficiency): The collection efficiency result container holding
            ``d_p`` and ``eta``. After the call, the fit fields are populated if ``fit`` is set.
        fit (str | None): The fit to overlay on the scatter. ``"sigmoid"`` extracts the
            cut diameter ``d_50``. ``"gompertz"`` allows non-0/100% asymptotes. ``None``
            plots only the data points. Defaults to ``"sigmoid"``.
        refit (bool): Force re-running the fit even if ``ce`` already carries a fit
              for the same ``model``. Defaults to ``False`` (cached fit is reused).
        theme (BaseTheme): The theme for the plot. Defaults to ``settings.THEME``.
        save_as (str | None): The path where to save the figure. Defaults to ``None`` which
            does not save.
        legend (str | None): The location of the legend, or ``None`` to hide it. Defaults to
            ``"best"``.
        spines_invisible (list): The spines not to show. Defaults to ``None``, in which case
            all are plotted.
        title (str | None): The title of the plot. Defaults to ``None`` and uses an adaptive
            title.
        xlabel (str | None): The x-axis label. Defaults to ``None`` and uses an adaptive label.
        xlim (tuple): The x-axis lower and upper bound. Defaults to ``None`` which uses the data range.
        xmajor_formatter (Formatter | str): The matplotlib ticker.Formatter for the x-axis.
        xscale (str): The scaling of the x-axis. Defaults to ``"log"``.
        ylabel (str | None): The y-axis label. Defaults to ``None`` and uses an adaptive label.
        ylim (tuple): The y-axis lower and upper bound. Defaults to ``None``.
        ymajor_formatter (Formatter | str): The matplotlib ticker.Formatter for the y-axis.
        yscale (str): The scaling of the y-axis. Defaults to ``"linear"``.
        kwargs: The additional kwargs for matplotlib. See the Keyword Args section.

    Keyword Args:
        scatter_color (str): The color of the scatter points. Can be either a hex code,
            e.g. "#000000", or from the color cycle, e.g. "C0". Defaults to the matplotlib default.
        scatter_marker (str): The matplotlib marker style for the scatter points. Defaults to ``"o"``.
        scatter_s (float): The marker size of the scatter points. Defaults to the matplotlib default.
        scatter_label (str | Callable[[CollectionEfficiency], str] | None): The legend label
            for the data points. Defaults to an adaptive label. Also supports a lambda function
            that takes the CollectionEfficiency object as input.

        fit_color (str): The color of the fit line. Defaults to the scatter color.
        fit_linestyle (str): The linestyle of the fit line. Defaults to ``"-"``.
        fit_linewidth (float): The linewidth of the fit line. Defaults to the matplotlib default.
        fit_label (str | Callable[[CollectionEfficiency], str] | None): The legend label
            for the fit. Defaults to an adaptive label (model name and ``d_50`` if available).
            Also supports a lambda function that takes the CollectionEfficiency object as input.
        fit_n_points (int): Number of points to evaluate the fit on. Defaults to ``1000``.

        grid_color (str): The color of the grid lines. Defaults to the matplotlib default.
        grid_linewidth (float): The linewidth of the grid lines. Defaults to the matplotlib default.
        grid_which (str): What type of grid to show. Either ``"major"``, ``"minor"``, or ``"both"``.

        legend_labelcolor (str): The color of the legend labels. Defaults to the matplotlib default.
        legend_loc (str): The location of the matplotlib legend. Defaults to the matplotlib default.
    """
    _theme = theme or settings.THEME

    _scatter_kwargs, _fit_kwargs, _grid_kwargs, _legend_kwargs = split_kwargs(
        "scatter_",
        "fit_",
        "grid_",
        "legend_",
        **kwargs,
    )

    if fit is not None:
        fit_collection_efficiency(ce, model=fit, refit=refit)

    _colors = (
        list(_theme.color_cycle.values())
        if _theme.color_cycle
        else plt.rcParams["axes.prop_cycle"].by_key()["color"]
    )
    _sc = _scatter_kwargs.pop("color", None)
    _fc = _fit_kwargs.pop("color", None)
    _scatter_color = cycle([_sc]) if isinstance(_sc, str) else cycle(_colors)
    _fit_color = cycle([_fc]) if isinstance(_fc, str) else _scatter_color

    _scatter_kwargs["label"] = _resolve_label(
        kwargs.get(
            "scatter_label", STANDARD_COLLECTION_EFFICIENCY_KWARGS["scatter_label"]
        ),
        ce,
        default=f"Data (n={len(ce)})",
    )
    _fit_label_default = (
        f"{ce.fit_model} fit (d₅₀ = {ce.d_50:.2g}, R² = {ce.fit_r_squared:.3f})"
        if ce.d_50 is not None and ce.fit_r_squared is not None
        else (f"{ce.fit_model} fit" if ce.fit_model else "fit")
    )
    _fit_kwargs["label"] = _resolve_label(
        kwargs.get("fit_label", STANDARD_COLLECTION_EFFICIENCY_KWARGS["fit_label"]),
        ce,
        default=_fit_label_default,
    )

    _handles: list = []
    _labels: list = []

    with matplotlib.rc_context(_theme.to_rcparams()):
        fig, ax = plt.subplots(layout="constrained")

        if _grid_kwargs:
            ax.grid(**_grid_kwargs)

        sc = _scatter_plot(_scatter_kwargs, _scatter_color, ce, ax)
        _handles.append(sc)
        _labels.append(_scatter_kwargs.get("label", ""))

        if fit is not None and ce.fit_function is not None:
            _n_points = int(
                cast(
                    int,
                    _fit_kwargs.pop(
                        "n_points",
                        STANDARD_COLLECTION_EFFICIENCY_KWARGS["fit_n_points"],
                    ),
                )
            )
            line = _fit_plot(
                _fit_kwargs,
                _fit_color,
                ce,
                _n_points,
                xscale,
                xlim,
                ax,
            )
            _handles.append(line)
            _labels.append(_fit_kwargs.get("label", ""))

        _format_ax(
            ax,
            xlabel,
            xlim,
            xmajor_formatter,
            xscale,
            ylabel,
            ylim,
            ymajor_formatter,
            yscale,
            title,
        )

        for spine in spines_invisible or []:
            ax.spines[spine].set_visible(False)

        if legend:
            ax.legend(_handles, _labels, loc=legend, **_legend_kwargs)

        if save_as is not None:
            fig.savefig(save_as, bbox_inches="tight", transparent=True)

        plt.show()


def _scatter_plot(  # pragma: no cover
    _scatter_kwargs: dict[str, object],
    _color_generator: Iterator[str],
    ce: CollectionEfficiency,
    ax: Axes,
) -> PathCollection:
    """Plots the scatter part."""
    _color_kwarg = {"color": next(_color_generator)}
    return ax.scatter(ce.d_p, ce.eta, **_color_kwarg, **_scatter_kwargs)


def _fit_plot(  # pragma: no cover
    _fit_kwargs: dict[str, object],
    _color_generator: Iterator[str],
    ce: CollectionEfficiency,
    n_points: int,
    xscale: Literal["linear", "log"],
    xlim: tuple[float, float] | None,
    ax: Axes,
) -> Line2D:
    """Plots the fit line part."""
    assert ce.fit_function is not None, "fit_function must be populated before plotting"

    _color_kwarg = {"color": next(_color_generator)}
    lo, hi = xlim if xlim else (float(ce.d_p.min()), float(ce.d_p.max()))
    x: FloatArray = np.asarray(
        np.logspace(np.log10(lo), np.log10(hi), n_points)
        if xscale == "log"
        else np.linspace(lo, hi, n_points),
        dtype=float,
    )
    (line,) = ax.plot(x, ce.fit_function(x), **_color_kwarg, **_fit_kwargs)
    return line


def _format_ax(  # pragma: no cover
    ax: Axes,
    xlabel: str | None,
    xlim: tuple[float, float] | None,
    xmajor_formatter: Formatter | str | None,
    xscale: Literal["linear", "log"],
    ylabel: str | None,
    ylim: tuple[float, float] | None,
    ymajor_formatter: Formatter | str | None,
    yscale: Literal["linear", "log"],
    title: str | None,
) -> None:
    """Sets the parameters for ax."""
    ax.set_xscale(xscale)
    ax.set_yscale(yscale)

    if xscale == "log":
        ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, subs=(1.0, 2.0, 5.0)))
        ax.xaxis.set_minor_locator(
            ticker.LogLocator(base=10.0, subs=(3.0, 4.0, 6.0, 7.0, 8.0, 9.0))
        )

    _xformatter = coerce_formatter(xmajor_formatter) or ticker.EngFormatter(unit="m")
    ax.xaxis.set_major_formatter(_xformatter)
    ax.xaxis.set_minor_formatter(ticker.NullFormatter())

    _yformatter = coerce_formatter(ymajor_formatter)
    if _yformatter is not None:
        ax.yaxis.set_major_formatter(_yformatter)

    ax.tick_params(axis="both", direction="in", which="both")

    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)

    ax.set_xlabel(xlabel or _default_xlabel())
    ax.set_ylabel(ylabel or _default_ylabel())

    if title:
        ax.set_title(title)


def _resolve_label(
    label: str | Callable[[CollectionEfficiency], str] | None,
    ce: CollectionEfficiency,
    default: str,
) -> str:
    """Resolves the label. Accepts str, callable on ``ce``, or None (uses default)."""
    if label is None:
        return default
    return label(ce) if callable(label) else label


def _default_xlabel() -> str:  # pragma: no cover
    return "Particle Diameter"


def _default_ylabel() -> str:  # pragma: no cover
    return "Collection Efficiency / -"
