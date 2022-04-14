import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy import signal

data = np.loadtxt("G2s.txt")

def normalize(data):
	mean = np.mean(data)
	ndata = []
	for j in range (0,len(data)):
		ndata.append(data[j]/mean)
	return ndata


def correct_data(data):
	# Gauss filter
	w=128 #filter length in bins (Gaussian Sigma)	
	datagaus=gaussian_filter1d(data,w)  #apply filter	
	datai=data/datagaus #divide filtered waveform to make it flat

	# Pattern correction
	corrector=np.zeros(8)
	for i in range(0,304):     #calculate 8 bin correction pattern, did 32 bin pattern here, enough data
	    corrector[i%8]+=datai[i]*1/38.
	datacor=[]
	for i in range(len(datai)):    #apply 8 bin correction
	    datacor.append(datai[i]/corrector[i%8])
	return datacor


n_1 = correct_data(data[:,0])
n_0 = correct_data(data[:,1])
nm1 = correct_data(data[:,2])
nm2 = correct_data(data[:,3])
nm3 = correct_data(data[:,4])

# RMS weight
rms_1 = np.std(n_1)
rms_0 = np.std(n_0)
rmsm1 = np.std(nm1)
rmsm2 = np.std(nm2)
rmsm3 = np.std(nm3)
n = 1/ ( 1/rms_1 + 1/rms_0 + 1/rmsm1 + 1/rmsm2 + 1/rmsm3 )


#plt.plot(n_1[4800:5200], label="+1")
plt.plot(n_0, label=" 0")
plt.plot(nm1, label="-1")
plt.plot(nm2, label="-2")
plt.plot(nm3, label="-3")
plt.axvline(x=265)
plt.legend()
plt.show()

g2 = []
for i in range (5,len(n_1)-5):
	g2.append( n * ( n_1[i+1]/rms_1 + n_0[i]/rms_0 + nm1[i-1]/rmsm1 + nm2[i-2]/rmsm2 + nm3[i-3]/rmsm3 ))
rms = np.std(g2)
x_g2 = np.arange(int(-0.5*len(g2)),int(0.5*len(g2)),1)

# Notch filter
fs = 625e6 # Sample frequency in Hz
Q  = 300 # Quality fator
# Design notch filter
def denoise(data, freq):
	b,a = b,a = signal.iirnotch(freq,Q,fs)
	newdata = signal.filtfilt(b, a, data)
	return newdata
g2 = denoise(g2, 94.7925e6)
g2 = denoise(g2, 93.6e6)
g2 = denoise(g2, 78.148e6)
g2 = denoise(g2, 101.110e6)

g2 = g2/np.mean(g2)
plt.errorbar(x_g2, g2, yerr=rms, marker="o", linestyle="", label="Sirius 2022")


# lab
g2_lab = np.loadtxt("g2_36nm.txt")
x_lab = np.arange(0,len(g2_lab),1)

plt.plot(x_lab, g2_lab, label="lab measurement")

#delaytest
data = np.loadtxt("delaytest/measurement_00000.fcorr")[20000:30000]
datad = normalize(data)
for i in range (len(datad)):
	datad[i] = (datad[i]-1)/1500 + 1
x_g2 = np.arange(int(-0.5*len(datad)),int(0.5*len(datad)),1)
plt.plot(x_g2, datad, color="grey", label="Cable delay measurement")

plt.xlim(-200,200)
plt.legend()
plt.show()


# FFT analysis
fft = np.abs(np.fft.fft(g2))
x_fft = np.linspace(0,1./1.6,len(fft), endpoint=True)
plt.plot(x_fft, fft)
plt.xlim(0.01,0.625/2)
plt.ylim(0,0.00012)
plt.show()