"""Shared Hypothesis strategies for building Measurement / InstrumentData test data."""

from datetime import datetime

import numpy as np
from hypothesis import strategies as st
from hypothesis.strategies import DrawFn, SearchStrategy

from pypana.data.collection_efficiency import CollectionEfficiency
from pypana.data.instrument_data import InstrumentData
from pypana.data.measurement import Measurement

MIN_SCAN_NR = 1
MAX_SCAN_NR = 1000


def empty_measurement(scan_nr: int) -> SearchStrategy:
    """Create an empty measurement with a fixed scan_nr."""
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
    """Create dictionaries of empty measurements keyed by scan_nr."""
    return st.lists(
        st.integers(min_value=MIN_SCAN_NR, max_value=MAX_SCAN_NR).flatmap(
            lambda scan_nr: st.tuples(st.just(scan_nr), empty_measurement(scan_nr))
        ),
        min_size=min_size,
        max_size=max_size,
        unique_by=lambda x: x[0],
    ).map(dict)


@st.composite
def populated_measurement(
    draw: DrawFn,
    *,
    scan_nr: int | None = None,
    seed: str = "delta_n",
    zero: bool = False,
    nonzero_total: bool = False,
    min_bins: int = 1,
    max_bins: int = 12,
    channels_per_decade: int = 8,
) -> Measurement:
    """Build a non-empty Measurement with uniformly log-spaced bins.

    Bins are log-spaced at a fixed resolution (``channels_per_decade``) to mimic
    a real SMPS-like instrument, giving a constant ``delta_log_d_p`` per bin.

    Args:
        scan_nr: Fixed scan number, or drawn when ``None``.
        seed: Which distribution to populate: ``"delta_n"`` or ``"delta_n_dlog_dp"``.
        zero: When ``True``, the distribution is all-zero (``n_total == 0``).
        nonzero_total: When ``True``, guarantees a strictly positive total (``n_total > 0``).
        min_bins: Lower bound on the number of bins.
        max_bins: Upper bound on the number of bins.
        channels_per_decade: Log-spacing resolution; bin width is ``1 / cpd`` decades.
    """
    if scan_nr is None:
        scan_nr = draw(st.integers(min_value=0, max_value=MAX_SCAN_NR))

    n_bins = draw(st.integers(min_value=min_bins, max_value=max_bins))

    # diameters in meters, from 1 nm to 1 µm in uniform log space
    log_start = draw(st.floats(min_value=-9.0, max_value=-6.0))
    log_width = 1.0 / channels_per_decade
    bin_boundaries = 10.0 ** (log_start + log_width * np.arange(n_bins + 1))

    d_lower, d_upper = bin_boundaries[:-1], bin_boundaries[1:]
    d_p = np.sqrt(d_lower * d_upper)
    delta_d_p = d_upper - d_lower
    delta_log_d_p = np.log10(d_upper) - np.log10(d_lower)

    if zero:
        values = np.zeros(n_bins)
    else:
        values = np.array(
            draw(
                st.lists(
                    st.floats(
                        min_value=0.0,
                        max_value=1e6,
                        allow_nan=False,
                        allow_infinity=False,
                    ),
                    min_size=n_bins,
                    max_size=n_bins,
                )
            )
        )
        if nonzero_total:
            values[0] += 1.0  # guarantee a strictly positive total

    kwargs: dict = {
        "scan_nr": scan_nr,
        "time": datetime(2026, 5, 29, 12, 0, 0),
        "d_p": d_p,
        "delta_d_p": delta_d_p,
        "delta_log_d_p": delta_log_d_p,
        "bin_boundaries": bin_boundaries,
        seed: values,
    }
    return Measurement(**kwargs)


@st.composite
def instrument_data(
    draw: DrawFn,
    *,
    n: int | None = None,
    min_n: int = 1,
    max_n: int = 8,
    seed: str = "delta_n",
    nonzero_total: bool = False,
) -> InstrumentData:
    """Build an InstrumentData with contiguously-keyed populated measurements.

    Args:
        n: Fixed number of measurements, or drawn when ``None``.
        min_n: Lower bound on the number of measurements.
        max_n: Upper bound on the number of measurements.
        seed: Which distribution to populate on each measurement.
        nonzero_total: When ``True``, every measurement has a strictly positive total.
    """
    if n is None:
        n = draw(st.integers(min_value=min_n, max_value=max_n))

    measurements = {
        i: draw(populated_measurement(scan_nr=i, seed=seed, nonzero_total=nonzero_total))
        for i in range(n)
    }
    return InstrumentData(measurements=measurements, device_name="test")


@st.composite
def collection_efficiency(
    draw: DrawFn,
    *,
    min_points: int = 1,
    max_points: int = 12,
) -> CollectionEfficiency:
    """Build a CollectionEfficiency without a fit (fit fields left at None).

    Args:
        min_points: Lower bound on the number of (up, down) pairs.
        max_points: Upper bound on the number of (up, down) pairs.
    """
    n = draw(st.integers(min_value=min_points, max_value=max_points))

    finite = {"allow_nan": False, "allow_infinity": False}
    d_p = np.array(
        draw(
            st.lists(
                st.floats(min_value=1e-9, max_value=1e-5, **finite),
                min_size=n,
                max_size=n,
            )
        )
    )
    eta = np.array(
        draw(
            st.lists(
                st.floats(min_value=0.0, max_value=1.0, **finite),
                min_size=n,
                max_size=n,
            )
        )
    )

    return CollectionEfficiency(
        d_p=d_p,
        eta=eta,
        upstream_scan_nrs=list(range(0, 2 * n, 2)),
        downstream_scan_nrs=list(range(1, 2 * n, 2)),
    )
