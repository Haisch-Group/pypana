# -*- coding: utf-8 -*-
"""
PALAS_USMPS_fileread.py

Created 2020-09-14
@written by Karin Wieland
Import of Data and Plot
@edited by Kevin Maier (kevin.r.maier@tum.de)

2020-10-xx: labels plot with comment from txt instead of timestamp
2020-11-14: created functions from previous script as "import_data" and "plot_data"
2020-11-17: added tkinter
2022-01-14-16: redid import function for later using it with one SMPS_analysis file
2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number
2023-01-19: filename is retrieved from SMPS_analysis now
"""

import numpy as np
from datetime import datetime

import pandas as pd

from Sup import get_filename
from Def import device_list


def import_data(filename):
    """takes the raw data and extracts the variables from it to return:
    X  = array with all the X values = particle size
    Xl = array with all the lower borders of the size bins (named Xu in the Palas SMPS file)
    Xu = array with all the upper borders of the size bins (named Xo in the Palas SMPS file)
    Cn = array with all the number counts of the particles per bin in inverted and diffusion corrected (dn_inv_diff in
    the Palas SMPS file)
    time  = list with the starting times of each measurement
    nr_scans = array with the number of the scans=index+1"""
    with open(filename) as f_in:  # open file and keep open
        lines = f_in.readlines()  # read the file in line by line
        len_file = len(lines)  # determine the length of the file
        nr_scans = int(len_file/7)  # calculate the number of scans in the file
        # scan_nr = np.array([i+1 for i in range(0, nr_scans, 1)])  # list of scan numbers for correlating in plots
        # not used atm

        data = []  # defines a list to fill with the data (has to be done this way as the length of the data can vary
        # accordingly to set measuring range
        data_len = []  # defines a list, in which the lengths of each data line are saved to later find out the max and
        # preallocate the data array

        parameters = []  # for import of parameters saved in every first line of the data file, added 20240901
        # with that also import of labels as done before was changed below

        counter = 0  # setting a counter for indexing correctly

        pos = np.arange(0, len_file, 7)  # builds an iterator including the positions of all lines filled with measuring
        # parameters and not data

        for i in np.arange(0, len_file):  # iterating through all lines in the file to produce a list of lists with the
            # data skipping all headerlines (the first and every 7th)
            if i in pos:
                parameters.append(lines[i].split("\t"))  # produces the list in the list called parameters
                # continue  # before, here was just skipped, as the first line was only used for time and label import
            else:
                data.append(lines[i].split("\t"))  # produces the list in the list called data
                data_len.append(len(data[counter]))  # gives the length of each data line for later building the array
                counter += 1
    f_in.close()  # closes the file from which the data was read

    nr_bins = max(data_len)-2  # calculates the maximum number of measuring points in the file subtracting 2 for the
    # first two columns being the "header" columns in the original txt

    X = np.zeros((nr_scans, nr_bins))  # preallocate the arrays
    Xl = np.zeros_like(X)
    Xu = np.zeros_like(X)
    Cn = np.zeros_like(X)
    X[:] = np.nan  # fill the arrays with nans, so all none filled values are nans later and not 0, necessary as within
    Xl[:] = np.nan  # one file, the measurint range can be changed easily on the PALAS SMPS leading to differently sized
    Xu[:] = np.nan  # data width
    Cn[:] = np.nan

    conc_data = input("Which of the available concentration data do you want to import? Type 3 for raw, 4 for "
                           "inverted, 5 for inverted and diffusion corrected")

    for i in range(nr_scans):  # filling the arrays with the values from the data list of lists
        for k in range(2, data_len[int(0 + i * 6)]):
            Xl[i, k-2] = data[int(0 + i * 6)][int(k)]
        for k in range(2, data_len[int(1 + i * 6)]):
            Xu[i, k-2] = data[int(1 + i * 6)][int(k)]
        for k in range(2, data_len[int(2 + i * 6)]):
            X[i, k-2] = data[int(2 + i * 6)][int(k)]  # should be equal to Xo-(Xo-Xu)/2 or Xu+(Xo-Xu)/2
        for k in range(2, data_len[int(int(conc_data) + i * 6)]):  # 5 is based on the inverted diff corrected data, 3
            # on the raw data
            Cn[i, k-2] = data[int(int(conc_data) + i * 6)][int(k)]  # 4 is the inverted but not diff corrected data

    parameter_list = ["Date", "Time", "Comment", "Sheath Temp (C)", "Sample Pressure (mbar)", "Sheath Flow (L/min)",
                      "Aerosol Flow (L/min)", "Relative Humidity Aerosol (%)", "Relative Humidity Sheath (%)",
                      "Sample Temp (C)", "Diff Pressure Impactor (Pa)", "Inner Diameter Column (mm)",
                      "Outer Diameter Column (mm)", "Length Column (mm)", "Transfer-Function A", "Transfer-Function d",
                      "Transfer-Function C", "Set Sheath Flow (L/min)", "Set Aerosol Flow (L/min)", "td (s)",
                      "Counter Type (0=CPC, 1=Elektrometer)", "Lower Size (nm)", "Upper Size (nm)",
                      "Scan Type (0=up, 1=down, 2=up+down_avg, 3=up+down_single)", "Scan Time (s)",
                      "Pre Scan Stabilisation Time (s)", "Neutralizer Type (0=Kr-85, 1=X-Ray)",
                      "HV Polarity (0=positive, 1=negative)"]

    parametersDF = pd.DataFrame(parameters, columns = parameter_list)
    # parameters given in PALAS SMPS manual 6787-de_V2.1_08/21

    time = []  # defining time list
    for i in range(nr_scans):
        time.append(datetime.strptime(parametersDF["Date"][i] + " " + parametersDF["Time"][i], '%m/%d/%Y %I:%M %p'))
        #

    scan_nr = []
    [scan_nr.append(k + 1) for k in range(len(Cn))]

    add_info = parametersDF[(parameter_list[2:])]
    add_info.insert(loc=0, column="Time", value=time)
    add_info.insert(loc=0, column="Scan Nr", value=scan_nr)

    # following part was used before 20240901 to extract time and columns from each measurements first line in the txt
    # labels = np.genfromtxt(fname=filename, delimiter='\t', usecols=(0, 1, 2), dtype=str)
    # # imports the first three columns containing the labels, the date, the time, and the comment from that create time
    # # and len of the whole file
    # time = []  # defining time list
    # comments = []
    # for i in range(0, nr_scans, 1):  # iteratively filling time list with datetime objects
    #     time.append(datetime.strptime(labels[i * 7, 0] + " " + labels[i * 7, 1], '%m/%d/%Y %I:%M %p'))
    #     comments.append(labels[i*7, 2])
    # # %p is the identifier for AM or PM in a 12 hour format

    dX = np.subtract(Xu, Xl)
    dlogX = np.log10(Xu/Xl)
    Cn_dlogX = Cn/dlogX  # calculate dC/dlogX from known interval width

    return X, dX, dlogX, Cn, Cn_dlogX, add_info


def import_data_dict(used_device):
    filename = get_filename()
    X, dX, dlogX, Cn, Cn_dlogX, add_info = import_data(filename)
    # used_device = device_list.query("Import_Script=='PALAS_USMPS_fileread'")["Device_Identifier"].values[0]
    data_dict = {"X": X, "dX": dX, "dlogX": dlogX, "Cn": Cn, "Cn_dlogX": Cn_dlogX, "filename": filename,
                 "used_device": used_device, "add_info": add_info}
    return data_dict


if __name__ == "__main__":

    filename = get_filename()
    X, dX, dlogX, Cn, Cn_dlogX, add_info = import_data(filename)
    print(f"imported {filename}")


