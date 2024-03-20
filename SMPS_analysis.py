# -*- coding: utf-8 -*-
"""
Script for SMPS Data Evaluation
Data has to be imported by the import function suitable for the used SMPS

Created 2022-01-18 to 2022-01-20
@written by Kevin Maier (kevin.r.maier@tum.de)

modified functions from oldSMPS_fileread_v1 and added functions for statistical evaluation
    function set:   fileread
                    select_data
                    mean_up_down
                    volume_conc
                    mass_conc
                    get_conc
                    mean_of_n
                    plot_meandata
                    geometric_mean
                    geometric_std
                    lognormal_dist
2022-02-10: plot_singledata
2022-03-03: now works with oldSMPS_fileread_v3 as well
2022-03-23: added plot_3Dsingledata
2022-07-20: changed lognormal dist function
2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number
2023-01-19: filename is retrieved from SMPS_analysis now and printed in console to save it with console input

Possible changes:
    write concentration data to csv automatically
"""

from Sup import get_filename
from matplotlib import ticker
from matplotlib import pyplot as plt
import numpy as np
import math
from matplotlib import cm as colormap
from scipy import optimize
import scipy.integrate as integrate


def fileread(filename):
    """just a very fast function for applying the correct import filter according to user choice"""
    used_smps = input("Which instrument did you use, type 0 for TSI SMPS 3081, 1 for PALAS SMPS 2100 and 2 for TSI APS "
                      "3321")
    #used_smps = 1

    if int(used_smps) == 0:
        import TSI_SMPS3071_fileread as fr  # ! utf-8 encoding for 3-superscript in the header second to last column P/cm^3
        # does not work sometimes, just change the ^3 to 3 in the data txt then
    elif int(used_smps) == 1:
        import PALAS_SMPS2100_fileread as fr
    else:
        import TSI_APS3321_fileread as fr

    # filename = fr.get_filename()
    X, bar_width, Cn, time = fr.import_data(filename)
    # somehow, when using the function twice, to import one old and one new smps file, it does not update fr,
    # but tries to use the fileread script used before
    # -> :D it always chose the else, as the input is string which does not work with == 0
    return X, bar_width, Cn, time


"""X = np.array((nr_scans, nr_bins)), bar_width, Cn = X.shape, time = []"""


def select_data(X, Cn, bar_width, scan_nrs):
    """select specific SMPS scans from the imported raw data to then process them, scan_nrs defines, which scans to take
    in normal non-pythonian logic (starting count at 1)"""
    sel_Cn = np.zeros((len(scan_nrs), Cn.shape[1]))
    # preallocate the np arrays in the correct size (nr of measurements, nr of measuring data)
    sel_X = np.zeros_like(sel_Cn)
    sel_bar_width = np.zeros_like(sel_Cn)
    for k in np.arange(len(scan_nrs)):  # fill the arrays with the selected data
        sel_Cn[k, :] = Cn[scan_nrs[k]-1, :]
        sel_X[k, :] = X[scan_nrs[k]-1, :]
        sel_bar_width[k, :] = bar_width[scan_nrs[k]-1, :]
    return sel_Cn, sel_X, sel_bar_width


def mean_up_down(sel_Cn, sel_X, sel_bar_width):
    """calculates the mean od up and down scan"""
    # not needed atm
    n = 2
    size = sel_Cn.shape
    nth_len = int(size[0] / n)
    up_down_Cn = np.zeros(shape=(nth_len, size[1]))
    up_down_X = np.zeros_like(up_down_Cn)
    up_down_bar_width = np.zeros_like(up_down_Cn)
    for k in range(nth_len):
        up_down_Cn[k, :] = np.mean(sel_Cn[(k*n):((k+1)*n-1), :], axis=0)
        up_down_X[k, :] = np.mean(sel_X[(k*n):((k+1)*n-1), :], axis=0)
        up_down_bar_width[k, :] = np.mean(sel_bar_width[(k * n):((k + 1) * n - 1), :], axis=0)
    return up_down_Cn, up_down_X, up_down_bar_width  # can be used as sel_Cn, sel_X, sel_bar_width


def volume_conc(sel_X, sel_Cn):
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


