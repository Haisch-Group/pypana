"""
Particle_analysis.py

Script for Particle Data Evaluation
Data has to be imported by the import function suitable for the used device

Created 2023-05 from SMPS_analysis.py
Modified 2024-03-20 to also run CPC_analysis.py which was renamed to Conc.py
@written by Kevin Maier (kevin.r.maier@tum.de)

modified 2024-06 to 2025-11 to work with new data structure
"""

import dill
import pandas as pd

# from matplotlib import ticker
# from scipy import optimize
# import scipy.integrate as integrate
# from matplotlib import cm as colormap
import Def  # definitions

# import Imp  #import functions
import Sup  # supporting functions


def get_data(method="prompt", used_device="", filename="", data_choice=""):
    if method == "fixed":
        used_device = Sup.check_device(used_device)
        fr = __import__(Def.device_list["Import_Script"][used_device])
        data = fr.import_data_dict(
            used_device=used_device, filename=filename, data_choice=data_choice
        )
    else:
        print(
            Def.device_list[["Device_Identifier", "Device", "Manufacturer"]].to_string(
                justify="left", index=False
            )
        )
        used_device = int(
            input("Which instrument do you want to import data from? Enter as int.")
        )
        used_device = Sup.check_device(used_device)
        fr = __import__(Def.device_list["Import_Script"][used_device])
        filename = Sup.decide_filename_function(used_device)
        data = fr.import_data_dict(used_device, filename, data_choice=data_choice)

    # data["add_info"].dropna(axis=1, how="all", inplace=True)
    data["results"] = data["add_info"][["Scan Nr", "Time", "Comment"]].copy()
    # create results array from add_info to save all the calculated values in there -> makes print easier too
    return data


def save_data_to_xlsx(data_dict, fileaddition="particleDF", save_arrays="all"):
    """saves selected variables to a csv file, select variables to save in variable_list as list of strings,
    allways use a different fileaddition when saving anything else than the data input array data_identifier"""
    # data_identifier = Sup.get_variable_name(data_dict)
    path = (
        data_dict["filename"][:-4] + "_" + fileaddition + ".xlsx"
    )  # was .csv with older function
    # path = data_dict["filename"][:-4] + "_" + data_identifier + "_" + fileaddition + ".csv"
    identity = (
        ["used_device", "filename"],
        [data_dict["used_device"], data_dict["filename"]],
    )
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame(identity).to_excel(writer, sheet_name="identity")
        data_dict["results"].to_excel(
            writer, sheet_name="results"
        )  # alternative: dataframe.to_csv(path)
        data_dict["add_info"].to_excel(writer, sheet_name="add_info")
        if (
            save_arrays == None
        ):  # save only the indentity, results and add_info arrays from data_dict
            pass
        elif save_arrays == "all":
            skip_arrays = ["add_info", "results", "used_device", "filename"]
            data_keys = list(data_dict.keys())
            [data_keys.remove(key) for key in skip_arrays]
            for key in data_keys:
                pd.DataFrame(data_dict[key]).to_excel(writer, sheet_name=key)
        else:
            for (
                array
            ) in save_arrays:  # choose specific keys and give them as list of strings
                pd.DataFrame(data_dict[array]).to_excel(writer, sheet_name=array)
    print(f"wrote data to file with name {path}")


def save_session():
    filename = Sup.set_filename()
    path = f"{filename}" + ".dill"
    dill.dump_module(path, "__main__")


def load_session():
    path = Sup.get_filename()
    dill.load_module(path)


if __name__ == "__main__":
    print("Particle_analysis.py started")
    # data = get_data()
