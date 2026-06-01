"""Methods for plotting histograms of measurements in a matrix format."""

from collections.abc import Callable, Iterator
from itertools import cycle
from typing import Any, Literal

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker
from matplotlib.axes import Axes
from matplotlib.container import BarContainer
from matplotlib.patches import StepPatch
from matplotlib.ticker import Formatter

from pypana.config import settings
from pypana.data.measurement import FloatArray, Measurement
from pypana.plots.themes import BaseTheme
from pypana.plots.utils import coerce_formatter, linear_sci_formatter, split_kwargs
from pypana.utils.measurement_data_type import MeasurementDataType

STANDARD_HIST_SINGLE_KWARGS: dict[str, Any] = {
    "legend": "lower right",
    "bar_edgecolor": "black",
    "bar_label": lambda m: f"Measurement {m.scan_nr}",
    "bar_linewidth": 0.25,
    "secondary_alpha": 0.7,
    "secondary_color": "black",
    "legend_frameon": False,
}
"""Standard kwargs for an out-of-the-box configuration of a single histogram.

These parameters may change with newer versions of pypana.
"""

STANDARD_HIST_MATRIX_KWARGS: dict[str, Any] = {
    "legend": "column",
    "bar_label": lambda m: f"Measurement {m.scan_nr}",
    "bar_linewidth": 0,
    "secondary_alpha": 0.7,
    "secondary_color": "black",
    "legend_frameon": False,
}
"""Standard kwargs for an out-of-the-box configuration of a matrix of histograms.

These parameters may change with newer versions of pypana.
"""


