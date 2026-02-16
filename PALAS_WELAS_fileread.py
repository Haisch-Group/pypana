"""
PALAS_WELAS_fileread.py

Script for Data import of the PALAS WELAS

Created 2025-07-20
@written by Kevin Maier (kevin.r.maier@tum.de)
"""

from datetime import datetime

import numpy as np
import pandas as pd

from Def import device_list
from Sup import get_filename


def import_data(filename):
    """takes the raw data and extracts the variables from it to return:
    X  = array with all the X values = particle size
    Xl = array with all the lower borders of the size bins (named Xuk in the PALAS WELAS file)
    Xu = array with all the upper borders of the size bins (named Xok in the PALAS WELAS file)
    Cn = array with all the number concentrations of the particles per bin (dCn in
    the PALAS WELAS file)
    time  = list with the starting times of each measurement
    nr_scans = array with the number of the scans=index+1"""
    with open(filename) as f_in:  # open file and keep open
        lines = f_in.readlines()  # read the file in line by line
        len_file = len(lines)  # determine the length of the file
        nr_scans = int(
            len_file / 49
        )  # calculate the number of scans in the file - 49 lines = 1 msmt

        data = []  # defines a list to fill with the data (has to be done this way as the length of the data can vary
        # accordingly to set measuring range
        data_len = []  # defines a list, in which the lengths of each data line are saved to later find out the max and
        # preallocate the data array

        first_lines = []  # for import of parameters saved in every first line of the data file
        # unfortunately, that is completely different to what SMPS data looks like, only date, time and time interval of
        # measured distribution is written here

        counter = 0  # setting a counter for indexing correctly

        pos = np.arange(
            0, len_file, 49
        )  # builds an iterator including the positions of all first lines of measurements

        for i in np.arange(
            0, len_file
        ):  # iterating through all lines in the file to produce a list of lists with the
            # dates and data skipping all useless lines
            if i in pos:
                first_lines.append(
                    lines[i].split(" ")
                )  # produces the list in the list called parameters
                data.append(
                    lines[i + 19].split("\t")
                )  # produces the list in the list called data - adds Xuk
                data.append(lines[i + 20].split("\t"))  # adds X
                data.append(lines[i + 21].split("\t"))  # adds Xok
                data.append(lines[i + 22].split("\t"))  # adds dX
                data.append(lines[i + 26].split("\t"))  # adds dCn
                data_len.append(
                    len(data[counter])
                )  # gives the length of each data line for later building the array
                counter += 1
            else:
                continue
    f_in.close()  # closes the file from which the data was read

    nr_bins = (
        max(data_len) - 2
    )  # calculates the maximum number of measuring points in the file subtracting 2 for the
    # first column being the "header" column in the original txt + last column being empty

    Xl = np.full(
        (nr_scans, nr_bins), np.nan
    )  # preallocate the arrays and fill the arrays with nans, so all
    X = np.full_like(Xl, np.nan)  # none filled values are nans later and not 0
    Xu = np.full_like(Xl, np.nan)
    dX = np.full_like(Xl, np.nan)
    Cn = np.full_like(Xl, np.nan)

    for i in range(
        nr_scans
    ):  # filling the arrays with the values from the data list of lists
        for k in range(
            1, data_len[i] - 1
        ):  # transfer values from list of list to respective array
            Xl[i, k - 1] = data[int(0 + i * 5)][int(k)]
            X[i, k - 1] = data[int(1 + i * 5)][
                int(k)
            ]  #  X should be equal to Xo-(Xo-Xu)/2 or Xu+(Xo-Xu)/2
            Xu[i, k - 1] = data[int(2 + i * 5)][int(k)]
            dX[i, k - 1] = data[int(3 + i * 5)][int(k)]
            Cn[i, k - 1] = data[int(4 + i * 5)][int(k)]
            # k-1 in new array as field 0 in it is filled with field 1 of list as first column in data is "header2

    parameter_list = ["Date", "Time", "whatever", "whatever2", "accumulation", "mode"]

    parametersDF = pd.DataFrame(first_lines, columns=parameter_list)

    time = []  # defining time list
    for i in range(nr_scans):
        time.append(
            datetime.strptime(
                parametersDF["Date"][i] + " " + parametersDF["Time"][i],
                "%Y/%m/%d %H:%M:%S",
            )
        )

    scan_nr = []
    [scan_nr.append(k + 1) for k in range(len(Cn))]

    add_info = pd.DataFrame(
        {
            "Time": time,
            "Scan Nr": scan_nr,
            "Comment": parametersDF["whatever"]
            + " "
            + parametersDF["whatever2"]
            + " "
            + parametersDF["accumulation"]
            + " "
            + parametersDF["mode"],
        }
    )

    dX = np.subtract(Xu, Xl)
    dlogX = np.log10(Xu / Xl)
    Cn_dlogX = Cn.copy() / dlogX  # calculate dC/dlogX from known interval width

    return X, dX, dlogX, Cn, Cn_dlogX, add_info


def import_data_dict(used_device, filename, data_choice=""):
    # filename = get_filename()
    X, dX, dlogX, Cn, Cn_dlogX, add_info = import_data(filename)
    data_dict = {
        "X": X,
        "dX": dX,
        "dlogX": dlogX,
        "Cn": Cn,
        "Cn_dlogX": Cn_dlogX,
        "filename": filename,
        "used_device": used_device,
        "add_info": add_info,
    }
    return data_dict


if __name__ == "__main__":
    filename = get_filename()
    # X, dX, dlogX, Cn, Cn_dlogX, add_info = import_data(filename)
    # print(f"imported {filename}")

    data_dict = import_data_dict(
        device_list.query("Import_Script=='PALAS_WELAS_fileread'")[
            "Device_Identifier"
        ].values[0],
        filename,
    )
    print(f"imported {data_dict['filename']} as dictionary")