def mass_conc(sel_Cv, density):
    """gives mass concentration per bin in mg/m^3, takes g/cm^3 as density input, sel_Cv in micrometer/m^3"""
    densitymgpermum = density*(10**(-9))  # convert the density from g/cm^3 to milligram per cubic micrometer
    sel_Cm = np.multiply(sel_Cv, densitymgpermum)  # last part converts from per cm^3 to per m^3
    return sel_Cm


def get_conc(sel_Cn, sel_Cv, sel_Cm):
    """calculate the total concentration for each selected measurement"""
    calc_conc_n = np.zeros(sel_Cn.shape[0], )  # preallocate the array again
    calc_conc_v = np.zeros_like(calc_conc_n)
    calc_conc_m = np.zeros_like(calc_conc_n)
    for k in range(sel_Cn.shape[0]):  # iteratively fill the array with the sum of all size concentrations
        calc_conc_n[k, ] = np.nansum(sel_Cn[k, :])  # np.nansum counts NaN as 0
        calc_conc_v[k, ] = np.nansum(sel_Cv[k, :])
        calc_conc_m[k, ] = np.nansum(sel_Cm[k, :])
    return calc_conc_n, calc_conc_v, calc_conc_m


def mean_of_n(sel_Cn, sel_X, sel_bar_width, calc_conc_n, calc_conc_v, calc_conc_m, nr_mean):
    """calculates a mean of every n consecutive measurements and also gives the standard deviation
    select the desired data in an array before, to correctly work with it, if the number of repetitions was not always n
    only works with more than 3 measurements"""
    # can definitely be shortened by making one function and calling it for the arguments
    n = nr_mean
    size = sel_Cn.shape
    nth_len = int(size[0]/n)
    mean_Cn = np.zeros(shape=(nth_len, size[1]))
    std_Cn = np.zeros_like(mean_Cn)
    mean_X = np.zeros_like(mean_Cn)
    mean_bar_width = np.zeros_like(mean_Cn)
    mean_conc_n = []
    std_conc_n = []
    mean_conc_v = []
    std_conc_v = []
    mean_conc_m = []
    std_conc_m = []
    for k in range(nth_len):
        mean_Cn[k, :] = np.mean(sel_Cn[(k*n):((k+1)*n-1), :], axis=0)
        std_Cn[k, :] = np.std(sel_Cn[(k*n):((k+1)*n-1), :], axis=0)
        mean_X[k, :] = np.mean(sel_X[(k*n):((k+1)*n-1), :], axis=0)
        mean_bar_width[k, :] = np.mean(sel_bar_width[(k * n):((k + 1) * n - 1), :], axis=0)
        mean_conc_n.append(np.mean(calc_conc_n[(k * n):((k + 1) * n - 1), ], axis=0))
        std_conc_n.append(np.std(calc_conc_n[(k * n):((k + 1) * n - 1), ], axis=0))
        mean_conc_v.append(np.mean(calc_conc_v[(k * n):((k + 1) * n - 1), ], axis=0))
        std_conc_v.append(np.std(calc_conc_v[(k * n):((k + 1) * n - 1), ], axis=0))
        mean_conc_m.append(np.mean(calc_conc_m[(k * n):((k + 1) * n - 1), ], axis=0))
        std_conc_m.append(np.std(calc_conc_m[(k * n):((k + 1) * n - 1), ], axis=0))
    return mean_Cn, std_Cn, mean_X, mean_bar_width, mean_conc_n, std_conc_n, mean_conc_v, std_conc_v, mean_conc_m, \
           std_conc_m


def calc_mean_of_n(X, Cn, bar_width, scan_nrs, nr_mean):
    """Does the above defined functions in one go and calculates a mean of the n scans given"""
    sel_Cn, sel_X, sel_bar_width = select_data(X, Cn, bar_width, scan_nrs)

    sel_Cv = volume_conc(sel_X, sel_Cn)
    sel_Cm = mass_conc(sel_X, sel_Cv)

    calc_conc_n, calc_conc_v, calc_conc_m = get_conc(sel_Cn, sel_Cv, sel_Cm)

    mean_Cn, std_Cn, mean_X, mean_bar_width, mean_conc_n, std_conc_n, mean_conc_v, std_conc_v, mean_conc_m, \
    std_conc_m = mean_of_n(sel_Cn, sel_X, sel_bar_width, calc_conc_n, calc_conc_v, calc_conc_m, nr_mean)

    return mean_Cn, std_Cn, mean_X, mean_bar_width, mean_conc_n, std_conc_n, mean_conc_v, std_conc_v, mean_conc_m, \
           std_conc_m


