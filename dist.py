"""
dist.py

Script for Evaluation of Particle Size Distributions
Run from particle_analysis.py

Created 2024-03-20 by moving functions from particle_analysis.py
@written by Kevin Maier (kevin.r.maier@tum.de)
2024-06 to 2025-11 adjusted to work with new data structure
"""

import math

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import ticker
from scipy import optimize
from scipy.signal import find_peaks

import defs
import dist
import sup


def select_data(data, scan_nrs, used_C="Cn"):
    """select specific scans from the imported raw data to then process them, scan_nrs defines, which scans to take
    in normal non-pythonian logic (starting count at 1)
    can only easily select data from one day for comparison"""
    py_nrs = sup.py_logic_converter(scan_nrs)
    sel_C = np.full((len(py_nrs), data[used_C].shape[1]), np.nan)
    # preallocate the np arrays in the correct size (nr of measurements, nr of measuring data)
    sel_X = np.full_like(
        sel_C, np.nan
    )  # nan is needed to avoid zeros in case of varying scan range
    sel_dX = np.full_like(sel_C, np.nan)
    sel_dlogX = np.full_like(sel_C, np.nan)
    sel_C_dlogX = np.full_like(sel_C, np.nan)

    for k in np.arange(len(py_nrs)):  # fill the arrays with the selected data
        sel_C[k, :] = data[used_C][py_nrs[k], :]
        sel_X[k, :] = data["X"][py_nrs[k], :]
        sel_dX[k, :] = data["dX"][py_nrs[k], :]
        sel_dlogX[k, :] = data["dlogX"][py_nrs[k], :]
        sel_C_dlogX[k, :] = data[f"{used_C}_dlogX"][py_nrs[k], :]
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
    )
    # dropping NaN columns would need .dropna("all")

    sel_data = {
        "X": sel_X,
        "dX": sel_dX,
        "dlogX": sel_dlogX,
        used_C: sel_C,
        f"{used_C}_dlogX": sel_C_dlogX,
        "filename": data["filename"],
        "used_device": data["used_device"],
        "add_info": sel_add_info,
        "results": sel_results,
    }
    return sel_data


def convert_C_to_C_dlogX(data, used_C="Cn"):
    data[f"{used_C}_dlogX"] = data[used_C].copy() / data["dlogX"]
    return data


def convert_C_dlogX_to_C(data, used_C="Cn_dlogX"):
    data[used_C.strip("_dlogX")] = data[f"{used_C}"].copy() * data["dlogX"]
    return data


def get_conc(C):
    """calculate the total concentration for each selected measurement, can be applied to Cn, Cv, or Cm
    call for example as data["results"]["calc_conc"] = get_conc(data["Cn"]) to specify (or Cv, or Cm)
    run on entire C array"""
    calc_conc = np.zeros(
        C.shape[0],
    )  # preallocate the array again
    for k in range(
        C.shape[0]
    ):  # iteratively fill the array with the sum of all size concentrations
        calc_conc[k,] = np.nansum(C[k, :])  # np.nansum counts NaN as 0
    return calc_conc


def cut_dist_data(
    X_row, dX_row, dlogX_row, C_row, C_dlogX_row, lowerbound, upperbound
):  # merge with select_data
    """to cut a part of the spectrum - this formerly created an array smaller than the original array
    -> changed to now produce an array of same size for easier handling afterwards be just changing all values outside
    of cut area to np.nan"""
    start_idx = np.where(X_row >= lowerbound)[0][0]
    end_idx = np.where(X_row <= upperbound)[-1][-1] + 1
    cut_X_row = np.full_like(
        X_row, np.nan
    )  # actually this would not be needed, just the C-array as nans should be enough
    cut_dX_row = np.full_like(dX_row, np.nan)
    cut_dlogX_row = np.full_like(dlogX_row, np.nan)
    cut_C_row = np.full_like(C_row, np.nan)
    cut_C_dlogX_row = np.full_like(C_dlogX_row, np.nan)
    cut_X_row[start_idx:end_idx] = X_row[start_idx:end_idx]
    cut_dX_row[start_idx:end_idx] = dX_row[start_idx:end_idx]
    cut_dlogX_row[start_idx:end_idx] = dlogX_row[start_idx:end_idx]
    cut_C_row[start_idx:end_idx] = C_row[start_idx:end_idx]
    cut_C_dlogX_row[start_idx:end_idx] = C_dlogX_row[start_idx:end_idx]
    cut_conc_row = np.nansum(cut_C_row)
    return (
        cut_X_row,
        cut_dX_row,
        cut_dlogX_row,
        cut_C_row,
        cut_C_dlogX_row,
        cut_conc_row,
    )


def cut_dist(data, scan_nrs, lowerbound, upperbound, used_C="Cn"):
    X, dX, C = sup.extract_from_dict(data, used_C)
    dlogX = data["dlogX"]
    C_dlogX = data[f"{used_C}_dlogX"]
    py_nrs = sup.py_logic_converter(scan_nrs)
    if "cut_X" in data:
        pass
    else:
        data["cut_X"] = np.full_like(data["X"], np.nan)
        data["cut_dX"] = np.full_like(data["X"], np.nan)
        data["cut_dlogX"] = np.full_like(data["X"], np.nan)
    if f"cut_{used_C}" in data:
        pass
    else:
        data[f"cut_{used_C}"] = np.full_like(data[used_C], np.nan)
        data[f"cut_{used_C}_dlogX"] = np.full_like(data[used_C], np.nan)
    for k in py_nrs:
        (
            cut_X_row,
            cut_dX_row,
            cut_dlogX_row,
            cut_C_row,
            cut_C_dlogX_row,
            cut_conc_row,
        ) = cut_dist_data(
            X[k], dX[k], dlogX[k], C[k], C_dlogX[k], lowerbound, upperbound
        )
        data["cut_X"][k] = cut_X_row
        data["cut_dX"][k] = cut_dX_row
        data["cut_dlogX"][k] = cut_dlogX_row
        data[f"cut_{used_C}"][k] = cut_C_row
        data[f"cut_{used_C}_dlogX"][k] = cut_C_dlogX_row
        data["results"].loc[k, f"cut_conc_{used_C}"] = (
            cut_conc_row  # dropped a SettingWithCopyWarning so using .loc now
        )
    return data


