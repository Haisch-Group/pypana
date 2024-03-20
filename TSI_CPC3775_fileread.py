# -*- coding: utf-8 -*-
"""
Script for Data import of the TSI CPC 3775
Data has to be exported in rows

Created 2022-03-10
@written by Kevin Maier (kevin.r.maier@tum.de)

2022-03-24 finished import_data function to produce Cn, el_time, start_time
"""

import numpy as np
import pandas as pd
from datetime import datetime
from Sup import get_filename


def import_data(filename):
    """import cpc data from txt file with name filename to pd dataframe, also includes time, some settings and some
    statistical values calculated by the TSI program
    then extract the actual measuring data from the dataframe and give X, bar_width, Cn and time
    to work, the data has to be exported in rows"""

    data = pd.read_table(filename, sep=',', header=2, index_col=0,
                         engine='python', encoding='ANSI')  # dropped utf-8 error as file is ANSI encoded
    # changed separator to "," from "/t" as i exported data with , separation

    timepoints = data.iloc[0, 2] / data.iloc[0, 3]
    el_time = np.array(range(data.iloc[0, 3], data.iloc[0, 2]+data.iloc[0, 3], data.iloc[0, 3]))  # elapsed time

    start_time = []
    Cn = np.zeros((len(data), int(timepoints)))

    for i in range(len(data)):
        start_time.append(datetime.strptime(data.iloc[i, 0] + " " + data.iloc[i, 1], '%m/%d/%y %H:%M:%S'))
        for k in range(int(timepoints)):
            #Cn[i, k] = data.iloc[i, 11+k*2] # for tab separatore used before
            Cn[i, k] = data.iloc[i, 11 + k * 4] # for currently used eport, as analog outputs were saved there too

    return Cn, el_time, start_time


if __name__ == "__main__":

    filename = get_filename()
    Cn, el_time, start_time = import_data(filename)
