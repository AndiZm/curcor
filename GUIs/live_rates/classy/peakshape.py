import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as sig
from tqdm import tqdm
from scipy.optimize import curve_fit
from multiprocessing import Process, Value, Array
from numba import jit, cuda

import globals as gl

def execute(file, nchn, min_pulses, height, cleanheight, tel_number, off_a, off_b):

	packet_length = 1000000

	# Define the length of the average peak 
	lrange = int(10) # range left from the peak maximum
	rrange = int(200) # range right from the peak maximum
	r = int(220)

	# x range of the final peak shape
	x_normed = np.arange(-lrange,rrange+1,1)
	y_tot_a = np.zeros(lrange+rrange+1); y_tot_b = np.zeros(lrange+rrange+1)
	pulses_total_a = 0; pulses_total_b = 0

	with open(file, 'rb') as f:
		if nchn == 2:
			keep_searching = (pulses_total_a < min_pulses[0] or pulses_total_b < min_pulses[1]) and gl.stop_calib_thread[tel_number] == False
		else:
			keep_searching = (pulses_total_a < min_pulses[0]) and gl.stop_calib_thread[tel_number] == False
		while keep_searching:
			# Read data
			if nchn == 2:
				buf = (f.read(2*packet_length))
				packet = np.frombuffer(buf, dtype=np.int8)
				packet = packet.reshape(packet_length, 2)
				y_a = np.array(packet[:,0]); y_b = np.array(packet[:,1])
				y_a = y_a.astype(float); y_b = y_b.astype(float)
			else:
				buf = (f.read(1*packet_length))
				packet = np.frombuffer(buf, dtype=np.int8)
				y_a = np.array(packet)
				y_a = y_a.astype(float)
			x = np.arange(0, len(y_a), 1)

			# Subtract mean and find peaks
			for i in range (0, len(x)):
				y_a[i] = y_a[i] - off_a
			peaks_a, _ = sig.find_peaks(-y_a, height=height[0])
			if nchn == 2:
				for i in range (0, len(x)):
					y_b[i] = y_b[i] - off_b
				peaks_b, _ = sig.find_peaks(-y_b, height=height[1])			

			# distance to neighboring peaks
			peaks_a_clean = []; peaks_b_clean = []
			for i in range (0,len(peaks_a)):	# Loop over all found pulses
				# The current peak position in the y-array is peaks_a[i]
				y_r =  y_a[(x >= peaks_a[i]-r) & (x <= peaks_a[i]+r)] # Current important fraction of the y-array around the peak position
				peaks_dist, w = sig.find_peaks(-y_r, height=cleanheight[0]) # find peaks in this array section 
				if len(peaks_dist) == 1:						# if only 1 peak found add to peaks3 
					peaks_a_clean.append(peaks_a[i])
			pulses_total_a += len(peaks_a_clean) # Total number of pulses after height adjustment
			if nchn == 2:
				for i in range (0,len(peaks_b)):	# Loop over all found pulses
					# The current peak position in the y-array is peaks_b[i]
					y_r =  y_b[(x >= peaks_b[i]-r) & (x <= peaks_b[i]+r)] # Current important fraction of the y-array around the peak position
					peaks_dist, w = sig.find_peaks(-y_r, height=cleanheight[1]) # find peaks in this array section 
					if len(peaks_dist) == 1:						# if only 1 peak found add to peaks3 
						peaks_b_clean.append(peaks_b[i])			
				pulses_total_b += len(peaks_b_clean) # Total number of pulses after height adjustment

			# Cumulative normalized peak shape
			for i in range (0,len(peaks_a_clean)):	# Loop over all found pulses
				# The current peak position in the y-array is peaks[i]
				y_range = y_a[(x >= peaks_a_clean[i]-lrange) & (x <= peaks_a_clean[i]+rrange)] # Current important fraction of the y-array around the peak position
				for j in range (0, len(y_range)):	
					# The peak maximum in y_range is at position [lrange] -> yrange[lrange] is the y-value of the peak maximum and hence denominator in the normalization			
					y_tot_a[j] += y_range[j]/y_range[lrange]
			if nchn == 2:
				for i in range (0,len(peaks_b_clean)):	# Loop over all found pulses
					# The current peak position in the y-array is peaks[i]
					y_range = y_b[(x >= peaks_b_clean[i]-lrange) & (x <= peaks_b_clean[i]+rrange)] # Current important fraction of the y-array around the peak position
					for j in range (0, len(y_range)):	
						# The peak maximum in y_range is at position [lrange] -> yrange[lrange] is the y-value of the peak maximum and hence denominator in the normalization			
						y_tot_b[j] += y_range[j]/y_range[lrange]
				gl.statusLabel[tel_number].config(text="Calibrating: Pulse shape ... \nA: {}/{}    B: {}/{}".format(pulses_total_a,min_pulses[0],pulses_total_b,min_pulses[1]))
			else:
				gl.statusLabel[tel_number].config(text="Calibrating: Pulse shape ... \nA: {}/{}".format(pulses_total_a,min_pulses[0]))

			# Check whether we need to have another run
			if nchn == 2:
				keep_searching = (pulses_total_a < min_pulses[0] or pulses_total_b < min_pulses[1]) and gl.stop_calib_thread[tel_number] == False
			else:
				keep_searching = (pulses_total_a < min_pulses[0]) and gl.stop_calib_thread[tel_number] == False

	# Average peak shape
	y_avg_a = []; y_avg_b = []
	for i in range (0, len(y_tot_a)):
		y_avg_a.append(y_tot_a[i]/pulses_total_a)
	mean_tail_a = np.mean(y_avg_a[50:200])	
	for i in range (0, len(y_avg_a)):
		y_avg_a[i] = (y_avg_a[i] - mean_tail_a)
	nsum_a = np.sum(y_avg_a) # Normalized peak sum
	ps_a = y_avg_a

	nsum_b = None; ps_b = None
	if nchn == 2:
		for i in range (0, len(y_tot_b)):
			y_avg_b.append(y_tot_b[i]/pulses_total_b)	
		mean_tail_b = np.mean(y_avg_b[50:200])	
		for i in range (0, len(y_avg_b)):
			y_avg_b[i] = (y_avg_b[i] - mean_tail_b)
		nsum_b = np.sum(y_avg_b) # Normalized peak sum
		ps_b = y_avg_b

	ps_x = x_normed

	return nsum_a, nsum_b, ps_x, ps_a, ps_b