def merge_data(sel_data_list, used_C="Cn", path="manual"):
    """merges dictionaries of data, should best be used with selected data dicts"""
    merged_data_X = []  # create lists to fill with list of 1D arrays
    merged_data_dX = []
    merged_data_dlogX = []
    merged_data_C = []
    merged_data_C_dlogX = []
    x_len_list = []
    origin = []
    n_scans = 0  # count measurements that are imported to the lists

    merged_add_info = pd.DataFrame(
        columns=list(sel_data_list[0]["add_info"].columns.values)
    )  # copy headers of add_info
    merged_results = pd.DataFrame(
        columns=list(sel_data_list[0]["results"].columns.values)
    )  # and results dfs

    for data in sel_data_list:  # append all imported lines to the lists
        for k in range(len(data["X"])):
            merged_data_X.append(data["X"][k])
            merged_data_dX.append(data["dX"][k])
            merged_data_dlogX.append(data["dlogX"][k])
            merged_data_C.append(data[used_C][k])
            merged_data_C_dlogX.append(data[f"{used_C}_dlogX"][k])
            x_len_list.append(len(data["X"][k]))
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
        x_len_list
    )  # get maximum length of the x_axis elements -> longest x-axis is base for array
    merged_array_X = np.full(
        (n_scans, x_len), np.nan
    )  # preallocate arrays for X, C, dX, ...
    merged_array_dX = np.full((n_scans, x_len), np.nan)
    merged_array_dlogX = np.full((n_scans, x_len), np.nan)
    merged_array_C = np.full((n_scans, x_len), np.nan)
    merged_array_C_dlogX = np.full((n_scans, x_len), np.nan)

    for k in range(n_scans):  # fill arrays row wise with data from list elements
        merged_array_X[k, 0 : len(merged_data_X[k])] = merged_data_X[k]
        merged_array_dX[k, 0 : len(merged_data_dX[k])] = merged_data_dX[k]
        merged_array_dlogX[k, 0 : len(merged_data_dlogX[k])] = merged_data_dlogX[k]
        merged_array_C[k, 0 : len(merged_data_C[k])] = merged_data_C[k]
        merged_array_C_dlogX[k, 0 : len(merged_data_C_dlogX[k])] = merged_data_C_dlogX[
            k
        ]

    merged_data = {}
    merged_data["X"] = merged_array_X
    merged_data["dX"] = merged_array_dX
    merged_data["dlogX"] = merged_array_dlogX
    merged_data[used_C] = merged_array_C
    merged_data[f"{used_C}_dlogX"] = merged_array_C_dlogX
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


def geometric_mean(X_row, C_row, conc_row):
    """calculates the geometric mean from given X_row, C_row and concentration
    Adapted from Eq. 22-12 in Aerosol Measurement p. 485, Ed. P. Kulkarni, P.A. Baron, K. Willeke 2011
    for lognormal distributions, count median diameter = geometric mean diameter - maybe add a check for lognormality ?"""
    if (
        conc_row == 0
    ):  # if the concentration of the array is 0, no distribution can be determined
        dg = 0  # so, 0 is reported as geometric mean diameter
    else:
        dg = math.pow(10, (np.nansum(np.log10(X_row) * C_row)) / conc_row)
        # dg = math.exp((1 / conc_row) * np.nansum(np.log(X_row)*C_row)) # using e as base
        # both methods give the same result only varying by 10**-14 in some cases so negligible
        # log10 is used, as data is also on log10 base
    return dg


def get_geometric_mean(X, C, conc):
    """calculates the geometric mean from given X, C and conc arrays by applying geometric mean function to array"""
    dg = []
    for k in np.arange(0, C.shape[0]):
        dg.append(geometric_mean(X[k], C[k], conc[k]))
    return dg


def geometric_std(X_row, C_row, conc_row, dg_row):
    """calculates the geometric standard deviation from given X, C, conc and dg can be used with different C
    Adapted from Eq. 22-12 in Aerosol Measurement p. 485, Ed. P. Kulkarni, P.A. Baron, K. Willeke 2011"""
    # gave a math error for conc < 1 because conc-1 in GSD is < 0 then, so division is not possible
    if conc_row < 1.00001:
        GSD = np.inf  # is infinity correct here? should it just be a massive value? if after that a std is
        # calculated for example when using mean_of_n, the std of GSD is nan of course
    else:
        GSD = math.pow(
            10,
            (
                math.sqrt(
                    (np.nansum(np.square(np.log10(X_row / dg_row)) * C_row))
                    / (conc_row - 1)
                )
            ),
        )
        # GSD = math.exp(math.sqrt((np.nansum(np.square(np.log(X[k])
        #                                                       - np.log(dg[k]))*C[k]))/(conc[k]-1))))
        # changed to log10 as it is used everywhere else on 20250128 same result as above
    return GSD


def get_geometric_std(X, C, conc, dg):
    """calculates the geometric standard deviation from given X, C, conc and dg arrays, can be used with different C
    Adapted from Eq. 22-12 in Aerosol Measurement p. 485, Ed. P. Kulkarni, P.A. Baron, K. Willeke 2011"""
    GSD = []
    for k in range(0, len(conc)):
        GSD.append(geometric_std(X[k], C[k], conc[k], dg[k]))
    return GSD


def count_median_diameter(X_row, C_row, conc_row):
    """calculates count median diameter for one measurement"""
    norm_C = np.divide(C_row, conc_row)
    return np.nanprod(np.power(X_row, norm_C))


def get_count_median_diameter(X, C):
    """does not work atm as all values are float and that only works until 10**308 which is reached with the first
    power operation"""
    CMD = []
    for k in np.arange(0, C.shape[0]):
        conc = np.nansum(C[k])
        if conc == 0:
            CMD.append(0)
        else:
            CMD.append(count_median_diameter(X[k], C[k], conc))
    return CMD


