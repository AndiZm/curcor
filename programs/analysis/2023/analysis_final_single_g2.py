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
import par_fixing_all as pfa
print("DONE par fixing all")

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
#mu_A = np.zeros((5,5)); mu_A[:] = np.nan
#dmu_A = np.zeros((5,5)); dmu_A[:] = np.nan
#mu_B = np.zeros((5,5)); mu_B[:] = np.nan
sigma_A = np.zeros((5,5)); sigma_A[:] = np.nan
dsigma_A = np.zeros((5,5)); dsigma_A[:] = np.nan
sigma_B = np.zeros((5,5)); sigma_B[:] = np.nan
dsigma_B = np.zeros((5,5)); dsigma_B[:] = np.nan
#amp_A = np.zeros((5,5)); amp_A[:] = np.nan
#amp_B = np.zeros((5,5)); amp_B[:] = np.nan

lam_g = 470e-9
lam_uv = 375e-9
lam_all = 422.5e-9

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
        N = len(chB)
        chBfft = chB # für auto corr teil ohne crosstalk [5500:10000]            
        N = len(chBfft)
        xfft = np.linspace(0.0, stepsize*N, N)
        ax1.plot(xfft, chBfft, label='B') 
        x_fft = np.linspace(0.0, 1./(2.*stepsize), N//2) #N2//2)
        chB_fft = np.abs(np.fft.fft(chBfft)/(N/2)) # ct4_fft = np.abs(np.fft.fft(ct4)/(N2))
        #chA_freq, rest = find_peaks(chA_fft, threshold=[0.5e-8, 1.e-8], width=[0,5])
        #print(chA_freq)
        ax2 = F_fft.add_subplot(122)
        ax2.plot(x_fft, chB_fft[0:N//2], label='B')
        '''
        # more data cleaning with notch filter for higher frequencies
        freqA = [45,90,95,110,145,155,175,195]
        for j in range(len(freqA)):
            chA = cor.notch(chA, freqA[j]*1e6, 80)
        freqB = [50, 90, 110]
        for j in range(len(freqB)):
            chB = cor.notch(chB, freqB[j]*1e6, 80)
    
        '''
        ### Plot g2 after cleaning ####
        chBfft = chB
        ax1.plot(xfft, chBfft, label='B')
        ax1.legend()
        ax1.set_xlabel('bins of 1.6ns')
        chB_fft = np.abs(np.fft.fft(chBfft)/(N/2))
        ax2.plot(x_fft, chB_fft[0:N//2], label='B clean')
        ax2.set_ylim(0,8e-8)
        ax2.legend()
        ax2.set_xlabel('MHz')
        plt.show()
        #plt.close()
        '''
        chA_clean[c1,c2][i] = chA
        chB_clean[c1,c2][i] = chB
    print("Cleaning done")

#########################################
###### Chunk analysis ###################
#########################################
plt.figure('SC', figsize=(12,8))
plt.suptitle("Spatial coherence of {}".format(star))

ints_fixedA = []; dints_fixedA = []
ints_fixedB = []; dints_fixedB = []
baselines_all = []; dbaselines_all = []
time_all = [] ; telstrings =[]

def chunk_ana(star, telcombi):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)
    plotnumber = len(telcombis)*100 + 10 + telcombis.index(telstring) + 1  
    
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
    #print(len(chAs), rows)
    
    singlesA, axsA = plt.subplots(rows,cols, sharex=True, sharey=True)
    singlesA.suptitle(f'{star} single g2 functions for {telstring} and 470nm')
    singlesA.supxlabel('Time difference (ns)')
    singlesA.supylabel('$g^(2)$')

    singlesB, axsB = plt.subplots(rows,cols, sharex=True, sharey=True)
    singlesB.suptitle(f'{star} single g2 functions for {telstring} and 375nm')
    singlesB.supxlabel('Time difference (ns)')
    singlesB.supylabel('$g^(2)$')

    # Define figure to show integrals of g2 fcts
    plt.figure(f'Integrals {telstring}')
    plt.suptitle(f'Integrals of single g2 functions for {telstring}')
    # Define figure to show means of g2 fcts
    #plt.figure(f'means {telstring}')
    #plt.suptitle(f'Means of single g2 functions for {telstring}')
    ## Define figure to show sigmas of g2 fcts
    #plt.figure(f'sigmas {telstring}')
    #plt.suptitle(f'Sigmas of single g2 functions for {telstring}')
    ## Define figure to show amps of g2 fcts
    #plt.figure(f'amps {telstring}')
    #plt.suptitle(f'Amplitudes of single g2 functions for {telstring}')
    
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

        # Fit with fixed sigma of each telcombi
        # chA
        xplotf, popt_A, perr_A = uti.fit_fixed(chA, x, -50, 50, pfa.avg_sigA)
        Int, dInt = uti.integral_fixed(popt_A, perr_A, pfa.avg_sigA) #, factor=2.3)
        ints_fixedA.append(1e6*Int); dints_fixedA.append(1e6*dInt)# in femtoseconds
        #noise_A = np.std(chA); ratioA = popt_A[0]/noise_A
        #print(popt_A)
        # chB
        xplotf, popt_B, perr_B = uti.fit_fixed(chB, x, -50, 50, pfa.avg_sigB)
        Int, dInt = uti.integral_fixed(popt_B, perr_B, pfa.avg_sigB) #, factor=2.38)
        ints_fixedB.append(1e6*Int); dints_fixedB.append(1e6*dInt)# in femtoseconds
        #noise_B = np.std(chB); ratioB = popt_B[0]/noise_B
        #print(f'{i} ratio SN A = {ratioA} \t ratio SN B = {ratioB}')
        
        ### Plots ###
        #plt.figure(f'means {telstring}')
        #plt.subplot(121)
        #plt.title('470nm')
        #plt.axhline( mu_A[c1][c2], ls='--', color='red', alpha=0.7, label='mu fixed')
        #plt.errorbar(i, popt_A[1], perr_A[1], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
        #plt.xlabel("# time chunk") 
        #plt.ylabel("Time (ns)") 
        ## legend 
        #handles, labels = plt.gca().get_legend_handles_labels()
        #by_label = OrderedDict(zip(labels, handles)) 
        #plt.legend(by_label.values(), by_label.keys())
        #plt.subplot(122)
        #plt.title('375nm')
        #plt.axhline( mu_B[c1][c2], ls='--', color='red', alpha=0.7, label='mu fixed')
        #plt.errorbar(i, popt_B[1], perr_B[1], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
        #plt.xlabel("# time chunk") 
        #plt.ylabel("Time (ns)") 
        ## legend 
        #handles, labels = plt.gca().get_legend_handles_labels()
        #by_label = OrderedDict(zip(labels, handles)) 
        #plt.legend(by_label.values(), by_label.keys())

        #plt.figure(f'sigmas {telstring}')
        #plt.subplot(121)
        #plt.title('470nm')
        #plt.axhline( sigma_A[c1][c2], ls='--', color='red', alpha=0.7, label='sigma fixed')
        #plt.errorbar(i, popt_A[2], perr_A[2], marker='o', ls='', color='blue', alpha=0.7, label='sigma free')
        #plt.xlabel("# time chunk") 
        #plt.ylabel("Time (ns)") 
        ## legend 
        #handles, labels = plt.gca().get_legend_handles_labels()
        #by_label = OrderedDict(zip(labels, handles)) 
        #plt.legend(by_label.values(), by_label.keys())
        #plt.subplot(122)
        #plt.title('375nm')
        #plt.axhline( sigma_B[c1][c2], ls='--', color='red', alpha=0.7, label='sigma fixed')
        #plt.errorbar(i, popt_B[2], perr_B[2], marker='o', ls='', color='blue', alpha=0.7, label='sigma free')
        #plt.xlabel("# time chunk") 
        #plt.ylabel("Time (ns)") 
        ## legend 
        #handles, labels = plt.gca().get_legend_handles_labels()
        #by_label = OrderedDict(zip(labels, handles)) 
        #plt.legend(by_label.values(), by_label.keys())

        #plt.figure(f'amps {telstring}')
        #plt.subplot(121)
        #plt.title('470nm')
        #plt.errorbar(i, popt_A[0], perr_A[0], marker='o', ls='', color='red', alpha=0.7, label='offset free')
        #plt.errorbar(i, popt_A1[0], perr_A1[0], marker='o', ls='', color='blue', alpha=0.7, label='offset fixed')
        #plt.xlabel("# time chunk") 
        ##plt.ylabel("g2") 
        ## legend 
        #handles, labels = plt.gca().get_legend_handles_labels()
        #by_label = OrderedDict(zip(labels, handles)) 
        #plt.legend(by_label.values(), by_label.keys())
        #plt.subplot(122)
        #plt.title('375nm')
        #plt.errorbar(i, popt_B[0], perr_B[0], marker='o', ls='', color='red', alpha=0.7, label='offset free')
        #plt.errorbar(i, popt_B1[0], perr_B1[0], marker='o', ls='', color='blue', alpha=0.7, label='offset fixed')
        #plt.xlabel("# time chunk") 
        ##plt.ylabel("g2") 
        ## legend 
        #handles, labels = plt.gca().get_legend_handles_labels()
        #by_label = OrderedDict(zip(labels, handles)) 
        #plt.legend(by_label.values(), by_label.keys())

        plt.figure(f'Integrals {telstring}')
        plt.subplot(121)
        plt.title('470nm')
        plt.errorbar(i, ints_fixedA[-1], dints_fixedA[-1], marker='o', ls='', color=uti.color_chA, alpha=0.7)
        plt.xlabel("# time chunk") 
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        #handles, labels = plt.gca().get_legend_handles_labels()
        #by_label = OrderedDict(zip(labels, handles)) 
        #plt.legend(by_label.values(), by_label.keys())
        plt.subplot(122)
        plt.title('375nm')
        plt.errorbar(i, ints_fixedB[-1], dints_fixedB[-1], marker='o', ls='', color=uti.color_chB, alpha=0.7)
        plt.xlabel("# time chunk") 
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        #handles, labels = plt.gca().get_legend_handles_labels()
        #by_label = OrderedDict(zip(labels, handles)) 
        #plt.legend(by_label.values(), by_label.keys())


        plt.figure('SC')
        plt.subplot(121)
        plt.title('470nm')
        plt.errorbar(x=baseline, xerr=dbaseline, y=ints_fixedA[-1], yerr=dints_fixedA[-1], marker='o', color=uti.color_chA)
        plt.axhline(y=0, color="black", linestyle="--") 
        plt.xlabel("Projected baseline (m)")
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        #handles, labels = plt.gca().get_legend_handles_labels()
        #by_label = OrderedDict(zip(labels, handles)) 
        #plt.legend(by_label.values(), by_label.keys())
        plt.subplot(122)
        plt.title('375nm')
        plt.errorbar(x=baseline, xerr=dbaseline, y=ints_fixedB[-1], yerr=dints_fixedB[-1], marker='o', color=uti.color_chB)
        plt.axhline(y=0, color="black", linestyle="--") 
        plt.xlabel("Projected baseline (m)")
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        #handles, labels = plt.gca().get_legend_handles_labels()
        #by_label = OrderedDict(zip(labels, handles)) 
        #plt.legend(by_label.values(), by_label.keys())

        # errorbars for g2 fct
        errorA = []; errorB = []
        errorA.append(np.std(chA[0:4000]))
        errorB.append(np.std(chB[0:4000]))
        # only plot certain range of g2 fct -> cut data to that range
        #chAss = []; chBss = []
        #for k in range(0, len(x)):
        #    if -100<= x[k] <=100:
        #        chAss.append(chA[k])
        #        chBss.append(chB[k])       
        #demo = chAss
        #xnew = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)  

        a = int(np.floor(i/cols))
        b = int(i%cols)
        #axsA[a,b].errorbar(xnew, chAss, yerr=errorA, linestyle="-", color = uti.color_chA,   alpha=0.7)
        #axsA[a,b].errorbar(x, chA, yerr=errorA, linestyle="-", color = uti.color_chA,   alpha=0.7)
        axsA[a,b].plot(x, chA, linestyle="-", color = uti.color_chA,   alpha=0.7)
        axsA[a,b].plot(xplotf, uti.gauss(xplotf, popt_A[0], popt_A[1], pfa.avg_sigA, popt_A[2]), color='red', linestyle="--", zorder=4)                
        #plt.ylim(np.min(chAss), np.max(chAss))
        axsA[a,b].set_xlim(-100,100)
        axsA[a,b].text(x=-100, y=0.5e-6+1, s=tstring_short, fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
        axsA[a,b].axhline(y=1, color='black', linestyle='--', linewidth=1)
        #axsA[a,b].legend() 

        #axsB[a,b].errorbar(xnew, chBss, yerr=errorB, linestyle="-", color = uti.color_chB,   alpha=0.7)
        #axsB[a,b].errorbar(x, chB, yerr=errorB, linestyle="-", color = uti.color_chB,   alpha=0.7)
        axsB[a,b].plot(x, chB, linestyle="-", color = uti.color_chB,   alpha=0.7)
        axsB[a,b].plot(xplotf, uti.gauss(xplotf, popt_B[0], popt_B[1], pfa.avg_sigB, popt_B[2]), color='red', linestyle="--", zorder=4)                
        axsB[a,b].set_xlim(-100,100)
        axsB[a,b].text(x=-100, y=0.5e-6+1, s=tstring_short, fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
        axsB[a,b].axhline(y=1, color='black', linestyle='--', linewidth=1)
        #axsB[a,b].legend() 
        
    print("DONE Chunks {}".format(telcombi))


# Loop over every potential telescope combination and check if it exists
telcombis = []
for c1 in range (1,5):
    for c2 in range(1,5):
        if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
            telcombis.append("{}{}".format(c1,c2))
            telstring = f"{c1}{c2}"
            
for c1 in range (1,5):
    for c2 in range(1,5):
        if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
            telcombi = [c1,c2]
            telcombistring = str(c1) + str(c2)
            print ("Found telescope combination {}".format(telcombi))
            if telcombistring in onlys or onlys == "None":
                cleaning(star, telcombi)
                chunk_ana(star, telcombi)

plt.show()     
