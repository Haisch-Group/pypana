# -*- coding: utf-8 -*-
"""
Dist.py

Script for Evaluation of Particle Size Distributions
Run from Particle_analysis.py

Created 2024-03-20 by moving functions from Particle_analysis.py
@written by Kevin Maier (kevin.r.maier@tum.de)

"""


from matplotlib import ticker
from matplotlib import pyplot as plt
import numpy as np
import math
from scipy import optimize
from scipy.signal import find_peaks
import random
import pandas as pd

import Dist
import Sup
import Def
import decimal

from Sup import py_logic_converter


# import scipy.integrate as integrate


def select_data(data, sel_nrs):
    """select specific scans from the imported raw data to then process them, scan_nrs defines, which scans to take
    in normal non-pythonian logic (starting count at 1)
    can only easily select data from one day for comparison"""
    scan_nrs = Sup.py_logic_converter(sel_nrs)
    sel_Cn = np.zeros((len(scan_nrs), data["Cn"].shape[1]))
    # preallocate the np arrays in the correct size (nr of measurements, nr of measuring data)
    sel_X = np.zeros_like(sel_Cn)  # maybe nan is needed to avoid zeros on the right of the x-data?
    sel_dX = np.zeros_like(sel_Cn)
    sel_time = []
    sel_scan_nr = []
    sel_filename = []
    # different datasets
    sel_used_device = []
    for k in np.arange(len(scan_nrs)):  # fill the arrays with the selected data
        sel_Cn[k, :] = data["Cn"][scan_nrs[k], :]
        sel_X[k, :] = data["X"][scan_nrs[k], :]
        sel_dX[k, :] = data["dX"][scan_nrs[k], :]
        sel_time.append(data["add_info"]["Time"][scan_nrs[k]])
        sel_scan_nr.append(data["add_info"]["Scan Nr"][scan_nrs[k]])
        sel_filename.append(data["filename"])
        sel_used_device.append(data["used_device"])
    sel_data = {"X": sel_X, "Cn": sel_Cn, "dX": sel_dX, "time": sel_time, "scan_nr": sel_scan_nr,
                "filename": sel_filename, "used_device": sel_used_device}
    return sel_data


# def convert_cn_to_cn_dlogx(data):
#     data["Cn_dlogX"] = data["Cn"]/data["dlogX"]
#     return data
#
#
# def convert_cn_dlogx_to_cn(data):
#     data["Cn"] = data["Cn_dlogX"]*data["dlogX"]
#     return data


def get_conc(C):
    """calculate the total concentration for each selected measurement, can be applied to Cn, Cv, or Cm
    call for example as data["calc_conc_n"] = get_conc(data["Cn"]) to specify (or Cv, or Cm)"""
    calc_conc = np.zeros(C.shape[0], )  # preallocate the array again
    for k in range(C.shape[0]):  # iteratively fill the array with the sum of all size concentrations
        calc_conc[k, ] = np.nansum(C[k, :])  # np.nansum counts NaN as 0
    return calc_conc


def cut_dist_data(X, C, dX, lowerbound, upperbound, scan_nrs):  # merge with select_data
    """to cut a part of the spectrum"""
    cut_nrs = Sup.py_logic_converter(scan_nrs)
    strt_idx = np.where(X[0] > lowerbound)[0][0]
    end_idx = np.where(X[0] < upperbound)[-1][-1] + 1
    cut_X = np.zeros((len(cut_nrs), len(X[0, strt_idx:end_idx])))
    cut_C = np.zeros((len(cut_nrs), len(C[0, strt_idx:end_idx])))
    cut_dX = np.zeros((len(cut_nrs), len(dX[0, strt_idx:end_idx])))
    cut_conc = []
    ct = 0
    for k in cut_nrs:
        cut_X[ct, :] = X[k, strt_idx:end_idx]
        cut_C[ct, :] = C[k, strt_idx:end_idx]
        cut_dX[ct, :] = dX[k, strt_idx:end_idx]
        cut_conc.append(np.nansum(cut_C[ct, :]))
        ct += 1
    return cut_X, cut_C, cut_dX, cut_conc