def Hatch_Choate(CMD_row, GSD_row):
    """calculates mode, length median (LMD), surface median (SMD), mass median (MMD) and mass mean diameter
    from dg and GSD or CMD and GSD
     Adapted from Eqs. equation given in Aerosol Measurement p.43 - usually calculated"""
    mode = CMD_row * math.pow(10, (-1 * np.log10(GSD_row) ** 2))
    LMD = CMD_row * math.pow(10, (1 * np.log10(GSD_row) ** 2))
    SMD = CMD_row * math.pow(10, (2 * np.log10(GSD_row) ** 2))
    MMD = CMD_row * math.pow(10, (3 * np.log10(GSD_row) ** 2))
    mass_mean_D = CMD_row * math.pow(10, (3.5 * np.log10(GSD_row) ** 2))
    return mode, LMD, SMD, MMD, mass_mean_D


def get_Hatch_Choate(CMD, GSD):
    """calculates mode, length median (LMD), surface median (SMD), mass median (MMD) and mass mean diameter
    from dg and GSD or CMD and GSD
     Adapted from Eqs. equation given in Aerosol Measurement p.43 - usually calculated"""
    mode = []
    LMD = []
    SMD = []
    MMD = []
    mass_mean_D = []
    for k in range(len(CMD)):
        if CMD[k] == 0:
            mode.append(0)
            LMD.append(0)
            SMD.append(0)
            MMD.append(0)
            mass_mean_D.append(0)
        else:
            mode_row, LMD_row, SMD_row, MMD_row, mass_mean_D_row = Hatch_Choate(
                CMD[k], GSD[k]
            )
            mode.append(mode_row)
            LMD.append(LMD_row)
            SMD.append(SMD_row)
            MMD.append(MMD_row)
            mass_mean_D.append(mass_mean_D_row)
    return mode, LMD, SMD, MMD, mass_mean_D


def calc_geometry(X, C, conc):
    """calculates geometric parameters of the distributions"""
    dg = get_geometric_mean(X, C, conc)
    GSD = get_geometric_std(X, C, conc, dg)
    return dg, GSD


def cumulative_distribution(C):
    """calculates the cumulative distribution for the entire array"""
    # tested, first column = Cn[0], last column = calc_conc_n
    cum_C = np.full_like(C, np.nan)
    for scan in range(len(C)):
        cum_C[scan, 0] = C[scan, 0]
        for k in range(1, len(C[scan])):
            cum_C[scan, k] = cum_C[scan, k - 1] + C[scan, k]
    return cum_C


def cumulative_diameters(X, cum_C):
    """calculates the diameters below which 10, 16, 50, 84 and 90 % of all particles are"""
    # seemingly works, at least X50 were similar to PDAnalyze X50 values, but slightly different, as i just give the
    # middle X value of the bin, maybe PALAS does some other magic with it like calculating a discrete distribution
    X10 = []
    X16 = []
    X50 = []
    X84 = []
    X90 = []
    for k in range(len(cum_C)):
        X10.append(
            X[k][
                next(
                    (
                        index
                        for index, val in enumerate(cum_C[k])
                        if val > cum_C[k][-1] * 0.1
                    ),
                    0,
                )
            ]
        )
        X16.append(
            X[k][
                next(
                    (
                        index
                        for index, val in enumerate(cum_C[k])
                        if val > cum_C[k][-1] * 0.16
                    ),
                    0,
                )
            ]
        )
        X50.append(
            X[k][
                next(
                    (
                        index
                        for index, val in enumerate(cum_C[k])
                        if val > cum_C[k][-1] * 0.5
                    ),
                    0,
                )
            ]
        )
        X84.append(
            X[k][
                next(
                    (
                        index
                        for index, val in enumerate(cum_C[k])
                        if val > cum_C[k][-1] * 0.84
                    ),
                    0,
                )
            ]
        )
        X90.append(
            X[k][
                next(
                    (
                        index
                        for index, val in enumerate(cum_C[k])
                        if val > cum_C[k][-1] * 0.9
                    ),
                    0,
                )
            ]
        )
    # cumDiameters = pd.DataFrame({"X10": X10, "X16": X16, "X50": X50, "X84": X84, "X90": X90})
    return X10, X16, X50, X84, X90  # cumDiameters


def typical_calculations(data, used_C="Cn"):
    data["results"][f"calc_conc_{used_C}"] = get_conc(data[used_C])
    data["results"][f"dg_{used_C}"], data["results"][f"GSD_{used_C}"] = calc_geometry(
        data["X"], data[used_C], data["results"][f"calc_conc_{used_C}"]
    )
    data["results"][f"CMD_{used_C}"] = get_count_median_diameter(
        data["X"], data[used_C]
    )
    (
        data["results"][f"mode_{used_C}"],
        data["results"][f"LMD_{used_C}"],
        data["results"][f"SMD_{used_C}"],
        data["results"][f"MMD_{used_C}"],
        data["results"][f"mass_mean_D_{used_C}"],
    ) = get_Hatch_Choate(
        data["results"][f"CMD_{used_C}"], data["results"][f"GSD_{used_C}"]
    )
    data[f"cum_{used_C}"] = cumulative_distribution(data[used_C])
    data[f"norm_cum_{used_C}"] = sup.norm_C(
        data[f"cum_{used_C}"], data["results"][f"calc_conc_{used_C}"]
    )
    (
        data["results"][f"X10_{used_C}"],
        data["results"][f"X16_{used_C}"],
        data["results"][f"X50_{used_C}"],
        data["results"][f"X84_{used_C}"],
        data["results"][f"X90_{used_C}"],
    ) = cumulative_diameters(data["X"], data[f"cum_{used_C}"])
    return data


