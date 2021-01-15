import numpy as np

def gauss(x,a,m,s):
	return a * np.exp(-(x-m)**2/2/s/s)

def phd(mean, sigma):
	
	# Rateloss calculation	
	border_left  = int(mean - 5*sigma)
	border_right = int(mean + 5*sigma)
	
	x_sample = np.arange(border_left,border_right,0.1)
	x_in  = np.arange(border_left,0,0.1)
	x_out = np.arange(0,border_right,0.1)
	sum_tot = 0; sum_sz = 0; sum_xy = 0
	for i in x_sample:
		x = i; y = gauss(i, 1,mean,sigma)
		sum_tot += y
		if i < 0:
			sum_sz += y
			sum_xy += x*y
	keep = sum_sz/sum_tot; loss = 1-keep; avg = sum_xy/sum_sz

	return keep, avg

def execute(calibfile_A, calibfile_B, voltage_a, voltage_b):
	# Calibration data
	calib_a = np.loadtxt(calibfile_A); calib_b = np.loadtxt(calibfile_B)
	c_v_a = calib_a[:,0]; c_mean_a = calib_a[:,1]; c_sigma_a = calib_a[:,2]
	c_v_b = calib_b[:,0]; c_mean_b = calib_b[:,1]; c_sigma_b = calib_b[:,2]
	#get mean and sigma
	phd_mean_a = []; phd_sigma_a = []; phd_keep_a = []; phd_avg_a = [] # mV
	phd_mean_b = []; phd_sigma_b = []; phd_keep_b = []; phd_avg_b = [] # mV

	for i in range (0, len(c_v_a)):
	    if c_v_a[i] == voltage_a:
	        phd_mean_a  = c_mean_a[i]; phd_sigma_a = c_sigma_a[i]
	        phd_keep_a, phd_avg_a = phd(phd_mean_a, phd_sigma_a)
	for i in range (0, len(c_v_b)):
	    if c_v_b[i] == voltage_b:
	        phd_mean_b  = c_mean_b[i]; phd_sigma_b = c_sigma_b[i]
	        phd_keep_b, phd_avg_b = phd(phd_mean_b, phd_sigma_b)

	return phd_avg_a, phd_avg_b

