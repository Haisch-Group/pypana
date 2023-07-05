# -*- coding: utf-8 -*-
"""
Script for Data import of the PALAS CPC 100

Created v0 2022-03-10 to 2022-04-04
@written by Kevin Maier (kevin.r.maier@tum.de)

2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number
"""

import numpy as np
from datetime import datetime
from get_filename import get_filename


def import_data(filename):
    """"""

    with open(filename) as f_in:  # open file and keep open
        lines = f_in.readlines()  # read the file in line by line
        len_file = len(lines)  # determine the length of the file

        data_list = []  # defines a list to fill with the data

        for i in np.arange(0, len_file):  # iterating through all lines in the file to produce a list of lists with the
            # data
                data_list.append(lines[i].split("\t"))  # produces the list in the list called data

        data = np.array(data_list) # makes the list of lists an np array for navigating easily
        # well in lists of lists its not harder, but i am more used to np :D

    f_in.close()  # closes the file from which the data was read

    # determine the number of measurements saved in one file from the comments and save the index of the last measuring
    # point per measurement in an indexlist
    msmt_counter = 1
    indexlist = []
    for k in range(1, len_file):
        if data[k, 2] == data[k - 1, 2]:
            continue
        else:
            msmt_counter += 1
            indexlist.append(k-1)
    indexlist.append(len_file-1)

    # determine the length of each measurement
    msmt_len_list = []
    for k in range(len(indexlist)):
        if k == 0:
            msmt_len_list.append(indexlist[k]+1)
        else:
            msmt_len_list.append(indexlist[k]-indexlist[k-1])

    # produce the elapsed time scale from the longest measurement
    el_time = np.array(range(1, max(msmt_len_list)+1, 1))

    # produce and fill the concentration array with the data and leave the non filled cells as nan, so no bullshit
    # is plotted/calculated, also create and fill the start_time list
    Cn = np.zeros((msmt_counter, max(msmt_len_list)))
    Cn[:] = np.nan
    start_time = []  # defining start_time list

    for k in range(0, msmt_counter):
        if k == 0:
            Cn[k, 0:indexlist[k]+1] = data[k:indexlist[k]+1, 3].T # not really sure, why indexlist+1, but it gives the
            # correct result
            start_time.append(datetime.strptime(data[0, 0] + " " + data[0, 1], '%m/%d/%Y %I:%M:%S %p'))
        else:
            Cn[k, 0:msmt_len_list[k]] = data[indexlist[k-1]+1:indexlist[k]+1, 3].T
            start_time.append(datetime.strptime(data[indexlist[k-1]+1, 0] + " " + data[indexlist[k-1]+1, 1], '%m/%d/%Y %I:%M:%S %p'))

    return Cn, el_time, start_time


if __name__ == "__main__":

    filename = get_filename()
    Cn, el_time, start_time = import_data(filename)


