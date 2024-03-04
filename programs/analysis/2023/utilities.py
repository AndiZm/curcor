import numpy as np
from datetime import datetime, timezone
import ephem
from scipy.optimize import curve_fit
import scipy.special as scp
import scipy.stats as stats
import random
import matplotlib.pyplot as plt
import scipy

# Define colors of the different channels for usage in all the plottings
color_3A = "#8f0303"
color_3B = "#f7a488"
color_4A = "#003366" # ECAP Blue
color_4B = "#98cced"

# Define colors for the correlation channels for usage in all the plottings
color_CT3   = "#c35446"
color_CT4   = "#4c80aa"

color_chA   = "deepskyblue"
color_chB   = "darkviolet"
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

# GET_BASELINE function for cross analysis
def get_baseline3T(date, star, telcombi):
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
    if telcombi == "13":
        baseline = file[:,6]
    if telcombi == "14":
        baseline = file[:,7]
    if telcombi == "34":
        baseline = file[:,8]
    lineindex = 0
    while ( hours[lineindex] != hour or minutes[lineindex] != minute ):
        lineindex += 1
    baseline = baseline[lineindex]
    #print ("Baseline from Buechele: {}".format(baseline))
    return baseline


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
def fit_fixed1(data,x,s,e,sigma,mu_start, error, par, d=1):
    xfit = x[(x>s) & (x<e)]
    yfit = data[(x>s) & (x<e)]
    N = len(yfit)
    xplot = np.arange(s, e, 0.01)
    popt, cov = curve_fit(lambda x, a, mu: gauss(x,a, mu,sigma,d), xfit, yfit, p0=[1e-6,mu_start])
    perr = np.sqrt(np.diag(cov))
    chi = chi_squared(yfit, gauss(xfit, popt[0], popt[1], sigma, d), error, N, par)
    return xplot, popt, perr, chi

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

def calc_array_mean(array, darray):
    mean = np.mean(array)
    squaresum = 0
    for i in range(0,len(darray)):
        squaresum += darray[i]**2
    dmean = 1/len(array) * np.sqrt(squaresum)
    return mean, dmean


def chi_squared(y, fy, error, N, par):
    chi = np.sum( (y-fy)**2 / (error)**2 )
    ndf = N - par
    chi_red = chi / ndf 
    return chi_red

####################################
# Spatial coherence plot functions #
####################################
# Fitting the spatial coherence values
def spatial_coherence(x, amp, ang, lam):
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
def spatial_coherenceG(x, amp, ang, lam=470e-9):
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
def spatial_coherenceUV(x, amp, ang, lam=375e-9):
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
def spatial_coherence_LD(x,amp,ang,lam,u):
    return amp * ( (1-u)/2 + u/3 )**(-2) * ( (1-u) * scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam) + (u*(np.pi/2)**0.5) * bessel32(ang, x, lam) / ((np.pi*x*ang/lam)**(3/2)))**2

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
    lam=422.5e-9
    amp, ang = p
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
def spatial_coherence_odr_scaled(ang, x):
    lam=422.5e-9
    amp = 1
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
def spatial_coherence_odrG(p, x):
    lam=470e-9
    amp, ang = p
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
def spatial_coherence_odrUV(p, x):
    lam=375e-9
    amp, ang = p
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2

def spatial_coherence_odrG_LD(p,x):
    lam=470e-9
    u = 0.37 # Mimosa
    amp, ang = p
    return amp * ( (1-u)/2 + u/3 )**(-2) * ( (1-u) * scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam) + (u*(np.pi/2)**0.5) * bessel32(ang, x, lam) / ((np.pi*x*ang/lam)**(3/2)))**2

def bessel32(phi, baseline, lam):
    x = np.pi * baseline * phi/lam
    return np.sqrt(2/(np.pi*x**3)) * (np.sin(x) - x*np.cos(x))
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

def mas2rad(x):
    return np.pi/(180*3600*1000) * x

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


# Function for extrapolating the limb darkening coefficient
def get_u(temp_star, logg_star):
    # read in table with LD coefficients
    table = np.loadtxt("tableu.txt", delimiter=' ', dtype={'names': ('logg', 'temp', 'Z', 'xi', 'u', 'Filt', 'Met'), 'formats': (np.float, np.float, np.float, np.float, np.float, '|S15', '|S15')}, usecols=(1,2,3,4,5,6,7))
    # shorten table to interesting values (z=0, xi=2, filter=B, method=L)
    tables = []
    for i in range(len(table)):
        if table[i][2] == 0.0 and table[i][3] == 2.0 and table[i][5] == b'B' and table[i][6] == b'L':
            tables.append(table[i])

    logg = []; temp = []; u = []
    logg1 = []; u1 = []; logg2 = []; u2 = []
    for i in range(len(tables)):
        if tables[i][1] == temp_star:  # if star temp exists in table
            logg.append(tables[i][0])
            u.append(tables[i][4])
        elif tables[i][1] != temp_star: # if star temp does not exist in table
            # round to 10.000 number
            temp1 = round(temp_star, -3)
            # get higher or lower 10.000 number
            if temp_star <= temp1:
                temp2 = temp1 - 1000
            elif temp_star >= temp1:
                temp2 = temp1 + 1000
            # get logg and u for those temps    
            if tables[i][1] == temp1: 
                logg1.append(tables[i][0])
                u1.append(tables[i][4])
            if tables[i][1] == temp2:
                logg2.append(tables[i][0])
                u2.append(tables[i][4])

    xnew = np.arange(0.0, 5.0, 0.01)
    plt.figure('LD coefficient')
    plt.title('Limb darkening coefficient'); plt.xlabel('logg'); plt.ylabel('u')
    if len(logg) > 0:
        plt.plot(logg, u, marker='o',linestyle='', color='green', label=str(temp_star))
        f = scipy.interpolate.interp1d(logg, u,'cubic', bounds_error=False, fill_value='extrapolate')
        ynew = f(xnew)
        plt.plot(xnew, ynew, color='green')
        x_want = round(float(f(logg_star)),2)
        
    elif len(logg) == 0:
        plt.plot(logg1, u1, marker='o',linestyle='', color='green', label=str(temp1))
        plt.plot(logg2, u2, marker='x',linestyle='', color='blue', label=str(temp2))
        f1 = scipy.interpolate.interp1d(logg1, u1,'cubic', bounds_error=False, fill_value='extrapolate')
        f2 = scipy.interpolate.interp1d(logg2, u2,'cubic', bounds_error=False, fill_value='extrapolate')
        y1new = f1(xnew)
        y2new = f2(xnew)
        plt.plot(xnew, y1new, color='green')
        plt.plot(xnew, y2new, color='blue')
        x1_want = f1(logg_star)
        x2_want = f2(logg_star)
        print(round(float(x1_want),2))
        print(round(float(x2_want),2))
        x_want = round(float(np.mean([x1_want, x2_want])),2)
    plt.legend()    
    return(x_want)

    