import numpy as np
import math
import matplotlib.pyplot as plt
import scipy.special as sp

R_s = 6.96342e8 # Solar radius
Ly  = 9.46e15 	# Light year

#Alle angaben in m
wellenlaenge = 465e-9
entfernung = 7500 * Ly
radius = 240 * R_s
baseline = 120.

# Angular diameter
phi_arc = 2 * radius / entfernung
phi_deg = phi_arc * 180 / np.pi
phi_milliarcseconds = phi_deg * 3600 * 1000
print ("Angular Diameter: {:.2f} mas".format(phi_milliarcseconds))

def g2(delta_r):
	zaehler = np.pi*2.*radius*delta_r
	nenner = (wellenlaenge*entfernung)
	argument = zaehler/nenner
	g2_value = ( 2* sp.j1(argument) / argument)**2
	return g2_value

plt.figure()
xplot = np.linspace(0.0001,1.*baseline,10000)
plt.plot(xplot, g2(xplot)+1., c="red")
plt.ylabel("$g^{(2)}$")
plt.show()
