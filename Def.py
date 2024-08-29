# -*- coding: utf-8 -*-
"""
Def.py

Definitions for running Particle_analysis.py

Created 2024-08-29
@written by Kevin Maier (kevin.r.maier@tum.de)

"""

import pandas as pd

device_list = pd.DataFrame([
    [0, "SMPS 3071", "TSI", "Number Distribution", "Electrodynamic", "nm", "TSI_SMPS3071_fileread"],
    [1, "SMPS 3938", "TSI", "Number Distribution", "Electrodynamic", "nm", "TSI_SMPS3938_fileread"],
    [2, "U-SMPS", "PALAS", "Number Distribution", "Electrodynamic", "nm", "PALAS_USMPS_fileread"],
    [3, "APS 3321", "TSI", "Number Distribution", "Aerodynamic", u"\xb5m", "TSI_APS3321_fileread"],
    [4, "WELAS", "PALAS", "Number Distribution", "Optical", u"\xb5m", "PALAS_WELAS_fileread"],
    [5, "LAS 3340A", "TSI", "Number Distribution", "Optical", u"\xb5m", "TSI_LAS3340A_fileread"],
    [6, "CPC 3775", "TSI", "Number Concentration", "Condensation", u"nm-\xb5m", "TSI_CPC3775_fileread"],
    [7, "UF-CPC", "PALAS", "Number Concentration", "Condensation", u"nm-\xb5m", "PALAS_UFCPC_fileread"],
    [8, "ELPI+", "DEKATI", "Number Distribution", "Aerodynamic", u"nm-\xb5m", "DEKATI_ELPI+_fileread"],
    [9, "APS 3310", "TSI", "Number Concentration", "Aerodynamic", u"nm-\xb5m", "TSI_APS3310_fileread"],
    [10, "EM 3068", "TSI", "Number Concentration", "Electrical Charge", "nm", "TSI_EM3068_fileread"]
], columns=["Device_Identifier", "Device", "Manufacturer", "Accquired_Data", "Working_Principle", "Measuring_Range",
            "Import_Script"])

if __name__ == "__main__":

    print(device_list.to_string(index=False, justify="left"))
