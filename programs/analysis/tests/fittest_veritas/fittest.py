### Information ###
# This program takes the VERITAS star data of beta CMa and epsilon Ori, which were extracted using the web plot digitizer
# The goal is to cross-check our spatial coherence function, in particular if the calculation of the angular diameter
# Error bars from the VERITAS data were not considered, which may lead to slight deviations 

import numpy as np
from scipy.optimize import curve_fit
import scipy.special as scp
import matplotlib.pyplot as plt

# Operating wavelength
lam = 465e-9

def spatial_coherence(x, amp, ang):
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
def bessel(phi, baseline):
    return scp.j1(np.pi*baseline*phi/lam)
def numerical_deviation(phi, baseline):
    step = 1e-10
    y1 = bessel(phi, baseline)
    y2 = bessel(phi+step, baseline)
    slope = (y2-y1) / (step)
    return slope
def delta_spatial_coherence(x, A,dA, phi,dphi):
    sum1 = dA * 4 * scp.j1(np.pi*x*phi/lam)**2*lam**2 / (np.pi*x*phi)**2
    sum2 = dphi * A * 4 * lam**2 / (np.pi*x)**2 * ( -2*scp.j1(np.pi*x*phi/lam)**2/phi**3 + 2*scp.j1(np.pi*x*phi/lam)/phi**2 * numerical_deviation(phi,baseline=x) )
    return np.sqrt( sum1**2 + sum2**2 )

def rad2mas(x):
    return 180*3600*1000/np.pi * x

plt.figure(figsize=(10,5))
# read in data
baseline = np.loadtxt("data_bcma.txt")[:,0]
g2       = np.loadtxt("data_bcma.txt")[:,1]

# calculate SC fit and errorbars
popt, pcov = curve_fit(spatial_coherence, baseline, g2, p0=[1.3, 2.2e-9])
perr = np.sqrt(np.diag(pcov))
xplot = np.arange(0.1,185,0.1)

plt.subplot(121); plt.title("$beta$ CMa (VERITAS: 0.523 +/- 0.017 mas)")
plt.plot(baseline, g2, "o")
plt.plot(xplot, spatial_coherence(xplot, *popt), color="grey", label="{:.3f} +/- {:.3f} (mas)".format( rad2mas(popt[1]),rad2mas(perr[1]) ))

plt.xlim(0,185)
plt.ylim(0,1.4)
plt.legend()


# read in data
baseline = np.loadtxt("data_eori.txt")[:,0]
g2       = np.loadtxt("data_eori.txt")[:,1]

# calculate SC fit and errorbars
popt, pcov = curve_fit(spatial_coherence, baseline, g2, p0=[1.3, 2.2e-9])
perr = np.sqrt(np.diag(pcov))
xplot = np.arange(0.1,185,0.1)

plt.subplot(122); plt.title("$\epsilon$ Ori (VERITAS: 0.631 +/- 0.017 mas)")
plt.plot(baseline, g2, "o")
plt.plot(xplot, spatial_coherence(xplot, *popt), color="grey", label="{:.3f} +/- {:.3f} (mas)".format( rad2mas(popt[1]),rad2mas(perr[1]) ))

plt.xlim(0,185)
plt.ylim(0,1.4)
plt.legend()

plt.show()