def cut_dist(data, lowerbound, upperbound, scan_nrs, used_C="Cn"):
    X, dX, C = Sup.extract_from_dict(data, used_C)
    cut_X, cut_C, cut_dX, cut_conc = cut_dist_data(X, C, dX, lowerbound, upperbound, scan_nrs)
    data["cut_X"] = cut_X
    data[f"cut_{used_C}"] = cut_C
    data["cut_dX"] = cut_dX
    data["results"][f"cut_conc_{used_C}"] = cut_conc
    return data

def merge_data(sel_data_list):
    """merges dictionaries of data, should best be used with selected data dicts"""
    merged_data_X = []  # create lists to fill with list of 1D arrays
    merged_data_Cn = []
    merged_data_dX =[]
    n_scans = 0  # count measurements that are imported to the lists
    x_len_list = []
    for i in sel_data_list:  # append all imported lines to the lists
        for k in range(len(i["scan_nr"])):
            merged_data_X.append(i["X"][k])
            merged_data_Cn.append(i["Cn"][k])
            merged_data_dX.append(i["dX"][k])
            n_scans += 1
            x_len_list.append(len(i["X"][k]))
    x_len = max(x_len_list)  # get maximum length of the x_axis elements -> longest x-axis is base for array
    merged_array_X = np.zeros((n_scans, x_len))  # preallocate arrays for X, Cn, dX
    merged_array_Cn = np.zeros((n_scans, x_len))
    merged_array_dX = np.zeros((n_scans, x_len))
    merged_array_X[:] = np.nan  # fill with nans so no weird zero values are plotted later
    merged_array_Cn[:] = np.nan
    merged_array_dX[:] = np.nan
    for k in range((n_scans)):  # fill arrays row wise with data from list elements
        merged_array_X[k, 0:len(merged_data_X[k])] = merged_data_X[k]
        merged_array_Cn[k, 0:len(merged_data_Cn[k])] = merged_data_Cn[k]
        merged_array_dX[k, 0:len(merged_data_dX[k])] = merged_data_dX[k]

    merged_data = {}
    merged_data["X"] = merged_array_X
    merged_data["Cn"] = merged_array_Cn
    merged_data["dX"] = merged_array_dX
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
    print(Def.device_list[["Device_Identifier", "Device", "Manufacturer"]].to_string(justify="left", index=False))
    sel_merged_data["used_device"] = int(input(f"Please enter the device identifier of the used device"))
    return sel_merged_data


def geometric_mean(X, C, conc):
    """calculates the geometric mean from given X, C and conc, can be used with mean_C, or sel_C,
    call mean_dg = geometric_mean(mean_X, mean_C, mean_conc then, or sel_dg = geometric_mean(sel_X, sel_C, calc_conc)"""
    # for lognormal, count median diameter = geometric mean diameter
    # maybe add a check for lognormal
    dg = []
    for k in np.arange(0, C.shape[0]):
        if conc[k] == 0:
            dg.append(0)
        else:
            dg.append(math.pow(10, ((1 / conc[k]) * np.nansum(np.log10(X[k]) * C[k]))))
            # dg.append(math.exp((1 / conc[k]) * np.nansum(np.log(X[k])*C[k])))
            # both methods give the same result only varying by 10**-14 in some cases so negligible
            # log10 is used, as data is also on log10 base
    return dg


def count_median_diameter(X, C, conc):
    """does not work atm as all values are float and that only works until 10**308 which is reached with the first
    power operation """
    X_dummy = np.array(X.copy(), dtype=np.longdouble)
    C_dummy = np.array(C.copy(), dtype=np.longdouble)
    CMD = []
    for k in np.arange(0, C.shape[0]):
        if conc[k] == 0:
            CMD.append(0)
        else:
            CMD.append(np.power(np.nanprod(np.power(X_dummy[k], C_dummy[k])), 1/conc[k]))
    return CMD


