# -*- coding: utf-8 -*-
"""
Conc.py

Script for Evaluation of Concentration Data
Run from Particle_analysis.py

Created 2022-03-24
@written by Kevin Maier (kevin.r.maier@tum.de)
2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number
2024-03-20: integrated in Particle_analysis.py
2024-06 to 2025-11 adapted to new data structure
"""

from matplotlib import ticker
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import datetime

import Def
import Sup
# import mpldatacursor  # not used atm


def select_data(data, scan_nrs):
    """select specific CPC msmts from the imported raw data, scan_nrs defines, which measurements to take
    in normal non-pythonian logic (starting count at 1)"""
    py_nrs = Sup.py_logic_converter(scan_nrs)
    sel_C = np.full((len(py_nrs), data["Cn"].shape[1]), np.nan)
    # preallocate the np array in the correct size (nr of measurements, nr of measuring data)
    sel_el_time = np.full_like(sel_C, np.nan)
    for k in np.arange(len(py_nrs)):  # fill the arrays with the selected data
        sel_C[k, :] = data["Cn"][py_nrs[k], :]
        sel_el_time[k, :] = data["el_time"][py_nrs[k], :]
    sel_add_info = pd.DataFrame(columns=list(data["add_info"].columns.values))  # just copy column headers to new DF
    sel_add_info = pd.concat([sel_add_info, data["add_info"].iloc[py_nrs]])  # fill the new dataframe
    sel_results = pd.DataFrame(columns=list(data["results"].columns.values))  # with values from selected data lines
    sel_results = pd.concat([sel_results, data["results"].iloc[py_nrs]])  # dropping NaN columns would need .dropna("all")
    sel_data = {"Cn": sel_C, "el_time": sel_el_time, "add_info": sel_add_info, "results": sel_results,
                "filename": data["filename"], "used_device": data["used_device"]}
    return sel_data


def merge_data(sel_data_list):
    """merges dictionaries of data, should best be used with selected data dicts"""
    merged_data_C = []  # create lists to fill with list of 1D arrays
    merged_data_el_time = []  # done so complicated as arrays can have different length
    time_len_list = []
    origin = []
    n_scans = 0  # count measurements that are imported to the lists

    merged_add_info = pd.DataFrame(columns=list(sel_data_list[0]["add_info"].columns.values))  # copy headers of add_info
    merged_results = pd.DataFrame(columns=list(sel_data_list[0]["results"].columns.values))  # and results dfs

    for data in sel_data_list:  # append all imported lines to the lists
        for k in range(len(data["Cn"])):
            merged_data_C.append(data["Cn"][k])
            merged_data_el_time.append(data["el_time"][k])
            n_scans += 1
            time_len_list.append(len(data["el_time"][k]))
        merged_add_info = pd.concat([merged_add_info, data["add_info"]]) # also concatenate add_info and results of
        merged_results = pd.concat([merged_results, data["results"]]) # all merged datasets
        origin.append(data["filename"]) # note down filename for each imported dataset

    x_len = max(time_len_list)  # get maximum length of the x-axis elements -> longest x-axis is base for array
    merged_array_C = np.full((n_scans, x_len), np.nan)  # preallocate data arrays
    merged_array_el_time = np.full((n_scans, x_len), np.nan)
    for k in range((n_scans)):  # fill arrays row wise with data from list elements
        merged_array_C[k, 0:len(merged_data_C[k])] = merged_data_C[k]
        merged_array_el_time[k, 0:len(merged_data_el_time[k])] = merged_data_el_time[k]

    merged_data = {} # prepare merged data dictionary

    merged_data["Cn"] = merged_array_C # fill merged data dictionary
    merged_data["el_time"] = merged_array_el_time
    merged_data["add_info"] = merged_add_info
    merged_data["results"] = merged_results
    merged_data["used_device"] = sel_data_list[0]["used_device"] # use info from first data set
    merged_data["filename"] = input("Please enter a Path this data should be associated with. - "
                                        "Used for naming figures")
    merged_data["origin"] = origin

    return merged_data


def select_multiple_data(list_of_tuples):
    """select specific scans from the imported raw data to then process them, scan_nrs defines, which scans to take
    in normal non-pythonian logic (starting count at 1)
    can only easily select data from one day for comparison
    import as list of tuples: [(data_identifier_1, [scan_nrs_1]),(data_identifier_2, [scan_nrs_2]),...]"""
    sel_data_list = []
    for tuple in list_of_tuples:
        sel_data_list.append(select_data(tuple[0], tuple[1]))
    sel_merged_data = merge_data(sel_data_list)

    return sel_merged_data


def cut_time_data(C_row, el_time_row, start, end):
    """can be used to cut conc data time wise per row"""
    start_idx = np.where(el_time_row >= start)[0][0]
    end_idx = np.where(el_time_row <= end)[-1][-1] + 1
    cut_C = np.full_like(C_row, np.nan)
    cut_el_time = np.full_like(C_row, np.nan)
    cut_C[start_idx:end_idx] = C_row[start_idx:end_idx]
    cut_el_time[start_idx:end_idx] = el_time_row[start_idx:end_idx]-el_time_row[start_idx-1]
    return cut_C, cut_el_time


def cut_time(data, start, end, scan_nrs, used_C="Cn"):
    py_nrs = Sup.py_logic_converter(scan_nrs)
    if "cut_el_time" in data:
        pass
    else:
        data["cut_el_time"] = np.full_like(data["el_time"], np.nan)
    if f"cut_{used_C}" in data:
        pass
    else:
        data[f"cut_{used_C}"] = np.full_like(data[used_C], np.nan)
    for msmt in py_nrs:
        data[f"cut_{used_C}"][msmt], data["cut_el_time"][msmt] = (
            cut_time_data(data[used_C][msmt], data["el_time"][msmt], start, end))
    return data


def calc_meanconc(C):
    """gives mean and std of a concentration array based on the key given as str
    call: mean_C, std_C = calc_meanconc(C) """
    mean_C = np.nanmean(C, 1)
    std_C = np.nanstd(C, 1)
    return mean_C, std_C


def get_meanconc(data, used_C="Cn"):
    """gives mean and std of a concentration array based on the key given as str and writes them into data dictionary
    call: get_meanconc(data, "Cn") """
    C = data[used_C]
    mean_C, std_C = calc_meanconc(C)
    data["results"]["mean_"+used_C] = mean_C
    data["results"]["std_"+used_C] = std_C
    return data


def typical_calculations(data):
    get_meanconc(data, "Cn")
    return data


def format_plot(fig, ax):
    cm = 1 / 2.54  # inches to cm
    fig.set_size_inches(16 * cm, 10 * cm) # height with title 12, without 10
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    fig.tight_layout()
    return ax


def plot_singledata(data, scan_nrs, used_C="Cn", used_time="el_time", colors=Def.tum_cm, a=1, legend="automatic",
                    save_plot="off"):
    """plots scan data"""
    py_nr = Sup.py_logic_converter(scan_nrs)
    C = data[used_C]
    el_time = data[used_time]  # cut_el_time starts at 1, el_time at actual timepoint, so both can be used to get different plots
    # mean_C, std_C = calc_meanconc(data, used_C) # was only printed before, better displayed in results now

    fig, ax = plt.subplots()

    legend_entries = []

    ct = 0
    if len(py_nr) == 1:
        k = py_nr[0]
        ax.scatter(el_time[k, :], C[k, :], edgecolor='black', color=colors[0])
        Sup.build_legend(legend_entries, scan_nrs, ct, legend=legend)
    else:
        for k in py_nr:
            ax.scatter(el_time[k, :], C[k, :], edgecolor='black', color=colors[ct], alpha=a)
            Sup.build_legend(legend_entries, scan_nrs, ct, legend=legend)
            ct+=1

    ax = format_plot(fig, ax)

    ax.set(xlabel='Elapsed Time / s',
           ylabel=u'Particle Number Concentration / 1/cm\u00B3')

    plt.legend(legend_entries)  # , loc='upper left')

    Sup.save_plot(data, save_plot)  # , fileaddition=scan_nr_fileaddition)

    plt.show()
    return ax


def plot_mean_timeline(data, start_time, end_time, used_C="mean_Cn", colors=Def.tum_cm, a=1, save_plot="off"):
    """plots concentration timeline with mean conc of chosen single CPC scans
    only works with more than 1 datapoints, enter time as datetime in format 'YYYY-MM-DD HH:MM:SS'"""
    # should use only samples of same length to make sense -> should be useable with cut_Cn and sel_Cn, but from cut_Cn
    # also mean has to be produced for that and a start time has to be calculated!
    mean_C = data["results"][used_C]
    std_C = data["results"][used_C.replace("mean", "std")]

    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)
    time = data["add_info"]["Time"].copy()
    time = time.to_numpy()

    if used_C == "cut_mean_Cn":
        for k in range(len(data["add_info"]["Time"])):
            time[k] += datetime.timedelta(seconds=data["el_time"][~np.isnan(data["cut_el_time"])][:][k])
    else:
        pass

    start_idx = np.where(time >= start_time)[0][0]
    end_idx = np.where(time >= end_time)[-1][-1]

    fig, ax = plt.subplots()  # height with title 12, without 10
    ax.scatter(time[start_idx:end_idx], mean_C[start_idx:end_idx], edgecolor='black', color=colors[0])
    ax.errorbar(time[start_idx:end_idx], mean_C[start_idx:end_idx], yerr=std_C[start_idx:end_idx], fmt="o")

    ax = format_plot(fig, ax)

    ax.xaxis.set_tick_params(reset=True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set(xlabel='Time / HH:MM',
           ylabel=u'Mean Particle Number Concentration / 1/cm\u00B3')

    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)

    # mpldatacursor.datacursor(ax)

    Sup.save_plot(data, save_plot)

    plt.show()
    return ax


def plot_calc_conc_n(data, scan_nrs, used_C="calc_conc_n", colors=Def.tum_cm, a=1, save_plot="off"):
    """ function by Nico: this is a function for distribution derived concentrations"""

    py_nrs = Sup.py_logic_converter(scan_nrs)
    calc_conc_n = data["results"][used_C]
    fig, ax = plt.subplots()

    ct=0
    if len(py_nrs) == 1:
        k = py_nrs[0]
        ax.scatter(scan_nrs[0], calc_conc_n[k], edgecolor="black", color=colors[0], alpha=a)
        # print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        for k in range(len(py_nrs)):
            ax.scatter(scan_nrs[k], calc_conc_n[py_nrs[k]], edgecolor="black", color=colors[0], alpha=a)
            # print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
            ct += 1

    format_plot(fig, ax)
    ax.set(xlabel='Scan Nr.',
           ylabel=u'Calculated Particle Number Concentration / 1/cm\u00B3')

    Sup.save_plot(data, save_plot)  # , fileaddition=scan_nr_fileaddition)
    plt.show()
    return ax


if __name__ == "__main__":

    """"""
