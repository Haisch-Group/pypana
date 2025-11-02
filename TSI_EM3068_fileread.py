# -*- coding: utf-8 -*-
"""
TSI_EM3068_fileread.py

Script for Data Evaluation of the TSI EM 3068 Data acquired via NI-Card and Self-Written Labview Script
The electrometer has a noise current of 1x10^15 ampere according to the manual (and i think there should be a - in the
power)
The output voltage is in a range of 0-10 volts, which correspond to a current of 0-10 picoampere
Created 2024-08-29
@written by Kevin Maier (kevin.r.maier@tum.de)

"""
import numpy as np
import pandas as pd

from Sup import get_filename
from Def import device_list
from datetime import datetime
from datetime import timedelta
from Def import elementary_charge


def voltage_to_conc(voltage, flowrate_ccs, n_charges=1):
    """calculates the particle concentration of an aerosol in particles per cubic centimeter from a given voltage with
    1V corresponding to 10**(-12) ampere, the number of elementary charges per particle and the aerosol flow rate
    formula given in manual of TSI EM3068
    elementary charge is in C = As, current in A, so flowrate must be in ccm/s"""
    amp = voltage*10**(-12)
    conc = amp/(n_charges*elementary_charge*flowrate_ccs)
    return conc


def import_data(filename):
    """"""
    data = np.genfromtxt(filename, delimiter='\t', skip_header=1)
    # load data into numpy array delimited by tab
    # first column is Sample Number added in the LabView Program manually
    # second column is the elapsed time since the start of the program in s
    # third column is the measured electrometer voltage in V

    flowrate = input("Please enter the used flow rate as float in L/min")
    flowrate_ccs = float(flowrate)*1000/60
    # manual_start = input("Please enter the start time of the measurement in format mm/dd/yyyy hh:mm:ss AM")
    # start = datetime.strptime(manual_start, '%m/%d/%Y %I:%M:%S %p')
    start = datetime.strptime("01/01/1900 00:00:00", '%m/%d/%Y %H:%M:%S')  # arbitrary start time as it is not
    # logged at the moment, so start_time will rather be a reference from the start of the first measurement

    # preallocation of lists that become lists of lists in the following section
    em_voltage = []
    sub_em_voltage = []
    tot_el_time = []
    sub_el_time = []
    scan_nr = []
    flow_list = []
    sub_flow_list = []
    comment_list = []
    counter = 1

    # Filling sub_em_voltage and sub_el_time with values every time a new entry that is not zero is found in the sample
    # number column. When the entry changes to a new sample number, the sub... lists are saved to the em_voltage and
    # tot_el_time lists. Also, a counter runs with it to fill the scan_nr list every time the sub... lists are copied
    # flow_list just runs withit filling the same value consantly, as the flow is not logged currently, but that could
    # be changed in the future
    for k in range(1, len(data)):  # runs through all the data line by line
        if data[k, 0] == 0:  # when the first column value in the line is 0, no sample was saved, so it is skipped
            continue
        elif data[k, 0] != 0 and data[k, 0] != data[k - 1, 0]:  # when the first column value is not zero and is
            # different from the last first column value, a new measurement is started
            if len(sub_el_time) == 0:  # if the length of the sub... list is 0, no measurement was saved in it before
                sub_em_voltage.append(data[k, 2])  # so only the new measurement is appended to it
                sub_el_time.append(data[k, 1])
                sub_flow_list.append(flowrate)
                comment_list.append(str(data[k, 0]))
            else:  # if the length is not zero, a measurement was saved in it before, so the data of the sub... lists is
                em_voltage.append(sub_em_voltage)  # transferred to em_voltage and tot_el_time
                tot_el_time.append(sub_el_time)
                flow_list.append(sub_flow_list)
                scan_nr.append(counter)  # also a scan number is added to the scan_nr list
                comment_list.append((data[k, 0]))
                counter += 1  # the new scan number for the next measurement is set
                sub_em_voltage = []  # the sub... lists are reset for saving the next measurements
                sub_el_time = []
                sub_flow_list = []
                sub_em_voltage.append(data[k, 2])  # the first entry of the new measurement is saved to the sub... lists
                sub_el_time.append(data[k, 1])
                sub_flow_list.append(flowrate)
        elif data[k, 0] != 0 and data[k, 0] == data[k-1, 0]:  # if the first column value is not zero and is the same as
            sub_em_voltage.append(data[k, 2])  # the value before, the measurement entry  belongs to the same
            sub_el_time.append(data[k, 1])  # measurement, so it is added to the sub... list
            sub_flow_list.append(flowrate)
    em_voltage.append(sub_em_voltage)  # at the end of the loop, the sub lists have to be saved into em_voltage and
    tot_el_time.append(sub_el_time)  # tot_el_time to also save the last measurement taken
    flow_list.append(sub_flow_list)
    scan_nr.append(counter)

    nr_scans = len(scan_nr)  # get number of scans for preallocation of arrays
    max_length = max(map(len, tot_el_time))  # get length of longest measurement for preallocation of arrays

    # Preallocation of all arrays and lists that should be exported
    el_time = np.zeros((nr_scans, max_length))
    el_time[:] = np.nan
    Cn = np.zeros((nr_scans, max_length))
    Cn[:] = np.nan
    flow_lpm = np.zeros((nr_scans, max_length))
    flow_lpm[:] = np.nan
    start_time = []

    for k in range(nr_scans):
        for i in range(len(tot_el_time[k])):  # fill el_time and Cn arrays with values from lists of lists
            el_time[k, i] = tot_el_time[k][i] - tot_el_time[k][0]
            Cn[k, i] = voltage_to_conc(em_voltage[k][i], flowrate_ccs)  # calculate concentration from voltage values
            flow_lpm[k, i] = flow_list[k][i]
        start_time.append(start+timedelta(0, tot_el_time[k][0]))  # add elapsed time at beginning of the
        # measurement to the start and by that fill the start_time list with times since the start of the measurement

    add_info = pd.DataFrame({"Scan Nr": scan_nr, "Time": start_time, "Comment": comment_list,
                             "Aerosol Flow (L/min)": list(flow_lpm)})
    # passed flow_lpm in add_info as list, when more actions should be done with flow rate, I would move it out of
    # add_info and make it a dictionary entry on its own

    return Cn, el_time, add_info


def import_data_dict(used_device, filename):
    # filename = get_filename()
    Cn, el_time, add_info = import_data(filename)
    data_dict = {"Cn": Cn, "el_time": el_time, "filename": filename, "used_device": used_device, "add_info": add_info}
    return data_dict


if __name__ == "__main__":

    filename = get_filename()
    # Cn, el_time, add_info = import_data(filename)
    # print(f"imported {filename}")

    data_dict = \
        import_data_dict(device_list.query("Import_Script=='TSI_EM3068_fileread'")["Device_Identifier"].values[0], filename)
    print(f"imported {data_dict['filename']} as dictionary")
