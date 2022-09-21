import numpy as np
import matplotlib.pyplot as plt
from random import randrange
import random
import scipy.signal as sign
from os import listdir
from os.path import isfile, join
from tqdm import tqdm
import cupy

def scalarproduct(vec_1, vec_2):
	return np.sum(np.array(vec_1) * np.array(vec_2))

star = "Shaula"

# Define files to analyze and subpackages
folders   = [] # Data folders for analysis


# Open text file with measurement split data and read the data for the specific star
f = open("../analysis/measurement_chunks.txt")
# Find line for the star
line = f.readline()
while star not in line:
    line = f.readline()
# Fill arrays with the data
line = f.readline()
while "[end]" not in line:
    folders.append(line.split()[0])
    line = f.readline()
f.close()

# Datapoints
datapoints = int(1e6)
time = datapoints * 1.6e-9 # in seconds

#Photon rate
rate = 200e6 # in Hz
# Number of photons simulated on each waveform
n_phot = int(rate*time)

# Expected RMS
rms_exp = 1./np.sqrt( rate**2 * time * 1.6e-9 )

for i in range(len(folders)):
	# Read calibration data for each folder
	calibs_ct3 = "C:/Users/ii/Documents/curcor/corr_results/results_HESS/{}/calibs_ct3".format(folders[i])
	calibs_ct4 = "C:/Users/ii/Documents/curcor/corr_results/results_HESS/{}/calibs_ct4".format(folders[i])

	# Gaussian parameters:
	med_3a = np.loadtxt(calibs_ct3 + "/calib.calib")[1]
	sig_3a = np.loadtxt(calibs_ct3 + "/calib.calib")[2]
	med_3b = np.loadtxt(calibs_ct3 + "/calib.calib")[4]
	sig_3b = np.loadtxt(calibs_ct3 + "/calib.calib")[5]

	med_4a = np.loadtxt(calibs_ct4 + "/calib.calib")[1]
	sig_4a = np.loadtxt(calibs_ct4 + "/calib.calib")[2]
	med_4b = np.loadtxt(calibs_ct4 + "/calib.calib")[4]
	sig_4b = np.loadtxt(calibs_ct4 + "/calib.calib")[5]

	# Peak shape
	data = np.loadtxt(calibs_ct3 + "/calib.shape", delimiter=" ")
	x_wf = data[:,0]; y_wf_3a = data[:,1]; y_wf_3b = data[:,2]

	data = np.loadtxt(calibs_ct4 + "/calib.shape", delimiter=" ")
	x_wf = data[:,0]; y_wf_4a = data[:,1]; y_wf_4b = data[:,2]

	beg = int(np.abs(x_wf[0])); end = int(np.abs(x_wf[-1]))

	#print ("3A:\t{}\t{}".format(med_3a,sig_3a))
	#print ("3B:\t{}\t{}".format(med_3b,sig_3b))
	#print ("4A:\t{}\t{}".format(med_4a,sig_4a))
	#print ("4B:\t{}\t{}".format(med_4b,sig_4b))

	#plt.title(folders[i])
	#plt.plot(x_wf, y_wf_3a)
	#plt.plot(x_wf, y_wf_3b)
	#plt.plot(x_wf, y_wf_4a)
	#plt.plot(x_wf, y_wf_4b)
	#plt.show()

	factor3s = []
	factor4s = []
	factorAs = []
	factorBs = []
	factor3Ax4Bs = []
	factor4Ax3Bs = []


	for run in range(0,400):
		print ("Run: ", run)

		# Waveform baseline
		waveform_3a = np.zeros(datapoints + len(x_wf))
		waveform_3b = np.zeros(datapoints + len(x_wf))
		waveform_4a = np.zeros(datapoints + len(x_wf))
		waveform_4b = np.zeros(datapoints + len(x_wf))
	
		# Random photons
		#print ("\tSimulate photons ...")
		for j in tqdm(range (0, n_phot)):
			#-- Channel 3a --#
			height = random.gauss(med_3a, sig_3a)
			# Only take the height if it's negative
			while (height >= 0):
				height = random.gauss(med_3a,sig_3a)
			# Draw arrival time of this photon on the waveform baseline
			arrival = randrange(beg,datapoints+beg)
			# Add the photon to the waveform baseline
			for k in range (0, len(x_wf)):
				waveform_3a[int(arrival + x_wf[k])] += y_wf_3a[k] * height
	
			#-- Channel 3b --#
			height = random.gauss(med_3b, sig_3b)
			# Only take the height if it's negative
			while (height >= 0):
				height = random.gauss(med_3b,sig_3b)
			# Draw arrival time of this photon on the waveform baseline
			arrival = randrange(beg,datapoints+beg)
			# Add the photon to the waveform baseline
			for k in range (0, len(x_wf)):
				waveform_3b[int(arrival + x_wf[k])] += y_wf_3b[k] * height
	
			#-- Channel 4a --#
			height = random.gauss(med_4a, sig_4a)
			# Only take the height if it's negative
			while (height >= 0):
				height = random.gauss(med_4a,sig_4a)
			# Draw arrival time of this photon on the waveform baseline
			arrival = randrange(beg,datapoints+beg)
			# Add the photon to the waveform baseline
			for k in range (0, len(x_wf)):
				waveform_4a[int(arrival + x_wf[k])] += y_wf_4a[k] * height
	
			#-- Channel 4b --#
			height = random.gauss(med_4b, sig_4b)
			# Only take the height if it's negative
			while (height >= 0):
				height = random.gauss(med_4b,sig_4b)
			# Draw arrival time of this photon on the waveform baseline
			arrival = randrange(beg,datapoints+beg)
			# Add the photon to the waveform baseline
			for k in range (0, len(x_wf)):
				waveform_4b[int(arrival + x_wf[k])] += y_wf_4b[k] * height
	
		# Round waveforms to integer because digitization to integer ADC counts
		waveform_3a = np.rint(waveform_3a)
		waveform_3b = np.rint(waveform_3b)
		waveform_4a = np.rint(waveform_4a)
		waveform_4b = np.rint(waveform_4b)
	
		#plt.plot(waveform_3a)
		#plt.plot(waveform_3b)
		#plt.plot(waveform_4a)
		#plt.plot(waveform_4b)
		#plt.show()	
	
		# Correlation
		corlen  = 50000
		length  = datapoints
		acorlen = corlen+1
	
		# 3A x 3B
		waveform_3b_cu = cupy.array(waveform_3b[ int(corlen/2) : length-int(corlen/2) ]).astype(np.float32)
		waveform_3a_cu = cupy.array(waveform_3a[ 0 : length ]).astype(np.float32)
		corr_3 = cupy.correlate(waveform_3b_cu, waveform_3a_cu, "valid")
		corr_3 = cupy.asnumpy(corr_3)
		# 4A x 4B
		waveform_4b_cu = cupy.array(waveform_4b[ int(corlen/2) : length-int(corlen/2) ]).astype(np.float32)
		waveform_4a_cu = cupy.array(waveform_4a[ 0 : length ]).astype(np.float32)
		corr_4 = cupy.correlate(waveform_4b_cu, waveform_4a_cu, "valid")
		corr_4 = cupy.asnumpy(corr_4)
		# 3A x 4A
		waveform_4a_cu = cupy.array(waveform_4a[ int(corlen/2) : length-int(corlen/2) ]).astype(np.float32)
		waveform_3a_cu = cupy.array(waveform_3a[ 0 : length ]).astype(np.float32)
		corr_A = cupy.correlate(waveform_4a_cu, waveform_3a_cu, "valid")
		corr_A = cupy.asnumpy(corr_A)
		# 3B x 4B
		waveform_4b_cu = cupy.array(waveform_4b[ int(corlen/2) : length-int(corlen/2) ]).astype(np.float32)
		waveform_3b_cu = cupy.array(waveform_3b[ 0 : length ]).astype(np.float32)
		corr_B = cupy.correlate(waveform_4b_cu, waveform_3b_cu, "valid")
		corr_B = cupy.asnumpy(corr_B)
		# 3A x 4B
		waveform_4b_cu = cupy.array(waveform_4b[ int(corlen/2) : length-int(corlen/2) ]).astype(np.float32)
		waveform_3a_cu = cupy.array(waveform_3a[ 0 : length ]).astype(np.float32)
		corr_3Ax4B = cupy.correlate(waveform_4b_cu, waveform_3a_cu, "valid")
		corr_3Ax4B = cupy.asnumpy(corr_3Ax4B)
		# 4A x 3B
		waveform_3b_cu = cupy.array(waveform_3b[ int(corlen/2) : length-int(corlen/2) ]).astype(np.float32)
		waveform_4a_cu = cupy.array(waveform_4a[ 0 : length ]).astype(np.float32)
		corr_4Ax3B = cupy.correlate(waveform_3b_cu, waveform_4a_cu, "valid")
		corr_4Ax3B = cupy.asnumpy(corr_4Ax3B)
	
		# Normalize
		corr_3 = corr_3/np.mean(corr_3)
		corr_4 = corr_4/np.mean(corr_4)
		corr_A = corr_A/np.mean(corr_A)
		corr_B = corr_B/np.mean(corr_B)
		corr_3Ax4B = corr_3Ax4B/np.mean(corr_3Ax4B)
		corr_4Ax3B = corr_4Ax3B/np.mean(corr_4Ax3B)
	
		#plt.plot(corr_3)
		#plt.plot(corr_4)
		#plt.plot(corr_A)
		#plt.plot(corr_B)
		#plt.plot(corr_3Ax4B)
		#plt.plot(corr_4Ax3B)
		#plt.show()
	
		# Calculate measured rms and correction factor
		# 3A x 3B
		rms_meas = np.std(corr_3)
		factor3  = rms_meas/rms_exp
		factor3s.append(factor3)
		# 4A x 4B
		rms_meas = np.std(corr_4)
		factor4  = rms_meas/rms_exp
		factor4s.append(factor4)
		# 3A x 4A
		rms_meas = np.std(corr_A)
		factorA  = rms_meas/rms_exp
		factorAs.append(factorA)
		# 3B x 4B
		rms_meas = np.std(corr_B)
		factorB  = rms_meas/rms_exp
		factorBs.append(factorB)
		# 3A x 4B
		rms_meas = np.std(corr_3Ax4B)
		factor3Ax4B = rms_meas/rms_exp
		factor3Ax4Bs.append(factor3Ax4B)
		# 4A x 3B
		rms_meas = np.std(corr_4Ax3B)
		factor4Ax3B = rms_meas/rms_exp
		factor4Ax3Bs.append(factor4Ax3B)
	
		print (factor3, factor4, factorA, factorB, factor3Ax4B, factor4Ax3B)

	# Save rms data
	np.savetxt("data/{}_{}.txt".format(star, folders[i]), np.c_[factor3s,factor4s,factorAs,factorBs,factor3Ax4Bs,factor4Ax3Bs], header="3, 4, A, B, 3Ax4B, 4Ax3B")


	# Calculate average, mean and std of correction factor
	mean_factor3s = np.mean(factor3s)
	mean_factor4s = np.mean(factor4s)
	mean_factorAs = np.mean(factorAs)
	mean_factorBs = np.mean(factorBs)
	mean_factor3Ax4Bs = np.mean(factor3Ax4Bs)
	mean_factor4Ax3Bs = np.mean(factor4Ax3Bs)

	#np.savetxt("data/{}_{}_mean.txt".format(star, folders[i]), np.c_[mean_factor3s, mean_factor4s, mean_factorAs, mean_factorBs, mean_factor3Ax4Bs, mean_factor4Ax3Bs], header="mean: 3, 4, A, B, 3Ax4B, 4Ax3B")
