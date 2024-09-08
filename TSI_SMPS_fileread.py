# -*- coding: utf-8 -*-
"""
TSI_SMPS_fileread.py

Script for Data Evaluation of the TSI SMPS consisting of Classifier 3082 and CPC 3775
Data has to be exported in rows and plot is written, so that it displays the dW/logDp

Created 2024-05-01 as copy of TSI_SMPS3071_fileread.py
@written by Kevin Maier (kevin.r.maier@tum.de)
"""

import numpy as np
import pandas as pd
from datetime import datetime
from Sup import get_filename
from Sup import convert_kPa_to_mbar
from Def import device_list


def rename_columns(df, used_device):
    """rename the colums, so they follow the same schematic for all devices"""
    if used_device == device_list.query("Device=='SMPS 3938'")["Device_Identifier"].values[0]:
        mapping = {'Sample Temp (C)': 'Sample Temp / °C', 'Sample Pressure (kPa)': 'Sample Pressure / kPa',
                            'Relative Humidity (%)': 'Relative Humidity %', 'Mean Free Path (m)': 'Mean Free Path / m',
                            'Gas Viscosity (Pa*s)': u'Gas Viscosity / Pa\u00B7s', 'Diameter Midpoint (nm)':
                            'Diameter Midpoint / nm', 'Scan Time (s)': 'Scan Time / s', 'Retrace Time (s)':
                            'Retrace Time / s', 'Scan Resolution (Hz)': 'Scan Resolution / Hz', 'Sheath Flow (L/min)':
                            'Sheath Flow / L/min', 'Aerosol Flow (L/min)': 'Aerosol Flow / L/min',
                            'Bypass Flow (L/min)': 'Bypass Flow / L/min', 'Low Voltage (V)': 'Low Voltage / V',
                            'High Voltage (V)': 'High Voltage / V', 'Lower Size (nm)': 'Lower Size / nm',
                            'Upper Size (nm)': 'Upper Size / nm', 'Density (g/cm³)': u'Density / g/cm\u00B3',
                            'td + 0.5 (s)': 'td + 0.5 / s', 'tf (s)': 'tf / s', 'D50 (nm)': 'D50 / nm',
                            'Neutralizer Status ': 'Neutralizer Status', 'Median (nm)': 'Median / nm', 'Mean (nm)':
                            'Mean / nm', 'Geo. Mean (nm)': 'Geo. Mean / nm', 'Mode (nm)': 'Mode / nm',
                            'Total Conc. (#/cm³)': u'Total Conc. / 1/cm\u00B3'}
        df.rename(columns=mapping, inplace=True)
    elif used_device == device_list.query("Device=='SMPS 3071'")["Device_Identifier"].values[0]:
        mapping = {'Sample Temp (C)': 'Sample Temp / °C', 'Sample Pressure (kPa)': 'Sample Pressure / kPa',
                    'Mean Free Path (m)': 'Mean Free Path / m', 'Gas Viscosity (Pa*s)': u'Gas Viscosity / Pa\u00B7s',
                    'Diameter Midpoint': 'Diameter Midpoint / nm', 'Scan Up Time(s)': 'Scan Time / s',
                    'Retrace Time(s)': 'Retrace Time / s', 'Impactor Type(cm)': 'Impactor Type / cm',
                    'Sheath Flow(lpm)': 'Sheath Flow / L/min', 'Aerosol Flow(lpm)': 'Aerosol Flow / L/min',
                    'CPC Inlet Flow(lpm)': 'CPC Inlet Flow / L/min', 'CPC Sample Flow(lpm)': 'CPC Sample Flow / L/min',
                    'Low Voltage': 'Low Voltage / V', 'High Voltage': 'High Voltage / V',
                    'Lower Size(nm)': 'Lower Size / nm', 'Upper Size(nm)': 'Upper Size / nm',
                    'Density(g/cc)': u'Density / g/cm\u00B3', 'td(s)': 'td / s', 'tf(s)': 'tf / s',
                    'D50(nm)': 'D50 / nm', 'Median(nm)': 'Median / nm', 'Mean(nm)': 'Mean / nm',
                    'Geo. Mean(nm)': 'Geo. Mean / nm', 'Mode(nm)': 'Mode / nm',
                    'Total Conc.(#/cm3)': u'Total Conc. / 1/cm\u00B3'}
        df.rename(columns=mapping, inplace=True)
    else:
        pass

    return df


