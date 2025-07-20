"""
DEKATI_ELPIplus_fileread.py

Import and Display of the Data acquired from the Dekati ELPI+

Created 2020-11-01: data_reader and plot_profile
@written by Kevin Maier (kevin.r.maier@tum.de)

2020-11-11 KM: now displays the concentration value calculated by ELPI instead of the raw current
2020-11-17 KM: added tkinter module for file picking
            function particles_per_stage added to calculate collected particles per stage for the collection
            function mass_per_stage added to estimate the mass collected on each stage
2021-01-13 KM: can now load in more than one file, and concatenates the data acquired from the files to display
            one measurement that was split up by the ELPI in multiple datafiles
            fixed particles_per_stage to actually calculate particle numbers and not something in P/min
            fixed display of datetime in plot and adapted plot for thesis

To Do:
    correct data
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates
from datetime import datetime
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askopenfilenames
from math import pi
from scipy import signal
from Def import device_list


def file_reader(filename):
    """reads the elpi data from one file
    input: filename (one from the tuple filenames)
    output: time = datetime array (n, ) shape
            current = raw electrometer current array (n, stages) shape
            concentration = particle concentration calculated by elpi in 1/cm^3 array (n, stages) shape"""
    if filename[-3:] == 'dat':  # for dat file directly aqcuired from elpi
        header_lines = 40
        timeconverter = lambda x: datetime.strptime(x.decode("utf-8"), '%Y/%m/%d %H:%M:%S.%f')
    else:   # for txt file from elpiVI recalculation
        header_lines = 42
        timeconverter = lambda x: datetime.strptime(x.decode("utf-8"), '%Y/%m/%d %H:%M:%S')
    # dateconverter = lambda x: x.decode("utf-8")[5:]
    # date = np.genfromtxt(filename, delimiter=",", skip_header=1, max_rows=1, names="date", usecols=0,
    #                     converters={"date": dateconverter})
    time = np.genfromtxt(filename, delimiter=",", skip_header=header_lines, names="time", usecols=0,
                         converters={"time": timeconverter})
    current = np.genfromtxt(filename, delimiter=",", skip_header=header_lines, usecols=(range(2, 16, 1)))
    concentration = np.genfromtxt(filename, delimiter=",", skip_header=header_lines, usecols=(range(34, 48, 1)))
    return time, current, concentration


def data_reader(filenames):
    """runs the file_reader on the files in the tuple 'filenames'
    input: filenames (tuple with filenames from tkinter.askopenfilenames)
    output: time = datetime array (n, ) shape
            current = raw electrometer current array (n, stages) shape
            concentration = particle concentration calculated by elpi in 1/cm^3 array (n, stages) shape"""
    print(f"current file: {filenames[0]}")
    time, current, concentration = file_reader(filenames[0])
    for k in range(1, len(filenames), 1):
        print(f"current file: {filenames[k]}")
        k_time, k_current, k_concentration = file_reader(filenames[k])
        time = np.concatenate((time, k_time), axis=0)
        current = np.concatenate((current, k_current), axis=0)
        concentration = np.concatenate((concentration, k_concentration), axis=0)
    return time, current, concentration


def plot_profile(time, data, stage_min, stage_max):
    """plots the elpi measurement profile
    input: time = datetime array (n, ) shape
            data = array of data, e.g. current, or concentration (n, stages) shape
    output: plot of the given data with time on the x axis and the data on the y axis"""
    fig = plt.figure()
    ax = fig.add_subplot(111)
    colors = ('b', 'g', 'r', 'c', 'm', 'y', 'k', 'gray', 'chocolate', 'orange', 'darkolivegreen', 'aqua',
              'indigo', 'fuchsia')
    for stage in range(stage_min, stage_max):
        ax.plot_date(time, data[:, stage], label=f'stage{stage+1}', fmt='-', linewidth=1, color=colors[stage])
    ax.set_xlabel('datetime')
    ax.set_ylabel('concentration / P/cm$^{3}$')
    date_format = matplotlib.dates.DateFormatter('%d.%m\n%H:%M')
    ax.xaxis.set_major_formatter(date_format)
    ax.tick_params(direction='in')
    for axis in ['top', 'bottom', 'left', 'right']:
        ax.spines[axis].set_linewidth(1)
    # set(gcf, fontsize=12, fontname='Arial', linewidth=1, ticklength=[0.01, 0.005])
    # ax.set_ylabel('current / fA')
    #plt.grid(which='both')
    plt.legend(loc='upper right')
    # plt.title(filename)
    plt.show()
    return


def concentration_correction(data):
    """some datasets contained negative values, so those have to be corrected"""
    corr_data = abs(data)
    #corr_data = signal.savgol_filter(data, 3, 2)
    return corr_data


def particles_per_stage(concentration, time):
    """calculate the number of particles collected in one measurement per stage
    input:  concentration = array (measurement_points, stages)shape
            time = array (measurement_points, 1)shape
    output: n_particles_stage = list of the particle numbers per stage (14 values)"""
    n_particles_stage = []
    flow = 9820/60     # ccm/s
    print("particles per stage:")
    for stage in range(14): # iterate through all stages, to obtain the particle number for each stage separately
        particles = 0   # set the variable particles to 0 for the start
        for k in range(0, len(time)-1): # iterate through all measurement_points
            t_interval = (time[k+1]-time[k]).total_seconds()    # calculate the time between two measurement points
            particles_interval = concentration[k, stage] * flow * t_interval    # calculate the number of particles
            # collected in the time_interval under the assumption, that the particle concentration does not change in
            # the time_interval, but is the concentration of the first measurement point in the time_interval
            # it is an estimation, but for more accurate results probably an interpolation between the data points would
            # be better
            particles += particles_interval # add particles of the time_interval to total particles of this stage
        n_particles_stage.append(particles)
        print(f"stage {stage+1}: {particles}")
    return n_particles_stage


def mass_per_stage(n_particles_stage):
    """di = calculated geometric mean of a stage given in the elpi raw data sheet
    gives mass in micrograms"""
    standard_density = 1.5    # g/cm^3
    di = (0.0097, 0.0221, 0.0413, 0.0724, 0.1215, 0.2000, 0.3152, 0.4838, 0.7620, 1.2515, 2.0208, 3.0271, 4.4578,
          7.3301)   # um
    m_stage = []
    print("mass per stage in micrograms:")
    for stage in range(14):
        di_cm = di[stage]/1000  # conversion to cm
        vi = 1/6*(di_cm**3)*pi  # calculation of average particle volume on stage
        mi = vi*standard_density    # calculation of average mass per particle on stage
        m = n_particles_stage[stage]*mi*(10**6)  # calculation of total mass per stage
        m_stage.append(m)
        print(f"stage {stage+1}: {m}")
    return m_stage


if __name__ == "__main__":

    while True:
        Tk().withdraw()
        filenames = askopenfilenames()
        time, current, concentration = data_reader(filenames)
        #concentration = concentration_correction(concentration)
        n_particles_stage = particles_per_stage(concentration, time)
        mass_per_stage(n_particles_stage)
        plot_profile(matplotlib.dates.date2num(time), concentration, 0, 14)