def mean_of_n(data, nr_mean, used_C="Cn"):
    """calculates a mean of every n consecutive measurements and also gives the standard deviation
    select the desired data in an array before, to correctly work with it, if the number of repetitions was not always n
    only works with more than 3 measurements"""
    X, dX, C = sup.extract_from_dict(data, used_C)
    dlogX = data["dlogX"]
    C_dlogX = data[f"{used_C}_dlogX"]
    calc_conc = data["results"][f"calc_conc_{used_C}"]
    dg = data["results"][f"dg_{used_C}"]
    GSD = data["results"][f"GSD_{used_C}"]
    n = nr_mean
    size = X.shape
    nth_len = int(size[0] / n)
    mean_X = np.full((nth_len, size[1]), np.nan)
    mean_dX = np.full_like(mean_X, np.nan)
    mean_dlogX = np.full_like(mean_X, np.nan)
    mean_C = np.full_like(mean_X, np.nan)
    std_C = np.full_like(mean_X, np.nan)
    mean_C_dlogX = np.full_like(mean_X, np.nan)
    std_C_dlogX = np.full_like(mean_X, np.nan)
    mean_conc = []
    std_conc = []
    mean_dg = []
    mean_GSD = []
    std_dg = []
    std_GSD = []
    scan_nr = []
    time = []
    comment = []
    subscan_nrs = []
    for k in range(nth_len):
        mean_X[k, :] = np.mean(X[(k * n) : ((k + 1) * n), :], axis=0)
        mean_dX[k, :] = np.mean(dX[(k * n) : ((k + 1) * n), :], axis=0)
        mean_dlogX[k, :] = np.mean(dlogX[(k * n) : ((k + 1) * n), :], axis=0)
        mean_C[k, :] = np.mean(C[(k * n) : ((k + 1) * n), :], axis=0)
        std_C[k, :] = np.std(C[(k * n) : ((k + 1) * n), :], axis=0)
        mean_C_dlogX[k, :] = np.mean(C_dlogX[(k * n) : ((k + 1) * n), :], axis=0)
        std_C_dlogX[k, :] = np.std(C_dlogX[(k * n) : ((k + 1) * n), :], axis=0)
        mean_conc.append(np.mean(calc_conc[(k * n) : ((k + 1) * n),], axis=0))
        std_conc.append(np.std(calc_conc[(k * n) : ((k + 1) * n),], axis=0))
        mean_dg.append(np.mean(dg[(k * n) : ((k + 1) * n)], axis=0))
        std_dg.append(np.std(dg[(k * n) : ((k + 1) * n)], axis=0))
        mean_GSD.append(np.mean(GSD[(k * n) : ((k + 1) * n)], axis=0))
        std_GSD.append(np.std(GSD[(k * n) : ((k + 1) * n)], axis=0))
        scan_nr.append(data["add_info"]["Scan Nr"][k * n])
        time.append(data["add_info"]["Time"][k * n])
        comment.append(data["add_info"]["Comment"][k * n])
        sscn = ""
        if "Subscan Nr" in data["add_info"]:
            for j in range(
                0, n
            ):  # for every scan that is meaned into one append the subscan nr from subscan nrs
                sscn += (
                    str(data["add_info"]["Scan Nr"][k * n + j])
                    + "-"
                    + str(data["add_info"]["Subscan Nr"][k * n + j])
                    + " "
                )
        else:
            for j in range(0, n):
                sscn += str(data["add_info"]["Scan Nr"][k * n + j]) + " "
        subscan_nrs.append(sscn)
    add_info = pd.DataFrame(
        {
            "Scan Nr": scan_nr,
            "Time": time,
            "Comment": comment,
            "Subscan Nrs": subscan_nrs,
        }
    )
    results = pd.DataFrame(
        {
            "Scan Nr": scan_nr,
            "Time": time,
            "Comment": comment,
            "mean_conc": mean_conc,
            "std_conc": std_conc,
            f"mean_dg_{used_C}": mean_dg,
            f"std_dg_{used_C}": std_dg,
            f"mean_GSD_{used_C}": mean_GSD,
            f"std_GSD_{used_C}": std_GSD,
        }
    )
    mean_data = {
        "X": mean_X,
        "dX": mean_dX,
        "dlogX": mean_dlogX,
        f"mean_{used_C}": mean_C,
        f"std_{used_C}": std_C,
        f"mean_{used_C}_dlogX": mean_C_dlogX,
        f"std_{used_C}_dlogX": std_C_dlogX,
        "filename": data["filename"],
        "used_device": data["used_device"],
        "add_info": add_info,
        "results": results,
    }
    return mean_data


def merge_mean_data(mean_data_list, used_C="Cn", path="manual"):
    """merges dictionaries of data, should best be used with mean data dicts"""
    mean_C = f"mean_{used_C}"
    std_C = f"std_{used_C}"
    std_C_dlogX = f"{std_C}_dlogX"
    merged_mean_data = merge_data(mean_data_list, mean_C, path=path)
    merged_mean_data[std_C] = mean_data_list[0][std_C].copy()
    merged_mean_data[std_C_dlogX] = mean_data_list[0][std_C_dlogX].copy()
    for i in mean_data_list[1:]:
        merged_mean_data[std_C] = np.append(merged_mean_data[std_C], i[std_C], axis=0)
        merged_mean_data[std_C_dlogX] = np.append(
            merged_mean_data[std_C_dlogX], i[std_C_dlogX], axis=0
        )
    return merged_mean_data


def surface_dist(data):
    """gives surface concentration per bin in micrometer^2 / cm^3
    can be used on data directly, or on data selected with select_data()"""
    Cn = data["Cn"]
    X = data["X"]
    Cs = np.full_like(Cn, np.nan)
    mum_D = np.divide(X, 1000)
    # convert sel_X from nm to micrometers by dividing by 1000
    # percubicmeter_Cn = np.multiply(Cn, 10 ** 6)
    # convert sel_Cn to P/m^3
    for k in np.arange(Cn.shape[0]):
        for j in np.arange(Cn.shape[1]):
            Cs[k, j] = Cn[k, j] * (math.pi * (mum_D[k, j]) ** 2)
    data["Cs"] = Cs
    return data


def volume_dist(data):
    """gives volume concentration per bin in micrometer^3 / m^3
    can be used on data directly, or on data selected with select_data()"""
    Cn = data["Cn"]
    X = data["X"]
    Cv = np.full_like(Cn, np.nan)
    mum_D = np.divide(X, 1000)
    # convert sel_X from nm to micrometers by dividing by 1000
    percubicmeter_Cn = np.multiply(Cn, 10**6)
    # convert sel_Cn to P/m^3
    for k in np.arange(Cn.shape[0]):
        for j in np.arange(Cn.shape[1]):
            Cv[k, j] = percubicmeter_Cn[k, j] * ((1 / 6) * math.pi * (mum_D[k, j]) ** 3)
    data["Cv"] = Cv
    return data


