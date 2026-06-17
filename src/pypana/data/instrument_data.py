"""Definition of a dataclass for instrument output.

This module provides a class to store the data and perform calculations on it
"""

import copy
from collections.abc import Callable, Hashable
from pathlib import Path
from textwrap import dedent
from typing import Annotated, Any, Literal, Self, overload

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from matplotlib.ticker import Formatter
from pydantic import BaseModel, Field
from rich import inspect

from pypana.console import console
from pypana.data.collection_efficiency import CollectionEfficiency
from pypana.data.exceptions.invalid_index_error import InvalidIndexError
from pypana.data._measurement import Measurement
from pypana.data.utils import get_xlims, is_full_rectangular_matrix
from pypana.exceptions.incompatible_argument_error import IncompatibleArgumentError
from pypana.plots.histograms.hist_matrix import plot_hist_matrix
from pypana.plots.histograms.hist_single import (
    plot_hist_single_matplotlib,
    plot_hist_single_plotly,
)
from pypana.plots.scatter.collection_efficiency import plot_collection_efficiency
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

    def __len__(self) -> int:
        return len(self.measurements)

    @overload
    def __getitem__(self, index: int) -> Measurement: ...

    @overload
    def __getitem__(self, index: slice) -> Self: ...

    def __getitem__(self, index: int | slice) -> Measurement | Self:
        if isinstance(index, int):
            return self.measurements[index]

        elif isinstance(index, slice):
            try:
                scan_nrs = list(self.measurements.keys())[index]
                return self.keep_measurements(scan_nrs, inplace=False, verbose=False)
            except InvalidIndexError as e:
                raise ValueError(
                    "Unexpected indices. If the Measurements are currently not contiguous,"
                    "call `reindex()` first."
                ) from e

        else:
            raise TypeError()

    def apply(self, f: Callable[[Self], Self]) -> Self:
        """Applies a function to this InstrumentData object.

        Args:
            f: The function or lambda to apply.

        Returns:
            The output of the supplied function.
        """
        return f(self)

    def mapply(self, f: Callable[[Measurement], Measurement]) -> Self:
        """Applies a function all contained Measurements.

        Args:
            f: The function or lambda to apply.

        Returns:
            Itself with modified Measurements.

        Note:
            This operation is inplace in regard to the InstrumentData object.
        """
        _measurements = {k: f(v) for k, v in self.measurements.items()}
        self.measurements = _measurements

        return self

    def permute(self, p: list[int]) -> Self:
        """Permutes the order of Measurements.

        Args:
            p: The permutation list where the position of a listed index is its new index.

        Returns:
            Itself with permuted Measurements.
        """
        if not set(p).issubset(set(self.measurements.keys())):
            raise ValueError(
                f"Unexpected indices: {set(p) - set(self.measurements.keys())}"
            )

        _measurements: dict[int, Measurement] = {}
        for new, old in enumerate(p, start=0):
            _measurements[new] = self.measurements[old]

        self.measurements = _measurements
        return self

    def reindex(self) -> Self:
        """Re-indexes the InstrumentData object.

        Returns:
            Itself, but with contiguous Measurement keys ranging from `0..(len(measurements)-1)`
        """
        p = list(self.measurements.keys())
        return self.permute(p)

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

    def summary(self) -> pd.DataFrame:
        """A debug DataFrame with one row per measurement.

        Index is the measurement key. Columns are the keys of ``Measurement.summary()``.

        Returns:
            The overview DataFrame.
        """
        rows = {key: m.summary() for key, m in self.measurements.items()}
        return pd.DataFrame.from_dict(rows, orient="index")

    def keep_measurements(  # noqa: PLR0912
        self,
        scan_nrs: Annotated[int | list[int] | range, Field(min_length=1)],
        *,
        inplace: bool = True,
        deepcopy: bool = False,
        verbose: bool = True,
    ) -> Self:
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
            return self.__class__(
                measurements=copy.deepcopy(selected_measurements),
                device_name=copy.deepcopy(self.device_name),
                file_path=copy.deepcopy(self.file_path),
            )

        if inplace:
            self.measurements = selected_measurements
            return self

        return self.__class__(
            measurements=selected_measurements,
            device_name=self.device_name,
            file_path=self.file_path,
        )

    def cut(self, d: tuple[float, float]) -> Self:
        """Sets bins with midpoint diameter outside the lower and higher bound to zero.

        Args:
            d (tuple[float, float]): The boundaries in (lower, higher)

        Returns:
            Itself, after applying the changes


        Note:
            This operation is inplace.
        """
        return self.mapply(lambda m: m.cut(d))

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
        xmajor_locations: tuple[float, ...] | None = None,
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
            xmajor_locations (tuple): The float values between 1.0 and 10.0 where major ticks are plotted.
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
            xmajor_locations=xmajor_locations,
            ylabel=ylabel,
            ylim=ylim,
            ymajor_formatter=ymajor_formatter,
            yscale=yscale,
            **kwargs,
        )

    def collection_efficiency(
        self,
        m: tuple[int, int] | range | slice | None = None,
        *,
        fit: Literal["sigmoid", "gompertz"] | None = "sigmoid",
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
    ) -> CollectionEfficiency:
        """Computes and plots the collection efficiency from consecutive (upstream, downstream) pairs.

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
            m (tuple[int, int] | range | slice | None): The measurement pairs. Defaults to
                ``None``, which uses *all* measurements in insertion order as consecutive
                ``(up, down)`` pairs (the total count must be even and ≥ 2). A ``tuple``
                ``(lo, hi)`` selects all scan numbers ``s`` with ``lo ≤ s ≤ hi`` and pairs
                them consecutively. A ``range`` or ``slice`` selects consecutive
                measurements by *position* in ``self.measurements``. All selections must
                yield an even, ≥ 2 count. Use ``permute()`` beforehand to arrange them.
            fit (str | None): The fit to overlay on the scatter. ``"sigmoid"`` extracts the
                cut diameter ``d_50``. ``"gompertz"`` allows non-0/100% asymptotes. ``None``
                plots only the data points. Defaults to ``"sigmoid"``.
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
            scatter_label (str | Callable[[CollectionEfficiency], str] | None): The legend label for
                the data points. Defaults to an adaptive label. Also supports a lambda function that
                takes the CollectionEfficiency object as input.

            fit_color (str): The color of the fit line. Defaults to the matplotlib default.
            fit_linestyle (str): The linestyle of the fit line. Defaults to ``"-"``.
            fit_linewidth (float): The linewidth of the fit line. Defaults to the matplotlib default.
            fit_label (str | Callable[[CollectionEfficiency], str] | None): The legend label for the fit.
                Defaults to an adaptive label (model name and ``d_50`` if available). Also supports a
                lambda function that takes the CollectionEfficiency object as input.
            fit_n_points (int): Number of points to evaluate the fit on. Defaults to ``1000``.

            grid_color (str): The color of the grid lines. Defaults to the matplotlib default.
            grid_linewidth (float): The linewidth of the grid lines. Defaults to the matplotlib default.
            grid_which (str): What type of grid to show. Either ``"major"``, ``"minor"``, or ``"both"``.

            legend_labelcolor (str): The color of the legend labels. Defaults to the matplotlib default.
            legend_loc (str): The location of the matplotlib legend. Defaults to the matplotlib default.

        Returns:
            The ``CollectionEfficiency`` result.

        Raises:
            InvalidIndexError: If any scan number is not present.
            ValueError: If the input shape is invalid or an upstream total concentration is 0.
            ParticleAnalysisError: If an internal error occurs during plotting.
        """
        keys = list(self.measurements.keys())

        if m is None:
            scan_nrs = keys
            if len(scan_nrs) == 0 or len(scan_nrs) % 2 != 0:
                raise ValueError(
                    f"Cannot pair all measurements: need an even, ≥ 2 number, "
                    f"got {len(scan_nrs)}."
                )

        elif isinstance(m, tuple):
            lo, hi = m
            if lo > hi:
                raise ValueError(
                    f"Tuple bounds must satisfy lower ≤ upper, got ({lo}, {hi})."
                )

            scan_nrs = [s for s in keys if lo <= s <= hi]
            if not scan_nrs:
                raise InvalidIndexError(
                    message=f"No scans in bound range [{lo}, {hi}].",
                    invalid_indices=[],
                )

            if len(scan_nrs) == 0 or len(scan_nrs) % 2 != 0:
                raise ValueError(
                    f"Bound selection [{lo}, {hi}] yielded {len(scan_nrs)} scans; "
                    f"need an even, ≥ 2 number."
                )

        elif isinstance(m, (range, slice)):
            try:
                scan_nrs = keys[m] if isinstance(m, slice) else [keys[i] for i in m]
            except IndexError as e:
                raise InvalidIndexError(
                    message=f"Position out of range for {len(keys)} measurements.",
                    invalid_indices=[],
                ) from e
            if len(scan_nrs) == 0 or len(scan_nrs) % 2 != 0:
                raise ValueError(
                    f"Selection must have an even, ≥ 2 number of measurements, got {len(scan_nrs)}."
                )

        else:
            raise TypeError(
                f"Expected None, tuple, range, or slice, got {type(m).__name__}."
            )

        ups, downs = scan_nrs[0::2], scan_nrs[1::2]

        n_ups = np.array([float(self.measurements[s].n_total) for s in ups])
        n_downs = np.array([float(self.measurements[s].n_total) for s in downs])
        if np.any(n_ups == 0):
            raise ValueError(
                "Upstream measurement has zero total concentration; η is undefined."
            )

        ce = CollectionEfficiency(
            d_p=np.array([self.measurements[s].geo_mean for s in downs], dtype=float),
            eta=1.0 - n_downs / n_ups,
            upstream_scan_nrs=ups,
            downstream_scan_nrs=downs,
        )

        plot_collection_efficiency(
            ce,
            fit=fit,
            theme=theme,
            save_as=save_as,
            legend=legend,
            spines_invisible=spines_invisible,
            title=title,
            xlabel=xlabel,
            xlim=xlim,
            xmajor_formatter=xmajor_formatter,
            xscale=xscale,
            ylabel=ylabel,
            ylim=ylim,
            ymajor_formatter=ymajor_formatter,
            yscale=yscale,
            **kwargs,
        )

        return ce
