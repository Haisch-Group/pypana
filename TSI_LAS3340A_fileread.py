# -*- coding: utf-8 -*-
"""
TSI_LAS3340A_fileread.py

Script for Data Import of the TSI LAS 3340A Data

Created 2023
@written by Nico Chrisam (nico.chrisam@tum.de)
@modified by Kevin Maier (kevin.r.maier@tum.de)
"""

import numpy as np
import pandas as pd
from datetime import datetime
from Sup import get_filename
from Sup import get_filenames
from Sup import convert_standard_to_volumetric_flow
from Def import device_list
from Def import TSI_standard_conditions


def rename_columns(df):
    """rename the columns, so they follow the same schematic for all devices"""
    mapping = {'Accum.': 'Accum. / s', 'Scatter': 'Scatter / V', 'Current': 'Current / V',
               'Sample': u'Aerosol Flow / scm\u00B3/min', 'Ref.': 'Ref. / V', 'Temp.': 'Temp. / V',
               'Sheath': u'Sheath Flow / scm\u00B3/min', 'Diff.': 'Diff. / V', 'Box': 'Box / K', 'Purge':
                   u'Purge / scm\u00B3/min', 'Pres.': 'Pressure / kPa', 'Aux.': 'Aux. / V',
               'Flow': u'Flow / scm\u00B3/min'}
    df.rename(columns=mapping, inplace=True)
    return df


def import_single_data(filename):
    data = pd.read_table(filename, sep='\t', header=0, engine='python')
    # import all data from a txt file with first line as header

    data = rename_columns(data)
    # rename data given in non concentration columns as stated in manual to naming scheme used in other imports

    parameter_list = ['Date', 'Time', 'Accum. / s', 'Scatter / V', 'Current / V',
                      u'Aerosol Flow / Aerosol Flow / scm\u00B3/min',
                      'Ref. / V', 'Temp. / V', u'Sheath Flow / scm\u00B3/min', 'Diff. / V', 'Box / K',
                      u'Purge / scm\u00B3/min', 'Pressure / kPa', 'Aux. / V', u'Flow / scm\u00B3/min']
    # parameters as given in the LASER AEROSOL SPECTROMETER MODEL 3340A Operation and service manual P/N 6012274
    # Revision C April 2019 Section B-10

    # Ref. is the laser reference voltage for monitoring relative laser power, should be between 1 and 2.8 V ideal
    # between 2.2 and 2.7 V

    usedcolumns = ['Accum. / s', 'Scatter / V', 'Current / V', u'Aerosol Flow / scm\u00B3/min',
                      'Ref. / V', 'Temp. / V', u'Sheath Flow / scm\u00B3/min', 'Box / K', 'Pressure / kPa', ]
    # columns actually used for building add_info, other columns are eather datetime, conc data, or not used in the
    # TSI 3340A according to the manual

    add_info = data.loc[1:, (usedcolumns)]

    # import concentration values from lines 15 to 114 from line 1 as line 0 after header is still header :D
    counts = data.iloc[1:, list(range(15, 114))].to_numpy()

    # building an x-axis spanning from lower bin boundary of lowest bin to upper boundary of highest bin
    Xl = data.columns.values[list(range(15, 114))].astype(float)
    # extracts the lower bin boundary from the pd.dataframe header
    Xu = data.iloc[0, list(range(15, 114))].to_numpy().astype(float)
    # extracts the upper bin boundary from pd.dataframe line 0 after header

    # calculation of bin widths delta_x, logarithmic bin widths dlog_X and midpoint diameter mid_x arrays
    delta_x = Xu - Xl  # boundary of same bin
    mid_x = (Xu + Xl)/2  # midpoint = arithmetic mean of upper and lower bin boundary
    dlog_x = np.log10(Xu/Xl)  # logarithmic bin width = log of upper- log of lower bin boundary

    corr_aerosol_flow = convert_standard_to_volumetric_flow(add_info[u'Aerosol Flow / scm\u00B3/min'].astype(float),
                                                            add_info['Box / K'].astype(float),
                                                            add_info['Pressure / kPa'].astype(float), \
                                                            TSI_standard_conditions['T / K'], \
                                                            TSI_standard_conditions['Pressure / kPa'], 'K')

    X = np.zeros(counts.shape)
    dX = np.zeros(counts.shape)
    dlogX = np.zeros(counts.shape)
    n_scans = len(counts)

    time = []
    subscan_nr = []
    Cn = counts.copy()
    n_scan_list = []

    for i in range(n_scans):
        X[i] = mid_x
        dX[i] = delta_x
        dlogX[i] = dlog_x
        time.append(datetime.strptime(data.loc[i+1, "Date"] + " " + data.loc[i+1, "Time"],
                                      '%m/%d/%Y %I:%M:%S.%f %p'))
        subscan_nr.append(i+1)
        Cn[i] = (Cn[i] * (60 / float(data.loc[i+1, "Accum. / s"]))) / corr_aerosol_flow[i+1]
        # raw counts are saved -> counts/accumulation_time*60s/min*acorrected flowrate in cm^3/min
        n_scan_list.append(n_scans)

    Cn_dlogX = Cn.copy()/dlogX

    add_info.insert(loc=add_info.columns.get_loc("Aerosol Flow / scm\u00B3/min") + 1,
                    column="Aerosol Flow / cm\u00B3/min", value=corr_aerosol_flow)
    add_info.insert(loc=0, column="Time", value=time)
    add_info.insert(loc=0, column="Nr Scans", value=n_scan_list)
    add_info.insert(loc=0, column="Subscan Nr", value=subscan_nr)

    return X, dX, dlogX, Cn, Cn_dlogX, add_info


