from datetime import datetime
from unittest.mock import Mock, patch

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from pypana.data.exceptions.invalid_index_error import InvalidIndexError
from pypana.data.instrument_data import InstrumentData
from pypana.data.measurement import Measurement
from pypana.utils.measurement_data_type import MeasurementDataType

MIN_SCAN_NR = 1
MAX_SCAN_NR = 1000


def measurement_factory(scan_nr: int) -> SearchStrategy:
    """Create empty measurements with certain scan_nr"""
    return st.builds(
        Measurement,
        scan_nr=st.just(scan_nr),
        time=st.just(datetime(scan_nr + 2000, 4, 1, 0, 0, 0)),
        d_p=st.just(np.array([], dtype=float)),
        delta_d_p=st.just(np.array([], dtype=float)),
        delta_log_d_p=st.just(np.array([], dtype=float)),
        delta_n=st.just(np.array([], dtype=float)),
        bin_boundaries=st.just(np.array([], dtype=float)),
    )


def measurement_dict(min_size: int = 1, max_size: int = 100) -> SearchStrategy:
    """Create dictionaries of measurements"""
    return st.lists(
        st.integers(min_value=MIN_SCAN_NR, max_value=MAX_SCAN_NR).flatmap(
            lambda scan_nr: st.tuples(st.just(scan_nr), measurement_factory(scan_nr))
        ),
        min_size=min_size,
        max_size=max_size,
        unique_by=lambda x: x[0],
    ).map(dict)


@settings(max_examples=5, deadline=None)
@given(
    measurements=measurement_dict(min_size=5, max_size=20),
)
def test_select_measurements_inplace(measurements: dict[int, Measurement]) -> None:
    """Test that the select_measurements works correctly"""
    data = InstrumentData(measurements=measurements)
    data_old = data.keep_measurements(range(MIN_SCAN_NR, MAX_SCAN_NR + 1), inplace=True)
    data_new = data.keep_measurements(list(data.measurements.keys())[0], inplace=False)

    assert data == data_old
    assert id(data) == id(data_old)
    assert data_new != data
    assert id(data_new) != id(data)


@settings(max_examples=1)
@given(measurements=measurement_dict(min_size=5, max_size=20))
def test_select_measurements_int(measurements: dict[int, Measurement]) -> None:
    """Test that int inputs result in expected behavior."""
    data = InstrumentData(measurements=measurements)

    # negative index
    with pytest.raises(InvalidIndexError):
        data.keep_measurements(-1)

    # valid index of existing scan
    second_scan_nr = list(data.measurements.keys())[1]
    data_int = data.keep_measurements(second_scan_nr, inplace=False)
    assert len(data_int.measurements) == 1
    assert data_int.measurements[second_scan_nr].scan_nr == second_scan_nr

    # non-existing scan
    invalid_scan_nr = list(data.measurements.keys())[-1] + 1
    with pytest.raises(InvalidIndexError):
        data.keep_measurements(invalid_scan_nr, inplace=False)


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=5, max_size=20))
def test_select_measurements_range(measurements: dict[int, Measurement]) -> None:
    """Test that range inputs result in expected behavior."""
    data = InstrumentData(measurements=measurements)

    # negative indices invalid
    with pytest.raises(InvalidIndexError):
        data.keep_measurements(range(-MAX_SCAN_NR, MAX_SCAN_NR), inplace=False)

    # upper bound unbounded ok
    data_old = data.keep_measurements(range(0, 2 * MAX_SCAN_NR + 1))
    assert data_old == data

    # valid range but no measurements
    with pytest.raises(InvalidIndexError):
        data.keep_measurements(range(MAX_SCAN_NR + 2, MAX_SCAN_NR + 100))

    # select all
    data_old = data.keep_measurements(range(MIN_SCAN_NR, MAX_SCAN_NR))
    assert data_old == data
    assert id(data_old) == id(data)

    # select everything except first and last
    first_scan_nr = list(data.measurements.keys())[0]
    last_scan_nr = list(data.measurements.keys())[-1]
    data_new = data.keep_measurements(
        range(first_scan_nr + 1, last_scan_nr), inplace=False, verbose=False
    )
    assert id(data_new) != id(data)
    assert len(data_new.measurements) == len(data.measurements) - 2


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=5, max_size=20))
def test_select_measurements_list(measurements: dict[int, Measurement]) -> None:
    """Test that list inputs result in expected behavior."""
    data = InstrumentData(measurements=measurements)
    first_scan_nr = list(data.measurements.keys())[0]
    last_scan_nr = list(data.measurements.keys())[-1]

    # negative indices invalid
    with pytest.raises(InvalidIndexError):
        data.keep_measurements([50, 40, -3])

    # not present indices invalid
    with pytest.raises(InvalidIndexError):
        data.keep_measurements([last_scan_nr + 1, last_scan_nr + 2])

    # duplicate indices invalid
    with pytest.raises(InvalidIndexError):
        data.keep_measurements([last_scan_nr, last_scan_nr + 1, last_scan_nr + 1])

    selection = [first_scan_nr, last_scan_nr]
    data_new = data.keep_measurements(selection, inplace=False)

    assert id(data_new) != id(data)
    assert len(data_new.measurements) == len(selection)
    assert data_new.measurements.get(first_scan_nr, None) is not None


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=5, max_size=20))
def test_select_measurements_deepcopy(measurements: dict[int, Measurement]) -> None:
    """Test that when deepcopy enabled it returns an independent copy."""
    data = InstrumentData(measurements=measurements)
    first_scan_nr = list(data.measurements.keys())[0]

    data_new = data.keep_measurements(
        range(MIN_SCAN_NR, MAX_SCAN_NR + 1), deepcopy=True, verbose=False
    )

    assert id(data_new) != id(data)
    # cannot use assert data_new == data due to faulty pydantic __eq__
    for m in data.measurements:
        m1 = data.measurements[m]
        m2 = data.measurements[m]

        assert m1.scan_nr == m2.scan_nr
        assert m1.time == m2.time
        assert np.array_equal(m1.d_p, m2.d_p)

    data.measurements[first_scan_nr].d_p = np.append(
        data.measurements[first_scan_nr].d_p, 1
    )

    assert not np.array_equal(
        data.measurements[first_scan_nr].d_p, data_new.measurements[first_scan_nr].d_p
    )


@settings(max_examples=1)
@given(measurements=measurement_dict(min_size=5, max_size=20))
@patch("pypana.data.instrument_data.plot_hist_single_plotly")
@patch("pypana.data.instrument_data.plot_hist_single_matplotlib")
def test_plot_histogram_single(
    matplotlib_mock: Mock, plotly_mock: Mock, measurements: dict[int, Measurement]
) -> None:
    """Test the plot_histogram_single function wraps correctly."""
    data = InstrumentData(measurements=measurements)
    first_scan_nr = list(data.measurements.keys())[0]

    with pytest.raises(InvalidIndexError):
        data.plot_histogram_single(-1, data_type=MeasurementDataType.dndlogdp)

    data.plot_histogram_single(
        first_scan_nr, data_type=MeasurementDataType.dn, backend="matplotlib"
    )

    assert matplotlib_mock.call_count == 1
    assert plotly_mock.call_count == 0

    data.plot_histogram_single(
        first_scan_nr, data_type=MeasurementDataType.dn, backend="plotly"
    )

    assert matplotlib_mock.call_count == 1
    assert plotly_mock.call_count == 1
