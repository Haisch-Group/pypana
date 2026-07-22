Data Manipulation
=================

pypana parses every supported instrument into one layered data structure. This tutorial follows that
structure from the top container down to the value arrays.

Loading the data
----------------

The :class:`~pypana.readers.discovery.SmartReader` is left to pick the correct reader and to load one of the example files. It returns an :class:`~pypana.data.instrument_data.InstrumentData` object, which is the main data container of pypana.

.. code-block:: python

    from pypana.readers import SmartReader

    FILE_PATH = "../ExampleFiles/20250822_PALAS_WELAS.txt"
    data = SmartReader(FILE_PATH).read()

    print(len(data))  # 14, the number of loaded measurements

Everything below operates on the object just loaded. The whole set can be acted upon at once, or any
single layer can be reached individually.

The shape of the data
---------------------

The following shows the composition of the underlying data structure that is used throughout the tutorial. For most instruments, one :class:`~pypana.data.measurement.Measurement` is equivalent to one line or file of the output.

.. note::
    The data model is composed of five layers:

    * :class:`~pypana.data.instrument_data.InstrumentData` holds a dictionary of ``{scan_nr: Measurement}``, where the ``scan_nr`` identifies a measurement.
    * each :class:`~pypana.data.measurement.Measurement` carries one shared :class:`~pypana.data.bin_axis.BinAxis`,
      a dictionary of :class:`~pypana.data.size_distribution.SizeDistribution` keyed by :class:`~pypana.data.defs.quantity.Quantity`,
      a dictionary of :class:`~pypana.data.time_series.TimeSeries` keyed by quantity, and an ``other`` bag for the remainder.
    * a :class:`~pypana.data.size_distribution.SizeDistribution` holds the value arrays of one quantity, defined on that axis.
    * a :class:`~pypana.data.bin_axis.BinAxis` holds the diameter grid on which those values are defined.
    * a :class:`~pypana.data.time_series.TimeSeries` holds values sampled over time, with no size axis.

    ::

        InstrumentData
        └── measurements: {scan_nr: Measurement}
            └── Measurement
                ├── axis:          BinAxis            (shared diameter grid)
                ├── distributions: {Quantity: SizeDistribution}
                ├── series:        {Quantity: TimeSeries}
                └── other:         {...}

InstrumentData
-----------------------------

The :class:`~pypana.data.instrument_data.InstrumentData` is a wrapper around the
``measurements`` dictionary. A single scan is reached by its key, the count is obtained with
``len``, and the dictionary itself can be iterated directly.

However, there is no guarantee for a certain ``scan_nr`` to exist. Some instruments, where the number is explicitly given, the ``0`` scan may be missing. To get a continuous list of scans, see the :ref:`Selecting and reordering` section.

.. code-block:: python

    print(len(data))            # 14 measurements

    third = data[3]             # a single Measurement
    print(data.measurements.keys())

    for key, measurement in data.measurements.items():
        print(key, measurement.scan_nr)

For an overview of the whole set, :meth:`~pypana.data.instrument_data.InstrumentData.summary`
returns a pandas DataFrame with one row per measurement, while
:meth:`~pypana.data.instrument_data.InstrumentData.info` prints a readable report that includes every detail.

.. code-block:: python

    data.summary()              # DataFrame, one row per measurement
    data.info(verbose=True)     # printed report of the underlying structure

Selecting and reordering
~~~~~~~~~~~~~~~~~~~~~~~~~~

A subset can be carved out with a slice or with
:meth:`~pypana.data.instrument_data.InstrumentData.keep_measurements`, whereas the order is changed
and unwanted scans are dropped with :meth:`~pypana.data.instrument_data.InstrumentData.permute`.
The keys are made contiguous again by :meth:`~pypana.data.instrument_data.InstrumentData.reindex`.

.. code-block:: python

    subset = data[2:6]                                            # a new InstrumentData
    subset = data.keep_measurements([2, 3, 4, 5], inplace=False)  # the same selection

    data.permute([5, 4, 2, 3])  # reorder, drop the rest, then assign new keys 0, 1, 2, 3
    data.reindex()              # equivalently: data.permute(list(data.measurements.keys()))

.. warning::
    A slice and ``keep_measurements(inplace=False)`` return a new
    :class:`~pypana.data.instrument_data.InstrumentData`, but the underlying
    :class:`~pypana.data.measurement.Measurement` objects are not copied: the new object shares the
    very same measurements. A mutation of one (for instance a cut) is therefore reflected in the
    other. ``deepcopy=True`` should be passed to
    :meth:`~pypana.data.instrument_data.InstrumentData.keep_measurements` when a fully independent
    copy is required.

    The default coupling allows operations on a subset of :class:`~pypana.data.measurement.Measurement` object after filtering, so that the original unfiltered :class:`~pypana.data.instrument_data.InstrumentData` object also has access to the modified data.

Filtering by quantity
~~~~~~~~~~~~~~~~~~~~~~~

When the container is indexed with a bare :class:`~pypana.data.defs.quantity.Quantity` (or its
string, ``"N"``), a new :class:`~pypana.data.instrument_data.InstrumentData` is returned in which
every measurement retains only that one quantity. Under the hood each measurement is filtered in
turn and a fresh container is assembled, so the original ``data`` is left untouched and is still coupled.

