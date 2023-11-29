# -*- coding: utf-8 -*-
"""
Converting from python logic (starting count with 0) to normal logic (starting count with 1) and back

2023-11-27 moved out from particle_analysis.py
@written by Kevin Maier (kevin.r.maier@tum.de)

"""


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
