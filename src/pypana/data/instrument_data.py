"""Definition of a dataclass for instrument output.

This module provides a class to store the data and perform calculations on it
"""

from collections.abc import Hashable, Sequence
from pathlib import Path
from textwrap import dedent
from typing import Annotated, Any, Literal

import plotly.graph_objects as go
from pydantic import BaseModel, Field
from rich import inspect

from pypana.console import console
from pypana.data.exceptions.invalid_index_error import InvalidIndexError
from pypana.data.measurement import Measurement
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
        min_length=1,
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

    def info(self, *, verbose: bool = False) -> None:
        """Prints the state of the instrument data."""
        scan_numbers = list(self.measurements.keys())

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

    def select_measurements(
        self,
        indices: Annotated[int, Field(ge=0)]
        | Annotated[Sequence[int], Field(min_length=1)],
        *,
        inplace: bool = True,
        verbose: bool = True,
    ) -> "InstrumentData":
        """Select a subset of measurements bases on indices.

        Args:
            indices (int | list[int]): Indices to select. All have to be valid and not duplicates.
            inplace (bool, optional): Whether to modify the data in this instance. Defaults to True.
            verbose (bool, optional): Whether to output textual hints. Defaults to True.

        Raises:
            InvalidIndexError: If the indices provided are invalid.

        Note:
            inplace=False will not deepcopy the measurement data itself. Its modifications will be reflected in the
            newly returned object.
            Ranges can include empty measurement indices or go beyond the actual measurement
            scan numbers, as long as they are lower bounded by 0 and no duplicates exist.
        """
        selected_indices: Sequence[int] = (
            [indices] if isinstance(indices, int) else indices
        )

        has_duplicates = len(selected_indices) != len(set(selected_indices))

        if has_duplicates or min(selected_indices) < 0:
            raise InvalidIndexError(
                message="Duplicate scan numbers given when selecting measurements",
                invalid_indices=[
                    x for x in set(selected_indices) if selected_indices.count(x) > 1
                ],
            )

        if isinstance(indices, list) and indices not in self.measurements:
            raise InvalidIndexError(
                message="Some scan numbers don't exist in the measurements. To avoid this behaviour, use `range()` "
                "instead.",
                invalid_indices=list(set(indices) - set(self.measurements.keys())),
            )

        selected_measurements: dict[int, Measurement] = {
            i: self.measurements[i]
            for i in selected_indices
            if self.measurements.get(i, None) is not None
        }

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
        xscale: The scaling og the x-axis.
        yscale: The scaling og the y-axis. Defaults to ``linear``.
        xlim: The range on the x-axis to display.
        grid: Whether to show grid lines.
        pmf: Whether to show the probability mass function instead of original values.
        save_as: Path where to store the output image. Defaults to no output.
        additional: Additional function to display. ``cdf``, ``fit_cdf``, or ``fit_pdf``. Defaults to None.
        backend: The backend to use to plot the histogram. Defaults to ``matplotlib``.
        kwargs: Additional Keyword Arguments for the backend.
        """
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
