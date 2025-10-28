import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from math import pi as PI
from scipy.optimize import curve_fit

def lognormal_function(x, mu, sigma, A):
    return A*(np.exp(-((np.log(x/mu))**2)/(2*np.log(sigma)**2))/(np.log(sigma)*x*np.sqrt(2*PI)))

def create_n_modal_lognormal_function(n):
    # Create the function signature
    args = ['x'] + [f'mu{i + 1}, sigma{i + 1}, A{i + 1}' for i in range(n)]
    func_signature = ', '.join(args)
    # Create the function body
    func_body = ' + '.join([f'lognormal_function(x, mu{i + 1}, sigma{i + 1}, A{i + 1})' for i in range(n)])
    # Combine the signature and body into a function definition
    func_def = f"def n_modal_lognormal({func_signature}):\n    return {func_body}\n"

    # Execute the function definition
    exec(func_def, globals()) # n_modal_lognormal = exec(func_def, globals())
    return n_modal_lognormal

def create_bounds(modalität):
	bounds_1 = []
	bounds_2 = []
	bounds=(bounds_1,bounds_2)
	for i in range(1, modalität+1):
		bounds_1.append(0.1)
		bounds_1.append(1.0)
		bounds_1.append(0.1)
	for k in range(1, modalität+1):
		bounds_2.append(8500)
		bounds_2.append(np.inf)
		bounds_2.append(np.inf)
	return bounds

# to use save_parma_data(df, data, "fit1")
def save_parma_data(df, origin, fileaddition):
    path = origin["filename"][:-4] + fileaddition + 'output.xlsx'
    df.to_excel(path, sheet_name='Sheet1')
    return

#set of running parameters
initial_gess = (285.82, 2.6, 299299.88, 211.08, 1.38, 28371.53, 23.392, 1.39, 46609.89, 45.99, 1.34, 25491.47)

#feed data to workspace by calling: param, cov, df = full_function(4, mean_Dry_AS, initial_gess)
def full_function(n, data, scan_nr, initial_gess= initial_gess):
    b = create_bounds(n)
    fit_nr = scan_nr - 1
    function_type = create_n_modal_lognormal_function(n)
    params, cov = curve_fit(function_type, data["mean_X"][0], data["mean_C"][fit_nr],
                            p0=initial_gess,
                            bounds=(b),
                            method="trf")
    sigma = np.sqrt(np.diag(cov))
    plt.plot(data["mean_X"][0], function_type(data["mean_X"][0], *params),
             color='red', lw=3, label='multimodal fit')
    for k in range(0,n):
        plt.plot(data["mean_X"][0], lognormal_function(data["mean_X"][0], *params[k*3:(k+1)*3]),
             color='yellow', lw=1.5, ls=":", label=f"distribution {k+1}")
    plt.legend()
    plt.xscale("log")
    df = pd.DataFrame(data={'params': params, 'sigma': sigma}, index=create_n_modal_lognormal_function(n).__code__.co_varnames[1:])
    return params, cov, df


import numpy as np
import random
from scipy.signal import find_peaks


def generate_initial_guesses_from_data(
        data_row,
        x_array,
        height=10,
        distance=5,
        a2_range=(1.3, 4.0),
        a3_range=(100, 100000)
):
    """
    Detects peaks in a 1D data array and generates initial guesses for fitting.
    Parameters:
    data_row (array-like): 1D array of data values (e.g., concentrations).
    x_array (array-like): 1D array of corresponding x-axis values (e.g., sizes).
    height (float): Minimum height of peaks to detect.
    distance (int): Minimum distance between peaks.
    a2_range (tuple): Range (min, max) for random generation of a2 values.
    a3_range (tuple): Range (min, max) for random generation of a3 values.

    Returns:
            tuple: (initial_guess_list, number_of_modes)
                - initial_guess_list: [a1, a2, a3, b1, b2, b3, ...]
                - number_of_modes: int, number of detected peaks
    """

    # Detect peaks
    peaks, _ = find_peaks(data_row, height=height, distance=distance)
    num_modes = len(peaks)

    # Generate initial guesses
    initial_guess = []
    for peak_index in peaks:
        a1 = x_array[peak_index]  # Use x value at peak position
        a2 = random.uniform(*a2_range)
        a3 = random.uniform(*a3_range)
        initial_guess.extend([a1, a2, a3])
    return initial_guess, num_modes

# to run: initial_guess = generate_initial_guesses_from_data(Mean_LAS_250826['mean_C'][10], Mean_LAS_250826["mean_X"][10]);
# to run: full_function(initial_guess[1], Mean_LAS_250826, 11, initial_gess=initial_guess[0]);
