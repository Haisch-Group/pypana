import random
from unittest.mock import Mock, patch

import numpy as np
import pytest
from hypothesis import given, settings

from data.strategies import (
    MAX_SCAN_NR,
    MIN_SCAN_NR,
    instrument_data,
    measurement_dict,
    populated_measurement,
)
from pypana.data.collection_efficiency import CollectionEfficiency
from pypana.data.exceptions.invalid_index_error import InvalidIndexError
from pypana.data.instrument_data import InstrumentData
from pypana.data._measurement import Measurement
from pypana.exceptions.incompatible_argument_error import IncompatibleArgumentError
from pypana.utils.measurement_data_type import MeasurementDataType

# four measurements paired consecutively yield two (up, down) pairs for collection efficiency
EXPECTED_PAIRS = 2
# int, tuple, list-of-int and list-of-tuple are the four accepted histogram inputs
HISTOGRAM_INPUT_FORMS = 4


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
    invalid_scan_nr = max(list(data.measurements.keys())) + 1
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
    first_scan_nr = min(list(data.measurements.keys()))
    last_scan_nr = max(list(data.measurements.keys()))
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
    first_scan_nr = min(list(data.measurements.keys()))
    last_scan_nr = max(list(data.measurements.keys()))

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
    first_scan_nr = min(list(data.measurements.keys()))

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
    first_scan_nr = min(list(data.measurements.keys()))

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


def test_len_empty_returns_zero() -> None:
    """Empty InstrumentData has length 0."""
    data = InstrumentData()

    assert len(data) == 0


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=5, max_size=20))
def test_len_matches_measurement_count(measurements: dict[int, Measurement]) -> None:
    """__len__ returns the number of measurements in hte dict."""
    data = InstrumentData(measurements=measurements)

    assert len(data) == len(measurements)


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=3, max_size=20))
def test_len_updates_after_keep_measurements(
    measurements: dict[int, Measurement],
) -> None:
    """__len__ reflects shrunk size after in-place keep_measurements."""
    data = InstrumentData(measurements=measurements)
    first = list(data.measurements.keys())[0]
    data.keep_measurements(first, inplace=True, verbose=False)

    assert len(data) == 1


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=20))
def test_getitem_int_returns_measurement_instance(
    measurements: dict[int, Measurement],
) -> None:
    """Indexing with an existing scan_nr returns a Measurement."""
    data = InstrumentData(measurements=measurements)
    scan_nr = random.choice(list(measurements.keys()))

    assert isinstance(data.measurements[scan_nr], Measurement)
    assert data.measurements[scan_nr].scan_nr == scan_nr


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=20))
def test_getitem_int_returns_correct_measurement_by_scan_nr(
    measurements: dict[int, Measurement],
) -> None:
    """Returned Measurement carries the requested scan_nr."""
    data = InstrumentData(measurements=measurements)
    for scan_nr in measurements:
        assert data[scan_nr].scan_nr == scan_nr


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=20))
def test_getitem_int_missing_key_raises_keyerror(
    measurements: dict[int, Measurement],
) -> None:
    """A scan_nr not present raises KeyError (dict lookup)."""
    data = InstrumentData(measurements=measurements)
    missing = max(measurements) + 1
    with pytest.raises(KeyError):
        _ = data[missing]


