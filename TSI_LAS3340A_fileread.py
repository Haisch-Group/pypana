import numpy as np
import pandas as pd
from datetime import datetime
from Sup import get_filename


def import_data(filename):
    data = pd.read_table(filename, sep='\t')

    Cn = data.iloc[1:114, list(range(15, 114))] #important size values in column 15 to 114
    Cn = Cn.to_numpy()

    x_ax = data.columns.values[list(range(15, 114))] #extracts the midpoint diameter from the pd.dataframe header
    x_ax = list(x_ax.astype(float))
    upper_boundery = data.iloc[0,-1]
    x_ax.append(upper_boundery)
    x_axis = np.array(x_ax)

    n_bins = len(x_axis)-1

    delta_x = np.zeros(n_bins)
    mid_x = np.zeros(n_bins)

    for k in range(n_bins):
        delta_x[k] = x_axis[k + 1] - x_axis[k]
        mid_x[k] = (x_axis[k + 1] + x_axis[k])/2

    X = np.zeros(Cn.shape)
    bar_width = np.zeros(Cn.shape)

    time = []
    for i in np.arange(len(Cn)):
        X[i] = mid_x
        bar_width[i] = delta_x
        time.append(datetime.strptime(data.iloc[i+1, 0] + " " + data.iloc[i+1, 1][0:8]+ " " +data.iloc[i+1, 1][-2:], '%m/%d/%Y %I:%M:%S %p'))

    return X,bar_width,Cn,time


if __name__ == "__main__":

    filename = get_filename()
    X, bar_width, Cn, time = import_data(filename)