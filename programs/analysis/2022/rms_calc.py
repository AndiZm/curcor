from matplotlib import pyplot as plt
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

######## RMS for chunks #################
star = sys.argv[1]

# Define files to analyze and subpackages
folders   = [] # Data folders for analysis
stepsizes = [] # Number of files for a single g2 function
ends      = [] # Total number of files used from this folder
# Create parameter arrays for storing 
exp_rmsA = []
exp_rmsB = []
exp_rms3 = []
exp_rms4 = []
exp_rmsAB = []
exp_rmsBA = []
exp_rmsA_corr = []
exp_rmsB_corr = []
exp_rms3_corr = []
exp_rms4_corr = []
exp_rmsAB_corr = []
exp_rmsBA_corr = []


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
folderpath = "C:/Users/ii/Documents/curcor/corr_results/results_HESS"

def rms_parts(folder, start, stop, j):
    # Define files for getting single expected rms
    files = []
    for i in range (start, stop): 
        files.append("{}/{}/size10000/{}_{:05d}.fcorr6".format(folderpath,folder, star_small, i))

    # Create rms parameters 
    M3ges = 0; M4ges = 0; M_Ages = 0; M_Bges = 0; MABges = 0; MBAges = 0
    times = []; baseline_values = []

    # Read offset data for offset correction
    off3A = np.loadtxt( "{}/{}/calibs_ct3/off.off".format(folderpath, folder) )[0]
    off3B = np.loadtxt( "{}/{}/calibs_ct3/off.off".format(folderpath, folder) )[1]
    off4A = np.loadtxt( "{}/{}/calibs_ct4/off.off".format(folderpath, folder) )[0]
    off4B = np.loadtxt( "{}/{}/calibs_ct4/off.off".format(folderpath, folder) )[1]

    # Read avg charge data for rate calculation
    charge3A = np.loadtxt( "{}/{}/calibs_ct3/calib.calib".format(folderpath, folder) )[10]
    charge3B = np.loadtxt( "{}/{}/calibs_ct3/calib.calib".format(folderpath, folder) )[11]
    charge4A = np.loadtxt( "{}/{}/calibs_ct4/calib.calib".format(folderpath, folder) )[10]
    charge4B = np.loadtxt( "{}/{}/calibs_ct4/calib.calib".format(folderpath, folder) )[11]


    # Loop over every file
    for i in range ( 0,len(files) ):
        file = files[i]
        
        # Read mean waveform values for rate calculation
        f = open(file)
        line_params = f.readline()[:-1].split(" ") # Read header of fcorr file
        mean3A = float(line_params[2])
        mean3B = float(line_params[3])
        mean4A = float(line_params[4])
        mean4B = float(line_params[5])

        # Get file parameters from header and ephem calculations
        #tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params(file, starname=star)
        # Store acquisition times 
        #times.append(ephem.Date(time))

        # Calculate rate for each channel 
        rate3A = (mean3A - off3A) / (charge3A * 1.6e-9)  # 1.6e-9 fuer 1.6ns bins bei peakshape
        rate3B = (mean3B - off3B) / (charge3B * 1.6e-9)
        rate4A = (mean4A - off4A) / (charge4A * 1.6e-9)
        rate4B = (mean4B - off4B) / (charge4B * 1.6e-9)
        
        # Calculate rms parameters
        M_A = rate3A * rate4A * 1.6e-9 * 2*(1024**3)*1.6e-9
        M_B = rate3B * rate4B * 1.6e-9 * 2*(1024**3)*1.6e-9
        M3 = rate3A * rate3B * 1.6e-9 * 2*(1024**3)*1.6e-9
        M4 = rate4A * rate4B * 1.6e-9 * 2*(1024**3)*1.6e-9
        Mab = rate3A * rate4B * 1.6e-9 * 2*(1024**3)*1.6e-9
        Mba = rate4A * rate3B * 1.6e-9 * 2*(1024**3)*1.6e-9

        M_Ages += M_A
        M_Bges += M_B
        M3ges += M3
        M4ges += M4
        MABges += Mab 
        MBAges += Mba

    # Calculate expected rms per channel
    exp_rmsA.append((1/ np.sqrt(M_Ages)) /1e-7)
    exp_rmsB.append((1/ np.sqrt(M_Bges)) /1e-7)
    exp_rms3.append((1/ np.sqrt(M3ges))  /1e-7)  
    exp_rms4.append((1/ np.sqrt(M4ges))  /1e-7)
    exp_rmsAB.append((1/ np.sqrt(MABges))  /1e-7)
    exp_rmsBA.append((1/ np.sqrt(MBAges))  /1e-7)

    # Apply correction factor from simulations
    exp_rmsA_corr.append(exp_rmsA[-1]*corfactor[2])
    exp_rmsB_corr.append(exp_rmsB[-1]*corfactor[3])
    exp_rms3_corr.append(exp_rms3[-1]*corfactor[0])
    exp_rms4_corr.append(exp_rms4[-1]*corfactor[1])
    exp_rmsAB_corr.append(exp_rmsAB[-1]*corfactor[4])
    exp_rmsBA_corr.append(exp_rmsBA[-1]*corfactor[5])

    #time_mean = np.mean(times)
    #tstring = ephem.Date(time_mean)
    #print("{}".format(j), tstring, "{:.2f}, {:.2f}, {:.2f}, {:.2f}".format(exp_rmsA, exp_rmsB, exp_rms3, exp_rms4 ))