def mass_dist(data, density):
    """gives mass concentration per bin in mg/m^3, takes g/cm^3 as density input, Cv in micrometer/m^3 must be
    calculated before! - can be used on data directly, or on data selected with select_data()"""
    Cv = data["Cv"]
    densitymgpermum = density * (
        10 ** (-9)
    )  # convert the density from g/cm^3 to milligram per cubic micrometer
    Cm = np.multiply(Cv, densitymgpermum)  # last part converts from per cm^3 to per m^3
    data["Cm"] = Cm
    return data  # check


def mean_and_std(data):
    """calculates the mean and std of whatever
    e.g. call for mean_dg, std_dg = mean_and_std(sel_data["results"]["dg"][idx]) to get mean and std of the geometric mean
    diameter of all the indexed measurements"""
    n = len(data)
    mean = np.mean(data)
    std = np.std(data)
    # print(f"mean of {n}:" + "{:e}".format(float(mean)) + u"\u00B1" +
    #        "{:e}".format(float(std)))
    return mean, std


def format_plot(fig, ax, used_C, used_device, size_range="standard"):
    cm = 1 / 2.54  # inches to cm
    fig.set_size_inches(16 * cm, 10 * cm)
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.ticklabel_format(style="sci", scilimits=(0, 0), axis="y", useMathText=True)
    size_unit = sup.decide_size_unit(used_device)
    x_label = "Particle Diameter / " + size_unit
    size_range = sup.decide_size_range(used_device, size_range)
    y_label = sup.decide_y_label(used_C)
    ax.set(
        xscale="log",
        xlabel=x_label,
        ylabel=y_label,
        xticks=size_range[0],
        xticklabels=size_range[1],
    )
    if size_range not in ["standard", ""]:
        ax.set_xlim(
            left=min(size_range[0]), right=max(size_range[0])
        )  # why is this chanigng my plots even if condition is met?
    # yscale='log', xscale='log', xlabel='$\mathregular{dlog D_p}$ / nm', ylabel='dN / $\mathregular{P/cm^3}$'
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(
        top=0.95
    )  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    return ax


def plot_singledata(
    data,
    scan_nrs,
    used_C="Cn",
    a=1,
    legend="automatic",
    legend_loc="upper right",
    save_plot="off",
    size_range="standard",
    color_map=defs.default_cm,
):
    """plots the given data, specify used_C to use "Cn", or "Cn_dlogX" measurement to use"""
    py_nrs = sup.py_logic_converter(scan_nrs)
    X, dX, C = sup.extract_from_dict(data, used_C)
    calc_conc = get_conc(data[used_C])
    used_device = data["used_device"]

    fig, ax = plt.subplots()  # height with title 12, without 10
    C_unit = sup.decide_C_unit(used_C)

    legend_entries = []

    ct = 0
    # if len(py_nrs) == 1:
    #     k = py_nrs[0]
    #     ax.bar(X[k, :], C[k, :], width=dX[k, :], edgecolor='black', color=Def.default_cm[0])
    #     Sup.build_legend(legend_entries, scan_nrs, ct, legend=legend)
    #     # print(f"scan {scan_nrs[0]} conc. = " + "{:e}".format(float(calc_conc[k])) + C_unit)
    # else:
    for k in py_nrs:
        ax.bar(
            X[k, :],
            C[k, :],
            width=dX[k, :],
            edgecolor="black",
            linewidth=0.5,
            color=color_map[ct],
            alpha=a,
        )
        sup.build_legend(legend_entries, scan_nrs, ct, legend=legend)
        # print(f"scan {k+1} conc. = " + "{:e}".format(float(calc_conc[k])) + C_unit)
        ct += 1

    ax = format_plot(fig, ax, used_C, used_device, size_range)
    # plt.rcParams['figure.dpi'] = 600
    # plt.rcParams['savefig.dpi'] = 600

    plt.legend(legend_entries, loc=legend_loc, frameon=False)

    sup.save_plot(data, save_plot)

    plt.show()
    return ax


def plot_add_stat_diameter(
    data, scan_nrs, diameter="dg"
):  # does not work in jupyter as it is not interactively plotting
    py_nrs = sup.py_logic_converter(scan_nrs)
    for k in py_nrs:
        plt.axvline(data["results"][diameter][k])


def plot_meandata(
    mean_data,
    scan_nrs,
    used_C="mean_Cn_dlogX",
    a=1,
    legend="automatic",
    legend_loc="upper right",
    save_plot="off",
    size_range="standard",
    color_map=defs.default_cm,
):
    """plots the given data, use range(start, end), or a list to specify the measurements to use, these are the indices
    in the given Cn and C arrays"""
    py_nrs = sup.py_logic_converter(scan_nrs)
    # add a mean of n in a corner of the plot
    used_C = used_C
    mean_X = mean_data["X"]
    mean_dX = mean_data["dX"]
    mean_C = mean_data[used_C]
    std_C = mean_data[used_C.replace("mean", "std")]

    used_device = mean_data["used_device"]

    fig, ax = plt.subplots()  # height with title 12, without 10
    legend_entries = []
    ct = 0
    for k in py_nrs:
        ax.bar(
            mean_X[k, :],
            mean_C[k, :],
            width=mean_dX[k, :],
            edgecolor="black",
            linewidth=0.5,
            color=color_map[ct],
            yerr=std_C[k, :],
            alpha=a,
        )

        sup.build_legend(legend_entries, scan_nrs, ct, legend=legend)
        ct += 1

        # [print(f"measurement {k+1} conc. = " + "{:e}".format(float(mean_conc_n[k])) + u"\u00B1" +
        #        "{:e}".format(float(std_conc_n[k])) + " P/cm" + u"\u00B3") for k in plot_nrs]

    format_plot(fig, ax, used_C, used_device, size_range=size_range)

    plt.legend(legend_entries, loc=legend_loc, frameon=False)

    sup.save_plot(mean_data, save_plot)
    plt.show()
    return ax


def normal_function(X_row, A, mu, sigma):
    """definition of a normal function with A being a scale factor, mu being the median and sigma being the geometric
    standard deviation"""
    return (
        A
        / (sigma * np.sqrt(2 * math.pi))
        * np.power(10, (-((X_row - mu) ** 2) / (2 * sigma**2)))
    )


