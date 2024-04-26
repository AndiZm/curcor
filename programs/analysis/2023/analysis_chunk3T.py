import numpy as np
from tqdm import tqdm
from datetime import datetime
import ephem
import sys
import os

import geometry_3T as geo3T
import corrections as cor

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
# g2 functions for each telescope combination
g2_A = np.zeros((5,5), dtype=object)
g2_B = np.zeros((5,5), dtype=object) 
# Baselines and uncertainties for each telescope combination
baselines  = np.zeros((5,5), dtype=object)
dbaselines = np.zeros((5,5), dtype=object)
# Acquisition times
ac_times = np.zeros((5,5), dtype=object)
# Every index is an empty list at the beginning
for i in range(5):
    for j in range(5):
        g2_A[i,j] = []
        g2_B[i,j] = []
        baselines[i,j] = []
        dbaselines[i,j] = []
        ac_times[i,j] = []
# -------------------------------------------------- #


# Number of datapoints
N = 2 * 1024**3        # 2G sample file
#folderpath = "D:/results_HESS"
folderpath = "C:/Users/ii/Documents/curcor/corr_results/results_HESS"

def corr_parts(folder, start, stop, telcombi):
    print ("\n")
    # Define the filetype based on the telcombi. Historically, measurements with two telescopes have the filetype "fcorr6", while measurements with 3 telescopes have "fcorr3T"
    if len(telcombi) == 2:
        filetype = "fcorr6"
    elif len(telcombi) == 3:
        filetype = "fcorr3T"
    else:
        print ("Arrrgh! The filetype for your telcombi does not exist!")
        exit(0)

    # Initialize g2 functions for channel A and B which will be filled in for loop
    # We create a matrix of g2 functions for each telescope combination. To access a combination, e.g. 13, do g2_sumA[1,3]
    # To avoid having CT1 as entry 0, the array will be 5 elements x 5 elements, with the 0th row and column remain empty
    g2_sum_A = np.zeros((5,5), dtype=object); g2_sum_A[:] = np.nan
    g2_sum_B = np.zeros((5,5), dtype=object); g2_sum_B[:] = np.nan 
    # Initialize array of offsets
    off_A = [np.nan,np.nan,np.nan,np.nan,np.nan]
    off_B = [np.nan,np.nan,np.nan,np.nan,np.nan]
    # Fill the relevant entries
    telpairs = [] # This will be a list of the existing telescope combinations. For "134" e.g. the list will be [[1,3],[1,4],[3,4]]
    for i in range(1,5):
        # Read offset data for offset correction
        if str(i) in telcombi:
            print ("Read offsets for telescope {}".format(i))
            off_A[i] = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(i) )[0]
            off_B[i] = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(i) )[1]
        # Now initialize the g2 functions of the participating telescope pairs
        for j in range (1,5):
            if j > i and str(i) in telcombi and str(j) in telcombi:
                print ("\tIntialize telescope combination {}-{}".format(i,j))
                telpairs.append([i,j])

                len_data = len( np.loadtxt("{}/{}/{}{}/{}_{:05d}.fcorrAB".format(folderpath, folder, i,j, star, start))[:,0] )
                g2_sum_A[i,j] = np.zeros(len_data)
                g2_sum_B[i,j] = np.zeros(len_data)


    times = [] # Will be filled with individual time stampes to find the central acquisition time for the chunk
    baseline_values = [] # TODO: wahrscheinlich aendern

    # Initialize baseline matrix
    baseline  = np.zeros((5,5), dtype=object)
    dbaseline = np.zeros((5,5), dtype=object) # for the uncertainties
    for k in range(0,5):
        for l in range(0,5):
            baseline[k,l]  = []
            dbaseline[k,l] = []

    # Loop over every file
    for i in tqdm(range ( start, stop )):
        # Read in the header information
        data = np.loadtxt("{}/{}/{}_{:05d}.header".format(folderpath, folder, star, i))
        time = datetime.utcfromtimestamp(data[0]); times.append( ephem.Date(time) )
        mean_A = [np.nan, data[1], data[3], data[5], data[7]] # Array of waveform means of each telescope chA (unused telescopes have "nan" entries)
        mean_B = [np.nan, data[2], data[4], data[6], data[8]] # Array of waveform means of each telescope chB (unused telescopes have "nan" entries)

        # Loop over every telescope pair
        for pair in telpairs:
            pairstring = str(pair[0]) + str(pair[1])
            file = "{}/{}/{}/{}_{:05d}.fcorrAB".format(folderpath, folder, pairstring, star_small, i)

            # Read in data
            crossA = np.loadtxt(file)[:,0] # crosscorrelation G2 chA
            crossB = np.loadtxt(file)[:,1] # crosscorrelation G2 chB

            # Apply offset correction ( for details see eq (7) in https://doi.org/10.1093/mnras/stab3058 )
            crossA -= N * ( mean_A[pair[0]]*off_A[pair[1]] + mean_A[pair[1]]*off_A[pair[0]] - off_A[pair[0]]*off_A[pair[1]] )
            crossB -= N * ( mean_B[pair[0]]*off_B[pair[1]] + mean_B[pair[1]]*off_B[pair[0]] - off_B[pair[0]]*off_B[pair[1]] )

            # Apply pattern correction
            crossA = cor.pattern_correction(crossA) # data already normalized
            crossB = cor.pattern_correction(crossB) # data already normalized
    
            # Get file parameters from header and ephem calculations
            if star == "Regor":
                tdiff, bl, az, alt = geo3T.get_params_manual3T(time, ra=[8,10,12.5], dec=[-47,24,22.2], telcombi=[pair[0],pair[1]])
            elif star == "Etacen":
                tdiff, bl, az, alt = geo3T.get_params_manual3T(time, ra=[14,35,30.42], dec=[-42,9,28.17], telcombi=[pair[0],pair[1]])
            elif star == "Dschubba":
                tdiff, bl, az, alt = geo3T.get_params_manual3T(time, ra=[16,0,20], dec=[-22,37,18.14], telcombi=[pair[0],pair[1]])
            else:
                tdiff, bl, az, alt = geo3T.get_params3T(time, starname=star, telcombi=[pair[0],pair[1]])

            # Store baseline
            baseline[pair[0],pair[1]].append(bl)
        
            # Apply optical path length correction for cross correlations
            binshift = timebin(tdiff)
            crossA = shift_bins(crossA, binshift)
            crossB = shift_bins(crossB, binshift)
        
            #-- Averaging of the g2 functions --#
            rms = np.std(crossA)
            g2_for_averaging = crossA/rms**2
            # Adding the new data to the total g2 function
            g2_sum_A[pair[0],pair[1]] += g2_for_averaging
            
            rms = np.std(crossB)
            g2_for_averaging = crossB/rms**2
            # Adding the new data to the total g2 function
            g2_sum_B[pair[0],pair[1]] += g2_for_averaging

    ##################################
    # Finish things up for the chunk #
    ##################################
    time_mean = np.mean(times)
    print ("Central time = {}".format(ephem.Date(time_mean)))

    # Re-normalize for proper g2 function: nanmean takes into account that there may be nan entries
    for i in range(5):
        for j in range(5):
            g2_sum_A[i,j] /= np.nanmean(g2_sum_A[i,j])
            g2_sum_B[i,j] /= np.nanmean(g2_sum_B[i,j])
    
    # Calculate mean baseline and baseline error
    for i in range(5):
        for j in range(5):
            dbaseline[i,j] = np.nanstd(baseline[i,j])  # first the error, bc the baseline array will be changed in the next line
            baseline[i,j]  = np.nanmean(baseline[i,j]) # this transfers the array of lists into a simple array with the mean baseline

    #print ("Baselines:"); print (baseline)
    #print ("Baseline errors:"); print (dbaseline)

    # save data into correct arrays
    for pair in telpairs:
        # append the g2 arrays to the matrix of telescope g2 lists
        g2_A[pair[0],pair[1]].append(g2_sum_A[pair[0],pair[1]])
        g2_B[pair[0],pair[1]].append(g2_sum_B[pair[0],pair[1]])
        # append baselines and uncertainties to the matrix of telescope baseline lists
        baselines[pair[0],pair[1]].append(baseline[pair[0],pair[1]])
        dbaselines[pair[0],pair[1]].append(dbaseline[pair[0],pair[1]])
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
os.makedirs("g2_functions/{}".format(star), exist_ok=True)

for i in range(5):
    for j in range(5):
        if len( ac_times[i,j] ) > 0: # this combination exists
            # create combination folder, if not already existing
            os.makedirs("g2_functions/{}/{}{}".format(star,i,j), exist_ok=True)
            # save all the data
            np.savetxt("g2_functions/{}/{}{}/ac_times.txt".format(star,i,j), np.c_[ ac_times[i,j] ])
            np.savetxt("g2_functions/{}/{}{}/baselines.txt".format(star,i,j), np.c_[ baselines[i,j] ])
            np.savetxt("g2_functions/{}/{}{}/dbaselines.txt".format(star,i,j), np.c_[ dbaselines[i,j] ])
            np.savetxt("g2_functions/{}/{}{}/chA.g2".format(star,i,j), np.c_[ g2_A[i,j] ])
            np.savetxt("g2_functions/{}/{}{}/chB.g2".format(star,i,j), np.c_[ g2_B[i,j] ])