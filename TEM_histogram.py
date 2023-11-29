# -*- coding: utf-8 -*-
"""
Script for creating TEM histograms from a list of particle areas

Created 2022-04-21
@written by Kevin Maier (kevin.r.maier@tum.de)
"""

from get_filename import get_filename
import pandas as pd
import math
import matplotlib.pyplot as plt
import numpy as np
import statistics


def import_data():
    filename = get_filename()
    data = pd.read_csv(filename)
    areas = data.Area
    print(filename)
    return areas


def calculate_d(areas):
    diameters = [2 * math.sqrt(x/math.pi) for x in areas]
    return diameters


def plot_hist(diameters):
    """if other particles, than some between 0 and 40 nm are measured, change bins = np.arange to (lower size lim,
    upper size lim, width of bins in nm) and in ax.st(..., xlim(lower size lim, upper size lim) according to the
    measured sizes - this could be automated"""
    bins = np.arange(0, 40, 0.5)
    cm = 1 / 2.54  # inches to cm
    fig, ax = plt.subplots(figsize=(18.5 * cm, 10 * cm))  # height with title 12, without 10
    ax.hist(diameters, bins=bins, density=True)
    ax.set(xlabel='particle diameter / nm', ylabel='prevalence of particles with given diameter', xlim=(0, 40))
    sample_size = len(diameters)
    median_dp = statistics.median(diameters)
    stdev_dp = statistics.stdev(diameters)
    plt.title(f"n = {sample_size}, median = {round(median_dp, 2)} \u00B1 {round(stdev_dp, 2)} nm")
    plt.show()
    return ax


if __name__ == "__main__":

    areas = import_data()
    diameters = calculate_d(areas)
    ax = plot_hist(diameters)

