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

#############################################
######## RMS fuer ein file ##################
#############################################
path = "C:/Users/ii/Documents/curcor/corr_results/results_HESS/20220419_HESS/"

off3A = np.loadtxt("{}/calibs_ct3/off.off".format(path) )[0]
off3B = np.loadtxt("{}/calibs_ct3/off.off".format(path) )[1]

charge3A = np.loadtxt("{}/calibs_ct3/calib.calib".format(path))[10]
charge3B = np.loadtxt("{}/calibs_ct3/calib.calib".format(path))[11]

######## expected rms ##############
run = 5825
file = "C:/Users/ii/Documents/curcor/corr_results/results_HESS/20220419_HESS/size10000/shaula_{:05d}.fcorr6".format(run)
f = open(file)
line_params = f.readline()[:-1].split(" ") # Read header of fcorr file
mean3A = float(line_params[2])              # mean from whole file
mean3B = float(line_params[3])
mean4A = float(line_params[4])
mean4B = float(line_params[5])

rate3A = ((mean3A - off3A) / (charge3A * 1.6e-9))/1e6
rate3B = ((mean3B - off3B) / (charge3B * 1.6e-9))/1e6

print(rate3A, rate3B) #, rate4A, rate4B)

exp_rms = 1/ np.sqrt(rate3A * rate3B * 1.6e-9 * 2*(1024**3)*1.6e-9)

#### rate with mean for 1M bins ####
mean_binsA = np.loadtxt("C:/Users/ii/Desktop/GITrepo/curcor/programs/analysis/rates/mean_bins_{}.txt".format(run))[:,0]
mean_binsB = np.loadtxt("C:/Users/ii/Desktop/GITrepo/curcor/programs/analysis/rates/mean_bins_{}.txt".format(run))[:,1]
rate_binsA = []
rate_binsB = []
print(len(mean_binsA))
for i in range( len(mean_binsA)):
    rate_binsA.append( ((mean_binsA[i] - off3A) / (charge3A *1.6e-9)) /1e6) 
    rate_binsB.append( ((mean_binsB[i] - off3B) / (charge3B *1.6e-9)) /1e6)
print(rate_binsA[0], rate_binsB[0])

Figure1 = plt.figure(figsize=(17,12))
plt.plot(rate_binsA, marker='.', ls=' ', label='rate A')
plt.plot(rate_binsB, marker='.', ls=' ', label='rate B')
plt.plot(0,rate3A, marker='o', color='black', label='rate whole file')
plt.plot(0,rate3B, marker='o', color='black', label='rate whole file')
plt.xticks(fontsize=13)
plt.yticks(fontsize=13)
plt.ylabel("Rate (MHz)", fontsize=13)
plt.xlabel("Time (bin)", fontsize=13)
plt.title("Rates of Shaula in {}".format(run), fontsize=17)
plt.savefig("rates/Shaula/rates_bins_{}.pdf".format(run))
plt.show()




######### measured rms ###################
data = np.loadtxt(file)
meas_rms = np.std(data[:,0]/np.mean(data[:,0]))

print("exp rms: ", exp_rms)
print("meas rms:", meas_rms)

print("Ratio:  ",(meas_rms/exp_rms)*100)