def lognormal_function(X_row, A, mu, sigma):
    """definition of a log-normal function with A being a scale factor, m being the median and sigma being the geometric
    standard deviation - from Aerosol-Measurement p. 42"""
    # return A / (np.log(sigma) * np.sqrt(2 * math.pi)) * np.exp(-((np.log(X_row / mu)) ** 2) / (2 * np.log(sigma) ** 2))
    # gives same result -> as log10 is used everywhere, also used here
    return (
        A
        / (np.log10(sigma) * np.sqrt(2 * math.pi))
        * np.power(10, (-((np.log10(X_row / mu)) ** 2) / (2 * np.log10(sigma) ** 2)))
    )


def find_peaks_in_data(
    X_row,
    C_row,
    height=0.01,  # -> minimum height in scipy.signal.find_peaks
    width=1,  # -> minimum width in scipy.signal.find_peaks
    # threshold = could be added here which describes the difference in height between neighboring peaks
    distance=5,
):  # horizontal distance between neighboring peaks
    """
    Detects peaks in a 1D data array and generates initial guesses for fitting.
    Parameters:
    X_row (array-like): 1D array of corresponding x-axis values (e.g., sizes).
    C_row (array-like): 1D array of data values (e.g., concentrations).
    height (float): Minimum height of peaks to detect.
    width (float): Minimum width of peaks to detect.
    distance (int): Minimum distance between peaks.

    Returns:
        tuple: (X_peaks = ndarray: X_axis-positions / mu-values of peaks,
                properties = dict: peak_heights, prominences, left_bases, right_bases, widths, width_heights, left_ips,
                    right_ips,
                modality = int: number of detected peaks)
    """
    C_peaks, properties = find_peaks(
        C_row, height=np.nansum(C_row) * height, width=width, distance=distance
    )  # also provides properties
    print(f"properties: {properties}")
    modality = len(C_peaks)
    X_peaks = X_row[C_peaks]
    return X_peaks, properties, modality


def generate_initial_guesses_from_data(
    X_peaks, properties
):  # horizontal distance between neighboring peaks
    """
    Takes X_peaks, properties and modality from find_peaks_in_data and converts them into initial guesses in the right
    format to be used with monomodal, or multimodal_fit

    Returns:
            initial_guess_list = list: [A1, mu1, sigma1, A2, mu2, sigma2, ...]
    """
    initial_guess = []
    for k in range(len(X_peaks)):
        mu = X_peaks[k]  # Use x value at peak position -> actually close to dg
        A = properties["prominences"][k]  # height in dlogX distribution
        sigma = 1.5  # before properties["widths"][k] but that is in number of bins and leads to bad initial guesses
        initial_guess.extend([A, mu, sigma])
    # print(f' initial_guess: {initial_guess}')
    # print(f'modality: {modality}')
    return initial_guess


def create_bounds(initial_guess, modality, allowed_deviation=0.1):
    lowerbounds = []
    upperbounds = []
    for i in range(modality):
        lowerbounds.append(1)  # A_min
        lowerbounds.append(initial_guess[3 * i + 1] * (1 - allowed_deviation))  # mu_min
        lowerbounds.append(1)  # sigma_min
        upperbounds.append(np.inf)  # A_max
        upperbounds.append(initial_guess[3 * i + 1] * (1 + allowed_deviation))  # mu_max
        upperbounds.append(
            5
        )  # sigma_max # when initial guess is bad, sigma > upperbound sigma -> error x0 infeasible
        # as setting sigma via vidth from find_peaks it is determined by number of bins and not the actual sigma
        # that happens a lot, so in generatr_initial_guess sigma is now set to 1.5 and here to 5 as max value
    # print(f'lower bounds {lowerbounds}')
    # print(f'upper bounds {upperbounds}')
    bounds = (lowerbounds, upperbounds)
    return bounds


def monomodal_fit(
    X_row,
    C_row,
    fit_function="lognormal_function",
    initial_guess="automatic",
    boundaries="automatic",
):
    """fit of a monomodal distribution - works only for one measurement at a time"""
    modality = 1
    XnoNaNs = X_row[~np.isnan(X_row)]  # ~ = logical-not operator
    CnoNaNs = C_row[~np.isnan(C_row)]
    # generate initial guess
    if initial_guess == "automatic":
        X_peaks, properties, _ = find_peaks_in_data(X_row, C_row)
        idx = np.argmax(properties["prominences"])
        properties_content = [
            "peak_heights",
            "prominences",
            "left_bases",
            "right_bases",
            "widths",
            "width_heights",
            "left_ips",
            "right_ips",
        ]
        cut_properties = {}
        for k in range(len(properties_content)):
            cut_properties[f"{properties_content[k]}"] = properties[
                f"{properties_content[k]}"
            ][idx]
        initial_guess = generate_initial_guesses_from_data(
            [X_peaks[idx]], cut_properties
        )
    else:
        initial_guess = initial_guess
    if boundaries == "automatic":
        b = create_bounds(initial_guess, modality, allowed_deviation=0.01)
    else:
        b = boundaries
    function_to_fit = create_n_modal_fit_function(modality, fit_function)
    popt_fit, pcov_fit = optimize.curve_fit(
        function_to_fit, XnoNaNs, CnoNaNs, p0=initial_guess, bounds=b
    )  # , maxfev=10000)
    A_fit = popt_fit[0]
    mu_fit = popt_fit[1]
    sigma_fit = popt_fit[2]
    C_fit = function_to_fit(X_row, *popt_fit)
    return A_fit, mu_fit, sigma_fit, C_fit


def create_n_modal_fit_function(modality, fit_function):
    """produce n-modal function as linear combination of multiple fit functions as defined above with n
    being the number of contained single functions"""
    # Create the function signature
    args = ["X"] + [f"A{i + 1}, mu{i + 1}, sigma{i + 1}" for i in range(modality)]
    func_signature = ", ".join(args)
    # Create the function body
    func_body = " + ".join(
        [
            f"{fit_function}(X, A{i + 1}, mu{i + 1}, sigma{i + 1})"
            for i in range(modality)
        ]
    )
    # Combine the signature and body into a function definition
    func_def = f"def n_modal_fit({func_signature}):\n    return {func_body}\n"

    # Execute the function definition
    exec(
        func_def, globals()
    )  # must stay like this, if changed to n_modal_fit = exec(.. it drops nonType error when
    # calling the function later
    return n_modal_fit


