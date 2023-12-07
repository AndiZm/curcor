import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
from scipy import fftpack

def db2lin(dbval):
    return 10**(dbval/20)

data0=np.loadtxt("airborne5.txt",delimiter=",")
data1=np.loadtxt("airborne10.txt",delimiter=",")
data2=np.loadtxt("hyperflex13.txt",delimiter=",")
data3=np.loadtxt("aircom15.txt",delimiter=",")
data4=np.loadtxt("lcf12-50j.txt",delimiter=",")

plt.plot(data0[:,0],(data0[:,1]/100.)*10,label='Airborne5   (5.0 mm, 0.2kg) 10m')
plt.plot(data0[:,0],(data0[:,1]/100.)*40,label='Airborne5   (5.0 mm, 0.9kg) 40m')
plt.plot(data1[:,0],(data1[:,1]/100.)*40,label='Airborne10  (10.3mm, 2.8kg) 40m')
plt.plot(data2[:,0],(data2[:,1]/100.)*40,label='Hyperflex13 (12.7mm, 7.2kg) 40m')
plt.plot(data3[:,0],(data3[:,1]/100.)*40,label='Aircom15    (14.0mm, 6.6kg) 40m')
plt.plot(data4[:,0],(data4[:,1]/100.)*40,label='LCF12-50J   (15.8mm, 7.2kg) 40m')
plt.xlim(0,500)
plt.ylim(0,10)
plt.xlabel("Frequency [MHz]")
plt.ylabel("Attenuation [dB]")
plt.legend(loc='upper left')
plt.tight_layout()
plt.savefig("cable_attenuation.png")
#plt.show()

plt.clf()

data5=np.loadtxt("pulseshape.txt",delimiter=",")
plt.plot(data5[:,0],(data5[:,1]))
plt.xlim(-10,50)
plt.xlabel("Time [ns]")
plt.ylabel("Rel. Amplitude")
plt.tight_layout()
plt.savefig("pulseshape.png")
#plt.show()

plt.clf()

x=data5[:,0]
y=data5[:,1]


sig_fft = fftpack.fft(y)
power = np.abs(sig_fft)**2
# The corresponding frequencies
sample_freq = fftpack.fftfreq(y.size, d=0.001)
plt.plot(sample_freq, power)
plt.xlabel('Frequency [Hz]')
plt.ylabel('Power')
#plt.show()

plt.clf()


x0=data0[:,0]
y0raw=40*data0[:,1]/100
y0=db2lin(y0raw)
f0 = interpolate.interp1d(x0,y0,fill_value='extrapolate')

x1=data1[:,0]
y1raw=40*data1[:,1]/100
y1=db2lin(y1raw)
f1 = interpolate.interp1d(x1,y1,fill_value='extrapolate')

x4=data4[:,0]
y4raw=40*data4[:,1]/100
y4=db2lin(y4raw)
f4 = interpolate.interp1d(x4,y4,fill_value='extrapolate')

ffreq=np.abs(sample_freq)

inty0=f0(ffreq)
inty1=f1(ffreq)
inty4=f4(ffreq)

fft_a5 = sig_fft.copy()
fft_a5 = fft_a5/inty0
filtered_a5_sig = fftpack.ifft(fft_a5)

fft_a10 = sig_fft.copy()
fft_a10 = fft_a10/inty1
filtered_a10_sig = fftpack.ifft(fft_a10)

fft_lcf = sig_fft.copy()
fft_lcf = fft_lcf/inty4
filtered_lcf_sig = fftpack.ifft(fft_lcf)

plt.clf()
plt.plot(x, y, label='Original signal')
plt.plot(x, filtered_a5_sig, label='Ariborne5')
plt.plot(x, filtered_a10_sig, label='Ariborne10')
plt.plot(x, filtered_lcf_sig, label='LCF12-50J')
plt.xlabel('Time [ns]')
plt.ylabel('Rel. Amplitude')
plt.xlim(-10,40)
plt.legend(loc='best')
plt.tight_layout()
plt.savefig("filtered.png")
plt.show()