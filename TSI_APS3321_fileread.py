# -*- coding: utf-8 -*-
"""
TSI_APS3321_fileread.py

Script for Data Evaluation of the TSI APS 3321
Data has to be exported in rows

Created 2023-05-15 from TSI_SMPS3071_fileread.py
Recreated on 2025-09-24 from TSI_SMPS_fileread due to changes in import of additional infos

!!first data column is all particles below the given size!!
"""

import numpy as np
import pandas as pd
from datetime import datetime
from Sup import get_filename
from Sup import convert_kPa_to_mbar
from Def import device_list


def rename_columns(df):
    """rename the colums, so they follow the same schematic for all devices"""
    mapping = {'Inlet Pressure': 'Sample Pressure / mbar', 'Total Flow': 'Total Flow / L/min', 'Sheath Flow':
                        'Sheath Flow / L/min', 'Laser Power': 'Laser Power %',
                        'Laser Current': 'Laser Current / mA', 'Sheath Pump Voltage':
                        'Sheath Pump Voltage / V', 'Total Pump Voltage': 'Total Pump Voltage / V',
                        'Box Temperature': 'Box Temperature / °C',
                        'Avalanch Photo Diode Temperature': 'Avalanch Photo Diode Temperature / °C',
                        'Avalanch Photo Diode Voltage': 'Avalanch Photo Diode Voltage / V',
                        u'Median(\xb5m)': u'Median / \xb5m', u'Mean(\xb5m)': u'Mean / \xb5m',
                        u'Geo. Mean(\xb5m)': u'Geo. Mean / \xb5m', u'Mode(\xb5m)': u'Mode / \xb5m',
                        'Total Conc.':  u'Total Conc. / 1/cm\u00B3'}
    df.rename(columns=mapping, inplace=True)

    return df


def def_parameter_list():
    """define parameters that are different between the different devices, here already renamed values are used, as
    the following comparison of columns is done based upon general naming scheme of the whole script"""


    parameter_list = ['Sample #', 'Date', 'Start Time', 'Aerodynamic Diameter','Event 1', 'Event 3', 'Event 4',
                      'Dead Time', 'Sample Pressure / mbar', 'Total Flow / L/min', 'Sheath Flow / L/min',
                      'Analog Input Voltage 0', 'Analog Input Voltage 1', 'Digital Input Level 0',
                      'Digital Input Level 1', 'Digital Input Level 2', 'Laser Power %', 'Laser Current / mA',
                      'Sheath Pump Voltage / V', 'Total Pump Voltage / V', 'Box Temperature / °C',
                      'Avalanch Photo Diode Temperature / °C', 'Avalanch Photo Diode Voltage / V', 'Status Flags',
                      u'Median / \xb5m', u'Mean / \xb5m', u'Geo. Mean / \xb5m', u'Mode / \xb5m', 'Geo. Std. Dev.',
                      u'Total Conc. / 1/cm\u00B3', 'Comment']
    # Comment just added here even though it is not in file, works because of the bug fix implemented for coping with
    # additional columns in slightly different files. :D
    header_pos = 6
    time_format = '%m/%d/%y %H:%M:%S'

    return parameter_list, header_pos, time_format


