"""Definition of a dataclass for instrument output.

This module provides a class to store the data and perform calculations on it
"""
from collections import defaultdict
from textwrap import dedent
from typing import Annotated

from pydantic import BaseModel, Field

from pypana.console import console
from pypana.data.exceptions.invalid_index_error import InvalidIndexError
from pypana.data.measurement import Measurement


class InstrumentData(BaseModel):
    """Data class for instrument data."""

    model_config = {"arbitrary_types_allowed": True}

    measurements: list[Measurement] = Field(
        min_length=1,
        description="List of measurement data to include in the analysis",
    )

    _device_name: str = Field(
        alias="device_name",
        default="",
        description="Name of the device the data was measured on",
    )
    _file_path: Path | None = Field(
        alias="file_path",
        default=None,
        description="Path to the imported measurement file",
    )

    def select_measurements(
        self,
        indices: Annotated[int, Field(ge=0)] | Annotated[list[int], Field(min_length=1)],
        *,
        inplace=True,
        verbose=True,
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
        """
        if isinstance(indices, int):
            indices: list[int] = [indices]

        max_index = max(indices)
        has_duplicates = len(indices) != len(set(indices))

        if has_duplicates or max_index > len(self.measurements):
            invalid_indices = list()
            counts = defaultdict(int)

            for i in indices:
                counts[i] += 1

            invalid_indices.append([i for i in indices if i >= len(self.measurements)])
            invalid_indices.append([i for i, count in counts.items() if count > 1])

            raise InvalidIndexError(
                message="Invalid indices given when selecting measurements",
                invalid_indices=invalid_indices
            )

        selected_measurements: list[Measurement] = [self.measurements[i] for i in indices]

        if verbose:
            first = selected_measurements[0]
            last = selected_measurements[-1]

            console.print(dedent(f"""\
                [bold]Selected Measurements:[/bold] 
                [Scan [cyan]{first.scan_nr}[/cyan] at time [magenta]{first.time:%Y-%m-%d %H:%M:%S}[/magenta]] \\ 
                → [Scan [cyan]{last.scan_nr}[/cyan] at time [magenta]{last.time:%Y-%m-%d %H:%M:%S}[/magenta]]
            """))

        if inplace:
            self.measurements = selected_measurements
            return self

        return InstrumentData(
            measurements=selected_measurements,
            device_name=self._device_name,
            file_path=self._file_path,
        )
