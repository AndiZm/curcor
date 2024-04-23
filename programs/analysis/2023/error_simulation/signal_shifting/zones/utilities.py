import numpy as np
from datetime import datetime, timezone
import ephem
from scipy.optimize import curve_fit
import scipy.special as scp
import scipy.stats as stats
import random
import matplotlib.pyplot as plt
import scipy

# Some utility functions for the final analysis
def gauss(x, a, x0, sigma, d):
    return a*np.exp(-(x-x0)**2/(2*sigma**2)) + d
def gauss_fixed(x, a, mu, sigma):
    return a*np.exp(-(x-mu)**2/(2*sigma**2)) + 1
def gauss_shifted(x, a, mu, sigma, shift, d=1, inverse=False, ntotal=1):
    if inverse == False:
        return a*np.exp(-(x-mu)**2/(2*sigma**2)) + d + 1e-6*shift
    else:
        return a*np.exp(-(x-mu)**2/(2*sigma**2)) + d + 1e-6*(ntotal-shift-1)

def fit(data, x, s, e, mu_start=-2): # used in parameter fixing
    xfit = x[(x>s) & (x<e)]
    yfit = data[(x>s) & (x<e)]
    xplot = np.arange(s, e, 0.01)
    popt, cov = curve_fit(gauss, xfit, yfit, p0=[1e-6,mu_start,3,1])
    perr = np.sqrt(np.diag(cov))
    return xplot, popt, perr
def fit_fixed(data, x, s, e, sigma, mu_start=-2): # fixes sigma, offset d free
    xfit = x[(x>s) & (x<e)]
    yfit = data[(x>s) & (x<e)]
    xplot = np.arange(s, e, 0.01)
    popt, cov = curve_fit(lambda x, a, mu, d: gauss(x,a, mu,sigma,d), xfit, yfit, p0=[1e-6,mu_start,1.])
    perr = np.sqrt(np.diag(cov))
    #chi = chi_squared(yfit, gauss(xfit, popt[0], popt[1], sigma, d), error, N, par)
    return xplot, popt, perr
def fit_fixed_offset(data,x,s,e,mu,sigma, d=1): # fixes mu and sigma and offset d
    xfit = x[(x>s) & (x<e)]
    yfit = data[(x>s) & (x<e)]
    N = len(yfit)
    xplot = np.arange(s, e, 0.01)
    #mu_start = -1
    popt, cov = curve_fit(lambda x, a: gauss(x,a, mu,sigma,d), xfit, yfit, p0=[1e-6])
    perr = np.sqrt(np.diag(cov))
    #chi = chi_squared(yfit, gauss(xfit, popt[0], popt[1], sigma, d), error, N, par)
    return xplot, popt, perr #, chi

def integral(fitpar, fitpar_err):
    a = fitpar[0]; d_a = fitpar_err[0]
    s = np.abs(fitpar[2]); d_s = fitpar_err[2]
    Int = a*s*np.sqrt(2*np.pi)
    dInt = np.sqrt(2*np.pi)*np.sqrt((a*d_s)**2 + (s*d_a)**2)
    return Int, dInt
def integral_fixed(fitpar, fitpar_err, sigma, factor=1):
    a = fitpar[0]; d_a = fitpar_err[0]
    s = np.abs(sigma); d_s = 0
    Int = a*s*np.sqrt(2*np.pi)
    dInt = factor * np.sqrt(2*np.pi)*np.sqrt((a*d_s)**2 + (s*d_a)**2)
    # Use the formula from Master thesis
    #dInt = 2 * rms * np.sqrt(1.6e-9 * sigma)
    return Int, dInt