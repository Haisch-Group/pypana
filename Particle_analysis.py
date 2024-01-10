# -*- coding: utf-8 -*-
"""
Script for Particle Data Evaluation
Data has to be imported by the import function suitable for the used Device

Created 2023-05 from SMPS_analysis.py
@written by Kevin Maier (kevin.r.maier@tum.de)

"""

from get_filename import get_filename
from matplotlib import ticker
from matplotlib import pyplot as plt
import numpy as np
import math
from scipy import optimize
import pandas as pd
from py_logic_converter import py_logic_converter, normal_logic_converter
# import scipy.integrate as integrate
# from matplotlib import cm as colormap


def fileread(filename, used_device):
    """applying the correct import filter according to user choice and importing data as
    X = np.array((nr_scans, nr_bins)), bar_width, Cn = X.shape, time = []"""
    if int(used_device) == 0:
        import TSI_SMPS3071_fileread as fr  # ! utf-8 encoding for 3-superscript in the header second to last
        # column P/cm^3 does not work sometimes, just change the ^3 to 3 in the data txt then
    elif int(used_device) == 1:
        import PALAS_SMPS2100_fileread as fr
    elif int(used_device) == 2:
        import TSI_LAS3340A_fileread as fr
    elif int(used_device) == 3:
        import TSI_APS3321_fileread as fr
    else:
        print(f"Device {used_device} is not a viable option")  # could be integrated after the input(used_device)

    X, bar_width, Cn, time = fr.import_data(filename)
    return X, bar_width, Cn, time


def get_data():
    filename = get_filename()
    used_device = input("Which instrument did you use, type 0 for TSI SMPS 3081, 1 for PALAS SMPS 2100, 2 for "
                        "TSI LAS 3340A and 3 for TSI APS 3321, enter as int.")
    #while user_input := input("Which instrument did you use, type 0 for TSI SMPS 3081, 1 for PALAS SMPS 2100, 2 for "
    #                        "TSI LAS 3340A and 3 for TSI APS 3321, enter as int.") not in [0, 1, 2, 3]:
    #    print(f"{user_input} is not a valid input.")
    #    continue
    #used_device = user_input

    X, bar_width, Cn, time = fileread(filename, used_device)
    scan_nr = []
    [scan_nr.append(k+1) for k in range(len(X))]
    data = {"X": X, "Cn": Cn, "bar_width": bar_width,
            "time": time, "scan_nr": scan_nr, "filename": filename, "used_device": used_device}
    return data


def select_data(data, sel_nrs):  # merge with cut_dist ?
    """select specific scans from the imported raw data to then process them, scan_nrs defines, which scans to take
    in normal non-pythonian logic (starting count at 1)
    can only easily select data from one day for comparison"""
    scan_nrs = py_logic_converter(sel_nrs)
    sel_Cn = np.zeros((len(scan_nrs), data["Cn"].shape[1]))
    # preallocate the np arrays in the correct size (nr of measurements, nr of measuring data)
    sel_X = np.zeros_like(sel_Cn)  # maybe nan is needed to avoid zeros on the right of the x-data?
    sel_bar_width = np.zeros_like(sel_Cn)
    sel_time = []
    sel_scan_nr = []
    sel_filename = data["filename"]  # should be defined as list or array, when making a function to select from
    # different datasets
    sel_used_device = data["used_device"]
    for k in np.arange(len(scan_nrs)):  # fill the arrays with the selected data
        sel_Cn[k, :] = data["Cn"][scan_nrs[k], :]
        sel_X[k, :] = data["X"][scan_nrs[k], :]
        sel_bar_width[k, :] = data["bar_width"][scan_nrs[k], :]
        sel_time.append(data["time"][scan_nrs[k]])
        sel_scan_nr.append(data["scan_nr"][scan_nrs[k]])
    sel_data = {"X": sel_X, "Cn": sel_Cn, "bar_width": sel_bar_width, "time": sel_time, "scan_nr": sel_scan_nr,
                "filename": sel_filename, "used_device": sel_used_device}
    typical_calculations(sel_data)
    return sel_data


def get_conc(C):
    """calculate the total concentration for each selected measurement, can be applied to Cn, Cv, or Cm
    call for example as data["calc_conc_n"] = get_conc(data["Cn"]) to specify (or Cv, or Cm)"""
    calc_conc = np.zeros(C.shape[0], )  # preallocate the array again
    for k in range(C.shape[0]):  # iteratively fill the array with the sum of all size concentrations
        calc_conc[k, ] = np.nansum(C[k, :])  # np.nansum counts NaN as 0
    return calc_conc


def cut_dist(X, C, bar_width, lowerbound, upperbound, scan_nrs):  # merge with select_data
    """to cut a part of the spectrum"""
    cut_nrs = py_logic_converter(scan_nrs)
    strt_idx = np.where(X[0] > lowerbound)[0][0]
    end_idx = np.where(X[0] < upperbound)[-1][-1] + 1
    cut_X = np.zeros((len(cut_nrs), len(X[0, strt_idx:end_idx])))
    cut_C = np.zeros((len(cut_nrs), len(C[0, strt_idx:end_idx])))
    cut_bar_width = np.zeros((len(cut_nrs), len(bar_width[0, strt_idx:end_idx])))
    cut_conc = []
    ct = 0
    for k in cut_nrs:
        cut_X[ct, :] = X[k, strt_idx:end_idx]
        cut_C[ct, :] = C[k, strt_idx:end_idx]
        cut_bar_width[ct, :] = bar_width[k, strt_idx:end_idx]
        cut_conc = np.nansum(cut_C[ct, :])
        ct += 1
    return cut_X, cut_C, cut_bar_width, cut_conc # write into dict


def merge_data(sel_data_list):
    """merges dictionaries of data, should best be used with selected data dicts
    currently also writes into the first dict it takes data from???"""
    merged_data = {}
    merged_data["X"] = sel_data_list[0]["X"]
    merged_data["Cn"] = sel_data_list[0]["Cn"]
    merged_data["bar_width"] = sel_data_list[0]["bar_width"]
    merged_data["time"] = sel_data_list[0]["time"][:]
    merged_data["scan_nr"] = sel_data_list[0]["scan_nr"][:]
    merged_data["origin"] = []
    [merged_data["origin"].append(sel_data_list[0]["filename"]) for k in range(len(sel_data_list[0]["scan_nr"]))]
    for i in sel_data_list[1:]:
        merged_data["X"] = np.append(merged_data["X"], i["X"], axis=0)
        merged_data["Cn"] = np.append(merged_data["Cn"], i["Cn"], axis=0)
        merged_data["bar_width"] = np.append(merged_data["bar_width"], i["bar_width"], axis=0)
        for k in range(len(i["scan_nr"])):
            merged_data["time"].append(i["time"][k])
            merged_data["scan_nr"].append(i["scan_nr"][k])
            merged_data["origin"].append(i["filename"])
    return merged_data


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
            dg.append(math.exp((1/conc[k]) * np.nansum(np.log(X[k])*C[k])))
            # gives seemingly correct results
            # dg.append(math.pow(10, ((1 / mean_conc_n[k]) * np.nansum(np.log10(mean_X[k]) * mean_Cn[k]))))
            # same result as above
            # dg.append(np.nansum(np.multiply(mean_Cn[k], mean_X[k])) / np.nansum(mean_Cn[k]))
            # gives bit higher dg that seems wrong
    return dg  # seems to work


def geometric_std(X, C, conc, dg):
    """calculates the geometric standard deviation from given X, C and conc, can be used with mean_C, or sel_C,
        call mean_sigma_g = geometric_std(mean_X, mean_C, mean_conc, mean_dg then,
        or sel_sigma_g = geometric_std(sel_X, sel_C, calc_conc, sel_dg)"""
    sigma_g = []
    for k in range(0, len(conc)):  # gave a math error for conc < 1 because conc-1 in sigma_g is < 0 then, so division
        #  is not possible
        if conc[k] < 1:
            sigma_g.append(np.inf) # is infinity correct here? should it just be a massiv value?
        else:
            sigma_g.append(math.exp(math.sqrt((np.nansum(np.square(np.log(X[k])
                                                                   - np.log(dg[k]))*C[k]))/(conc[k]-1))))
            # 22-13 in aerosol measurement, Kulkarni et.al.  # 20230705 changed /conc to /np.nansum(C[k]-1)
        #sigma_g.append(math.pow(10, (math.sqrt((np.nansum(np.square(np.log10(mean_X[k]) - np.log10(dg[k])) *
        #                                                  mean_Cn[k])) / (mean_conc_n[k] - 1)))))
        # same result as above
    return sigma_g


def lognormal_dist(conc, sigma_g, dg, X, bar_width):
    """calculates a normal distribution based on the concentration, the median diameter and the geometric standard
    deviation"""
    fit = np.zeros_like(X)
    for k in np.arange(0, X.shape[0]):
        #fit[k, :] = (mean_conc_n[k] / (math.sqrt(2 * math.pi) * np.log(sigma_g[k]))) * \
        #            np.exp((-np.square(np.log(mean_X[k, :]) - np.log(dg[k]))) / (2 * (math.log(sigma_g[k])) ** 2))
        # is roughly 28 times higher than the histogram
        fit[k, :] = ((conc[k]/bar_width[k])/(math.sqrt(2 * math.pi) * np.log(sigma_g[k])))*\
                    np.exp((-np.square(np.log(X[k, :])-np.log(dg[k])))/(2*(math.log(sigma_g[k]))**2))
        # did not do what i wanted it to
        # fit[k, :] = ((mean_conc_n[k] / mean_X.shape[0]) / (math.sqrt(2 * math.pi) * np.log10(sigma_g[k]))) * \
        #            np.power(10, ((-np.square(np.log10(mean_X[k, :]) - np.log10(dg[k]))) /
        #                          (2 * (math.log10(sigma_g[k])) ** 2)))
        # gives more narrow distribution than with natural base
        # fit[k, :] = (1 / (math.sqrt(2 * math.pi) * np.log(sigma_g[k]))) * \
        #             np.exp((-np.square(np.log(mean_X[k, :]) - np.log(dg[k]))) / (2 * (math.log(sigma_g[k])) ** 2))

    return fit


def lognormal_function(x, A, m, sigma):
    """definition of a log-normal function with A being a scale factor, m being the median and sigma being the geometric
    standard deviation"""
    return A*(np.exp(-((np.log(x/m))**2)/(2*np.log(sigma)**2))/(np.log(sigma)*x*np.sqrt(2*math.pi)))


def normal_function(x, A, mu, sigma):
    """definition of a normal function with A being a scale factor, mu being the median and sigma being the geometric
    standard deviation"""
    return A*np.exp(-((x-mu)**2)/(2*sigma**2))/(sigma*np.sqrt(2*math.pi))


def lognormal_fit(X, C):
    """fit of a lognormal peak"""
    p0=[1000, 100, 1.2]
    lowerbounds=[0, 10, 0.2]
    upperbounds=[np.inf, 1000, 5]
    popt_lognorm_fit, pcov_lognorm_fit = optimize.curve_fit(lognormal_function, X, C, p0=p0,
                                                            bounds=(lowerbounds, upperbounds), maxfev=1000)
    A_fit=popt_lognorm_fit[0]
    m_fit=popt_lognorm_fit[1]
    sigma_fit=popt_lognorm_fit[2]
    Cn_fit=lognormal_function(X, *popt_lognorm_fit)
    return A_fit, m_fit, sigma_fit ,Cn_fit


def calc_geometry(X, C, conc, bar_width):
    """calculates geometric parameters of the distributions"""
    dg = geometric_mean(X, C, conc)   # spectra by using sel_X, sel_Cn, calc_conc_n, sel_bar_width
    sigma_g = geometric_std(X, C, conc, dg)
    #fit = lognormal_dist(conc, sigma_g, dg, X, bar_width)
    return dg, sigma_g#, fit


def cumulative_distribution(C):
    """calculates the cumulative distribution"""  # tested, first column = Cn[0], last column = calc_conc_n
    cummC = np.zeros_like(C)
    for scan in range(len(C)):
        cummC[scan, 0] = C[scan, 0]
        for k in range(1, len(C[scan])):
            cummC[scan, k] = cummC[scan, k-1] + C[scan, k]
    return cummC


def cumulative_diameters(X, cummC):
    """calculates the diameters below which 10, 16, 50, 84 and 90 % of all particles are"""
    # seemingly works, at least X50 were similar to PDAnalyze X50 values, but slightly different, as i just give the
    # middle X value of the bin, maybe PALAS does some other magic with it like calculating a discrete distribution
    X10 = []
    X16 = []
    X50 = []
    X84 = []
    X90 = []
    for k in range(len(cummC)):
        X10.append(X[k][next((index for index, val in enumerate(cummC[k]) if val > cummC[k][-1]*0.1), 0)])
        X16.append(X[k][next((index for index, val in enumerate(cummC[k]) if val > cummC[k][-1]*0.16), 0)])
        X50.append(X[k][next((index for index, val in enumerate(cummC[k]) if val > cummC[k][-1]*0.5), 0)])
        X84.append(X[k][next((index for index, val in enumerate(cummC[k]) if val > cummC[k][-1]*0.84), 0)])
        X90.append(X[k][next((index for index, val in enumerate(cummC[k]) if val > cummC[k][-1]*0.9), 0)])
    return X10, X16, X50, X84, X90


def typical_calculations(data):
    data["calc_conc_n"] = get_conc(data["Cn"])
    data["dg"], data["sigma"] = calc_geometry(data["X"], data["Cn"], data["calc_conc_n"], data["bar_width"])
    return data


def mean_of_n(data, nr_mean):
    """calculates a mean of every n consecutive measurements and also gives the standard deviation
    select the desired data in an array before, to correctly work with it, if the number of repetitions was not always n
    only works with more than 3 measurements"""
    C = data["Cn"]
    X = data["X"]
    bar_width = data["bar_width"]
    calc_conc = data["calc_conc_n"]
    dg = data["dg"]
    sigma = data["sigma"]
    n = nr_mean
    size = C.shape
    nth_len = int(size[0]/n)
    mean_C = np.zeros(shape=(nth_len, size[1]))  # np.nans?
    std_C = np.zeros_like(mean_C)
    mean_X = np.zeros_like(mean_C)
    mean_bar_width = np.zeros_like(mean_C)
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
        mean_bar_width[k, :] = np.mean(bar_width[(k * n):((k + 1) * n), :], axis=0)
        mean_conc.append(np.mean(calc_conc[(k * n):((k + 1) * n), ], axis=0))
        std_conc.append(np.std(calc_conc[(k * n):((k + 1) * n), ], axis=0))
        mean_dg.append(np.mean(dg[(k * n):((k + 1) * n)], axis=0))
        std_dg.append(np.std(dg[(k * n):((k + 1) * n)], axis=0))
        mean_sigma.append(np.mean(sigma[(k * n):((k + 1) * n)], axis=0))
        std_sigma.append(np.std(sigma[(k * n):((k + 1) * n)], axis=0))
    mean_data = {"mean_X": mean_X, "mean_C": mean_C, "std_C": std_C, "bar_width": mean_bar_width,
                 "mean_conc": mean_conc, "std_conc": std_conc, "mean_dg": mean_dg,"std_dg":std_dg,
                 "mean_sigma": mean_sigma, "std_sigma": std_sigma}
    return mean_data


def merge_mean_data(mean_data_list):
    """merges dictionaries of data, should best be used with mean data dicts
    currently also writes into the first dict it takes data from???"""
    merged_mean_data = {}
    merged_mean_data["mean_X"] = mean_data_list[0]["mean_X"]
    merged_mean_data["mean_C"] = mean_data_list[0]["mean_C"]
    merged_mean_data["std_C"] = mean_data_list[0]["std_C"]
    merged_mean_data["bar_width"] = mean_data_list[0]["bar_width"]
    merged_mean_data["mean_conc"] = mean_data_list[0]["mean_conc"][:]
    merged_mean_data["std_conc"] = mean_data_list[0]["std_conc"][:]
    merged_mean_data["mean_dg"] = mean_data_list[0]["mean_dg"][:]
    merged_mean_data["std_dg"] = mean_data_list[0]["std_dg"][:]
    for i in mean_data_list[1:]:
        merged_mean_data["mean_X"] = np.append(merged_mean_data["mean_X"], i["mean_X"], axis=0)
        merged_mean_data["mean_C"] = np.append(merged_mean_data["mean_C"], i["mean_C"], axis=0)
        merged_mean_data["std_C"] = np.append(merged_mean_data["std_C"], i["std_C"], axis=0)
        merged_mean_data["bar_width"] = np.append(merged_mean_data["bar_width"], i["bar_width"], axis=0)
        merged_mean_data["mean_conc"].extend(i["mean_conc"])
        merged_mean_data["std_conc"].extend(i["std_conc"])
        merged_mean_data["mean_dg"].extend(i["mean_dg"])
        merged_mean_data["std_dg"].extend(i["std_dg"])
    return merged_mean_data


def typical_calculation_mean(data):
    data["calc_conc_n"] = get_conc(data["mean_C"])
    data["dg"], data["sigma"] = calc_geometry(data["mean_X"], data["mean_C"], data["calc_conc_n"], data["bar_width"])
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


def format_plot(fig, ax, used_device):
    cm = 1 / 2.54  # inches to cm
    fig.set_size_inches(18.5 * cm, 10 * cm)
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    if used_device == 2 or used_device == 3:
        ax.set(xscale='log', xticks=[0.5, 1, 2, 5, 10], xticklabels=[0.5, 1, 2, 5, 10],
               xlabel='Particle Diameter / $\mu$m',  # changed that to go with APS data for a moment
               ylabel='Number Concentration / $\mathregular{1/cm^3}$')
    else:
        ax.set(xscale='log', xticks=[20, 50, 100, 200, 400, 800], xticklabels=[20, 50, 100, 200, 400, 800],
               xlabel='Particle Diameter / nm',
               ylabel='Number Concentration / $\mathregular{1/cm^3}$') # dN/dlogD$_{p}$
    # yscale='log', xscale='log', xlabel='$\mathregular{dlog D_p}$ / nm', ylabel='dN / $\mathregular{P/cm^3}$'
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    return


def plot_singledata(data, used_device, scan_nrs):
    """plots the given data, specify measurement to use from sel_Cn array"""
    X = data["X"]
    bar_width = data["bar_width"]
    Cn = data["Cn"]
    calc_conc_n = data["calc_conc_n"]
    plot_nrs = py_logic_converter(scan_nrs)
    fig, ax = plt.subplots()  # height with title 12, without 10
    if len(plot_nrs) == 1:
        k = plot_nrs[0]
        ax.bar(X[k, :], Cn[k, :], width=bar_width[k, :], edgecolor='black')
        legend_entries = [input(f"Please enter the legend entry for scan {scan_nrs[0]}")]
        # scan_nrs is used here on purpose
        print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        legend_entries = []
        ct = 0
        for k in plot_nrs:
            ax.bar(X[k, :], Cn[k, :], width=bar_width[k, :], edgecolor='black', alpha=0.5)
            legend_entries.append(input(f"Please enter the legend entry for scan {scan_nrs[ct]}"))
            print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
            ct += 1
    format_plot(fig, ax, used_device)
    #plt.rcParams['figure.dpi'] = 600
    #plt.rcParams['savefig.dpi'] = 600
    plt.legend(legend_entries, loc='upper left')
    plt.show()
    return ax


def plot_meandata(mean_data, used_device, scan_nrs):
    """plots the given data, use range(start, end), or a list to specify the measurements to use, these are the indices
    in the given Cn and C arrays"""
    # add a mean of n in a corner of the plot
    mean_X = mean_data["mean_X"]
    mean_bar_width = mean_data["bar_width"]
    mean_C = mean_data["mean_C"]
    std_C = mean_data["std_C"]
    mean_conc_n = mean_data["mean_conc"]
    std_conc_n = mean_data["std_conc"]
    mean_dg = mean_data["mean_dg"]
    std_dg = mean_data["std_dg"]
    plot_nrs = py_logic_converter(scan_nrs)
    fig, ax = plt.subplots()  # height with title 12, without 10
    legend_entries = []
    for k in plot_nrs:
        ax.bar(mean_X[k, :], mean_C[k, :], width=mean_bar_width[k, :], yerr=std_C[k, :], edgecolor='black')
        user_input = input(f"Please enter the legend entry for scan {k+1}")
        legend_entries.append(user_input + " (" + str("{:.2f}".format(float(mean_dg[k]))) + u"\u00B1" +
           str("{:.2f}".format(float(std_dg[k]))) + " nm)")
        # legend_entries.append(user_input) # scan_nrs is used here on purpose
    [print(f"measurement {k+1} conc. = " + "{:e}".format(float(mean_conc_n[k])) + u"\u00B1" +
           "{:e}".format(float(std_conc_n[k])) + " P/cm" + u"\u00B3") for k in plot_nrs]

    format_plot(fig, ax, used_device)

    plt.legend(legend_entries, loc='upper left')
    plt.show()
    return ax


def plot_cummdata(data, used_device, scan_nrs):
    """plots the given data, specify measurement to use from sel_Cn array"""
    # seems to work, just needs another axis label to indicate it is cummulative :D
    X = data["X"]
    bar_width = data["bar_width"]
    cummCn = data["cummCn"]
    calc_conc_n = data["calc_conc_n"]
    normcummCn = np.zeros_like(cummCn)
    for k in range(len(cummCn)):
        if calc_conc_n[k] > 0:
            normcummCn[k] = cummCn[k]/calc_conc_n[k]
        else:
            normcummCn[k] = cummCn[k]
    plot_nrs = py_logic_converter(scan_nrs)
    fig, ax = plt.subplots()  # height with title 12, without 10
    if len(plot_nrs) == 1:
        k = plot_nrs[0]
        ax.bar(X[k, :], normcummCn[k, :], width=bar_width[k, :], edgecolor='black')
        legend_entries = [input(f"Please enter the legend entry for scan {scan_nrs[0]}")]
        # scan_nrs is used here on purpose
        print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        legend_entries = []
        ct = 0
        for k in plot_nrs:
            ax.bar(X[k, :], normcummCn[k, :], width=bar_width[k, :], edgecolor='black', alpha=0.5)
            legend_entries.append(input(f"Please enter the legend entry for scan {scan_nrs[ct]}"))
            print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
            ct += 1
    format_plot(fig, ax, used_device)
    #plt.rcParams['figure.dpi'] = 600
    #plt.rcParams['savefig.dpi'] = 600
    plt.legend(legend_entries, loc='upper left')
    plt.show()
    return ax


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


"""ToDo:"""

# Vorschlag Nico: Median als senkrechte Linie / Marker in den Plot einbauen

# save funktion die dict zu einfacherer struktur macht, evtl. in form ähnlich zu PALAS Daten?
#   filename, scan_nr ,time, used_device, calc_conc_n, dg, sigma # everything that is only one item per measurement
#   X...
#   Cn...
#   bar_width...
#   ... # everything, that is an array element in one line
# kann dann als csv gespeichert werden, oder gepicklet, oder gejsont?

# just a code sniplet, that could be used to automatically import multiple datasets at once
#   naming variables automatically and getting them out of a function does not work though
#   input_name = input("Enter a name for the data you are importing (has to start with a letter)")
#   locals()[input_name] = data

# check, where Cn and where C makes sense as variable name
# all processes , like select, merge, etc. can be done with Cn, then the data can be converted to Cv and Cm
# -> change mean_C to "Cn" in mean function
# after that, dg, sigma etc. can be calculated with Cn, Cv, or Cm alike
# add plot option for Cv and Cm in format plot function depending on one variable

# integrate CPC_analysis.py? -> make particle_analysis.py the master file that runs functions from CPC_analysis
# (maybe renamed to count_analysis?) and the functions now used for SMPS analysis in a new file maybe named
# dist_analysis


if __name__ == "__main__":

    # transfer this to wiki

    # 1. run particle_analysis.py
    # Hallo

    """data import - imports one file at a time to a dictionary"""

    # 2. data_identifier = get_data() # change identifier to something that identifies the dataset, like a date

    """typical calculations - calculates number concentration, geometric mean and standard deviation and adds them to
    the data dictionary"""
    # typical_calculations(data);

    """calculation of concentration"""
    # 3. data_identifier["calc_conc_n"] = get_conc(data_identifier["Cn"]
    # calc_conc_n = get_conc(Cn)
    # calc_conc_v = get_conc(Cv)
    # calc_conc_m = get_conc(Cm)

    """data selection"""
    # scan_nrs = list(range(1, 26))  # actual scan numbers in non-pythonian logic + 1 in the end due to range()
    # 4. scan_nrs = [1, 3, 5, 9, 12] # as alternative
    # 5. sel_data = select_data(data, scan_nrs) # enter scan_nrs manually in a list (name identifier)
    # 6. sel_data["conc"] = get_conc(sel_data["Cn"])
    # print(f"selected scan_nrs: {scan_nrs}")

    """calculation of volume and mass distributions"""
    # density = 1  # in g/cm^3
    # data["Cv"] = volume_dist(data["X"], data["Cn"])
    # data["Cm"] = mass_dist(data["Cv"], density)
    # print(f"mass distribution with density = {density} g/cm^3 calculated"

    """cut size distribution"""
    # lowerbound = 100 #in the unit, the size data are saved by the instrument e.g. nm
    # upperbound = 350
    # cut_nrs = [1, 5, 7, 15]  # cut_nrs in []
    # cut_X, cut_Cn, cut_bar_width = cut_dist(sel_data["X"], sel_data["Cn"], sel_data["bar_width"], lowerbound,
    # upperbound, cut_nrs)

    """mean of data - data have to be selected before"""
    # 7. nr_mean = 1
    # 8. mean_C, std_C, mean_X, mean_bar_width, mean_conc, std_conc = mean_of_n(data_identifier["C"],
    #   data_identifier["X"], data_identifier["bar_width"], nr_mean)
    # print(f"mean of: {nr_mean} calculated")

    """calculation of geometric parameters"""
    # data_identifier["dg", "sigma_g"] = calc_geometry(data_identifier["X"], data_identifier["Cn"],
    # data_identifier["calc_conc_n"], data_identifier["bar_width"])

    # dg, sigma_g = calc_geometry(X, Cn, calc_conc_n, sel_bar_width)
    # dg, sigma_g = calc_geometry(mean_X, mean_Cn, mean_conc_n, mean_bar_width)
    # print(f'median = {dg}, sigma = {sigma_g}')
    # if conc is 0 an error will be displayed

    """plotting of data"""
    # plot_nrs = [1, 5, 7, 15]  # or list(range(1, 7))
    # print(f"Plotted scan numbers: {plot_nrs}")
    # ax1 = plot_singledata(sel_X, sel_bar_width, sel_Cn, calc_conc_n, plot_nrs)
    # 9. ax1 = plot_singledata(data_identifier["X"], data_identifier["bar_width"], data_identifier["Cn"],
    #   data_identifier["calc_conc_n"], used_device, scan_nrs) # [1,4,7,9]

    # ax2 = plot_singledata(cut_X, cut_bar_width, cut_Cn, calc_conc_n, plot_nrs)
    # if only a selection of distributions was cut with e.g. cut_nrs = [1, 5, 7, 15], counting for the plot of the cut
    # distributions has to start at 1, if all distributions were cut, the scan_nrs can be used as plot_nrs

    # 9. ax1 = plot_meandata(mean_X, mean_bar_width, mean_C, std_C, mean_conc, std_conc, used device, plot_nrs)

    # save_calc_to_csv(data_identifier, ["scan_nr", "time", "dg", "sigma", "calc_conc_n"], fileaddition="_particleDF")

    """other calls"""
    # ax1.plot(mean_X[measurement_nr], fit[measurement_nr])
    # print(dg)
    # print(sigma_g)
    # x_mean, x_std = mean_and_std(sel_data["dg"][:])

    # plt.ioff()
    # plt.show() # if plot doesnt show!
