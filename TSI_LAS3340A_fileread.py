import numpy as np
import pandas as pd
from datetime import datetime
from Sup import get_filename
from Sup import get_filenames


def import_single_data(filename):
    data = pd.read_table(filename, sep='\t')

    Cn = data.iloc[1:114, list(range(15, 114))]  # important size values in column 15 to 114
    Cn = Cn.to_numpy()

    x_ax = data.columns.values[list(range(15, 114))]  # extracts the midpoint diameter from the pd.dataframe header
    x_ax = list(x_ax.astype(float))
    upper_boundery = data.iloc[0,-1]
    x_ax.append(upper_boundery)
    x_axis = np.array(x_ax)

    n_bins = len(x_axis)-1

    delta_x = np.zeros(n_bins)
    mid_x = np.zeros(n_bins)

    for k in range(n_bins):
        delta_x[k] = x_axis[k + 1] - x_axis[k]
        mid_x[k] = (x_axis[k + 1] + x_axis[k])/2  # passt der, oder müsste das aus dem log berechnet werden?

    X = np.zeros(Cn.shape)
    bar_width = np.zeros(Cn.shape)
    n_scans = len(Cn)

    time = []
    for i in np.arange(n_scans):
        X[i] = mid_x
        bar_width[i] = delta_x
        time.append(datetime.strptime(data.iloc[i+1, 0] + " " + data.iloc[i+1, 1][0:8]+ " " +data.iloc[i+1, 1][-2:],
                                      '%m/%d/%Y %I:%M:%S %p'))

    return X, bar_width, Cn, time, n_scans


def import_data(filenames):
    n_scans=[]
    X, bar_width, Cn, time, n_scans_i = import_single_data(filenames[0])
    n_scans.append(n_scans_i)
    for filename in filenames[1:]:
        X_i, bar_width_i, Cn_i, time_i, n_scans_i = import_single_data(filename)
        X = np.concatenate((X, X_i))
        bar_width = np.concatenate((bar_width, bar_width_i))
        Cn = np.concatenate((Cn, Cn_i))
        time.append(time_i)
        n_scans.append(n_scans_i)
    return X, bar_width, Cn, time # , n_scans


if __name__ == "__main__":

    filenames = get_filenames()
    X, bar_width, Cn, time = import_data(filenames)
    # X, bar_width, Cn, time, n_scans = import_data(filenames)
