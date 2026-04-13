"""Definition of a dataclass for instrument output.

This module provides a class to store the data and perform calculations on it
"""

from collections.abc import Hashable, Sequence
from pathlib import Path
from textwrap import dedent
from typing import Annotated, Any

from pydantic import BaseModel, Field

from pypana.console import console
from pypana.data.exceptions.invalid_index_error import InvalidIndexError
from pypana.data.measurement import Measurement


class InstrumentData(BaseModel):
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
