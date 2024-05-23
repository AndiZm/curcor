import numpy as np
from scipy.optimize import curve_fit
import scipy.special as scp
import matplotlib.pyplot as plt
import scipy

# Define colors for the correlation channels for usage in all the plottings
color_chA   = "deepskyblue"
color_chB   = "blueviolet"

# Operating wavelength
#lam = 465e-9

# Some utility functions for the final analysis
def gauss(x, a, x0, sigma, d):
    return a*np.exp(-(x-x0)**2/(2*sigma**2)) + d

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
def integral_fixed(fitpar, fitpar_err, sigma):
    a = fitpar[0]; d_a = fitpar_err[0]
    s = np.abs(sigma); d_s = 0
    Int = a*s*np.sqrt(2*np.pi)
    return Int

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
def spatial_coherence_odrG_amp(p, x):
    lam=470e-9
    amp = 19.60; ang = p
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2
def spatial_coherence_odrUV_amp(p, x):
    lam=375e-9
    amp = 8.75; ang = p 
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2

def spatial_coherence_odrG_LD(p,x):
    lam=470e-9
    u = 0.37
    amp, ang = p
    return amp * ( (1-u)/2 + u/3 )**(-2) * ( (1-u) * scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam) + (u*(np.pi/2)**0.5) * bessel32(ang, x, lam) / ((np.pi*x*ang/lam)**(3/2)))**2

def bessel32(phi, baseline, lam):
    x = np.pi * baseline * phi/lam
    return np.sqrt(2/(np.pi*x**3)) * (np.sin(x) - x*np.cos(x))

def rad2mas(x):
    return 180*3600*1000/np.pi * x
def mas2rad(x):
    return np.pi/(180*3600*1000) * x

def fourier(data):
    fft  = np.abs(np.fft.fft(data-1))
    xfft = np.linspace(0,1/1.6,len(data),endpoint=True)
    return xfft, fft

# Function for extrapolating the limb darkening coefficient
def get_u(temp_star, logg_star):
    # read in table with LD coefficients
    table = np.loadtxt("tableu.txt", delimiter=' ', dtype={'names': ('logg', 'temp', 'Z', 'xi', 'u', 'Filt', 'Met'), 'formats': (float, float, float, float, float, '|S15', '|S15')}, usecols=(1,2,3,4,5,6,7))
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
        u_want = round(float(f(logg_star)),2)
        plt.plot( float(logg_star), u_want, marker='o', color='black')
        
    elif len(logg) == 0:
        plt.plot(logg1, u1, marker='o',linestyle='', color='blue', label=str(temp1))
        plt.plot(logg2, u2, marker='x',linestyle='', color='red', label=str(temp2))
        f1 = scipy.interpolate.interp1d(logg1, u1,'cubic', bounds_error=False, fill_value='extrapolate')
        f2 = scipy.interpolate.interp1d(logg2, u2,'cubic', bounds_error=False, fill_value='extrapolate')
        y1new = f1(xnew)
        y2new = f2(xnew)
        plt.plot(xnew, y1new, color='blue')
        plt.plot(xnew, y2new, color='red')
        u1_want = f1(logg_star)
        u2_want = f2(logg_star)
        print(round(float(u1_want),2))
        print(round(float(u2_want),2))
        u_want = round(float(np.mean([u1_want, u2_want])),2)
        plt.plot(float(logg_star), u_want, marker='o', color='black')
    plt.legend()    
    return(u_want)

############################################
# Functions for simulating the uncertainty #
############################################
def single_zone_analysis(g2, x, center, amp_0, mu_0, sigma):
    s = center-50; e = center+50
    # Extract the g2 zone
    x_zone = x[(x>s) & (x<e)]
    y_zone = g2[(x>s) & (x<e)]

    # Add the peak
    for i in range (0, len(y_zone)):
        y_zone[i] += gauss(x_zone[i], amp_0, mu_0+center, sigma, 0)
    # Re-fit
    xplotf, popt, perr = fit_fixed(y_zone, x_zone, s, e, sigma, mu_start=center-2)
    Int = integral_fixed(popt, perr, sigma)

    return Int

def simulate_uncertainty(g2, x, popt, sigma):
    amp_0 = popt[0]
    mu_0  = popt[1]

    # Now add it onto consecutive g2 sections
    ints = []    
    # Positive range
    for j in range (1,80):      
        center = j*100
        ints.append(single_zone_analysis(g2, x, center, amp_0, mu_0, sigma))        
    # Negative range
    for j in range (1,80):  
        center = -j*100
        ints.append(single_zone_analysis(g2, x, center, amp_0, mu_0, sigma))

    rms_error = np.std(ints)
    return rms_error