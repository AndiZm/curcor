import numpy as np
import matplotlib.pyplot as plt
import corrections as cor
from scipy.signal import find_peaks
import utilities as uti

#######
# The purpose of this program is to get the most out of the noisy autocorrelations.
# Therefore the more or less okayish Acrux autocorrelation data are used to find the exact cable delays.
# The Shaula of both CT3 and CT4 are then overlayed to get a statistical more significant signal.
#######

# Get the timebin shift of the specific measurement from the time difference
def timebin(tdiff):
    return int(1.0* np.floor((tdiff+0.8)/1.6))
def shift_bins(data, binshift):
    # A negative number means shifting to the right, so scrapping the right end of the array to the beginning
    if binshift <= 0:
        for j in range (binshift,0):
            data = np.insert(data,0,data[-1])
            data = np.delete(data, -1)
    # A positive number means shifting to the left, so scrapping the beginning of the array to the end
    if binshift > 0:
        for j in range (0, binshift):
            data = np.append(data,data[0])
            data = np.delete(data, 0)
    return data

##############################
# Acrux data for calibration #
##############################
data = np.loadtxt("autocorrelation_Acrux.txt")
ct3 = data[:,0]
ct4 = data[:,1]

# Initial corrections
ct3 = cor.lowpass(ct3)
ct4 = cor.lowpass(ct4)
# Cut frequencies
freq3 = [92.8, 97.7, 130]
for j in range(len(freq3)):
    ct3 = cor.notch(ct3, freq3[j]*1e6, 80)

x = np.arange(-1.6*len(ct3)//2,+1.6*len(ct3)//2,1.6)

xfft = np.linspace(0,1./1.6,len(ct3[0:4500]),endpoint=True)
fft3 = np.abs(np.fft.fft(ct3[0:4500]-1))
fft4 = np.abs(np.fft.fft(ct4[0:4500]-1))
# Find peaks in FFT
peaks_4, _ = find_peaks(fft4, height=1e-6)
peaks_ghz4 = []; peaks_4_sur = []
for i in peaks_4:
	if xfft[i] > 0.12 and xfft[i] < 0.32:
		peaks_ghz4.append(xfft[i])
		peaks_4_sur.append(i)
# Cut more frequencies
freq4 = peaks_ghz4
for j in range(len(freq4)):
    ct4 = cor.notch(ct4, freq4[j]*1e6, 80)

# Fit gauss to autocorrelations
xplot, popt3, perr3 = uti.fit(ct3, x, 80,140, mu_start=120)
xplot, popt4, perr4 = uti.fit(ct4, x, 80,140, mu_start=120)

shift_ct3 = popt3[1]
shift_ct4 = popt4[1]
print ("Shift CT3: {:.2f}  ns".format(popt3[1]))
print ("Shift CT4: {:.2f}  ns".format(popt4[1]))



plt.subplot(211)
plt.plot(x,ct3)
plt.plot(x,ct4)
plt.plot(xplot,uti.gauss(xplot,*popt3), color="black")
plt.plot(xplot,uti.gauss(xplot,*popt4), color="black")
plt.xlim(-100,300)

plt.subplot(212)
plt.plot(xfft, fft3)
plt.plot(xfft, fft4)
plt.plot(peaks_ghz4, fft4[peaks_4_sur], "o")

plt.show()


# Shift g2s to zero
tbin = timebin(popt3[1]); ct3 = shift_bins(ct3, tbin)
tbin = timebin(popt4[1]); ct4 = shift_bins(ct4, tbin)
# Fit gauss to autocorrelations
xplot, popt3, perr3 = uti.fit(ct3, x, -50,50, mu_start=0)
xplot, popt4, perr4 = uti.fit(ct4, x, -50,50, mu_start=0)

# Average over all 2 functions
def average_g2s(c3, c4):
    g2_avg = np.zeros( len(c3) )
    g2_avg += c3/np.std(c3[0:4500])
    g2_avg += c4/np.std(c4[0:4500])

    g2_avg = g2_avg/np.mean(g2_avg[0:4500])

    return g2_avg
avg = average_g2s(ct3, ct4)

plt.subplot(211)
plt.plot(x,ct3)
plt.plot(x,ct4)
plt.plot(x, avg, color="grey", linewidth=4)
plt.plot(xplot,uti.gauss(xplot,*popt3), color="black")
plt.plot(xplot,uti.gauss(xplot,*popt4), color="black")
plt.xlim(-200,200)
plt.show()


#################################
# Apply to data for calibration #
#################################
data = np.loadtxt("autocorrelation_Shaula.txt")
ct3 = data[:,0]
ct4 = data[:,1]
# Initial corrections
ct3 = cor.lowpass(ct3)
ct4 = cor.lowpass(ct4)
# Cut frequencies
freq3 = [90, 110, 120, 130]
freq4 = [90, 125]
for j in range(len(freq3)):
    ct3 = cor.notch(ct3, freq3[j]*1e6, 80)
for j in range(len(freq4)):
    ct4 = cor.notch(ct4, freq4[j]*1e6, 80)

fft3 = np.abs(np.fft.fft(ct3[0:4500]-1))
fft4 = np.abs(np.fft.fft(ct4[0:4500]-1))

plt.subplot(211)
plt.title("Shaula")
plt.plot(x,ct3)
plt.plot(x,ct4)
plt.xlim(-100,300)

plt.subplot(212)
plt.plot(xfft,fft3)
plt.plot(xfft,fft4)

plt.show()


# Shift g2s to zero
tbin = timebin(shift_ct3); ct3 = shift_bins(ct3, tbin)
tbin = timebin(shift_ct4); ct4 = shift_bins(ct4, tbin)
avg = average_g2s(ct3, ct4)

# check frequencies around peak
fft3 = np.abs(np.fft.fft(ct3[4950:5200]-1))
fft4 = np.abs(np.fft.fft(ct4[4950:5200]-1))
xfft = np.linspace(0,1/1.6,len(fft3), endpoint=True)

plt.subplot(211)
plt.plot(x,ct3)
plt.plot(x,ct4)
plt.plot(x,avg, color="black", linewidth=3)
#plt.xlim(-200,200)

plt.subplot(212)
plt.plot(xfft, fft3)
plt.plot(xfft, fft4)

plt.show()