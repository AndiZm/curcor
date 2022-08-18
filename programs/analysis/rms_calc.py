from matplotlib import pyplot as plt
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

######## RMS for chunks #################
star = "Shaula"

# Define files to analyze and subpackages
folders   = [] # Data folders for analysis
stepsizes = [] # Number of files for a single g2 function
ends      = [] # Total number of files used from this folder
# Create parameter arrays for storing 
exp_rmsA = []
exp_rmsB = []
exp_rms3 = []
exp_rms4 = []

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

def rms_parts(folder, start, stop, j):
    # Define files for getting single expected rms
    files = []
    for i in range (start, stop): 
        files.append("{}/size10000/{}_{:05d}.fcorr".format(folder, star_small, i))

    # Create rms parameters 
    M3ges = 0; M4ges = 0; M_Ages = 0; M_Bges = 0
    times = []; baseline_values = []

    # Read offset data for offset correction
    off3A = np.loadtxt( folder + "/calibs_ct3/off.off" )[0]
    off3B = np.loadtxt( folder + "/calibs_ct3/off.off" )[1]
    off4A = np.loadtxt( folder + "/calibs_ct4/off.off" )[0]
    off4B = np.loadtxt( folder + "/calibs_ct4/off.off" )[1]

    # Read avg charge data for rate calculation
    charge3A = np.loadtxt( folder + "/calibs_ct3/calib.calib" )[10]
    charge3B = np.loadtxt( folder + "/calibs_ct3/calib.calib" )[11]
    charge4A = np.loadtxt( folder + "/calibs_ct4/calib.calib" )[10]
    charge4B = np.loadtxt( folder + "/calibs_ct4/calib.calib" )[11]


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

        M_Ages += M_A
        M_Bges += M_B
        M3ges += M3
        M4ges += M4

    # Calculate expected rms per channel
    exp_rmsA.append((1/ np.sqrt(M_Ages)) /1e-7)
    exp_rmsB.append((1/ np.sqrt(M_Bges)) /1e-7)
    exp_rms3.append((1/ np.sqrt(M3ges))  /1e-7)  
    exp_rms4.append((1/ np.sqrt(M4ges))  /1e-7)

    #time_mean = np.mean(times)
    #tstring = ephem.Date(time_mean)
    #print("{}".format(j), tstring, "{:.2f}, {:.2f}, {:.2f}, {:.2f}".format(exp_rmsA, exp_rmsB, exp_rms3, exp_rms4 ))

##########################################
# Add the number of files to be analyzed #
for i in range(len(folders)):  #range(2,3): #
    folder   = folders[i]
    stepsize = stepsizes[i]
    end      = ends[i]
    steps = np.arange(0, end + 1, stepsize)
    for j in range(len(steps)-1):
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
chunk =[]
chunk_times =[]
y =[]
mo = []
d =[]
h = []
mi = []
s = []

# Read in the data (g2 functions and time/baseline parameters)
chAs  = np.loadtxt("../g2_functions/Cross/txt_new/{}/ChA.txt".format(star))
chBs  = np.loadtxt("../g2_functions/Cross/txt_new/{}/ChB.txt".format(star))
ct3s  = np.loadtxt("../g2_functions/Cross/txt_new/{}/CT3.txt".format(star))
ct4s  = np.loadtxt("../g2_functions/Cross/txt_new/{}/CT4.txt".format(star))
data  = np.loadtxt("../g2_functions/Cross/txt_new/{}/baseline.txt".format(star))

