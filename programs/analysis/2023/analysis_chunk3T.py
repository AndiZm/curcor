import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from matplotlib.pyplot import cm
import matplotlib as mpl
from tqdm import tqdm
from datetime import datetime, timezone
import ephem
import sys

import geometry as geo
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

# Initialize parameter arrays for data storing
g2_3s = []
g2_4s = []
g2_As_14 = []; g2_As_34 = []
g2_Bs_14 = []; g2_Bs_34 = []
#g2_3Ax4Bs = []
#g2_4Ax3Bs = []
baselines14 = []; dbaselines14 = []; baselines34 =[]; dbaselines34 =[]
time_means14 = []; time_means34 = []

# Number of datapoints
N = 2 * 1024**3        # 2G sample file
#folderpath = "D:/results_HESS"
folderpath = "C:/Users/ii/Documents/curcor/corr_results/results_HESS"

def corr_parts(folder, start, stop, telcombi):
    # Define the filetype based on the telcombi. Historically, measurements with two telescopes have the filetype "fcorr6", while measurements with 3 telescopes have "fcorr3T"
    if len(telcombi) == 2:
        filetype = "fcorr6"
    elif len(telcombi) == 3:
        filetype = "fcorr3T"
    elif:
        print ("Arrrgh! The filetype for your telcombi does not exist!")
        exit(0)

    # Define files to be analized for a single g2 function
    files = []
    for i in range (start, stop): 
        files.append("{}/{}/size10000/{}_{:05d}.{}".format(folderpath, folder, star_small, i, filetype))

    # Initialize g2 functions for channel A and B which will be filled in for loop
    len_data = len( np.loadtxt(files[0])[:,2] )

    # We creat a matrix of g2 functions for each telescope combination. To access a combination, e.g. 13, do g2_sumA[1,3]
    # To avoid having CT1 as entry 0, the array will be 5 elements x 5 elements, with the 0th row and column remain empty
    g2_sum_A = np.array(5,5, dtype=object)
    g2_sum_B = np.array(5,5, dtype=object)
   
    # Initialize array of offsets
    off_A = [0,0,0,0,0]
    off_B = [0,0,0,0,0]
    # Fill the relevant entries
    for i in range(1,5):
        # Read offset data for offset correction
        if str(i) in telcombi:
            off_A[i]
            hier weiter
        for j in range (1,5):
            if j > i and str(i) in telcombi and str(j) in telcombi:
                g2_sum_A[i,j] = np.zeros(len_data)
                g2_sum_B[i,j] = np.zeros(len_data)


    times = []; baseline_values = [] # TODO: aendern


    off3A = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[0]) )[0]
    off3B = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[0]) )[1]
    off4A = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[1]) )[0]
    off4B = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[1]) )[1]

    # Loop over every file
    for i in tqdm(range ( 0,len(files) )):
        file = files[i]

        # Read in data
        #auto3  = np.loadtxt(file)[:,0] # G2 of CT3 A x CT3 B (autocorrelations)
        #auto4  = np.loadtxt(file)[:,1] # G2 of CT4 A x CT4 B (autocorrelations)
        crossA = np.loadtxt(file)[:,2] # G2 of CT3 A x CT4 A (crosscorrelations)
        crossB = np.loadtxt(file)[:,3] # G2 of CT3 B x CT4 B (crosscorrelations)

        # Read mean waveform values
        f = open(file)
        line_params = f.readline()[:-1].split(" ") # Read header of fcorr file
        mean3A = float(line_params[2])
        mean3B = float(line_params[3])
        mean4A = float(line_params[4])
        mean4B = float(line_params[5])

        # Apply offset correction
        #auto3  -= N * ( mean3A*off3B + mean3B*off3A - off3A*off3B ) # Only CT 3 both channels
        #auto4  -= N * ( mean4A*off4B + mean4B*off4A - off4A*off4B ) # Only CT 4 both channels        
        crossA -= N * ( mean3A*off4A + mean4A*off3A - off3A*off4A ) # Only CH A, but CT3 and CT4
        crossB -= N * ( mean3B*off4B + mean4B*off3B - off3B*off4B ) # Only CH B, but CT3 and CT4

        # Apply pattern correction
        #auto3  = cor.pattern_correction(auto3) # data already normalized
        #auto4  = cor.pattern_correction(auto4) # data already normalized
        crossA = cor.pattern_correction(crossA) # data already normalized
        crossB = cor.pattern_correction(crossB) # data already normalized
    
        # Get file parameters from header and ephem calculations
        if star == "Regor":
            tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params_manual(file, ra=[8,10,12.5], dec=[-47,24,22.2], telcombi=telcombi)
        elif star == "Etacen":
            tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params_manual(file, ra=[14,35,30.42], dec=[-42,9,28.17], telcombi=telcombi)
        elif star == "Dschubba":
            tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params_manual(file, ra=[16,0,20], dec=[-22,37,18.14], telcombi=telcombi)
        else:
            tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params(file, starname=star, telcombi=telcombi)
        # Store acquisition times and corresponding baselines for sc plot
        times.append(ephem.Date(time))
        baseline_values.append(uti.get_baseline(date=time, star=star)[get_baseline_entry(telcombi=telcombi)])

        # Apply optical path length correction for cross correlations
        binshift = timebin(tdiff)
        crossA = shift_bins(crossA, binshift)
        crossB = shift_bins(crossB, binshift)
        
        #################################
        # Averaging of the g2 functions #
        #################################
        #--  Autocorrelations --#
        #rms = np.std(auto3[0:4500])
        #g2_for_averaging = auto3/rms**2
        ## Adding the new data to the total g2 function
        #g2_sum_3 += g2_for_averaging

        #rms = np.std(auto4[0:4500])
        #g2_for_averaging = auto4/rms**2
        ## Adding the new data to the total g2 function
        #g2_sum_4 += g2_for_averaging


        #-- Crosscorrelations --#
        rms = np.std(crossA)
        g2_for_averaging = crossA/rms**2
        # Adding the new data to the total g2 function
        g2_sum_A += g2_for_averaging
    
        rms = np.std(crossB)
        g2_for_averaging = crossB/rms**2
        # Adding the new data to the total g2 function
        g2_sum_B += g2_for_averaging


    # Re-normalize for proper g2 function
    #g2_sum_3 = g2_sum_3/np.mean(g2_sum_3)
    #g2_sum_4 = g2_sum_4/np.mean(g2_sum_4)
    g2_sum_A = g2_sum_A/np.mean(g2_sum_A)
    g2_sum_B = g2_sum_B/np.mean(g2_sum_B)

    time_mean = np.mean(times)
    # Calculate mean baseline and baseline error
    baseline  = np.mean(baseline_values)
    dbaseline = np.std(baseline_values)
    print ("Telescope combination =  {}".format(telcombi))
    print ("Baseline =  {:.1f} +/- {:.1f}  m".format(baseline, dbaseline))
    print ("Central time = {}".format(ephem.Date(time_mean)))

    # save data into correct tel combi folders
    if telcombi == '14':
        # Save the data of this correlation to the arrays
        #g2_3s.append(g2_sum_3)
        #g2_4s.append(g2_sum_4)
        g2_As_14.append(g2_sum_A)
        g2_Bs_14.append(g2_sum_B)
        baselines14.append(baseline)
        dbaselines14.append(dbaseline)
        time_means14.append(time_mean) 
        print('DONE 14')

    elif telcombi == '34':
        # Save the data of this correlation to the arrays
        #g2_3s.append(g2_sum_3)
        #g2_4s.append(g2_sum_4)
        g2_As_34.append(g2_sum_A)
        g2_Bs_34.append(g2_sum_B)
        baselines34.append(baseline)
        dbaselines34.append(dbaseline)
        time_means34.append(time_mean) 
        print('DONE 34')

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
    print(len(baselines14))

#np.savetxt("g2_functions/weight_rms_squared/{}/{}/CT3.txt".format(star,telcombi), np.c_[g2_3s], header="{} CT3".format(star))
#np.savetxt("g2_functions/weight_rms_squared/{}/{}/CT4.txt".format(star,telcombi), np.c_[g2_4s], header="{} CT4".format(star))
np.savetxt("g2_functions/weight_rms_squared/{}/{}/ChA.txt".format(star,telcombis[0]), np.c_[g2_As_14], header="{} Channel A".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/{}/ChB.txt".format(star,telcombis[0]), np.c_[g2_Bs_14], header="{} Channel B".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/{}/baseline.txt".format(star,telcombis[0]), np.c_[time_means14, baselines14, dbaselines14], header="14: Time, baseline, baseline error" )
np.savetxt("g2_functions/weight_rms_squared/{}/{}/ChA.txt".format(star,telcombis[1]), np.c_[g2_As_34], header="{} Channel A".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/{}/ChB.txt".format(star,telcombis[1]), np.c_[g2_Bs_34], header="{} Channel B".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/{}/baseline.txt".format(star,telcombis[1]), np.c_[time_means34, baselines34, dbaselines34], header="34: Time, baseline, baseline error" )