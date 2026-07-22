"""Shared Hypothesis strategies for building Measurement / InstrumentData test data."""

from datetime import datetime

import numpy as np
from hypothesis import strategies as st
from hypothesis.strategies import DrawFn, SearchStrategy

from pypana.data.bin_axis import BinAxis
from pypana.data.collection_efficiency import CollectionEfficiency
from pypana.data.defs import Quantity
from pypana.data.instrument_data import InstrumentData
from pypana.data.measurement import Measurement
from pypana.data.size_distribution import SizeDistribution
from pypana.data.time_series import TimeSeries

MIN_SCAN_NR = 1
MAX_SCAN_NR = 1000


@st.composite
def bin_axis(
    draw: DrawFn,
    *,
    min_bins: int = 1,
    max_bins: int = 12,
    channels_per_decade: int = 8,
    diameter_type: str = "mobility",
) -> BinAxis:
    """Build a log-spaced BinAxis at a fixed resolution (constant delta_log_d_p).

    Args:
        min_bins: Lower bound on the number of bins.
        max_bins: Upper bound on the number of bins.
        channels_per_decade: Log-spacing resolution; bin width is ``1 / cpd`` decades.
        diameter_type: The axis' physical diameter basis.
    """
    n_bins = draw(st.integers(min_value=min_bins, max_value=max_bins))

    # diameters in meters, from ~1 nm to ~1 µm in uniform log space
    log_start = draw(st.floats(min_value=-9.0, max_value=-6.0))
    log_width = 1.0 / channels_per_decade
    bin_boundaries = 10.0 ** (log_start + log_width * np.arange(n_bins + 1))

    return BinAxis(bin_boundaries=bin_boundaries, diameter_type=diameter_type)


@st.composite
def size_distribution(
    draw: DrawFn,
    *,
    axis: BinAxis | None = None,
    quantity: Quantity = Quantity.NUMBER,
    seed: str = "delta",
    zero: bool = False,
    nonzero_total: bool = False,
    min_bins: int = 1,
    max_bins: int = 12,
    channels_per_decade: int = 8,
    diameter_type: str = "mobility",
) -> SizeDistribution:
    """Build a SizeDistribution on a (drawn or supplied) axis.

    Args:
        axis: The axis to build on; a fresh one is drawn when ``None``.
        quantity: The quantity the values represent.
        seed: Which representation to populate: ``"delta"`` or ``"delta_dlogdp"``.
        zero: When ``True``, the values are all zero (``total == 0``).
        nonzero_total: When ``True``, guarantees a strictly positive total.
        min_bins, max_bins, channels_per_decade, diameter_type: Forwarded to ``bin_axis``
            when an axis must be drawn.
    """
    if axis is None:
        axis = draw(
            bin_axis(
                min_bins=min_bins,
                max_bins=max_bins,
                channels_per_decade=channels_per_decade,
                diameter_type=diameter_type,
            )
        )

    n_bins = axis.n_bins

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

    return SizeDistribution(quantity=quantity, axis=axis, **{seed: values})


@st.composite
def populated_measurement(
    draw: DrawFn,
    *,
    scan_nr: int | None = None,
    quantity: Quantity = Quantity.NUMBER,
    seed: str = "delta",
    zero: bool = False,
    nonzero_total: bool = False,
    min_bins: int = 1,
    max_bins: int = 12,
    channels_per_decade: int = 8,
    diameter_type: str = "mobility",
) -> Measurement:
    """Build a single-distribution Measurement sharing one BinAxis.

    Args:
        scan_nr: Fixed scan number, or drawn when ``None``.
        quantity: The stored quantity.
        seed: Which representation to populate: ``"delta"`` or ``"delta_dlogdp"``.
        zero: When ``True``, the distribution is all-zero (``total == 0``).
        nonzero_total: When ``True``, guarantees a strictly positive total.
        min_bins, max_bins, channels_per_decade, diameter_type: Axis parameters.
    """
    if scan_nr is None:
        scan_nr = draw(st.integers(min_value=0, max_value=MAX_SCAN_NR))

    dist = draw(
        size_distribution(
            quantity=quantity,
            seed=seed,
            zero=zero,
            nonzero_total=nonzero_total,
            min_bins=min_bins,
            max_bins=max_bins,
            channels_per_decade=channels_per_decade,
            diameter_type=diameter_type,
        )
    )

    return Measurement(
        scan_nr=scan_nr,
        time=datetime(2026, 5, 29, 12, 0, 0),
        axis=dist.axis,
        distributions={dist.quantity: dist},
    )