# loop over all chunks
for i in tqdm(range(len(chAs))):  # range( 10,12):
    chunk.append(i)
    chA = chAs[i]
    chB = chBs[i]
    ct3 = ct3s[i]
    ct4 = ct4s[i]

    # Do some more data cleaning, e.g. lowpass filters
    ct3 = cor.lowpass(ct3)
    ct4 = cor.lowpass(ct4)

    # FFT of data to see unwanted frequencies
    fftA = np.abs(np.fft.fft(chA-1))
    fftA = fftA[0:len(fftA)//2]
    
    fftB = np.abs(np.fft.fft(chB-1))
    fftB = fftB[0:len(fftB)//2]
    
    fft3 = np.abs(np.fft.fft(ct3-1))
    fft3 = fft3[0:len(fft3)//2]
    
    fft4 = np.abs(np.fft.fft(ct4-1))
    fft4 = fft4[0:len(fft4)//2]
    
    fftx = np.linspace(0,1./1.6/2,len(fft3), endpoint=False)
    #plt.plot(chA, color='blue', label = 'A')
    #plt.plot(chB, color='orange', label = 'B')
    #plt.plot(ct3, color='purple', label = '3')
    #plt.plot(ct4, color='green', label = '4')
    #plt.title('original data')
    #plt.legend()
    #plt.show()
    #plt.close()
    plt.plot(fftx,fftA, color='blue', label = 'A')
    plt.plot(fftx,fftB, color='orange', label = 'B')
    plt.plot(fftx,fft3, color='purple', label = '3')
    plt.plot(fftx,fft4, color='green', label = '4')
    plt.title('original fft')
    plt.legend()
    plt.show()
    plt.close()

    # filter higher frequencies
    freq = [50, 90, 125, 150]
    ct31 = ct3
    for i in range(len(freq)):
    	ct31 = cor.notch(ct31, freq[i]*1e6, 80)
    freq4 = [50, 90, 110, 130, 150, 250]
    ct41 = ct4
    for i in range(len(freq4)):
    	ct41 = cor.notch(ct41, freq4[i]*1e6, 80)

    #plt.plot(chA, color='blue', label = 'A')
    #plt.plot(chB, color='orange', label = 'B')
    #plt.plot(ct31, color='purple', label = '3')
    #plt.plot(ct41, color='green', label = '4')
    #plt.title('cleaned data')
    #plt.legend()
    #plt.show()
    #plt.close()
    fft31 = np.abs(np.fft.fft(ct31-1))
    fft31 = fft31[0:len(fft31)//2]
    fft41 = np.abs(np.fft.fft(ct41-1))
    fft41 = fft41[0:len(fft41)//2]
    plt.plot(fftx,fftA, color='blue', label = 'A', alpha=0.6)
    plt.plot(fftx,fftB, color='orange', label = 'B', alpha=0.6)
    plt.plot(fftx,fft3, color='purple', label = '3', alpha=0.6)
    plt.plot(fftx,fft4, color='green', label='4', alpha=0.6)
    plt.plot(fftx,fft41, color='red', label = '41', alpha=0.6)
    plt.plot(fftx,fft31, color='cyan', label = '31', alpha=0.6)
    plt.title("cleaned fft")
    plt.legend()
    plt.show()
    plt.close()

    # calculate measured rms via std for each channel CT3AxCT3A, CT3BxCT4B, CT3 AxB, CT4 AxB
    meas_rmsA.append( np.std(chA) /1e-7 )
    meas_rmsB.append( np.std(chB) /1e-7 )
    meas_rms3.append( np.std(ct31[0:4500]) /1e-7 )
    meas_rms4.append( np.std(ct41[0:4500]) /1e-7 )

    # Check acquisition time of original data
    chunk_times.append( (data[:,0][i]) )
    t = ephem.Date(chunk_times[-1])
    year, month, day, hour, minute, sec = t.tuple()
    y.append(year); mo.append(month); d.append(day); h.append(hour); mi.append(minute); s.append(sec)

## Printing all rms data ###
ratioA = []
ratioB = []
ratio3 = []
ratio4 = []
for i in range( len(chunk_times)):
	ratioA.append((meas_rmsA[i]/exp_rmsA[i])*100)
	ratioB.append((meas_rmsB[i]/exp_rmsB[i])*100)
	ratio3.append((meas_rms3[i]/exp_rms3[i])*100)
	ratio4.append((meas_rms4[i]/exp_rms4[i])*100)
	timestrings = ephem.Date(chunk_times[i])
	print("Expected rms {}".format(i), timestrings, "{:.2f}, {:.2f}, {:.2f}, {:.2f}".format(exp_rmsA[i], exp_rmsB[i], exp_rms3[i], exp_rms4[i]) )
	print("Measured rms {}".format(i), timestrings, "{:.2f}, {:.2f}, {:.2f}, {:.2f}".format(meas_rmsA[i], meas_rmsB[i], meas_rms3[i], meas_rms4[i]) )
	print("Ratio of rms {}".format(i), timestrings, "{:.2f}, {:.2f}, {:.2f}, {:.2f}".format(ratioA[i], ratioB[i], ratio3[i], ratio4[i]) )

## Saving all rms data ###
np.savetxt("rms/{}.txt".format(star), np.c_[chunk, d, h, mi, exp_rmsA, meas_rmsA, ratioA, exp_rmsB, meas_rmsB, ratioB, exp_rms3, meas_rms3, ratio3, exp_rms4, meas_rms4, ratio4], fmt=' '.join(["%02d"]*4 + ["%02.2f"]*12), header = "{}, {}, chunk number, day, hour, min, exp rms A, meas rms A, ratio A, exp B, meas B, ratio B, exp 3, meas 3, ratio3, exp 4, meas 4, ratio 4".format(y[-1], mo[-1]))

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