def test_getitem_int_on_empty_raises_keyerror() -> None:
    """Any int on an empty InstrumentData raises KeyError."""
    data = InstrumentData()
    with pytest.raises(KeyError):
        _ = data[0]


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=2, max_size=20))
def test_getitem_slice_returns_new_instrumentdata(
    measurements: dict[int, Measurement],
) -> None:
    """A slice returns an InstrumentData, not a Measurement."""
    data = InstrumentData(measurements=measurements)
    sliced = data[0:1]

    assert isinstance(sliced, InstrumentData)
    assert id(sliced) != id(data)


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=3, max_size=20))
def test_getitem_slice_does_not_mutate_original(
    measurements: dict[int, Measurement],
) -> None:
    """Slicing is non-inplace; source keeps all measurements."""
    data = InstrumentData(measurements=measurements)
    original_keys = list(data.measurements.keys())
    _ = data[0:1]

    assert list(data.measurements.keys()) == original_keys


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=20))
def test_getitem_slice_full_range_returns_equivalent_keys(
    measurements: dict[int, Measurement],
) -> None:
    """data[:] yields an InstrumentData with the same measurement keys."""
    data = InstrumentData(measurements=measurements)
    sliced = data[:]

    assert list(sliced.measurements.keys()) == list(data.measurements.keys())


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=4, max_size=20))
def test_getitem_slice_subset_returns_expected_keys(
    measurements: dict[int, Measurement],
) -> None:
    """data[1:3] returns measurements at positions 1 and 2 of keys()."""
    data = InstrumentData(measurements=measurements)
    keys = list(data.measurements.keys())
    sliced = data[1:3]

    assert list(sliced.measurements.keys()) == keys[1:3]


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=4, max_size=20))
def test_getitem_slice_with_step_returns_expected_keys(
    measurements: dict[int, Measurement],
) -> None:
    """data[::2] returns every other measurement in insertion order."""
    data = InstrumentData(measurements=measurements)
    keys = list(data.measurements.keys())
    sliced = data[::2]

    assert list(sliced.measurements.keys()) == keys[::2]


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=2, max_size=20))
def test_getitem_slice_empty_result_raises(
    measurements: dict[int, Measurement],
) -> None:
    """A slice selecting nothing surfaces as an error from keep_measurements."""
    data = InstrumentData(measurements=measurements)
    with pytest.raises((InvalidIndexError, ValueError)):
        _ = data[5:5]


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=20))
def test_getitem_slice_preserves_device_name_and_file_path(
    measurements: dict[int, Measurement],
) -> None:
    """The sliced InstrumentData carries over device_name and file_path."""
    data = InstrumentData(measurements=measurements, device_name="test_device")
    sliced = data[:]

    assert sliced.device_name == "test_device"
    assert sliced.file_path == data.file_path


