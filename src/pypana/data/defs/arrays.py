"""Data type for most measured arrays."""

import numpy as np
import numpy.typing as npt

type FloatArray = npt.NDArray[np.floating]

type DateTime64Array = npt.NDArray[np.datetime64]
