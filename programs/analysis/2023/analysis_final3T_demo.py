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

import utilities as uti
import corrections as cor
import geometry as geo

star = sys.argv[1]

combicolors = np.zeros((5,5), dtype=object); combicolors[:] = np.nan
combicolors[1,3] = "blue"
combicolors[1,4] = "fuchsia"
combicolors[3,4] = "green"

combicolors3T = np.zeros((5,5), dtype=object); combicolors3T[:] = np.nan
combicolors3T[1,3] = "#66ccff"
combicolors3T[1,4] = "#ffcccc"
combicolors3T[3,4] = "#ccff33"

################################################
#### Analysis over whole measurement time #####
################################################
    
##########################################
####### Chunk analysis ###################
##########################################

times = []
baselines_all = []; dbaselines_all = []
baselines3T_all = []; dbaselines3T_all = []
time_all = [] ; telstrings =[]

def chunk_ana(star, telcombi):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)

    chAs    = np.loadtxt("testing/g2_functions/{}/{}/baselines.txt".format(star, telstring))

    # Read the telescope data (acquisition times of chunks, baselines and baseline uncertainties)
    timestrings = np.loadtxt("testing/g2_functions/{}/{}/ac_times.txt".format(star,telstring))
    baselines   = np.loadtxt("testing/g2_functions/{}/{}/baselines.txt".format(star,telstring))
    baselines3T   = np.loadtxt("testing/g2_functions/{}/{}/baselines3T.txt".format(star,telstring))
    dbaselines  = np.loadtxt("testing/g2_functions/{}/{}/dbaselines.txt".format(star,telstring))
    dbaselines3T  = np.loadtxt("testing/g2_functions/{}/{}/dbaselines3T.txt".format(star,telstring))
    
    # loop over every g2 function chunk
    for i in range(0,len(chAs)):
        # Check acquisition time of original data
        timestring = ephem.Date(timestrings[i])
        tstring_short = str(timestring)[5:-3]

        baseline     = baselines[i]
        baseline3T   = baselines3T[i]
        dbaseline    = dbaselines[i]
        dbaseline3T  = dbaselines3T[i]
        baselines_all.append(baseline); dbaselines_all.append(dbaseline)
        baselines3T_all.append(baseline3T); dbaselines3T_all.append(dbaseline3T)

        time_all.append(timestring)
        telstrings.append(telstring)

    print("DONE Chunks {}".format(telcombi))


def plotting(star):
    plt.figure("baselines")
    plt.title("{}".format(star))
    plt.xlabel("Acquisition time")
    plt.ylabel("Telescope baseline (m)")

    sorted_indices = np.argsort(time_all)
    sorted_time = np.array(time_all)[sorted_indices]
    sorted_baselines = np.array(baselines_all)[sorted_indices]
    sorted_baselines3T = np.array(baselines3T_all)[sorted_indices]
    sorted_db = np.array(dbaselines_all)[sorted_indices]
    sorted_db3T = np.array(dbaselines3T_all)[sorted_indices]
    sorted_telstring = np.array(telstrings)[sorted_indices]

    for i in range(0,len(time_all)):
        # Check acquisition time of original data
        timestring = ephem.Date(sorted_time[i])
        t_short = str(timestring)[5:-3]
        baseline = sorted_baselines[i]
        baseline3T = sorted_baselines3T[i]
        dbaseline = sorted_db[i]
        dbaseline3T = sorted_db3T[i]
        telstr = sorted_telstring[i]
        col1, col2 = telstr.split()[0]
        c1 = int(col1)
        c2 = int(col2)

        # Draw "new night" lines into the plot, if there is a new night
        if i != 0:
            t1 = sorted_time[i-1]
            t2 = sorted_time[i]
            if np.floor(t2) - np.floor(t1) > 0:
                plt.axvline(t_short, color='darkgrey', label='new night')

        plt.errorbar(x=t_short, y=baseline, yerr=dbaseline, marker="o", linestyle="", label=telstr, color=combicolors[c1][c2])
        plt.errorbar(x=t_short, y=baseline3T, yerr=dbaseline3T, marker="^", linestyle="", label=telstr, color=combicolors3T[c1][c2])

        print (baseline, baseline3T)

        plt.xticks(rotation=45)

    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles)) 
    plt.legend(by_label.values(), by_label.keys()); plt.tight_layout()

    # legend 
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles)) 
    plt.legend(by_label.values(), by_label.keys())

# Loop over every potential telescope combination and check if it exists
telcombis = []
for c1 in range (1,5):
    for c2 in range(1,5):
        if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
            telcombis.append("{}{}".format(c1,c2))

#plt.figure("CrossCorr", figsize=(12,8))
for c1 in range (1,5):
    for c2 in range(1,5):
        if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
            telcombi = [c1,c2]
            print ("Found telescope combination {}".format(telcombi))
            chunk_ana(star, telcombi)
plotting(star)


plt.show()            