def plot_hist_matrix(  # pragma: no cover # noqa: PLR0912, PLR0915
    m: list[list[tuple[Measurement, ...]]],
    data_type: MeasurementDataType,
    *,
    theme: BaseTheme | None = None,
    hist_type: Literal["bar", "stairs", "both"] = "bar",
    secondary: Literal["cdf", "fit_cdf", "fit_pdf"] | None = None,
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
        "row",
        "column",
    ]
    | None = "best",
    pmf: bool = False,
    spines_invisible: list[Literal["left", "right", "top", "bottom"]] | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    xlim: tuple[float, float] = (-np.inf, np.inf),
    xmajor_formatter: Formatter | str | None = None,
    xmajor_locations: tuple[float, ...] | None = None,
    ylabel: str | None = None,
    ylim: tuple[float, float] | None = None,
    ymajor_formatter: Formatter | str | None = None,
    yscale: Literal["linear", "log"] = "linear",
    **kwargs,
) -> None:
    """Plots the histogram of the specified measurement.

    Note:
        Not all possible matplotlib kwargs are specified in the Keyword Args section.
        Additional kwargs can be passed to matplotlib with their respective name prepended
        by the following prefixes that indicates the target:

        - ``bar_`` for the main histogram,
        - ``grid_`` for the background grid (only visible, if grid_visible=True in theme),
        - ``legend_`` for the legend,
        - ``secondary_`` for the secondary line plot,
        - ``stairs_`` for the stairs plot.

        For matplotlib kwargs, please consult the matplotlib documentation: https://matplotlib.org/stable/ .

    Args:
        m (list[list[Measurement]]): The measurement grid. The measurements are given row-major like numpy.
            Has to be a full rectangular matrix.
        data_type (MeasurementDataType): The data type to plot. ``dN/dlogdp`` or ``dN``.
        theme (BaseTheme): The theme for the plot. Defaults to ``settings.THEME``.
        hist_type (str): What histogram type to display. "bar" plots a standard bar histogram,
            "stairs" plots the outlines of the histogram, and "both" plots both together.
            Defaults to ``"bar"``.
        secondary (str): The additional function to plot for the first measurement per plot.
            "fit_cdf" and "fit_pdf" require the measurement to already be fitted previously. Both currently raise
            NotImplementedError. Defaults to ``None``.
        save_as (str | None): The path where to save the figure. Defaults to ``None`` which does not save.
        legend (str | None): Whether to show the legend and where.
        pmf (bool): Whether to plot the measurement as probability mass function. Defaults to ``False``.
        spines_invisible (list): The spines not to show. Defaults to ``None``, in which case all are plotted.
        title (str | None): The title of the plot. Defaults to ``None`` and uses an adaptive title.
        xlabel (str | None): The x-axis label of the plot. Defaults to ``None`` and uses an adaptive title.
        xlim (tuple): The x-axis lower and upper bound.
        xmajor_formatter (Formatter | str): The matplotlib ticker.Formatter for the x-axis.
        xmajor_locations (tuple): The float values between 1.0 and 10.0 where major ticks are plotted.
        ylabel (str | None): The y-axis label of the plot. Defaults to ``None`` and uses an adaptive title.
        ylim (tuple): The y-axis lower and upper bound. Can be used to give specific y-ranges on the axis.
        ymajor_formatter (Formatter | str): The matplotlib ticker.Formatter for the y-axis.
        yscale (str): The type of scaling the y-axis uses. Defaults to ``"linear"``.
        kwargs: The additional kwargs for matplotlib. See the Keyword Args section for more information.
    """
    _rows = len(m)
    _cols = len(m[0])
    _theme = theme or settings.THEME

    _bar_kwargs, _grid_kwargs, _legend_kwargs, _secondary_kwargs, _stairs_kwargs = (
        split_kwargs("bar_", "grid_", "legend_", "secondary_", "stairs_", **kwargs)
    )

    _colors = (
        list(_theme.color_cycle.values())
        if _theme.color_cycle
        else plt.rcParams["axes.prop_cycle"].by_key()["color"]
    )

    _handles: list = []
    _labels: list = []
    _secondary_handles: list = []
    _secondary_labels: list = []

    _bf = _bar_kwargs.pop("facecolor", None)
    _sf = _stairs_kwargs.pop("facecolor", None)
    _bar_colors = cycle([_bf]) if isinstance(_bf, str) else cycle(_colors)
    _stairs_colors = cycle([_sf]) if isinstance(_sf, str) else cycle(_colors)

    with matplotlib.rc_context(_theme.to_rcparams()):
        fig, axs = plt.subplots(
            _rows, _cols, sharex=True, sharey=True, squeeze=False, layout="constrained"
        )

        _title = title or _get_default_title()
        fig.suptitle(_title)

        for (r, c), ax in np.ndenumerate(axs):
            ax.grid()
            _m_tuple: tuple[Measurement, ...] = m[r][c]

            for _m in _m_tuple:
                _data = (
                    _m.delta_n_dlog_dp.copy()
                    if data_type == MeasurementDataType.dndlogdp
                    else _m.delta_n.copy()
                )
                _bar_kwargs["label"] = _resolve_label(
                    kwargs.get("bar_label"), _m, f"Measurement {_m.scan_nr}"
                )
                _stairs_kwargs["label"] = (
                    _resolve_label(
                        kwargs.get("stairs_label"), _m, f"Measurement {_m.scan_nr}"
                    )
                    if hist_type != "both"
                    else None
                )
                _secondary_kwargs["label"] = _resolve_label(
                    kwargs.get("secondary_label"),
                    _m,
                    "CDF"
                    if secondary == "cdf"
                    else ("fitted CDF" if secondary == "fit_cdf" else "fitted pdf"),
                )

                if pmf:
                    _data /= sum(_data)

                if hist_type in ["bar", "both"]:
                    bar = _bar_plot(_bar_kwargs, _bar_colors, _data, _m, ax)

                    _handles.append(bar)
                    _labels.append(_bar_kwargs.get("label", ""))

                if hist_type in ["stairs", "both"]:
                    stairs = _stairs_plot(_stairs_kwargs, _stairs_colors, _data, _m, ax)

                    _handles.append(stairs) if hist_type != "both" else None
                    _labels.append(
                        _stairs_kwargs.get("label", "")
                    ) if hist_type != "both" else None

            if secondary:
                if secondary in ["fit_cdf", "fit_pdf"]:
                    raise NotImplementedError

                _color_kwarg = (
                    {} if "color" in _secondary_kwargs else {"color": "black"}
                )

                total = _data.sum()
                cdf = np.cumsum(_data / total) if total > 0 else np.zeros_like(_data)

                ax2 = ax.twinx()
                (line,) = ax2.plot(
                    _m.d_p,
                    cdf,
                    **_color_kwarg,
                    **_secondary_kwargs,
                )

                if c != _cols - 1:
                    ax2.yaxis.set_visible(False)
                else:
                    ax2.set_ylabel("CDF")

                _secondary_handles.append(line)
                _secondary_labels.append(_secondary_kwargs.get("label", ""))

            _format_ax(
                ax,
                data_type,
                pmf,
                xlabel,
                xlim,
                xmajor_formatter,
                ylabel,
                ylim,
                ymajor_formatter,
                yscale,
                xmajor_locations=xmajor_locations,
            )

            h1, l1 = ax.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels() if secondary else ([], [])
            ax.legend(
                h1 + h2, l1 + l2, loc=legend, **_legend_kwargs
            ) if legend and legend not in ["row", "column"] else None

            for spine in spines_invisible or []:
                ax.spines[spine].set_visible(False)

        _secondary_handles, _secondary_labels = _deduplicate_handles_labels(
            _secondary_handles, _secondary_labels
        )

        if legend and legend == "row":
            fig.legend(
                _handles + _secondary_handles,
                _labels + _secondary_labels,
                loc="outside lower center",
                ncol=len(_labels),
                **_legend_kwargs,
            )

        if legend and legend == "column":
            fig.legend(
                _handles + _secondary_handles,
                _labels + _secondary_labels,
                loc="outside right upper",
                **_legend_kwargs,
            )

        if save_as is not None:
            fig.savefig(save_as, bbox_inches="tight", transparent=True)

        plt.show()


