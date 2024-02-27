import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from matplotlib.pyplot import cm
import matplotlib as mpl
from tqdm import tqdm
from datetime import datetime, timezone
import ephem
import sys
import os

import geometry as geo
import geometry_3T as geo3T
import corrections as cor
import utilities as uti

from threading import Thread

star = sys.argv[1]

# Define files to analyze and subpackages
folders   = [] # Data folders for analysis
stepsizes = [] # Number of files for a single g2 function
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
    stepsizes.append( int(line.split()[1]) )
    ends.append( int(line.split()[2]) )
    telcombis.append( str(line.split()[3]) )
    line = f.readline()
f.close()

print ("Analyzing {}".format(star))

star_small = star[0].lower() + star[1:]
# Get the timebin shift of the specific measurement from the time difference
def timebin(tdiff):
    return int(1.0* np.floor((tdiff+0.8)/1.6))
def shift_bins(data, binshift):
    # A negative number means shifting to the right, so scrapping the right end of the array to the beginning
    if binshift <= 0:
        for j in range (binshift,0):
            data = np.insert(data,0,data[-1])
            data = np.delete(data, -1)
    # A positive number means shifting to the left, so scrapping the beginning of the array to the end
    if binshift > 0:
        for j in range (0, binshift):
            data = np.append(data,data[0])
            data = np.delete(data, 0)
    return data
def get_baseline_entry(telcombi):
    if telcombi == "13":
        return int(0)
    elif telcombi == "14":
        return int(1)
    elif telcombi == "34":
        return int(2)

# -------------------------------------------------- #
# -- Initialize parameter arrays for data storing -- #
# Baselines and uncertainties for each telescope combination
baselines  = np.zeros((5,5), dtype=object)
dbaselines = np.zeros((5,5), dtype=object)

baselines3T  = np.zeros((5,5), dtype=object)
dbaselines3T = np.zeros((5,5), dtype=object)
# Acquisition times
ac_times = np.zeros((5,5), dtype=object)
# Every index is an empty list at the beginning
for i in range(5):
    for j in range(5):
        baselines[i,j] = []
        baselines3T[i,j] = []
        dbaselines[i,j] = []
        dbaselines3T[i,j] = []
        ac_times[i,j] = []
# -------------------------------------------------- #


# Number of datapoints
N = 2 * 1024**3 # 2G sample file
folderpath = "C:/Users/ii/Documents/curcor/corr_results/results_HESS"

