import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl  
from scipy.optimize import curve_fit
from scipy.signal import butter, filtfilt, find_peaks
import scipy.stats as stats
from matplotlib.pyplot import cm
import ephem
import math
import scipy.special as scp
import sys
from brokenaxes import brokenaxes
from matplotlib.gridspec import GridSpec
import os
from scipy import odr
from collections import OrderedDict
from matplotlib.offsetbox import AnchoredText
from optparse import OptionParser
from tqdm import tqdm
from datetime import datetime, timezone

import utilities as uti
import corrections as cor
import geometry_3T as geo3T

star = sys.argv[1]

colors = np.zeros((5), dtype=object); colors[:] = np.nan
colors[1] = "blue"
colors[4] = "fuchsia"
colors[3] = "turquoise"


# Define files to analyze
folders   = [] # Data folders for analysis
ends      = [] # Total number of files used from this folder
telcombis = [] # Combination of telescopes (either 14, 34 or 134)

# Open text file with measurement split data and read the data for the specific star
f = open("measurement_chunks.txt")
# Find line for the star
line = f.readline()
while star not in line:
    line = f.readline()
# Fill arrays with the data
line = f.readline()
while "[end]" not in line:
    folders.append(line.split()[0])
    #stepsizes.append( int(line.split()[1]) )
    ends.append( int(line.split()[2]) )
    telcombis.append( str(line.split()[3]) )
    line = f.readline() 
f.close()

print ("Rates of {}".format(star))

star_small = star[0].lower() + star[1:]
folderpath = "C:/Users/ii/Documents/curcor/corr_results/results_HESS"

def rate_calc (folder, start, stop, telcombi):
    print(folder)
    os.makedirs(f"rates/{star}/{folder}", exist_ok=True)
    # Initialize parameter arrays for data storing
    alt_all = []
    times = []; tplot =[]
    #realt =[]
    #ratio_ratesA = [] ; ratio_ratesB = []

    # Define total figure for plotting all rates of one night for each channel vs time
    plt.rcParams['figure.figsize'] = 22,10
    fig1, (ax1,ax2) = plt.subplots(1,2, sharey='row')
    # add a big axes, hide frame
    fig1.add_subplot(111, frameon=False)  
    plt.tick_params(labelcolor="none", top=False, bottom=False, left=False, right=False) # hide tick label of the big axes
    date = str(folder[0:8])
    ax1.set_title('470nm')
    ax2.set_title('375nm')
    fig1.suptitle("Rates of {} from {}".format(star, date, fontsize=17))
    fig1.supxlabel("Time (UTC)", fontsize=14)
    fig1.supylabel("Rate (GHz)", fontsize=14)
    plt.tight_layout()

    # Define total figure for plotting all rates of one night for each channel vs altitude
    plt.rcParams['figure.figsize'] = 22,10
    fig2, (ax3,ax4) = plt.subplots(1,2, sharey='row')
    # add a big axes, hide frame
    fig2.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor="none", top=False, bottom=False, left=False, right=False) # hide tick label of the big axes
    ax3.set_title('470nm')
    ax4.set_title('375nm')
    fig2.suptitle("Rates of {} from {}".format(star, date, fontsize=17))
    fig2.supxlabel("Altitude", fontsize=14)
    fig2.supylabel("Rate (GHz)", fontsize=14)
    plt.tight_layout()

    # Define files to analyze for rates of one night 
    files =[]
    for i in range(start, stop):
        files.append("{}/{}/size10000/{}_{:05d}.fcorr6".format(folderpath, folder, star_small, i))  
    
    ## Define colormap for plotting all rates of one night of one channel
    #x = np.arange(0, len(files))
    #cm_sub = np.linspace(1.0, 0.0, len(files))
    #colors = [cm.viridis(x) for x in cm_sub]

    # To avoid having CT1 as entry 0, the array will be 5 elements x 5 elements, with the 0th row and column remain empty
    # Initialize array of rates
    rate_A = [np.nan,np.nan,np.nan,np.nan,np.nan]
    rate_B = [np.nan,np.nan,np.nan,np.nan,np.nan]
    # Initialize array of offsets
    off_A = [np.nan,np.nan,np.nan,np.nan,np.nan]
    off_B = [np.nan,np.nan,np.nan,np.nan,np.nan]
    # Initialize array of charges
    charge_A = [np.nan,np.nan,np.nan,np.nan,np.nan]
    charge_B = [np.nan,np.nan,np.nan,np.nan,np.nan]
    # Initialize array of 2nd calib factors
    factor_A = [np.nan,np.nan,np.nan,np.nan,np.nan]
    factor_B = [np.nan,np.nan,np.nan,np.nan,np.nan]
    # Fill the relevant entries
    for i in range(1,5):
        # Read offset data for offset correction and charge and make empty list in rates
        if str(i) in telcombi:
            print ("Read offsets for telescope {}".format(i))
            off_A[i] = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(i) )[0]
            off_B[i] = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(i) )[1]
            charge_A[i] = (np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/calib.calib".format(i) )[10]) #*(-1)
            charge_B[i] = (np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/calib.calib".format(i) )[11]) #*(-1)
            factor_A[i] = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/calib.calib".format(i) )[12]
            factor_B[i] = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/calib.calib".format(i) )[13]
            rate_A[i] = []
            rate_B[i] = []

    # Loop over every file
    for i in tqdm(range ( 0,len(files) )):
        file = files[i]
        # Read in the header information
        data = np.loadtxt("{}/{}/{}_{:05d}.header".format(folderpath, folder, star, i))
        time = datetime.utcfromtimestamp(data[0]); times.append( ephem.Date(time) )
        t = str(times[-1]) 
        tplot.append(t.split(' ')[1])   # get h:min:sec
        mean_A = [np.nan, data[1], data[3], data[5], data[7]] # Array of waveform means of each telescope chA (unused telescopes have "nan" entries)
        mean_B = [np.nan, data[2], data[4], data[6], data[8]] # Array of waveform means of each telescope chB (unused telescopes have "nan" entries)

        # Get file parameters from header and ephem calculations ---- we only need alt
        if star == "Regor":
            tdiff, bl, az, alt = geo3T.get_params_manual3T(time, ra=[8,10,12.5], dec=[-47,24,22.2], telcombi=[1,4])
        elif star == "Etacen":
            tdiff, bl, az, alt = geo3T.get_params_manual3T(time, ra=[14,35,30.42], dec=[-42,9,28.17], telcombi=[1,4])
        elif star == "Dschubba":
            tdiff, bl, az, alt = geo3T.get_params_manual3T(time, ra=[16,0,20], dec=[-22,37,18.14], telcombi=[1,4])
        else:
            tdiff, bl, az, alt = geo3T.get_params3T(time, starname=star, telcombi=[1,4])  # doesn't matter which telcombi, since we only need alt for rates

        alt_all.append(alt)
        p_time = []; p_alt = []
        
        # Calculate rate for each channel 
        for j in range(1,5):
            if str(j) in telcombi:
                #print (f"Calculate rate for telescope {j}")
                rateA = factor_A[j]* ((mean_A[j] - off_A[j]) * 1e-9)/ (charge_A[j] * 1.6e-9)  # 1e-9 fuer GHz (durch e9 teilen) und 1.6e-9 fuer 1.6ns bins bei peakshape
                rateB = factor_A[j]* ((mean_B[j] - off_B[j]) * 1e-9)/ (charge_B[j] * 1.6e-9) 
                rate_A[j].append( rateA)
                rate_B[j].append( rateB)
                #print(rateA)
                #print(rate_A)
                p1, = ax1.plot(tplot[-1], rateA, color=colors[j], alpha=0.6, marker='.', label=f"Tel {j}")
                ax2.plot(tplot[-1], rateB, color=colors[j], alpha=0.6, marker='.', label=f"Tel {j}")
                if p1 not in p_time:
                    p_time.append(p1)
                p3, = ax3.plot(alt, rateA, color=colors[j], alpha=0.6, marker='.', label=f'Tel {j}')
                ax4.plot(alt, rateB, color=colors[j], alpha=0.6, marker='.', label=f'Tel {j}')
                if p3 not in p_alt:
                    p_alt.append(p3)

       
        ## rate ratios between the telescopes
        #rateA_ratio.append(rate3A / rate4A)
        #rateB_ratio.append(rate3B / rate4B)

        ## rate ratio between two neighboring files
        #if len(rate3A_all) >=2 :
        #   ratio_ratesA.append(rate3A / rate3A_all[-2])
        #   ratio_ratesB.append(rate3B / rate3B_all[-2])

        
    # Plotting rates vs time
    ax1.set_xticks(tplot[::1000])
    ax1.set_xticklabels(tplot[::1000], rotation=45, fontsize=13)
    ax1.tick_params(labelsize=13)
    ax1.legend(handles=[*p_time], fontsize=13)
    ax2.set_xticks(tplot[::1000])
    ax2.set_xticklabels(tplot[::1000], rotation=45, fontsize=13)
    ax2.legend(handles=[*p_time], fontsize=13)
    ax2.tick_params(labelsize=13)
    fig1.savefig(f"rates/{star}/{folder}/rates_time.png")
    
    # Plotting rates vs altitude
    ax3.tick_params(labelsize=13)
    ax3.legend(handles=[*p_alt], fontsize=13)
    ax4.legend(handles=[*p_alt], fontsize=13)
    ax4.tick_params(labelsize=13)
    fig2.savefig(f"rates/{star}/{folder}/rates_alt.png")

    plt.show()
      
    #print(times[0])
    ## creating x axis for altitude plot
    #minval = min(alt_all)
    #maxval = max(alt_all)
    #minval = math.floor(minval)
    #maxval = math.ceil(maxval)
    #if maxval-minval <= 1:
    #    xplot = np.arange(minval, maxval, 0.5)
    #else:
    #    xplot = np.arange(minval, maxval, 5)
    #alt_all = np.array(alt_all)
    # fitting cos to rate vs altitude
    #def func(x, a, f, c):
    #    return a * np.sin(f*x) + c
    #p0 = [400, 1/20, 200]
    #popt3A, pcov3A = curve_fit(func, alt_all, rate3A_all, p0=p0)
    #popt3B, pcov3B = curve_fit(func, alt_all, rate3B_all, p0=p0)
    #popt4A, pcov4A = curve_fit(func, alt_all, rate4A_all, p0=p0)
    #popt4B, pcov4B = curve_fit(func, alt_all, rate4B_all, p0=p0)

    
    #Figure3 = plt.figure(figsize=(17,12))
    #plt.plot(tplot, rateA_ratio, linestyle='-', label='Ratio {}A/{}A'.format(telcombi[0], telcombi[1]))
    #plt.plot(tplot, rateB_ratio, linestyle='-', label="Ratio {}B/{}B".format(telcombi[0], telcombi[1]))
    #plt.legend(fontsize=13)
    #plt.xlabel("Time (UTC)", fontsize=14)
    #plt.xticks(tplot[::1000],rotation=45, fontsize=13)
    #plt.yticks(fontsize=13)
    #plt.ylabel("Ratio", fontsize=14)
    #plt.title("Ratio of rates of {}".format(star), fontsize=17)
    #plt.tight_layout()
    #plt.savefig("rates/{}/{}_{}_ratio.pdf".format(star,star,date))

    #Figure5 = plt.figure(figsize=(17,12))
    #plt.plot(tplot[0:-1], ratio_ratesA, label='Ratio {}A files'.format(telcombi[0]), marker='o', color='blue')
    #plt.plot(tplot[0:-1], ratio_ratesB, label="Ratio {}B files".format(telcombi[0]), marker='o', color='orange')
    #plt.legend(fontsize=13)
    #plt.xlabel("Time (UTC)", fontsize=14)
    #plt.xticks(tplot[::1000],rotation=45, fontsize=13)
    #plt.yticks(fontsize=13)
    #plt.ylabel("Ratio", fontsize=14)
    #plt.title("Ratio of rates of {}".format(star), fontsize=17)
    #plt.tight_layout()
    #plt.savefig("rates/{}/{}_{}_rate_ratio_file.pdf".format(star,star,date))
    #plt.show()
    
##########################################
# Add the number of files to be analyzed #
start = 0
#end = 200
for i in range(len(folders)): #(0,1): 
    folder   = folders[i]
    date = folder[0:8]
    #stepsize = stepsizes[i]
    end      = ends[i]
    telcombi = telcombis[i]
    #steps = np.arange(0, end + 1, stepsize)
    #for j in range(len(steps)-1):
    #    start = steps[j]
    #    stop = steps[j+1]
    #    corr_parts(folder, start, stop)
    rate_calc(folder, start, end, telcombi)