def _format_ax(  # pragma: no cover
    ax: Axes,
    data_type: MeasurementDataType,
    pmf: bool,
    xlabel: str | None,
    xlim: tuple[float, float],
    xmajor_formatter: Formatter | str | None,
    ylabel: str | None,
    ylim: tuple[float, float] | None,
    ymajor_formatter: Formatter | str | None,
    yscale: Literal["linear", "log"],
    xmajor_locations: tuple[float, ...] | None = None,
) -> None:
    """Sets the parameters for ax."""
    xmajor_locations = xmajor_locations or (1.0, 2.0, 5.0)
    xminor_locations = tuple(
        x
        for x in (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
        if x not in xmajor_locations
    )

    ax.set_xscale("log")
    ax.set_yscale(yscale)

    ax.xaxis.set_major_locator(
        ticker.LogLocator(base=10.0, subs=xmajor_locations, numticks=15)
    )
    ax.xaxis.set_minor_locator(ticker.LogLocator(base=10.0, subs=xminor_locations))

    _xformatter = coerce_formatter(xmajor_formatter) or ticker.EngFormatter(unit="m")
    ax.xaxis.set_major_formatter(_xformatter)
    ax.xaxis.set_minor_formatter(ticker.NullFormatter())

    _xformatter = coerce_formatter(xmajor_formatter) or ticker.EngFormatter(unit="m")
    _yformatter = coerce_formatter(ymajor_formatter) or (
        linear_sci_formatter()
        if yscale == "linear"
        else ticker.LogFormatterSciNotation()
    )
    ax.xaxis.set_major_formatter(_xformatter)
    ax.yaxis.set_major_formatter(_yformatter)
    ax.tick_params(axis="both", direction="in", which="both")

    ax.set_xlim(*xlim) if xlim != (-np.inf, np.inf) else None
    ax.set_ylim(*ylim) if ylim else None

    _xlabel = xlabel or _get_default_xlabel()
    _ylabel = ylabel or _get_default_ylabel(data_type, pmf)

    ax.set_xlabel(_xlabel)
    ax.set_ylabel(_ylabel)
    ax.label_outer()


def _stairs_plot(  # pragma: no cover
    _stairs_kwargs: dict[str, object],
    _color_generator: Iterator[str],
    _data: FloatArray,
    _m: Measurement,
    ax: Axes,
) -> StepPatch:
    """Plots the stairs plot part."""
    _color_kwarg = {"color": next(_color_generator)}

    stairs = ax.stairs(
        values=_data,
        edges=_m.bin_boundaries,
        **_color_kwarg,
        **_stairs_kwargs,
    )
    return stairs


def _bar_plot(  # pragma: no cover
    _bar_kwargs: dict[str, object],
    _color_generator: Iterator[str],
    _data: FloatArray,
    _m: Measurement,
    ax: Axes,
) -> BarContainer:
    """Plots the bar plot part."""
    _color_kwarg = {"color": next(_color_generator)}

    bar = ax.bar(
        _m.d_p,
        _data,
        width=_m.delta_d_p,
        align="center",
        **_color_kwarg,
        **_bar_kwargs,
    )
    return bar


def _get_default_title() -> str:  # pragma: no cover
    """Gets the default title."""
    return "Histogram"


def _get_default_xlabel() -> str:  # pragma: no cover
    """Gets the default xlabel."""
    return "Particle Diameter"


def _get_default_ylabel(
    data_type: MeasurementDataType, pmf: bool
) -> str:  # pragma: no cover
    """Gets the default ylabel."""
    suffix = ", PMF" if pmf else ", in cm⁻³"

    if data_type == MeasurementDataType.dn:
        return f"Number Concentration\nΔN{suffix}"

    if data_type == MeasurementDataType.dndlogdp:
        return f"Normalized Concentration\nΔN/ΔlogDₚ{suffix}"

    return ""


def _deduplicate_handles_labels(handles: list, labels: list) -> tuple[list, list]:
    """Deduplicated handles and labels.

    Args:
        handles (list): handles.
        labels (list): labels.

    Returns:
        The secondary functions deduplicated legend input.
    """
    seen = set()
    deduped_handles = []
    deduped_labels = []

    for handle, label in zip(reversed(handles), reversed(labels), strict=True):
        if label not in seen:
            seen.add(label)
            deduped_handles.append(handle)
            deduped_labels.append(label)

    return list(reversed(deduped_handles)), list(reversed(deduped_labels))


def _resolve_label(
    label: str | Callable[[Measurement], str] | None,
    m: Measurement,
    default: str,
) -> str:
    """Resolves the label."""
    if label is None:
        return default

    return label(m) if callable(label) else label
