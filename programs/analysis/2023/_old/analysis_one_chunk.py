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

print ("Analyzing one chunk {}".format(star))

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
g2_As = []
g2_Bs = []
g2_As_clean = []
g2_Bs_clean = []
baselines = []; dbaselines = []
time_means = []
g2_ratio_A =[]

# Number of datapoints
N = 2 * 1024**3        # 2G sample file
folderpath = "D:/results_HESS"

def corr_parts(folder, start, stop, telcombi):
    # Initialize parameter arrays for data storing
    rate3A_all = []
    rate3B_all = []
    rate4A_all = []
    rate4B_all = []
    rateA_ratio =[]
    rateB_ratio =[]
    alt_all = []
    times = []; baseline_values = []; tplot =[]; realt =[]
    ratio_rates3A = [] ; number = 0
    # Define files to be analized for a single g2 function
    files = []
    for i in range (start, stop): 
        files.append("{}/{}/size10000/{}_{:05d}.fcorr6".format(folderpath, folder, star_small, i))
    print(files[0], files[-1])

    # Initialize g2 functions for channel A and B which will be filled in for loop
    len_data = len( np.loadtxt(files[0])[:,2] )
    g2_sum_A = np.zeros(len_data)
    g2_sum_B = np.zeros(len_data)

    # g2 functions for files without rate fluctuations
    g2_sum_A_clean = np.zeros(len_data)
    g2_sum_B_clean = np.zeros(len_data)

    # Read offset data for offset correction
    off3A = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[0]) )[0]
    off3B = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[0]) )[1]
    off4A = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[1]) )[0]
    off4B = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[1]) )[1]

    # Read avg charge data for rate calculation
    charge3A = (np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/calib.calib".format(telcombi[0]) )[12] ) *(-1)
    charge3B = (np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/calib.calib".format(telcombi[0]) )[13] ) *(-1)
    charge4A = (np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/calib.calib".format(telcombi[1]) )[12] ) *(-1)
    charge4B = (np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/calib.calib".format(telcombi[1]) )[13] ) *(-1)

    # Loop over every file
    for i in tqdm(range ( 0,len(files) )):
        file = files[i]

        # Read in data
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
        crossA -= N * ( mean3A*off4A + mean4A*off3A - off3A*off4A ) # Only CH A, but CT3 and CT4
        crossB -= N * ( mean3B*off4B + mean4B*off3B - off3B*off4B ) # Only CH B, but CT3 and CT4

        # Apply pattern correction
        crossA = cor.pattern_correction(crossA) # data already normalized
        crossB = cor.pattern_correction(crossB) # data already normalized

        # Get file parameters from header and ephem calculations
        if star == "Regor":
            tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params_manual(file, ra=[8,10,12.5], dec=[-47,24,22.2], telcombi=telcombi)
        elif star == "Etacen":
            tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params_manual(file, ra=[14,35,30.42], dec=[-42,9,28.17], telcombi=telcombi)
        else:
            tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params(file, starname=star, telcombi=telcombi)
        # Store acquisition times and corresponding baselines for sc plot
        times.append(ephem.Date(time))
        baseline_values.append(uti.get_baseline(date=time, star=star)[get_baseline_entry(telcombi=telcombi)])
        # for rate plotting x axis
        t = str(times[-1]) 
        tplot.append(t.split(' ')[1][0:5])   # get h:min:sec
        alt_all.append(alt)

        # Calculate rate for each channel 
        rate3A = (mean3A - off3A) * 1e-6/ (charge3A * 1.6e-9)  # 1e-6 fuer MHz (durch e6 teilen) und 1.6e-9 fuer 1.6ns bins bei peakshape
        rate3B = (mean3B - off3B) * 1e-6/ (charge3B * 1.6e-9)
        rate4A = (mean4A - off4A) * 1e-6/ (charge4A * 1.6e-9)
        rate4B = (mean4B - off4B) * 1e-6/ (charge4B * 1.6e-9)

        # store rates for txt file
        rate3A_all.append(rate3A)
        rate3B_all.append(rate3B)
        rate4A_all.append(rate4A)
        rate4B_all.append(rate4B)

        # rate ratios between the telescopes
        rateA_ratio.append(rate3A / rate4A)
        rateB_ratio.append(rate3B / rate4B)

        # rate ratio between two neighboring files
        if len(rate3A_all) >=2 :
            ratio_rates3A.append(rate3A / rate3A_all[-2])

        

        # Apply optical path length correction for cross correlations
        binshift = timebin(tdiff)
        crossA = shift_bins(crossA, binshift)
        crossB = shift_bins(crossB, binshift)

        #-- Crosscorrelations --#
        rms = np.std(crossA)
        g2_for_averaging = crossA/rms**2
        # Adding the new data to the total g2 function
        g2_sum_A += g2_for_averaging
    
        rms = np.std(crossB)
        g2_for_averaging = crossB/rms**2
        # Adding the new data to the total g2 function
        g2_sum_B += g2_for_averaging

        if len(ratio_rates3A) >= 1:
            if ratio_rates3A[-1] <= 1.5 and ratio_rates3A[-1] >= 0.5 :
                number += 1
                #-- Crosscorrelations --#
                rms = np.std(crossA)
                g2_for_averaging2 = crossA/rms**2
                # Adding the new data to the total g2 function
                g2_sum_A_clean += g2_for_averaging2
                
                rms = np.std(crossB)
                g2_for_averaging2 = crossB/rms**2
                # Adding the new data to the total g2 function
                g2_sum_B_clean += g2_for_averaging2
        
    print(number)
    # Calculate mean baseline and baseline error
    print(len(baseline_values))
    print(len(tplot))
    bl_diff = baseline_values[0]-baseline_values[-1]
    time_mean = np.mean(times)
    baseline  = np.mean(baseline_values)
    dbaseline = np.std(baseline_values)
    print('Baseline {}     baseline error {}'.format(baseline, dbaseline))

    # Re-normalize for proper g2 function
    g2_sum_A = g2_sum_A/np.mean(g2_sum_A)
    g2_sum_B = g2_sum_B/np.mean(g2_sum_B)

    g2_sum_A_clean = g2_sum_A_clean/np.mean(g2_sum_A_clean)
    g2_sum_B_clean = g2_sum_B_clean/np.mean(g2_sum_B_clean)

    # Save the data of this correlation to the arrays
    g2_As.append(g2_sum_A)
    g2_Bs.append(g2_sum_B)

    g2_As_clean.append(g2_sum_A_clean)
    g2_Bs_clean.append(g2_sum_B_clean)

    # Ratio between g2 and g2 clean (no weird rate fluctuations)
    for i in range(len(g2_sum_A)):
        g2_ratio_A.append(g2_sum_A[i] / g2_sum_A_clean[i])

    # Demo function for initializing x axis and some stuff
    demo = g2_As[0]
    x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)

    plt.plot(x, g2_sum_A, label="{}A x {}A".format(telcombi[0], telcombi[1]))
    plt.plot(x, g2_sum_B, label="{}B x {}B".format(telcombi[0], telcombi[1]))
    plt.plot(x, g2_sum_A_clean, label="A clean")
    plt.plot(x, g2_sum_B_clean, label='B clean')
    plt.xlim(-100,200); plt.grid()
    plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")
    plt.legend()

    # Fit for gaining mu and sigma to fix these parameters
    xplot, popt, perr = uti.fit(g2_sum_A, x, -50, +50)
    muA = popt[1]; sigmaA = popt[2]
    integral, dintegral = uti.integral(popt, perr)
    print ("3A x 4A sigma/integral: {:.2f} +/- {:.2f} ns \t {:.2f} +/- {:.2f} fs".format(popt[2],perr[2],1e6*integral,1e6*dintegral))
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

    xplot, popt, perr = uti.fit(g2_sum_B, x, -50, +50)
    muB = popt[1]; sigmaB = popt[2]
    integral, dintegral = uti.integral(popt, perr)
    print ("3B x 4B sigma/integral: {:.2f} +/- {:.2f} ns \t {:.2f} +/- {:.2f} fs".format(popt[2],perr[2],1e6*integral,1e6*dintegral))
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

    Figure5 = plt.figure(figsize=(10,7))
    plt.plot(tplot[0:-1], ratio_rates3A, label='Ratio {}A files'.format(telcombi[0]), marker='o', color='blue')
    #plt.plot(tplot[0:-1], ratio_ratesB, label="Ratio {}B files".format(telcombi[0]), marker='o', color='orange')
    plt.legend()
    plt.xlabel("Time (UTC)")
    plt.xticks(tplot[::50],rotation=45)
    plt.ylabel("Ratio")
    plt.title("Rates ratio neighboring files of {}".format(star), fontsize=17)
    plt.tight_layout()
    #plt.savefig("rates/{}/{}_{}_rate_ratio_file.pdf".format(star,star,date))

    Figure6 = plt.figure(figsize=(10,7))
    plt.plot(x, g2_ratio_A, label='Ratio A', marker='o', color='blue')
    plt.legend()
    plt.xlabel("Time delay (ns)")
    plt.ylabel("Ratio")
    plt.xlim(-100,200)
    plt.title("Ratio g2 values of {}".format(star))
    plt.tight_layout()

    Figure7 = plt.figure(figsize=(10,7))
    plt.plot(tplot, baseline_values, marker='o', label='Baselines {}'.format(telcombi))
    plt.legend(); plt.xlabel('Time UTC'); plt.ylabel('Baseline (m)')
    plt.title('Baselines for {} of {} one chunk'.format(star,telcombi))
    plt.xticks(tplot[::50],rotation=45)
    plt.text(tplot[-200], baseline_values[70], 'baseline difference: {:.2f}'.format(bl_diff))
    plt.text(tplot[-200], baseline_values[75], 'mean baseline: {:.2f}'.format(baseline))
    plt.text(tplot[-200], baseline_values[90], 'error baseline: {:.2f}'.format(dbaseline))

    plt.show()

##########################################
# Add the number of files to be analyzed #
folder = folders[0]
print(len(folders))
stepsize = stepsizes[0]
end = ends[0]
telcombi = telcombis[0]
steps = np.arange(0, end + 1, stepsize)
start = steps[-2]
stop = steps[-1]
corr_parts(folder, start, stop, telcombi)
