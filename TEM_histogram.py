# -*- coding: utf-8 -*-
"""
TEM_histogram.py

Script for creating TEM histograms from a list of particle areas

Created 2022-04-21
@written by Kevin Maier (kevin.r.maier@tum.de)
"""

from Sup import get_filename
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


def calc_d(areas):
    diameters = [2 * math.sqrt(x/math.pi) for x in areas]
    return diameters


def calc_geometry(diameters):
    sample_size = len(diameters)
    median_dp = statistics.median(diameters)
    mean_dp = statistics.mean(diameters)
    stdev_dp = statistics.stdev(diameters)
    CV = stdev_dp/mean_dp # coefficient of variation
    CV_percent = CV*100
    return sample_size, median_dp, mean_dp, stdev_dp, CV, CV_percent


def plot_hist(diameters, sample_size, median_dp, stdev_dp):
    """if other particles, than some between 0 and 40 nm are measured, change bins = np.arange to (lower size lim,
    upper size lim, width of bins in nm) and in ax.st(..., xlim(lower size lim, upper size lim) according to the
    measured sizes - this could be automated"""
    min_d = min(diameters)-min(diameters)*0.2  # automatically calculate x-limits from data
    max_d = max(diameters)+min(diameters)*0.2  # use min in*factor on both sides to have equal distance from last
    # data point to window border
    bin_width = (max(diameters)-min(diameters))/100  # automatically but data in 100 bins for plotting
    bins = np.arange(min_d, max_d, bin_width)
    cm = 1 / 2.54  # inches to cm
    fig, ax = plt.subplots(figsize=(18.5 * cm, 10 * cm))  # height with title 12, without 10
    ax.hist(diameters, bins=bins, density=True)
    ax.set(xlabel='particle diameter / nm', ylabel='prevalence of particles with given diameter', xlim=(min_d, max_d))
    plt.title(f"n = {sample_size}, median = {round(median_dp, 2)} \u00B1 {round(stdev_dp, 2)} nm")
    plt.show()
    return ax


if __name__ == "__main__":

    areas = import_data()
    diameters = calc_d(areas)
    sample_size, median_dp, mean_dp, stdev_dp, CV, CV_percent = calc_geometry(diameters)
    ax = plot_hist(diameters, sample_size, median_dp, stdev_dp)
    print(f"median = {median_dp}, mean = {mean_dp}, sigma = {stdev_dp}, CV = {CV}, CV in % = {CV_percent}, "
          f"sample size = {sample_size}")