@pytest.mark.parametrize("bad_index", ["foo", 1.5, (1, 2), None])
@settings(max_examples=1)
@given(measurements=measurement_dict(min_size=1, max_size=5))
def test_getitem_invalid_type_raises_typeerror(
    measurements: dict[int, Measurement], bad_index: object
) -> None:
    """Passing a non int/slice to __getitem__ raises TypeError."""
    data = InstrumentData(measurements=measurements)
    with pytest.raises(TypeError):
        _ = data[bad_index]  # type: ignore[call-overload]


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=2, max_size=20))
def test_getitem_slice_empty_result_raises_valueerror(
    measurements: dict[int, Measurement],
) -> None:
    """An empty slice raises ValueError."""
    data = InstrumentData(measurements=measurements)
    with pytest.raises(ValueError):
        _ = data[5:5]


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=2, max_size=20))
def test_getitem_slice_out_of_range_returns_empty_raises(
    measurements: dict[int, Measurement],
) -> None:
    """A slice fully past the end produces an empty selection and raises."""
    data = InstrumentData(measurements=measurements)
    with pytest.raises(ValueError):
        _ = data[len(data) + 10 : len(data) + 20]


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=10))
def test_apply_returns_function_result(
    measurements: dict[int, Measurement],
) -> None:
    """apply forwards self into f and returns its result."""
    data = InstrumentData(measurements=measurements)
    result = data.apply(lambda d: d)

    assert result is data


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=10))
def test_apply_passes_self_to_function(
    measurements: dict[int, Measurement],
) -> None:
    """The function receives the InstrumentData itself as its argument."""
    data = InstrumentData(measurements=measurements)
    seen: list[InstrumentData] = []

    def capture(d: InstrumentData) -> InstrumentData:
        seen.append(d)
        return d

    data.apply(capture)

    assert seen == [data]


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=2, max_size=10))
def test_apply_chainable_with_keep_measurements(
    measurements: dict[int, Measurement],
) -> None:
    """apply can be used to chain operations like keep_measurements."""
    data = InstrumentData(measurements=measurements)
    first = next(iter(data.measurements))
    result = data.apply(
        lambda d: d.keep_measurements(first, inplace=False, verbose=False)
    )

    assert list(result.measurements.keys()) == [first]


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=10))
def test_mapply_returns_self(
    measurements: dict[int, Measurement],
) -> None:
    """mapply returns the same InstrumentData instance (inplace)."""
    data = InstrumentData(measurements=measurements)
    result = data.mapply(lambda m: m)

    assert result is data


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=10))
def test_mapply_applies_to_every_measurement(
    measurements: dict[int, Measurement],
) -> None:
    """The function is invoked once per measurement."""
    data = InstrumentData(measurements=measurements)
    calls: list[int] = []

    def f(m: Measurement) -> Measurement:
        calls.append(m.scan_nr)
        return m

    data.mapply(f)
    assert sorted(calls) == sorted(measurements.keys())


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=10))
def test_mapply_replaces_measurements_with_function_output(
    measurements: dict[int, Measurement],
) -> None:
    """The dict values are replaced by what the function returns, keys preserved."""
    data = InstrumentData(measurements=measurements)
    original_keys = list(data.measurements.keys())

    def bump_d_p(m: Measurement) -> Measurement:
        m.d_p = np.append(m.d_p, 1.0)
        return m

    data.mapply(bump_d_p)
    assert list(data.measurements.keys()) == original_keys
    for m in data.measurements.values():
        assert m.d_p.tolist() == [1.0]


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=3, max_size=10))
def test_permute_reorders_keys(
    measurements: dict[int, Measurement],
) -> None:
    """permute reindexes measurements in the order given by p."""
    data = InstrumentData(measurements=measurements)
    p = list(data.measurements.keys())[::-1]
    expected_first_measurement_scan_nr = data.measurements[p[0]].scan_nr

    data.permute(p)

    assert list(data.measurements.keys()) == list(range(len(p)))
    assert data.measurements[0].scan_nr == expected_first_measurement_scan_nr


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=10))
def test_permute_returns_self(
    measurements: dict[int, Measurement],
) -> None:
    """permute returns the same instance."""
    data = InstrumentData(measurements=measurements)
    p = list(data.measurements.keys())

    assert data.permute(p) is data


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=2, max_size=10))
def test_permute_with_unknown_index_raises_valueerror(
    measurements: dict[int, Measurement],
) -> None:
    """A permutation containing an unknown key raises ValueError."""
    data = InstrumentData(measurements=measurements)
    keys: list[int] = list(data.measurements.keys())
    bad_p = [*keys[:-1], max(keys) + 999]
    with pytest.raises(ValueError):
        data.permute(bad_p)


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=2, max_size=10))
def test_permute_partial_drops_remaining_keys(
    measurements: dict[int, Measurement],
) -> None:
    """Permuting a strict subset reduces the measurement count accordingly."""
    data = InstrumentData(measurements=measurements)
    subset = list(data.measurements.keys())[:1]
    data.permute(subset)

    assert len(data) == 1


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=10))
def test_reindex_produces_contiguous_keys(
    measurements: dict[int, Measurement],
) -> None:
    """After reindex(), keys are 0..n-1."""
    data = InstrumentData(measurements=measurements)
    data.reindex()

    assert list(data.measurements.keys()) == list(range(len(measurements)))


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=1, max_size=10))
def test_reindex_preserves_measurement_order(
    measurements: dict[int, Measurement],
) -> None:
    """reindex keeps the insertion order, only the keys change."""
    data = InstrumentData(measurements=measurements)
    original_scan_nrs = [m.scan_nr for m in data.measurements.values()]
    data.reindex()

    assert [m.scan_nr for m in data.measurements.values()] == original_scan_nrs


@settings(max_examples=5)
@given(measurements=measurement_dict(min_size=2, max_size=10))
def test_reindex_enables_slicing_when_keys_were_noncontiguous(
    measurements: dict[int, Measurement],
) -> None:
    """Slicing works the same after reindex; result has new contiguous keys."""
    data = InstrumentData(measurements=measurements)
    data.reindex()
    sliced = data[0:2]

    assert list(sliced.measurements.keys()) == [0, 1]


def test_reindex_on_empty_is_noop() -> None:
    """reindex on an empty InstrumentData leaves it empty."""
    data = InstrumentData()
    data.reindex()

    assert len(data) == 0


@settings(max_examples=5)
@given(data=instrument_data(min_n=1, max_n=4))
def test_summary_returns_one_row_per_measurement(data: InstrumentData) -> None:
    """summary() yields a DataFrame indexed by measurement key, one row each."""
    df = data.summary()

    assert len(df) == len(data.measurements)
    assert list(df.index) == list(data.measurements.keys())


