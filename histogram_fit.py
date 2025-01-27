import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import skewnorm
from sympy import symbols, Function


#data generation
#np.random.seed(123)
#data=np.concatenate((np.random.normal(1, .2, 5000), np.random.normal(1.6, .3, 2500)))
#y,x,_=plt.hist(data, 100, alpha=.3, label='data')
#x=(x[1:]+x[:-1])/2 # for len(x)==len(y)

#x, y inputs can be lists or 1D numpy arrays

def gauss(x, mu, sigma, A):
    return A*np.exp(-(x-mu)**2/2/sigma**2)

def lognormal_function(x, mu, sigma, A):
    return A*(np.exp(-((np.log(x/mu))**2)/(2*np.log(sigma)**2))/(np.log(sigma)*x*np.sqrt(2*math.pi)))

def erlang(x, lambda_param, k, A):
    return A*(lambda_param**k * x**(k-1) * np.exp(-lambda_param * x)) / np.math.factorial(k-1)

#def lognormal_skew(x, shape, loc, scale, skew):
    #return skewnorm.pdf(x, skew, loc=loc, scale=scale) * np.exp(-((np.log(x) - shape) ** 2) / (2 * scale ** 2))

def bimodal_gauss(x, mu1, sigma1, A1, mu2, sigma2, A2):
    return gauss(x,mu1,sigma1,A1)+gauss(x,mu2,sigma2,A2)

def bimodal_lognormal(x, mu1, sigma1, A1, mu2, sigma2, A2):
    return lognormal_function(x,mu1,sigma1,A1)+lognormal_function(x,mu2,sigma2,A2)

def trimodal_lognormal(x, mu1, sigma1, A1, mu2, sigma2, A2, mu3, sigma3, A3):
    return lognormal_function(x,mu1,sigma1,A1)+lognormal_function(x,mu2,sigma2,A2)+lognormal_function(x,mu3,sigma3,A3)

def n_modal_lognormal(modalität):
    #variable_list = create_distribution_parameter(modalität)
    x = symbols('x')
    total_sum = 0
    for i in range(1, modalität + 1):
        mu = symbols(f'mu{i}')
        sigma = symbols(f'sigma{i}')
        A = symbols(f'A{i}')
        lognormal_func = Function(f'lognormal_function')(x, mu, sigma, A)
        total_sum += lognormal_func
    return total_sum

def bimodal_erlang(x, lambda_param1, k1, A1, lambda_param2, k2, A2):
    return erlang(x, lambda_param1, k1, A1) + erlang(x, lambda_param2, k2, A2)

modalität = 3

def create_distribution_parameter(modalität):
    variable_list = ['x']
    for i in range(1, modalität+1):
        variable_list.append(f'mu{i}')
        variable_list.append(f'sigma{i}')
        variable_list.append(f'A{i}')
    return variable_list

def create_variable_list(modalität):
    variable_list = []
    for i in range(1, modalität+1):
        variable_list.append(f'mu{i}')
        variable_list.append(f'sigma{i}')
        variable_list.append(f'A{i}')
    return variable_list

def create_bounds(modalität):
	bounds_1 = []
	bounds_2 = []
	bounds=(bounds_1,bounds_2)
	for i in range(1, (modalität*3)+1):
		bounds_1.append(0.1)
	for k in range(1, modalität+1):
		bounds_2.append(850)
		bounds_2.append(np.inf)
		bounds_2.append(np.inf)
	return bounds

#set of running parameters
initial_gess = (20, 1.6, 100 ,40, 1.6, 100, 180, 1.6, 40)

def full_function(modalität, data, initial_gess= initial_gess):
    b = create_bounds(modalität)
    function_type = n_modal_lognormal(modalität)
    params, cov = curve_fit(function_type, data["mean_X"][0], data["mean_C"][0],
                            p0=initial_gess,
                            bounds=(b),
                            method="trf")
    plt.plot(data["mean_X"][0], function_type(data["mean_X"][0], *params),
             color='red', lw=3, label='model')
    for k in range(0,n):
        plt.plot(data["mean_X"][0], lognormal_function(data["mean_X"][0], *params[k*3:(k+1)*3]),
             color='red', lw=1, ls=":", label=f"distribution {k+1}")
    plt.xscale("log")
    return params, cov

# normal Distibution with inceased skewness (does not work at the moment)
#def bimodal_skew(x, shape, loc, scale, skew, mu1, sigma1, A1):
    #return lognormal_skew(x, shape, loc, scale, skew,)+lognormal_function(x, mu1,sigma1,A1)

#expected = (22, 2, 2700, 180, 4, 700)
#params, cov = curve_fit(bimodal_lognormal, mean_Dry_05["mean_X"][0], mean_Dry_05["mean_C"][0], p0=expected, bounds=([0,0,1,0,0,1],[850,1000000,100000000,850,10000000,10000000])) # replace X and C bei the specific variable names
#sigma=np.sqrt(np.diag(cov))
#x_fit = np.linspace(x.min(), x.max(), 500)
#plot combined...
#plt.plot(mean_Dry_05["mean_X"][0], bimodal_lognormal(mean_Dry_05["mean_X"][0], *params), color='red', lw=3, label='model')
#...and individual Gauss curves
#plt.plot(mean_Dry_05["mean_X"][0], lognormal_function(mean_Dry_05["mean_X"][0], *params[:3]), color='red', lw=1, ls="--", label='distribution 1')
#plt.plot(mean_Dry_05["mean_X"][0], lognormal_function(mean_Dry_05["mean_X"][0], *params[3:]), color='red', lw=1, ls=":", label='distribution 2')
#and the original data points if no histogram has been created before
#plt.scatter(x, y, marker="X", color="black", label="original data")
#plt.legend()
#print(pd.DataFrame(data={'params': params, 'sigma': sigma}, index=bimodal.__code__.co_varnames[1:]))
#plt.show()


#def find_high_points(data["Array"]):
 #   high_points = []
  #  for i in range(1, len(data) - 1):
   #     if data[i] > data[i - 1] and data[i] > data[i + 1]:
    #    high_points.append((i, data[i]))
    #return high_points

# Find high points
#high_points = find_high_points(data[Array])

#print("Indices and values of high points:", high_points)