.. code-block:: python

    from pypana.data.defs import Quantity

    numbers = data[Quantity.NUMBER]   # every measurement filtered to its number quantity
    numbers = data["N"]               # the same, by symbol

Reading a whole quantity as a matrix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the container is indexed with a full data type rather than a bare quantity, that one binned
data type is stacked across all measurements into a 2D array.
:meth:`~pypana.data.instrument_data.InstrumentData.matrix` performs the same operation and accepts a
string or a :class:`~pypana.data.defs.data_type.DataType`.

.. code-block:: python

    from pypana.data.defs import DataType

    m = data["dN/dlogdp"]                       # (n_scans x n_bins) array
    m = data.matrix("dN/dlogdp")                # the same
    m = data.matrix(DataType.parse("dN/dlogdp"))

Under the hood the matrix is the row stack of ``measurement["dN/dlogdp"]`` over every measurement, so
all scans are required to share the same bin count, otherwise an error is raised. The split is
deliberate: a bare quantity filters and returns a container, whereas a data type (``dN`` or
``dN/dlogdp``) reads values and returns an array.

Measurement
----------------------

A :class:`~pypana.data.measurement.Measurement` represents one scan. Its fields are the
:attr:`~pypana.data.measurement.Measurement.scan_nr`, the
:attr:`~pypana.data.measurement.Measurement.time`, the shared
:attr:`~pypana.data.measurement.Measurement.axis`, the
:attr:`~pypana.data.measurement.Measurement.distributions` and
:attr:`~pypana.data.measurement.Measurement.series` dictionaries, and an ``other`` bag.

.. code-block:: python

    measurement = data[3]

    print(measurement.scan_nr, measurement.time)
    print(measurement.quantities)          # the quantities it stores
    print(Quantity.NUMBER in measurement)  # membership test

The indexing of a measurement mirrors that of the container. A bare quantity filters it to a smaller
measurement, whereas a data type reads the binned values of that quantity as a 1D array aligned to
:attr:`~pypana.data.measurement.Measurement.d_p`.

.. code-block:: python

    only_number = measurement[Quantity.NUMBER]   # a smaller Measurement, drops rest
    values = measurement["dN/dlogdp"]            # a 1D value array (no Measurement object, since exact data requested)

    print(measurement.d_p)              # bin midpoint diameters [m]
    print(measurement.n_bins)           # number of bins
    print(measurement.delta_log_d_p)    # logarithmic bin widths

The :attr:`~pypana.data.measurement.Measurement.d_p`,
:attr:`~pypana.data.measurement.Measurement.n_bins` and similar properties are passthroughs to the :class:`~pypana.data.bin_axis.BinAxis`. Multiple :class:`~pypana.data.size_distribution.SizeDistribution`s can share the same :class:`~pypana.data.bin_axis.BinAxis`.

One distribution or many
~~~~~~~~~~~~~~~~~~~~~~~~~~

When a measurement holds exactly one size distribution, it behaves as though it were that
distribution. The convenience statistics are read straight off it, and no quantity has to be named.

.. code-block:: python

    measurement.total      # total concentration of the sole distribution
    measurement.geo_mean   # geometric mean diameter [m] of the sole distribution

This is what most files provide, so the common case remains transparent. As soon as a measurement
holds several distributions, however, the shortcut becomes ambiguous:
:attr:`~pypana.data.measurement.Measurement.total` and
:attr:`~pypana.data.measurement.Measurement.geo_mean` then raise, since the intended quantity cannot
be inferred. Once a quantity has been selected, the statistic is well defined again.

.. code-block:: python

    measurement[Quantity.NUMBER].total                # filter first, then read
    measurement.distributions[Quantity.NUMBER].total  # or reach the distribution directly

.. hint::
    The same rule governs indexing. A value read such as ``measurement["dN"]`` always names its
    quantity through the data type, so it remains unambiguous regardless of how many distributions are
    present.

Cutting the size range
~~~~~~~~~~~~~~~~~~~~~~~~

:meth:`~pypana.data.measurement.Measurement.cut` zeroes every bin whose midpoint lies outside the
given window, on every distribution of the measurement, in place. On the container,
:meth:`~pypana.data.instrument_data.InstrumentData.cut` applies the same operation to all
measurements at once.

.. code-block:: python

    measurement.cut((0.35e-6, 10e-6))   # bounds in metres, one scan
    data.cut((0.35e-6, 10e-6))          # every scan at once

SizeDistribution
----------------

A :class:`~pypana.data.size_distribution.SizeDistribution` holds the values of one quantity on the
axis, in two representations: :attr:`~pypana.data.size_distribution.SizeDistribution.delta`, the
concentration per bin, and :attr:`~pypana.data.size_distribution.SizeDistribution.delta_dlogdp`, the
normalized form. One is reached through its measurement.

.. code-block:: python

    dist = measurement.distributions[Quantity.NUMBER]

    dist["dN"]          # per bin values
    dist["dN/dlogdp"]   # normalized values

