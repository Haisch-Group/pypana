"""
conc.py

Script for Evaluation of Concentration Data
Run from particle_analysis.py

Created 2022-03-24
@written by Kevin Maier (kevin.r.maier@tum.de)
2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number
2024-03-20: integrated in particle_analysis.py
2024-06 to 2025-11 adapted to new data structure
"""

import datetime

import defs
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import sup
from matplotlib import pyplot as plt
from matplotlib import ticker

# import mpldatacursor  # not used atm


def select_data(data, scan_nrs, used_C="Cn"):
    """select specific CPC msmts from the imported raw data, scan_nrs defines, which measurements to take
    in normal non-pythonian logic (starting count at 1)"""
    py_nrs = sup.py_logic_converter(scan_nrs)
    sel_C = np.full((len(py_nrs), data[used_C].shape[1]), np.nan)
    # preallocate the np array in the correct size (nr of measurements, nr of measuring data)
    sel_el_time = np.full_like(sel_C, np.nan)

    for k in np.arange(len(py_nrs)):  # fill the arrays with the selected data
        sel_C[k, :] = data[used_C][py_nrs[k], :]
        sel_el_time[k, :] = data["el_time"][py_nrs[k], :]

    sel_add_info = pd.DataFrame(
        columns=list(data["add_info"].columns.values)
    )  # just copy column headers to new DF
    sel_add_info = pd.concat(
        [sel_add_info, data["add_info"].iloc[py_nrs]], ignore_index=True
    )  # fill the new dataframe
    sel_results = pd.DataFrame(
        columns=list(data["results"].columns.values)
    )  # with values from selected data lines
    sel_results = pd.concat(
        [sel_results, data["results"].iloc[py_nrs]], ignore_index=True
    )  # dropping NaN columns would need .dropna("all")

    sel_data = {
        used_C: sel_C,
        "el_time": sel_el_time,
        "filename": data["filename"],
        "used_device": data["used_device"],
        "add_info": sel_add_info,
        "results": sel_results,
    }
    return sel_data


def merge_data(sel_data_list, used_C="Cn", path="manual"):
    """merges dictionaries of data, should best be used with selected data dicts"""
    merged_data_C = []  # create lists to fill with list of 1D arrays
    merged_data_el_time = []  # done so complicated as arrays can have different length
    time_len_list = []
    origin = []
    n_scans = 0  # count measurements that are imported to the lists

    merged_add_info = pd.DataFrame(
        columns=list(sel_data_list[0]["add_info"].columns.values)
    )  # copy headers of add_info
    merged_results = pd.DataFrame(
        columns=list(sel_data_list[0]["results"].columns.values)
    )  # and results dfs

    for data in sel_data_list:  # append all imported lines to the lists
        for k in range(len(data["el_time"])):
            merged_data_C.append(data[used_C][k])
            merged_data_el_time.append(data["el_time"][k])
            time_len_list.append(len(data["el_time"][k]))
            origin.append(
                data["filename"]
            )  # note down filename for each imported dataset
            n_scans += 1

        merged_add_info = pd.concat(
            [merged_add_info, data["add_info"]], ignore_index=True
        )  # also concatenate add_info and results of
        merged_results = pd.concat(
            [merged_results, data["results"]], ignore_index=True
        )  # all merged datasets

    x_len = max(
        time_len_list
    )  # get maximum length of the x-axis elements -> longest x-axis is base for array
    merged_array_C = np.full((n_scans, x_len), np.nan)  # preallocate data arrays
    merged_array_el_time = np.full((n_scans, x_len), np.nan)

    for k in range(n_scans):  # fill arrays row wise with data from list elements
        merged_array_C[k, 0 : len(merged_data_C[k])] = merged_data_C[k]
        merged_array_el_time[k, 0 : len(merged_data_el_time[k])] = merged_data_el_time[
            k
        ]

    merged_data = {}  # prepare merged data dictionary

    merged_data[used_C] = merged_array_C  # fill merged data dictionary
    merged_data["el_time"] = merged_array_el_time
    merged_data["used_device"] = sel_data_list[0][
        "used_device"
    ]  # use info from first data set
    merged_data["filename"] = sup.add_path(path)
    merged_add_info.insert(loc=1, column="Origin", value=origin)
    merged_data["add_info"] = merged_add_info
    merged_data["results"] = merged_results

    return merged_data


def select_multiple_data(list_of_tuples, used_C="Cn", path="manual"):
    """select specific scans from the imported raw data to then process them, scan_nrs defines, which scans to take
    in normal non-pythonian logic (starting count at 1)
    can only easily select data from one day for comparison
    import as list of tuples: [(data_identifier_1, [scan_nrs_1]),(data_identifier_2, [scan_nrs_2]),...]"""
    sel_data_list = []
    for tuple in list_of_tuples:
        sel_data_list.append(select_data(tuple[0], tuple[1]))
    sel_merged_data = merge_data(sel_data_list, used_C=used_C, path=path)

    return sel_merged_data


def cut_time_data(C_row, el_time_row, start, end):
    """can be used to cut conc data time wise per row"""
    start_idx = np.where(el_time_row >= start)[0][0]
    end_idx = np.where(el_time_row <= end)[-1][-1] + 1
    cut_C = np.full_like(C_row, np.nan)
    cut_el_time = np.full_like(C_row, np.nan)
    cut_C[start_idx:end_idx] = C_row[start_idx:end_idx]
    cut_el_time[start_idx:end_idx] = (
        el_time_row[start_idx:end_idx] - el_time_row[start_idx]
    )
    return cut_C, cut_el_time