def multimodal_fit(
    X_row,
    C_row,
    fit_function="lognormal_function",
    initial_guess="automatic",
    boundaries="automatic",
):
    """If initial guess is not automatic, provide it as list [A1, mu1, sigma1, ... An, mun, sigman].
    If boundaries are not automatic, provide them as tuple of lists
    ([lowerA1, lowermu1, lowersigma1, ...],[upperA1, uppermu1, uppersigma1, ... upperAn, uppermun, uppersigman]).
    Returned a ValueError: array must not contain infs or NaNs from scipy.optimize, so arrays have to be stripped of
    NaNs first when using cut arrays -> first two lines."""
    XnoNaNs = X_row[~np.isnan(X_row)]  # ~ = logical-not operator
    CnoNaNs = C_row[~np.isnan(C_row)]

    if initial_guess == "automatic":
        X_peaks, properties, modality = find_peaks_in_data(X_row, C_row)
        initial_guess = generate_initial_guesses_from_data(X_peaks, properties)
    else:
        initial_guess = initial_guess
        modality = int(len(initial_guess) / 3)
    if boundaries == "automatic":
        b = create_bounds(initial_guess, modality, allowed_deviation=0.1)
    else:
        b = boundaries
    function_to_fit = create_n_modal_fit_function(modality, fit_function)
    params, covs = optimize.curve_fit(
        function_to_fit, XnoNaNs, CnoNaNs, p0=initial_guess, bounds=(b), method="trf"
    )  #  # trf -> bounds are provided
    # ftol=10**(-11))  # xtol, gtol also available in least_squares, default is 1**(-8)
    var = np.diag(covs)  # variance is in diag of covs, sigma is sqrt of var
    C_fit = function_to_fit(X_row, *params)
    # print(params)
    # print(var)
    # in params for k = len measurements, every 0+(n*3) value is A, every 1+(n*3) value is mu and every 2+(n*3) value is
    # sigma -> have to be sorted into dataframe
    fit_params_vars = np.full((modality, 6), np.nan)
    for k in range(
        0, modality
    ):  # sort params A, mu, sigma into rows for each detected mode n as row
        fit_params_vars[k, 0] = params[0 + (k * 3)]  # A
        fit_params_vars[k, 1] = params[1 + (k * 3)]  # mu
        fit_params_vars[k, 2] = params[2 + (k * 3)]  # sigma
        fit_params_vars[k, 3] = var[0 + (k * 3)]  # Acov
        fit_params_vars[k, 4] = var[1 + (k * 3)]  # mucov
        fit_params_vars[k, 5] = var[2 + (k * 3)]  # sigmacov
    return modality, fit_params_vars, C_fit


def get_fit_modes(
    X_row, dlogX_row, modality, fit_params_vars, fit_function="lognormal_function"
):
    """calculate values from fitted size distributions"""
    modes = np.full((modality, X_row.shape[0]), np.nan)
    modes_no_dlogX = modes.copy()
    mode_descriptors = pd.DataFrame(columns=["dg", "GSD", "calc_conc"])
    function_to_fit = create_n_modal_fit_function(1, fit_function)
    calc_conc = []
    dg = []
    GSD = []
    for k in range(modality):
        modes[k] = function_to_fit(
            X_row, fit_params_vars[k, 0], fit_params_vars[k, 1], fit_params_vars[k, 2]
        )
        modes_no_dlogX[k] = modes[k] * dlogX_row
        conc = np.nansum(modes_no_dlogX[k])
        calc_conc.append(conc)
        dg.append(geometric_mean(X_row, modes_no_dlogX[k], conc))
        GSD.append(geometric_std(X_row, modes_no_dlogX[k], conc, dg[k]))
    mode_descriptors["calc_conc"] = calc_conc
    mode_descriptors["dg"] = dg
    mode_descriptors["GSD"] = GSD
    return modes, mode_descriptors


def fit_data(
    data,
    scan_nrs,
    used_C="Cn_dlogX",
    fit_function="lognormal_function",
    initial_guess="automatic",
    boundaries="automatic",
):
    """wrapper for the above functions - use with C_dlogX !"""
    py_nrs = sup.py_logic_converter(scan_nrs)
    C = data[used_C]
    if "cut" in used_C:
        X = data["cut_X"]
        dlogX = data["cut_dlogX"]
    else:
        X = data["X"]
        dlogX = data["dlogX"]

    used_C_no_dlogX = used_C.replace("_dlogX", "")
    # if C_dlogX was used (which is standard), the concentration has to be calculated from the non dlogX C -> see below
    # if no "_dlogX" in used_C, nothing changes and conc is still correctly calculated

    # create arrays to place data in if not already there
    if f"fit_{used_C}" in data:
        data[f"fit_{used_C}_modes"] = data[f"fit_{used_C}_modes"].reshape(
            C.shape[0], 10, C.shape[1]
        )
        pass
    else:
        data[f"fit_{used_C}"] = np.full_like(data[used_C], np.nan)
        data[f"fit_{used_C}_modes"] = np.full((C.shape[0], 10, C.shape[1]), np.nan)
        # creates array that is 3D with manymany NaNs - plot function needs removal of all completely nan rows in iterator
        # saving to excel requires 2D array -> conversion below

    # fill arrays and store values in results
    for k in py_nrs:
        if np.nansum(C[k]) == 0:
            modality = 0
            modes = C[k]
            mode_descriptors = {"calc_conc": [0], "dg": [0], "GSD": [np.inf]}
            data[f"fit_{used_C}"][k] = C[k]
        else:
            modality, fit_params_vars, C_fit = multimodal_fit(
                X[k],
                C[k],
                fit_function=fit_function,
                initial_guess=initial_guess,
                boundaries=boundaries,
            )
            modes, mode_descriptors = get_fit_modes(
                X[k],
                dlogX[k],
                modality,
                fit_params_vars,
                fit_function="lognormal_function",
            )
            data[f"fit_{used_C}"][k] = C_fit
        data["results"].loc[k, "modality"] = modality

        conc_list = []
        for i in range(modality):
            conc_list.append(np.nansum(modes[i] * dlogX[k]))

        data["results"].loc[k, f"calc_conc_fit_{used_C_no_dlogX}"] = sum(conc_list)

        # maximum number of modes should be 10, more are not transferred to results
        if modality > 10:
            maxmodality = 10
        else:
            maxmodality = modality

        for i in range(maxmodality):
            data[f"fit_{used_C}_modes"][k][i] = modes[i]
            data["results"].loc[k, f"dg fit {i + 1}"] = mode_descriptors["dg"][i]
            data["results"].loc[k, f"GSD fit {i + 1}"] = mode_descriptors["GSD"][i]
            data["results"].loc[k, f"calc_conc_fit_{used_C_no_dlogX} {i + 1}"] = (
                mode_descriptors["calc_conc"][i]
            )

    data[f"fit_{used_C}_modes"] = data[f"fit_{used_C}_modes"].reshape(
        C.shape[0] * 10, C.shape[1]
    )
    # reshape to get 2D array which can be saved to xlsx and viewd in workspace

    return data


