# -*- coding: utf-8 -*-
"""
PALAS_WELAS_fileread.py

Script for Data import of the PALAS WELAS

Created 2025-07-20
@written by Kevin Maier (kevin.r.maier@tum.de)
"""

### txt data format is crazyly bad

import numpy as np
from datetime import datetime

import pandas as pd

from Sup import get_filename
from Sup import convert_mbar_to_kPa
from Def import device_list


def import_data(filename):
    """takes the raw data and extracts the variables from it to return:
    X  = array with all the X values = particle size
    Xl = array with all the lower borders of the size bins (named Xuk in the Palas WELAS file)
    Xu = array with all the upper borders of the size bins (named Xok in the Palas WELAS file)
    Cn = array with all the number concentrations of the particles per bin (dCn in
    the Palas WELAS file)
    time  = list with the starting times of each measurement
    nr_scans = array with the number of the scans=index+1"""
    with open(filename) as f_in:  # open file and keep open
        lines = f_in.readlines()  # read the file in line by line
        len_file = len(lines)  # determine the length of the file
        nr_scans = int(len_file/50) # calculate the number of scans in the file - 50 lines = 1 msmt

        data = []  # defines a list to fill with the data (has to be done this way as the length of the data can vary
        # accordingly to set measuring range
        data_len = []  # defines a list, in which the lengths of each data line are saved to later find out the max and
        # preallocate the data array

        first_lines = []  # for import of parameters saved in every first line of the data file
        # unfortunately, that is completely different to what SMPS data looks like, only date, time and time interval of
        # measured distribution is written here

        counter = 0  # setting a counter for indexing correctly

        pos = np.arange(0, len_file, 49)  # builds an iterator including the positions of all first lines of measurements

        for i in np.arange(0, len_file):  # iterating through all lines in the file to produce a list of lists with the
            # dates and data skipping all useless lines
            if i in pos:
                first_lines.append(lines[i].split("\t"))  # produces the list in the list called parameters
                data.append(lines[i+19].split("\t"))  # produces the list in the list called data - adds Xuk
                data.append(lines[i+20].split("\t"))  # adds X
                data.append(lines[i+21].split("\t"))  # adds Xok
                data.append(lines[i+22].split("\t"))  # adds dX
                data.append(lines[i+26].split("\t"))  # adds dCn
                data_len.append(len(data[counter]))  # gives the length of each data line for later building the array
                counter += 1
            else:
                continue
    f_in.close()  # closes the file from which the data was read

    nr_bins = max(data_len)-2  # calculates the maximum number of measuring points in the file subtracting 2 for the
    # first two columns being the "header" columns in the original txt

###hier geendet, sortieren wie oben

    X = np.zeros((nr_scans, nr_bins))  # preallocate the arrays
    Xl = np.zeros_like(X)
    Xu = np.zeros_like(X)
    dX = np.zeros_like(X)
    Cn = np.zeros_like(X)
    X[:] = np.nan  # fill the arrays with nans, so all none filled values are nans later and not 0, necessary as within
    Xl[:] = np.nan  # one file, the measuring range can be changed easily on the PALAS SMPS leading to differently sized
    Xu[:] = np.nan  # data width
    dX[:] = np.nan
    Cn[:] = np.nan

### hier die richtigen zahlen aus liste von listen eintragen die oben generiert wurde.

    for i in range(nr_scans):  # filling the arrays with the values from the data list of lists
        for k in range(2, data_len[int(0 + i * 5)]):  # lower bin boundary values contained in each second line in the
            Xl[i, k-2] = data[int(0 + i * 6)][int(k)]  # file, or first line in data list of lists created before
        for k in range(2, data_len[int(1 + i * 5)]):  # upper bin boundary values contained in each third line in the
            Xu[i, k-2] = data[int(1 + i * 5)][int(k)]  # file, or second line in data list of lists created before
        for k in range(2, data_len[int(2 + i * 5)]):  # bin midpoints from firth line in file or third in data listslist
            X[i, k-2] = data[int(2 + i * 5)][int(k)]  # should be equal to Xo-(Xo-Xu)/2 or Xu+(Xo-Xu)/2
        for k in range(2, data_len[int(int(3) + i * 5)]):  # dCn
            Cn[i, k-2] = data[int(int(3) + i * 5)][int(k)]

### dump this, its useless basically, the whole part, only write datetime and comment or something similar

    parameter_list = ["Date", "Time", "Comment", "Sheath Temp / °C", "Sample Pressure / mbar", "Sheath Flow / L/min",
                      "Aerosol Flow / L/min", "Relative Humidity Aerosol %", "Relative Humidity Sheath %",
                      "Sample Temp / °C", "Diff Pressure Impactor / Pa", "Inner Diameter Column / mm",
                      "Outer Diameter Column / mm", "Length Column / mm", "Transfer-Function A", "Transfer-Function d",
                      "Transfer-Function C", "Set Sheath Flow / L/min", "Set Aerosol Flow / L/min", "td / s",
                      "Counter Type (0=CPC, 1=Elektrometer)", "Lower Size / nm", "Upper Size / nm",
                      "Scan Type (0=up, 1=down, 2=up+down_avg, 3=up+down_single)", "Scan Time / s",
                      "Pre Scan Stabilisation Time / s", "Neutralizer Type (0=Kr-85, 1=X-Ray)",
                      "HV Polarity (0=positive, 1=negative)"]

    # parameters given in PALAS SMPS manual 6787-de_V2.1_08/21 page 66, newer SMPS has 2 columns more in each header row
    # so for these files, additional headers have to be added to header list after firmware update both SMPS give these
    # data

    if len(parameters[0]) == 28:
        pass
    elif len(parameters[0]) == 30:
        parameter_list.extend(["CPC1 Device Status (0=not ready, 1=ready)", "CPC2 Device Status (0=not ready, 1=ready)"])
    else:  # added to avoid the error when there are more columns coming. :D
        parameter_list.extend(["CPC1 Device Status (0=not ready, 1=ready)", "CPC2 Device Status (0=not ready, 1=ready)"])
        count = 2
        while len(parameter_list) < len(parameters[0]):
            parameter_list.append("")  # if parameters have less than 28 columns, still an error will occur
            count += 1
        print(f"Added {count} column headers as parameters line contains {28+count} columns")

    parametersDF = pd.DataFrame(parameters, columns=parameter_list)

    time = []  # defining time list
    for i in range(nr_scans):
        time.append(datetime.strptime(parametersDF["Date"][i] + " " + parametersDF["Time"][i], '%m/%d/%Y %I:%M %p'))
        #

    scan_nr = []
    [scan_nr.append(k + 1) for k in range(len(Cn))]

    add_info = parametersDF[(parameter_list[2:])]

    sample_p_kPa = convert_mbar_to_kPa(parametersDF["Sample Pressure / mbar"].astype(float).copy())
    add_info.insert(loc=add_info.columns.get_loc("Sample Pressure / mbar") + 1, column="Sample Pressure / kPa",
                    value=sample_p_kPa)
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
    data_dict = {"X": X, "dX": dX, "dlogX": dlogX, "Cn": Cn, "Cn_dlogX": Cn_dlogX, "filename": filename,
                 "used_device": used_device, "add_info": add_info}
    return data_dict


if __name__ == "__main__":

    # filename = get_filename()
    # X, dX, dlogX, Cn, Cn_dlogX, add_info = import_data(filename)
    # print(f"imported {filename}")

    data_dict = \
        import_data_dict(device_list.query("Import_Script=='PALAS_USMPS_fileread'")["Device_Identifier"].values[0])
    print(f"imported {data_dict['filename']} as dictionary")