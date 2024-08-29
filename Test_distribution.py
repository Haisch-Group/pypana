"""
Test_distribution.py

"""

import numpy as np
import math
from Particle_analysis import lognormal_dist


def lognormal_test(x_lower, x_upper, x_steps, conc, dg, sigma_g):
    """log-normal function with A being a scale factor, m being the median and sigma being the geometric
        standard deviation"""
    X = np.logspace(x_lower, x_upper, x_steps, endpoint=True, base=10.0)
    C = (np.exp(-((np.log(X/dg))**2)/(2*np.log(sigma_g)**2))/(np.log(sigma_g)*X*np.sqrt(2*math.pi)))
    return X, C


if __name__ == "__main__":

    x_lower = 5
    x_upper = 1000
    x_steps = 99
    conc = 1E5
    dg = 80
    sigma_g = 1.16

    X, C = lognormal_test(x_lower, x_upper, x_steps, conc, dg, sigma_g)
