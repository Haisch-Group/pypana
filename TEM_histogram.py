# -*- coding: utf-8 -*-
"""
Script for creating TEM histograms from a list of particle areas

Created 2022-04-21
@written by Kevin Maier (kevin.r.maier@tum.de)
"""

from tkinter import Tk
from tkinter.filedialog import askopenfilename
import pandas as pd
import math
import matplotlib.pyplot as plt
import numpy as np


def get_filename():
    """get the filename via UI"""
    Tk().withdraw()
    filename = askopenfilename()
    return filename


def import_data():
    filename = get_filename()
    data = pd.read_csv(filename)
    areas = data.Area
    return areas


def calculate_d(areas):
    diameters = [2 * math.sqrt(x/math.pi) for x in areas]
    return diameters


def plot_hist(diameters):
    bins = np.arange(0, 40, 0.5)
    cm = 1 / 2.54  # inches to cm
    fig, ax = plt.subplots(figsize=(18.5 * cm, 10 * cm))  # height with title 12, without 10
    ax.hist(diameters, bins=bins, density=True)
    ax.set(xlabel='particle diameter / nm', ylabel='probability', xlim=(0, 40))
    plt.show()
    return ax


if __name__ == "__main__":
    areas = import_data()
    diameters = calculate_d(areas)
    ax = plot_hist(diameters)

