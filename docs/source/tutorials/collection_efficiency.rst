Collection Efficiency
=====================

This short example walks through computing the size-resolved collection efficiency of a
size-selective device - such as an impactor - from paired upstream and downstream measurements,
and extracting its cut diameter.

Set-up
------

Although you can skip this part (pypana imitates other libraries' defaults), when exporting plots you might want to
customize their appearance. See the :doc:`/tutorials/themes` tutorial for a more comprehensive overview.

First, we load pypana and set the theme.

.. code-block:: python

    from pypana.config import settings
    from pypana.plots.themes.tol7 import Tol7Theme

    # other available ready-to-use options: Tab10Theme, IBMTheme, Tol3Theme, ...
    # explicitly plots light-mode plots even with IDEs set to dark-mode
    settings.THEME = Tol7Theme
    settings.THEME.set_mode("light")

Loading the data
----------------

As in the :doc:`/tutorials/histogram` tutorial, we let the :class:`~pypana.readers.discovery.SmartReader`
pick the correct reader for us.

.. important::
    A collection-efficiency study measures each particle size twice: once *upstream* of the device
    (the undisturbed aerosol) and once *downstream* (after the device removed part of it). This tutorial
    uses :file:`/ExampleFiles/20250822_PALAS_WELAS.txt`, which holds upstream and downstream measurements
    for several sizes - but not in a tidy order, so matching each upstream scan to its downstream
    partner is part of the work below.

.. code-block:: python

    from pypana.readers import SmartReader

    FILE_PATH = "../ExampleFiles/20250822_PALAS_WELAS.txt"
    data = SmartReader(FILE_PATH).read()

    print(len(data))  # 14 measurements -> 7 (upstream, downstream) pairs

The measurements rarely give a clean efficiency curve straight away. Two preparation steps come first:
cleaning each distribution, then arranging the trusted pairs.

Cleaning the distributions
--------------------------

The efficiency is built from each measurement's total concentration (:attr:`~pypana.data.measurement.Measurement.total`),
so for e.g. polydisperse aerosols, extra modes would distort it.
Cut the distributions to the size window of interest with
:meth:`~pypana.data.instrument_data.InstrumentData.cut` (on the whole dataset) or
:meth:`~pypana.data.measurement.Measurement.cut` (per measurement), which zeroes the bins outside the bounds
in place.

Here every scan is cut to 0.35-10 µm except the 0.4 µm pair (scans 4 and 5), whose mode sits at the low
end and would be removed by the cut, so it keeps its full distribution:

.. code-block:: python

    for key, m in data.measurements.items():
        if key not in (4, 5):        # leave the 0.4 µm pair un-cut
            m.cut((0.35e-6, 10e-6))  # bounds in metres: drop the secondary modes

.. tip::
    There are multiple ways to do this. Because
    :meth:`~pypana.data.instrument_data.InstrumentData.keep_measurements` with ``inplace=False`` returns a
    a new :obj:`~pypana.data.instrument_data.InstrumentData` that shares the very same :class:`~pypana.data.measurement.Measurement` objects,
    cutting that view also cuts them in ``data`` - so you select the scans to clean and cut them all at once,
    no per-scan ``if``:

    .. code-block:: python

        to_clean = [key for key in data.measurements if key not in (4, 5)]
        data.keep_measurements(to_clean, inplace=False, verbose=False).cut((0.35e-6, 10e-6))

Arranging the pairs
-------------------

:meth:`~pypana.data.instrument_data.InstrumentData.collection_efficiency` consumes the measurements as
consecutive ``(upstream, downstream)`` pairs. Use
:meth:`~pypana.data.instrument_data.InstrumentData.permute` to keep only the measurements you trust and place
each upstream directly before its downstream. Here we keep the five clean pairs (0.4, 0.7, 1.2, 1.8 and
2.0 µm):

.. code-block:: python

    # (upstream, downstream) scan keys for the 0.4, 0.7, 1.2, 1.8 and 2.0 µm pairs
    data.permute([5, 4, 2, 3, 12, 13, 10, 11, 8, 9])

.. hint::
    ``permute`` both reorders **and** drops anything you leave out, re-keying the survivors to ``0, 1, 2, …``.

Computing the efficiency
------------------------

For each pair the method computes the fraction the device removed,

.. math::

    \eta = 1 - \frac{N_\text{down}}{N_\text{up}},

where :math:`N` is the total number concentration of a measurement. Each :math:`\eta` is plotted against the
geometric mean diameter (:attr:`~pypana.data.measurement.Measurement.geo_mean`) of the upstream
measurement - the size of the particles presented to the device - and, by default, a sigmoid is fitted to
extract the cut diameter :math:`d_{50}`, the size at which half of the particles are collected.

A wide ``xlim`` draws the fitted curve well beyond the data points so full S-shape is shown (the curve
is otherwise only drawn between the smallest and largest data point); ``ylim`` pins the axis to the
full 0-100 % efficiency range.

.. code-block:: python

    ce = data.collection_efficiency(fit="sigmoid", xlim=(0.3e-6, 4e-6), ylim=(0, 1))

    print(f"cut diameter d50 = {ce.d_50 * 1e6:.2f} µm")  # ~0.97 µm

The method both plots the curve and returns a :class:`~pypana.data.collection_efficiency.CollectionEfficiency`
object for further use (see :ref:`ce-result` below).

.. figure:: /_static/collection_efficiency/ce_default.svg
    :alt: Collection efficiency with a sigmoid fit
    :width: 100%

    Collection efficiency of the five cleaned pairs with a sigmoid fit. The cut diameter is the 50 %
    crossing.

Choosing the fit
~~~~~~~~~~~~~~~~~

The ``fit`` argument selects the model overlaid on the data points:

* ``"sigmoid"`` (default) - a symmetric 0 %/100 % curve; reports :math:`d_{50}`.
* ``"gompertz"`` - allows asymmetric asymptotes for skewed efficiency curves.
* ``None`` - plots only the data points, no fit.

.. code-block:: python

    ce = data.collection_efficiency(fit="gompertz")

    ce = data.collection_efficiency(fit=None)  # data points only

.. figure:: /_static/collection_efficiency/ce_points.svg
    :alt: Collection efficiency data points without a fit
    :width: 100%

    The efficiency data points with ``fit=None`` - useful to inspect the pairs before committing to a model.

.. warning::
    The fit-functions are currently an early implementation and may not be fully working. The ``sigmoid`` function
    will always fit between ``0.0`` and ``1.0``.

.. _ce-result:

Reading the result
~~~~~~~~~~~~~~~~~~~

Besides plotting, the returned :class:`~pypana.data.collection_efficiency.CollectionEfficiency` holds every
number for your own tables and plots.

.. code-block:: python

    ce = data.collection_efficiency()

    print(ce.d_50)             # cut diameter [m] (only when a fit was performed)
    print(ce.d_p, ce.eta)      # per-pair upstream diameter [m] and efficiency
    print(ce.fit_r_squared)    # goodness of fit
    print(ce.upstream_scan_nrs, ce.downstream_scan_nrs)  # which scans formed each pair

Making it pretty
~~~~~~~~~~~~~~~~~

Like :meth:`~pypana.data.instrument_data.InstrumentData.histogram`, cosmetic matplotlib arguments are passed
with a target prefix - ``scatter_`` for the data points, ``fit_`` for the fitted curve, ``grid_`` for the
grid, and ``legend_`` for the legend. Labels accept a lambda that receives the
:class:`~pypana.data.collection_efficiency.CollectionEfficiency` object.

.. code-block:: python

    ce = data.collection_efficiency(
        fit="sigmoid",
        title="Impactor collection efficiency",
        scatter_color="C1",
        scatter_marker="s",
        fit_label=lambda ce: f"sigmoid, d50 = {ce.d_50 * 1e6:.2f} µm",
        xlim=(0.3e-6, 4e-6),
        ylim=(0, 1),
    )

.. figure:: /_static/collection_efficiency/ce_styled.svg
    :alt: Styled collection efficiency
    :width: 100%

    The same curve with a custom title, markers, and fit label.

Conclusion
----------

The showcased plots only cover a few arguments of the
:meth:`~pypana.data.instrument_data.InstrumentData.collection_efficiency` method. Please refer to its
documentation for further details.

The returned :class:`~pypana.data.collection_efficiency.CollectionEfficiency` lets you take the analysis
further - tabulate the per-pair efficiencies, compare :math:`d_{50}` across devices, or build your own plot.
The :doc:`/tutorials/data_manipulation` tutorial will help you with that.

For further quick reference, here are all arguments:

.. automethod:: pypana.data.instrument_data.InstrumentData.collection_efficiency
   :noindex: