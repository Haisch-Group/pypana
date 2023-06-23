# -*- coding: utf-8 -*-
"""
Script for Particle Data Evaluation
Data has to be imported by the import function suitable for the used Device

Created 2023-05 from SMPS_analysis.py
@written by Kevin Maier (kevin.r.maier@tum.de)

"""

from tkinter import Tk
from tkinter.filedialog import askopenfilename
from matplotlib import ticker
from matplotlib import pyplot as plt
import numpy as np
import math
# from matplotlib import cm as colormap
from scipy import optimize
# import scipy.integrate as integrate


def get_filename():
    """get the filename via UI"""
    Tk().withdraw()
    filename = askopenfilename()
    print(filename)
    return filename


def fileread(filename, used_device):
    """applying the correct import filter according to user choice"""

    if int(used_device) == 0:
        import TSI_SMPS3071_fileread as fr  # ! utf-8 encoding for 3-superscript in the header second to last column
        # P/cm^3 does not work sometimes, just change the ^3 to 3 in the data txt then
    elif int(used_device) == 1:
        import PALAS_SMPS2100_fileread as fr
    else:
        import TSI_APS3321_fileread as fr

    X, bar_width, Cn, time = fr.import_data(filename)
    return X, bar_width, Cn, time


"""X = np.array((nr_scans, nr_bins)), bar_width, Cn = X.shape, time = []"""


def select_data(X, Cn, bar_width, time, scan_nrs):
    """select specific scans from the imported raw data to then process them, scan_nrs defines, which scans to take
    in normal non-pythonian logic (starting count at 1)"""
    sel_Cn = np.zeros((len(scan_nrs), Cn.shape[1]))
    # preallocate the np arrays in the correct size (nr of measurements, nr of measuring data)
    sel_X = np.zeros_like(sel_Cn)
    sel_bar_width = np.zeros_like(sel_Cn)
    sel_time = []
    for k in np.arange(len(scan_nrs)):  # fill the arrays with the selected data
        sel_Cn[k, :] = Cn[scan_nrs[k]-1, :]
        sel_X[k, :] = X[scan_nrs[k]-1, :]
        sel_bar_width[k, :] = bar_width[scan_nrs[k]-1, :]
        sel_time.append(time[scan_nrs[k]-1])
    return sel_Cn, sel_X, sel_bar_width, sel_time


# def mean_up_down(sel_Cn, sel_X, sel_bar_width):
#     """calculates the mean od up and down scan"""
#     # not needed atm
#     n = 2
#     size = sel_Cn.shape
#     nth_len = int(size[0] / n)
#     up_down_Cn = np.zeros(shape=(nth_len, size[1]))
#     up_down_X = np.zeros_like(up_down_Cn)
#     up_down_bar_width = np.zeros_like(up_down_Cn)
#     for k in range(nth_len):
#         up_down_Cn[k, :] = np.mean(sel_Cn[(k*n):((k+1)*n-1), :], axis=0)
#         up_down_X[k, :] = np.mean(sel_X[(k*n):((k+1)*n-1), :], axis=0)
#         up_down_bar_width[k, :] = np.mean(sel_bar_width[(k * n):((k + 1) * n - 1), :], axis=0)
#     return up_down_Cn, up_down_X, up_down_bar_width  # can be used as sel_Cn, sel_X, sel_bar_width


def volume_dist(sel_X, sel_Cn):
    """gives volume concentration per bin in micrometer^3 / m^3"""
    sel_Cv = np.zeros_like(sel_Cn)
    mum_D = np.divide(sel_X, 1000)
    # convert sel_X from nm to micrometers by dividing by 1000
    percubicmeter_Cn = np.multiply(sel_Cn, 10 ** 6)
    # convert sel_Cn to P/m^3
    for k in np.arange(sel_Cn.shape[0]):
        for j in np.arange(sel_Cn.shape[1]):
            sel_Cv[k, j] = (percubicmeter_Cn[k, j] * ((1 / 6) * math.pi * (mum_D[k, j]) ** 3))
    return sel_Cv


def mass_dist(sel_Cv, density):
    """gives mass concentration per bin in mg/m^3, takes g/cm^3 as density input, sel_Cv in micrometer/m^3"""
    densitymgpermum = density*(10**(-9))  # convert the density from g/cm^3 to milligram per cubic micrometer
    sel_Cm = np.multiply(sel_Cv, densitymgpermum)  # last part converts from per cm^3 to per m^3
    return sel_Cm


def get_conc(sel_C):
    """calculate the total concentration for each selected measurement, can be applied to sel_Cn, sel_Cv, or sel_Cm
    call as calc_conc_n = get_conc(sel_Cn) to specify (or Cv, or Cm)"""
    calc_conc = np.zeros(sel_C.shape[0], )  # preallocate the array again
    for k in range(sel_C.shape[0]):  # iteratively fill the array with the sum of all size concentrations
        calc_conc[k, ] = np.nansum(sel_C[k, :])  # np.nansum counts NaN as 0
    return calc_conc


def mean_of_n(sel_C, sel_X, sel_bar_width, nr_mean):
    """calculates a mean of every n consecutive measurements and also gives the standard deviation
    select the desired data in an array before, to correctly work with it, if the number of repetitions was not always n
    only works with more than 3 measurements"""
    # can definitely be shortened by making one function and calling it for the arguments
    n = nr_mean
    size = sel_C.shape
    nth_len = int(size[0]/n)
    mean_C = np.zeros(shape=(nth_len, size[1]))
    std_C = np.zeros_like(mean_C)
    mean_X = np.zeros_like(mean_C)
    mean_bar_width = np.zeros_like(mean_C)
    calc_conc = get_conc(sel_C)
    mean_conc = []
    std_conc = []
    for k in range(nth_len):
        mean_C[k, :] = np.mean(sel_C[(k*n):((k+1)*n-1), :], axis=0)
        std_C[k, :] = np.std(sel_C[(k*n):((k+1)*n-1), :], axis=0)
        mean_X[k, :] = np.mean(sel_X[(k*n):((k+1)*n-1), :], axis=0)
        mean_bar_width[k, :] = np.mean(sel_bar_width[(k * n):((k + 1) * n - 1), :], axis=0)
        mean_conc.append(np.mean(calc_conc[(k * n):((k + 1) * n - 1), ], axis=0))
        std_conc.append(np.std(calc_conc[(k * n):((k + 1) * n - 1), ], axis=0))
    return mean_C, std_C, mean_X, mean_bar_width, mean_conc, std_conc


# def calc_mean_of_n(X, Cn, bar_width, scan_nrs, nr_mean):
#   I KILLED IT ALREADY, TO REVIVE IT COPY FROM SMPS_ANALYSIS.PY
#     """Does the above defined functions in one go and calculates a mean of the n scans given"""
#     sel_Cn, sel_X, sel_bar_width, sel_time = select_data(X, Cn, bar_width, time, scan_nrs)
#     sel_Cv = volume_conc(sel_X, sel_Cn)
#     sel_Cm = mass_conc(sel_X, sel_Cv)
#     calc_conc_n = get_conc(sel_Cn)
#     calc_conc_v = get_conc(sel_Cv)
#     calc_conc_m = get_conc(sel_Cm)
#
#     mean_Cn, std_Cn, mean_X, mean_bar_width, mean_conc, std_conc = mean_of_n(sel_Cn, sel_X, sel_bar_width, nr_mean)
#
#     return mean_Cn, std_Cn, mean_X, mean_bar_width, mean_conc_n, std_conc_n, mean_conc_v, std_conc_v, mean_conc_m, \
#            std_conc_m


def format_plot(fig, ax, used_device):
    cm = 1 / 2.54  # inches to cm
    fig.set_size_inches(18.5 * cm, 10 * cm)
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    if used_device == 2:
        ax.set(xscale='log', xticks=[0.5, 1, 2, 5, 10], xticklabels=[0.5, 1, 2, 5, 10],
               xlabel='Particle Diameter / $\mu$m',  # changed that to go with APS data for a moment
               ylabel='dN/dlogD$_{p}$ / $\mathregular{1/cm^3}$')
    else:
        ax.set(xscale='log', xticks=[20, 50, 100, 200, 400, 800], xticklabels=[20, 50, 100, 200, 400, 800],
               xlabel='Particle Diameter / nm',
               ylabel='dN/dlogD$_{p}$ / $\mathregular{1/cm^3}$')
    # yscale='log', xscale='log', xlabel='$\mathregular{dlog D_p}$ / nm', ylabel='dN / $\mathregular{P/cm^3}$'
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    return


def plot_meandata(mean_X, mean_bar_width, mean_Cn, std_Cn, mean_conc_n, std_conc_n, scan_nrs):
    """plots the given data, use range(start, end), or a list to specify the measurements to use, these are the indices
    in the given Cn and C arrays"""
    plot_nrs = py_logic_converter(scan_nrs)
    fig, ax = plt.subplots()  # height with title 12, without 10
    legend_entries = []
    for k in plot_nrs:
        ax.bar(mean_X[k, :], mean_Cn[k, :], width=mean_bar_width[k, :], yerr=std_Cn[k, :], edgecolor='black')
        legend_entries.append(input(f"Please enter the legend entry for scan {scan_nrs[k]}"))
        # scan_nrs is used here on purpose
    [print(f"measurement {k} conc. = " + "{:e}".format(float(mean_conc_n[k])) + u"\u00B1" +
           "{:e}".format(float(std_conc_n[k])) + " P/cm" + u"\u00B3") for k in plot_nrs]

    format_plot(fig, ax, used_device)

    plt.legend(legend_entries)
    plt.show()
    return ax


def plot_singledata(sel_X, sel_bar_width, sel_Cn, calc_conc_n, scan_nrs):
    """plots the given data, specify measurement to use from sel_Cn array"""
    plot_nrs = py_logic_converter(scan_nrs)
    fig, ax = plt.subplots()  # height with title 12, without 10
    if len(plot_nrs) == 1:
        k = plot_nrs[0]
        ax.bar(sel_X[k, :], sel_Cn[k, :], width=sel_bar_width[k, :], edgecolor='black')
        legend_entries = [input(f"Please enter the legend entry for scan {scan_nrs[k]}")]
        # scan_nrs is used here on purpose
        print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        legend_entries = []
        ct = 0
        for k in plot_nrs:
            ax.bar(sel_X[k, :], sel_Cn[k, :], width=sel_bar_width[k, :], edgecolor='black', alpha=0.5)
            legend_entries.append(input(f"Please enter the legend entry for scan {scan_nrs[ct]}"))
            print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
            ct += 1

    format_plot(fig, ax, used_device)

    plt.legend(legend_entries)
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


def geometric_mean(X, C, conc):
    """calculates the geometric mean from given X, C and conc, can be used with mean_C, or sel_C,
    call mean_dg = geometric_mean(mean_X, mean_C, mean_conc then, or sel_dg = geometric_mean(sel_X, sel_C, calc_conc)"""
    # for lognormal, count median diameter = geometric mean diameter
    # maybe add a check for lognormal
    dg = []
    for k in np.arange(0, C.shape[0]):
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
    for k in np.arange(0, len(conc)):
        sigma_g.append(math.exp(math.sqrt((np.nansum(np.square(np.log(X[k]) - np.log(dg[k]))*C[k]))/
                                         (conc[k]-1))))  # 22-13 in aerosol measurement, kulkarni et.al.
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


def lognormal_fit(X, Cn):
    """fit of a lognormal peak"""
    p0=[1000, 100, 1.2]
    lowerbounds=[0, 10, 0.2]
    upperbounds=[np.inf, 1000, 5]
    popt_lognorm_fit, pcov_lognorm_fit = optimize.curve_fit(lognormal_function, X, Cn, p0=p0,
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


def cut_dist(sel_X, sel_C, sel_bar_width, lowerbound, upperbound, scan_nrs):
    """to cut a part of the spectrum"""
    cut_nrs = py_logic_converter(scan_nrs)
    strt_idx = np.where(sel_X[0] > lowerbound)[0][0]
    end_idx = np.where(sel_X[0] < upperbound)[-1][-1] + 1
    cut_X = np.zeros((len(cut_nrs), len(sel_X[0, strt_idx:end_idx])))
    cut_C = np.zeros((len(cut_nrs), len(sel_C[0, strt_idx:end_idx])))
    cut_bar_width = np.zeros((len(cut_nrs), len(sel_bar_width[0, strt_idx:end_idx])))
    ct = 0
    for k in cut_nrs:
        cut_X[ct, :] = sel_X[k, strt_idx:end_idx]
        cut_C[ct, :] = sel_C[k, strt_idx:end_idx]
        cut_bar_width[ct, :] = sel_bar_width[k, strt_idx:end_idx]
        ct += 1
    return cut_X, cut_C, cut_bar_width


def py_logic_converter(nr_list):
    py_nr_list = []
    [py_nr_list.append(i - 1) for i in nr_list]
    return py_nr_list


# def save_values(filename, calc_conc_n):
#     """function, that saves all the important values (median, sigma, conc) to a csv or txt"""
#     savefile = f"{filename[0:-4]}_savedata.xlsx"
#     return


if __name__ == "__main__":

    """data import"""
    filename = get_filename()
    used_device = 1  # input("Which instrument did you use, type 0 for TSI SMPS 3081, 1 for PALAS SMPS 2100 and 2 for TSI
    # APS 3321")
    X, bar_width, Cn, time = fileread(filename, used_device)
    # data_identifier = {"X": X, "Cn": Cn, "bar_width": bar_width, "time": time} # set identifier as desired e.g. date

    """data selection"""
    # scan_nrs = list(range(1, 26))  # actual scan numbers in non-pythonian logic + 1 in the end due to range()
    # scan_nrs = [1, 3, 5,9, 12] # as alternative
    # sel_Cn, sel_X, sel_bar_width, sel_time = select_data(X, Cn, bar_width, time, scan_nrs)
    # print(f"selected scan_nrs: {scan_nrs}")

    """calculation of volume and mass distributions"""
    # density = 1  # in g/cm^3
    # sel_Cv = volume_dist(sel_X, sel_Cn)
    # sel_Cm = mass_dist(sel_Cv, density)
    # print(f"mass distribution with density = {density} g/cm^3 calculated"

    """cut size distribution"""
    # lowerbound = 100 #in the unit, the size data are saved by the instrument e.g. nm
    # upperbound = 350
    # cut_nrs = [1, 5, 7, 15]  # cut_nrs in []
    # cut_X, cut_Cn, cut_bar_width = cut_dist(sel_X, sel_Cn, sel_bar_width, lowerbound, upperbound, cut_nrs)

    """calculation of concentration"""
    # calc_conc_n = get_conc(sel_Cn)
    # calc_conc_v = get_conc(sel_Cv)
    # calc_conc_m = get_conc(sel_Cm)

    """mean of data"""
    # nr_mean = 1
    # print(f"mean of: {nr_mean} calculated")

    """calculation of geometric parameters"""
    # dg, sigma_g = calc_geometry(sel_X, sel_Cn, calc_conc_n, sel_bar_width)
    # dg, sigma_g = calc_geometry(mean_X, mean_Cn, mean_conc_n, mean_bar_width)
    # print(f'median = {dg}, sigma = {sigma_g}')
    # if conc is 0 an error will be displayed

    """plotting of data"""
    # plot_nrs = [1, 5, 7, 15]  # or list(range(1, 7))
    # print(f"Plotted scan numbers: {plot_nrs}")
    # ax1 = plot_singledata(sel_X, sel_bar_width, sel_Cn, calc_conc_n, plot_nrs)
    # ax1 = plot_meandata(mean_X, mean_bar_width, mean_Cn, std_Cn, mean_conc_n, std_conc_n, plot_nrs)
    # ax2 = plot_singledata(cut_X, cut_bar_width, cut_Cn, calc_conc_n, plot_nrs)
    # if only a selection of distributions was cut with e.g. cut_nrs = [1, 5, 7, 15], counting for the plot of the cut
    # distributions has to start at 1, if all distributions were cut, the scan_nrs can be used as plot_nrs

    """other calls"""
    # ax1.plot(mean_X[measurement_nr], fit[measurement_nr])
    # print(dg)
    # print(sigma_g)

    # plt.ioff()
    # plt.show() # if plot doesnt show!