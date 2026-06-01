Data Overview - Histogram
=========================

This short example walks through getting an overview of imported data by plotting a histogram of measurements.

Set-up
------

Although you can skip this part (pypana imitates other libraries' defaults), when exporting plots you might want to
customize their appearance. See the :doc:`/tutorials/themes` tutorial for a more comprehensive overview.

First, we load pypana and set the theme.

.. code-block:: python

    from pypana.config import settings
    from pypana.plots.themes.ibm import IBMTheme

    # other available ready-to-use options: Tab10Theme, Tol3Theme, Tol7Theme, ...
    # explicitly plots light-mode plots even with IDEs set to dark-mode
    settings.THEME = IBMTheme
    settings.THEME.set_mode("light")

Loading the data
----------------

The pypana package can read the output of many different aerosol measurement devices.
You don't have to change your import code for different devices. Although you can still manually select the device,
pypana provides the :class:`~pypana.readers.discovery.SmartReader` class
that automatically chooses the correct reader of the  :mod:`~pypana.readers` module for you.

.. important::
    For this tutorial, we will use one of the example files, specifically :file:`/ExampleFiles/20250822_PALAS_WELAS.txt`.
    You can either directly pass the file path as a string to the :class:`~pypana.readers.discovery.SmartReader`,
    or select the file to read in an interactive dialogue.

.. code-block:: python

    from pypana.readers import SmartReader

    FILE_PATH = "../ExampleFiles/20250822_PALAS_WELAS.txt"
    data = SmartReader(FILE_PATH).read()

    print(len(data))  # 14, number of loaded measurements

The data of your measurements is now successfully loaded into the data object.
The :class:`~pypana.data.instrument_data.InstrumentData` object stores a :class:`~pypana.data.measurement.Measurement`
object per loaded measurement and acts as a wrapper. To perform data manipulation, you can either modify each
:class:`~pypana.data.measurement.Measurement` object individually, or apply transformations to all simultaneously by using the
:class:`~pypana.data.instrument_data.InstrumentData` object as a proxy.

.. hint::
    Depending on how much low-level checks you want to perform on the loaded data, instead of printing the length,
    there are some other methods available:
        - :meth:`~pypana.data.instrument_data.InstrumentData.summary` to get a pandas DataFrame with key attributes per measurement,
        - and :meth:`info(verbose=True) <pypana.data.instrument_data.InstrumentData.info()>` to show the underlying datastructure in great detail.


Plotting a histogram
--------------------

You can now plot the loaded data as histogram. The magic happens when calling the :meth:`~pypana.data.instrument_data.InstrumentData.histogram`.
This method can produce all sorts of different histograms depending on the caller arguments. For more detail,
see the documentation of that function. The following subsections introduce some use cases.

.. hint::
    Most matplotlib settings are specified in the theme for consistent use throughout multiple plots.
    See :doc:`/tutorials/themes` for how to create your own custom style, change to a predefined one, or
    set specific plot sizes and dpi.
    Still, some matplotlib arguments can be given to the  :meth:`~pypana.data.instrument_data.InstrumentData.histogram` method itself.

    The figure size was adapted for the shown plots of this tutorial. Since pypana uses a matplotlib backend,
    you can add `%matplotlib notebook` to a cell to rescale the plots as you need.

In general, you have to specify three things:
    1. which data to display (measurements)
    2. what to display (data type of :class:`~pypana.utils.measurement_data_type.MeasurementDataType`)
    3. how to display (cosmetic arguments)


Single measurement
~~~~~~~~~~~~~~~~~~

The following code plots the simplest of all histograms, just one single measurement for easy analysis.
Great to visualize specific data.

.. code-block:: python

    from pypana.utils.measurement_data_type import MeasurementDataType

    data.histogram(
        1,                             # measurement number to plot
        MeasurementDataType.dndlogdp,  # data type to show, can also be `dn`
        save_as="./path/to/save.png",  # omit to just show
    )

.. figure:: /_static/histograms/single_noargs.svg
    :alt: Histogram of a single measurement
    :width: 100%

    Histogram of a single measurement with no additional arguments.

As you can see, it produces a valid histogram of the measured data. But there are some things to note:

    - The x-axis covers the entire measurement's device's range. In this case, the data is centered in the lower portion of the range.
    - X/Y-labels are automatically generated, as well as the title and legend.
    - The bars are indistinguishable, no border is shown.
    - A histogram is nice, but showing an additional function is nicer.

We can solve this by passing some arguments. The :attr:`~pypana.plots.histograms.hist_matrix.STANDARD_HIST_SINGLE_KWARGS`
provide additional preconfigured input. It supplies the arguments in the same way anyone can refer to additional matplotlib keyword arguments.

.. code-block:: python

    from pypana.plots.histograms.hist_matrix import STANDARD_HIST_SINGLE_KWARGS
    from pypana.utils.measurement_data_type import MeasurementDataType

    data.histogram(
        1,
        MeasurementDataType.dndlogdp,
        secondary="cdf",
        title="Histogram of a single measurement with additional args",
        xlim=(1.5e-7, 1e-6),
        bar_facecolor="C2",
        **STANDARD_HIST_SINGLE_KWARGS,
    )

.. figure:: /_static/histograms/single_args.svg
    :alt: Histogram of a single measurement
    :width: 100%

    Histogram of a single measurement with additional arguments.


Multiple measurements
~~~~~~~~~~~~~~~~~~~~~

The following code plots multiple histograms together. Great to compare a trend over different measurements.

.. note::

    1.  The histograms are plotted on top of each other, starting with the first specified measurement.
        You should not set a custom color via the method arguments, as then all measurements will get plotted with the same color.
        When leaving the color argument empty, it cycles through the specified colors of the theme.
        Refer to the :doc:`/tutorials/themes` tutorial on how to define your own color cycle.

    2.  When normalizing the data as a probability mass function (argument `pmf=True`), the measurements are normalized
        individually. Therefore, differences in magnitude between single measurements are not preserved.

Let's get a little bit more fancy with the histograms and show the number concentration of four different
measurements. We can select multiple measurements by passing the specific scan numbers as a tuple, as well as change
the label of the legend.

The left plot displays the measurements as bars, while the right displays them as stairs to less obstruct the other measurements.

.. code-block:: python

    from pypana.plots.histograms.hist_matrix import STANDARD_HIST_SINGLE_KWARGS
    from pypana.utils.measurement_data_type import MeasurementDataType


    STANDARD_HIST_SINGLE_KWARGS["bar_label"] = lambda m: f"Scan {m.scan_nr - 1}"

    data.histogram(
        (2, 3, 4, 5),
        MeasurementDataType.dn,
        title="Histogram of four measurements",
        xlim=(1.5e-7, 3e-6),
        **STANDARD_HIST_SINGLE_KWARGS,
    )


.. code-block:: python

    from pypana.plots.histograms.hist_matrix import STANDARD_HIST_SINGLE_KWARGS
    from pypana.utils.measurement_data_type import MeasurementDataType

    STANDARD_HIST_SINGLE_KWARGS["stairs_label"] = lambda m: f"T = {m.scan_nr - 1} min"

    data.histogram(
        (2, 3, 4, 5),
        MeasurementDataType.dn,
        hist_type="stairs",
        title="Histogram of four measurements",
        xlim=(1.5e-7, 3e-6),
        stairs_linewidth=2,
        **STANDARD_HIST_SINGLE_KWARGS,
    )


.. grid:: 2

    .. grid-item::

        .. figure:: /_static/histograms/multi_bar.svg

            Multiple histograms as bars.

    .. grid-item::

        .. figure:: /_static/histograms/multi_stairs.svg

            Multiple histograms as stairs.


Multiple histograms
~~~~~~~~~~~~~~~~~~~

The following code plots a matrix of histograms, each subplot may contain one or multiple histograms.
Great to get an overview of the collected data.

You can specify the measurements to show in the matrix like before, but this time as a 2-dimensional list in row-major order.
Each entry represents one subplot. To avoid visual cluttering, we remove some x-ticks (the 2.0 and 5.0 ones) and switch
to a theme with more available colors.

Similar to the :attr:`~pypana.plots.histograms.hist_matrix.STANDARD_HIST_SINGLE_KWARGS` available for single subplot
histograms, pypana also provides the :attr:`~pypana.plots.histograms.hist_matrix.STANDARD_HIST_MATRIX_KWARGS` for the matrix use-case.

.. note::

    Currently, each plot gets its own legend entry, even if the same measurement was already plotted.
    This is a known limitation and may be changed in the future. When selecting an additional function to plot,
    the reference measurement is the first one specified for that subplot. All secondary functions will be represented
    with one label in the legend.


.. code-block:: python

    from pypana.plots.histograms.hist_matrix import STANDARD_HIST_MATRIX_KWARGS
    from pypana.plots.themes.tol4 import Tol4Theme
    from pypana.utils.measurement_data_type import MeasurementDataType


    settings.THEME = Tol4Theme
    settings.THEME.set_mode("light")

    data.histogram(
        [[2, 3, 4], [(2, 5), (3, 5), (4, 5)]],
        MeasurementDataType.dn,
        title="Matrix Histogram",
        stairs_linewidth=2,
        xmajor_locations=(1.0,),
        **STANDARD_HIST_MATRIX_KWARGS,
    )

.. figure:: /_static/histograms/matrix_stairs.svg
    :alt: Matrix histogram
    :width: 100%

    Histogram matrix of multiple different measurements.

.. code-block:: python

    from pypana.plots.histograms.hist_matrix import STANDARD_HIST_MATRIX_KWARGS
    from pypana.plots.themes.tab10 import Tab10Theme
    from pypana.utils.measurement_data_type import MeasurementDataType


    settings.THEME = Tab10Theme
    settings.THEME.set_mode("light")
    settings.THEME.figure_size = (9, 6)

    data.histogram(
        [[2, 3, 4], [5, 6, 7]],
        MeasurementDataType.dn,
        title="Matrix Histogram",
        xmajor_locations=(1.0,),
        **STANDARD_HIST_MATRIX_KWARGS,
    )

.. figure:: /_static/histograms/matrix_single.svg
    :alt: Matrix histogram
    :width: 100%

    Histogram matrix of a single measurement each.

Conclusion
----------

The showcased plots only cover few additional arguments and features of the :meth:`~pypana.data.instrument_data.InstrumentData.histogram`
method. Please refer to its documentation for further details.

After the first visual impressions of the data, you might want to modify it.
You can always create your own plots based on pypana data and access the :class:`~pypana.data.instrument_data.InstrumentData`
or a :class:`~pypana.data.measurement.Measurement` directly to extract the necessary information.
The :doc:`/tutorials/data_manipulation` tutorial will help you with that.

For further quick reference, here are all arguments:

.. automethod:: pypana.data.instrument_data.InstrumentData.histogram
   :noindex:

