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
"""

from matplotlib import ticker
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import Sup
# import mpldatacursor


def select_data(data, sel_nrs):
    """select specific CPC msmts from the imported raw data, msmt_nrs defines, which measurements to take
    in normal non-pythonian logic (starting count at 1)"""
    scan_nrs = Sup.py_logic_converter(sel_nrs)
    sel_Cn = np.zeros((len(scan_nrs), data["Cn"].shape[1]))
    # preallocate the np arrays in the correct size (nr of measurements, nr of measuring data)
    sel_el_time = np.zeros_like(sel_Cn)  # maybe nan is needed to avoid zeros on the right of the x-data?
    sel_time = []
    sel_scan_nr = []
    sel_filename = []
    # different datasets
    sel_used_device = []
    for k in np.arange(len(scan_nrs)):  # fill the arrays with the selected data
        sel_Cn[k, :] = data["Cn"][scan_nrs[k], :]
        sel_el_time[k, :] = data["el_time"][scan_nrs[k], :]
        sel_time.append(data["add_info"]["Time"][scan_nrs[k]])
        sel_scan_nr.append(data["add_info"]["Scan Nr"][scan_nrs[k]])
        sel_filename.append(data["filename"])
        sel_used_device.append(data["used_device"])
    sel_data = {"Cn": sel_Cn, "el_time": sel_el_time, "time": sel_time, "scan_nr": sel_scan_nr,
                "filename": sel_filename, "used_device": sel_used_device}
    return sel_data


def merge_data(sel_data_list):
    """merges dictionaries of data, should best be used with selected data dicts"""
    merged_data_Cn = []  # create lists to fill with list of 1D arrays
    merged_data_el_time = []
    time_len_list = []
    n_scans = 0  # count measurements that are imported to the lists
    for i in sel_data_list:  # append all imported lines to the lists
        for k in range(len(i["scan_nr"])):
            merged_data_Cn.append(i["Cn"][k])
            merged_data_el_time.append(i["el_time"][k])
            n_scans += 1
            time_len_list.append(len(i["el_time"][k]))
    x_len = max(time_len_list)  # get maximum length of the x-axis elements -> longest x-axis is base for array
    merged_array_Cn = np.zeros((n_scans, x_len))
    merged_array_el_time = np.zeros((n_scans, x_len))
    merged_array_Cn[:] = np.nan
    merged_array_el_time[:] = np.nan
    for k in range((n_scans)):  # fill arrays row wise with data from list elements
        merged_array_Cn[k, 0:len(merged_data_Cn[k])] = merged_data_Cn[k]
        merged_array_el_time[k, 0:len(merged_data_el_time[k])] = merged_data_el_time[k]
    merged_data = {}
    merged_data["Cn"] = merged_array_Cn
    merged_data["el_time"] = merged_array_el_time
    merged_data["time"] = sel_data_list[0]["time"][:]
    merged_data["scan_nr"] = sel_data_list[0]["scan_nr"][:]
    merged_data["origin"] = []
    [merged_data["origin"].append(sel_data_list[0]["filename"]) for k in range(len(sel_data_list[0]["scan_nr"]))]
    for i in sel_data_list[1:]:
        for k in range(len(i["scan_nr"])):
            merged_data["time"].append(i["time"][k])
            merged_data["scan_nr"].append(i["scan_nr"][k])
            merged_data["origin"].append(i["filename"])
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
    sel_merged_data["filename"] = input("Please enter a Path this data should be associated with. - "
                                        "Used for naming figures")
    return sel_merged_data


def calc_meanconc(data, used_C="Cn"):
    """gives mean and std of a concentration array based on the key given as str
    call: mean_C, std_C = calc_meanconc(data, "Cn") """
    mean_C = np.nanmean(data[used_C], 1)
    std_C = np.nanstd(data[used_C], 1)
    return mean_C, std_C


def get_meanconc(data, used_C="Cn"):
    """gives mean and std of a concentration array based on the key given as str and writes them into data dictionary
    call: get_meanconc(data, "Cn") """
    mean_C, std_C = calc_meanconc(data, used_C)
    data["results"]["mean_"+used_C] = mean_C
    data["results"]["std_"+used_C] = std_C
    return data


def typical_calculations(data):
    get_meanconc(data, "Cn")
    return data


def cut_time(data, start, end):
    """can be used to cut conc array time wise"""
    data["cut_Cn"] = data["Cn"][:, start:end]
    data["cut_time"] = data["el_time"][:, start:end]
    return data


def plot_singledata(data, scan_nr, used_C="Cn"):
    """plots scan data"""
    C = data[used_C]
    if used_C == "cut_Cn":
        el_time = data["cut_time"]
    else:
        el_time = data["el_time"]
    mean_C, std_C = calc_meanconc(data, used_C)
    filename = data["filename"]
    plot_nr = Sup.py_logic_converter(scan_nr)
    cm = 1/2.54  # inches to cm
    fig, ax = plt.subplots(figsize=(18.5*cm, 10*cm))  # height with title 12, without 10
    if len(plot_nr) == 1:
        k = plot_nr[0]
        ax.scatter(el_time[k, :], C[k, :], edgecolor='black')
    else:
        for k in plot_nr:
            ax.scatter(el_time[k, :], C[k, :], edgecolor='black')
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.set(xlabel='Elapsed Time / s',
           ylabel=u'Particle Number Concentration / 1/cm\u00B3')
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
    [print(f"measurement {k+1} conc. = " + "{:e}".format(float(mean_C[k])) + u"\u00B1" +
            "{:e}".format(float(std_C[k])) + " P/cm" + u"\u00B3") for k in plot_nr]
    #mpldatacursor.datacursor(ax)
    plt.legend(legend_entries)

    fileaddition = input("Please enter a fileaddition")
    path = filename[:-4] + "_" + fileaddition + ".png"
    plt.savefig(path, transparent=True)

    plt.show()
    return ax


def plot_timeline(mean_Cn, std_Cn, start_time, start, end):
    """plots concentration timeline with mean conc of chosen single CPC scans
    only works with more than 1 datapoints"""
    cm = 1/2.54  # inches to cm
    fig, ax = plt.subplots(figsize=(18.5*cm, 10*cm))  # height with title 12, without 10
    ax.scatter(start_time[start:end], mean_Cn[start:end], edgecolor='black')
    ax.errorbar(start_time[start:end], mean_Cn[start:end], yerr=std_Cn[start:end], fmt="o")
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.xaxis.set_tick_params(reset=True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set(xlabel='Time / HH:MM',
           ylabel=u'Mean Particle Number Concentration / 1/cm\u00B3')
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    legend_entries = [input(f"Please enter the legend entry for the measurement")]
    [print(f"measurement {k} conc. = " + "{:e}".format(float(mean_Cn[k])) + u"\u00B1" +
           "{:e}".format(float(std_Cn[k])) + " P/cm" + u"\u00B3") for k in np.arange(start, end)]
    #mpldatacursor.datacursor(ax)
    plt.legend(legend_entries)

    plt.show()
    return ax

# Maybe add D50 eval function?


def plot_calc_conc_n(data, scan_nrs):
    """ function by Nico"""
    # this is a function for distribution derived concentrations! -> maybe it is misplaced here?
    plot_nrs = Sup.py_logic_converter(scan_nrs)
    x_axis = range(1, len(scan_nrs) + 1)
    calc_conc_n = data["results"]["calc_conc_n"]
    fig, ax = plt.subplots()
    if len(plot_nrs) == 1:
        k = plot_nrs[0]
        ax.scatter(x_axis[k], calc_conc_n[k], edgecolor="black")
        print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        for k in range(len(plot_nrs)):
            ax.scatter(x_axis[k], calc_conc_n[plot_nrs[k]], edgecolor="black")
            print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    format_conc_plot(fig, ax, scan_nrs)
    plt.show()
    return ax


def format_conc_plot(fig, ax, scan_nrs):
    cm = 1 / 2.54  # inches to cm
    fig.set_size_inches(18.5 * cm, 10 * cm)
    xtick_entries = []
    for k in scan_nrs:
        xtick_entries.append(input(f"Please enter the xtick entries for measurement {k}"))
    ax.set(xticks=range(1, len(scan_nrs)+1), xticklabels=xtick_entries,
           ylabel=u'Number Concentration / 1/cm\u00B3')
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    return


if __name__ == "__main__":

    """"""
    # get_meanconc(data)
    # measurement_nr = [0]#np.arange(0, 3)
    # ax = plot_singledata(Cn, el_time, conc_n, std_n, measurement_nr)
    # ax = plot_timeline(conc_n, std_n, start_time, start, end) # start end are measurement numbers in conc array

    # ax.legend(legend_entries, ncol=2,handleheight=2.4, labelspacing=0.05) if legend is too long
