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

star = sys.argv[1]

# Option parser for options
parser = OptionParser()
parser.add_option("-o", "--only", dest="onlys", help="only telescope combinations")

(options, args) = parser.parse_args()
onlys = str(options.onlys)

if onlys != "None":
    onlys = onlys.split(",")

bl_HBT = []
# Open text file with star data from HBT
f = open("stars_HBT.txt")
# Find line for the star
line = f.readline()
while star not in line:
    line = f.readline()
lam_HBT = line.split()[1]
ang_HBT = uti.mas2rad(float(line.split()[2]))
logg_star = line.split()[3]
temp_star = int(line.split()[4])
line = f.readline()
while "[end]" not in line:
    bl_HBT.append(float(line.split()[0]))
    line = f.readline()
f.close()

combicolorsA = np.zeros((5,5), dtype=object); combicolorsA[:] = np.nan
combicolorsA[1,3] = 'lightblue'
combicolorsA[1,4] = 'deepskyblue'
combicolorsA[3,4] = 'dodgerblue'

combicolorsB = np.zeros((5,5), dtype=object); combicolorsB[:] = np.nan
combicolorsB[1,3] = 'mediumpurple'
combicolorsB[1,4] = 'blueviolet'
combicolorsB[3,4] = 'purple'

combicolors = np.zeros((5,5), dtype=object); combicolors[:] = np.nan
combicolors[1,3] = "blue"
combicolors[1,4] = "fuchsia"
combicolors[3,4] = "turquoise"

# Create array of fixed parameters
mu_A = np.zeros((5,5)); mu_A[:] = np.nan
dmu_A = np.zeros((5,5)); dmu_A[:] = np.nan
mu_B = np.zeros((5,5)); mu_B[:] = np.nan
sigma_A = np.zeros((5,5)); sigma_A[:] = np.nan
sigma_B = np.zeros((5,5)); sigma_B[:] = np.nan
amp_A = np.zeros((5,5)); amp_A[:] = np.nan
amp_B = np.zeros((5,5)); amp_B[:] = np.nan

lam_g = 470e-9
lam_uv = 375e-9
lam_all = 422.5e-9
amp_g = 21.25
amp_uv = 10

ratioA = []; ratioB = []

################################################
####### Cleaning the measurement data ##########
################################################
chA_clean = np.zeros((5,5), dtype=object); chA_clean[:] = np.nan 
chB_clean = np.zeros((5,5), dtype=object); chB_clean[:] = np.nan 
def cleaning(star, telcombi):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)  

    chAs = np.loadtxt("g2_functions/{}/{}/chA.g2".format(star, telstring))
    chBs = np.loadtxt("g2_functions/{}/{}/chB.g2".format(star, telstring))
    chA_clean[c1][c2] = np.zeros(len(chAs), dtype=object)
    chB_clean[c1][c2] = np.zeros(len(chBs), dtype=object)

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
        freqB = [50]
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
        chA_clean[c1,c2][i] = chA
        chB_clean[c1,c2][i] = chB
    print("Cleaning done")