@settings(max_examples=5)
@given(data=instrument_data(min_n=1, max_n=4))
def test_cut_returns_self_and_delegates_to_measurements(data: InstrumentData) -> None:
    """cut() maps over measurements in place and returns self."""
    assert data.cut((1e-12, 1.0)) is data


@settings(max_examples=5)
@given(data=instrument_data(min_n=2, max_n=4))
def test_getitem_slice_invalid_index_becomes_valueerror(data: InstrumentData) -> None:
    """A slice whose selection raises InvalidIndexError is surfaced as ValueError."""
    with (
        patch.object(
            InstrumentData,
            "keep_measurements",
            side_effect=InvalidIndexError(message="boom", invalid_indices=[]),
        ),
        pytest.raises(ValueError),
    ):
        _ = data[0:2]


@settings(max_examples=3)
@given(data=instrument_data(n=2))
@patch("pypana.data.instrument_data.plot_hist_matrix")
def test_histogram_accepts_int_tuple_and_list_inputs(
    plot_mock: Mock, data: InstrumentData
) -> None:
    """int, tuple, list-of-int and list-of-tuple inputs all reach the plotter."""
    dt = MeasurementDataType.dndlogdp

    data.histogram(0, dt)
    data.histogram((0, 1), dt)
    data.histogram([[0, 1]], dt)
    data.histogram([[(0, 1)]], dt)

    assert plot_mock.call_count == HISTOGRAM_INPUT_FORMS


@settings(max_examples=3)
@given(data=instrument_data(n=3))
@patch("pypana.data.instrument_data.plot_hist_matrix")
def test_histogram_non_rectangular_raises(
    plot_mock: Mock, data: InstrumentData
) -> None:
    """A ragged measurement matrix is rejected."""
    with pytest.raises(InvalidIndexError):
        data.histogram([[0], [1, 2]], MeasurementDataType.dn)
    assert plot_mock.call_count == 0


@settings(max_examples=3)
@given(data=instrument_data(n=2))
@patch("pypana.data.instrument_data.plot_hist_matrix")
def test_histogram_xspace_sides_with_xlim_is_incompatible(
    plot_mock: Mock, data: InstrumentData
) -> None:
    """xspace_sides and xlim cannot be combined."""
    with pytest.raises(IncompatibleArgumentError):
        data.histogram(0, MeasurementDataType.dn, xspace_sides=0.1, xlim=(1e-9, 1e-6))


@settings(max_examples=3)
@given(data=instrument_data(n=2))
@patch("pypana.data.instrument_data.plot_hist_matrix")
def test_histogram_xspace_sides_computes_limits(
    plot_mock: Mock, data: InstrumentData
) -> None:
    """xspace_sides alone drives the xlim computation path."""
    with np.errstate(all="ignore"):
        data.histogram(0, MeasurementDataType.dn, xspace_sides=0.1)
    assert plot_mock.call_count == 1


@settings(max_examples=3)
@given(data=instrument_data(n=2))
@patch("pypana.data.instrument_data.plot_hist_matrix")
def test_histogram_explicit_xlim(plot_mock: Mock, data: InstrumentData) -> None:
    """An explicit, ordered xlim is accepted."""
    data.histogram(0, MeasurementDataType.dn, xlim=(1e-9, 1e-6))
    assert plot_mock.call_count == 1


@settings(max_examples=3)
@given(data=instrument_data(n=2))
@patch("pypana.data.instrument_data.plot_hist_matrix")
def test_histogram_inverted_xlim_raises(plot_mock: Mock, data: InstrumentData) -> None:
    """An xlim whose lower bound is not below the upper bound is rejected."""
    with pytest.raises(ValueError):
        data.histogram(0, MeasurementDataType.dn, xlim=(1e-6, 1e-9))


@settings(max_examples=3)
@given(data=instrument_data(n=4, nonzero_total=True))
@patch("pypana.data.instrument_data.plot_collection_efficiency")
def test_collection_efficiency_none_pairs_all(
    plot_mock: Mock, data: InstrumentData
) -> None:
    """m=None pairs all measurements consecutively into (up, down) pairs."""
    ce = data.collection_efficiency(m=None)

    assert isinstance(ce, CollectionEfficiency)
    assert len(ce) == EXPECTED_PAIRS
    assert plot_mock.call_count == 1