def def_used_smps(used_device):
    """define parameters that are different between the different smps systems, here already renamed values are used, as
    the following comparison of columns is done based upon general naming scheme of the whole script"""

    if used_device == device_list.query("Device=='SMPS 3938'")["Device_Identifier"].values[0]:
        # compare the used_device parameter taken from particle_analysis.get_data() to the values defined in
        # Def.device_list - done this way, so device_list can be changed easily without having to rewrite everything
        parameter_list = ['Sample #', 'Date', 'Start Time', 'Sample Temp / °C', 'Sample Pressure / kPa',
                            'Relative Humidity %', 'Mean Free Path / m', u'Gas Viscosity / Pa\u00B7s',
                            'Diameter Midpoint / nm', 'Scan Time / s', 'Retrace Time / s', 'Scan Resolution / Hz',
                            'Scans Per Sample', 'Sheath Flow / L/min', 'Aerosol Flow / L/min', 'Bypass Flow / L/min',
                            'Low Voltage / V', 'High Voltage / V', 'Lower Size / nm', 'Upper Size / nm',
                            u'Density / g/cm\u00B3', 'td + 0.5 / s', 'tf / s', 'D50 / nm', 'Neutralizer Status',
                            'Median / nm', 'Mean / nm', 'Geo. Mean / nm', 'Mode / nm', 'Geo. Std. Dev.',
                            u'Total Conc. / 1/cm\u00B3', 'Title', 'User Name', 'Sample ID', 'Instrument ID', 'Lab ID',
                            'Leak Test and Leakage Rate', 'Instrument Errors', 'Comment']
        header_pos = 25
        time_format = '%m/%d/%Y %H:%M:%S'

        # "Neutralizer Status " is not contained in every measurement file... additionally it has a space in the column

    elif used_device == device_list.query("Device=='SMPS 3071'")["Device_Identifier"].values[0]:
        parameter_list = ['Sample #', 'Date', 'Start Time', 'Sample Temp / °C', 'Sample Pressure / kPa',
                            'Relative Humidity %', 'Mean Free Path / m', u'Gas Viscosity / Pa\u00B7s',
                            'Diameter Midpoint / nm', 'Scan Time / s', 'Retrace Time / s', 'Down Scan First',
                            'Scans Per Sample', 'Impactor Type / cm', 'Sheath Flow / L/min', 'Aerosol Flow / L/min',
                            'CPC Inlet Flow / L/min', 'CPC Sample Flow / L/min', 'Low Voltage / V', 'High Voltage / V',
                            'Lower Size / nm', 'Upper Size / nm', u'Density / g/cm\u00B3', 'td / s', 'tf / s',
                            'D50 / nm', 'Median / nm', 'Mean / nm', 'Geo. Mean / nm', 'Mode / nm', 'Geo. Std. Dev.',
                            u'Total Conc. / 1/cm\u00B3', 'Title', 'Status Flag', 'Comment']
        header_pos = 17
        time_format = '%m/%d/%y %H:%M:%S'
    else:
        print(f"Device {used_device} is not a viable option")
        parameter_list = used_device
        header_pos = used_device
        time_format = used_device

    return parameter_list, header_pos, time_format


