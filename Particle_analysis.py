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
import dill
# import scipy.integrate as integrate
# from matplotlib import cm as colormap


def read_distribution(filename, used_device):
    """function for importing distribution data, applying the correct import filter according to user choice and
    importing data as X = np.array((nr_scans, nr_bins)), bar_width, Cn = X.shape, time = []"""
    if used_device == 0:
        import TSI_SMPS3071_fileread as fr  # ! utf-8 encoding for 3-superscript in the header second to last
        # column P/cm^3 does not work sometimes, just change the ^3 to 3 in the data txt then
    elif used_device == 1:
        import TSI_SMPS3938_fileread as fr
    elif used_device == 2:
        import PALAS_SMPS2100_fileread as fr
    elif used_device == 3:
        import TSI_APS3321_fileread as fr
    elif used_device == 4:
        import PALAS_Welas_fileread as fr
    elif used_device == 5:
        import TSI_LAS3340A_fileread as fr

    X, bar_width, Cn, time = fr.import_data(filename)
    return X, bar_width, Cn, time


def read_concentration(filename, used_device):
    """function for importing concentration data, applying the correct import filter according to user choice and
    importing data as Cn, el_time = np.array((nr_scans, nr_times)), start_time = []"""
    if used_device == 6:
        import TSI_CPC3775_fileread as fr
    elif used_device == 7:
        import PALAS_UFCPC_fileread as fr

    Cn, el_time, start_time = fr.import_data(filename)
    return Cn, el_time, start_time


def get_data():
    used_device = int(input("Which instrument did you use, type 0 for TSI SMPS 3081, 1 for TSI SMPS 3938, 2 for PALAS "
                            "SMPS 2100, 3 for TSI APS 3321, 4 for PALAS Welas, 5 for TSI LAS 3340A, 6 for CPC 3775 and "
                            "7 for PALAS UFCPC, enter as int."))

    if used_device in [0, 1, 2, 3, 4]:  # Size Distribution Instruments
        filename = Sup.get_filename()
        X, bar_width, Cn, time = read_distribution(filename, used_device)
        scan_nr = []
        [scan_nr.append(k + 1) for k in range(len(X))]
        data = {"X": X, "Cn": Cn, "bar_width": bar_width, "time": time, "scan_nr": scan_nr, "filename": filename,
                "used_device": used_device}

    elif used_device == 5:
        filenames = Sup.get_filenames()
        X, bar_width, Cn, time = read_distribution(filenames, used_device)
        # X, bar_width, Cn, time, n_scans = read_distribution(filenames, used_device)
        scan_nr = []
        n_scans = int(input("How many scans did you accquire per measurement? Give as int!"))
        for k in range(len(filenames)):
            [scan_nr.append(k + 1) for i in range(n_scans)]
        data = {"X": X, "Cn": Cn, "bar_width": bar_width, "time": time, "scan_nr": scan_nr, "filename": filenames,
                "used_device": used_device, "n_scans": n_scans}

    elif used_device in [6, 7]:  # Particle Counters
        filename = Sup.get_filename()
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
    # data_identifier = Sup.get_variable_name(data_dict)
    path = data_dict["filename"][:-4]+"_"+fileaddition+".csv"
    # path = data_dict["filename"][:-4] + "_" + data_identifier + "_" + fileaddition + ".csv"
    dataframe = pd.DataFrame()
    for variable in variable_list:
        dataframe[variable] = data_dict[variable]
    print(f"wrote file with variables {variable_list} to csv with name {path}")
    dataframe.to_csv(path)
    return

def save_session():
    filename = Sup.set_filename()
    path = (f"{filename}" + ".dill")
    dill.dump_session(path)
    return

def load_session():
    path = Sup.get_filename()
    dill.load_session(path)
    return