def plot_fit_data(
    data,
    scan_nrs,
    used_C="Cn_dlogX",
    a=1,
    legend="automatic",
    legend_loc="upper right",
    save_plot="off",
    size_range="standard",
    color_map=defs.default_cm,
):
    """plots the fit data, only plot one dataset at a time"""
    py_nrs = sup.py_logic_converter(scan_nrs)
    X = data["X"]
    dX = data["dX"]
    C = data[used_C]
    C_fit = data["fit_" + used_C]
    C_modes = data["fit_" + used_C + "_modes"].reshape(
        C.shape[0], 10, C.shape[1]
    )  # reshape from 2D to 3D
    modality = data["results"]["modality"]
    used_device = data["used_device"]
    markers = [".", "x", "o", "v", "^", "s", "8", "*", "h", ","]

    legend_entries = []
    fig, ax = plt.subplots()

    ct = 0
    if len(py_nrs) == 1:
        # plot the distribution and the fit
        k = py_nrs[0]
        ax.bar(
            X[k, :],
            C[k, :],
            width=dX[k, :],
            edgecolor="black",
            linewidth=0.5,
            color=color_map[0],
        )
        plt.plot(X[k, :], C_fit[k, :], color="black")  # , lw=3, label='multimodal fit')
        sup.build_legend(
            legend_entries, scan_nrs, ct, legend=legend
        )  # work on build legend!

        # plot the modes one by one
        for i in range(int(modality[k])):
            plt.scatter(
                X[k, :], C_modes[k, i, :], color="black", marker=markers[i], s=5
            )
            # lw=3, ls=":", label=f"distribution {k + 1}", color=color_map[ct])
            legend_entries.append(f"Mode {i + 1}")

    else:
        for k in py_nrs:
            # plot the distribution
            ax.bar(
                X[k, :],
                C[k, :],
                width=dX[k, :],
                edgecolor="black",
                linewidth=0.5,
                color=color_map[ct],
                alpha=a,
            )
            plt.scatter(
                X[k, :], C_fit[k, :], color="black", marker=markers[k], s=5
            )  # , lw=3, label='multimodal fit')
            # add the legend
            sup.build_legend(legend_entries, scan_nrs, ct, legend=legend)
            ct += 1

    plt.xscale("log")

    ax = format_plot(fig, ax, used_C, used_device, size_range=size_range)

    plt.legend(legend_entries, loc=legend_loc, frameon=False)
    Sup.save_plot(data, save_plot)

    plt.show()
    return ax


# following did not work of course. Instead, there should be a new function created and the format plot should maybe be
# changed, or rather the save fig passage should be moved to format_plot
# def plot_mixeddata(datalist):
#     """plots mixed data from distribution and concentration, enter input as in plot_singledata, but as list of different
#     inputs like [(data1, [scan_nrs1], used_C1), (data2, [scan_nrs2], used_C2),...]"""
#     for dataset in datalist:
#         ax = plot_singledata(dataset[0], dataset[1], dataset[2])
#     return ax


# def plot_3Dsingledata(sel_X, sel_Cn, start, end):
#     """plots the given data in 3D, specify scan numbers start and end in actual scan number"""
#     cm = 1/2.54  # inches to cm
#     fig = plt.figure(figsize=(18.5*cm, 18.5*cm))
#     ax = fig.add_subplot(111, projection='3d')
#     X, Y = np.meshgrid(np.log(sel_X[start, :]), np.arange(start, end+1)) #log as ax.set(xscale ='log') doesnt work in 3d
#     ax.plot_surface(X, Y, sel_Cn[start-1:end, :], cmap=colormap.coolwarm)
#         #, alpha=0.5)
#     ax.set(xticks=[np.log(20), np.log(50), np.log(100), np.log(200), np.log(400), np.log(800)],
#            xticklabels=[20, 50, 100, 200, 400, 800],
#            xlabel='Particle Diameter / nm',
#            ylabel='Scan Number',
#            zlabel='Differential Particle Number Concentration / $\mathregular{1/cm^3}$')
#     # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
#     #fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
#     #legend_entries = []
#     #for k in measurement_nr:
#     #    legend_entries.append(input(f"Please enter the legend entry for measurement {k}"))
#     #    print(f"measurement {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
#     #plt.legend(legend_entries)
#
#     plt.show()
#     return ax

if __name__ == "__main__":
    """"""

    import particle_analysis as pa

    # data = pa.get_data("fixed", used_device=2, filename='C:/Users/kevin.maier/PycharmProjects/py_particleanalysis/ExampleFiles/20230704_PALAS_USMPS.txt')
    data = pa.get_data(
        "fixed",
        used_device=2,
        filename="C:/UniStuff/Code/Python/py_particleanalysis/ExampleFiles/20230704_PALAS_USMPS.txt",
    )
    dist.typical_calculations(data)
    n_msmts = len(data["X"])
    dist.typical_calculations(data)

    for k in [1, 2, 3, 4, 5, 6, 10, 16, 29, 31, 35, 36]:
        dist.fit_data(data, [k])
        dist.plot_fit_data(data, [k])

    # print(data["results"])
