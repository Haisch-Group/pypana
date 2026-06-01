"""Interactive histogram plot of a single measurement selected via slider."""

from collections.abc import Sequence
from typing import Literal

import matplotlib
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import ticker
from matplotlib.widgets import Slider

from pypana.config import settings
from pypana.data.measurement import FloatArray, Measurement
from pypana.plots.themes import BaseTheme
from pypana.plots.themes.utils import resolve_color
from pypana.utils.measurement_data_type import MeasurementDataType


def plot_hist_single_interactive_matplotlib(  # pragma: no cover # noqa: PLR0915
    measurements: Sequence[Measurement],
    *,
    data_type: MeasurementDataType,
    theme: type[BaseTheme] | None = None,
    xscale: Literal["log"] = "log",
    yscale: Literal["linear", "log"] = "linear",
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    autoscale: Literal["x", "y", "both", "none"] = "both",
    grid: bool = True,
    pmf: bool = False,
    additional: Literal["cdf", "fit_cdf", "fit_pdf"] | None = None,
    **kwargs: object,
) -> None:
    """Plots the histograms of multiple measurements with a slider to switch between them.

    Missing entries in ``measurements`` are skipped.

    Args:
       measurements: Measurements to browse; ``None`` marks a missing slot.
       data_type: The data type to display. ``dN/dlogdp`` or ``dN``.
       theme: The theme for the plot. Defaults to ``settings.THEME``.
       xscale: The scaling of the x-axis.
       yscale: The scaling of the y-axis.
       xlim: Fixed x-limits. Overrides x-autoscaling when provided.
       ylim: Fixed y-limits. Overrides y-autoscaling when provided.
       autoscale: Which axes to autoscale per selected measurement.
           ``"none"`` requires both ``xlim`` and ``ylim`` to be set.
       grid: Whether to show grid lines.
       pmf: Whether to show the probability mass function instead of original values.
       additional: Additional function to display.
       x_label: Override for the x-axis label.
       y_label: Override for the y-axis label.
       kwargs: Additional keyword arguments forwarded to matplotlib.

    Keyword Args:
          arg1: something something
    """
    _theme = theme or settings.THEME

    if not measurements:
        raise ValueError("No measurements to display.")

    if autoscale == "none" and (xlim is None or ylim is None):
        raise ValueError("autoscale='none' requires xlim and ylim to be provided.")
    if autoscale == "x" and ylim is None:
        raise ValueError("autoscale='x' requires ylim to be provided.")
    if autoscale == "y" and xlim is None:
        raise ValueError("autoscale='y' requires xlim to be provided.")

    if additional in ["fit_cdf", "fit_pdf"]:
        raise NotImplementedError()

    ref = measurements[0]
    same_bins = all(
        m.d_p.shape == ref.d_p.shape
        and np.allclose(m.d_p, ref.d_p)
        and np.allclose(m.delta_d_p, ref.delta_d_p)
        for m in measurements
    )

    x_label = str(kwargs["x_label"]) if "x_label" in kwargs else "Particle Diameter [m]"
    y_label = ""

    if "y_label" in kwargs:
        y_label = str(kwargs["y_label"])
    elif data_type == MeasurementDataType.dndlogdp:
        y_label = f"{'PMF ' if pmf else ''}Number Size Distribution [1/cm³]"
    elif data_type == MeasurementDataType.dn:
        y_label = f"{'PMF ' if pmf else ''}Number concentration per bin ΔN[1/cm³]"

    def _data_for(m: Measurement) -> FloatArray:  # pragma: no cover
        arr = (
            m.delta_n_dlog_dp.copy()
            if data_type == MeasurementDataType.dndlogdp
            else m.delta_n.copy()
        )

        if pmf:
            total = arr.sum()
            arr = arr / total if total > 0 else np.zeros_like(arr)

        return arr

    def _compute_lims(  # pragma: no cover
        m: Measurement, data: FloatArray
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        x_low = m.bin_boundaries[0]
        x_high = m.bin_boundaries[-1]

        y_low = 0
        y_high = data.max() * 1.1

        return (min(x_low, 0), x_high), (y_low, y_high)

    with matplotlib.rc_context(_theme.to_rcparams()):
        fig, ax = plt.subplots(**kwargs)
        fig.subplots_adjust(bottom=0.22)

        ax.set_xscale(xscale)
        ax.set_yscale(yscale)
        ax.xaxis.set_major_formatter(ticker.LogFormatterSciNotation())
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        ax.grid(True, which="both", ls="-", alpha=0.3) if grid else None

        if additional == "cdf":
            ax2 = ax.twinx()

            ax2.set_ylabel("CDF")
            ax2.set_ylim(0, 1)

        state: dict = {
            "bars": None,
            "cdf_line": None,
        }

        def _draw(pos: int) -> None:  # pragma: no cover # noqa: PLR0912
            m = list(filter(lambda ms: ms.scan_nr == pos, measurements))

            if m is None:
                return

            m = m[0]

            data = _data_for(m)
            color = resolve_color(pos, _theme)
            label = f"Scan {m.scan_nr}"

            if same_bins and state["bars"] is not None:
                for rect, h in zip(state["bars"], data, strict=True):
                    (rect.set_height(h),)
                    rect.set_facecolor(color)

                state["bars"].set_label(label)
            else:
                if state["bars"] is not None:
                    state["bars"].remove()

                state["bars"] = ax.bar(
                    m.d_p,
                    data,
                    width=m.delta_d_p,
                    align="center",
                    edgecolor="black",
                    color=color,
                    label=label,
                )

            if additional == "cdf":
                total = data.sum()
                cdf = np.cumsum(data / total) if total > 0 else np.zeros_like(data)

                if state["cdf_line"] is None:
                    (state["cdf_line"],) = ax2.plot(
                        m.d_p, cdf, color="grey", labels="CDF"
                    )
                else:
                    state["cdf_line"].set_data(m.d_p, cdf)

            auto_x = autoscale in ("x", "both") and xlim is None
            auto_y = autoscale in ("y", "both") and ylim is None

            if auto_x or auto_y:
                (x_lo, x_hi), (y_lo, y_hi) = _compute_lims(m, data)
                if auto_x:
                    ax.set_xlim(x_lo, x_hi)
                if auto_y:
                    ax.set_ylim(y_lo, y_hi)

            if xlim is not None:
                ax.set_xlim(xlim)
            if ylim is not None:
                ax.set_ylim(ylim)

            ax.set_title(f"Histogram of Measurement {m.scan_nr}")

            handles = [state["bars"]]
            labels = [label]
            if additional == "cdf":
                handles.append(state["cdf_line"])
                labels.append("CDF")

            ax.legend(handles=handles, labels=labels)

            fig.canvas.draw_idle()

        _draw(measurements[0].scan_nr)

        slider_ax = fig.add_axes((0.15, 0.08, 0.7, 0.04))
        slider = Slider(
            slider_ax,
            "Scan nr.",
            valmin=min([m.scan_nr for m in measurements if m is not None]),
            valmax=max([m.scan_nr for m in measurements if m is not None]),
            valinit=measurements[0].scan_nr,
            valstep=1,
        )

        def _on_changed(val: float) -> None:  # pragma: no cover
            _draw(int(val))

        slider.on_changed(_on_changed)
        fig._hist_slider = slider

        plt.show()