def measurement_dict(min_size: int = 1, max_size: int = 100) -> SearchStrategy:
    """Create dictionaries of minimal populated measurements keyed by scan_nr."""
    return st.lists(
        st.integers(min_value=MIN_SCAN_NR, max_value=MAX_SCAN_NR).flatmap(
            lambda scan_nr: st.tuples(
                st.just(scan_nr),
                populated_measurement(scan_nr=scan_nr, max_bins=4),
            )
        ),
        min_size=min_size,
        max_size=max_size,
        unique_by=lambda x: x[0],
    ).map(dict)


@st.composite
def instrument_data(
    draw: DrawFn,
    *,
    n: int | None = None,
    min_n: int = 1,
    max_n: int = 8,
    seed: str = "delta",
    nonzero_total: bool = False,
    min_bins: int = 1,
    max_bins: int = 12,
) -> InstrumentData:
    """Build an InstrumentData with contiguously-keyed populated measurements.

    Args:
        n: Fixed number of measurements, or drawn when ``None``.
        min_n: Lower bound on the number of measurements.
        max_n: Upper bound on the number of measurements.
        seed: Which representation to populate on each measurement.
        nonzero_total: When ``True``, every measurement has a strictly positive total.
    """
    if n is None:
        n = draw(st.integers(min_value=min_n, max_value=max_n))

    measurements = {
        i: draw(
            populated_measurement(
                scan_nr=i,
                seed=seed,
                nonzero_total=nonzero_total,
                min_bins=min_bins,
                max_bins=max_bins,
            )
        )
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


@st.composite
def time_series(
    draw: DrawFn,
    *,
    quantity: Quantity = Quantity.NUMBER,
    min_samples: int = 2,
    max_samples: int = 50,
) -> TimeSeries:
    """Build a TimeSeries with strictly-increasing millisecond timestamps.

    Args:
        quantity: The quantity the samples represent.
        min_samples: Lower bound on the number of samples (≥ 2).
        max_samples: Upper bound on the number of samples.
    """
    n = draw(st.integers(min_value=min_samples, max_value=max_samples))

    # strictly-increasing timestamps
    gaps = draw(
        st.lists(
            st.integers(min_value=1, max_value=60_000),
            min_size=n - 1,
            max_size=n - 1,
        )
    )
    offsets = np.concatenate(([0], np.cumsum(gaps))).astype("timedelta64[ms]")
    timestamps = np.datetime64("2026-05-29T12:00:00", "ms") + offsets

    values = np.array(
        draw(
            st.lists(
                st.floats(
                    min_value=0.0,
                    max_value=1e6,
                    allow_nan=False,
                    allow_infinity=False,
                ),
                min_size=n,
                max_size=n,
            )
        )
    )

    return TimeSeries(quantity=quantity, timestamps=timestamps, values=values)


@st.composite
def series_measurement(
    draw: DrawFn,
    *,
    scan_nr: int | None = None,
    quantity: Quantity = Quantity.NUMBER,
    min_samples: int = 2,
    max_samples: int = 50,
) -> Measurement:
    """Build a time-series-only Measurement (no axis, no distributions).

    Args:
        scan_nr: Fixed scan number, or drawn when ``None``.
        quantity: The stored quantity.
    """
    if scan_nr is None:
        scan_nr = draw(st.integers(min_value=0, max_value=MAX_SCAN_NR))

    ts = draw(
        time_series(quantity=quantity, min_samples=min_samples, max_samples=max_samples)
    )

    return Measurement(
        scan_nr=scan_nr,
        time=datetime(2026, 5, 29, 12, 0, 0),
        series={ts.quantity: ts},
    )
