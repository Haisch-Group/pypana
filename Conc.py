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
from Sup import py_logic_converter, normal_logic_converter
# import mpldatacursor


def select_data(Cn, msmt_nrs):
    # !!! has to be changed to dictionary logic
    """select specific CPC msmts from the imported raw data, msmt_nrs defines, which measurements to take
    in normal non-pythonian logic (starting count at 1)"""
    sel_Cn = np.zeros((len(msmt_nrs), Cn.shape[1]))
    # preallocate the sel_Cn array with shape = (n_msmts, n_timepoints)
    for k in np.arange(len(msmt_nrs)):  # fill the arrays with the selected data
        sel_Cn[k, :] = Cn[msmt_nrs[k]-1, :]
    return sel_Cn


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
    data["mean_"+used_C] = mean_C
    data["std_"+used_C] = std_C
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
    plot_nr = py_logic_converter(scan_nr)
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
           ylabel='Mean Particle Number Concentration / $\mathregular{1/cm^3}$')
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
    plot_nrs = py_logic_converter(scan_nrs)
    x_axis = range(1, len(scan_nrs) + 1)
    calc_conc_n = data["calc_conc_n"]
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
           ylabel='Number Concentration / $\mathregular{1/cm^3}$')
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    return


if __name__ == "__main__":

    """"""
    # get_meanconc(data)
    # measurement_nr = [0]#np.arange(0, 3)
    # ax = plot_singledata(Cn, el_time, conc_n, std_n, measurement_nr)
    # ax = plot_timeline(conc_n, std_n, start_time, start, end) # start end are measurement numbers in conc array

    # ax.legend(legend_entries, ncol=2,handleheight=2.4, labelspacing=0.05) if legend is too long