################################################
#### Analysis over whole measurement time #####
################################################
plt.figure("CrossCorr", figsize=(12,8))
def par_fixing(star, telcombi):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)
    plotnumber = len(telcombis)*100 + 10 + telcombis.index(telstring) + 1

    # Read in the data g2 functions already cleaned
    #chAs    = np.loadtxt("g2_functions/{}/{}/chA.g2".format(star, telstring))     
    #chBs    = np.loadtxt("g2_functions/{}/{}/chB.g2".format(star, telstring)) 
    chAs = chA_clean[c1,c2]  
    chBs = chB_clean[c1,c2]  

    # Demo function for initializing x axis and some stuff
    demo = chAs[0]
    x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)
    
    # Combine all data for channel A and B each for initial parameter estimation and fixing
    g2_allA = np.zeros(len(x)); g2_allB = np.zeros(len(x))
    for i in range (0,len(chAs)):
        #plt.plot(chAs[i]); plt.plot(chBs[i]); plt.show()
        g2_allA += chAs[i]/np.std(chAs[i][0:4500])**2
        g2_allB += chBs[i]/np.std(chBs[i][0:4500])**2
    g2_allA /= np.mean(g2_allA[0:4500])
    g2_allB /= np.mean(g2_allB[0:4500])

    # Fit for gaining mu and sigma to fix these parameters for different baseline combis
    plt.figure("CrossCorr")
    plt.subplot(plotnumber)
    plt.title("Cross correlation data of {} for {}".format(star, telstring))
    print("Fixed parameters")
    # Channel A
    xplot, popt, perr = uti.fit(g2_allA, x, -50, +50)
    mu_A[c1][c2] = popt[1]; sigma_A[c1][c2] = popt[2] # fixing mu and sigma
    amp_A[c1][c2] = popt[0]*1e7
    noise_A = np.std(g2_allA)*1e7
    dmu_A[c1][c2] = perr[1]
    dsigA = []; dsigA = perr[2]
    integral, dintegral = uti.integral(popt, perr)
    print("{} A 470nm amp: {:.2f}e-7 +/- {:.2f}e-7 \t mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs \t A Noise: {:.2f} \t Ratio: {:.2f}".format(telstring, amp_A[c1][c2], perr[0]*1e7, mu_A[c1][c2], perr[1],sigma_A[c1][c2],perr[2],1e6*integral,1e6*dintegral, noise_A, amp_A[c1][c2]/noise_A))
    ratioA.append(amp_A[c1][c2]/noise_A)
    plt.plot(x, g2_allA, label=telstring + "A", color=uti.color_chA)
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    # Channel B
    xplot, popt, perr = uti.fit(g2_allB, x, -50, +50)
    mu_B[c1][c2] = popt[1]; sigma_B[c1][c2] = popt[2]
    amp_B[c1][c2] = popt[0]*1e7
    noise_B = np.std(g2_allB)*1e7
    dmuB = []; dsigB = []
    dmuB = perr[1]; dsigB = perr[2]
    integral, dintegral = uti.integral(popt, perr)
    print ("{} B 375nm amp: {:.2f}e-7 +/- {:.2f}e-7 \t mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs \t B Noise: {:.2f} \t Ratio: {:.2f}".format(telstring,amp_B[c1][c2], perr[0]*1e7, mu_B[c1][c2],perr[1],sigma_B[c1][c2],perr[2],1e6*integral,1e6*dintegral, noise_B, amp_B[c1][c2]/noise_B))
    ratioB.append(amp_B[c1][c2]/noise_B)
    plt.plot(x, g2_allB, label=telstring + "B", color=uti.color_chB)
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    
    plt.legend(); plt.xlim(-100,100); plt.grid()
    plt.ticklabel_format(useOffset=False)
    plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")
    plt.tight_layout()
    print(f'DONE par fixing for {telstring}')

#########################################
###### Chunk analysis ###################
#########################################
plt.figure('SC', figsize=(12,8))
plt.suptitle("Spatial coherence of {}".format(star))

intsA = []; dintsA = []; times = []
intsB = []; dintsB = []
ints_fixedA = []; dints_fixedA = []
ints_fixedB = []; dints_fixedB = []
ints_fixedA1 = []; dints_fixedA1 = []
ints_fixedB1 = []; dints_fixedB1 = []
baselines_all = []; dbaselines_all = []
time_all = [] ; telstrings =[]
baselinesA = []; dbaselinesA = []
baselinesB = []; dbaselinesB = []

# Define figure to show fixed means
plt.figure('means fixed')
plt.suptitle('Fixed means')

