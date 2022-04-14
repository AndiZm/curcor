import numpy as np
import matplotlib.pyplot as plt
import corrections as cor

datac = np.loadtxt("g2_con.txt")
datan = np.loadtxt("g2_new.txt")

len_data = len(datan[:,0])

n_N = 0
isum_uncorr = np.zeros(len_data)
isum_corr   = np.zeros(len_data)

for i in range (0,5):
	data = cor.gauss_fit_filter(datan[:,i])
	
	rms = np.std(data)
	n_N += 1./rms
	for j in range(5,len_data-5):
		isum_uncorr[j] += data[j]     / rms
		#isum_corr[j]   += data[j+3-i] / rms
		isum_corr[j]   += data[j+i-3] / rms

n = 1./n_N
for j in range (5,len_data-5):
	isum_uncorr[j] *= n
	isum_corr[j]   *= n

# delaytest
delay = np.loadtxt("../delaytest/measurement_00000.fcorr")
delay = cor.pattern_correction(delay)
for j in range (0,len(delay)):
	delay[j] = (delay[j]-1) / 1500 + 1


meas = np.loadtxt("g2_36nm.txt")
x = np.arange(25000,25000+len(meas),1)

plt.plot(isum_uncorr, color="grey", alpha=0.9, label="g2 (uncorrected)")
plt.plot(isum_corr, color="blue", label="g2 (path-delay corrected)")
plt.plot(x,meas)
plt.plot(delay, color="orange" , linestyle="--", label="Delay measurement (scaled)")
plt.xlim(24500,25500)
plt.ylim(0.999999,1.000001)
plt.legend()
plt.show()