def cut_time(data, scan_nrs, start, end, used_C="Cn"):
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
        data[f"cut_{used_C}"][msmt], data["cut_el_time"][msmt] = cut_time_data(
            data[used_C][msmt], data["el_time"][msmt], start, end
        )
    return data


def calc_meanconc(C):
    """gives mean and std of a concentration array based on the key given as str
    call: mean_C, std_C = calc_meanconc(C)"""
    mean_C = np.nanmean(C, 1)
    std_C = np.nanstd(C, 1)
    return mean_C, std_C


def get_meanconc(data, used_C="Cn"):
    """gives mean and std of a concentration array based on the key given as str and writes them into data dictionary
    call: get_meanconc(data, "Cn")"""
    C = data[used_C]
    mean_C, std_C = calc_meanconc(C)
    data["results"]["mean_" + used_C] = mean_C
    data["results"]["std_" + used_C] = std_C
    return data


def typical_calculations(data, used_C="Cn"):
    get_meanconc(data, used_C)
    return data


def format_plot(fig, ax):
    cm = 1 / 2.54  # inches to cm
    fig.set_size_inches(16 * cm, 10 * cm)  # height with title 12, without 10
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.ticklabel_format(style="sci", scilimits=(0, 0), axis="y", useMathText=True)
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(
        top=0.95
    )  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    fig.tight_layout()
    return ax


def plot_singledata(
    data,
    scan_nrs,
    used_C="Cn",
    used_time="el_time",
    a=1,
    legend="automatic",
    legend_loc="upper right",
    save_plot="off",
    color_map=defs.default_cm,
):
    """plots scan data"""
    py_nr = sup.py_logic_converter(scan_nrs)
    C = data[used_C]
    el_time = data[
        used_time
    ]  # cut_el_time starts at 1, el_time at actual timepoint, so both can be used to get different plots
    # mean_C, std_C = calc_meanconc(data, used_C) # was only printed before, better displayed in results now

    fig, ax = plt.subplots()

    legend_entries = []

    ct = 0
    if len(py_nr) == 1:
        k = py_nr[0]
        ax.scatter(
            el_time[k, :], C[k, :], edgecolor="black", linewidth=0.5, color=color_map[0]
        )
        sup.build_legend(legend_entries, scan_nrs, ct, legend=legend)
    else:
        for k in py_nr:
            ax.scatter(
                el_time[k, :],
                C[k, :],
                edgecolor="black",
                linewidth=0.5,
                color=color_map[ct],
                alpha=a,
            )
            sup.build_legend(legend_entries, scan_nrs, ct, legend=legend)
            ct += 1

    ax = format_plot(fig, ax)

    ax.set(
        xlabel="Elapsed Time / s", ylabel="Particle Number Concentration / 1/cm\u00b3"
    )

    plt.legend(legend_entries, loc=legend_loc, frameon=False)

    sup.save_plot(data, save_plot)  # , fileaddition=scan_nr_fileaddition)

    plt.show()
    return ax


def plot_mean_timeline(
    data,
    start_time,
    end_time,
    used_C="mean_Cn",
    save_plot="off",
    color_map=defs.default_cm,
):
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
            time[k] += datetime.timedelta(
                seconds=data["el_time"][~np.isnan(data["cut_el_time"])][:][k]
            )
    else:
        pass

    start_idx = np.where(time >= start_time)[0][0]
    end_idx = np.where(time >= end_time)[-1][-1]

    fig, ax = plt.subplots()  # height with title 12, without 10
    ax.scatter(
        time[start_idx:end_idx],
        mean_C[start_idx:end_idx],
        edgecolor="black",
        linewidth=0.5,
        color=color_map[0],
    )
    ax.errorbar(
        time[start_idx:end_idx],
        mean_C[start_idx:end_idx],
        yerr=std_C[start_idx:end_idx],
        fmt="o",
    )

    ax = format_plot(fig, ax)

    ax.xaxis.set_tick_params(reset=True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set(
        xlabel="Time / HH:MM", ylabel="Mean Particle Number Concentration / 1/cm\u00b3"
    )

    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)

    # mpldatacursor.datacursor(ax)

    sup.save_plot(data, save_plot)

    plt.show()
    return ax


def plot_calc_conc_n(
    data, scan_nrs, used_C="calc_Cn", a=1, save_plot="off", color_map=defs.default_cm
):
    """function by Nico: this is a function for distribution derived concentrations"""

    py_nrs = sup.py_logic_converter(scan_nrs)
    calc_C = data["results"][used_C]
    fig, ax = plt.subplots()

    ct = 0
    if len(py_nrs) == 1:
        k = py_nrs[0]
        ax.scatter(
            scan_nrs[0],
            calc_C[k],
            edgecolor="black",
            linewidth=0.5,
            color=color_map[0],
            alpha=a,
        )
        # print(f"scan {k} conc. = " + "{:e}".format(float(calc_C[k])) + " P/cm" + u"\u00B3")
    else:
        for k in range(len(py_nrs)):
            ax.scatter(
                scan_nrs[k],
                calc_C[py_nrs[k]],
                edgecolor="black",
                linewidth=0.5,
                color=color_map[0],
                alpha=a,
            )
            # print(f"scan {k} conc. = " + "{:e}".format(float(calc_C[k])) + " P/cm" + u"\u00B3")
            ct += 1

    format_plot(fig, ax)
    ax.set(
        xlabel="Scan Nr.",
        ylabel="Calculated Particle Number Concentration / 1/cm\u00b3",
    )

    sup.save_plot(data, save_plot)  # , fileaddition=scan_nr_fileaddition)
    plt.show()
    return ax


if __name__ == "__main__":
    """"""