def corr_parts(folder, start, stop, telcombi):
    # Define the filetype based on the telcombi. Historically, measurements with two telescopes have the filetype "fcorr6", while measurements with 3 telescopes have "fcorr3T"
    if len(telcombi) == 2:
        filetype = "fcorr6"
    elif len(telcombi) == 3:
        filetype = "fcorr3T"
    else:
        print ("Arrrgh! The filetype for your telcombi does not exist!")
        exit(0)

    # Fill the relevant entries
    telpairs = [] # This will be a list of the existing telescope combinations. For "134" e.g. the list will be [[1,3],[1,4],[3,4]]
    for i in range(1,5):
        # Now initialize the g2 functions of the participating telescope pairs
        for j in range (1,5):
            if j > i and str(i) in telcombi and str(j) in telcombi:
                print ("\tIntialize telescope combination {}-{}".format(i,j))
                telpairs.append([i,j])

    times = [] # Will be filled with individual time stampes to find the central acquisition time for the chunk

    # Initialize baseline matrix
    baseline  = np.zeros((5,5), dtype=object)
    dbaseline = np.zeros((5,5), dtype=object) # for the uncertainties
    baseline3T  = np.zeros((5,5), dtype=object)
    dbaseline3T = np.zeros((5,5), dtype=object) # for the uncertainties
    for k in range(0,5):
        for l in range(0,5):
            baseline[k,l]  = []
            baseline3T[k,l]  = []
            dbaseline[k,l] = []
            dbaseline3T[k,l] = []

    # Loop over every file
    #del# for i in tqdm(range ( 0,len(files) )):
    for i in tqdm(range ( start, stop )):
        # Read in the header information
        data = np.loadtxt("{}/{}/{}_{:05d}.header".format(folderpath, folder, star, i))
        time = datetime.utcfromtimestamp(data[0]); times.append( ephem.Date(time) )

        # Loop over every telescope pair
        for pair in telpairs:
            pairstring = str(pair[0]) + str(pair[1])
    
            # Get file parameters from header and ephem calculations
            if star == "Regor":
                tdiff, bl3T, az, alt = geo3T.get_params_manual3T(time, ra=[8,10,12.5], dec=[-47,24,22.2], telcombi=[pair[0],pair[1]])
            elif star == "Etacen":
                tdiff, bl3T, az, alt = geo3T.get_params_manual3T(time, ra=[14,35,30.42], dec=[-42,9,28.17], telcombi=[pair[0],pair[1]])
            elif star == "Dschubba":
                tdiff, bl3T, az, alt = geo3T.get_params_manual3T(time, ra=[16,0,20], dec=[-22,37,18.14], telcombi=[pair[0],pair[1]])
            else:
                tdiff, bl3T, az, alt = geo3T.get_params3T(time, starname=star, telcombi=[pair[0],pair[1]])

            # Store baseline
            baseline[pair[0],pair[1]].append( uti.get_baseline3T(date=time, star=star, telcombi=pairstring) )
            baseline3T[pair[0],pair[1]].append( bl3T )
        

    ##################################
    # Finish things up for the chunk #
    ##################################
    time_mean = np.mean(times)
    print ("Central time = {}".format(ephem.Date(time_mean)))
    
    # Calculate mean baseline and baseline error
    for i in range(5):
        for j in range(5):
            dbaseline[i,j] = np.nanstd(baseline[i,j])  # first the error, bc the baseline array will be changed in the next line
            baseline[i,j]  = np.nanmean(baseline[i,j]) # this transfers the array of lists into a simple array with the mean baseline

            dbaseline3T[i,j] = np.nanstd(baseline3T[i,j])  # first the error, bc the baseline array will be changed in the next line
            baseline3T[i,j]  = np.nanmean(baseline3T[i,j]) # this transfers the array of lists into a simple array with the mean baseline

    print ("Baselines:")
    print (baseline)
    print ("Baseline errors:")
    print (dbaseline)

    # save data into correct arrays
    for pair in telpairs:
        # append baselines and uncertainties to the matrix of telescope baseline lists
        baselines[pair[0],pair[1]].append(baseline[pair[0],pair[1]])
        baselines3T[pair[0],pair[1]].append(baseline3T[pair[0],pair[1]])
        dbaselines[pair[0],pair[1]].append(dbaseline[pair[0],pair[1]])
        dbaselines3T[pair[0],pair[1]].append(dbaseline3T[pair[0],pair[1]])
        # append acquisition times array. Even though they are the same for each combination in this chunk, there may be different runs with different telescope combinations
        ac_times[pair[0],pair[1]].append(time_mean)

##########################################
# Add the number of files to be analyzed #
for i in range(len(folders)):
    folder   = folders[i]
    stepsize = stepsizes[i]
    end      = ends[i]
    telcombi = telcombis[i]

    steps = np.arange(0, end + 1, stepsize)
    for j in range(len(steps)-1):
        start = steps[j]
        stop = steps[j+1]
        corr_parts(folder, start, stop, telcombi)



# Create folder for stars, if not already existing
os.makedirs("testing/g2_functions/{}".format(star), exist_ok=True)

for i in range(5):
    for j in range(5):
        if len( ac_times[i,j] ) > 0: # this combination exists
            # create combination folder, if not already existing
            os.makedirs("testing/g2_functions/{}/{}{}".format(star,i,j), exist_ok=True)
            # save all the data
            np.savetxt("testing/g2_functions/{}/{}{}/ac_times.txt".format(star,i,j), np.c_[ ac_times[i,j] ])
            np.savetxt("testing/g2_functions/{}/{}{}/baselines.txt".format(star,i,j), np.c_[ baselines[i,j] ])
            np.savetxt("testing/g2_functions/{}/{}{}/baselines3T.txt".format(star,i,j), np.c_[ baselines3T[i,j] ])
            np.savetxt("testing/g2_functions/{}/{}{}/dbaselines.txt".format(star,i,j), np.c_[ dbaselines[i,j] ])
            np.savetxt("testing/g2_functions/{}/{}{}/dbaselines3T.txt".format(star,i,j), np.c_[ dbaselines3T[i,j] ])