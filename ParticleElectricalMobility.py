"""
ParticleElectricalMobility.py

calculation of the particle size of a particle with different charge, but same mobility as another particle
with that also calculation of Cunningham factor and electrical mobility of the initial particle

Created 2022-08
@written by Kevin Maier (kevin.r.maier@tum.de)
"""


import math
from matplotlib import pyplot as plt

# values for mean free path and viscosity taken from jennings 1988

dp = 160*10**(-9) # initial particle size in m
# l = 66*10**(-9) # mean free path in m, nicos value
l = 65.43*10**(-9)
# eta = 1.81*10**(-5) # dynamic viscosity of air in kg/ms, nico
eta = 1.8192*10**(-5)
el = 1.602*10**(-19) # elementary charge in C = J/V = kg*m^2/s^2*V
n1 = 1 # number of charges initial particle
n2 = 2 # number of charges new particle different size
# a = 2.514 # nico
# b = 0.8 # nico
# c = -0.55 # nico
a = 1.252
b = 0.399
c = -1.1

Ccini = 1+(2*l/dp)*(a+b*math.exp(c*(dp/(2*l)))) # cunningham factor of particle with dp
Z = (n1*el*Ccini)/(3*math.pi*eta*dp) # electrical mobility of particle wit dp and n in m^2/Vs
# Z = 1.03*10**(-7) # For set value of Z, just activate this
# when calculating centroid mobility in a DMA for set values, activate below

# for DMA calculation:
Vsheath = 10.5 # in L/min
Vexhaust = 10.5 # in L/min
Router = 1.961 # in cm # TSI 3081A: 1.961 # PALAS DEMC 2000: 3.35
Rinner = 0.937 # in cm # TSI 3081A: 0.937 # PALAS DEMC 2000: 2.5
Length = 0.44369 # in m # TSI 3081A: 0.44369 # PALAS DEMC 2000: 0.277
# Voltage = 5000 # in V
# Z = (((Vsheath+Vexhaust)/2)/60000)*(math.log(Router/Rinner)/(2*math.pi*Voltage*Length))
Voltage = (((Vsheath+Vexhaust)/2)/60000)*(math.log(Router/Rinner)/(2*math.pi*Z*Length)) # Mäkelä Vorlesung Summer School

ct_list = []
C_list = []
dp_list = []

tol = 1
ct = 0

while abs(tol) > 10**(-12): # iterative calculation of dp and Cc of the
    Cc = 1+(2*l/dp)*(a+b*math.exp(c*(dp/(2*l))))
    #Cc = 1 + (l / dp) * (a + b * math.exp(c * (dp / l))) # nico
    x = (n2*el*Cc)/(3*math.pi*eta*Z)
    tol = x-dp
    dp = x
    ct += 1
    # print(ct)
    ct_list.append(ct)
    C_list.append(Cc)
    dp_list.append(dp)

print(f'Ccini = {Ccini}')
print(f'Z = {Z}')
print(f'dp = {dp}')
print(f'Cc = {Cc}')
print(f'Voltage = {Voltage}')
fig, axs = plt.subplots(2)
axs[0].scatter(ct_list, [i*(10**9) for i in dp_list])
#axs[0].set_title("Particle Diameter over Iterations")
#axs[0].set_xlabel("Iterations")
axs[0].set_ylabel("Particle Diameter / nm")
axs[1].scatter(ct_list, C_list)
#axs[1].set_title("Cunningham Correction Factor over Iterations")
axs[1].set_xlabel("Iterations")
axs[1].set_ylabel("Cunningham Correction Factor")
plt.show()
