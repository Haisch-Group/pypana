"""
ParticleMechanics.py

calculation of terminal settling velocity, Re(settling), relaxation time, Stopping distance, root mean square
displacement along axis, Diffusion coefficient and Cunningham correction factor of a particle with given diameter

Created 2022-08
@written by Kevin Maier (kevin.r.maier@tum.de) for the Aerosol Summer School in Vienna 2022
"""


import math
import pandas as pd

"""particle properties and experimental parameters"""
dp_um = [0.01, 0.065, 0.1, 0.5, 1, 5, 10, 100, 200] # particle diameter in micrometer
dp_m = [i*10**(-6) for i in dp_um]  # particle diameter in meter
ro_p = 1000     # particle density in kg/m^3
v0 = 10     # initial velocity of the particle in m/s
t = 1   # observation time in s

"""physical constants"""

k = 1.38*10**(-23)  # rounded Boltzmann constant in (kg*m^2)/(s^2*K)
g = 9.81    # gravitational acceleration in m/s^2

"""gas properties"""
# standard conditions (s.c.) = 101 kPa, 293 K
T = 293 # temperature in Kelvin (s.c.)
lam = 66*10**(-9)   # lambda = mean free path in air at ss.c. in m
eta = 1.81*10**(-5) # dynamic viscosity of air at s.c. in kg/(m*s)
ro_g = 1.204  # density of air at s.c. in kg/m^3

"""functions"""


def calc_Cc(dp_m, lam):
    """calculates Cunningham correction factor - dimensionless"""
    a = 2.34    # empirical constants for cunningham factor
    b = 1.05
    c = -0.39
    Cc = 1+(lam/dp_m)*(a+b*math.exp(c*(dp_m/lam)))
    return Cc


def calc_vts(dp_m, ro_p, g, Cc, eta):
    """calculates terminal settling velocity in m/s"""
    vts = ((ro_p*dp_m**2*g*Cc) / (18*eta))
    vts_mm = vts*10**3 # conversion to mm/s
    return vts, vts_mm


def calc_Res(dp_m, ro_g, vts, eta):
    """calculates Reynolds with settling velocity - dimensionless"""
    Res = (ro_g*vts*dp_m)/eta
    return Res


def calc_tau(dp_m, ro_p, Cc, eta):
    """calculates the relaxation time in s"""
    tau = (ro_p*dp_m**2*Cc) / (18*eta)
    return tau


def calc_S(v0, tau):
    """calculates the stopping distance of the particle in m"""
    S = v0 * tau
    S_mm = S*10**3  # conversion to mm
    return S, S_mm


def calc_D(dp_m, k, T, Cc, eta):
    """calculates the diffusion constant of the particle at given conditions in m^2/s"""
    D = (k*T*Cc)/(3*math.pi*eta*dp_m)
    return D


def calc_xrms(D, t):
    """calculates the brownian displacement in m"""
    xrms = math.sqrt(2*D*t)
    xrms_mm = xrms *10**3   # conversion to mm
    return xrms, xrms_mm


if __name__ == "__main__":

    table = pd.DataFrame(columns=['d[um]', 'vts[mm/s]', 'Re(settling)', 'tau[s]', 'S[mm]', 'xrms[mm]', 'D[m^2/s]', 'Cc'])
    pd.set_option('display.float_format', '{:.2E}'.format)
    for i in range(len(dp_m)):
        Cc = calc_Cc(dp_m[i], lam)
        vts, vts_mm = calc_vts(dp_m[i], ro_p, g, Cc, eta)
        Res = calc_Res(dp_m[i], ro_g, vts, eta)
        tau = calc_tau(dp_m[i], ro_p, Cc, eta)
        S, S_mm = calc_S(v0, tau)
        D = calc_D(dp_m[i], k, T, Cc, eta)
        xrms, xrms_mm = calc_xrms(D, t)
        table = table.append({'d[um]':dp_um[i], 'vts[mm/s]':vts_mm, 'Re(settling)':Res, 'tau[s]':tau, 'S[mm]':S_mm,
                      'xrms[mm]':xrms_mm, 'D[m^2/s]':D, 'Cc':Cc}, ignore_index=True)
    print(table)
    #table.to_clipboard(excel=True, sep='\t')