def geometric_std(X, C, conc, dg):
    """calculates the geometric standard deviation from given X, C and conc, can be used with mean_C, or sel_C,
        call mean_sigma_g = geometric_std(mean_X, mean_C, mean_conc, mean_dg then,
        or sel_sigma_g = geometric_std(sel_X, sel_C, calc_conc, sel_dg)"""
    sigma_g = []
    for k in range(0, len(conc)):  # gave a math error for conc < 1 because conc-1 in sigma_g is < 0 then, so division
        #  is not possible
        if conc[k] < 1.00001:
            sigma_g.append(np.inf) # is infinity correct here? should it just be a massiv value? if after that a std is
            # calculated for example when using mean_of_n, the std of sigma is nan of course
        else:
            # sigma_g.append(math.exp(math.sqrt((np.nansum(np.square(np.log(X[k])
            #                                                       - np.log(dg[k]))*C[k]))/(conc[k]-1))))
            # 22-13 in aerosol measurement, Kulkarni et.al.  # 20230705 changed /conc to /np.nansum(C[k]-1)
            sigma_g.append(math.pow(10, (math.sqrt((np.nansum(np.square(np.log10(X[k])-np.log10(dg[k]))*
                                                              C[k]))/(conc[k]-1)))))
            # changed to log10 as it is used everywhere else on 20250128
        # same result as above
    return sigma_g


def mode_surface_volume_diameter(dg, sigma_g):
    """calculates the mode diameter from dg and sigma_g via equation given in Aerosol Measurement p.43 - usually
    calculated from CMD"""
    mode = []
    SMD = []
    VMD = []
    for k in range(len(dg)):
        if dg[k] == 0:
            mode.append(0)
            SMD.append(0)
            VMD.append(0)
        else:
            mode.append(dg[k]*math.pow(10,(-np.log10(sigma_g[k])**2)))
            SMD.append(dg[k]*math.pow(10,(2*np.log10(sigma_g[k])**2)))
            VMD.append(dg[k]*math.pow(10,(3*np.log10(sigma_g[k])**2)))
    return mode, SMD, VMD


def calc_geometry(X, C, conc):
    """calculates geometric parameters of the distributions"""
    dg = geometric_mean(X, C, conc)
    sigma_g = geometric_std(X, C, conc, dg)
    return dg, sigma_g


def cumulative_distribution(C):
    """calculates the cumulative distribution"""  # tested, first column = Cn[0], last column = calc_conc_n
    cumC = np.zeros_like(C)
    for scan in range(len(C)):
        cumC[scan, 0] = C[scan, 0]
        for k in range(1, len(C[scan])):
            cumC[scan, k] = cumC[scan, k-1] + C[scan, k]
    return cumC


def cumulative_diameters(X, cumC):
    """calculates the diameters below which 10, 16, 50, 84 and 90 % of all particles are"""
    # seemingly works, at least X50 were similar to PDAnalyze X50 values, but slightly different, as i just give the
    # middle X value of the bin, maybe PALAS does some other magic with it like calculating a discrete distribution
    X10 = []
    X16 = []
    X50 = []
    X84 = []
    X90 = []
    for k in range(len(cumC)):
        X10.append(X[k][next((index for index, val in enumerate(cumC[k]) if val > cumC[k][-1]*0.1), 0)])
        X16.append(X[k][next((index for index, val in enumerate(cumC[k]) if val > cumC[k][-1]*0.16), 0)])
        X50.append(X[k][next((index for index, val in enumerate(cumC[k]) if val > cumC[k][-1]*0.5), 0)])
        X84.append(X[k][next((index for index, val in enumerate(cumC[k]) if val > cumC[k][-1]*0.84), 0)])
        X90.append(X[k][next((index for index, val in enumerate(cumC[k]) if val > cumC[k][-1]*0.9), 0)])
    # cumDiameters = pd.DataFrame({"X10": X10, "X16": X16, "X50": X50, "X84": X84, "X90": X90})
    return X10, X16, X50, X84, X90  # cumDiameters


def typical_calculations(data):
    data["results"]["calc_conc_n"] = get_conc(data["Cn"])
    data["results"]["dg"], data["results"]["sigma_g"] = calc_geometry(data["X"], data["Cn"], data["results"]["calc_conc_n"])
    data["results"]["mode"], data["results"]["SMD"], data["results"]["VMD"] = (
        mode_surface_volume_diameter(data["results"]["dg"], data["results"]["sigma_g"]))
    data["cumC"] = cumulative_distribution(data["Cn"])
    (data["results"]["X10"], data["results"]["X16"], data["results"]["X50"], data["results"]["X84"],
     data["results"]["X90"]) = cumulative_diameters(data["X"], data["cumC"])
    return data


def lognormal_dist(conc, sigma_g, dg, X, dX):
    """calculates a normal distribution based on the concentration, the median diameter and the geometric standard
    deviation"""
    fit = np.zeros_like(X)
    for k in np.arange(0, X.shape[0]):
        #fit[k, :] = (mean_conc_n[k] / (math.sqrt(2 * math.pi) * np.log(sigma_g[k]))) * \
        #            np.exp((-np.square(np.log(mean_X[k, :]) - np.log(dg[k]))) / (2 * (math.log(sigma_g[k])) ** 2))
        # is roughly 28 times higher than the histogram
        fit[k, :] = ((conc[k])/(math.sqrt(2 * math.pi) * np.log(sigma_g[k])))*\
                    np.exp((-np.square(np.log(X[k, :])-np.log(dg[k])))/(2*(math.log(sigma_g[k]))**2))
        # did not do what i wanted it to
        # fit[k, :] = ((mean_conc_n[k] / mean_X.shape[0]) / (math.sqrt(2 * math.pi) * np.log10(sigma_g[k]))) * \
        #            np.power(10, ((-np.square(np.log10(mean_X[k, :]) - np.log10(dg[k]))) /
        #                          (2 * (math.log10(sigma_g[k])) ** 2)))
        # gives more narrow distribution than with natural base
        # fit[k, :] = (1 / (math.sqrt(2 * math.pi) * np.log(sigma_g[k]))) * \
        #             np.exp((-np.square(np.log(mean_X[k, :]) - np.log(dg[k]))) / (2 * (math.log(sigma_g[k])) ** 2))

    return fit


def lognormal_function(x, A, mu, sigma):
    """definition of a log-normal function with A being a scale factor, m being the median and sigma being the geometric
    standard deviation - from Aerosol-Measurement p. 486 with added A parameter similar to p. 42
    A is not directly conc, don't use with fit!"""
    return A / (x * np.log(sigma) * np.sqrt(2 * math.pi)) * np.exp(-((np.log(x / mu)) ** 2) / (2 * np.log(sigma) ** 2))


def normalized_lognormal_function(x, A, mu, sigma):
    """normalized lognormal function and factor A for scaling -> by that, A should directly be the concentration
    use this!"""
    return A*(1/(x*np.log(sigma)*np.sqrt(2*math.pi))*np.exp(-((np.log(x/mu))**2)/(2*np.log(sigma)**2))
              /np.nansum(1/(x*np.log(sigma)*np.sqrt(2*math.pi))*np.exp(-((np.log(x/mu))**2)/(2*np.log(sigma)**2))))


def normal_function(x, A, mu, sigma):
    """definition of a normal function with A being a scale factor, mu being the median and sigma being the geometric
    standard deviation"""
    return A/(sigma*np.sqrt(2*math.pi))*np.exp(-((x-mu)**2)/(2*sigma**2))


def monomodal_fit(X, C, fit_function=Dist.normalized_lognormal_function):
    """fit of a monomodal distribution - works only for one measurement at a time"""
    ## work this through
    p0=[1000, np.median(X), 1.2] # guesses a monodisperse peak in the middle of the X-axis and with 10^4 /cm^3
    lowerbounds=[0, min(X), 1]  # lower bound is 0 conc, lower boundary of X-axis and completely monodisperse
    upperbounds=[np.inf, max(X), 5]  # upper bound is infinite conc., upper bound of X-axis and polydisperse
    popt_fit, pcov_fit = optimize.curve_fit(fit_function, X, C, p0=p0,
                                                            bounds=(lowerbounds, upperbounds), maxfev=1000)
    A_fit=popt_fit[0]
    mu_fit=popt_fit[1]
    sigma_fit=popt_fit[2]
    C_fit=fit_function(X, *popt_fit)
    return A_fit, mu_fit, sigma_fit, C_fit


def create_bounds(n):
    bounds_1 = []
    bounds_2 = []
    bounds=(bounds_1,bounds_2)
    for i in range(1, n+1):
        bounds_1.append(0.1)
        bounds_1.append(1.0)
        bounds_1.append(0.1)
    for k in range(1, n+1):
        bounds_2.append(8500)
        bounds_2.append(np.inf)
        bounds_2.append(np.inf)
    return bounds


def generate_initial_guesses_from_data(
        x_array,
        data_row,
        height=10,
        distance=5,
        a2_range=(1.3, 4.0),
        a3_range=(100, 100000)):
    """
    Detects peaks in a 1D data array and generates initial guesses for fitting.
    Parameters:
    data_row (array-like): 1D array of data values (e.g., concentrations).
    x_array (array-like): 1D array of corresponding x-axis values (e.g., sizes).
    height (float): Minimum height of peaks to detect.
    distance (int): Minimum distance between peaks.
    a2_range (tuple): Range (min, max) for random generation of a2 values.
    a3_range (tuple): Range (min, max) for random generation of a3 values.

    Returns:
            tuple: (initial_guess_list, number_of_modes)
                - initial_guess_list: [a1, a2, a3, b1, b2, b3, ...]
                - number_of_modes: int, number of detected peaks
    """

    # Detect peaks
    peaks, _ = find_peaks(data_row, height=height, distance=distance)
    num_modes = len(peaks)

    # Generate initial guesses
    initial_guess = []
    for peak_index in peaks:
        a1 = x_array[peak_index]  # Use x value at peak position
        a2 = random.uniform(*a2_range)
        a3 = random.uniform(*a3_range)
        initial_guess.extend([a1, a2, a3])
    print(f' initial_guess: {initial_guess}, n modes: {num_modes}')
    return initial_guess, num_modes


def create_n_modal_fit_function(n, fit_function):
    """produce n-modal function as linear combination of multiple fit functions as defined above with n
    being the number of contained single functions"""
    # Create the function signature
    args = ['x'] + [f'mu{i + 1}, sigma{i + 1}, A{i + 1}' for i in range(n)]
    func_signature = ', '.join(args)
    # Create the function body
    func_body = ' + '.join([f'{fit_function}(x, mu{i + 1}, sigma{i + 1}, A{i + 1})' for i in range(n)])
    # Combine the signature and body into a function definition
    func_def = f"def n_modal_fit({func_signature}):\n    return {func_body}\n"

    # Execute the function definition
    exec(func_def, globals())  # must stay like this, if changed to n_modal_fit = exec(.. it drops nonType error when
    # calling the function later
    return n_modal_fit


def multimodal_fit(X, C, fit_function="normalized_lognormal_function"):
    initial_guess, n = generate_initial_guesses_from_data(X, C, height=10, distance=5, a2_range=(1.3, 4.0),
        a3_range=(100, 100000))
    b = create_bounds(n)
    function_type = create_n_modal_fit_function(n, fit_function)
    params, cov = optimize.curve_fit(function_type, X, C,
                            p0=initial_guess,
                            bounds=(b),
                            method="trf")  # trf -> bounds are provided
    sigma = np.sqrt(np.diag(cov))
    plt.plot(X, function_type(X, *params),
             color='red', lw=3, label='multimodal fit')
    for k in range(0,n):
        plt.plot(X, lognormal_function(X, *params[k*3:(k+1)*3]),
             color='yellow', lw=1.5, ls=":", label=f"distribution {k+1}")
    plt.legend()
    plt.xscale("log")
    print(params) # this looks super weird -> there, the writing into  the df is wrongly scripted by me

    df = pd.DataFrame(data={'A': params[0], 'mu': params[1], 'sigma': params[2], 'covA': cov[0], 'covmu': cov[1], 'covsigma': cov[2]})
    return df


def mean_of_n(data, nr_mean):
    """calculates a mean of every n consecutive measurements and also gives the standard deviation
    select the desired data in an array before, to correctly work with it, if the number of repetitions was not always n
    only works with more than 3 measurements"""
    C = data["Cn"]
    X = data["X"]
    dX = data["dX"]
    calc_conc = data["results"]["calc_conc_n"]
    dg = data["results"]["dg"]
    sigma = data["results"]["sigma_g"]
    n = nr_mean
    size = C.shape
    nth_len = int(size[0]/n)
    mean_C = np.zeros(shape=(nth_len, size[1]))  # np.nans?
    std_C = np.zeros_like(mean_C)
    mean_X = np.zeros_like(mean_C)
    mean_dX = np.zeros_like(mean_C)
    mean_conc = []
    std_conc = []
    mean_dg = []
    mean_sigma = []
    std_dg = []
    std_sigma = []
    for k in range(nth_len):
        mean_C[k, :] = np.mean(C[(k*n):((k+1)*n), :], axis=0)
        std_C[k, :] = np.std(C[(k*n):((k+1)*n), :], axis=0)
        mean_X[k, :] = np.mean(X[(k*n):((k+1)*n), :], axis=0)
        mean_dX[k, :] = np.mean(dX[(k * n):((k + 1) * n), :], axis=0)
        mean_conc.append(np.mean(calc_conc[(k * n):((k + 1) * n), ], axis=0))
        std_conc.append(np.std(calc_conc[(k * n):((k + 1) * n), ], axis=0))
        mean_dg.append(np.mean(dg[(k * n):((k + 1) * n)], axis=0))
        std_dg.append(np.std(dg[(k * n):((k + 1) * n)], axis=0))
        mean_sigma.append(np.mean(sigma[(k * n):((k + 1) * n)], axis=0))
        std_sigma.append(np.std(sigma[(k * n):((k + 1) * n)], axis=0))
    mean_data = {"mean_X": mean_X, "mean_C": mean_C, "std_C": std_C, "dX": mean_dX,
                 "mean_conc": mean_conc, "std_conc": std_conc, "mean_dg": mean_dg,"std_dg":std_dg,
                 "mean_sigma": mean_sigma, "std_sigma": std_sigma, "used_device": data["used_device"]}
    return mean_data


def merge_mean_data(mean_data_list):
    """merges dictionaries of data, should best be used with mean data dicts
    currently also writes into the first dict it takes data from???"""
    merged_mean_data = {}
    merged_mean_data["mean_X"] = mean_data_list[0]["mean_X"]
    merged_mean_data["mean_C"] = mean_data_list[0]["mean_C"]
    merged_mean_data["std_C"] = mean_data_list[0]["std_C"]
    merged_mean_data["dX"] = mean_data_list[0]["dX"]
    merged_mean_data["mean_conc"] = mean_data_list[0]["mean_conc"][:]
    merged_mean_data["std_conc"] = mean_data_list[0]["std_conc"][:]
    merged_mean_data["mean_dg"] = mean_data_list[0]["mean_dg"][:]
    merged_mean_data["std_dg"] = mean_data_list[0]["std_dg"][:]
    for i in mean_data_list[1:]:
        merged_mean_data["mean_X"] = np.append(merged_mean_data["mean_X"], i["mean_X"], axis=0)
        merged_mean_data["mean_C"] = np.append(merged_mean_data["mean_C"], i["mean_C"], axis=0)
        merged_mean_data["std_C"] = np.append(merged_mean_data["std_C"], i["std_C"], axis=0)
        merged_mean_data["dX"] = np.append(merged_mean_data["dX"], i["dX"], axis=0)
        merged_mean_data["mean_conc"].extend(i["mean_conc"])
        merged_mean_data["std_conc"].extend(i["std_conc"])
        merged_mean_data["mean_dg"].extend(i["mean_dg"])
        merged_mean_data["std_dg"].extend(i["std_dg"])
    return merged_mean_data


def typical_calculations_mean(data):
    data["calc_conc_n"] = get_conc(data["mean_C"])
    data["dg"], data["sigma"] = calc_geometry(data["mean_X"], data["mean_C"], data["calc_conc_n"], data["dX"])
    return data


def volume_dist(data):
    """gives volume concentration per bin in micrometer^3 / m^3
    can be used on data directly, or on data selected with select_data()"""
    Cn = data["Cn"]
    X = data["X"]
    Cv = np.zeros_like(Cn)
    mum_D = np.divide(X, 1000)
    # convert sel_X from nm to micrometers by dividing by 1000
    percubicmeter_Cn = np.multiply(Cn, 10 ** 6)
    # convert sel_Cn to P/m^3
    for k in np.arange(Cn.shape[0]):
        for j in np.arange(Cn.shape[1]):
            Cv[k, j] = (percubicmeter_Cn[k, j] * ((1 / 6) * math.pi * (mum_D[k, j]) ** 3))
    data["Cv"] = Cv
    return data


def mass_dist(data, density):
    """gives mass concentration per bin in mg/m^3, takes g/cm^3 as density input, Cv in micrometer/m^3 must be
    calculated before! - can be used on data directly, or on data selected with select_data()"""
    Cv = data["Cv"]
    densitymgpermum = density*(10**(-9))  # convert the density from g/cm^3 to milligram per cubic micrometer
    Cm = np.multiply(Cv, densitymgpermum)  # last part converts from per cm^3 to per m^3
    data["Cm"] = Cm
    return data # check


def mean_and_std(data):
    """calculates the mean and std of whatever
    e.g. call for mean_dg, std_dg = mean_and_std(sel_data["dg"][idx]) to get mean and std of the geometric mean
    diameter, or call mean_conc_n, std_conc_n = mean_and_std(data_identifier["calc_conc_n"][idx])"""
    n = len(data)
    mean = np.mean(data)
    std = np.std(data)
    # print(f"mean of {n}:" + "{:e}".format(float(mean)) + u"\u00B1" +
    #        "{:e}".format(float(std)))
    return mean, std


def format_plot(fig, ax, used_C, used_device):
    cm = 1 / 2.54  # inches to cm
    fig.set_size_inches(16 * cm, 10 * cm)
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    y_label = Sup.decide_y_label(used_C)
    if used_device in list(Def.device_list.query("Size_Plot_Range==u'\xb5m'")["Device_Identifier"].values):
        # for micrometer instruments TSI APS, PALAS WELAS
        ax.set(xscale='log', xticks=[0.5, 1, 2, 5, 10], xticklabels=[0.5, 1, 2, 5, 10],
               xlabel=u'Particle Diameter / \xb5m',
               ylabel=y_label)
    elif used_device in list(Def.device_list.query("Size_Plot_Range==u'\xb5m in nm'")["Device_Identifier"].values):
        # for micrometer instruments with nm x-axis
        ax.set(xscale='log', xticks=[100, 500, 1000, 2000, 5000, 10000], xticklabels=[0.1, 0.5, 1, 2, 5, 10],
               xlabel=u'Particle Diameter / \xb5m',
               ylabel=y_label)
    elif used_device in list(Def.device_list.query("Size_Plot_Range=='nm'")["Device_Identifier"].values):
        # for nanometer instruments SMPS
        ax.set(xscale='log', xticks=[20, 50, 100, 200, 400, 800], xticklabels=[20, 50, 100, 200, 400, 800],
               xlabel='Particle Diameter / nm',
               ylabel=y_label)
    else:
        x_label = input("Please enter the desired x-label as string.")
        y_label = input("Please enter the desired y-label as string.")
        ax.set(xlabel=x_label, ylabel=y_label)
    # yscale='log', xscale='log', xlabel='$\mathregular{dlog D_p}$ / nm', ylabel='dN / $\mathregular{P/cm^3}$'
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    return ax


def plot_singledata(data, scan_nrs, used_C="Cn", colors=Def.fhg_cm, a=1, legend="automatic", save_plot="off"):
    """plots the given data, specify used_C to use "Cn", or "Cn_dlogX" measurement to use"""
    X, dX, C = Sup.extract_from_dict(data, used_C)
    calc_conc = get_conc(data[used_C])
    used_device = data["used_device"]
    plot_nrs = Sup.py_logic_converter(scan_nrs)
    fig, ax = plt.subplots()  # height with title 12, without 10
    C_unit = Sup.decide_C_unit(used_C)
    legend_entries=[]
    ct=0
    if len(plot_nrs) == 1:
        k = plot_nrs[0]
        ax.bar(X[k, :], C[k, :], width=dX[k, :], edgecolor='black', color=colors[0])
        Sup.build_legend(legend_entries, scan_nrs, ct, legend=legend)
        #print(f"scan {scan_nrs[0]} conc. = " + "{:e}".format(float(calc_conc[k])) + C_unit)
    else:
        for k in plot_nrs:
            ax.bar(X[k, :], C[k, :], width=dX[k, :], edgecolor='black', color=colors[ct], alpha=a)
            Sup.build_legend(legend_entries, scan_nrs, ct, legend=legend)
            print(f"scan {k+1} conc. = " + "{:e}".format(float(calc_conc[k])) + C_unit)
            ct += 1
    ax = format_plot(fig, ax, used_C, used_device)
    #plt.rcParams['figure.dpi'] = 600
    #plt.rcParams['savefig.dpi'] = 600
    plt.legend(legend_entries)  # , loc='upper left')
    # move this into format_plot ?
    # scan_nr_fileaddition = f"scan_nr_{['{k}_' for k in scan_nrs]}"
    Sup.save_plot(data, save_plot) #, fileaddition=scan_nr_fileaddition)

    plt.show()
    return ax


def plot_meandata(mean_data, scan_nrs, colors=Def.fhg_cm, a=1):
    """plots the given data, use range(start, end), or a list to specify the measurements to use, these are the indices
    in the given Cn and C arrays"""
    # add a mean of n in a corner of the plot
    used_C = "mean_C"
    mean_X = mean_data["mean_X"]
    mean_dX = mean_data["dX"]
    mean_C = mean_data["mean_C"]
    std_C = mean_data["std_C"]
    mean_conc_n = mean_data["mean_conc"]
    std_conc_n = mean_data["std_conc"]
    mean_dg = mean_data["mean_dg"]
    std_dg = mean_data["std_dg"]
    used_device = mean_data["used_device"]
    plot_nrs = Sup.py_logic_converter(scan_nrs)
    fig, ax = plt.subplots()  # height with title 12, without 10
    legend_entries = []
    for k in plot_nrs:
        ax.bar(mean_X[k, :], mean_C[k, :], width=mean_dX[k, :], edgecolor='black') #yerr=std_C[k, :]
        user_input = input(f"Please enter the legend entry for scan {k+1}")
        legend_entries.append(user_input)
        # legend_entries.append(user_input + " (" + str("{:.2f}".format(float(mean_dg[k]))) + u"\u00B1" +
        #    str("{:.2f}".format(float(std_dg[k]))) + " nm)")
        # legend_entries.append(user_input) # scan_nrs is used here on purpose
    [print(f"measurement {k+1} conc. = " + "{:e}".format(float(mean_conc_n[k])) + u"\u00B1" +
           "{:e}".format(float(std_conc_n[k])) + " P/cm" + u"\u00B3") for k in plot_nrs]

    format_plot(fig, ax, used_C, used_device)

    # maybe add savefig, but then filename must be entered differently as mean data can consist of different input files

    plt.legend(legend_entries)  # , loc='upper left')
    plt.show()
    return ax


def plot_cummdata(data, used_device, scan_nrs):
    """plots the given data, specify measurement to use from sel_Cn array"""
    # seems to work, just needs another axis label to indicate it is cummulative :D
    used_C = "cummCn"
    X = data["X"]
    dX = data["dX"]
    cummCn = data["cummCn"]
    calc_conc_n = data["calc_conc_n"]
    normcummCn = np.zeros_like(cummCn)
    for k in range(len(cummCn)):
        if calc_conc_n[k] > 0:
            normcummCn[k] = cummCn[k]/calc_conc_n[k]
        else:
            normcummCn[k] = cummCn[k]
    plot_nrs = Sup.py_logic_converter(scan_nrs)
    fig, ax = plt.subplots()  # height with title 12, without 10
    if len(plot_nrs) == 1:
        k = plot_nrs[0]
        ax.bar(X[k, :], normcummCn[k, :], width=dX[k, :], edgecolor='black')
        legend_entries = [input(f"Please enter the legend entry for scan {scan_nrs[0]}")]
        # scan_nrs is used here on purpose
        print(f"scan {scan_nrs[0]} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        legend_entries = []
        ct = 0
        for k in plot_nrs:
            ax.bar(X[k, :], normcummCn[k, :], width=dX[k, :], edgecolor='black', alpha=0.5)
            legend_entries.append(input(f"Please enter the legend entry for scan {scan_nrs[ct]}"))
            print(f"scan {scan_nrs[k]} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
            ct += 1
    format_plot(fig, ax, used_C, used_device)
    #plt.rcParams['figure.dpi'] = 600
    #plt.rcParams['savefig.dpi'] = 600
    plt.legend(legend_entries)  # , loc='upper left')
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

# def plot_add_data():


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
