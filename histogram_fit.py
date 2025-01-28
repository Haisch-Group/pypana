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
    exec(func_def, globals())
    return n_modal_lognormal

def create_bounds(modalität):
	bounds_1 = []
	bounds_2 = []
	bounds=(bounds_1,bounds_2)
	for i in range(1, modalität+1):
		bounds_1.append(0.1)
		bounds_1.append(0.1)
		bounds_1.append(0.1)
	for k in range(1, modalität+1):
		bounds_2.append(850)
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
def full_function(n, data, initial_gess= initial_gess):
    b = create_bounds(n)
    function_type = create_n_modal_lognormal_function(n)
    params, cov = curve_fit(function_type, data["mean_X"][0], data["mean_C"][0],
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