def import_data(filename, used_device):
    """import smps data from txt file with name filename to pd dataframe, also includes time, some settings and some
    statistical values calculated by the TSI program
    then extract the actual measuring data from the dataframe and give X, dX, Cn and time
    to work, the data has to be exported in rows"""

    # data file has variable number of data columns depending on measuring range set so conc data has to be constructed
    # from difference of all columns and the non conc columns = paramter_list

    parameter_list, header_pos, time_format = def_used_smps(used_device)

    data = pd.read_table(filename, sep='\t', header=header_pos, engine='python', encoding='iso-8859-1')
    # originally ansi which is superset of iso; smps file is in encoding = ansi which caused an import error off cm^3
    # due to wrong encoding setting changed to iso as ansi is windows only and iso also works on linux

    # data = data.reset_index(drop=True)  # resetting index, anecessary, when Sample # column is used as index col in
    # pd.read_table -> removed as Sample # is used to directly generate Scan Nr

    data = rename_columns(data, used_device)

    nr_scans = len(data)

    # added the following part to avoid the KeyError - key not found in files that do not contain some columns like
    # "Neutralizer Status"
    # seems to work also for other fields that are not contained in the data :D Only when new fields are in the
    # data, but not in the list above, they should be added to the list.

    for k in parameter_list:
        if k in data:
            pass
        else:
            data[k] = np.zeros((nr_scans,))
            data[k] = np.nan  # with np.empty, it somehow filled the newly created column with some values from another
            # existing column??

    add_info = data[(parameter_list[3:])]

    # converting Sample Pressure from kPa to mbar
    if used_device == device_list.query("Device=='SMPS 3938'")["Device_Identifier"].values[0]:
        sample_p_mbar = convert_kPa_to_mbar(data["Sample Pressure / kPa"].copy())

    Cn = data[data.columns.difference(parameter_list)].to_numpy()

    x_axis = data[data.columns.difference(parameter_list)].columns.values
    # extracts the midpoint diameter from the pd.dataframe header similar to how Cn was extracted
    x_axis = x_axis.astype(float)

    nr_bins = len(x_axis)

    # calculate upper bin boundary from midpoint diameters

    X = np.zeros(Cn.shape)
    Xl = np.zeros(Cn.shape)
    Xu = np.zeros(Cn.shape)

    # unfortunately, the methods for calculating the bin boundaries Xl and Xu based on the midpoint diameters contained
    # in the measurement file do not give a constant dlogX as I think TSI sets "nice" values for midpoint diameters with
    # only one decimal
    # I contacted TSI to ask how they construct their X-axis and why the given midpoints are not equaly spaced on a
    # log axis
    # below I implemented 3 methods for calculating Xu and Xl, the first two are based on the given midpoints, the last
    # is only based on the upper and lower size limits given in the measurement file and constructs a new x-axis with
    # newly calculated midpoint diameters with intervals of equal length on the logarithmic axis
    # each method should work by just uncommenting it and commenting the method not to be used

    for i in range(nr_scans):

        # Method 1: calculating xu and xl based on midpoint diameters:  # (gives x-axis with gaps between bins in lower
        # size range and  overlapping bins in higher size range and variable dlogX especially in lower size range)

        # for k in range(nr_bins-1):
        #     Xu[i, k] = (2*x_axis[k])/((x_axis[k]/x_axis[k+1])+1)
        # Xu[i, -1] = 2*x_axis[-1]-Xu[i, -2]
        # Xl[i] = 2*x_axis-Xu[i] # calculate lower boundary from midpoint diameters and upper boundary
        # for k in range(nr_bins):
        #     X[i, k] = x_axis[k]

        # Method 2: calculating xu and xl iteratively from given lower size limit and midpoint diameters: (gives closure
        # between size bins, but still has variable dlogX especially in lower size range)

        # Xl[i, 0] = add_info["Lower Size (nm)"][i]
        # Xu[i, -1] = add_info["Upper Size (nm)"][i]
        # for k in range(nr_bins-1):
        #     Xl[i, k+1] = 2*x_axis[k]-Xl[i, k]
        #     Xu[i, k] = Xl[i, k+1]
        # for k in range(nr_bins):
        #     X[i, k] = x_axis[k]

        # Method 3: constructing my own x-axis based on lower and upper limits given in measurement file
        # also the two less indented lines after this block for calculating X and assigning it to X are required
        const_dlogX = np.log10(add_info["Upper Size / nm"]/add_info["Lower Size / nm"])/nr_bins
        Xl[i, 0] = add_info["Lower Size / nm"][i]
        Xu[i, -1] = add_info["Upper Size / nm"][i]
        for k in range(1, nr_bins):
            Xl[i, k] = Xl[i, k-1]*10**(const_dlogX[i])
            Xu[i, k-1] = Xl[i, k]
    Xm=(Xl+Xu)/2  # new array for midpoint diameters that are evenly spaced on log axis
    X=Xm

    # end of the three methods rest works with all three of them

    # calculate bin width from upper and lower boundary
    dX = np.subtract(Xu, Xl)

    # calculate dlogX from upper and lower boundary
    dlogX = np.log10(Xu/Xl)

    Cn_dlogX = Cn/dlogX

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


def import_data_dict(used_device):
    filename = get_filename()
    X, dX, dlogX, Cn, Cn_dlogX, add_info = import_data(filename, used_device)
    # used_device = device_list.query("Import_Script=='TSI_SMPS3938_fileread'")["Device_Identifier"].values[0]
    data_dict = {"X": X, "dX": dX, "dlogX": dlogX, "Cn": Cn, "Cn_dlogX": Cn_dlogX, "filename": filename,
                 "used_device": used_device, "add_info": add_info}
    return data_dict


if __name__ == "__main__":

    SMPS_3071_id = device_list.query("Device=='SMPS 3071'")["Device_Identifier"].values[0]
    SMPS_3938_id = device_list.query("Device=='SMPS 3938'")["Device_Identifier"].values[0]
    print(f"{SMPS_3071_id} = SMPS 3071; {SMPS_3938_id} = SMPS 3938")
    used_device = int(input("Which instrument did you use? Enter as int."))

    # filename = get_filename()
    # X, dX, dlogX, Cn, Cn_dlogX, add_info = import_data(filename, used_device)
    # print(f"imported {filename}")


    data_dict = import_data_dict(used_device)
    print(f"imported {data_dict['filename']} as dictionary")
