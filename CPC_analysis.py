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
#import mpldatacursor


def fileread():
    """just a very fast function for applying the correct import filter according to user choice"""
    used_cpc = input("Which CPC did you use, type 0 for old TSI, or 1 for new PALAS")
    #used_cpc = 0

    if int(used_cpc) == 0:
        import TSICPC_fileread as fr
    else:
        import PALASCPC_fileread as fr

    filename = fr.get_filename()
    Cn, el_time, start_time = fr.import_data(filename)
    return Cn, el_time, start_time


# def select_data(Cn, msmt_nrs):
#     """select specific CPC msmts from the imported raw data, msmt_nrs defines, which measurements to take
#     in normal non-pythonian logic (starting count at 1)"""
#     sel_Cn = np.zeros((len(msmt_nrs), Cn.shape[1]))
#     # preallocate the sel_Cn array with shape = (n_msmts, n_timepoints)
#     for k in np.arange(len(msmt_nrs)):  # fill the arrays with the selected data
#         sel_Cn[k, :] = Cn[msmt_nrs[k]-1, :]
#
#     return sel_Cn

def get_meanconc(Cn):
    conc_n = np.nanmean(Cn, 1)
    std_n = np.nanstd(Cn, 1)
    return conc_n, std_n


def plot_singledata(Cn, el_time, conc_n, std_n, scan_nr):
    """plots complete data"""
    cm = 1/2.54  # inches to cm
    fig, ax = plt.subplots(figsize=(18.5*cm, 10*cm))  # height with title 12, without 10
    if len(scan_nr) == 1:
        k = scan_nr[0]
        ax.scatter(el_time, Cn[k, :], edgecolor='black')
    else:
        for k in scan_nr:
            ax.scatter(el_time, Cn[k, :], edgecolor='black')
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.set(xlabel='Elapsed Time / s',
           ylabel='Particle Number Concentration / $\mathregular{1/cm^3}$')
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    if len(scan_nr) == 1:
        k = scan_nr[0]
        legend_entries = [input(f"Please enter the legend entry for measurement {k}")]
        #print(f"measurement {k} conc. = " + "{:e}".format(float(conc_n[k])) + u"\u00B1" +
        #       "{:e}".format(float(std_n[k])) + " P/cm" + u"\u00B3")
    else:
        legend_entries = []
        for k in scan_nr:
            legend_entries.append(input(f"Please enter the legend entry for measurement {k}"))
    [print(f"measurement {k} conc. = " + "{:e}".format(float(conc_n[k])) + u"\u00B1" +
            "{:e}".format(float(std_n[k])) + " P/cm" + u"\u00B3") for k in scan_nr]
    #mpldatacursor.datacursor(ax)
    plt.legend(legend_entries)

    plt.show()
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


if __name__ == "__main__":

    Cn, el_time, start_time = fileread()
    conc_n, std_n = get_meanconc(Cn)
    # measurement_nr = [0]#np.arange(0, 3)
    # ax = plot_singledata(Cn, el_time, conc_n, std_n, measurement_nr)
    # ax = plot_timeline(conc_n, std_n, start_time, start, end) # start end are measurement numbers in conc array

    # ax.legend(legend_entries, ncol=2,handleheight=2.4, labelspacing=0.05) if legend is too long

    """utf-8 error is mostly due to the cm^-3 column -> replace 0xb3 by cm3"""
