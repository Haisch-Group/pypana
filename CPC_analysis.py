# -*- coding: utf-8 -*-
"""
Script for CPC Data Evaluation
Data has to be imported by the import function suitable for the used CPC

Created 2022-03-24
@written by Kevin Maier (kevin.r.maier@tum.de)
2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number
"""

from matplotlib import ticker
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from get_filename import get_filename
import pandas as pd
from py_logic_converter import py_logic_converter, normal_logic_converter
#import mpldatacursor


def fileread(filename, used_device):
    """just a very fast function for applying the correct import filter according to user choice"""

    if int(used_device) == 0:
        import TSI_CPC3775_fileread as fr
    else:
        import PALAS_UFCPC_fileread as fr

    Cn, el_time, start_time = fr.import_data(filename)
    return Cn, el_time, start_time


def get_data():
    filename = get_filename()
    used_device = input("Which instrument did you use, type 0 for TSI 3775, or 1 for PALAS CPC")
    Cn, el_time, start_time = fileread(filename, used_device)
    scan_nr = []
    [scan_nr.append(k + 1) for k in range(len(Cn))]
    data = {"Cn": Cn, "el_time": el_time,
            "start_time": start_time, "scan_nr": scan_nr, "filename": filename, "used_device": used_device}
    return data

# def select_data(Cn, msmt_nrs):
#     """select specific CPC msmts from the imported raw data, msmt_nrs defines, which measurements to take
#     in normal non-pythonian logic (starting count at 1)"""
#     sel_Cn = np.zeros((len(msmt_nrs), Cn.shape[1]))
#     # preallocate the sel_Cn array with shape = (n_msmts, n_timepoints)
#     for k in np.arange(len(msmt_nrs)):  # fill the arrays with the selected data
#         sel_Cn[k, :] = Cn[msmt_nrs[k]-1, :]
#
#    return sel_Cn


def cut_time(data, start, end):
    """can be used to cut conc array time wise"""
    data["cut_Cn"] = data["Cn"][:, start:end]
    data["cut_time"] = data["el_time"][start:end]
    return data


def get_meanconc(data):
    data["conc_n"] = np.nanmean(data["Cn"], 1)
    data["std_n"] = np.nanstd(data["Cn"], 1)
    return data


def plot_singledata(data, scan_nr):
    """plots complete data"""
    Cn, el_time, conc_n, std_n = data["Cn"], data["el_time"], data["conc_n"], data["std_n"]
    plot_nr = py_logic_converter(scan_nr)
    cm = 1/2.54  # inches to cm
    fig, ax = plt.subplots(figsize=(18.5*cm, 10*cm))  # height with title 12, without 10
    if len(plot_nr) == 1:
        k = plot_nr[0]
        ax.scatter(el_time, Cn[k, :], edgecolor='black')
    else:
        for k in plot_nr:
            ax.scatter(el_time, Cn[k, :], edgecolor='black')
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.set(xlabel='Elapsed Time / s',
           ylabel='Particle Number Concentration / $\mathregular{1/cm^3}$')
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    if len(plot_nr) == 1:
        k = plot_nr[0]
        legend_entries = [input(f"Please enter the legend entry for measurement {k+1}")]
        #print(f"measurement {k} conc. = " + "{:e}".format(float(conc_n[k])) + u"\u00B1" +
        #       "{:e}".format(float(std_n[k])) + " P/cm" + u"\u00B3")
    else:
        legend_entries = []
        for k in plot_nr:
            legend_entries.append(input(f"Please enter the legend entry for measurement {k+1}"))
    [print(f"measurement {k+1} conc. = " + "{:e}".format(float(conc_n[k])) + u"\u00B1" +
            "{:e}".format(float(std_n[k])) + " P/cm" + u"\u00B3") for k in plot_nr]
    #mpldatacursor.datacursor(ax)
    plt.legend(legend_entries)

    fileaddition = input("Please enter a fileaddition")
    path = data["filename"][:-4] + fileaddition + ".png"
    plt.savefig(path, transparent=True)

    #plt.show()
    return ax


def plot_timeline(conc_n, std_n, start_time, start, end):
    """plots concentration timeline with mean conc of chosen single CPC scans
    only works with more than 1 datapoints"""
    cm = 1/2.54  # inches to cm
    fig, ax = plt.subplots(figsize=(18.5*cm, 10*cm))  # height with title 12, without 10
    ax.scatter(start_time[start:end], conc_n[start:end], edgecolor='black')
    ax.errorbar(start_time[start:end], conc_n[start:end], yerr=std_n[start:end], fmt="o")
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.xaxis.set_tick_params(reset=True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set(xlabel='Time / HH:MM',
           ylabel='Mean Particle Number Concentration / $\mathregular{1/cm^3}$')
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    legend_entries = [input(f"Please enter the legend entry for the measurement")]
    [print(f"measurement {k} conc. = " + "{:e}".format(float(conc_n[k])) + u"\u00B1" +
           "{:e}".format(float(std_n[k])) + " P/cm" + u"\u00B3") for k in np.arange(start, end)]
    #mpldatacursor.datacursor(ax)
    plt.legend(legend_entries)

    plt.show()
    return ax


def save_calc_to_csv(data_dict, variable_list, fileaddition="_particleDF"):
    """saves selected variables to a csv file, select variables to save in variable_list as list of strings,
     allways use a different fileaddition when saving anything else than the data input array data_identifier"""
    path = data_dict["filename"][:-4]+fileaddition+".csv"
    dataframe = pd.DataFrame()
    for variable in variable_list:
        dataframe[variable] = data_dict[variable]
    print(f"wrote file with variables {variable_list} to csv with name {path}")
    dataframe.to_csv(path)
    return

# Maybe add D50 eval function?


if __name__ == "__main__":

    """"""
    # data_identifier = get_data()
    #conc_n, std_n = get_meanconc(Cn)
    #save_calc_to_csv(data_identifier, ["scan_nr", "start_time", "conc_n", "std_n"],
    #                 fileaddition="_particleDF")
    # measurement_nr = [0]#np.arange(0, 3)
    # ax = plot_singledata(Cn, el_time, conc_n, std_n, measurement_nr)
    # ax = plot_timeline(conc_n, std_n, start_time, start, end) # start end are measurement numbers in conc array

    # ax.legend(legend_entries, ncol=2,handleheight=2.4, labelspacing=0.05) if legend is too long
