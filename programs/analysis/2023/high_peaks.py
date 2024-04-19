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
import os
from scipy import odr
from collections import OrderedDict
from matplotlib.offsetbox import AnchoredText
from optparse import OptionParser
import math

import utilities as uti
import corrections as cor
import geometry as geo


stars = ['Mimosa', 'Etacen', 'Nunki', 'Dschubba']

# Option parser for options
parser = OptionParser()
parser.add_option("-o", "--only", dest="onlys", help="only telescope combinations")

(options, args) = parser.parse_args()
onlys = str(options.onlys)

if onlys != "None":
    onlys = onlys.split(",")

# Create array of fixed parameters
mu_A = np.zeros((5,5)); mu_A[:] = np.nan
dmu_A = np.zeros((5,5)); dmu_A[:] = np.nan
mu_B = np.zeros((5,5)); mu_B[:] = np.nan
sigma_A = np.zeros((5,5)); sigma_A[:] = np.nan
sigma_B = np.zeros((5,5)); sigma_B[:] = np.nan
amp_A = np.zeros((5,5)); amp_A[:] = np.nan
amp_B = np.zeros((5,5)); amp_B[:] = np.nan

################################################
####### Cleaning the measurement data ##########
################################################
g2_allA = np.zeros((5,5), dtype=object); g2_allA[:] = 'nan'
g2_allB = np.zeros((5,5), dtype=object); g2_allB[:] = 'nan'

def cleaning_adding(star, telcombi):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)  

    chAs = np.loadtxt("g2_functions/{}/{}/chA.g2".format(star, telstring))
    chBs = np.loadtxt("g2_functions/{}/{}/chB.g2".format(star, telstring))
    if g2_allA[c1,c2] == 'nan':
        g2_allA[c1,c2] = np.zeros(len(chAs[0]))
        g2_allB[c1,c2] = np.zeros(len(chAs[0]))

    # Demo function for initializing x axis
    demo = chAs[0]
    x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)

    # loop over every g2 function chunk
    for i in range(0,len(chAs)):
        # Read g2 function
        chA = chAs[i]
        chB = chBs[i]
        # Do some more data cleaning, e.g. lowpass filters
        chA = cor.lowpass(chA)
        chB = cor.lowpass(chB)

        '''
        ### building fft of g2 to cut out noise ###
        F_fft = plt.figure(figsize=(12,7))
        ax1 = F_fft.add_subplot(121)
        stepsize = 1.6e-3                   # sampling bin size
        N = len(chA)
        chAfft = chA # für auto corr teil ohne crosstalk [5500:10000]            
        N = len(chAfft)
        xfft = np.linspace(0.0, stepsize*N, N)
        ax1.plot(xfft, chAfft, label='A') 
        x_fft = np.linspace(0.0, 1./(2.*stepsize), N//2) #N2//2)
        chA_fft = np.abs(np.fft.fft(chAfft)/(N/2)) # ct4_fft = np.abs(np.fft.fft(ct4)/(N2))
        #chA_freq, rest = find_peaks(chA_fft, threshold=[0.5e-8, 1.e-8], width=[0,5])
        #print(chA_freq)
        ax2 = F_fft.add_subplot(122)
        ax2.plot(x_fft, chA_fft[0:N//2], label='A')
        '''
        # more data cleaning with notch filter for higher frequencies
        freqA = [45,95,110,145,155,175,195]
        for j in range(len(freqA)):
            chA = cor.notch(chA, freqA[j]*1e6, 80)
        freqB = [50,90,110]
        for j in range(len(freqB)):
            chB = cor.notch(chB, freqB[j]*1e6, 80)
    
        '''
        ### Plot g2 after cleaning ####
        chAfft = chA
        ax1.plot(xfft, chAfft, label='A')
        ax1.legend()
        ax1.set_xlabel('bins of 1.6ns')
        chA_fft = np.abs(np.fft.fft(chAfft)/(N/2))
        ax2.plot(x_fft, chA_fft[0:N//2], label='A')
        ax2.set_ylim(0,8e-8)
        ax2.legend()
        ax2.set_xlabel('MHz')
        #plt.show()
        plt.close()
        '''    
        # calculating SN
        noise_A = np.std(chA)
        ampA = max(chA[(x>-20) & (x<20)]) - 1
        ratioA = ampA/noise_A

        noise_B = np.std(chB)
        ampB = max(chB[(x>-20) & (x<20)]) - 1
        ratioB = ampB/noise_B
        print(i, ratioA, ratioB)

        if telstring == '13':
            if ratioA >= 3:
                print(f'A: {i}')
                g2_allA[c1,c2] += chA/np.std(chA)**2
            if ratioB >= 2: 
                print(f'B: {i}')   
                g2_allB[c1,c2] += chB/np.std(chB)**2

        
        if ratioA >= 5:
            print(f'A: {i}')
            g2_allA[c1,c2] += chA/np.std(chA)**2
        if ratioB >= 2:    
            g2_allB[c1,c2] += chB/np.std(chB)**2
            print(f'B: {i}')
   
    print("Cleaning done")

################################################
#### Analysis over whole measurement time #####
################################################
plt.figure("CrossCorrHigh", figsize=(12,8))
def par_fixing(telcombi):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)
    plotnumber = len(telcombis)*100 + 10 + telcombis.index(telstring) + 1
    # read in g2 fct for telcombi
    chA = g2_allA[c1,c2]  
    chB = g2_allB[c1,c2]  

    # Demo function for initializing x axis
    demo = chA
    x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)
    # normalizing g2 fct
    chA /= np.mean(chA)
    chB /= np.mean(chB)

    # Fit for gaining mu and sigma to fix these parameters for different baseline combis
    plt.figure("CrossCorrHigh")
    plt.subplot(plotnumber)
    plt.title("Cross correlation data of all stars for {}".format(telstring))
    print("Fixed parameters")
    # Channel A
    xplot, popt, perr = uti.fit(chA, x, -50, +50)
    mu_A[c1][c2] = popt[1]; sigma_A[c1][c2] = popt[2] # fixing mu and sigma
    amp_A[c1][c2] = popt[0]*1e7
    noise_A = np.std(chA)*1e7
    dmu_A[c1][c2] = perr[1]
    dsigA = []; dsigA = perr[2]
    integral, dintegral = uti.integral(popt, perr)
    print("{} A 470nm amp: {:.2f}e-7 +/- {:.2f}e-7 \t mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs \t A Noise: {:.2f} \t Ratio: {:.2f}".format(telstring, amp_A[c1][c2], perr[0]*1e7, mu_A[c1][c2], perr[1],sigma_A[c1][c2],perr[2],1e6*integral,1e6*dintegral, noise_A, amp_A[c1][c2]/noise_A))
    plt.plot(x, chA, label=telstring + "A", color=uti.color_chA)
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    # Channel B
    xplot, popt, perr = uti.fit(chB, x, -50, +50)
    mu_B[c1][c2] = popt[1]; sigma_B[c1][c2] = popt[2]
    amp_B[c1][c2] = popt[0]*1e7
    noise_B = np.std(chB)*1e7
    dmuB = []; dsigB = []
    dmuB = perr[1]; dsigB = perr[2]
    integral, dintegral = uti.integral(popt, perr)
    print ("{} B 375nm amp: {:.2f}e-7 +/- {:.2f}e-7 \t mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs \t B Noise: {:.2f} \t Ratio: {:.2f}".format(telstring,amp_B[c1][c2], perr[0]*1e7, mu_B[c1][c2],perr[1],sigma_B[c1][c2],perr[2],1e6*integral,1e6*dintegral, noise_B, amp_B[c1][c2]/noise_B))
    plt.plot(x, chB, label=telstring + "B", color=uti.color_chB)
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    
    plt.legend(); plt.grid()
    plt.xlim(-100,100)
    plt.ticklabel_format(useOffset=False)
    plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")
    plt.tight_layout()
    print(f'DONE par fixing for {telstring}')

    np.savetxt(f'g2_functions/mu_sig_{telstring}_high.txt', np.c_[mu_A[c1,c2], dmu_A[c1,c2], sigma_A[c1,c2], dsigA, mu_B[c1,c2], dmuB, sigma_B[c1,c2], dsigB], header='A: mu, dmu, sig, dsig /t B: mu, dmu, sig, dsig')


# Loop over all the stars
for i in range(len(stars)):
    star = stars[i]
    print(star)
    for c1 in range (1,5):
        for c2 in range(1,5):
            if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
                telcombi = [c1,c2]
                telcombistring = str(c1) + str(c2)
                print ("Found telescope combination {}".format(telcombi))
                if telcombistring in onlys or onlys == "None":
                    cleaning_adding(star, telcombi)
#print(g2_allA)
telcombis = []
for c1 in range (1,5):
    for c2 in range(1,5):
        if g2_allA[c1,c2] != 'nan':
            telcombis.append(f'{c1}{c2}')
for c1 in range (1,5):
    for c2 in range(1,5):
        if g2_allA[c1,c2] != 'nan':
            telcombi = [c1,c2]
            par_fixing(telcombi)
plt.show()

