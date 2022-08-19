import numpy as np
from datetime import datetime, timezone
import ephem
from scipy.optimize import curve_fit
import scipy.special as scp

# Operating wavelength
lam = 465e-9

# GET_BASELINE function for cross analysis
def get_baseline(date, star):
	starname_big = star[0].upper() + star[1:]
	timestring = ephem.Date(date)
	# Split time string a la 2022/4/20 23:15:07
	year, month, day, hour, minute, second = timestring.tuple()
	# Decide which part of the night
	if hour > 12: # before midnight
		filename = "stardata/{}/{}_{}_{}.txt".format(starname_big, starname_big, day, day+1)
	elif hour <= 12: # after midnight
		filename = "stardata/{}/{}_{}_{}.txt".format(starname_big, starname_big, day-1, day)

	#print (filename)
	# Try open the file
	file = np.loadtxt(filename)
	hours     = file[:,3]
	minutes   = file[:,4]
	baselines = file[:,6]

	lineindex = 0
	while ( hours[lineindex] != hour or minutes[lineindex] != minute ):
		lineindex += 1
	baseline = baselines[lineindex]

	#print (baseline)
	return baseline


# Some utility functions for the final analysis
def gauss(x, a, x0, sigma, d):
    return a*np.exp(-(x-x0)**2/(2*sigma**2)) + d
def gauss_fixed(x, a, mu, sigma):
    return a*np.exp(-(x-mu)**2/(2*sigma**2)) + 1
def gauss_shifted(x, a, mu, sigma, shift, d=1):
    return a*np.exp(-(x-mu)**2/(2*sigma**2)) + d + 2e-6*shift

def fit(data, x, s, e, mu_start=-2):
    xfit = x[(x>s) & (x<e)]
    yfit = data[(x>s) & (x<e)]
    xplot = np.arange(s, e, 0.01)
    popt, cov = curve_fit(gauss, xfit, yfit, p0=[1e-6,mu_start,3,1])
    perr = np.sqrt(np.diag(cov))
    return xplot, popt, perr
def fit_fixed(data, x, s, e, mu,sigma, d=1):
    xfit = x[(x>s) & (x<e)]
    yfit = data[(x>s) & (x<e)]
    xplot = np.arange(s, e, 0.01)
    popt, cov = curve_fit(lambda x, a: gauss(x,a, mu,sigma,d), xfit, yfit, p0=[1e-6])
    perr = np.sqrt(np.diag(cov))
    return xplot, popt, perr

def integral(fitpar, fitpar_err):
    a = fitpar[0]; d_a = fitpar_err[0]
    s = np.abs(fitpar[2]); d_s = fitpar_err[2]
    Int = a*s*np.sqrt(2*np.pi)
    dInt = np.sqrt(2*np.pi)*np.sqrt((a*d_s)**2 + (s*d_a)**2)
    return Int, dInt
def integral_fixed(fitpar, fitpar_err, sigma):
    a = fitpar[0]; d_a = fitpar_err[0]
    s = np.abs(sigma); d_s = 0
    Int = a*s*np.sqrt(2*np.pi)
    dInt = np.sqrt(2*np.pi)*np.sqrt((a*d_s)**2 + (s*d_a)**2)
    return Int, dInt

def calc_array_mean(array, darray):
    mean = np.mean(array)
    squaresum = 0
    for i in range(0,len(darray)):
        squaresum += darray[i]**2
    dmean = 1/len(array) * np.sqrt(squaresum)
    return mean, dmean

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