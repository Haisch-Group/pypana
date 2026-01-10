# -*- coding: utf-8 -*-
"""
Def.py

Definitions for running Particle_analysis.py

Created 2024-08-29
@written by Kevin Maier (kevin.r.maier@tum.de)

"""
import pandas as pd
from matplotlib import colormaps as cmp

device_list = pd.DataFrame([
    [0, "SMPS 3071",
     "TSI", "Number Distribution", "Electrodynamic", "nm", "TSI_SMPS_fileread", ([10, 20, 50, 100, 200, 400, 800], [10, 20, 50, 100, 200, 400, 800])],
    [1, "SMPS 3938",
     "TSI", "Number Distribution", "Electrodynamic", "nm", "TSI_SMPS_fileread", ([10, 20, 50, 100, 200, 400, 800], [10, 20, 50, 100, 200, 400, 800])],
    [2, "U-SMPS",
     "PALAS", "Number Distribution", "Electrodynamic", "nm", "PALAS_USMPS_fileread", ([10, 20, 50, 100, 200, 400, 800], [10, 20, 50, 100, 200, 400, 800])],
    [3, "APS 3321",
     "TSI", "Number Distribution", "Aerodynamic", u"\xb5m", "TSI_APS3321_fileread", ([0.5, 1, 2, 5, 10],[0.5, 1, 2, 5, 10])],
    [4, "WELAS",
     "PALAS", "Number Distribution", "Optical", u"\xb5m", "PALAS_WELAS_fileread", ([0.5, 1, 2, 5, 10],[0.5, 1, 2, 5, 10])],
    [5, "LAS 3340A",
     "TSI", "Number Distribution", "Optical", u"nm", "TSI_LAS3340A_fileread", ([100, 500, 1000, 2000, 5000, 10000], [0.1, 0.5, 1, 2, 5, 10])],
    [6, "CPC 3775",
     "TSI", "Number Concentration", "Condensation", "nm", "TSI_CPC3775_fileread", ""],
    [7, "UF-CPC",
     "PALAS", "Number Concentration", "Condensation", u"nm", "PALAS_UFCPC_fileread", ""],
    [8, "ELPI+",
     "DEKATI", "Number Distribution", "Aerodynamic", u"\xb5m", "DEKATI_ELPIplus_fileread", ([0.5, 1, 2, 5, 10],[0.5, 1, 2, 5, 10])],
    [9, "APS 3310",
     "TSI", "Number Concentration", "Aerodynamic", u"\xb5m", "TSI_APS3310_fileread", ([0.5, 1, 2, 5, 10],[0.5, 1, 2, 5, 10])],
    [10, "EM 3068",
     "TSI", "Number Concentration", "Electrical Charge", "nm", "TSI_EM3068_fileread", ""]
    ],
    columns=["Device_Identifier", "Device", "Manufacturer", "Accquired_Data", "Working_Principle", "Size_Unit",
            "Import_Script", "Standard_Size_Range (xticks, xticklabels)"])

all_parameters = [['Absolute Pressure / mbar', 'Actual Differential Pressure / Pa', 'Aerodynamic Diameter',
                   'Aerosol Flow / L/min', 'Analog Input Voltage 0', 'Analog Input Voltage 1',
                   'Avalanch Photo Diode Temperature / °C', 'Avalanch Photo Diode Voltage / V'],
                  ['Box Temperature / °C', 'Bypass Flow / L/min'],
                  ['Comment', 'CPC Inlet Flow / L/min', 'CPC Sample Flow / L/min',
                   'Counter Type (0=CPC, 1=Elektrometer)'],
                  ['D50 / nm', 'Date', 'Dead Time', u'Density / g/cm\u00B3', 'Diameter Midpoint / nm',
                   'Diff Pressure Impactor / Pa', 'Digital Input Level 0', 'Digital Input Level 1', 'Down Scan First'],
                  ['Empty Field', 'Error Notification (0=no Error, 1 = Error)', 'Event 1', 'Event 3', 'Event 4'],
                  [u'Gas Viscosity / Pa\u00B7s', 'Geo. Mean / nm', u'Geo. Mean / \xb5m', 'Geo. Std. Dev.'],
                  ['High Voltage / V', 'HV Polarity (0=positive, 1=negative)'],
                  ['Impactor Type / cm','Inner Diameter Column / mm', 'Instrument Errors', 'Instrument ID'],
                  ['Lab ID', 'Laser Current / mA', 'Laser Power %', 'Leak Test and Leakage Rate', 'Length Column / mm',
                   'Low Voltage / V', 'Lower Size / nm'],
                  ['Mean / nm', u'Mean Droplet size / \u00B5m', 'Mean Free Path / m',
                   u'1s Mean Particle Concentration / 1/cm\u00B3', u'10s Mean Particle Concentration / 1/cm\u00B3',
                   u'Mean / \xb5m', 'Median / nm', u'Median / \xb5m', 'Mode / nm', u'Mode / \xb5m'],
                  ['Neutralizer Status', 'Neutralizer Type (0=Kr-85, 1=X-Ray)'],
                  ['Operating Mode DSI (0=off, 1=Humidity, 2=Diiferential Pressure)', 'Outer Diameter Column / mm'],
                  ['Position of Valve in MSS 08 (1-8)', 'Power of Pump %', 'Pre Scan Stabilisation Time / s'],
                  ['Relative Humidity %', 'Relative Humidity Aerosol %', 'Retrace Time / s'],
                  ['Sample #', 'Sample ID', 'Sample Pressure / kPa', 'Sample Pressure / mbar', 'Sample Temp / °C',
                   'Scan Resolution / Hz', 'Scan Time / s', 'Scan Type (0=up, 1=down, 2=up+down_avg, 3=up+down_single)',
                   'Scans Per Sample', 'Set Aerosol Flow / L/min', 'Set Sheath Flow / L/min',
                   'Sheath Flow / L/min', 'Sheath Pump Voltage / V', 'Sheath Temp / °C', 'Start Time',
                   'Status Flag', 'Status Flags'],
                  ['T Aerosol Inlet / C', 'T Condenser / °C', 'T Saturator / °C', 'Target Relative Humidity %',
                   'Target Differential Pressure / Pa', 'td / s', 'td + 0.5 / s', 'tf / s', 'Time', 'Title',
                   u'Total Conc. 1/cm\u00B3', 'Total Flow / L/min', 'Total Pump Voltage / V', 'Transfer-Function A',
                   'Transfer-Function d', 'Transfer-Function C'],
                  ['Upper Size / nm', 'User Name']]


