# -*- coding: utf-8 -*-
"""
Script for Data Evaluation of the TSI APS 3321
Data has to be exported in rows and plot is written, so that it displays the dW/logDp

Created 2023-05-15 from oldSMPS_fileread.py

!!first data column is al particles below the given size!!
"""

import numpy as np
import pandas as pd
from datetime import datetime
from tkinter import Tk
from tkinter.filedialog import askopenfilename


def import_data(filename):
    """import aps data from txt file with name filename to pd dataframe
    then extract the actual measuring data from the dataframe and give X, bar_width, Cn and time
    to work, the data has to be exported in rows and should be exported as concentration i guess"""
    data = pd.read_table(filename, sep='\t', header=5, index_col=0, skiprows=1,
                         engine='python', encoding='ansi')

    Cn = data.iloc[:, list(range(3, 55))] #extracts the data by column location
    Cn = Cn.to_numpy()
    x_axis = data.columns.values[list(range(3, 55))] #extracts the aerodynamic diameter from the pd.dataframe header
    x_axis[0] = x_axis[0].strip('<')  # to remove the "smaller" sign of the first column
    x_axis = x_axis.astype(float)
    #conc_data = data.iloc[:, -2]
    #conc_data = conc_data.to_numpy()
    n_bins = len(x_axis)

    delta_x = np.zeros(n_bins)
    for k in range(n_bins):
        if k < n_bins - 1:
            delta_x[k] = x_axis[k + 1] - x_axis[k]
        else:
            delta_x[k] = x_axis[k] - x_axis[k - 1]

    X = np.zeros(Cn.shape)
    bar_width = np.zeros(Cn.shape)
    time = []
    for i in np.arange(len(Cn)):
        X[i] = x_axis
        bar_width[i] = delta_x
        time.append(datetime.strptime(data.iloc[i, 0] + " " + data.iloc[i, 1], '%m/%d/%y %H:%M:%S'))

    return X, bar_width, Cn, time


if __name__ == "__main__":
    def get_filename():
        """get the filename via UI"""
        Tk().withdraw()
        filename = askopenfilename()
        return filename

    filename = get_filename()
    X, bar_width, Cn, time = import_data(filename)