def import_data(filename):
    """import aps data from txt file with name filename to pd dataframe, also includes time, some settings and some
    statistical values calculated by the TSI program
    then extract the actual measuring data from the dataframe and give X, dX, Cn and time
    to work, the data has to be exported in rows"""

    # data file has variable number of data columns depending on measuring range set so conc data has to be constructed
    # from difference of all columns and the non conc columns = paramter_list

    parameter_list, header_pos, time_format = def_parameter_list()

    data = pd.read_table(filename, sep='\t', header=header_pos, engine='python', encoding='iso-8859-1')
    # originally ansi which is superset of iso; file is in encoding = ansi which caused an import error off cm^3
    # due to wrong encoding setting changed to iso as ansi is windows only and iso also works on linux

    # data = data.reset_index(drop=True)  # resetting index, necessary, when Sample # column is used as index col in
    # pd.read_table -> removed as Sample # is used to directly generate Scan Nr

    data = rename_columns(data)

    nr_scans = len(data)

    # added the following part to avoid the KeyError - key not found in files that do not contain some columns like
    # "Neutralizer Status"
    # seems to work also for other fields that are not contained in the data :D Only when new fields are in the
    # data, but not in the list above, they should be added to the list.

    for k in parameter_list:
        if k in data:
            pass
        else:
            data[k] = np.full((nr_scans,), np.nan)
            # with np.empty, it somehow filled the newly created column with some values from another existing column??

    add_info = data[(parameter_list[3:])]

    conc = data[data.columns.difference(parameter_list, sort=False)].to_numpy()

    x_axis = data[data.columns.difference(parameter_list, sort=False)].columns.values
    # extracts the midpoint diameter from the pd.dataframe header similar to how conc was extracted
    x_axis[0] = x_axis[0].replace("<", "")  # first x-axis value contains "<" as this bin is particles below ca 500 nm
    x_axis = x_axis.astype(float)

    nr_bins = len(x_axis)

    # calculate upper bin boundary from midpoint diameters

    X = np.full_like(conc, np.nan)
    Xl = np.full_like(conc, np.nan)
    Xu = np.full_like(conc, np.nan)

   # multiple methods for building an x-array are implemented in TSI_SMPS_fileread, they could also be used here
    # method 4 gave best results for SMPS, so also used here

    with open(filename) as f_in:  # open file and keep open
        for i, line in enumerate(f_in):
            if i == 4:
                lower_size = float(line.split("\t")[1])
            elif i == 5:
                upper_size = float(line.split("\t")[1])
            elif i == header_pos:
                break
            else:
                continue

    # Method 3: constructing x-axis based on lower and upper limits given in measurement file
    # also the two less indented lines after this block for calculating X and assigning it to X are required

    # const_dlogX = np.log10(upper_size / lower_size) / nr_bins
    # Xl[0, 0] = lower_size
    # Xu[0, -1] = upper_size
    #
    # for k in range(1, nr_bins):
    #     Xl[0, k] = Xl[0, k - 1] * 10 ** (const_dlogX)
    #     Xu[0, k - 1] = Xl[0, k]
    #
    # for i in range(1, nr_scans):
    #     Xl[i] = Xl[0]
    #     Xu[i] = Xu[0]
    #
    # X=(Xl+Xu)/2  # new array for midpoint diameters that are evenly spaced on log axis

    # Method 4: calculating dlogX from resolution in channels per decade (can be automized from log length of axis
    # / by number of bins) similar to Method 3 but then rounded to actual even number (gives 64). Then calculating
    # Xl and Xu from midpoints.

    const_dlogX = 1 / np.rint(nr_bins / np.log10(upper_size / lower_size)) # -> only one number not a row -> Xl and Xu
    for i in range(nr_scans):

        for k in range(nr_bins):
            X[i, k] = x_axis [k]
            Xl[i, k] = (2 * X[i, k]) / (np.power(10, const_dlogX) + 1)
            Xu[i, k] = (2 * X[i, k]) / (1 / np.power(10, const_dlogX) + 1)

    # end of the x-array generation

    # calculate bin width from upper and lower boundary
    dX = np.subtract(Xu, Xl)

    # calculate dlogX from upper and lower boundary
    dlogX = np.log10(Xu/Xl)

    conc_data = input("Which of the possible concentration data is contained in the txt-file? Type 0 for dCn/dlogDp, "
                      "1 for Cn")

    if conc_data == "0":
        Cn_dlogX = conc
        Cn = Cn_dlogX*dlogX
        print("Data imported from dCn/dlogDp")
    elif conc_data == "1":
        Cn = conc
        Cn_dlogX = Cn/dlogX
        print("Data imported from dCn")
    else:
        print(f"{conc_data} is not a viable option, please enter again.")
        conc_data = input("Which of the possible concentration data is contained in the txt-file? Type 0 for dCn/glogDp"
                          ",1 for Cn")

    # calculating time list from dates and times given in measurement file
    time = []
    for i in range(nr_scans):
        time.append(datetime.strptime(data["Date"][i] + " " + data["Start Time"][i], time_format))

    # adding columns to the add_info dataframe in specific positions to match the common scheme
    # add_info.insert(loc=add_info.columns.get_loc("Sample Pressure / kPa") + 1, column="Sample Pressure / mbar",
    #                 value=sample_p_mbar)
    add_info.insert(loc=0, column="Time", value=time)
    add_info.insert(loc=0, column="Scan Nr", value=data["Sample #"])

    return X, dX, dlogX, Cn, Cn_dlogX, add_info


def import_data_dict(used_device, filename):
    # filename = get_filename()
    X, dX, dlogX, Cn, Cn_dlogX, add_info = import_data(filename)
    data_dict = {"X": X, "dX": dX, "dlogX": dlogX, "Cn": Cn, "Cn_dlogX": Cn_dlogX, "filename": filename,
                 "used_device": used_device, "add_info": add_info}
    return data_dict


if __name__ == "__main__":

    filename = get_filename()
    # X, dX, dlogX, Cn, Cn_dlogX, add_info = import_data(filename)
    # print(f"imported {filename}")

    data_dict = \
        import_data_dict(device_list.query("Import_Script=='TSI_APS3321_fileread'")["Device_Identifier"].values[0], filename)
    print(f"imported {data_dict['filename']} as dictionary")