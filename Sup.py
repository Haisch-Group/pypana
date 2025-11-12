# -*- coding: utf-8 -*-
"""
Sup.py

Functions for running Particle_analysis.py

Created 2024-03-20 from get_filenames.py and other small scripts
@written by Kevin Maier (kevin.r.maier@tum.de)

"""


from tkinter import Tk
from tkinter.filedialog import askopenfilename, askopenfilenames, asksaveasfilename
import numpy as np
import math
import matplotlib.pyplot as plt

import Sup
import Def

def get_filename():
    """get one filename via UI"""
    popup = Tk()
    popup.attributes('-topmost', 1)
    popup.withdraw()
    filename = askopenfilename()
    print(filename)
    return filename


def get_filenames():
    """get multiple filenames via UI"""
    popup = Tk()
    popup.attributes('-topmost', 1)
    popup.withdraw()
    filenames = askopenfilenames()
    print(filenames)
    return filenames


def set_filename():
    """set filename via UI"""
    popup = Tk()
    popup.attributes('-topmost', 1)
    popup.withdraw()
    filename = asksaveasfilename(filetypes=(("All Files", "*"), ("png file", ".png"), ("csv file", "*.csv"),
                                            ("dill file", ".dill")))
    print(filename)
    return filename


def get_variable_name(some_variable):
    for name, value in globals().items():
        if value is some_variable:
            return name


def check_device(used_device):
    if int(used_device) in Def.device_list["Device_Identifier"]:
        used_device = int(used_device)
    else:
        while int(used_device) not in Def.device_list["Device_Identifier"]:
            print(f"Device {used_device} is not a viable option")
            print(Def.device_list[["Device_Identifier", "Device", "Manufacturer"]].to_string(justify="left", index=False))
            used_device = input("Which instrument do you want to import data from? Enter as int.\n"
                                    "Enter 'break' to stop the input loop.")
            if used_device == "break":  # this is not perfect yet -> drops error, resolve
                break
            else:
                used_device = int(used_device)
    return used_device


def py_logic_converter(scan_nr_list):
    """converts from normal logic (starting count from 1) to python logic (starting count from 0)"""
    py_nr_list = []
    [py_nr_list.append(i - 1) for i in scan_nr_list]
    return py_nr_list


def normal_logic_converter(py_nr_list):
    """converts from python logic (starting count from 0) to normal logic (starting count from 1)"""
    scan_nr_list = []
    [scan_nr_list.append(i + 1) for i in py_nr_list]
    return scan_nr_list


def convert_standard_to_volumetric_flow(standard_flow, T_flow, p_flow, T_standard, p_standard, T_unit):
    """converts standard flow rate given by mass flow controllers to volumetric flow rate as required for calculation
    of aerosol concentrations based on ideal gas law
    units must match, so T should be given in K, or °C, p should be given in matching units, Pa, kPa, mbar, or bar
    formula also given in TSI Application Note FLOW-004"""
    if T_unit == "°C":
        T_flow = convert_C_to_K(T_flow)
    elif T_unit == "K":
        pass
    else:
        print(f"{T_unit} is not a viable Temperature unit, use °C or K")
    volumetric_flow = standard_flow * ((T_flow) / (T_standard) * (p_standard / p_flow))
    return volumetric_flow


def convert_C_to_K(T_in_C):
    """convert Temperature from °C to K"""
    T_in_K = T_in_C + 273.15
    return T_in_K


def convert_K_to_C(T_in_K):
    """convert Temperature from K to °C"""
    T_in_C = T_in_K - 273.15
    return T_in_C


def convert_mbar_to_kPa(p_in_mbar):
    """convert Pressure from mbar to kPa"""
    p_in_kPa = p_in_mbar/10
    return p_in_kPa


def convert_kPa_to_mbar(p_in_kPa):
    """convert Pressure from kPa to mbar"""
    p_in_mbar = p_in_kPa/10
    return p_in_mbar


def lognormal_test(x_lower=5, x_upper=1000, x_steps=99, conc=1E5, dg=80, sigma_g=1.15):
    """log-normal function with A being a scale factor, m being the median and sigma being the geometric
        standard deviation"""
    X = np.logspace(x_lower, x_upper, x_steps, endpoint=True, base=10.0)
    C = (np.exp(-((np.log(X/dg))**2)/(2*np.log(sigma_g)**2))/(np.log(sigma_g)*X*np.sqrt(2*math.pi)))
    return X, C


def decide_C_unit(used_C):
    if used_C == "Cv":
        C_unit = u" \u00B5m\u00B3 g" + u"/cm\u00B3"
    elif used_C == "Cm":
        C_unit = " mg" + u"/cm\u00B3"
    elif used_C == "Cn_dlogX":
        C_unit = " 1" + u"/cm\u00B3"
    else:
        C_unit = " 1" + u"/cm\u00B3"
    return C_unit


def decide_y_label(used_C):
    C_unit = Sup.decide_C_unit(used_C)
    if "dlogX" in used_C:
        y_label = 'dN/dlogD$_{p}$/ ' + C_unit
    elif "cum" in used_C:
        y_label = 'Fraction of Total Particle Concentration %'
    elif "Cv" in used_C:
        y_label = 'Volume Concentration / ' + C_unit
    elif "Cm" in used_C:
        y_label = 'Mass Concentration / ' + C_unit
    else:
        y_label = 'Number Concentration / ' + C_unit
    return y_label


def decide_x_scale(used_device):
    if used_device in list(Def.device_list.query("Size_Plot_Range==u'\xb5m'")["Device_Identifier"].values):
        x_scale = u'\xb5m'
    elif used_device in list(Def.device_list.query("Size_Plot_Range==u'\xb5m in nm'")["Device_Identifier"].values):
        x_scale = 'nm'
    elif used_device in list(Def.device_list.query("Size_Plot_Range=='nm'")["Device_Identifier"].values):
        x_scale = 'nm'
    else:
        x_scale = input("Please enter the given x-scale as string.")
    return x_scale


def decide_filename_function(used_device):
    if used_device == 5:
        filename = Sup.get_filenames()
    else:
        filename = Sup.get_filename()
    return filename


def pack_to_dict_df(data, variables):
    """function to pack variables into a dict and the contained dataframe - maybe use if X and so on are packed to df"""
    data


def extract_from_dict(data, used_C="Cn"):
    if "cut" in used_C:
        X = data["cut_X"]
        dX = data["cut_dX"]
        C = data[used_C]
    else:
        X = data["X"]
        dX = data["dX"]
        C = data[used_C]
    return X, dX, C


def build_legend(legend_entries, scan_nrs, ct, legend="automatic"):
    if legend == "manual":
        legend_entries.append(input(f"Please enter the legend entry for scan {scan_nrs[ct]}"))
    else:
        legend_entries.append(f"Scan {scan_nrs[ct]}")
    return


def save_plot(data, save_plot="off", fileaddition=""):
    if save_plot=="on":
        #data_identifier = Sup.get_variable_name(data)
        path = data["filename"][:-4] + "_" + fileaddition + ".png"
        # path = data["filename"][:-4] + "_" + data_identifier + "_" + fileaddition + ".png"
        plt.savefig(path, dpi=600, transparent=True)
        print(f"file saved to {path}")
    else:
        pass
    return

def norm_C(C, calc_conc):
    norm_C = np.zeros_like(C)
    for k in range(len(C)):
        if calc_conc[k] > 0:
            norm_C[k] = C[k]/calc_conc[k]
        else:
            norm_C[k] = C[k]
    return norm_C