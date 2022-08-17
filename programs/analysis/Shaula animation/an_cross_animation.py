import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl  
from scipy.optimize import curve_fit
from scipy.signal import butter, filtfilt, find_peaks
from matplotlib.pyplot import cm 

x = np.arange(0,len(np.loadtxt("g2cross_20220421_HESS_Shaula_use_17_35_8.6--37_7_9.9.txt")[:,1]),1)

def gauss(x, a, x0, sigma, d):
    return a*np.exp(-(x-x0)**2/(2*sigma**2)) + d

def fit(data, s, e, m):
    xfit = x[(x>s) & (x<e)]
    yfit = data[(x>s) & (x<e)]
    xplot = np.arange(s, e, 0.01)
    popt, cov = curve_fit(gauss, xfit, yfit, p0=[1e-6,m,3,1])
    perr = np.sqrt(np.diag(cov))
    return xplot, popt, perr

def integral(fitpar, fitpar_err):
    a = fitpar[0]; d_a = fitpar_err[0]
    s = np.abs(fitpar[2]*1e-9); d_s = fitpar_err[2]*1e-9
    Int = a*s*np.sqrt(2*np.pi)
    dInt = np.sqrt(2*np.pi)*np.sqrt((a*d_s)**2 + (s*d_a)**2)
    return Int, dInt

# Scan into one direction
plt.figure(figsize=(9,6))
plt.axvline(x=5000, color="grey", linestyle="--")
plt.xlim(4700,5300); plt.ylim(0.9999995, 1.0000014)
plt.ylabel("$g^{(2)}$")
plt.ticklabel_format(useOffset=False)
plt.tight_layout()



js = np.arange(10, 47, 1)

data = np.loadtxt("g2cross_20220421_HESS_Shaula_use_17_35_8.6-{}_7_9.9.txt".format(-1*js[0]))[:,1]
correlation, = plt.plot(data, color="red")
for j in js:
    plt.title("Dec = {}".format(j))
    dec = -1*j
    data = np.loadtxt("g2cross_20220421_HESS_Shaula_use_17_35_8.6-{}_7_9.9.txt".format(dec))[:,1]

    #correlation, = plt.plot(data, label="{} deg off".format(j), color="red")
    correlation.set_ydata(data)
    plt.pause(0.3)
plt.show()