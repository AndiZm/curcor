import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl  
from scipy.optimize import curve_fit
from scipy.signal import butter, filtfilt, find_peaks
import scipy.stats as stats
from matplotlib.pyplot import cm
import ephem
import scipy.special as scp
import sys
from brokenaxes import brokenaxes
from matplotlib.gridspec import GridSpec

import utilities as uti
import corrections as cor
import geometry as geo
import scipy.special as scp


def SC_LD(x,amp,ang,lam,u):
    return amp * ( (1-u)/2 + u/3 )**(-2) * ( (1-u)/2 * scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam) + (u*(np.pi/2)**0.5) * scp.jn(1.5,np.pi*x*ang/lam) / ((np.pi*x*ang/lam)))**2

u = [1, 0.8, 0.6, 0.4, 0.2, 0]
ang = [3e-9, 4e-9, 5e-9, 6e-9]
lam = 422.5e-9
amp = 1
xplot = np.arange(0.1,300,0.1)

for j in range(len(ang)):
	limbfigure = plt.figure(figsize=(10,7))
	ax_limb = plt.subplot(111)
	ax_limb.set_title("Limb darkening spatial coherence ang={}".format(ang[j]))
	#ax_limb.set_xlabel("Baseline/Wavelength"); ax_limb.set_ylabel("Normalized coherence time") 
	ax_limb.axhline(0.0, color='black', linestyle='--')     
	
	
	for i in range(len(u)):
		ax_limb.plot(xplot, SC_LD(xplot,amp,ang[j], lam, u[i]), linewidth=2, label=u[i])


	plt.legend()


for j in range(len(ang)):
	limbfigure = plt.figure(figsize=(10,7))
	ax_limb = plt.subplot(111)
	ax_limb.set_title("Limb darkening spatial coherence")
	#ax_limb.set_xlabel("Baseline/Wavelength"); ax_limb.set_ylabel("Normalized coherence time") 
	ax_limb.axhline(0.0, color='black', linestyle='--')     
	
	
	for i in range(len(u)):
		ax_limb.plot(xplot, uti.SC_limb_darkening(xplot,amp,ang[j], lam, u[i]), linewidth=2, label=u[i])


	plt.legend()
plt.show()












