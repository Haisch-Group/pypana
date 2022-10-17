# -*- coding: utf-8 -*-
"""
Script for Data Evaluation of the TSI APS

Created 2021-10-26
@written by Kevin Maier (kevin.r.maier@tum.de)
"""

from matplotlib import ticker
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilenames #plural here


def import_data(filenames):
    """import aps data from txt file with name filename"""
    if len(filenames) == 1:
        data = np.genfromtxt(filenames[0], delimiter=",", skip_header=8)
    else:
        data = np.genfromtxt(filenames[0], delimiter=",", skip_header=8)
        for k in range(1, len(filenames)):
            dummy = np.genfromtxt(filenames[k], delimiter=",", skip_header=8)
            data = np.append(data, dummy[:, 1].reshape(len(dummy),1), axis=1)

    return data


def mean_of_3(data):
    """calculates a mean of every three consecutive measurements and also gives the standard deviation"""
    size = data.shape
    x_axis = data[:, 0]
    third_len = int((size[1]-1) / 3)
    mean_data = np.zeros(shape=(size[0], third_len))
    std_data = np.zeros(shape=(size[0], third_len))
    for k in range(third_len):
        mean_data[:, k] = np.mean(data[:, (k * 3)+1:((k + 1) * 3)], axis=1)
        std_data[:, k] = np.std(data[:, (k * 3)+1:((k + 1) * 3)], axis=1)

    return x_axis, mean_data, std_data


def plot_data(x_axis, mean_data, std_data):
    """plots the given data"""

    bar_width = np.zeros(len(x_axis))
    for k in range(len(x_axis)):
        if k < len(x_axis) - 1:
            bar_width[k] = x_axis[k + 1] - x_axis[k]
        else:
            bar_width[k] = x_axis[k] - x_axis[k - 1]

    fig, ax = plt.subplots()
    for k in range(len(mean_data[0, :])):
        ax.bar(x_axis, mean_data[:, k], width=bar_width, yerr=std_data[:, k], edgecolor='black')
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.set(xscale='log', xticks=[20, 50, 100, 200, 400], xticklabels=[20, 50, 100, 200, 400],
           xlabel='$\mathregular{log D_p}$ / ${\mu m}$', ylabel='dW / $\mathregular{P/cm^3}$')
    plt.title(input("Please enter the title of the figure"), y=1.08)
    #legend_entries = []
    #for k in measurement_nr:
    #    legend_entries.append(input(f"Please enter the legend entry for measurement {k}"))
    #plt.legend(legend_entries)
    plt.show()
    return ax


if __name__ == "__main__":

    Tk().withdraw()
    filenames = askopenfilenames()
    data = import_data(filenames)
    x_axis, mean_data, std_data = mean_of_3(data)
    ax = plot_data(x_axis, mean_data, std_data)