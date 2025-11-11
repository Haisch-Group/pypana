# -*- coding: utf-8 -*-
"""
PALAS_UFCPC_fileread.py

Script for Data import of the PALAS CPC 100 or 50

Created v0 2022-03-10 to 2022-04-04
@written by Kevin Maier (kevin.r.maier@tum.de)

2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number

2024-06 to 2025-11 updated t provide data of structure as used in particle_analysis.py
"""

import numpy as np
from datetime import datetime
from Sup import get_filename
import pandas as pd
from Def import device_list


def import_data(filename):
    """"""
    parameter_list = ["Date", "Time", "Comment", u"1s Mean Particle Concentration / 1/cm\u00B3",
                      u"10s Mean Particle Concentration / 1/cm\u00B3", u"Mean Droplet size / \u00B5m",
                      "Aerosol Flow / L/min", "Empty Field", "T Condenser / °C", "T Saturator / °C",
                      "Operating Mode DSI (0=off, 1=Humidity, 2=Differential Pressure)",
                      "Target Relative Humidity %", "Target Differential Pressure / Pa",
                      "Actual Differential Pressure / Pa", "Power of Pump %", "Relative Humidity %",
                      "Absolute Pressure / mbar", "T Aerosol Inlet / °C", "Error Notification (0=no Error, 1 = Error)",
                      "Position of Valve in MSS 08 (1-8)"]
    # parameters given in PALAS CPC manual 4597-de_V1.0_06/17 page 23, Operating Mode to T Aerosol Inlet only relevant
    # for ENVI CPC

    nonusedcolumns = ["Date", "Time", "Comment", u"1s Mean Particle Concentration / 1/cm\u00B3", "Empty Field",
                      "Operating Mode DSI (0=off, 1=Humidity, 2=Differential Pressure)",
                      "Target Relative Humidity %", "Target Differential Pressure / Pa",
                      "Actual Differential Pressure / Pa",  "Relative Humidity %", "T Aerosol Inlet / °C",
                      "Position of Valve in MSS 08 (1-8)"]
    # first four columns are rearranged in the following script and are in this list as they should be excluded from the
    # add_info dataframe, the rest of the columns is currently not giving meaningful data for UFCPC, so they are also
    # not to be included in the add_info dataframe in the end

    data = pd.read_table(filename, sep='\t',index_col=False, names=parameter_list, engine='python')
    # load the entire file as pd dataframe

    # determine the number of measurements saved in one file from the comments and save the index of the last measuring
    # point per measurement in an indexlist:
    len_file = len(data)

    msmt_counter = 1  # start at 1, as the file is only written, when a measurement is taken
    indexlist = [0]  # create list for indices of each last measuring point, first index = 0
    comment_list =[data["Comment"][0]]  # also create list for all comments starting with first
    # measurement works by ticking a checkbox, then the current measurement is saved, when unticking, saving stops until
    # next time the box is ticked, then the new measurement is just appended, so last index of a measurement is
    # index-1 of the next measurement
    for k in range(1, len_file):
        if data["Comment"][k] == data["Comment"][k - 1]:  # comment needs to be entered before ticking the checkbox for
            continue  # this selection process to work, then measurements are identified by change of the comment
        else:
            msmt_counter += 1
            indexlist.append(k)  # this appends first point of each measurement
            comment_list.append(data["Comment"][k])

    # determine the length of each measurement
    msmt_len_list = []  # calculate the length of each scan from the first and the last index of each measurement
    for k in range(msmt_counter):  # go through all entries in indexlist and calculate lengths of each msmt from indices
        if k == msmt_counter-1:  # k starts from 0, so msmt_conter-1 is last entry in indexlist
            msmt_len_list.append(len_file-indexlist[k])  # len of file - start index of last measurement = len
        else:
            msmt_len_list.append(indexlist[k+1]-indexlist[k])  # first point of next - last point of current msmt

    # produce and fill the concentration array with the data and leave the non-filled cells as nan, so no bullshit
    # is plotted/calculated, also create and fill the start_time list
    Cn = np.zeros((msmt_counter, max(msmt_len_list)))
    Cn[:] = np.nan
    start_time = []  # defining start_time list

    for k in range(msmt_counter):  # go through all measurements and fill Cn array from 0 to length of the measurement
        # with data from indexlist (startindex of msmt till startindex of next msmt -1 )
        if k == msmt_counter-1:  # for last msmt, no startindex of next is available so end of file is used
            Cn[k, 0:msmt_len_list[k]] = \
                data[u"1s Mean Particle Concentration / 1/cm\u00B3"][indexlist[k]:len_file]
            start_time.append(datetime.strptime(data["Date"][indexlist[k]] + " " + data["Time"][indexlist[k]],
                                                '%m/%d/%Y %I:%M:%S %p'))
        else:
            Cn[k, 0:msmt_len_list[k]] = \
                data[u"1s Mean Particle Concentration / 1/cm\u00B3"][indexlist[k]:indexlist[k+1]]
            start_time.append(datetime.strptime(data["Date"][indexlist[k]] + " " + data["Time"][indexlist[k]],
                                                '%m/%d/%Y %I:%M:%S %p'))


    # calculate elapsed time array from each time point - start point of the measurement (done this way because PALAS
    # SMPS sometimes had a hanger and just assigning an elapsed_time array with 1s intervals might lead to wrong axis)
    el_time = np.zeros_like(Cn)  # preallocation of array
    el_time[:] = np.nan  # filling with NaN to not have wrong numbers in there
    for k in range(msmt_counter):  # goint through all measurements
        for i in range(0, msmt_len_list[k]):  # and in that through all entries to calculate elapsed time for each
            dt = datetime.strptime(data["Date"][indexlist[k]+i] + " " + data["Time"][indexlist[k]+i],
                                   '%m/%d/%Y %I:%M:%S %p') - start_time[k]
            el_time[k, i] = dt.total_seconds()  # assign calculated time in seconds to el_time array

    # create scan numbers as list from msmt_counter with +1 as range is exclusive on right side
    scan_nr = []
    [scan_nr.append(k) for k in range(1, msmt_counter+1)]

    # get all additionally available info and pack it in a dataframe that has the same size as the Cn array
    # must be made to lists of lists to pack it in the dataframe
    usedcolumns = data[data.columns.difference(nonusedcolumns)].columns.values  # get column names from difference of
    # all column headers and the nonusedcolumns headers
    add_info = pd.DataFrame()  # create empty dataframe
    for data_column in usedcolumns:  # go through all columns in the original dataframe
        listoflists = []  # create a list for each column that will include lists for each measurement
        for i in range(msmt_counter):  # go through all measurements in each column
            list = []  # create a list, that will contain all values of one measurement
            for k in range(msmt_len_list[i]):  # go through all datapoints in each measurement in each column
                list.append(data[data_column][indexlist[i]+k])  # append these values to the list of one measurement
            listoflists.append(list)  # append the list of values to the list representing one column
        add_info[data_column] = listoflists  # add the list of lists as column to new dataframe

    add_info.insert(loc=0, column="Comment", value=comment_list)  # insert the comment, start_time and scan_nr lists
    add_info.insert(loc=0, column="Time", value=start_time)  # in the dataframe too
    add_info.insert(loc=0, column="Scan Nr", value=scan_nr)

    return Cn, el_time, add_info


def import_data_dict(used_device, filename):
    # filename = get_filename()
    Cn, el_time, add_info = import_data(filename)
    data_dict = {"Cn": Cn, "el_time": el_time, "filename": filename, "used_device": used_device, "add_info":add_info}
    return data_dict


if __name__ == "__main__":

    filename = get_filename()
    # Cn, el_time, start_time = import_data(filename)
    # print(f"imported {filename}")

    data_dict = \
        import_data_dict(device_list.query("Import_Script=='PALAS_UFCPC_fileread'")["Device_Identifier"].values[0], filename)
    print(f"imported {data_dict['filename']} as dictionary")
