"""
TSI_CPC3775_fileread.py

Script for Data import of the TSI CPC 3775
Data has to be exported in rows

Created 2022-03-10
@written by Kevin Maier (kevin.r.maier@tum.de)

2022-03-24 finished import_data function to produce Cn, el_time, start_time
2024-06 to 2025-11 updated to work with new data structure
"""

from datetime import datetime

import numpy as np
import pandas as pd
from sup import get_filename

from _v1.defs import device_list


def rename_columns(df):
    """rename the columns, so they follow the same schematic for all devices"""
    mapping = {
        "Sample Length": "Sample Length / s",
        "Averaging Interval (s)": "Averaging Interval / s",
        "Conc Mean": "Conc Mean / 1/cm\u00b3",
        "Conc Min": "Conc Min / 1/cm\u00b3",
        "Conc Max": "Conc Max / 1/cm\u00b3",
        "Conc Std Dev": "Conc Std Dev / 1/cm\u00b3",
    }
    df.rename(columns=mapping, inplace=True)
    return df


def import_data(filename, data_choice=""):
    """import cpc data from txt file with name filename to pd dataframe, also includes time, some settings and some
    statistical values calculated by the TSI program
    then extract the actual measuring data from the dataframe and give Cn, el_time, start_time
    to work, the data has to be exported in rows"""

    data = pd.read_table(
        filename, sep="\t", header=2, engine="python", encoding="iso-8859-1"
    )  # originally ansi which
    # is superset of iso
    # file is in encoding = ansi which caused an import error off cm^3 due to wrong encoding setting
    # changed to iso as ansi is windows only and iso also works on linux -> if error reoccurs quick fix is to recode the
    # measurement file, which is not a nice, but a quick solution. :D

    data = rename_columns(
        data
    )  # change names of the array to match the other input files schematic

    parameter_list = [
        "Sample #",
        "Start Date",
        "Start Time",
        "Sample Length / s",
        "Averaging Interval / s",
        "Title",
        "Instrument ID",
        "Instrument Errors",
        "Conc Mean / 1/cm\u00b3",
        "Conc Min / 1/cm\u00b3",
        "Conc Max / 1/cm\u00b3",
        "Conc Std Dev / 1/cm\u00b3",
    ]
    # parameters as displayed in txt file

    conc = data[
        data.columns.difference(parameter_list, sort=False)
    ].to_numpy()  # somehow in the file there is an empty
    # column attached, used -1 below when copying from conc to Cn array to not have empty values
    add_info = data[
        (parameter_list[3:])
    ]  # copying the infos from the imported dataframe to add_info dataframe using
    # the paramter_list omitting the sample number and datetime parameters as they are added later

    avg_interval = data.loc[:, "Averaging Interval / s"].astype(float).to_numpy()
    sample_length = data.loc[:, "Sample Length / s"].astype(float).to_numpy()
    # data is saved every n seconds for a set amount of time, which is saved in the parameters Averaging Interval and
    # Sample Length, put them into a numpy array each, so timepoints can be calculated without loops

    timepoints = (
        sample_length / avg_interval
    )  # calculates how many timepoints are in one measurement to pre-allocate
    # arrays later

    # when exporting measurement data, also raw counts can be exported, if so, every second column contains the raw
    # counts, to automatically adjust for that, the following factor is introduced based on the length of the conc array
    if int(max(timepoints)) == conc.shape[1] - 1:  # when no raw counts are contained
        factor = 1
    else:
        factor = int((conc.shape[1] - 1) / int(max(timepoints)))
        # when more different counts are exported, the factor is automatically adjusted

    Cn = np.full(
        (len(data), int(max(timepoints))), np.nan
    )  # pre-allocation of Cn and el_time arrays done with max, as i
    # thought, it might be the case, that there are measurements of different length in one file which could happen if
    # the measurement is abandoned while running, as shown in 20230223_TSI_CPC3775_variablelength file
    el_time = np.full((len(data), int(max(timepoints))), np.nan)
    # filling with NaN to not have wrong numbers in there
    start_time = []

    for i in range(len(data)):  # filling start_time, Cn and el_time with values
        start_time.append(
            datetime.strptime(
                data.loc[i, "Start Date"] + " " + data.loc[i, "Start Time"],
                "%m/%d/%y %H:%M:%S",
            )
        )
        for k in range(
            int(timepoints[i])
        ):  # -1 as there is an empty column at the end of each file
            Cn[i, k] = conc[
                i, 0 + k * factor
            ]  # k times factor selects every kth row when counts were also exported to the
            # txt file for example
            el_time[i, k] = (
                k * avg_interval[i] + 1
            )  # el_time fills from known averaging interval for each msmt

    add_info.insert(loc=0, column="Comment", value="")
    add_info.insert(loc=0, column="Time", value=start_time)
    add_info.insert(loc=0, column="Scan Nr", value=data["Sample #"])

    return Cn, el_time, add_info


def import_data_dict(used_device, filename, data_choice=""):
    # filename = get_filename()
    Cn, el_time, add_info = import_data(filename)
    data_dict = {
        "Cn": Cn,
        "el_time": el_time,
        "filename": filename,
        "used_device": used_device,
        "add_info": add_info,
    }
    return data_dict


if __name__ == "__main__":
    filename = get_filename()
    # Cn, el_time, add_info = import_data(filename)
    # print(f"imported {filename}")

    data_dict = import_data_dict(
        device_list.query("Import_Script=='TSI_CPC3775_fileread'")[
            "Device_Identifier"
        ].values[0],
        filename,
    )
    print(f"imported {data_dict['filename']} as dictionary")
