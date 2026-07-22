[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue?logo=python&logoColor=white)
[![CI Status](https://github.com/Haisch-Group/pypana/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Haisch-Group/pypana/actions/workflows/ci.yml)

# Pypana

A Python package for importing, analyzing, and plotting aerosol measurements.

pypana reads the raw output of many aerosol measurement instruments into one consistent data model, 
to easily compute, modify, and derive statistics for publication-ready plots. And all of that without writing instrument-specific code.

## Installation

```bash
# pip
pip install pypana

# uv
uv add pypana

# conda
conda install -c conda-forge pypana
```

## Quick example

Read a file (the instrument format is detected automatically among all supported instruments), and overlay several measurements in a single number-distribution histogram:

```python
from pypana.config import settings
from pypana.plots.histograms.hist_matrix import STANDARD_HIST_SINGLE_KWARGS
from pypana.plots.themes.ibm import IBMTheme
from pypana.readers import SmartReader

# set one of the ready-to-use themes as default
settings.THEME = IBMTheme
settings.THEME.set_mode("light")

# load the data from the instrument's output file
data = SmartReader("../ExampleFiles/20250822_PALAS_WELAS.txt").read()

# overlay scans 2-5 in one histogram of the number distribution (dN)
data.histogram(
    (2, 3, 4, 5),
    "dN",
    title="Histogram of four measurements",
    **STANDARD_HIST_SINGLE_KWARGS,
)
```
![Four measurements overlaid in a single histogram](https://raw.githubusercontent.com/Haisch-Group/pypana/main/docs/source/_static/readme/histogram.svg)

## Documentation

Tutorials and API references are available at <TODO ADD LINK>.

To get started with pypana, we suggest starting with these tutorials:
<TODO ADD LINK TO HIST AND DATA MANIPULATION>

Example measurement files for some supported instrument are in `ExampleFiles/`

## Readers

The following table lists the currently supported readers. If a certain aerosol-measurement-instrument is not listed here, you can either open an [issue](https://github.com/Haisch-Group/pypana/issues), or implement it yourself, so you can profit from the already implemented analysis features of the `InstrumentData` datastructure.

| Device | State | Note |
|--------|-------|------|
| PALAS UFCPC | ✅ | -/- |
| PALAS USMPS | ✅ | -/- |
| PALAS WELAS | ✅ | -/- |
| TSI APS 3310A | planned | -/- |
| TSI APS 3321 | ✅ | -/- |
| TSI CPC 3775 | ✅ | -/- |
| TSI EM 3068 | planned | -/- |
| TSI LAS 3340A | ✅ | -/- |
| TSI SMPS 3071 | ✅ | -/- |
| TSI SMPS 3938 | ✅ | preliminary support for ACTRIS Level 0 and 1 |



## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Haisch-Group/pypana/issues).


## License

pypana is released under the **GNU General Public License v3.0** (GPLv3). See `LICENSE` for details.

    pypana python aerosol analysis package.
    Copyright (C) 2026 TUM IWC - Laser and Particles Group (Haisch-Group)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

**Main Contributors:** Maximilian Böhmichen, Kevin Maier, Nico Chrisam.
