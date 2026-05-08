"""Methods for plotting histograms of single measurements."""

from pathlib import Path
from typing import Literal

import matplotlib
import numpy as np
import plotly.graph_objects as go
from matplotlib import pyplot as plt
from matplotlib import ticker
from plotly.subplots import make_subplots

from pypana.config import settings
from pypana.data.measurement import FloatArray, Measurement
from pypana.plots.themes import BaseTheme
from pypana.plots.themes.utils import resolve_color
from pypana.utils.measurement_data_type import MeasurementDataType


def plot_hist_single_matplotlib(
    measurement: Measurement,
    *,
    data_type: MeasurementDataType,
    theme: type[BaseTheme] | None = None,
    xscale: Literal["log"] = "log",
    yscale: Literal["linear", "log"] = "linear",
    xlim: tuple[float, float] | None = None,
    grid: bool = False,
    pmf: bool = False,
    save_as: Path | None = None,
    additional: Literal["cdf", "fit_cdf", "fit_pdf"] | None = None,
    **kwargs: object,
) -> None:
    """Plots the histogram of a single measurement with matplotlib.

    Args:
        measurement: The single measurement to display.
        data_type: The data type to display. ``dN/dlogdp`` or ``dN``.
        theme: The theme for the plot. Defaults to ``settings.THEME``.
        xscale: The scaling og the x-axis.
        yscale: The scaling og the y-axis. Defaults to ``linear``.
        xlim: The range on the x-axis to display.
        grid: Whether to show grid lines.
        pmf: Whether to show the probability mass function instead of original values.
        save_as: Path where to store the output image. Defaults to no output.
        additional: Additional function to display. ``cdf``, ``fit_cdf``, or ``fit_pdf``. Defaults to None.
        kwargs: Additional Keyword Arguments for matplotlib.
    """
    _data, _theme, color, legend_label, title, x_label, y_label = _preprocess_data(
        data_type, measurement, pmf, theme, **kwargs
    )
    kwargs.pop("legend_label", None)
    kwargs.pop("color", None)

    handles: list = []
    labels: list = []

    if pmf:
        _data = _data / sum(_data)

    with matplotlib.rc_context(_theme.to_rcparams()):
        fig, ax = plt.subplots(**kwargs)

        bar = ax.bar(
            measurement.d_p,
            _data,
            width=measurement.delta_d_p,
            align="center",
            edgecolor="black",
            label=legend_label,
            color=color,
            **kwargs,
        )

        ax.set_xscale(xscale)
        ax.set_yscale(yscale)
        ax.xaxis.set_major_formatter(ticker.LogFormatterSciNotation())
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.grid(True, which="both", ls="-", alpha=0.3) if grid else None

        handles.append(bar)
        labels.append(legend_label)

        if xlim:
            ax.set_xlim(xlim)

        if additional == "cdf":
            total = _data.sum()
            cdf = np.cumsum(_data / total) if total > 0 else np.zeros_like(_data)

            ax2 = ax.twinx()
            (cdf_line,) = ax2.plot(measurement.d_p, cdf, color="grey", label="CDF")
            ax2.set_ylabel("CDF")
            ax2.set_ylim(0, 1)

            handles.append(cdf_line)
            labels.append("CDF")
        elif additional in ["fit_cdf", "fit_pdf"]:
            raise NotImplementedError

        if save_as is not None:
            fig.savefig(save_as, bbox_inches="tight", **kwargs)

        ax.legend(handles, labels, **kwargs)
        plt.show()


def plot_hist_single_plotly(
    measurement: Measurement,
    *,
    data_type: MeasurementDataType,
    theme: type[BaseTheme] | None = None,
    xscale: Literal["log"] = "log",
    yscale: Literal["linear", "log"] = "linear",
    xlim: tuple[float, float] | None = None,
    grid: bool = False,
    pmf: bool = False,
    additional: Literal["cdf", "fit_cdf", "fit_pdf"] | None = None,
    **kwargs: object,
) -> go.Figure:
    """Plots the histogram of a single measurement with plotly.

    Args:
        measurement: The single measurement to display.
        data_type: The data type to display. ``dN/dlogdp`` or ``dN``.
        theme: The theme for the plot. Defaults to ``settings.THEME``.
        xscale: The scaling og the x-axis.
        yscale: The scaling og the y-axis. Defaults to ``linear``.
        xlim: The range on the x-axis to display.
        grid: Whether to show grid lines.
        pmf: Whether to show the probability mass function instead of original values.
        additional: Additional function to display. ``cdf``, ``fit_cdf``, or ``fit_pdf``. Defaults to None.
        kwargs: Additional Keyword Arguments for plotly.
    """
    _data, _theme, color, legend_label, title, x_label, y_label = _preprocess_data(
        data_type, measurement, pmf, theme, **kwargs
    )
    kwargs.pop("legend_label", None)
    kwargs.pop("color", None)
    kwargs.pop("save_as", None)

    if pmf:
        _data = _data / sum(_data)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=measurement.d_p,
            y=_data,
            width=measurement.delta_d_p,
            marker={
                "color": color,
                "line": {
                    "color": "black",
                    "width": 0.5,
                },
            },
            name=legend_label,
        ),
        secondary_y=False,
    )

    if additional == "cdf":
        total = _data.sum()
        cdf = np.cumsum(_data / total) if total > 0 else np.zeros_like(_data)

        fig.add_trace(
            go.Scatter(
                x=measurement.d_p,
                y=cdf,
                mode="lines",
                line={
                    "color": "grey",
                },
                name="CDF",
            ),
            secondary_y=True,
            **kwargs,
        )
        fig.update_yaxes(title_text="CDF", range=[0, 1], secondary_y=True, **kwargs)

    fig.update_xaxes(
        type=xscale,
        title_text=x_label,
        range=[np.log10(xlim[0]), np.log10(xlim[1])] if xlim else None,
        showgrid=grid,
        **kwargs,
    )

    fig.update_yaxes(
        type=yscale, title_text=y_label, secondary_y=False, showgrid=grid, **kwargs
    )
    fig.update_layout(
        title=title, bargap=0.05, template=_theme.to_plotly_template(), **kwargs
    )

    return fig


def _preprocess_data(
    data_type: MeasurementDataType,
    measurement: Measurement,
    pmf: bool,
    theme: type[BaseTheme] | None,
    **kwargs: object,
) -> tuple[FloatArray, type[BaseTheme], str, str, str, str, str]:
    _data = (
        measurement.delta_n_dlog_dp.copy()
        if data_type == MeasurementDataType.dndlogdp
        else measurement.delta_n.copy()
    )
    _theme = theme or settings.THEME

    x_label = str(kwargs["x_label"]) if "x_label" in kwargs else "Particle Diameter [m]"
    y_label = ""

    if "y_label" in kwargs:
        y_label = str(kwargs["y_label"])
    elif data_type == MeasurementDataType.dndlogdp:
        y_label = f"{'PMF ' if pmf else ''}Number Size Distribution [1/cm³]"
    elif data_type == MeasurementDataType.dn:
        y_label = f"{'PMF ' if pmf else ''}Number concentration per bin ΔN[1/cm³]"

    title = (
        str(kwargs["title"])
        if "title" in kwargs
        else f"Histogram of Measurement '{measurement.scan_nr}'"
    )

    legend_label = (
        str(kwargs["legend_label"])
        if "legend_label" in kwargs
        else f"Scan {measurement.scan_nr}"
    )
    color = resolve_color(kwargs.get("color", 0), _theme)
    return _data, _theme, color, legend_label, title, x_label, y_label