def pick_scans(X, Cn, bar_width, density, scan_nrs, nr_mean):
    sel_Cn, sel_X, sel_bar_width = select_data(X, Cn, bar_width, scan_nrs)
    sel_Cv = volume_conc(sel_X, sel_Cn)
    sel_Cm = mass_conc(sel_Cv, density)
    calc_conc_n, calc_conc_v, calc_conc_m = get_conc(sel_Cn, sel_Cv, sel_Cm)
    if nr_mean == 0 or nr_mean == 1:
        mean_Cn, std_Cn, mean_X, mean_bar_width, mean_conc_n, std_conc_n, mean_conc_v, std_conc_v, mean_conc_m, \
            std_conc_m = [], [], [], [], [], [], [], [], [], []
    else:
        mean_Cn, std_Cn, mean_X, mean_bar_width, mean_conc_n, std_conc_n, mean_conc_v, std_conc_v, mean_conc_m, \
        std_conc_m = mean_of_n(sel_Cn, sel_X, sel_bar_width, calc_conc_n, calc_conc_v, calc_conc_m, nr_mean)

    return sel_Cn, sel_X, sel_bar_width, sel_Cv, sel_Cm, calc_conc_n, calc_conc_v, calc_conc_m, mean_Cn, std_Cn, \
        mean_X, mean_bar_width, mean_conc_n, std_conc_n, mean_conc_v, std_conc_v, mean_conc_m, std_conc_m


def plot_meandata(mean_X, mean_bar_width, mean_Cn, std_Cn, mean_conc_n, std_conc_n, measurement_nr):
    """plots the given data, use range(start, end), or a list to specify the measurements to use, these are the indices
    in the given Cn and C arrays"""
    cm = 1/2.54  # inches to cm
    fig, ax = plt.subplots(figsize=(18.5*cm, 10*cm))  # height with title 12, without 10
    for k in measurement_nr:
        ax.bar(mean_X[k, :], mean_Cn[k, :], width=mean_bar_width[k, :], yerr=std_Cn[k, :], edgecolor='black')
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.set(xscale='log', xticks=[20, 50, 100, 200, 400, 800], xticklabels=[20, 50, 100, 200, 400, 800],
           xlabel='Particle Diameter / nm',
           ylabel='Differential Particle Number Concentration / $\mathregular{1/cm^3}$')
    # yscale='log', xscale='log', xlabel='$\mathregular{dlog D_p}$ / nm', ylabel='dN / $\mathregular{P/cm^3}$'
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    [print(f"measurement {k} conc. = " + "{:e}".format(float(mean_conc_n[k])) + u"\u00B1" +
           "{:e}".format(float(std_conc_n[k])) + " P/cm" + u"\u00B3") for k in measurement_nr]
    legend_entries = []
    for k in measurement_nr:
        legend_entries.append(input(f"Please enter the legend entry for measurement {k}"))
    plt.legend(legend_entries)

    plt.show()
    return ax


def plot_singledata(sel_X, sel_bar_width, sel_Cn, calc_conc_n, scan_nr):
    """plots the given data, specify measurement to use from sel_Cn array"""
    cm = 1/2.54  # inches to cm
    fig, ax = plt.subplots(figsize=(18.5*cm, 10*cm))  # height with title 12, without 10
    if len(scan_nr) == 1:
        k = scan_nr[0]
        ax.bar(sel_X[k, :], sel_Cn[k, :], width=sel_bar_width[k, :], edgecolor='black')
    else:
        for k in scan_nr:
            ax.bar(sel_X[k, :], sel_Cn[k, :], width=sel_bar_width[k, :], edgecolor='black', alpha=0.5)
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.set(xscale='log', xticks=[20, 50, 100, 200, 400, 800], xticklabels=[20, 50, 100, 200, 400, 800],
           xlabel='Particle Diameter / nm',
           ylabel='Differential Particle Number Concentration / $\mathregular{1/cm^3}$')
    # yscale='log', xscale='log', xlabel='$\mathregular{dlog D_p}$ / nm', ylabel='dN / $\mathregular{P/cm^3}$'
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    if len(scan_nr) == 1:   # this could maybe be moved up into the previous for loop
        k = scan_nr[0]
        legend_entries = [input(f"Please enter the legend entry for scan {k}")]
        print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        legend_entries = []
        for k in scan_nr:
            legend_entries.append(input(f"Please enter the legend entry for scan {k}"))
            print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    plt.legend(legend_entries)

    plt.show()
    return ax


