# -*- coding: utf-8 -*-
"""
Sup.py

Functions for running Particle_analysis.py

Created 2024-03-20 from get_filenames.py and other small scripts
@written by Kevin Maier (kevin.r.maier@tum.de)

"""


from tkinter import Tk
from tkinter.filedialog import askopenfilename, askopenfilenames


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


def get_variable_name(some_variable):
    for name, value in globals().items():
        if value is some_variable:
            return name


def py_logic_converter(nr_list):
    """converts from normal logic (starting count from 1) to python logic (starting count from 0)"""
    py_nr_list = []
    [py_nr_list.append(i - 1) for i in nr_list]
    return py_nr_list


def normal_logic_converter(nr_list):
    """converts from python logic (starting count from 0) to normal logic (starting count from 1)"""
    normal_nr_list = []
    [normal_nr_list.append(i + 1) for i in nr_list]
    return normal_nr_list


def convert_standard_to_volumetric_flow(standard_flow, T_flow, p_flow, T_standard, p_standard):
    """converts standard flow rate given by mass flow controllers to volumetric flow rate as required for calculation
    of aerosol concentrations based on ideal gas law
    units must match, so T should be given in °C, p should be given in matching units, Pa, kPa, mbar, or bar
    formula also given in TSI Application Note FLOW-004"""
    volumetric_flow = standard_flow*((T_flow+273.15)/(T_standard+273.15)*(p_standard/p_flow))
    return volumetric_flow