@settings(max_examples=3)
@given(data=instrument_data(n=3, nonzero_total=True))
def test_collection_efficiency_none_odd_count_raises(data: InstrumentData) -> None:
    """An odd number of measurements cannot be paired."""
    with pytest.raises(ValueError):
        data.collection_efficiency(m=None)


@settings(max_examples=3)
@given(data=instrument_data(n=4, nonzero_total=True))
@patch("pypana.data.instrument_data.plot_collection_efficiency")
def test_collection_efficiency_tuple_bounds(
    plot_mock: Mock, data: InstrumentData
) -> None:
    """A (lo, hi) tuple selects the inclusive scan-number range."""
    ce = data.collection_efficiency(m=(0, 3))
    assert len(ce) == EXPECTED_PAIRS


@settings(max_examples=3)
@given(data=instrument_data(n=4, nonzero_total=True))
def test_collection_efficiency_tuple_inverted_raises(data: InstrumentData) -> None:
    """Tuple bounds with lower > upper are rejected."""
    with pytest.raises(ValueError):
        data.collection_efficiency(m=(3, 0))


@settings(max_examples=3)
@given(data=instrument_data(n=4, nonzero_total=True))
def test_collection_efficiency_tuple_no_scans_raises(data: InstrumentData) -> None:
    """Tuple bounds matching no scans raise an index error."""
    with pytest.raises(InvalidIndexError):
        data.collection_efficiency(m=(100, 200))


@settings(max_examples=3)
@given(data=instrument_data(n=4, nonzero_total=True))
def test_collection_efficiency_tuple_odd_count_raises(data: InstrumentData) -> None:
    """A tuple selecting an odd number of scans is rejected."""
    with pytest.raises(ValueError):
        data.collection_efficiency(m=(0, 0))


@settings(max_examples=3)
@given(data=instrument_data(n=4, nonzero_total=True))
@patch("pypana.data.instrument_data.plot_collection_efficiency")
def test_collection_efficiency_range_and_slice(
    plot_mock: Mock, data: InstrumentData
) -> None:
    """range and slice select consecutive measurements by position."""
    assert len(data.collection_efficiency(m=range(0, 4))) == EXPECTED_PAIRS
    assert len(data.collection_efficiency(m=slice(0, 4))) == EXPECTED_PAIRS


@settings(max_examples=3)
@given(data=instrument_data(n=4, nonzero_total=True))
def test_collection_efficiency_range_out_of_bounds_raises(
    data: InstrumentData,
) -> None:
    """A range that addresses a non-existent position raises an index error."""
    with pytest.raises(InvalidIndexError):
        data.collection_efficiency(m=range(0, 10))


@settings(max_examples=3)
@given(data=instrument_data(n=4, nonzero_total=True))
def test_collection_efficiency_range_odd_count_raises(data: InstrumentData) -> None:
    """A range selecting an odd number of measurements is rejected."""
    with pytest.raises(ValueError):
        data.collection_efficiency(m=range(0, 1))


@settings(max_examples=3)
@given(data=instrument_data(n=4, nonzero_total=True))
def test_collection_efficiency_bad_type_raises(data: InstrumentData) -> None:
    """A selector that is not None/tuple/range/slice raises TypeError."""
    with pytest.raises(TypeError):
        data.collection_efficiency(m=1.5)  # type: ignore[arg-type]


@settings(max_examples=3)
@given(
    up=populated_measurement(scan_nr=0, zero=True),
    down=populated_measurement(scan_nr=1, nonzero_total=True),
)
@patch("pypana.data.instrument_data.plot_collection_efficiency")
def test_collection_efficiency_zero_upstream_raises(
    plot_mock: Mock, up: Measurement, down: Measurement
) -> None:
    """A zero upstream total concentration makes η undefined."""
    data = InstrumentData(measurements={0: up, 1: down})
    with pytest.raises(ValueError):
        data.collection_efficiency(m=None)


@settings(max_examples=3)
@given(data=instrument_data(n=2))
@patch("pypana.data.instrument_data.plot_hist_matrix")
def test_histogram_unsupported_input_type_raises(
    plot_mock: Mock, data: InstrumentData
) -> None:
    """An m that is neither int, tuple nor list yields an empty, non-full matrix."""
    with pytest.raises(InvalidIndexError):
        data.histogram(1.5, MeasurementDataType.dn)  # type: ignore[arg-type]
    assert plot_mock.call_count == 0