##########################################
# Add the number of files to be analyzed #
for i in range(len(folders)): # range(2,3)
    folder   = folders[i]
    print(folder)
    stepsize = stepsizes[i]
    end      = ends[i]
    steps = np.arange(0, end + 1, stepsize)
    print(len(steps))
    # Load correction factors from simulations
    corfactor = np.loadtxt("../simulations/data/{}_{}_ana.txt".format(star,folder))[:,0]
    corfactor_std = np.loadtxt("../simulations/data/{}_{}_ana.txt".format(star,folder))[:,1]
    corfactor_err = np.loadtxt("../simulations/data/{}_{}_ana.txt".format(star,folder))[:,2]
    #print(corfactor)
    for j in tqdm(range(len(steps)-1)):
        start = steps[j]
        stop = steps[j+1]
        rms_parts(folder, start, stop, j)

##########################################
######### Calculate measured rms for data #########
# Create parameter arrays for data storing
meas_rmsA = []
meas_rmsB = []
meas_rms3 = []
meas_rms4 = []
meas_rmsAB = []
meas_rmsBA = []
chunk =[]

y =[]
mo = []
d =[]
h = []
mi = []
s = []

# Read in the data (g2 functions and time/baseline parameters)
chAs  = np.loadtxt("g2_functions/{}/ChA.txt".format(star))
chBs  = np.loadtxt("g2_functions/{}/ChB.txt".format(star))
ct3s  = np.loadtxt("g2_functions/{}/CT3.txt".format(star))
ct4s  = np.loadtxt("g2_functions/{}/CT4.txt".format(star))
cABs = np.loadtxt("g2_functions/{}/c3Ax4B.txt".format(star))
cBAs = np.loadtxt("g2_functions/{}/C4Ax3B.txt".format(star))
data  = np.loadtxt("g2_functions/{}/baseline.txt".format(star))

