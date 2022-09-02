import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from matplotlib.pyplot import cm
import matplotlib as mpl
from tqdm import tqdm
from datetime import datetime, timezone
import ephem

import geometry as geo
import corrections as cor
import utilities as uti

from threading import Thread

star = "Nunki"

# Define files to analyze and subpackages
folders   = [] # Data folders for analysis
stepsizes = [] # Number of files for a single g2 function
ends      = [] # Total number of files used from this folder

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

# Initialize parameter arrays for data storing
g2_3s = []
g2_4s = []
g2_As = []
g2_Bs = []
g2_3Ax4Bs = []
g2_4Ax3Bs = []
baselines = []; dbaselines = []
time_means = []

# Number of datapoints
N = 2 * 1024**3        # 2G sample file
folderpath = "C:/Users/ii/Documents/curcor/corr_results/results_HESS"

def corr_parts(folder, start, stop):
    # Define files to be analized for a single g2 function
    files = []
    for i in range (start, stop): 
        files.append("{}/{}/size10000/{}_{:05d}.fcorr6".format(folderpath, folder, star_small, i))

    # Initialize g2 functions for channel A and B which will be filled in for loop
    len_data = len( np.loadtxt(files[0])[:,2] )
    g2_sum_A = np.zeros(len_data)
    g2_sum_B = np.zeros(len_data)
    g2_sum_3 = np.zeros(len_data)
    g2_sum_4 = np.zeros(len_data)
    g2_sum_3Ax4B = np.zeros(len_data)
    g2_sum_4Ax3B = np.zeros(len_data)
    times = []; baseline_values = []

    # Read offset data for offset correction
    off3A = np.loadtxt( folderpath + "/" + folder + "/calibs_ct3/off.off" )[0]
    off3B = np.loadtxt( folderpath + "/" + folder + "/calibs_ct3/off.off" )[1]
    off4A = np.loadtxt( folderpath + "/" + folder + "/calibs_ct4/off.off" )[0]
    off4B = np.loadtxt( folderpath + "/" + folder + "/calibs_ct4/off.off" )[1]

    # Loop over every file
    for i in tqdm(range ( 0,len(files) )):
        file = files[i]

        # Read in data
        auto3  = np.loadtxt(file)[:,0] # G2 of CT3 A x CT3 B (autocorrelations)
        auto4  = np.loadtxt(file)[:,1] # G2 of CT4 A x CT4 B (autocorrelations)
        crossA = np.loadtxt(file)[:,2] # G2 of CT3 A x CT4 A (crosscorrelations)
        crossB = np.loadtxt(file)[:,3] # G2 of CT3 B x CT4 B (crosscorrelations)
        c3Ax4B = np.loadtxt(file)[:,4] # G2 of CT3 A x CT4 B (crosscorrelations)
        c4Ax3B = np.loadtxt(file)[:,5] # G2 of CT4 A x CT3 B (crosscorrelations)

        # Read mean waveform values
        f = open(file)
        line_params = f.readline()[:-1].split(" ") # Read header of fcorr file
        mean3A = float(line_params[2])
        mean3B = float(line_params[3])
        mean4A = float(line_params[4])
        mean4B = float(line_params[5])

        # Apply offset correction
        auto3  -= N * ( mean3A*off3B + mean3B*off3A - off3A*off3B ) # Only CT 3 both channels
        auto4  -= N * ( mean4A*off4B + mean4B*off4A - off4A*off4B ) # Only CT 4 both channels        
        crossA -= N * ( mean3A*off4A + mean4A*off3A - off3A*off4A ) # Only CH A, but CT3 and CT4
        crossB -= N * ( mean3B*off4B + mean4B*off3B - off3B*off4B ) # Only CH B, but CT3 and CT4
        c3Ax4B -= N * ( mean3A*off4B + mean4B*off3A - off3A*off4B ) # CT3 A X CT4 B
        c4Ax3B -= N * ( mean4A*off3B + mean3B*off4A - off4A*off3B ) # CT4 A X CT3 B

        # Apply pattern correction
        auto3  = cor.pattern_correction(auto3) # data already normalized
        auto4  = cor.pattern_correction(auto4) # data already normalized
        crossA = cor.pattern_correction(crossA) # data already normalized
        crossB = cor.pattern_correction(crossB) # data already normalized
        c3Ax4B = cor.pattern_correction(c3Ax4B) # data already normalized
        c4Ax3B = cor.pattern_correction(c4Ax3B) # data already normalized
    
        # Get file parameters from header and ephem calculations
        tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params(file, starname=star)

        # Store acquisition times and corresponding baselines for sc plot
        times.append(ephem.Date(time))
        baseline_values.append(uti.get_baseline(date=time, star=star))

        # Apply optical path length correction for cross correlations
        binshift = timebin(tdiff)
        crossA = shift_bins(crossA, binshift)
        crossB = shift_bins(crossB, binshift)
        c3Ax4B = shift_bins(c3Ax4B, binshift)
        c4Ax3B = shift_bins(c4Ax3B, -1*binshift) # negative binshift since CT4 is mentioned first
        #c4Ax3B = shift_bins(c4Ax3B, binshift) # for testing
    
        #################################
        # Averaging of the g2 functions #
        #################################
        #--  Autocorrelations --#
        rms = np.std(auto3[0:4500])
        g2_for_averaging = auto3/rms
        # Adding the new data to the total g2 function
        g2_sum_3 += g2_for_averaging

        rms = np.std(auto4[0:4500])
        g2_for_averaging = auto4/rms
        # Adding the new data to the total g2 function
        g2_sum_4 += g2_for_averaging


        #-- Crosscorrelations --#
        rms = np.std(crossA)
        g2_for_averaging = crossA/rms
        # Adding the new data to the total g2 function
        g2_sum_A += g2_for_averaging
    
        rms = np.std(crossB)
        g2_for_averaging = crossB/rms
        # Adding the new data to the total g2 function
        g2_sum_B += g2_for_averaging

        rms = np.std(c3Ax4B)
        g2_for_averaging = c3Ax4B/rms
        # Adding the new data to the total g2 function
        g2_sum_3Ax4B += g2_for_averaging

        rms = np.std(c4Ax3B)
        g2_for_averaging = c4Ax3B/rms
        # Adding the new data to the total g2 function
        g2_sum_4Ax3B += g2_for_averaging

    time_mean = np.mean(times)
    # Calculate mean baseline and baseline error
    baseline  = np.mean(baseline_values)
    dbaseline = np.std(baseline_values)
    print ("Baseline =  {:.1f} +/- {:.1f}  m".format(baseline, dbaseline))
    print ("Central time = {}".format(ephem.Date(time_mean)))
    
    # Re-normalize for proper g2 function
    g2_sum_3 = g2_sum_3/np.mean(g2_sum_3)
    g2_sum_4 = g2_sum_4/np.mean(g2_sum_4)
    g2_sum_A = g2_sum_A/np.mean(g2_sum_A)
    g2_sum_B = g2_sum_B/np.mean(g2_sum_B)
    g2_sum_3Ax4B = g2_sum_3Ax4B/np.mean(g2_sum_3Ax4B)
    g2_sum_4Ax3B = g2_sum_4Ax3B/np.mean(g2_sum_4Ax3B)

    # Save the data of this correlation to the arrays
    g2_3s.append(g2_sum_3)
    g2_4s.append(g2_sum_4)
    g2_As.append(g2_sum_A)
    g2_Bs.append(g2_sum_B)
    g2_3Ax4Bs.append(g2_sum_3Ax4B)
    g2_4Ax3Bs.append(g2_sum_4Ax3B)
    baselines.append(baseline)
    dbaselines.append(dbaseline)
    time_means.append(time_mean)  

