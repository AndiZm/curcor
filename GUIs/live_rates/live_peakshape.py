import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as sig
from tqdm import tqdm
from scipy.optimize import curve_fit
from multiprocessing import Process, Value, Array
#from numba import jit, cuda

import globals as gl

def execute(file, min_pulses, offset, height, cleanheight):
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
		while (pulses_total_a < min_pulses[0] or pulses_total_b < min_pulses[1]) and gl.stop_calib_thread == False:
			# Read data
			buf = (f.read(2*packet_length))
			packet = np.frombuffer(buf, dtype=np.int8)
			packet = packet.reshape(packet_length, 2)
			y_a = np.array(packet[:,0]); y_b = np.array(packet[:,1])
			y_a = y_a.astype(float); y_b = y_b.astype(float)
			x = np.arange(0, len(y_a), 1)

			# Subtract mean
			for i in range (0, len(x)):
				y_a[i] = y_a[i] - offset[0]; y_b[i] = y_b[i] - offset[1]

			# Find peaks
			peaks_a, _ = sig.find_peaks(-y_a, height=height[0]); peaks_b, _ = sig.find_peaks(-y_b, height=height[1])

			# distance to neighboring peaks
			peaks_a_clean = []; peaks_b_clean = []
			for i in range (0,len(peaks_a)):	# Loop over all found pulses
				# The current peak position in the y-array is peaks_a[i]
				y_r =  y_a[(x >= peaks_a[i]-r) & (x <= peaks_a[i]+r)] # Current important fraction of the y-array around the peak position
				peaks_dist, w = sig.find_peaks(-y_r, height=cleanheight[0]) # find peaks in this array section 
				if len(peaks_dist) == 1:						# if only 1 peak found add to peaks3 
					peaks_a_clean.append(peaks_a[i])
			for i in range (0,len(peaks_b)):	# Loop over all found pulses
				# The current peak position in the y-array is peaks_b[i]
				y_r =  y_b[(x >= peaks_b[i]-r) & (x <= peaks_b[i]+r)] # Current important fraction of the y-array around the peak position
				peaks_dist, w = sig.find_peaks(-y_r, height=cleanheight[1]) # find peaks in this array section 
				if len(peaks_dist) == 1:						# if only 1 peak found add to peaks3 
					peaks_b_clean.append(peaks_b[i])
			pulses_total_a += len(peaks_a_clean) # Total number of pulses after height adjustment
			pulses_total_b += len(peaks_b_clean) # Total number of pulses after height adjustment

			# Cumulative normalized peak shape
			for i in range (0,len(peaks_a_clean)):	# Loop over all found pulses
				# The current peak position in the y-array is peaks[i]
				y_range = y_a[(x >= peaks_a_clean[i]-lrange) & (x <= peaks_a_clean[i]+rrange)] # Current important fraction of the y-array around the peak position
				for j in range (0, len(y_range)):	
					# The peak maximum in y_range is at position [lrange] -> yrange[lrange] is the y-value of the peak maximum and hence denominator in the normalization			
					y_tot_a[j] += y_range[j]/y_range[lrange]
			for i in range (0,len(peaks_b_clean)):	# Loop over all found pulses
				# The current peak position in the y-array is peaks[i]
				y_range = y_b[(x >= peaks_b_clean[i]-lrange) & (x <= peaks_b_clean[i]+rrange)] # Current important fraction of the y-array around the peak position
				for j in range (0, len(y_range)):	
					# The peak maximum in y_range is at position [lrange] -> yrange[lrange] is the y-value of the peak maximum and hence denominator in the normalization			
					y_tot_b[j] += y_range[j]/y_range[lrange]

			print ("Total pulses:\tA: " + str(pulses_total_a) + "/" +str(min_pulses[0]) + "\tB: " + str(pulses_total_b) + "/" + str(min_pulses[1]))

	# Average peak shape
	y_avg_a = []; y_avg_b = []
	for i in range (0, len(y_tot_a)):
		y_avg_a.append(y_tot_a[i]/pulses_total_a)
	for i in range (0, len(y_tot_b)):
		y_avg_b.append(y_tot_b[i]/pulses_total_b)
	
	mean_tail_a = np.mean(y_avg_a[50:200])	
	for i in range (0, len(y_avg_a)):
		y_avg_a[i] = (y_avg_a[i] - mean_tail_a)
	mean_tail_b = np.mean(y_avg_b[50:200])	
	for i in range (0, len(y_avg_b)):
		y_avg_b[i] = (y_avg_b[i] - mean_tail_b)
	
	# Integrated normalized peak
	int_tot_a = np.sum(y_avg_a); int_tot_b = np.sum(y_avg_b)

	return int_tot_a, int_tot_b, x_normed, y_avg_a, y_avg_b

def execute_single(file, min_pulses, offset, height, cleanheight):
	packet_length = 1000000

	# Define the length of the average peak 
	lrange = int(10) # range left from the peak maximum
	rrange = int(200) # range right from the peak maximum
	r = int(220)

	# x range of the final peak shape
	x_normed = np.arange(-lrange,rrange+1,1)
	y_tot_a = np.zeros(lrange+rrange+1)
	pulses_total_a = 0

	with open(file, 'rb') as f:
		while (pulses_total_a < min_pulses) and gl.stop_calib_thread == False:
			# Read data
			buf = (f.read(packet_length))
			packet = np.frombuffer(buf, dtype=np.int8)
			y_a = np.array(packet)
			y_a = y_a.astype(float)
			x = np.arange(0, len(y_a), 1)

			# Subtract mean
			for i in range (0, len(x)):
				y_a[i] = y_a[i] - offset

			# Find peaks
			peaks_a, _ = sig.find_peaks(-y_a, height=height)

			# distance to neighboring peaks
			peaks_a_clean = []
			for i in range (0,len(peaks_a)):	# Loop over all found pulses
				# The current peak position in the y-array is peaks_a[i]
				y_r =  y_a[(x >= peaks_a[i]-r) & (x <= peaks_a[i]+r)] # Current important fraction of the y-array around the peak position
				peaks_dist, w = sig.find_peaks(-y_r, height=cleanheight) # find peaks in this array section 
				if len(peaks_dist) == 1:						# if only 1 peak found add to peaks3 
					peaks_a_clean.append(peaks_a[i])
			pulses_total_a += len(peaks_a_clean) # Total number of pulses after height adjustment

			# Cumulative normalized peak shape
			for i in range (0,len(peaks_a_clean)):	# Loop over all found pulses
				# The current peak position in the y-array is peaks[i]
				y_range = y_a[(x >= peaks_a_clean[i]-lrange) & (x <= peaks_a_clean[i]+rrange)] # Current important fraction of the y-array around the peak position
				for j in range (0, len(y_range)):	
					# The peak maximum in y_range is at position [lrange] -> yrange[lrange] is the y-value of the peak maximum and hence denominator in the normalization			
					y_tot_a[j] += y_range[j]/y_range[lrange]

			print ("Total pulses:\tA: " + str(pulses_total_a) + "/" +str(min_pulses))

	# Average peak shape
	y_avg_a = []
	for i in range (0, len(y_tot_a)):
		y_avg_a.append(y_tot_a[i]/pulses_total_a)
	
	mean_tail_a = np.mean(y_avg_a[50:200])	
	for i in range (0, len(y_avg_a)):
		y_avg_a[i] = (y_avg_a[i] - mean_tail_a)
	
	# Integrated normalized peak
	int_tot_a = np.sum(y_avg_a)

	return int_tot_a, x_normed, y_avg_a