.. note::
    Only one of the two representations is the source of truth; the other is computed lazily on first
    access (``delta_dlogdp = delta / delta_log_d_p``) and cached. When one of them is written, the
    cached other is dropped, so the two can never drift apart and inconsistent data is never held. A
    read of a quantity that does not match the distribution is rejected, since e.g. volume values cannot be
    returned from a number distribution.

    Since at loading-time, only one representation is the source of truth, the other may differ slightly due to small numerical inconsistencies from what some input files report.

The common weighted statistics are exposed as well, each computed over the per bin values.

.. code-block:: python

    dist.total        # integrated concentration
    dist.geo_mean     # geometric mean diameter [m]
    dist.geo_std_dev  # geometric standard deviation
    dist.mean         # arithmetic mean diameter [m]
    dist.median       # median diameter [m]
    dist.mode         # diameter of the peak of the normalized distribution [m]

For a custom transformation, :meth:`~pypana.data.size_distribution.SizeDistribution.apply` maps the
source of truth array and recomputes the other representation from the result.
:meth:`~pypana.data.size_distribution.SizeDistribution.cut` is built on top of it.

.. code-block:: python

    import numpy as np

    dist.apply(lambda values: np.clip(values, 0, None))  # in place, the pair is then re-derived

.. hint::
    Each distribution also carries a :attr:`~pypana.data.size_distribution.SizeDistribution.provenance`
    of ``"measured"`` or ``"derived"``, prepared for the time when a quantity can be derived from
    another (for instance volume from number). That derivation is not yet implemented; the conversion
    between the per bin and the normalized form does not count as derivation.

BinAxis
-------

A :class:`~pypana.data.bin_axis.BinAxis` is the diameter grid on which the values are defined. It is
specified by its ``n + 1`` :attr:`~pypana.data.bin_axis.BinAxis.bin_boundaries` (strictly increasing
and positive); the midpoints and widths are derived from them.

.. code-block:: python

    axis = measurement.axis

    axis.bin_boundaries   # the n + 1 boundaries [m]
    axis.d_p              # bin midpoint diameters [m]
    axis.d_lower          # lower boundary of each bin [m]
    axis.d_upper          # upper boundary of each bin [m]
    axis.delta_d_p        # absolute bin width [m]
    axis.delta_log_d_p    # logarithmic bin width
    axis.n_bins           # number of bins

.. note::
    The axis is immutable, and within one scan the very same axis object is shared by every
    distribution. Neither a cut nor a transformation of the values can
    desync the grid, as long as all :obj:`~pypana.data.measurement.Measurement` refer to the same :attr:`~pypana.data.bin_axis.BinAxis`. When no midpoint is reported by the instrument,
    :attr:`~pypana.data.bin_axis.BinAxis.d_p` is derived from the boundaries, geometrically by
    default. The :attr:`~pypana.data.bin_axis.BinAxis.diameter_type` records the physical basis of the
    diameter (mobility, optical, or aerodynamic).

TimeSeries
----------

Some instruments, such as counters and photometers, sample one quantity over time rather than over a
size grid. Such scans carry a :class:`~pypana.data.time_series.TimeSeries` instead of a size
distribution, and their :attr:`~pypana.data.measurement.Measurement.axis` is ``None``. One is reached
through the :attr:`~pypana.data.measurement.Measurement.series` dictionary.

.. code-block:: python

    series = measurement.series[Quantity.NUMBER]

    series.n_samples          # number of samples
    series.elapsed("s")       # time of each sample since the first, in seconds
    series.duration("m")      # total span between first and last sample, in minutes
    series.mean               # mean of the sampled values
    series.vmin, series.vmax  # extremes
    series.std                # standard deviation

.. note::
    A measurement that holds only a time series has no size axis, so a request for its
    :attr:`~pypana.data.measurement.Measurement.d_p` or
    :attr:`~pypana.data.measurement.Measurement.total` is rejected; those belong to a size
    distribution. The example file used here carries size distributions, so the snippet above is given
    for reference.

Conclusion
----------

The data model comprises five layers: the :class:`~pypana.data.instrument_data.InstrumentData`
container, the per scan :class:`~pypana.data.measurement.Measurement`, the
:class:`~pypana.data.size_distribution.SizeDistribution` values, the
:class:`~pypana.data.bin_axis.BinAxis` on which they are defined, and the
:class:`~pypana.data.time_series.TimeSeries` for time sampled scans. The distinction
between an in place change and a copy should be kept in mind whenever the data is sliced or filtered. By default, pypana opts for coupling of that transforms :class:`~pypana.data.measurement.Measurement` objects in place, but other options remain available through method arguments.

Once a dataset has been prepared, e.g. the :doc:`/tutorials/histogram` and
:doc:`/tutorials/collection_efficiency` tutorials turn it into plots.

For quick reference, the core container methods are listed below.

.. automethod:: pypana.data.instrument_data.InstrumentData.keep_measurements
   :noindex:

.. automethod:: pypana.data.instrument_data.InstrumentData.permute
   :noindex:

.. automethod:: pypana.data.instrument_data.InstrumentData.matrix
   :noindex: