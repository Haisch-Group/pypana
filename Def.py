# -*- coding: utf-8 -*-
"""
Def.py

Definitions for running Particle_analysis.py

Created 2024-08-29
@written by Kevin Maier (kevin.r.maier@tum.de)

"""

import pandas as pd

device_list = pd.DataFrame([
    [0, "SMPS 3071", "TSI", "Number Distribution", "Electrodynamic", "nm", "TSI_SMPS_fileread"],
    [1, "SMPS 3938", "TSI", "Number Distribution", "Electrodynamic", "nm", "TSI_SMPS_fileread"],
    [2, "U-SMPS", "PALAS", "Number Distribution", "Electrodynamic", "nm", "PALAS_USMPS_fileread"],
    [3, "APS 3321", "TSI", "Number Distribution", "Aerodynamic", u"\xb5m", "TSI_APS3321_fileread"],
    [4, "WELAS", "PALAS", "Number Distribution", "Optical", u"\xb5m", "PALAS_WELAS_fileread"],
    [5, "LAS 3340A", "TSI", "Number Distribution", "Optical", u"\xb5m in nm", "TSI_LAS3340A_fileread"],
    [6, "CPC 3775", "TSI", "Number Concentration", "Condensation", u"\xb5m", "TSI_CPC3775_fileread"],
    [7, "UF-CPC", "PALAS", "Number Concentration", "Condensation", u"\xb5m", "PALAS_UFCPC_fileread"],
    [8, "ELPI+", "DEKATI", "Number Distribution", "Aerodynamic", u"\xb5m", "DEKATI_ELPI+_fileread"],
    [9, "APS 3310", "TSI", "Number Concentration", "Aerodynamic", u"\xb5m", "TSI_APS3310_fileread"],
    [10, "EM 3068", "TSI", "Number Concentration", "Electrical Charge", "nm", "TSI_EM3068_fileread"]
], columns=["Device_Identifier", "Device", "Manufacturer", "Accquired_Data", "Working_Principle", "Size_Plot_Range",
            "Import_Script"])

all_parameters = [['Absolute Pressure / mbar', 'Actual Differential Pressure / Pa"' 'Aerosol Flow / L/min'],
                  ['Bypass Flow / L/min'],
                  ['Comment', 'CPC Inlet Flow / L/min', 'CPC Sample Flow / L/min',
                   'Counter Type (0=CPC, 1=Elektrometer)'],
                  ['D50 / nm', 'Date', u'Density / g/cm\u00B3', 'Diameter Midpoint / nm', 'Diff Pressure Impactor / Pa',
                   'Down Scan First'],
                  ['Empty Field', 'Error Notification (0=no Error, 1 = Error'],
                  [u'Gas Viscosity / Pa\u00B7s', 'Geo. Mean / nm', 'Geo. Std. Dev.'],
                  ['High Voltage / V', 'HV Polarity (0=positive, 1=negative)'],
                  ['Impactor Type / cm','Inner Diameter Column / mm', 'Instrument Errors', 'Instrument ID'],
                  ['Lab ID', 'Leak Test and Leakage Rate', 'Length Column / mm', 'Low Voltage / V', 'Lower Size / nm'],
                  ['Mean / nm', u'Mean Droplet size / \u00B5m', 'Mean Free Path / m',
                   u'1s Mean Particle Concentration / 1/cm\u00B3', u'10s Mean Particle Concentration / 1/cm\u00B3',
                   'Median / nm', 'Mode / nm'],
                  ['Neutralizer Status', 'Neutralizer Type (0=Kr-85, 1=X-Ray)'],
                  ['Operating Mode DSI (0=off, 1=Humidity, 2=Diiferential Pressure)', 'Outer Diameter Column / mm'],
                  ['Position of Valve in MSS 08 (1-8)', 'Power of Pump %', 'Pre Scan Stabilisation Time / s'],
                  ['Relative Humidity %', 'Relative Humidity Aerosol %', 'Retrace Time / s'],
                  ['Sample #', 'Sample ID', 'Sample Pressure / kPa', 'Sample Temp / °C', 'Scan Resolution / Hz',
                   'Scan Time / s', 'Scan Type (0=up, 1=down, 2=up+down_avg, 3=up+down_single)', 'Scans Per Sample',
                   'Set Aerosol Flow / L/min', 'Set Sheath Flow / L/min',
                   'Sheath Flow / L/min', 'Sheath Temp / °C', 'Start Time',
                   'Status Flag'],
                  ['T Aerosol Inlet / C', 'T Condenser / °C', 'T Saturator / °C', 'Target Relative Humidity %',
                   'Target Differential Pressure / Pa', 'td / s', 'td + 0.5 / s', 'tf / s', 'Time', 'Title',
                   u'Total Conc. 1/cm\u00B3', 'Transfer-Function A', 'Transfer-Function d', 'Transfer-Function C'],
                  ['Upper Size / nm', 'User Name']]


elementary_charge = 1.602176634*10**(-19)  # in Coulomb = As https://physics.nist.gov/cgi-bin/cuu/Value?e

if __name__ == "__main__":

    print(device_list.to_string(index=False, justify="left"))
