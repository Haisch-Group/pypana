"""Methods for plotting histograms of measurements in a matrix format."""

from typing import Literal

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker
from matplotlib.ticker import Formatter

from pypana.config import settings
from pypana.data.measurement import Measurement
from pypana.data.utils import linear_sci_formatter
from pypana.plots.themes import BaseTheme
from pypana.plots.utils import split_kwargs
from pypana.utils.measurement_data_type import MeasurementDataType


def plot_hist_matrix(
    m: list[list[Measurement]],
    data_type: MeasurementDataType,
    *,
    theme: BaseTheme | None = None,
    hist_type: Literal["bar", "stairs", "both"] = "bar",
    secondary: Literal["cdf", "fit_cdf", "fit_pdf"] | None = None,
    save_as: str | None = None,
    legend: bool = True,
    pmf: bool = False,
    spines_invisible: list[Literal["left", "right", "top", "bottom"]] | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    xlim: tuple[float, float] = (-np.inf, np.inf),
    xmajor_formatter: Formatter | str | None = None,
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
        secondary (str): The additional function to plot.
            "fit_cdf" and "fit_pdf" require the measurement to already be fitted previously. Both currently raise
            NotImplementedError. Defaults to ``None``.
        save_as (str | None): The path where to save the figure. Defaults to ``None`` which does not save.
        legend (bool): Whether to show the legend. Defaults to ``True``.
        pmf (bool): Whether to plot the measurement as probability mass function. Defaults to ``False``.
        spines_invisible (list): The spines not to show. Defaults to ``None``, in which case all are plotted.
        title (str | None): The title of the plot. Defaults to ``None`` and uses an adaptive title.
        xlabel (str | None): The x-axis label of the plot. Defaults to ``None`` and uses an adaptive title.
        xlim (tuple): The x-axis lower and upper bound.
        xmajor_formatter (Formatter | str): The matplotlib ticker.Formatter for the x-axis.
        ylabel (str | None): The y-axis label of the plot. Defaults to ``None`` and uses an adaptive title.
        ylim (tuple): The y-axis lower and upper bound. Can be used to give specific y-ranges on the axis.
        ymajor_formatter (Formatter | str): The matplotlib ticker.Formatter for the y-axis.
        yscale (str): The type of scaling the y-axis uses. Defaults to ``"linear"``.
        kwargs: The additional kwargs for matplotlib. See the Keyword Args section for more information.
    """
    _rows = len(m[0])
    _cols = len(m)
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

    with matplotlib.rc_context(_theme.to_rcparams()):
        fig, axs = plt.subplots(_rows, _cols, sharex=True, sharey=True, squeeze=False)

        _title = title or get_adaptive_title()
        fig.suptitle(_title)

        for (r, c), ax in np.ndenumerate(axs):
            ax.grid()

            _m: Measurement = m[r][c]
            _data = (
                _m.delta_n_dlog_dp.copy()
                if data_type == MeasurementDataType.dndlogdp
                else _m.delta_n.copy()
            )

            if pmf:
                _data /= sum(_data)

            if hist_type in ["bar", "both"]:
                _color_kwarg = (
                    {}
                    if "facecolor" in _bar_kwargs
                    else {"color": _colors[(r * _cols + c) % len(_colors)]}
                )

                bar = ax.bar(
                    _m.d_p,
                    _data,
                    width=_m.delta_d_p,
                    align="center",
                    **_color_kwarg,
                    **_bar_kwargs,
                )

                _handles.append(bar)
                _labels.append(_bar_kwargs.get("label", ""))

            if hist_type in ["stairs", "both"]:
                _color_kwarg = (
                    {}
                    if "facecolor" in _stairs_kwargs
                    else {"color": _colors[(r * _cols + c) % len(_colors)]}
                )

                stairs = ax.stairs(
                    values=_data,
                    edges=_m.bin_boundaries,
                    **_color_kwarg,
                    **_stairs_kwargs,
                )

                _handles.append(stairs)
                _labels.append(_stairs_kwargs.get("label", ""))

            if secondary:
                if secondary in ["fit_cdf", "fit_pdf"]:
                    raise NotImplementedError

                _color_kwarg = (
                    {} if "color" in _secondary_kwargs else {"color": "black"}
                )

                total = _data.sum()
                cdf = np.cumsum(_data / total) if total > 0 else np.zeros_like(_data)

                ax2 = ax.twinx()
                (line,) = ax2.plot(  # TODO: add alpha=0.7 to kwargs
                    _m.d_p,
                    cdf,
                    **_color_kwarg,
                    **_secondary_kwargs,
                )

                _handles.append(line)
                _labels.append("CDF")

            ax.set_xscale("log")
            ax.set_yscale(yscale)

            _xformatter = xmajor_formatter or ticker.EngFormatter(unit="m")
            _yformatter = ymajor_formatter or (
                linear_sci_formatter()
                if yscale == "linear"
                else ticker.LogFormatterSciNotation()
            )
            ax.xaxis.set_major_formatter(_xformatter)
            ax.yaxis.set_major_formatter(_yformatter)
            ax.tick_params(axis="both", direction="in", which="both")

            ax.set_xlim(*xlim) if xlim != (-np.inf, np.inf) else None
            ax.set_ylim(*ylim) if ylim else None

            for spine in spines_invisible or []:
                ax.spines[spine].set_visible(False)

        if save_as is not None:
            fig.savefig(save_as, bbox_inches="tight", transparent=True)

        plt.show()


def get_adaptive_title() -> str:
    """Gets the default adaptive title."""
    return "Test Test 123"
