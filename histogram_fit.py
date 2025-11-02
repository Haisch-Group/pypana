import matplotlib.pyplot as plt  # KM already in Dist
import numpy as np  # KM already in Dist
import pandas as pd  # KM already in Dist
import math  # KM already in Dist but as math only -> rewrite to import math -> done, was only one use
from scipy import optimize # KM already in Dist sd optimize -> rewrite -> done, was only one use
import Sup

def lognormal_function(x, mu, sigma, A):
    """just definition of the lognormal function that should be fitted"""
    return A*(np.exp(-((np.log(x/mu))**2)/(2*np.log(sigma)**2))/(np.log(sigma)*x*np.sqrt(2*math.pi)))

def create_n_modal_lognormal_function(n):
    """produce n-modal lognormal function as linear combination of multiple lognormal_functions as defined above with n
    being the number of contained single functions"""
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

def create_bounds(modality):
	bounds_1 = []
	bounds_2 = []
	bounds=(bounds_1,bounds_2)
	for i in range(1, modality+1):
		bounds_1.append(0.1)
		bounds_1.append(1.0)
		bounds_1.append(0.1)
	for k in range(1, modality+1):
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
initial_guess = (285.82, 2.6, 299299.88, 211.08, 1.38, 28371.53, 23.392, 1.39, 46609.89, 45.99, 1.34, 25491.47)

#feed data to workspace by calling: param, cov, df = full_function(4, mean_Dry_AS, initial_gess)
def full_function(n, data, scan_nr, initial_guess= initial_guess, used_C="Cn"):
    X, dX, C = Sup.extract_from_dict(data, used_C)
    b = create_bounds(n)
    fit_nr = scan_nr - 1
    function_type = create_n_modal_lognormal_function(n)
    params, cov = optimize.curve_fit(function_type, X[fit_nr], C[fit_nr],
                            p0=initial_guess,
                            bounds=(b),
                            method="trf")  # trf -> bounds are provided
    sigma = np.sqrt(np.diag(cov))
    plt.plot(X[fit_nr], function_type(X[fit_nr], *params),
             color='red', lw=3, label='multimodal fit')
    for k in range(0,n):
        plt.plot(X[fit_nr], lognormal_function(X[fit_nr], *params[k*3:(k+1)*3]),
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
