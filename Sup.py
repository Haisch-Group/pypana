# -*- coding: utf-8 -*-
"""
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


def get_variable_name(var):
    for name, value in globals().items():
        if value is var:
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
