# -*- coding: utf-8 -*-
"""
Script for Data Evaluation of the TSI SMPS consisting of Classifier 3082 and CPC 3775
Data has to be exported in rows and plot is written, so that it displays the dW/logDp

Created 2024-05-01 as copy of TSI_SMPS3938_fileread.py
@written by Kevin Maier (kevin.r.maier@tum.de)
"""

import numpy as np
import pandas as pd
from datetime import datetime
from Sup import get_filename
from Def import device_list


def import_data(filename):
    """import smps data from txt file with name filename to pd dataframe, also includes time, some settings and some
    statistical values calculated by the TSI program
    then extract the actual measuring data from the dataframe and give X, bar_width, Cn and time
    to work, the data has to be exported in rows"""
    data = pd.read_table(filename, sep='\t', header=25, index_col=0, skiprows=0,
                         engine='python', encoding='iso-8859-1')  # originally ansi which is superset of iso
    # smps file is in encoding = ansi which caused an import error off cm^3 due to wrong encoding setting
    # changed to iso as ansi is windows only and iso also works on linux

    Cn = data.iloc[:, list(range(8, 94))] #extracts the data by column location
    Cn = Cn.to_numpy()
    x_axis = data.columns.values[list(range(8, 94))] #extracts the midpoint diameter from the pd.dataframe header
    x_axis = x_axis.astype(float)
    #conc_data = data.iloc[:, -2]
    #conc_data = conc_data.to_numpy()
    n_bins = len(x_axis)

    delta_x = np.zeros(n_bins)  # only gives the delta between the midpoint diameters, but nor the real bin min and max
    for k in range(n_bins):
        if k < n_bins - 1:
            delta_x[k] = x_axis[k + 1] - x_axis[k]
        else:
            delta_x[k] = x_axis[k] - x_axis[k - 1]

    # log_delta_x = np.zeros(n_bins)  # attempt to convert from dCn/dlog(dp)
    # for k in range(n_bins):
    #     if k < n_bins - 1:
    #         log_delta_x[k] = np.log(x_axis[k + 1]/x_axis[k])
    #     else:
    #         delta_x[k] = np.log(x_axis[k]/x_axis[k - 1])
    #
    # for k in range(len(Cn)):
    #     Cn[k] = Cn[k]*log_delta_x[k]

    X = np.zeros(Cn.shape)
    bar_width = np.zeros(Cn.shape)
    time = []
    for i in np.arange(len(Cn)):
        X[i] = x_axis
        bar_width[i] = delta_x
        time.append(datetime.strptime(data.iloc[i, 0] + " " + data.iloc[i, 1], '%m/%d/%Y %H:%M:%S'))

    return X, bar_width, Cn, time


def import_data_dict():
    filename = get_filename()
    X, bar_width, Cn, time = import_data(filename)
    scan_nr = []
    [scan_nr.append(k + 1) for k in range(len(Cn))]
    used_device = device_list.query("Import_Script=='TSI_SMPS3938_fileread'")["Device_Identifier"].values[0]
    data_dict = {"X": X, "Cn": Cn, "bar_width": bar_width, "time": time, "scan_nr": scan_nr, "filename": filename,
                 "used_device": used_device}
    return data_dict


if __name__ == "__main__":

    filename = get_filename()
    X, bar_width, Cn, time = import_data(filename)
    print(f"imported {filename}")

