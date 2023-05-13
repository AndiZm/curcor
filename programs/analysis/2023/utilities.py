import numpy as np
from datetime import datetime, timezone
import ephem
from scipy.optimize import curve_fit
import scipy.special as scp
import random

# Define colors of the different channels for usage in all the plottings
color_3A = "#8f0303"
color_3B = "#f7a488"
color_4A = "#003366" # ECAP Blue
color_4B = "#98cced"

# Define colors for the correlation channels for usage in all the plottings
color_CT3   = "#c35446"
color_CT4   = "#4c80aa"

color_chA   = "green"
color_chB   = "blue"
color_c3A4B = "#581894"
color_c4A3B = "#d980ff"


# Operating wavelength
#lam = 465e-9

# GET_BASELINE function for cross analysis
def get_baseline(date, star):
    starname_big = star[0].upper() + star[1:]
    timestring = ephem.Date(date)
    # Split time string a la 2022/4/20 23:15:07
    year, month, day, hour, minute, second = timestring.tuple()
    datestring1 = str(year) + str("{:02d}".format(month)) + str("{:02d}".format(day))
    datestring2 = str(year) + str("{:02d}".format(month)) + str("{:02d}".format(day-1))
    # Decide which part of the night
    if hour > 12: # before midnight
    	filename = "stardata/{}/{}_{}_baselines.txt".format(starname_big, starname_big, datestring1)
    elif hour <= 12: # after midnight
    	filename = "stardata/{}/{}_{}_baselines.txt".format(starname_big, starname_big, datestring2)
    #print (filename)
    # Try open the file
    file = np.loadtxt(filename)
    hours     = file[:,3]
    minutes   = file[:,4]
    baselines13 = file[:,6] # Baseline 13
    baselines14 = file[:,7] # Baseline 14
    baselines34 = file[:,8] # Baseline 34
    lineindex = 0
    while ( hours[lineindex] != hour or minutes[lineindex] != minute ):
        lineindex += 1
        #print ( str(hours[lineindex]) + " " + str(minutes[lineindex]) )
    baseline13 = baselines13[lineindex]
    baseline14 = baselines14[lineindex]
    baseline34 = baselines34[lineindex]
    #print (baseline)
    return baseline13, baseline14, baseline34


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
    #popt, cov = curve_fit(lambda x, a, d: gauss(x,a, mu,sigma,d), xfit, yfit, p0=[1e-6,1.])
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
    # Use the formula from Master thesis
    #dInt = 2 * rms * np.sqrt(1.6e-9 * sigma)
    return Int, dInt

def calc_array_mean(array, darray):
    mean = np.mean(array)
    squaresum = 0
    for i in range(0,len(darray)):
        squaresum += darray[i]**2
    dmean = 1/len(array) * np.sqrt(squaresum)
    return mean, dmean

####################################
# Spatial coherence plot functions #
####################################
# Fitting the spatial coherence values
def spatial_coherence(x, amp, ang, lam=470e-9):
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
def spatial_coherenceUV(x, amp, ang, lam=375e-9):
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
# Calculate error band numerically
def get_error_numerical(x, amp, damp, ang, dang):
    sc_vals = []
    # simulate random (gaussian distributed) realizations of amp and ang
    for i in range (0,100):
        amp_real = random.gauss(amp, damp)
        ang_real = random.gauss(ang, dang)
        # calculate corresponding spatial coherence values
        sc_vals.append( spatial_coherence(x=x, amp=amp_real, ang=ang_real) )
    return np.std(sc_vals)

# Try including x error bars with orthogonal distance regression
def spatial_coherence_odr(p, x):
    lam=470e-9
    amp, ang = p
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
def spatial_coherence_odrUV(p, x):
    lam=375e-9
    amp, ang = p
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
def bessel(phi, baseline, lam=470e-9):
    return scp.j1(np.pi*baseline*phi/lam)
def besselUV(phi, baseline, lam=375e-9):
    return scp.j1(np.pi*baseline*phi/lam)
def numerical_deviation(phi, baseline):
    step = 1e-10
    y1 = bessel(phi, baseline)
    y2 = bessel(phi+step, baseline)
    slope = (y2-y1) / (step)
    return slope
def delta_spatial_coherence(x, A,dA, phi,dphi, lam=470e-9):
    sum1 = dA * 4 * scp.j1(np.pi*x*phi/lam)**2*lam**2 / (np.pi*x*phi)**2
    sum2 = dphi * A * 4 * lam**2 / (np.pi*x)**2 * ( -2*scp.j1(np.pi*x*phi/lam)**2/phi**3 + 2*scp.j1(np.pi*x*phi/lam)/phi**2 * numerical_deviation(phi,baseline=x) )
    return np.sqrt( sum1**2 + sum2**2 )
def delta_spatial_coherenceUV(x, A,dA, phi,dphi, lam=375e-9):
    sum1 = dA * 4 * scp.j1(np.pi*x*phi/lam)**2*lam**2 / (np.pi*x*phi)**2
    sum2 = dphi * A * 4 * lam**2 / (np.pi*x)**2 * ( -2*scp.j1(np.pi*x*phi/lam)**2/phi**3 + 2*scp.j1(np.pi*x*phi/lam)/phi**2 * numerical_deviation(phi,baseline=x) )
    return np.sqrt( sum1**2 + sum2**2 )

def rad2mas(x):
    return 180*3600*1000/np.pi * x

# Function for averaging over the 4 cross correlation datapoints
def weighted_avg(cA, dcA, cB, dcB, c3Ax4B, dc3Ax4B, c4ax3B, dc4Ax3B):
    means  = []
    dmeans = []
    for i in range (0,len(cA)):
        inverse_error_sum = 1/dcA[i]**2 + 1/dcB[i]**2 + 1/dc3Ax4B[i]**2 + 1/dc4Ax3B[i]**2
        mean = 1/(inverse_error_sum) * ( cA[i]/dcA[i]**2 + cB[i]/dcB[i]**2 + c3Ax4B[i]/dc3Ax4B[i]**2 + c4ax3B[i]/dc4Ax3B[i]**2 )
        means.append(mean)

        dmean = np.sqrt( 1/inverse_error_sum )
        dmeans.append(dmean)
    return means, dmeans

def fourier(data):
    fft  = np.abs(np.fft.fft(data-1))
    xfft = np.linspace(0,1/1.6,len(data),endpoint=True)
    return xfft, fft