def plot_3Dsingledata(sel_X, sel_Cn, start, end):
    """plots the given data in 3D, specify scan numbers start and end in actual scan number"""
    cm = 1/2.54  # inches to cm
    fig = plt.figure(figsize=(18.5*cm, 18.5*cm))
    ax = fig.add_subplot(111, projection='3d')
    X, Y = np.meshgrid(np.log(sel_X[start, :]), np.arange(start, end+1)) #log as ax.set(xscale ='log') doesnt work in 3d
    ax.plot_surface(X, Y, sel_Cn[start-1:end, :], cmap=colormap.coolwarm)
        #, alpha=0.5)
    ax.set(xticks=[np.log(20), np.log(50), np.log(100), np.log(200), np.log(400), np.log(800)],
           xticklabels=[20, 50, 100, 200, 400, 800],
           xlabel='Particle Diameter / nm',
           ylabel='Scan Number',
           zlabel='Differential Particle Number Concentration / $\mathregular{1/cm^3}$')
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    #fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    #legend_entries = []
    #for k in measurement_nr:
    #    legend_entries.append(input(f"Please enter the legend entry for measurement {k}"))
    #    print(f"measurement {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    #plt.legend(legend_entries)

    plt.show()
    return ax


def geometric_mean(mean_X, mean_Cn, mean_conc_n):
    # for lognormal, count median diameter = geometric mean diameter
    # maybe add a check for lognormal
    dg = []
    for k in np.arange(0, mean_Cn.shape[0]):
        dg.append(math.exp((1/mean_conc_n[k]) * np.nansum(np.log(mean_X[k])*mean_Cn[k])))
        # gives seemingly correct results
        # dg.append(math.pow(10, ((1 / mean_conc_n[k]) * np.nansum(np.log10(mean_X[k]) * mean_Cn[k]))))
        # same result as above
        # dg.append(np.nansum(np.multiply(mean_Cn[k], mean_X[k])) / np.nansum(mean_Cn[k]))
        # gives bit higher dg that seems wrong
    return dg  # seems to work


def geometric_std(mean_X, mean_Cn, mean_conc_n, dg):
    sigma_g = []
    for k in np.arange(0, len(mean_conc_n)):
        sigma_g.append(math.exp(math.sqrt((np.nansum(np.square(np.log(mean_X[k]) - np.log(dg[k]))*mean_Cn[k]))/
                                         (mean_conc_n[k]-1))))  # 22-13 in aerosol measurement, kulkarni et.al.
        #sigma_g.append(math.pow(10, (math.sqrt((np.nansum(np.square(np.log10(mean_X[k]) - np.log10(dg[k])) *
        #                                                  mean_Cn[k])) / (mean_conc_n[k] - 1)))))
        # same result as above
    return sigma_g


def lognormal_dist(mean_conc_n, sigma_g, dg, mean_X, mean_bar_width):
    """calculates a normal distribution based on the median diameter and the geometric standard deviation"""
    fit = np.zeros_like(mean_X)
    for k in np.arange(0, mean_X.shape[0]):
        #fit[k, :] = (mean_conc_n[k] / (math.sqrt(2 * math.pi) * np.log(sigma_g[k]))) * \
        #            np.exp((-np.square(np.log(mean_X[k, :]) - np.log(dg[k]))) / (2 * (math.log(sigma_g[k])) ** 2))
        # is roughly 28 times higher than the histogram
        fit[k, :] = ((mean_conc_n[k]/mean_bar_width[k])/(math.sqrt(2 * math.pi) * np.log(sigma_g[k])))*\
                    np.exp((-np.square(np.log(mean_X[k, :])-np.log(dg[k])))/(2*(math.log(sigma_g[k]))**2))
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