elementary_charge = 1.602176634*10**(-19)  # in Coulomb = As https://physics.nist.gov/cgi-bin/cuu/Value?e

TSI_standard_conditions = {'T / K': 294.26, 'Pressure / kPa': 101.3}  # values given in TSI Application Note FLOW-004 as
# 21.11°C and 101.3 kPa

std_cm = cmp["tab10"].colors

tum_corp_cls = {"black": (0, 0, 0, 1),
           "blue": (0, 101/256, 189/256, 1),
           "grey-80": (0, 0, 0, 0.8),
           "grey-50": (0, 0, 0, 0.5),
           "grey-20": (0, 0, 0, 0.2),
           "darker-blue": (0, 82/256, 147/256, 1),
           "very-dark-blue": (0, 51/256, 89/256, 1),
           "very-light-blue": (152/256, 198/256, 234/256, 1),
           "light-blue": (100/256, 160/256, 200/256, 1),
           "ivory": (218/256, 215/256, 203/256, 1),
           "orange": (227/256, 114/256, 34/256, 1),
           "green": (162/256, 173/256, 0, 1)
           }  # in RGBA red green blue alpha

tum_corp_cm = (tum_corp_cls["blue"],
          tum_corp_cls["very-light-blue"],
          tum_corp_cls["orange"],
          tum_corp_cls["green"],
          tum_corp_cls["grey-50"],
          tum_corp_cls["very-dark-blue"],
          tum_corp_cls["light-blue"],
          tum_corp_cls["ivory"])

tum_plot_cls = {"purple": (105/256, 8/256, 90/256, 1),
                "dark blue": (15/256, 27/256, 95/256, 1),
                "light blue": (0, 119/256, 138/256, 1),
                "green": (0, 124/256, 48/256, 1),
                "grass green": (103/256, 154/256, 29/256, 1),
                "yellow": (255/256, 220/256, 0, 1),
                "dark yellow": (249/256, 186/256, 0/256, 1),
                "orange": (214/256, 76/256, 19/256, 1),
                "red": (196/256, 7/256, 27/256, 1),
                "dark red": (156/256, 13/256, 22/256, 1)
                }

tum_plot_cm = (tum_plot_cls["purple"],
               tum_plot_cls["dark blue"],
               tum_plot_cls["light blue"],
               tum_plot_cls["green"],
               tum_plot_cls["grass green"],
               tum_plot_cls["yellow"],
               tum_plot_cls["dark yellow"],
               tum_plot_cls["orange"],
               tum_plot_cls["red"],
               tum_plot_cls["dark red"])

kevin_cls = {"add 1": (157/256, 81/256, 140/256, 1),
             "add 2": (183/256, 63/256, 63/256, 1),
             "add 3": (194/256, 164/256, 17/256, 1),
             "add 4": (81/256, 128/256, 74/256,1)}

kevin_cm = (tum_corp_cls["blue"],
            kevin_cls["add 1"],
            kevin_cls["add 2"],
            tum_corp_cls["orange"],
            kevin_cls["add 3"],
            tum_corp_cls["green"],
            kevin_cls["add 4"],
            tum_corp_cls["ivory"])

fhg_cls = {"black": (0, 0, 0, 1),
           "fhg-green": (23/256, 156/256, 125/256, 1),
           "steel-blue": (0/256, 91/256, 127/256, 1),
           "silver-grey": (166/256, 187/256, 200/256, 1),
           "orange": (245/256, 130/256, 32/256, 1),
           "graphit": (28/256, 63/256, 82/256, 1),
           "sand": (211/256, 199/256, 174/256, 1),
           "petrol": (0/256, 133/256, 152/256, 1),
           "aqua": (57/256, 193/256, 205/256, 1),
           "lime": (178/256, 210/256, 53/256, 1),
           "gelb": (253/256, 185/256, 19/256, 1),
           "rot": (187/256, 0/256, 86/256, 1),
           "weinrot": (124/256, 21/256, 77/256, 1)
           }  # in RGBA red green blue alpha

fhg_cm = (fhg_cls["fhg-green"],
          fhg_cls["steel-blue"],
          fhg_cls["orange"],
          fhg_cls["silver-grey"],
          fhg_cls["weinrot"],
          fhg_cls["petrol"],
          fhg_cls["aqua"],
          fhg_cls["lime"])

default_cm = kevin_cm

if __name__ == "__main__":

    print(device_list.to_string(index=False, justify="left"))
