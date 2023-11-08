import pandas as pd


def save_calc_to_csv(data_dict, variable_list, fileaddition="_particleDF"):
    """saves selected variables to a csv file, select variables to save in variable_list as list of strings,
     allways use a different fileaddition when saving anything else than the data input array data_identifier"""
    path = data_dict["filename"][:-4]+fileaddition+".csv"
    dataframe = pd.DataFrame()
    for variable in variable_list:
        dataframe[variable] = data_dict[variable]
    print(f"wrote file with variables {variable_list} to csv with name {path}")
    dataframe.to_csv(path)
    return
