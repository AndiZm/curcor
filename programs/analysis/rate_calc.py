from matplotlib import pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from matplotlib.pyplot import cm
import matplotlib as mpl
from tqdm import tqdm
from datetime import datetime, timezone
import ephem
import math
from scipy.optimize import curve_fit
import sys

import geometry as geo
import corrections as cor
import utilities as uti

from threading import Thread

star = sys.argv[1]

# Define files to analyze
folders   = [] # Data folders for analysis
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
    #stepsizes.append( int(line.split()[1]) )
    ends.append( int(line.split()[2]) )
    line = f.readline() 
f.close()

print ("Rates of {}".format(star))

star_small = star[0].lower() + star[1:]
folderpath = "C:/Users/ii/Documents/curcor/corr_results/results_HESS"


def rate_calc (folder, start, stop):
	# Initialize parameter arrays for data storing
	rate3A_all = []
	rate3B_all = []
	rate4A_all = []
	rate4B_all = []
	rateA_ratio =[]
	rateB_ratio =[]
	alt_all = []

	# Define total figure for plotting all rates of one night for each channel
	plt.rcParams['figure.figsize'] = 22,10
	fig1, (ax1,ax2) = plt.subplots(1,2, sharey='row')
	# add a big axes, hide frame
	fig1.add_subplot(111, frameon=False)

	# Define files to analyzed for rates of one night 
	files =[]
	for i in range(start, stop):
		files.append("{}/{}/size10000/{}_{:05d}.fcorr6".format(folderpath, folder, star_small, i))

	# Define colormap for plotting all rates of one night of one channel
	x = np.arange(0, len(files))
	cm_sub = np.linspace(1.0, 0.0, len(files))
	colors = [cm.viridis(x) for x in cm_sub]
	times = []; baseline_values = []; tplot =[]
	#print(len(files))

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
	for i in tqdm(range ( 0,len(files) )):
		file = files[i]

        # Read mean waveform values
		f = open(file)
		line_params = f.readline()[:-1].split(" ") # Read header of fcorr file
		mean3A = float(line_params[2])
		mean3B = float(line_params[3])
		mean4A = float(line_params[4])
		mean4B = float(line_params[5])

		# Get file parameters from header and ephem calculations
		if star == "Regor":
			tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params_manual(file, ra=[8,10,12.5], dec=[-47,24,22.2])
		else:
			tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params(file, starname=star)
		# Store acquisition times and corresponding baselines and altitudes for rate plot
		times.append(ephem.Date(time))
		baseline_values.append(uti.get_baseline(date=time, star=star))
		t = str(times[-1]) 
		tplot.append(t.split(' ')[1])	# get h:min:sec
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

		# Plot rates vs time
		p1, = ax1.plot(tplot[-1], rate3A, color="blue", alpha=0.6, marker='.', label="Channel 3A")
		p2, = ax1.plot(tplot[-1], rate3B, color="orange", alpha=0.6, marker='.', label="Channel 3B")
		p3, = ax2.plot(tplot[-1], rate4A, color="green", alpha=0.6, marker='.', label="Channel 4A")
		p4, = ax2.plot(tplot[-1], rate4B, color="purple", alpha=0.6, marker='.', label="Channel 4B")

	# creating x axis for altitude plot
	minval = min(alt_all)
	maxval = max(alt_all)
	minval = math.floor(minval)
	maxval = math.ceil(maxval)
	xplot = np.arange(minval, maxval, 5)

	alt_all = np.array(alt_all)
	# fitting cos to rate vs altitude
	def func(x, a, f, c):
		return a * np.sin(f*x) + c
	p0 = [400, 1/20, 200]
	popt3A, pcov3A = curve_fit(func, alt_all, rate3A_all, p0=p0)
	popt3B, pcov3B = curve_fit(func, alt_all, rate3B_all, p0=p0)
	popt4A, pcov4A = curve_fit(func, alt_all, rate4A_all, p0=p0)
	popt4B, pcov4B = curve_fit(func, alt_all, rate4B_all, p0=p0)


	# Plotting rates vs time
	ax1.set_xticks(tplot[::1000])
	ax1.set_xticklabels(tplot[::1000], rotation=45, fontsize=13)
	ax1.tick_params(labelsize=13)
	ax1.legend(handles=[p1,p2], fontsize=13)
	ax2.set_xticks(tplot[::1000])
	ax2.set_xticklabels(tplot[::1000], rotation=45, fontsize=13)
	ax2.legend(handles=[p3,p4], fontsize=13)
	ax2.tick_params(labelsize=13)
	# hide tick label of the big axes
	plt.tick_params(labelcolor="none", top=False, bottom=False, left=False, right=False)
	# set labels for figure
	plt.title("Rates of {}".format(star), fontsize=17)
	fig1.supxlabel("Time (UTC)", fontsize=14)
	fig1.supylabel("Rate (MHz)", fontsize=14)
	plt.tight_layout()
	fig1.savefig("rates/{}/{}_{}_Tel.pdf".format(star, star, date))
	np.savetxt("rates/{}/{}_{}.txt".format(star, star, date), np.c_[rate3A_all, rate3B_all, rate4A_all, rate4B_all], fmt=' '.join(["%03.2d"]*4 ), header="{} 3A, 3B, 4A, 4B".format(star))


	Figure2 = plt.figure(figsize=(22,10))
	plt.subplot(121)
	plt.plot(tplot, rate3A_all, color="blue", alpha=0.6, marker='.', linestyle='', label="Channel 3A")
	plt.plot(tplot, rate4A_all, color="green", alpha=0.6, marker='.', linestyle='', label="Channel 4A")
	plt.legend(fontsize=13)
	plt.xlabel("Time (UTC)", fontsize=14)
	plt.xticks(tplot[::1000],rotation=45, fontsize=13)
	plt.yticks(fontsize=13)
	plt.ylabel("Rate (MHz)", fontsize=14)
	plt.title("Rates of {}".format(star), fontsize=17)
	plt.tight_layout()
	plt.subplot(122)
	plt.plot(tplot, rate3B_all, color="orange", alpha=0.6, marker='.', linestyle='', label="Channel 3B")
	plt.plot(tplot, rate4B_all, color="purple", alpha=0.6, marker='.', linestyle='', label="Channel 4B")
	plt.legend(fontsize=13)
	plt.xlabel("Time (UTC)", fontsize=14)
	plt.xticks(tplot[::1000],rotation=45, fontsize=13)
	plt.yticks(fontsize=13)
	plt.ylabel("Rate (MHz)", fontsize=14)
	plt.title("Rates of {}".format(star), fontsize=17)
	plt.tight_layout()
	plt.savefig("rates/{}/{}_{}_Ch.pdf".format(star,star,date))


	Figure3 = plt.figure(figsize=(17,12))
	plt.plot(tplot, rateA_ratio, linestyle='-', label='Ratio 3A/4A')
	plt.plot(tplot, rateB_ratio, linestyle='-', label="Ratio 3B/4B")
	plt.legend(fontsize=13)
	plt.xlabel("Time (UTC)", fontsize=14)
	plt.xticks(tplot[::1000],rotation=45, fontsize=13)
	plt.yticks(fontsize=13)
	plt.ylabel("Ratio", fontsize=14)
	plt.title("Ratio of rates of {}".format(star), fontsize=17)
	plt.tight_layout()
	plt.savefig("rates/{}/{}_{}_ratio.pdf".format(star,star,date))

	Figure4 = plt.figure(figsize=(22,10))
	plt.subplot(121)
	plt.plot(alt_all, rate3A_all, marker='.', linestyle='', color="blue", label='Channel 3A')
	plt.plot(alt_all, func(alt_all, *popt3A), color='blue')
	plt.plot(alt_all, rate3B_all, marker='.', linestyle='', color="orange", label='Channel 3B')
	plt.plot(alt_all, func(alt_all, *popt3B), color='orange')
	plt.legend(fontsize=13)
	plt.xlabel("Altitude (degree)", fontsize=14)
	plt.xticks(xplot, fontsize=13)
	plt.yticks(fontsize=13)
	plt.ylabel("Rate (MHz)", fontsize=14)
	plt.title("Rates of {} vs altitude".format(star), fontsize=17)
	plt.tight_layout()
	plt.subplot(122)
	plt.plot(alt_all, rate4A_all, marker='.', linestyle='', color="green", label='Channel 4A')
	plt.plot(alt_all, func(alt_all, *popt4A), color='green')
	plt.plot(alt_all, rate4B_all, marker='.', linestyle='', color="purple", label='Channel 4B')
	plt.plot(alt_all, func(alt_all, *popt4B), color='purple')
	plt.legend(fontsize=13)
	plt.xlabel("Altitude (degree)", fontsize=14)
	plt.xticks(xplot, fontsize=13)
	plt.yticks(fontsize=13)
	plt.ylabel("Rate (MHz)", fontsize=14)
	plt.title("Rates of {} vs altitude".format(star), fontsize=17)
	plt.tight_layout()
	plt.savefig("rates/{}/{}_{}_alt.pdf".format(star,star,date))
	#plt.show()

##########################################
# Add the number of files to be analyzed #
start = 0
#end = 100
for i in range(len(folders)): #range(0,1):#
    folder   = folders[i]
    date = folder[0:8]
    #stepsize = stepsizes[i]
    end      = ends[i]
    #steps = np.arange(0, end + 1, stepsize)
    #for j in range(len(steps)-1):
    #    start = steps[j]
    #    stop = steps[j+1]
    #    corr_parts(folder, start, stop)
    rate_calc(folder, start, end)
    