if __name__ == "__main__":

    """
    The script is run from the python console with the following commands
    
    # Start Script
    
    run particle_analysis.py

    # Data Import

    data_identifier = get_data() 
    
    change identifier to something that identifies the dataset, like a device + date e.g.: cpc_20240515
    imports one file at a time as dictionary
    choose input prompt according to the used device and the desired data possible prompts are displayed in console
    
    # Typical Calculations
    
    ## For Distributions:
    
    Dist.typical_calculations(data_identifier);
    
    calculates the concentration, median diameter and geometrical standard deviation of a measurement
    
    ## For Concentrations:
    
    Conc.typical_calculations(data_identifier);
    
    calculates the mean concentration of a measurement
    
    # Save Calculated Values to CSV    
    
    ## For Distributionss
    
    save_calc_to_csv(data_identifier, ["scan_nr", "time", "dg", "sigma", "calc_conc_n"], fileaddition="particleDF")
    
    ## For Concentrations
    
    save_calc_to_csv(data_identifier, ["scan_nr", "start_time", "conc_n", "std_n"], fileaddition="particleDF")
    
    # Distribution-specific Functions
    
    ## Data Selection
    
    sel_data_identifier = Dist.select_data(data_identifier, [scan_nrs]) 
    
    creates a new dictionary from the parent to sort the needed measurements and get rid of failes scans for 
    calculating a mean
    enter scan_nrs manually in a list, or as range
    Dist.typical_calculations has to be run for the selected array again
    print(f"selected scan_nrs: {scan_nrs}") to have them documented in console

    ## Calculation of Volume and Mass Distributions
    
    density = 1  # in g/cm^3
    data["Cv"] = Dist.volume_dist(data["X"], data["Cn"])
    data["Cm"] = Dist.mass_dist(data["Cv"], density)
    print(f"Mass Distribution with Density = {density} g/cm^3 calculated.") 

    ## Cut Size Distribution
    
    lowerbound = 100 #in the unit, the size data are saved by the instrument e.g. nm
    upperbound = 350
    cut_nrs = [1, 5, 7, 15]
    cut_X, cut_Cn, cut_bar_width = Dist.cut_dist(sel_data["X"], sel_data["Cn"], sel_data["bar_width"], lowerbound,
    upperbound, cut_nrs)
    
    Allows to cut specific measurements to a more narrow size region, usually selected data should be used, but also 
    normal data can be used

    ## Calculate Mean Distributions
    
    nr_mean = 3
    mean_data = Dist.mean_of_n(data_identifier, nr_mean)
    print(f"mean of: {nr_mean} calculated")
    
    Calculates the mean distribution of n measurements. Measurements have to be in direct succession, so in normal cases
    measurements have to be selected first to bring the desired measurements in the right order and remove outliers

    ## Calculation of Geometric Parameters
    
    data_identifier["dg", "sigma_g"] = Dist.calc_geometry(data_identifier["X"], data_identifier["Cn"],
        data_identifier["calc_conc_n"], data_identifier["bar_width"])
    
    Calculation the geometrical mean and the geometrical standard deviation. Is called in "typical_calculations", so
    calling it on its own is not usually necessary. Also works for selected data. In mean data, the dg and sigma are
    calculated from the values given in the selected data set
    
    ## Calculation of cummulative distribution
    
    data_identifier["cummC"] = Dist.cumulative_distribution(data_identifier["Cn"])
    data_identifier["X10"], data_identifier["X16"], data_identifier["X50"], data_identifier["X84"], 
        data_identifier["X90"] = Dist.cumulative_diameters(data_identifier["X"], data_identifier["cummC"]
    
    calculated the cumulative distributions and the particle diameters below which 10, 16, 50, 84 and 90 % of all 
    particles are

    ## plotting of data -> has to be adjustet to allow for different data to be plotted
    
    ### plot normal distributions (no mean)
    
    scan_nrs = [1, 5, 7, 15]  # or list(range(1, 7))
    print(f"Plotted scan numbers: {scan_nrs}")
    ax = Dist.plot_singledata(data_identifier, scan_nrs)

    ### plot mean data
    
    ax = Dist.plot_meandata(mean_data_identifier, scan_nrs)
    
    neads a mean array created before, plots mean scans from it
    
    ### plot cumulative data
    
    ax = Dist.plot_cummdata(data_identifier, data_identifier["used_device"], scan_nrs)
    
    # Concentration specific calls
    
    ## cut time of measurement
    
    cut_time(data_identifier, scan_nrs, start, end)
    
    start and end are times in s of the measurements
    new column with ["cut_Cn"] is created
    
    ## ploting of data
    
    ### plot normal data
    
    ax = plot_fulldata(data_identifier, scan_nrs)
    
    ### plot cut data
    
    ax = plot_cutdata(data_identifier, scan_nrs)

    # Other Calls
    
    ## Calculate Mean and Std of whatever
    
    x_mean, x_std = mean_and_std(sel_data["dg"][:])

    ## Copy without Overwriting
    
    from copy import deepcopy
    dict_copy = deepcopy(dict) 
    
    gives flat copy that does not change original when changing copy

    ## If plot does not display
    
    plt.ioff()
    plt.show()

    ## Save and load session
    ### Save
    
    import dill
    filename = "Z:/Projects/AeroCal/Measurements/whatever.dill"
    dill.dump_session(filename)
    
    ### Load
    dill.load_session(filename)
    """
