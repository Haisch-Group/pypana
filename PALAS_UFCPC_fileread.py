# -*- coding: utf-8 -*-
"""
PALAS_UFCPC_fileread.py

Script for Data import of the PALAS CPC 100

Created v0 2022-03-10 to 2022-04-04
@written by Kevin Maier (kevin.r.maier@tum.de)

2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number
"""

import numpy as np
from datetime import datetime
from Sup import get_filename
import pandas as pd
from Def import device_list


def import_data(filename):
    """"""
    parameter_list = ["Date", "Time", "Comment", u"1s Mean Particle Concentration (1/cm\u00B3)",
                      u"10s Mean Particle Concentration (1/cm\u00B3)", u"Mean Droplet size (\u00B5m)",
                      "Aerosol Flow (L/min)", "Empty Field", "T Condenser (C)", "T Saturator (C)",
                      "Operating Mode DSI (0=off, 1=Humidity, 2=Diiferential Pressure)",
                      "Target Relative Humidity (%)", "Target Differential Pressure (Pa)",
                      "Actual Differential Pressure (Pa)", "Power of Pump (%)", "Relative Humidity (%)",
                      "Absolute Pressure (mbar)", "T Aerosol Inlet (C)", "Error Notification (0=no Error, 1 = Error",
                      "Position of Valve in MSS 08 (1-8)"]
    # parameters given in PALAS CPC manual 4597-de_V1.0_06/17 page 23, Operating Mode to T Aerosol Inlet only relevant
    # for ENVI CPC

    nonusedcolumns = ["Empty Field", "Operating Mode DSI (0=off, 1=Humidity, 2=Diiferential Pressure)",
                      "Target Relative Humidity (%)", "Target Differential Pressure (Pa)",
                      "Actual Differential Pressure (Pa)",  "Relative Humidity (%)", "T Aerosol Inlet (C)",
                      "Position of Valve in MSS 08 (1-8)"]
    # currently not giving meaningful data for UFCPC, so they are not used

    data = pd.read_table(filename, sep='\t', names=parameter_list, engine='python')
    # load the entire file as pd dataframe

    # determine the number of measurements saved in one file from the comments and save the index of the last measuring
    # point per measurement in an indexlist:
    len_file = len(data)

    msmt_counter = 1  # start at 1, as the file is only written, when a measurement is taken
    indexlist = []  # create list for indices of each last measuring point
    # measurement works by ticking a checkbox, then the current measurement is saved, when unticking, saving stops until
    # next time the box is ticked, then the new measurement is just appended, so last index of first point in next
    # measurement is index+1 of the last point in the previous measurement
    for k in range(1, len_file):
        if data["Comment"][k] == data["Comment"][k - 1]:  # comment needs to be entered before ticking the checkbox for
            continue  # this selection process to work, then measurements are identified by change of the comment
        else:
            msmt_counter += 1
            indexlist.append(k-1)  # this appends last point before comment changed = last point of previous measurement
    indexlist.append(len_file-1)

    # determine the length of each measurement
    msmt_len_list = []  # calculate the length of each scan from the first and the last index of each measurement
    for k in range(len(indexlist)):  # defined
        if k == 0:
            msmt_len_list.append(indexlist[k]+1)  # as index follows python logic, length is index+1 also counting 0
        else:
            msmt_len_list.append(indexlist[k]-indexlist[k-1])  # last point of current - last point of previous msmt

    # produce and fill the concentration array with the data and leave the non filled cells as nan, so no bullshit
    # is plotted/calculated, also create and fill the start_time list
    Cn = np.zeros((msmt_counter, max(msmt_len_list)))
    Cn[:] = np.nan
    start_time = []  # defining start_time list

    for k in range(0, msmt_counter):
        if k == 0:
            Cn[k, 0:indexlist[k]+1] = data[u"1s Mean Particle Concentration (1/cm\u00B3)"][k:indexlist[k]+1]

            start_time.append(datetime.strptime(data["Date"][0] + " " + data["Time"][0], '%m/%d/%Y %I:%M:%S %p'))
        else:
            Cn[k, 0:msmt_len_list[k]] = data[u"1s Mean Particle Concentration (1/cm\u00B3)"][indexlist[k-1]+1:indexlist[k]+1]
            start_time.append(datetime.strptime(data["Date"][indexlist[k-1]+1] + " " + data["Time"][indexlist[k-1]+1, 1],
                                                '%m/%d/%Y %I:%M:%S %p'))


    # produce the elapsed time scale from the shape of the cn array
    el_time = np.zeros_like(Cn)
    el_time[:] = np.nan
    for k in range(len(el_time)):
        for i in range(msmt_len_list[k]):
            el_time[k, i] = indexlist[k]+i






    scan_nr = indexlist



    return Cn, el_time, add_info


def import_data_dict(used_device):
    filename = get_filename()
    Cn, el_time, add_info = import_data(filename)
    # used_device = device_list.query("Import_Script=='PALAS_UFCPC_fileread'")["Device_Identifier"].values[0]
    data_dict = {"Cn": Cn, "el_time": el_time, "filename": filename, "used_device": used_device, "add_info":add_info}
    return data_dict


if __name__ == "__main__":

    filename = get_filename()
    Cn, el_time, start_time = import_data(filename)


