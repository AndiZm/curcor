import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as ssi
from matplotlib.pyplot import cm

import utilities as uti
import corrections as cor

ct3 = np.loadtxt("g2_functions/Shaula/CT3.txt")
ct4 = np.loadtxt("g2_functions/Shaula/CT4.txt")
x = np.arange(-1.6*len(ct3[0])//2,+1.6*len(ct3[0])//2,1.6)

# Define colormap for plotting all summarized individual g2 functions
cm_sub = np.linspace(1.0, 0.0, len(ct3))
colors = [cm.viridis(x) for x in cm_sub]


##########################
# Do everything with CT3 #
##########################
rms_thres = 1.7e-6
rmss = []
g2_avg = np.zeros(len(ct3[0]))

plt.subplot(211)

for i in range (0,len(ct3)):
    # get specific g2 function
    g2 = ct3[i]
    # first the usual lowpass
    g2 = cor.lowpass(g2)
    # fft for frequency analysis
    xfft, fft = uti.fourier(g2[5300:])
    # find prominent peaks in Fourier transform
    peaks, _ = ssi.find_peaks(fft, prominence=0.00008, width=(1,5))
    # remove peaks in unwanted frequency regions from the list
    peaks_new = []
    for j in peaks:
        if xfft[j] > 0.04 and xfft[j] < 0.625/2:
            peaks_new.append(j)

    #plt.subplot(211)
    #plt.plot(g2, color="blue", alpha=0.5)
    #plt.subplot(212)    
    #plt.plot(xfft, fft, color="blue")
    #plt.plot(xfft[peaks_new], fft[peaks_new], "o")

    # clear g2 function from the peaks
    freqs = xfft[peaks_new]
    for j in range(len(freqs)):
        g2 = cor.notch(g2, freqs[j]*1e9, 80)
    #g2 = cor.notch(g2, 0.104*1e9, 80)

    #xfft, fft = uti.fourier(g2[5300:])
    #plt.subplot(211)
    #plt.plot(g2, color="red")
    #plt.subplot(212)    
    #plt.plot(xfft, fft, color="red")
#
    #plt.show()

    #xfft, fft = uti.fourier(g2[5020:5225])
    #plt.plot(xfft, fft)
    #plt.show()

    # Average g2 functions
    rms = np.std(g2[5020:5300])
    if rms < rms_thres:
        plt.plot(x, g2, color=colors[i])
        g2_avg += g2/rms

    rmss.append(rms)

g2_avg = g2_avg/np.mean(g2_avg[0:4500])
plt.plot(x,g2_avg, color="black", linewidth=4)

plt.subplot(212)
plt.plot(rmss, "o--")
plt.axhline(y = rms_thres, linestyle="--", color="grey")
plt.show()

g2_ct3 = g2_avg

##########################
# Do everything with CT4 #
##########################
rms_thres = 1.7e-6
rmss = []
g2_avg = np.zeros(len(ct3[0]))

plt.subplot(211)

for i in range (0,len(ct3)):
    # get specific g2 function
    g2 = ct4[i]
    # first the usual lowpass
    g2 = cor.lowpass(g2)
    # fft for frequency analysis
    xfft, fft = uti.fourier(g2[5300:])
    # find prominent peaks in Fourier transform
    peaks, _ = ssi.find_peaks(fft, prominence=0.00008, width=(1,5))
    # remove peaks in unwanted frequency regions from the list
    peaks_new = []
    for j in peaks:
        if xfft[j] > 0.04 and xfft[j] < 0.625/2:
            peaks_new.append(j)

    #plt.subplot(211)
    #plt.plot(g2, color="blue", alpha=0.5)
    #plt.subplot(212)    
    #plt.plot(xfft, fft, color="blue")
    #plt.plot(xfft[peaks_new], fft[peaks_new], "o")

    # clear g2 function from the peaks
    freqs = xfft[peaks_new]
    for j in range(len(freqs)):
        g2 = cor.notch(g2, freqs[j]*1e9, 80)
    #g2 = cor.notch(g2, 0.104*1e9, 80)

    #xfft, fft = uti.fourier(g2[5300:])
    #plt.subplot(211)
    #plt.plot(g2, color="red")
    #plt.subplot(212)    
    #plt.plot(xfft, fft, color="red")
#
    #plt.show()

    #xfft, fft = uti.fourier(g2[5020:5225])
    #plt.plot(xfft, fft)
    #plt.show()

    # Average g2 functions
    rms = np.std(g2[5020:5300])
    if rms < rms_thres:
        plt.plot(x, g2, color=colors[i])
        g2_avg += g2/rms

    rmss.append(rms)

g2_avg = g2_avg/np.mean(g2_avg[0:4500])
plt.plot(x,g2_avg, color="black", linewidth=4)

plt.subplot(212)
plt.plot(rmss, "o--")
plt.axhline(y = rms_thres, linestyle="--", color="grey")
plt.show()

g2_ct4 = g2_avg


###########
# Combine #
###########
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

tbin = timebin(118.62); g2_ct3 = shift_bins(g2_ct3, tbin)
tbin = timebin(114.23); g2_ct4 = shift_bins(g2_ct4, tbin)

g2_avg = g2_ct3/np.std(g2_ct3[5020:5300]) + g2_ct4/np.std(g2_ct4[5020:5300])
g2_avg = g2_avg/np.mean(g2_avg[0:4500])

# Fit
xplot, popt, perr = uti.fit(g2_avg, x, -30, +30)
Int, dInt = uti.integral(popt, perr)
print ("Coherence time: {:.2f} +/- {:.2f}  (fs)".format(1e6*Int, 1e6*dInt))

#plt.plot(x, g2_ct3)
#plt.plot(x, g2_ct4)
plt.plot(x, g2_avg, color="black", linewidth=1)
plt.plot(xplot, uti.gauss(xplot, *popt), color="red", linestyle="--")
plt.xlabel("Time difference (ns)")
plt.ylabel("$g^{(2)}$")
plt.title("Shaula auto correlation")
plt.grid()
plt.xlim(-150,150)
plt.show()