def import_data(filenames):
    scan_nr = []
    counter = 1
    X, dX, dlogX, Cn, Cn_dlogX, add_info = import_single_data(filenames[0])
    [scan_nr.append(counter) for k in add_info["Subscan Nr"]]
    for filename in filenames[1:]:
        X_i, dX_i, dlogX_i, Cn_i, Cn_dlogX_i, add_info_i = import_single_data(filename)
        X = np.concatenate((X, X_i))
        dX = np.concatenate((dX, dX_i))
        dlogX = np.concatenate((dlogX, dlogX_i))
        Cn = np.concatenate((Cn, Cn_i))
        Cn_dlogX = np.concatenate((Cn_dlogX, Cn_dlogX_i))
        add_info = pd.concat([add_info, add_info_i], ignore_index=True)
        counter += 1
        [scan_nr.append(counter) for k in add_info_i["Subscan Nr"]]
    add_info.insert(loc=0, column="Scan Nr", value=scan_nr)
    return X, dX, dlogX, Cn, Cn_dlogX, add_info


def import_data_dict(used_device):
    filenames = get_filenames()
    X, dX, dlogX, Cn, Cn_dlogX, add_info = import_data(filenames)
    for k in range(len(filenames)):
        # used_device = device_list.query("Import_Script=='TSI_LAS3340A_fileread'")["Device_Identifier"].values[0]
        data_dict = {"X": X, "dX": dX, "dlogX": dlogX, "Cn": Cn, "Cn_dlogX": Cn_dlogX, "filename": filenames,
                 "used_device": used_device, "add_info": add_info}
    return data_dict


if __name__ == "__main__":

    # filename = get_filename()
    # X, dX, dlogX, Cn, Cn_dlogX, add_info = import_single_data(filename)
    # print(f"imported {filename}")

    # filenames = get_filenames()
    # X, dX, dlogX, Cn, Cn_dlogX, add_info = import_data(filenames)
    # print(f"imported {filenames}")

    data_dict = \
        import_data_dict(device_list.query("Import_Script=='TSI_LAS3340A_fileread'")["Device_Identifier"].values[0])
    print(f"imported {data_dict['filename']} as dictionary")
