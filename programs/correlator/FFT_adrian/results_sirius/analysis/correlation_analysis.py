import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from matplotlib.pyplot import cm
import matplotlib as mpl
from tqdm import tqdm

import files as files
import geometry as geo
import corrections as cor

from threading import Thread

ratecut = 150
len_data = len(np.loadtxt(files.files[0]))

n_N = 0; isum = np.zeros( len_data )

# Get the timebin shift of the specific measurement from the time difference
def timebin(tdiff):
    return int(1.0* np.floor((tdiff+0.8)/1.6))
def g2_array(timebin):
    return int(timebin + 3)

# Initialize the 5 sub-g2 data arrays
n_N  = [0,0,0,0,0] # denominator of normalization
isum = [np.zeros(len_data),np.zeros(len_data),np.zeros(len_data),np.zeros(len_data),np.zeros(len_data)] # isum becoms g2 in the end
G2   = [np.zeros(len_data),np.zeros(len_data),np.zeros(len_data),np.zeros(len_data),np.zeros(len_data)] # conventional calculation of G2

tdiffs = []; rates_1 = []; rates_2 = []; rmss = []

for i in tqdm(range ( 0,len(files.files) )):
    # Read in files
    file    = files.files[i]
    off_1   = files.off_1  [files.info_id[i]]
    off_2   = files.off_2  [files.info_id[i]]
    calib_1 = files.calib_1[files.info_id[i]]
    calib_2 = files.calib_2[files.info_id[i]]
    # Calculate rate and time difference
    mean_1, mean_2, tdiff = geo.get_params(file)
    rate_1 = 1e-6 * mean_1/(calib_1 * 1.6e-9)
    rate_2 = 1e-6 * mean_2/(calib_2 * 1.6e-9)
    # Apply cut
    if rate_1 >= ratecut and rate_2 >= ratecut:
        data_orig = np.loadtxt(file)
        #data = cor.gauss_filter(data)
        data = cor.pattern_correction(data_orig)
        rms = np.std(data)

        binshift = timebin(tdiff)
        array_position = g2_array(binshift)
        for j in range (0,len_data):
            isum[array_position][j] += data[j]/rms
            G2[array_position][j] += data_orig[j]
        n_N[array_position] += 1./rms

       #tdiffs.append(tdiff); rates_1.append(rate_1); rates_2.append(rate_2); rmss.append(rms)

# Create final 5 g2 arrays
for i in range (0,5):
    if n_N[i] == 0:
        n_N[i] = 1
    n = 1./n_N[i]
    for j in range (0,len_data):
        isum[i][j] *= n
    G2[i] = cor.pattern_correction(G2[i])

np.savetxt("g2_con.txt", np.c_[ G2[0],G2[1],G2[2],G2[3],G2[4] ])
np.savetxt("g2_new.txt", np.c_[ isum[0],isum[1],isum[2],isum[3],isum[4] ])