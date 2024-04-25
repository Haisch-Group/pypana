# -*- coding: utf-8 -*-
"""
Script for Particle Data Evaluation
Data has to be imported by the import function suitable for the used Device

Created 2023-05 from SMPS_analysis.py
Modified 2024-03-20 to also run CPC_analysis.py which was renamed to Conc.py
@written by Kevin Maier (kevin.r.maier@tum.de)

"""

import Sup
import Dist
import Conc
import pandas as pd
import numpy as np
import math
from matplotlib import pyplot as plt
from matplotlib import ticker
from scipy import optimize
# import scipy.integrate as integrate
# from matplotlib import cm as colormap


def read_distribution(filename, used_device):
    """function for importing distribution data, applying the correct import filter according to user choice and
    importing data as X = np.array((nr_scans, nr_bins)), bar_width, Cn = X.shape, time = []"""
    if used_device == 0:
        import TSI_SMPS3071_fileread as fr  # ! utf-8 encoding for 3-superscript in the header second to last
        # column P/cm^3 does not work sometimes, just change the ^3 to 3 in the data txt then
    elif used_device == 1:
        import PALAS_SMPS2100_fileread as fr
    elif used_device == 2:
        import TSI_LAS3340A_fileread as fr
    elif used_device == 3:
        import TSI_APS3321_fileread as fr

    X, bar_width, Cn, time = fr.import_data(filename)
    return X, bar_width, Cn, time


def read_concentration(filename, used_device):
    """function for importing concentration data, applying the correct import filter according to user choice and
    importing data as Cn, el_time = np.array((nr_scans, nr_times)), start_time = []"""
    if used_device == 4:
        import TSI_CPC3775_fileread as fr
    elif used_device == 5:
        import PALAS_UFCPC_fileread as fr

    Cn, el_time, start_time = fr.import_data(filename)
    return Cn, el_time, start_time


def get_data():
    filename = Sup.get_filename()
    used_device = int(input("Which instrument did you use, type 0 for TSI SMPS 3081, 1 for PALAS SMPS 2100, 2 for "
                        "TSI LAS 3340A, 3 for TSI APS 3321, 4 for TSI CPC 3775 and 5 for PALAS UFCPC, enter as int."))

    if used_device in [0, 1, 2, 3]:
        X, bar_width, Cn, time = read_distribution(filename, used_device)
        scan_nr = []
        [scan_nr.append(k + 1) for k in range(len(X))]
        data = {"X": X, "Cn": Cn, "bar_width": bar_width, "time": time, "scan_nr": scan_nr, "filename": filename,
                "used_device": used_device}

    elif used_device in [4, 5]:
        Cn, el_time, start_time = read_concentration(filename, used_device)
        scan_nr = []
        [scan_nr.append(k + 1) for k in range(len(Cn))]
        data = {"Cn": Cn, "el_time": el_time,
                "start_time": start_time, "scan_nr": scan_nr, "filename": filename, "used_device": used_device}

    else:
        print(f"Device {used_device} is not a viable option")
        data = used_device

    return data


def save_calc_to_csv(data_dict, variable_list, fileaddition="particleDF"):
    """saves selected variables to a csv file, select variables to save in variable_list as list of strings,
     allways use a different fileaddition when saving anything else than the data input array data_identifier"""
    data_identifier = Sup.get_variable_name(data_dict)
    path = data_dict["filename"][:-4]+"_"+data_identifier+"_"+fileaddition+".csv"
    dataframe = pd.DataFrame()
    for variable in variable_list:
        dataframe[variable] = data_dict[variable]
    print(f"wrote file with variables {variable_list} to csv with name {path}")
    dataframe.to_csv(path)
    return


"""ToDo:"""


# Add Multiple Charge Correction

# Add Diffusion Loss calculator

# For SMPS maybe integrate the whole data inversion process

# Vorschlag Nico: Median als senkrechte Linie / Marker in den Plot einbauen

# Kommentar mit einlesen bei Dateiimport ?

# filename in merged array aus filenames der gemergeten arrays zusammenschnetzeln

# save funktion die dict zu einfacherer struktur macht, evtl. in form ähnlich zu PALAS Daten?
#   filename, scan_nr ,time, used_device, calc_conc_n, dg, sigma # everything that is only one item per measurement
#   X...
#   Cn...
#   bar_width...
#   ... # everything, that is an array element in one line
# kann dann als csv gespeichert werden, oder gepicklet, oder gejsont? Evtl. mehrere Tabellenblätter in xlsx?

# just a code sniplet, that could be used to automatically import multiple datasets at once
#   naming variables automatically and getting them out of a function does not work though
#   input_name = input("Enter a name for the data you are importing (has to start with a letter)")
#   locals()[input_name] = data

# check, where Cn and where C makes sense as variable name
# all processes , like select, merge, etc. can be done with Cn, then the data can be converted to Cv and Cm
# -> change mean_C to "Cn" in mean function
# after that, dg, sigma etc. can be calculated with Cn, Cv, or Cm alike
# add plot option for Cv and Cm in format plot function depending on one variable

# Add 2023-12-12 Eval to this script? -> comparison of 2 devices for calibration?

# get ELPI data into this file too?

if __name__ == "__main__":

    # run particle_analysis.py

    """data import - imports one file at a time to a dictionary"""

    # data_identifier = get_data() # change identifier to something that identifies the dataset, like a date

    """Distribution operations"""
    # Dist.typical_calculations(data);




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

    # for Dist
    # save_calc_to_csv(data_identifier, ["scan_nr", "time", "dg", "sigma", "calc_conc_n"], fileaddition="particleDF")
    # for mean Dist
    # save_calc_to_csv(mean_identifier, ["mean_conc", "std_conc", "mean_dg", "std_dg", "mean_sigma", "std_sigma],
    # fileaddition="particleDF")  # dafür muss erst die funktion noch geändert werden
    # for Conc
    # save_calc_to_csv(data_identifier, ["scan_nr", "start_time", "conc_n", "std_n"], fileaddition="particleDF")

    """other calls"""
    # ax1.plot(mean_X[measurement_nr], fit[measurement_nr])
    # print(dg)
    # print(sigma_g)
    # x_mean, x_std = mean_and_std(sel_data["dg"][:])

    # from copy import deepcopy
    # dict_copy = deepcopy(dict) gives flat copy that does not change original when changing copy

    plt.ioff()
    # plt.show() # if plot doesnt show!

    """to save"""
    # import dill
    # filename = "Z:/Projects/AeroCal/Measurements/whatever.dill"
    # dill.dump_session(filename)
    # dill.load_session(filename