##########################################
# Add the number of files to be analyzed #
for i in range(len(folders)):
    folder   = folders[i]
    stepsize = stepsizes[i]
    end      = ends[i]
    steps = np.arange(0, end + 1, stepsize)
    for j in range(len(steps)-1):
        start = steps[j]
        stop = steps[j+1]
        corr_parts(folder, start, stop)

np.savetxt("g2_functions/{}/CT3.txt".format(star), np.c_[g2_3s], header="{} CT3".format(star))
np.savetxt("g2_functions/{}/CT4.txt".format(star), np.c_[g2_4s], header="{} CT4".format(star))
np.savetxt("g2_functions/{}/ChA.txt".format(star), np.c_[g2_As], header="{} Channel A".format(star) )
np.savetxt("g2_functions/{}/ChB.txt".format(star), np.c_[g2_Bs], header="{} Channel B".format(star) )
np.savetxt("g2_functions/{}/c3Ax4B.txt".format(star), np.c_[g2_3Ax4Bs], header="{} CT3 A x CT4 B".format(star) )
np.savetxt("g2_functions/{}/c4Ax3B.txt".format(star), np.c_[g2_4Ax3Bs], header="{} CT4 A x CT3 B".format(star) )
np.savetxt("g2_functions/{}/baseline.txt".format(star), np.c_[time_means, baselines, dbaselines], header="Time, baseline, baseline error" )