def calc_geometry(mean_X, mean_Cn, mean_conc_n, mean_bar_width):  # theoretically this would also work with noon-mean
    dg = geometric_mean(mean_X, mean_Cn, mean_conc_n)   # spectra by using sel_X, sel_Cn, calc_conc_n, sel_bar_width
    sigma_g = geometric_std(mean_X, mean_Cn, mean_conc_n, dg)
    fit = lognormal_dist(mean_conc_n, sigma_g, dg, mean_X, mean_bar_width)
    return dg, sigma_g, fit


def save_values(filename, calc_conc_n):
    """function, that saves all the important values (median, sigma, conc) to a csv or txt"""
    savefile = f"{filename[0:-4]}_savedata.xlsx"
    return


def cut_X(X, Cn):
    """to cut a part of the spectrum"""
    strt_idx = np.where(X[10] > 150)[0][0]
    end_idx = np.where(X[10] < 250)[-1][-1] + 1
    return


def save_values(mean_conc_n, dg, sigma):
    """function, that saves all the important values (median, sigma, conc) to a csv or txt"""

    return


"""write a function, to build mean measurement arrays step by step, so that with pick scans all the input arrays are 
 produced, which are then each concatenated to new lines in collection arrays. By that, it should become possible to 
 select specific scans, mean them according to the number of selected scans and put them in the new arrays stepwise
 when all desired measurements are collected, these can then easily be plotted with plot_meandata
 in etwa das nutzend:
 mean_Cn_a, std_Cn_a, mean_X_a, mean_bar_width_a, mean_conc_n_a, std_conc_n_a, = \
    np.concatenate((mean_Cn_a, mean_Cn)), np.concatenate((std_Cn_a, std_Cn)), np.concatenate((mean_X_a, mean_X)), 
    np.concatenate((mean_bar_width_a, mean_bar_width)), np.concatenate((mean_conc_n_a, mean_conc_n)), 
    np.concatenate((std_conc_n_a, std_conc_n))
    see end of 2022-04-13 eval pyconsole"""


if __name__ == "__main__":

    filename = get_filename()
    X, bar_width, Cn, time = fileread(filename)
    # data_identifier = {"X": X, "Cn": Cn, "bar_width": bar_width, "time": time} # set identifier as desired e.g. date

    # scan_nrs = np.arange(1, 28)  # actual scan numbers in non-pythonian logic + 1 in the and due tu np.arange
    # nr_mean = 1
    # density = 1  # if unknown use 1 g/cm^3
    # print(f"scan_nrs: {scan_nrs}, nr_mean: {nr_mean}, density: {density}")

    # sel_Cn, sel_X, sel_bar_width, sel_Cv, sel_Cm, calc_conc_n, calc_conc_v, calc_conc_m, mean_Cn, std_Cn, \
    # mean_X, mean_bar_width, mean_conc_n, std_conc_n, mean_conc_v, std_conc_v, mean_conc_m, std_conc_m = \
    #      pick_scans(X, Cn, bar_width, density, scan_nrs, nr_mean)

    # dg, sigma_g, fit = calc_geometry(mean_X, mean_Cn, mean_conc_n, mean_bar_width)
    # dg, sigma_g, fit = calc_geometry(sel_X, sel_Cn, calc_conc_n, sel_bar_width)

    # print(f'median = {dg}, sigma = {sigma_g}')

    # measurement_nr = [0]#np.arange(1, 7) # for plotting
    # print(f"measurement_nr: {measurement_nr}")

    # ax1 = plot_singledata(sel_X, sel_bar_width, sel_Cn, calc_conc_n, measurement_nr)
    # ax1 = plot_meandata(mean_X, mean_bar_width, mean_Cn, std_Cn, mean_conc_n, std_conc_n, measurement_nr)

    # ax1.plot(mean_X[measurement_nr], fit[measurement_nr])
    # print(dg)
    # print(sigma_g)

    # plt.ioff()
    # plt.show() # if plot doesnt show!

    # plt.ioff()
    # plt.show() # if plot doesnt show!

