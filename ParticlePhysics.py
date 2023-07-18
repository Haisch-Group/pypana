"""
calculation of terminal settling velocity, Re(settling), relaxation time, Stopping distance, root mean square
displacement along axis, Diffusion coefficient and Cunningham correction factor of a particle with given diameter

Created 2023-04-13 from ParticleMechanics.py and ParticleElectricalMobility.py
@written by Kevin Maier (kevin.r.maier@tum.de)
"""


import math
import pandas as pd

"""experimental parameters"""
d_tube_mm = 3 # diameter of a tube or nozzle
d_tube_m = d_tube_mm/10**3
flow_lpm = 0.3  # flow rate in liter per minute in a tube or nozzle
flow_cmps = flow_lpm/(10**3*60) # flow rate in cubic meters per second
v0 = flow_cmps/((0.5*d_tube_m)**2*math.pi)# initial velocity of a particle in m/s
# v0 = 10     # initial velocity of a particle in m/s
t = 1   # observation time in s
v_el = -3000 # electrical potential between two electrodes
d_el_mm = 1 # distance of two opposing electrodes in mm
d_el_m = d_el_mm*10**(-3)   # distance of two opposing electrodes in m
E = -v_el/d_el_m    # electrical field strength

"""particle properties"""
dp_nm = [10, 30, 50, 100, 350, 500, 800, 1000] # particle diameter in nanometer
dp_m = [i*10**(-9) for i in dp_nm]  # particle diameter in meter
ro_p = 1000     # particle density in kg/m^3
n_el = 1    # number of charges

"""physical constants"""
k = 1.38*10**(-23)  # rounded Boltzmann constant in (kg*m^2)/(s^2*K)
g = 9.81    # gravitational acceleration in m/s^2
el = 1.602*10**(-19) # elementary charge in C = J/V = (kg*m^2)/(s^2*V)

"""gas properties"""
# standard conditions (s.c.) = 101 kPa, 293 K
T = 293 # temperature in Kelvin (s.c.)
lam = 66*10**(-9)   # lambda = mean free path in air at s.c. in m
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


def calc_B(dp_m, Cc, eta):
    """calculated the mechanical mobility in m^2/s"""
    B = Cc/(3*math.pi*eta*dp_m)
    return B


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


def calc_vte(dp_m, n_el, el, E, Cc, eta):
    """calculates terminal velocity in electric field in m/s"""
    vte = ((n_el*el*E*Cc)/(3*math.pi*eta*dp_m))
    vte_mm = vts*10**3 # conversion to mm/s
    return vte, vte_mm


def calc_Z(dp_m, n_el, el, Cc, eta):
    """calculates the electrical mobility in in m^2/Vs"""
    Z = (n_el*el*Cc)/(3*math.pi*eta*dp_m)
    return Z


if __name__ == "__main__":

    table = pd.DataFrame(columns=['d[nm]', 'vts[mm/s]', 'B[m^2/s]', 'Re(settling)', 'tau[s]', 'S[mm]', 'xrms[mm]',
                                  'D[m^2/s]', 'vte[mm/s]', 'Z[m^2/Vs]', 'Cc'])
    pd.set_option('display.float_format', '{:.2E}'.format)
    for i in range(len(dp_m)):
        Cc = calc_Cc(dp_m[i], lam)
        vts, vts_mm = calc_vts(dp_m[i], ro_p, g, Cc, eta)
        B = calc_B(dp_m[i], Cc, eta)
        Res = calc_Res(dp_m[i], ro_g, vts, eta)
        tau = calc_tau(dp_m[i], ro_p, Cc, eta)
        S, S_mm = calc_S(v0, tau)
        D = calc_D(dp_m[i], k, T, Cc, eta)
        xrms, xrms_mm = calc_xrms(D, t)
        vte, vte_mm = calc_vte(dp_m[i], n_el, el, E, Cc, eta)
        Z = calc_Z(dp_m[i], n_el, el, Cc, eta)
        table = table.append({'d[nm]':dp_nm[i], 'vts[mm/s]':vts_mm, 'B[m^2/s]':B, 'Re(settling)':Res, 'tau[s]':tau,
                              'S[mm]':S_mm, 'xrms[mm]':xrms_mm, 'D[m^2/s]':D, 'vte[mm/s]':vte_mm, 'Z[m^2/Vs]':Z,
                              'Cc':Cc}, ignore_index=True)
    print(f'v0[mm/s]={v0*10**(3)}')
    print(table)
    #table.to_clipboard(excel=True, sep='\t')