# loop over all chunks
for i in tqdm( range(len(chAs)) ): # range( 11,13)
    chunk.append(i)
    chA = chAs[i]
    chB = chBs[i]
    ct3 = ct3s[i]
    ct4 = ct4s[i]
    cAB = cABs[i]
    cBA = cBAs[i]

    # Only take part of g2 since auto corr have cross talk
    chA = chA[0:4000]
    chB = chB[0:4000]
    ct3 = ct3[0:4000]
    ct4 = ct4[0:4000]
    cAB = cAB[0:4000]
    cBA = cBA[0:4000]

    # Do some more data cleaning, e.g. lowpass filters
    chA = cor.lowpass(chA)
    chB = cor.lowpass(chB)
    ct3 = cor.lowpass(ct3)
    ct4 = cor.lowpass(ct4)
    cAB = cor.lowpass(cAB)
    cBA = cor.lowpass(cBA)

    # Plotting g2 functions
    Figure1 = plt.figure(figsize=(22,10))
    x = np.arange(0, len(chA))
    plt.plot(x, chA, label="A")
    plt.plot(x, chB, label="B")
    plt.plot(x, ct3, label="3", color="green")
    plt.plot(x, ct4, label="4", color="limegreen")
    plt.plot(x, cAB, label="3Ax4B", color="purple")
    plt.plot(x, cBA, label="4Ax3B", color="plum")
    plt.legend()
    plt.title("g2 functions of each channel")
    #plt.show()
    plt.close()

    # FFT of data to see unwanted frequencies
    fftA = np.abs(np.fft.fft(chA-1))
    fftA = fftA[0:len(fftA)//2]
    
    fftB = np.abs(np.fft.fft(chB-1))
    fftB = fftB[0:len(fftB)//2]
    
    fft3 = np.abs(np.fft.fft(ct3-1))
    fft3 = fft3[0:len(fft3)//2]
    
    fft4 = np.abs(np.fft.fft(ct4-1))
    fft4 = fft4[0:len(fft4)//2]

    fftAB = np.abs(np.fft.fft(cAB-1))
    fftAB = fftAB[0:len(fftAB)//2]

    fftBA = np.abs(np.fft.fft(cBA-1))
    fftBA = fftBA[0:len(fftBA)//2]
    
    fftx = np.linspace(0,1./1.6/2,len(fft3), endpoint=False)
    
    # filter higher frequencies
    freqA = [90,130,150]
    chA1 = chA
    for i in range(len(freqA)):
        chA1 = cor.notch(chA1, freqA[i]*1e6, 80)

    freqB = [90, 110, 130, 150, 250]
    chB1 = chB
    for i in range(len(freqB)):
        chB1 = cor.notch(chB1, freqB[i]*1e6, 80)

    freq3 = [50, 90, 125, 130, 150, 250]
    ct31 = ct3
    for i in range(len(freq3)):
    	ct31 = cor.notch(ct31, freq3[i]*1e6, 80)

    freq4 = [50,90,110,125, 130,150, 250]
    ct41 = ct4
    for i in range(len(freq4)):
    	ct41 = cor.notch(ct41, freq4[i]*1e6, 80)
    
    freqAB = [90,130, 150, 250]
    cAB1 = cAB
    for i in range(len(freqAB)):
        cAB1 = cor.notch(cAB1, freqAB[i]*1e6, 80)

    freqBA = [50,90,110,130]
    cBA1 = cBA
    for i in range(len(freqBA)):
        cBA1 = cor.notch(cBA1, freqBA[i]*1e6, 80)

    fftA1 = np.abs(np.fft.fft(chA1-1))
    fftA1 = fftA1[0:len(fftA1)//2]
    fftB1 = np.abs(np.fft.fft(chB1-1))
    fftB1 = fftB1[0:len(fftB1)//2]
    fft31 = np.abs(np.fft.fft(ct31-1))
    fft31 = fft31[0:len(fft31)//2]
    fft41 = np.abs(np.fft.fft(ct41-1))
    fft41 = fft41[0:len(fft41)//2]
    fftAB1 = np.abs(np.fft.fft(cAB1-1))
    fftAB1 = fftAB1[0:len(fftAB1)//2]
    fftBA1 = np.abs(np.fft.fft(cBA1-1))
    fftBA1 = fftBA1[0:len(fftBA1)//2]

    # Plotting g2 functions
    Figure2 = plt.figure(figsize=(22,10))
    x = np.arange(0, len(chA))
    plt.plot(x, chA1, label="A")
    plt.plot(x, chB1, label="B")
    plt.plot(x, ct31, label="3", color="green")
    plt.plot(x, ct41, label="4", color="limegreen")
    plt.plot(x, cAB1, label="3Ax4B", color="purple")
    plt.plot(x, cBA1, label="4Ax3B", color="plum")
    plt.legend()
    plt.title("g2 functions of each channel cleaned")
    #plt.show()
    plt.close()
    
    # Define figure
    Figure3 = plt.figure(figsize=(22,10))
    
    # Subplot for the fft
    plt.subplot(241)
    plt.plot(fftx, fftA, label='A', color="blue")
    plt.plot(fftx, fftA1, label='A clean', color="orange")
    plt.legend(fontsize=14)

    plt.subplot(245) 
    plt.plot(fftx, fftB, label='B', color="blue")
    plt.plot(fftx, fftB1, label='B clean', color="orange")
    plt.legend(fontsize=14)

    plt.subplot(242)
    plt.plot(fftx, fft3, label='3', color="blue")
    plt.plot(fftx, fft31, label='3 clean', color="orange")
    plt.legend(fontsize=14)

    plt.subplot(246)
    plt.plot(fftx, fft4, label='4', color="blue")
    plt.plot(fftx, fft41, label='4 clean', color="orange")
    plt.legend(fontsize=14)

    plt.subplot(243)
    plt.plot(fftx, fftAB, label='3Ax4B', color="blue")
    plt.plot(fftx, fftAB1, label='3Ax4B clean', color="orange")
    plt.legend(fontsize=14)

    plt.subplot(247)
    plt.plot(fftx, fftBA, label='4Ax3B', color="blue")
    plt.plot(fftx, fftBA1, label='4Ax3B clean', color="orange")
    plt.legend(fontsize=14)

    plt.subplot(244)
    plt.plot(fftx, fftA, label='A', color="blue", )
    plt.plot(fftx, fftB, label='B', color="orange")
    plt.plot(fftx, fft3, label='3', color="green")
    plt.plot(fftx, fft4, label='4', color="limegreen")
    plt.plot(fftx, fftAB, label='3Ax4B', color="purple")
    plt.plot(fftx, fftBA, label='4Ax3B', color="plum")
    plt.legend(fontsize=14)

    plt.subplot(248)
    plt.plot(fftx, fftA1, label='A clean', color="blue" )
    plt.plot(fftx, fftB1, label='B clean', color="orange")
    plt.plot(fftx, fft31, label='3 clean', color="green")
    plt.plot(fftx, fft41, label='4 clean', color="limegreen")
    plt.plot(fftx, fftAB1, label='3Ax4B clean', color="purple")
    plt.plot(fftx, fftBA1, label='4Ax3B clean', color="plum")
    plt.legend(fontsize=14)

    #plt.show()
    plt.close()

    # calculate measured rms via std for each channel CT3AxCT4A, CT3BxCT4B, CT3 AxB, CT4 AxB, CT3AxCT4B, CT4AxCT3B
    meas_rmsA.append( np.std(chA1) /1e-7 )
    meas_rmsB.append( np.std(chB1) /1e-7 )
    meas_rms3.append( np.std(ct31) /1e-7 )
    meas_rms4.append( np.std(ct41) /1e-7 )
    meas_rmsAB.append( np.std(cAB1 /1e-7) )
    meas_rmsBA.append( np.std(cBA1 /1e-7) )

# Check acquisition time of original data
chunk_times = data[:,0]
print(ephem.Date(chunk_times[-1]))

## Printing all rms data ###
ratioA = []
ratioB = []
ratio3 = []
ratio4 = []
ratioAB = []
ratioBA = []
ratioA_corr = []
ratioB_corr = []
ratio3_corr = []
ratio4_corr = []
ratioAB_corr = []
ratioBA_corr = []
timestrings = []
for i in range( len(chunk_times)):
    ratioA.append((meas_rmsA[i]/exp_rmsA[i])*100)
    ratioB.append((meas_rmsB[i]/exp_rmsB[i])*100)
    ratio3.append((meas_rms3[i]/exp_rms3[i])*100)
    ratio4.append((meas_rms4[i]/exp_rms4[i])*100)
    ratioAB.append((meas_rmsAB[i]/exp_rmsAB[i])*100)
    ratioBA.append((meas_rmsBA[i]/exp_rmsBA[i])*100)
    ratioA_corr.append((meas_rmsA[i]/exp_rmsA_corr[i])*100)
    ratioB_corr.append((meas_rmsB[i]/exp_rmsB_corr[i])*100)
    ratio3_corr.append((meas_rms3[i]/exp_rms3_corr[i])*100)
    ratio4_corr.append((meas_rms4[i]/exp_rms4_corr[i])*100)
    ratioAB_corr.append((meas_rmsAB[i]/exp_rmsAB_corr[i])*100)
    ratioBA_corr.append((meas_rmsBA[i]/exp_rmsBA_corr[i])*100)
    timestring = ephem.Date(chunk_times[i])
    timestrings.append(str(timestring))
    year, month, day, hour, minute, sec = timestring.tuple()
    y.append(year); mo.append(month); d.append(day); h.append(hour); mi.append(minute); s.append(sec)
    #print("Expected rms {}".format(i), timestring, "{:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}".format(exp_rmsA[i], exp_rmsB[i], exp_rms3[i], exp_rms4[i], exp_rmsAB[i], exp_rmsBA[i]) )
    #print("Measured rms {}".format(i), timestring, "{:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}".format(meas_rmsA[i], meas_rmsB[i], meas_rms3[i], meas_rms4[i], meas_rmsAB[i], meas_rmsBA[i]) )
    #print("Ratio of rms {}".format(i), timestring, "{:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}".format(ratioA[i], ratioB[i], ratio3[i], ratio4[i], ratioAB[i], ratioBA[i]) )

## Saving all rms data ###
np.savetxt("rms/{}.txt".format(star), np.c_[chunk, d, h, mi, exp_rmsA, meas_rmsA, ratioA, exp_rmsB, meas_rmsB, ratioB, exp_rms3, meas_rms3, ratio3, exp_rms4, meas_rms4, ratio4, exp_rmsAB, meas_rmsAB, ratioAB, exp_rmsBA, meas_rmsBA, ratioBA], fmt=' '.join(["%02d"]*4 + ["%02.2f"]*18), header = "{}, {}, chunk number, day, hour, min, exp rms A, meas rms A, ratio A, exp B, meas B, ratio B, exp 3, meas 3, ratio3, exp 4, meas 4, ratio 4, exp AB, meas AB, ratio AB, exp BA, meas BA, ratio BA".format(y[-1], mo[-1]))
data = np.loadtxt("rms/{}.txt".format(star))

## plotting all rms data ###
Figure4 = plt.figure(figsize=(25,10))
plt.subplot(121)
plt.plot(timestrings, exp_rmsA, marker='o', label="exp rms A", color="blue")
plt.plot(timestrings, exp_rmsB, marker='o', label="exp rms B", color="orange")
plt.plot(timestrings, exp_rms3, marker='o', label="exp rms 3", color="green")
plt.plot(timestrings, exp_rms4, marker='o', label="exp rms 4", color="limegreen")
plt.plot(timestrings, exp_rmsAB, marker='o', label="exp rms AB", color="purple")
plt.plot(timestrings, exp_rmsBA, marker='o', label="exp rms BA", color="plum")
plt.plot(timestrings, meas_rmsA, marker='o', label="meas rms A", linestyle="--", color="blue")
plt.plot(timestrings, meas_rmsB, marker='o', label="meas rms B", linestyle="--", color="orange")
plt.plot(timestrings, meas_rms3, marker='o', label="meas rms 3", linestyle="--", color="green")
plt.plot(timestrings, meas_rms4, marker='o', label="meas rms 4", linestyle="--", color="limegreen")
plt.plot(timestrings, meas_rmsAB, marker='o', linestyle="--", label="meas rms AB", color="purple")
plt.plot(timestrings, meas_rmsBA, marker='o', linestyle="--", label="meas rms BA", color="plum")
plt.legend(fontsize=13)
plt.xlabel("Time chunk", fontsize=14)
plt.xticks(rotation=45, fontsize=13)
plt.yticks(fontsize=13)
plt.ylabel("RMS", fontsize=14)
plt.title("RMS of {}".format(star), fontsize=17)
plt.tight_layout()
plt.subplot(122)
plt.plot(timestrings, exp_rmsA_corr, marker='^', linestyle="-", label="exp rms A corfactor", color="blue")
plt.plot(timestrings, exp_rmsB_corr, marker='^', linestyle="-", label="exp rms B corfactor", color="orange")
plt.plot(timestrings, exp_rms3_corr, marker='^', linestyle="-", label="exp rms 3 corfactor", color="green")
plt.plot(timestrings, exp_rms4_corr, marker='^', linestyle="-", label="exp rms 4 corfactor", color="limegreen")
plt.plot(timestrings, exp_rmsAB_corr, marker='^', linestyle="-", label="exp rms AB corfactor", color="purple")
plt.plot(timestrings, exp_rmsBA_corr, marker='^', linestyle="-", label="exp rms BA corfactor", color="plum")
plt.plot(timestrings, meas_rmsA, marker='o', label="meas rms A", linestyle="--", color="blue")
plt.plot(timestrings, meas_rmsB, marker='o', label="meas rms B", linestyle="--", color="orange")
plt.plot(timestrings, meas_rms3, marker='o', label="meas rms 3", linestyle="--", color="green")
plt.plot(timestrings, meas_rms4, marker='o', label="meas rms 4", linestyle="--", color="limegreen")
plt.plot(timestrings, meas_rmsAB, marker='o', linestyle="--", label="meas rms AB", color="purple")
plt.plot(timestrings, meas_rmsBA, marker='o', linestyle="--", label="meas rms BA", color="plum")
plt.legend(fontsize=13)
plt.xlabel("Time chunk", fontsize=14)
plt.xticks(rotation=45, fontsize=13)
plt.yticks(fontsize=13)
plt.ylabel("RMS", fontsize=14)
plt.title("RMS corrected of {}".format(star), fontsize=17)
plt.tight_layout()

Figure5 = plt.figure(figsize=(20,10))
plt.plot(timestrings, ratioA, marker='o', label="ratio A", linestyle="-", color="blue")
plt.plot(timestrings, ratioB, marker='o', label="ratio B", linestyle="-", color="orange")
plt.plot(timestrings, ratio3, marker='o', label="ratio 3", linestyle="-", color="green")
plt.plot(timestrings, ratio4, marker='o', label="ratio 4", linestyle="-", color="limegreen")
plt.plot(timestrings, ratioAB, marker='o', linestyle="-", label="ratio AB", color="purple")
plt.plot(timestrings, ratioBA, marker='o', linestyle="-", label="ratio BA", color="plum")
plt.plot(timestrings, ratioA_corr, marker='o', label="ratio corrected A", linestyle="--", color="blue")
plt.plot(timestrings, ratioB_corr, marker='o', label="ratio corrected B", linestyle="--", color="orange")
plt.plot(timestrings, ratio3_corr, marker='o', label="ratio corrected 3", linestyle="--", color="green")
plt.plot(timestrings, ratio4_corr, marker='o', label="ratio corrected 4", linestyle="--", color="limegreen")
plt.plot(timestrings, ratioAB_corr, marker='o', linestyle="--", label="ratio corrected AB", color="purple")
plt.plot(timestrings, ratioBA_corr, marker='o', linestyle="--", label="ratio corrected BA", color="plum")

plt.legend(fontsize=13)
plt.xlabel("Time chunk", fontsize=14)
plt.xticks(rotation=45, fontsize=13)
plt.yticks(fontsize=13)
plt.ylabel("Ratio measured to expected", fontsize=14)
plt.title("Ratio of RMS of {}".format(star), fontsize=17)
plt.tight_layout()
plt.show()

'''
######## RMS fuer ein file ##################
file = "../20220419_HESS/size10000/shaula_00000.fcorr"

off3A = np.loadtxt( "../20220419_HESS/calibs_ct3/off.off" )[0]
off3B = np.loadtxt( "../20220419_HESS/calibs_ct3/off.off" )[1]

charge3A = np.loadtxt( "../20220419_HESS/calibs_ct3/calib.calib" )[10]
charge3B = np.loadtxt( "../20220419_HESS/calibs_ct3/calib.calib" )[11]

f = open(file)
line_params = f.readline()[:-1].split(" ") # Read header of fcorr file
mean3A = float(line_params[2])
mean3B = float(line_params[3])

rate3A = (mean3A - off3A) / (charge3A * 1.6e-9)
rate3B = (mean3B - off3B) / (charge3B * 1.6e-9)

print(rate3A)
print(rate3B)

exp_rms = 1/ np.sqrt(rate3A * rate3B * 1.6e-9 * 2*(1024**3)*1.6e-9)

data = np.loadtxt("../20220419_HESS/size10000/shaula_00000.fcorr")
meas_rms = np.std(data[:,0]/np.mean(data[:,0]))

print(exp_rms)
print(meas_rms)

print((meas_rms/exp_rms)*100)
'''