def chunk_ana(star, telcombi, ratioA, ratioB):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)
    plotnumber = len(telcombis)*100 + 10 + telcombis.index(telstring) + 1  
    
    # initialize cleaned arrays
    #chA_clean = []; chB_clean = []
    ampA = []; ampB = []; muA = []; muB =[] ; chiA =[]; chiB = []; dmuA = []; dmuB =[]
    ffts = []
    #chAs    = np.loadtxt("g2_functions/{}/{}/chA.g2".format(star, telstring))
    #chBs    = np.loadtxt("g2_functions/{}/{}/chB.g2".format(star, telstring))
    chAs = chA_clean[c1,c2]  
    chBs = chB_clean[c1,c2]  

    # Read the telescope data (acquisition times of chunks, baselines and baseline uncertainties)
    timestrings = np.loadtxt("g2_functions/{}/{}/ac_times.txt".format(star,telstring))
    baselines   = np.loadtxt("g2_functions/{}/{}/baselines.txt".format(star,telstring))
    dbaselines  = np.loadtxt("g2_functions/{}/{}/dbaselines.txt".format(star,telstring))
    
    # Demo function for initializing x axis and some stuff
    demo = chAs[0]
    x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)

    # Define figure which will show individual g2 cross correlations for 470nm chA
    cols = 4
    rows = max (math.ceil(len(chAs)/cols) ,2)
    print(len(chAs), rows)
    
    singlesA, axsA = plt.subplots(rows,cols, sharex=True, sharey=True)
    singlesA.suptitle(f'Single g2 functions for {telstring} and 470nm')
    singlesA.supxlabel('Time difference (ns)')
    singlesA.supylabel('$g^(2)$')

    singlesB, axsB = plt.subplots(rows,cols, sharex=True, sharey=True)
    singlesB.suptitle(f'Single g2 functions for {telstring} and 375nm')
    singlesB.supxlabel('Time difference (ns)')
    singlesB.supylabel('$g^(2)$')

    # Define figure to show integrals of g2 fcts
    plt.figure(f'Integrals {telstring}')
    plt.suptitle(f'Integrals of single g2 functions for {telstring}')
    # Define figure to show means of g2 fcts
    plt.figure(f'means {telstring}')
    plt.suptitle(f'Means of single g2 functions for {telstring}')
    # Define figure to show amps of g2 fcts
    plt.figure(f'amps {telstring}')
    plt.suptitle(f'Amplitudes of single g2 functions for {telstring}')
    


    g2A = np.zeros(len(x)); g2B = np.zeros(len(x))

    # loop over every g2 function chunk
    for i in range(0,len(chAs)):
        # Check acquisition time of original data
        timestring = ephem.Date(timestrings[i])
        tstring_short = str(timestring)[5:-3]
        baseline   = baselines[i]
        dbaseline  = dbaselines[i]
        baselines_all.append(baseline); dbaselines_all.append(dbaseline)
        time_all.append(timestring)
        telstrings.append(telstring)  
    
        # Read g2 function
        chA = chAs[i]
        chB = chBs[i]

        # Fit with fixed mu and sigma
        # chA
        xplotf, popt_A, perr_A = uti.fit_fixed(chA, x, -50, 50, mu_A[c1][c2], sigma_A[c1][c2])
        Int, dInt = uti.integral_fixed(popt_A, perr_A, sigma_A[c1][c2], factor=2.3)
        ints_fixedA.append(1e6*Int); dints_fixedA.append(1e6*dInt)# in femtoseconds
        # chB
        xplotf, popt_B, perr_B = uti.fit_fixed(chB, x, -50, 50, mu_B[c1][c2], sigma_B[c1][c2])
        Int, dInt = uti.integral_fixed(popt_B, perr_B, sigma_B[c1][c2], factor=2.38)
        ints_fixedB.append(1e6*Int); dints_fixedB.append(1e6*dInt)# in femtoseconds
        
        # Fit with mu free
        # chA
        xplotf1, popt_A1, perr_A1 = uti.fit_fixed1(chA, x, -50, 50, sigma_A[c1][c2], mu_start=mu_A[c1][c2])
        Int1, dInt1 = uti.integral_fixed(popt_A1, perr_A1, sigma_A[c1][c2], factor=2.3)
        #dInt1 = np.sqrt( dInt1**2 + (np.std(chA)*sig_A*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
        ints_fixedA1.append(1e6*Int1); dints_fixedA1.append(1e6*dInt1)# in femtoseconds
        #print('CHIA = {}'.format(chi_A1))
        # chB
        xplotf1, popt_B1, perr_B1 = uti.fit_fixed1(chB, x, -50, 50, sigma_B[c1][c2], mu_start=mu_B[c1][c2])
        Int1, dInt1 = uti.integral_fixed(popt_B1, perr_B1, sigma_B[c1][c2], factor=2.38)
        #dInt1 = np.sqrt( dInt1**2 + (np.std(chB)*sig_B*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
        ints_fixedB1.append(1e6*Int1); dints_fixedB1.append(1e6*dInt1)# in femtoseconds
        #print('CHIB = {}'.format(chi_B1))

        
        ### Plots ###
        plt.figure(f'means {telstring}')
        plt.subplot(121)
        plt.title('470nm')
        plt.axhline( mu_A[c1][c2], ls='--', color='red', alpha=0.7, label='mu fixed')
        plt.errorbar(i, popt_A1[1], perr_A1[1], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
        plt.xlabel("# time chunk") 
        plt.ylabel("Time (ns)") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())
        plt.subplot(122)
        plt.title('375nm')
        plt.axhline( mu_B[c1][c2], ls='--', color='red', alpha=0.7, label='mu fixed')
        plt.errorbar(i, popt_B1[1], perr_B1[1], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
        plt.xlabel("# time chunk") 
        plt.ylabel("Time (ns)") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())

        plt.figure(f'amps {telstring}')
        plt.subplot(121)
        plt.title('470nm')
        plt.errorbar(i, popt_A[0], perr_A[0], marker='o', ls='', color='red', alpha=0.7, label='mu fixed')
        plt.errorbar(i, popt_A1[0], perr_A1[0], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
        plt.xlabel("# time chunk") 
        #plt.ylabel("g2") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())
        plt.subplot(122)
        plt.title('375nm')
        plt.errorbar(i, popt_B[0], perr_B[0], marker='o', ls='', color='red', alpha=0.7, label='mu fixed')
        plt.errorbar(i, popt_B1[0], perr_B1[0], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
        plt.xlabel("# time chunk") 
        #plt.ylabel("g2") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())

        plt.figure(f'Integrals {telstring}')
        plt.subplot(121)
        plt.title('470nm')
        plt.errorbar(i, ints_fixedA[-1], dints_fixedA[-1], marker='o', ls='', color='red', alpha=0.7, label='mu fixed')
        plt.errorbar(i, ints_fixedA1[-1], dints_fixedA1[-1], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
        plt.xlabel("# time chunk") 
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())
        plt.subplot(122)
        plt.title('375nm')
        plt.errorbar(i, ints_fixedB[-1], dints_fixedB[-1], marker='o', ls='', color='red', alpha=0.7, label='mu fixed')
        plt.errorbar(i, ints_fixedB1[-1], dints_fixedB1[-1], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
        plt.xlabel("# time chunk") 
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())


        plt.figure('SC')
        plt.subplot(121)
        plt.errorbar(x=baseline, xerr=dbaseline, y=ints_fixedA[-1], yerr=dints_fixedA[-1], marker='o', color='red', label='mu fixed')
        plt.errorbar(x=baseline, xerr=dbaseline, y=ints_fixedA1[-1], yerr=dints_fixedA1[-1], marker='o', color='blue', label='mu free')
        plt.axhline(y=0, color="black", linestyle="--") 
        plt.xlabel("Projected baseline (m)")
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())
        plt.subplot(122)
        plt.errorbar(x=baseline, xerr=dbaseline, y=ints_fixedB[-1], yerr=dints_fixedB[-1], marker='o', color='red', label='mu fixed')
        plt.errorbar(x=baseline, xerr=dbaseline, y=ints_fixedB1[-1], yerr=dints_fixedB1[-1], marker='o', color='blue', label='mu free')
        plt.axhline(y=0, color="black", linestyle="--") 
        plt.xlabel("Projected baseline (m)")
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())

        # errorbars for g2 fct
        errorA = []; errorB = []
        errorA.append(np.std(chA[0:4000]))
        errorB.append(np.std(chB[0:4000]))
        # only plot certain range of g2 fct -> cut data to that range
        chAss = []; chBss = []
        for k in range(0, len(x)):
            if -100<= x[k] <=100:
                chAss.append(chA[k])
                chBss.append(chB[k])       
        demo = chAss
        xnew = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)  

        a = int(np.floor(i/cols))
        b = int(i%cols)
        axsA[a,b].errorbar(xnew, chAss, yerr=errorA, linestyle="-", color = uti.color_chA,   alpha=0.7)
        axsA[a,b].plot(xplotf, uti.gauss_fixed(xplotf, popt_A[0], mu_A[c1][c2], sigma_A[c1][c2]), color='red', linestyle="--", zorder=4, label='mu fixed')                
        axsA[a,b].plot(xplotf1, uti.gauss_fixed(xplotf1, popt_A1[0], popt_A1[1], sigma_A[c1][c2]), color='blue', ls='--', zorder=4, label='mu free')
        #plt.ylim(np.min(chAss), np.max(chAss))
        axsA[a,b].set_xlim(-100,100)
        axsA[a,b].text(x=-100, y=0.5e-6+1, s=tstring_short, fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
        axsA[a,b].axhline(y=1, color='black', linestyle='--', linewidth=1)
        axsA[a,b].legend() 

        axsB[a,b].errorbar(xnew, chBss, yerr=errorB, linestyle="-", color = uti.color_chB,   alpha=0.7)
        axsB[a,b].plot(xplotf, uti.gauss_fixed(xplotf, popt_B[0], mu_B[c1][c2], sigma_B[c1][c2]), color='red', linestyle="--", zorder=4, label='mu fixed')                
        axsB[a,b].plot(xplotf1, uti.gauss_fixed(xplotf1, popt_B1[0], popt_B1[1], sigma_B[c1][c2]), color='blue', ls='--', zorder=4, label='mu free')
        axsB[a,b].set_xlim(-100,100)
        axsB[a,b].text(x=-100, y=0.5e-6+1, s=tstring_short, fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
        axsB[a,b].axhline(y=1, color='black', linestyle='--', linewidth=1)
        axsB[a,b].legend() 
        
        
        for r in range(9,15):
            if i == r:
                # take into account SN ratio for summing up and fixing parameters
                noise_As = []; ratio_As = []
                noise_As = np.std(chA)*1e7
                ratio_As = popt_A[0]*1e7/noise_As
                print(ratio_As)

                # Combine all data for channel A and B each for initial parameter estimation and fixing
                g2A += chA/np.std(chA[0:4500])**2
                g2B += chB/np.std(chB[0:4500])**2
                g2A /= np.mean(g2A[0:4500])
                g2B /= np.mean(g2B[0:4500])
    # Fit for gaining mu and sigma to fix these parameters for different baseline combis
    plt.figure("CrossCorr2")
    plt.subplot(plotnumber)
    plt.title(" Reduced cross correlation data of {} for {}".format(star, telstring))
    print("Fixed parameters reduced")
    # Channel A
    xplot, popt, perr = uti.fit(g2A, x, -50, +50)
    muA = popt[1]; sigmaA = popt[2] # fixing mu and sigma
    ampA = popt[0]*1e7
    noiseA = np.std(g2A)*1e7
    dmuA = []; dsigA = []
    dmuA = perr[1]; dsigA = perr[2]
    integral, dintegral = uti.integral(popt, perr)
    print("{} A 470nm amp: {:.2f}e-7 +/- {:.2f}e-7 \t mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs \t A Noise: {:.2f} \t Ratio: {:.2f}".format(telstring, ampA, perr[0]*1e7, muA, perr[1],sigmaA,perr[2],1e6*integral,1e6*dintegral, noiseA, ampA/noiseA))
    plt.plot(x, g2A, label=telstring + "A", color=uti.color_chA)
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    plt.axvline(muA, ls='--', color='red', label='mean')
    plt.legend(); plt.xlim(-100,100); plt.grid()
    plt.ticklabel_format(useOffset=False)
    plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")
    plt.tight_layout()

    plt.figure('means fixed')
    plt.errorbar(telstring, mu_A[c1][c2], dmu_A[c1][c2], marker='o', color=uti.color_chA, label='all data')
    plt.errorbar(telstring, muA,dmuA, marker='x', color=uti.color_chA, label='reduced data')
    plt.xlabel('Telcombi')
    plt.legend()



    print("DONE Chunks {}".format(telcombi))


# Loop over every potential telescope combination and check if it exists
telcombis = []
for c1 in range (1,5):
    for c2 in range(1,5):
        if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
            telcombis.append("{}{}".format(c1,c2))

for c1 in range (1,5):
    for c2 in range(1,5):
        if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
            telcombi = [c1,c2]
            telcombistring = str(c1) + str(c2)
            print ("Found telescope combination {}".format(telcombi))
            if telcombistring in onlys or onlys == "None":
                cleaning(star, telcombi)
                par_fixing(star, telcombi)
                chunk_ana(star, telcombi, ratioA, ratioB)

plt.show()     
