"""Definition of a dataclass for instrument output.

This module provides a class to store the data and perform calculations on it
"""

import copy
from collections.abc import Hashable
from pathlib import Path
from textwrap import dedent
from typing import Annotated, Any, Literal

import numpy as np
import plotly.graph_objects as go
from matplotlib.ticker import Formatter
from pydantic import BaseModel, Field
from rich import inspect

from pypana.console import console
from pypana.data.exceptions.invalid_index_error import InvalidIndexError
from pypana.data.measurement import Measurement
from pypana.data.utils import get_xlims, is_full_rectangular_matrix
from pypana.exceptions.incompatible_argument_error import IncompatibleArgumentError
from pypana.plots.histograms.hist_matrix import plot_hist_matrix
from pypana.plots.histograms.hist_single import (
    plot_hist_single_matplotlib,
    plot_hist_single_plotly,
)
from pypana.plots.themes import BaseTheme
from pypana.utils.debug import Debuggable
from pypana.utils.measurement_data_type import MeasurementDataType


class InstrumentData(BaseModel, Debuggable):
    """Data class for instrument data."""

    model_config = {"arbitrary_types_allowed": True}

    measurements: dict[int, Measurement] = Field(
        default_factory=dict,
        description="List of measurement data to include in the analysis",
    )

    device_name: str = Field(
        default="",
        description="Name of the device the data was measured on",
    )

    file_path: Path | None = Field(
        default=None,
        description="Path to the imported measurement file",
    )

    other_info: dict[Hashable, Any] = Field(
        default_factory=dict,
        description="Other info about the measurements that might be required.",
    )

    def info(self, *, verbose: bool = False) -> None:  # pragma: no cover
        """Prints the state of the instrument data."""
        scan_numbers = list(self.measurements.keys())

        if not scan_numbers:
            console.print("[bold]No Analyzable Measurements![/bold]\n")
        else:
            first_scan = scan_numbers[0]
            last_scan = scan_numbers[-1]
            first_scan_time = self.measurements[first_scan].time
            last_scan_time = self.measurements[last_scan].time

            console.print(
                f"[bold]Analyzable Measurements:[/bold]\n"
                f"[cyan]{len(scan_numbers)}[/cyan] measurements ([cyan]{first_scan}[/cyan] → [cyan]{last_scan}[/cyan])\n"
                f"between [magenta]{first_scan_time:%Y-%m-%d %H:%M:%S}[/magenta] and "
                f"[magenta]{last_scan_time:%Y-%m-%d %H:%M:%S}[/magenta] "
                f"(Duration: [magenta]{last_scan_time - first_scan_time}[/magenta])"
            )

        console.print(self.other_info)

        if verbose:
            inspect(self)

    def keep_measurements(  # noqa: PLR0912
        self,
        scan_nrs: Annotated[int | list[int] | range, Field(min_length=1)],
        *,
        inplace: bool = True,
        deepcopy: bool = False,
        verbose: bool = True,
    ) -> "InstrumentData":
        """Select a subset of measurements bases on indices.

        Args:
            scan_nrs (int | list[int] | range): Indices to select. All have to be valid and not duplicates.
            inplace (bool, optional): Whether to modify the data in this instance. Defaults to `True``
            deepcopy (bool, optional): Whether to deepcopy the data in this instance. Defaults to ``False``.
                If ``True``, it has precedence over inplace.
            verbose (bool, optional): Whether to output textual hints. Defaults to True.

        Raises:
            InvalidIndexError: If the indices provided are invalid.

        Note:
            inplace=False will not deepcopy the measurement data itself. Its modifications will be reflected in the
            newly returned object.
            Ranges can include empty measurement indices or go beyond the actual measurement
            scan numbers, as long as they are lower bounded by 0 and no duplicates exist.
        """
        valid_scan_nrs: list[int] | range

        if isinstance(scan_nrs, int):
            if scan_nrs < 0:
                raise InvalidIndexError(
                    message="Negative scan number given.", invalid_indices=[scan_nrs]
                )
            if scan_nrs not in self.measurements:
                raise InvalidIndexError(
                    message="Scan number doesn't exist.", invalid_indices=[scan_nrs]
                )

            valid_scan_nrs = [scan_nrs]
        else:
            if min(scan_nrs) < 0:
                raise InvalidIndexError(
                    message="Negative scan numbers given.",
                    invalid_indices=[x for x in scan_nrs if x < 0],
                )

            if isinstance(scan_nrs, list):
                if len(scan_nrs) != len(set(scan_nrs)):
                    raise InvalidIndexError(
                        message="Duplicate scan numbers given.",
                        invalid_indices=[
                            x for x in set(scan_nrs) if scan_nrs.count(x) > 1
                        ],
                    )

                missing_scan_nrs = set(scan_nrs) - set(self.measurements.keys())
                if missing_scan_nrs:
                    raise InvalidIndexError(
                        message="Some scan numbers don't exist. Use `range()` instead.",
                        invalid_indices=list(missing_scan_nrs),
                    )

            valid_scan_nrs = scan_nrs

        selected_measurements: dict[int, Measurement] = {
            i: self.measurements[i] for i in valid_scan_nrs if i in self.measurements
        }

        if not selected_measurements:
            raise InvalidIndexError(
                "No valid measurements found for the given scan numbers.",
                invalid_indices=[],
            )

        if verbose:
            selected_ordered = sorted(selected_measurements.keys())

            first = selected_measurements[selected_ordered[0]]
            last = selected_measurements[selected_ordered[-1]]

            console.print(
                dedent(f"""\
                [bold]Selected Measurements:[/bold]
                 [Scan [cyan]{first.scan_nr}[/cyan] at time [magenta]{first.time:%Y-%m-%d %H:%M:%S}[/magenta]] \\
                 → [Scan [cyan]{last.scan_nr}[/cyan] at time [magenta]{last.time:%Y-%m-%d %H:%M:%S}[/magenta]]
            """)
            )

        if deepcopy:
            return InstrumentData(
                measurements=copy.deepcopy(selected_measurements),
                device_name=copy.deepcopy(self.device_name),
                file_path=copy.deepcopy(self.file_path),
            )

        if inplace:
            self.measurements = selected_measurements
            return self

        return InstrumentData(
            measurements=selected_measurements,
            device_name=self.device_name,
            file_path=self.file_path,
        )

    def plot_histogram_single(
        self,
        measurement: int,
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
        backend: Literal["matplotlib", "plotly"] = "plotly",
        **kwargs: object,
    ) -> None | go.Figure:
        """Plots the histogram of a single measurement selected.

        Args:
            measurement: The single measurement to display.
            data_type: The data type to display. ``dN/dlogdp`` or ``dN``.
            theme: The theme for the plot. Defaults to ``settings.THEME``.
            xscale: The scaling of the x-axis.
            yscale: The scaling of the y-axis. Defaults to ``linear``.
            xlim: The range on the x-axis to display.
            grid: Whether to show grid lines.
            pmf: Whether to show the probability mass function instead of original values.
            save_as: Path where to store the output image. Defaults to no output.
            additional: Additional function to display. ``cdf``, ``fit_cdf``, or ``fit_pdf``. Defaults to None.
            backend: The backend to use to plot the histogram. Defaults to ``matplotlib``.
            kwargs: Additional Keyword Arguments for the backend.
        """
        if measurement not in self.measurements:
            raise InvalidIndexError(
                message="Invalid scan number.", invalid_indices=[measurement]
            )

        if backend == "matplotlib":
            plot_hist_single_matplotlib(
                self.measurements[measurement],
                data_type=data_type,
                theme=theme,
                xscale=xscale,
                yscale=yscale,
                xlim=xlim,
                grid=grid,
                pmf=pmf,
                save_as=save_as,
                additional=additional,
                **kwargs,
            )
            return None
        else:
            return plot_hist_single_plotly(
                self.measurements[measurement],
                data_type=data_type,
                theme=theme,
                xscale=xscale,
                yscale=yscale,
                xlim=xlim,
                grid=grid,
                pmf=pmf,
                save_as=save_as,
                additional=additional,
                **kwargs,
            )

    def histogram(
        self,
        m: int | tuple[int, ...] | list[list[int | tuple[int, ...]]],
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
        xlim: tuple[float, float] | None = None,
        xmajor_formatter: Formatter | str | None = None,
        xspace_sides: float = 0.0,
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
            m (int | list[list[int]]): The measurement(s) to plot the histogram for. For a grid, the
                measurements are given row-major like numpy. Has to be a full rectangular matrix.
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
            xlim (tuple): The x-axis lower and upper bound. Can be used to manually set blank space on the sides
                or specify x-axis ranges. Defaults to ``None`` which is equivalent to `xpace_sides=0`.
            xmajor_formatter (Formatter | str): The matplotlib ticker.Formatter for the x-axis.
            xspace_sides (float): The total percentage of the plot that should be empty space on both sides.
                Each side gets half the specified space. If not the default, it is mutually exclusive with xlim.
                Defaults to ``0.0`` which plots exactly the range from the lowest to the highest bin boundary.
            ylabel (str | None): The y-axis label of the plot. Defaults to ``None`` and uses an adaptive title.
            ylim (tuple): The y-axis lower and upper bound. Can be used to give specific y-ranges on the axis.
            ymajor_formatter (Formatter | str): The matplotlib ticker.Formatter for the y-axis.
            yscale (str): The type of scaling the y-axis uses. Defaults to ``"linear"``.
            kwargs: The additional kwargs for matplotlib. See the Keyword Args section for more information.

        Keyword Args:
            bar_edgecolor (str): The edgecolor of the bar. Can only be specified when hist_type="bar" or "both".
                Can be either a hex code, e.g. "#000000" or from the color cycle, e.g. "C0".
                Defaults to the matplotlib default.
            bar_facecolor (str): The facecolor of the bar. Can only be specified when hist_type="bar" or "both".
                Can be either a hex code, e.g. "#000000"" or from the color cycle, e.g. "C0".
                Defaults to the matplotlib default.
            bar_hatch (str): The bar hatches. Can only be specified when hist_type="bar" or "both". If not specified,
                the bars are filled with the facecolor.
            bar_label (str | Callable[[Measurement], str] | None): The legend label for the bar.
                Defaults to an adaptive label. Also supports a lambda function that takes a measurement object as input.
            bar_linewidth (str): the edge linewidth of the bars. Can only be specified when hist_type="bar" or "both".
                Defaults to the matplotlib default.

            grid_color (str): The color of the grid lines. Can be either a hex code, e.g. "#000000"
                or from the color cycle, e.g. "C0". Defaults to the matplotlib default.
            grid_linewidth (float): The linewidth of the grid lines. Defaults to the matplotlib default.
            grid_which (str): What type of grid to show. Either "major", "minor", or "both".

            legend_labelcolor (str): The color of the legend labels. Can be either a hex code, e.g. "#000000"
                or from the color cycle, e.g. "C0". Can only be specified when legend=True.
                Defaults to the matplotlib default.
            legend_loc (str): The location of the matplotlib legend. Can only be specified when legend=True.
                Defaults to the matplotlib default.

            secondary_color (str): The color of the line plot that shows the secondary function.
                Can be either a hex code, e.g. "#000000" or from the color cycle, e.g. "C0". Can only be specified
                when secondary is not None.
            secondary_fmt (str): The format of the line plot that shows the secondary function. Can only be specified
                when secondary is not None.
            secondary_label (str | Callable[[Measurement], str] | None):
                The label of the secondary function for the legend. Can only be specified when secondary is not None.
                Defaults to an adaptive label. Also supports a lambda function that takes a measurement object as input.
            secondary_linestyle (str): The linestyle of the line plot that shows the secondary function.
                Can only be specified when secondary is not None. Defaults to the matplotlib default.
            secondary_linewidth (float): The linewidth of the line of the secondary function. Can only be specified
                when secondary is not None. Defaults to the matplotlib default.

            stairs_color: The color of the stairs plot. Can be either a hex code, e.g. "#000000"
                or from the color cycle, e.g. "C0". Can only be specified when hist_type="stairs" or "both".
                Defaults to the matplotlib default.
            stairs_label (str | Callable[[Measurement], str] | None): The legend label for the stairs.
                Defaults to an adaptive label. Also supports a lambda function that takes a measurement object as input.
            stairs_linestyle (str): The linestyle of the stairs plot. Can only be specified when
                hist_type="stairs" or "both". Defaults to the matplotlib default.
            stairs_linewidth (str): The linewidth of the stairs plot. Can only be specified when
                hist_type="stairs" or "both". Defaults to the matplotlib default.

        Raises:
            NotImplementedError: If the functionality is currently not supported and is only a placeholder.
            ParticleAnalysisError: If an internal error occurs during plotting.
        """
        _measurements: list[list[tuple[int, ...]]] = []
        _lowest_bound: float
        _highest_bound: float

        if isinstance(m, int):
            _measurements = [[(m,)]]

        elif isinstance(m, tuple):
            _measurements = [[m]]

        elif isinstance(m, list):
            _measurements = [
                [(_m,) if isinstance(_m, int) else _m for _m in inner] for inner in m
            ]

        if not is_full_rectangular_matrix(_measurements):
            raise InvalidIndexError(
                message="The measurement matrix is not full!",
            )

        _xlim: tuple[float, float] = (-np.inf, np.inf)
        if xspace_sides != 0.0:
            if xlim is not None:
                raise IncompatibleArgumentError(
                    message="Argument 'xspace_sides' is incompatible.",
                    incompatible_with=[("xlim", xlim)],
                )

            _xlim = get_xlims(
                [
                    _m
                    for _m in self.measurements.values()
                    if _m.scan_nr in sum(_measurements, [])
                ],
                xspace_sides,
            )

        if xlim is not None:
            if xlim[0] >= xlim[1]:
                raise ValueError

            _xlim = xlim

        plot_hist_matrix(
            [
                [tuple(self.measurements[_m] for _m in tup) for tup in inner]
                for inner in _measurements
            ],
            data_type,
            theme=theme,
            hist_type=hist_type,
            secondary=secondary,
            save_as=save_as,
            legend=legend,
            pmf=pmf,
            spines_invisible=spines_invisible,
            title=title,
            xlabel=xlabel,
            xlim=_xlim,
            xmajor_formatter=xmajor_formatter,
            ylabel=ylabel,
            ylim=ylim,
            ymajor_formatter=ymajor_formatter,
            yscale=yscale,
            **kwargs,
        )
