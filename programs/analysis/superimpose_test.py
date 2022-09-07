import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl  
from scipy.optimize import curve_fit
from scipy.signal import butter, filtfilt, find_peaks
from matplotlib.pyplot import cm
import ephem
import scipy.special as scp

import utilities as uti
import corrections as cor
import geometry as geo

star = "Nunki"

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

# Average over all 4 functions
def average_g2s(cA, cB, c3Ax4B, c4Ax3B):
    g2_avg = np.zeros( len(cA) )
    g2_avg += cA/np.std(cA[0:4500])
    g2_avg += cB/np.std(cB[0:4500])
    g2_avg += c3Ax4B/np.std(c3Ax4B[0:4500])
    g2_avg += c4Ax3B/np.std(c4Ax3B[0:4500])

    g2_avg = g2_avg/np.mean(g2_avg[0:4500])

    return g2_avg

print("Final Analysis of {}".format(star))

# Read in the data (g2 functions and time/baseline parameters)
chAs    = np.loadtxt("g2_functions/{}/ChA.txt".format(star))     #[0:5]
chBs    = np.loadtxt("g2_functions/{}/ChB.txt".format(star))     #[0:5]
ct3s    = np.loadtxt("g2_functions/{}/CT3.txt".format(star))     #[0:5]
ct4s    = np.loadtxt("g2_functions/{}/CT4.txt".format(star))     #[0:5]
c3Ax4Bs = np.loadtxt("g2_functions/{}/c3Ax4B.txt".format(star))  #[0:5]
c4Ax3Bs = np.loadtxt("g2_functions/{}/c4Ax3B.txt".format(star))  #[0:5]
data    = np.loadtxt("g2_functions/{}/baseline.txt".format(star))#[0:5]

# Demo function for initializing x axis and some stuff
demo = chAs[0]
x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)

# Combine all data for channel A and B each for initial parameter estimation and fixing
plt.figure(figsize=(10,9))
plt.subplot(211)
plt.title("Cumulative cross correlation data of {}".format(star))

g2_allA = np.zeros(len(x)); g2_allB = np.zeros(len(x))
g2_all3Ax4B = np.zeros(len(x)); g2_all4Ax3B = np.zeros(len(x))
for i in range (0,len(chAs)):
    g2_allA += chAs[i]/len(chAs)
    g2_allB += chBs[i]/len(chBs)
    g2_all3Ax4B += c3Ax4Bs[i]/len(c3Ax4Bs)
    g2_all4Ax3B += c4Ax3Bs[i]/len(c4Ax3Bs)

# Fit for gaining mu and sigma to fix these parameters
xplot, popt, perr = uti.fit(g2_allA, x, -50, +50)
muA = popt[1]; sigmaA = popt[2]
plt.plot(x, g2_allA, label="3A x 4A", color="blue")
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

xplot, popt, perr = uti.fit(g2_allB, x, -50, +50)
muB = popt[1]; sigmaB = popt[2]
plt.plot(x, g2_allB, label="3B x 4B", color="#32a8a2")
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

xplot, popt, perr = uti.fit(g2_all3Ax4B, x, 65, 165, mu_start=115)
mu3Ax4B = popt[1]; sigma3Ax4B = popt[2]
plt.plot(x, g2_all3Ax4B, label="3A x 4B", color="red")
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

xplot, popt, perr = uti.fit(g2_all4Ax3B, x, 65, 165, mu_start=115)
mu4Ax3B = popt[1]; sigma4Ax3B = popt[2]
plt.plot(x, g2_all4Ax3B, label="4A x 3B", color="orange")
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

plt.legend(); plt.xlim(-100,200); plt.grid()#; plt.tight_layout()
plt.ticklabel_format(useOffset=False)
plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")

plt.tight_layout()
#########################
# Shift all peaks to zero
#########################
plt.subplot(212)

tbin = timebin(muA); g2_allA = shift_bins(g2_allA, tbin)
tbin = timebin(muB); g2_allB = shift_bins(g2_allB, tbin)
tbin = timebin(mu3Ax4B); g2_all3Ax4B = shift_bins(g2_all3Ax4B, tbin)
tbin = timebin(mu4Ax3B); g2_all4Ax3B = shift_bins(g2_all4Ax3B, tbin)

g2_avg = average_g2s(g2_allA, g2_allB, g2_all3Ax4B, g2_all4Ax3B)

# Fit for gaining mu and sigma to fix these parameters
xplot, popt, perr = uti.fit(g2_avg, x, -100, +100)
mu_avg = popt[1]; sigma_avg = popt[2]
print ("Resolution: {:.2f} +/- {:.2f}  (ns)".format(sigma_avg,perr[2]))


plt.plot(x, g2_allA, label="3A x 4A", color="blue")
plt.plot(x, g2_allB, label="3B x 4B", color="#32a8a2")
plt.plot(x, g2_all3Ax4B, label="3A x 4B", color="red")
plt.plot(x, g2_all4Ax3B, label="4A x 3B", color="orange")

plt.plot(x, g2_avg, color="grey", linewidth="4", label="Average")
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--", label="Gaussian fit")

plt.legend(); plt.xlim(-150,150); plt.grid()#; plt.tight_layout()
plt.ticklabel_format(useOffset=False)
plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")

plt.tight_layout()
plt.savefig("images/{}_cumulative.png".format(star))
plt.show()

# Define colormap for plotting all summarized individual g2 functions
cm_sub = np.linspace(1.0, 0.0, len(chAs))
colors = [cm.viridis(x) for x in cm_sub]

# Define total figure which will show individuall g2 functions off cross and auto-correlation
# and also the spatial correlation curve (baseline vs. g2 integral)
bigfigure = plt.figure(figsize=(16,9))
plt.subplot(231)#; bigfigure.patch.set_facecolor("blue")
plt.subplot(233)#; bigfigure.patch.set_facecolor("red")
intsA = []; dintsA = []; times = []
intsB = []; dintsB = []
ints3Ax4B = []; dints3Ax4B = []
ints4Ax3B = []; dints4Ax3B = []

ints_fixed = []; dints_fixed = []
ints_free  = []; dints_free = []

# initialize CT3 and CT4 sum arrays and cleaned arrays
chA_clean = []
chB_clean = []
ct3_clean = []
ct4_clean = []
ct3_sum = np.zeros(len(ct3s[0]))
ct4_sum = np.zeros(len(ct4s[0]))
ticks = []
ffts = []

# loop over every g2 function chunks
for i in range(0,len(chAs)):
    chA = chAs[i]
    chB = chBs[i]
    ct3 = ct3s[i]
    ct4 = ct4s[i]
    c3Ax4B = c3Ax4Bs[i]
    c4Ax3B = c4Ax3Bs[i]

    # Do some more data cleaning, e.g. lowpass filters
    chA = cor.lowpass(chA)
    chB = cor.lowpass(chB)
    ct3 = cor.lowpass(ct3)
    ct4 = cor.lowpass(ct4)
    c3Ax4B = cor.lowpass(c3Ax4B)
    c4Ax3B = cor.lowpass(c4Ax3B)

    # more data cleaning with notch filter for higher frequencies
    freq3 = [50, 90, 125, 150]
    for j in range(len(freq3)):
        ct3 = cor.notch(ct3, freq3[j]*1e6, 80)
    freq4 = [50, 90, 110, 130, 150, 250]
    for j in range(len(freq4)):
        ct4 = cor.notch(ct4, freq4[j]*1e6, 80)
    freqB = [90, 150, 250]
    for j in range(len(freqB)):
        chB = cor.notch(chB, freqB[j]*1e6, 80)
    freqA = [90]
    for j in range(len(freqA)):
        chA = cor.notch(chA, freqA[j]*1e6, 80)
    freqAB = [90,250]
    for j in range(len(freqAB)):
        c3Ax4B = cor.notch(c3Ax4B, freqAB[j]*1e6, 80)
    freqBA = [90]
    for j in range(len(freqBA)):
        c4Ax3B = cor.notch(c4Ax3B, freqBA[j]*1e6, 80)

    # save cleaned data
    chA_clean.append(chA)
    chB_clean.append(chB)
    ct3_clean.append(ct3)
    ct4_clean.append(ct4)
    # TODO: Save cleaned data for x correlations

    #########################
    # Shift all peaks to zero
    #########################
    tbin = timebin(muA); chA = shift_bins(chA, tbin)
    tbin = timebin(muB); chB = shift_bins(chB, tbin)
    tbin = timebin(mu3Ax4B); c3Ax4B = shift_bins(c3Ax4B, tbin)
    tbin = timebin(mu4Ax3B); c4Ax3B = shift_bins(c4Ax3B, tbin)


    # for autocorrelations of CT3 and CT4 we also average over all acquised data and sum all up
    rms = np.std(ct3[0:4500])
    g2_for_averaging = ct3/rms
    ct3_sum += g2_for_averaging

    rms = np.std(ct4[0:4500])
    g2_for_averaging = ct4/rms
    ct4_sum += g2_for_averaging

    # Averaged cross correlations
    avg = average_g2s(chA, chB, c3Ax4B, c4Ax3B)
    # additional data cleaning
    freq_avg = [50,110,130,144.4,150,230]
    for j in range(len(freq_avg)):
        avg = cor.notch(avg, freq_avg[j]*1e6, 80)


    # Fit with fixed mu and sigma
    xplotf, popt_avg, perr_avg = uti.fit_fixed(avg, x, -100, 100, mu_avg, sigma_avg)
    Int, dInt = uti.integral_fixed(popt_avg, perr_avg, sigma_avg)
    ints_fixed.append(1e6*Int); dints_fixed.append(1e6*dInt)# in femtoseconds
    # Fit with free mu and sigma
    xplotf, popt_avg_free, perr_avg_free = uti.fit(avg, x, -100, 100)
    Int, dInt = uti.integral(popt_avg_free, perr_avg_free)
    ints_free.append(1e6*Int); dints_free.append(1e6*dInt)# in femtoseconds

    # Check acquisition time of original data
    timestring = ephem.Date(data[:,0][i])
    print("{}".format(i), timestring, Int, dInt)

    # FFT check
    fft = np.abs(np.fft.fft(avg-1))
    ffts.append(fft)
    
    # Subplot for all cross correlations
    the_shift = (len(chAs)-i-1)*2e-6
    ticks.append(1.+the_shift)
    plt.subplot(121)
    plt.errorbar(x, chA    +the_shift,    yerr=0, linestyle="-", color = "blue", alpha=0.3)
    plt.errorbar(x, c3Ax4B +the_shift, yerr=0, linestyle="-", color = "red", alpha=0.3)
    plt.errorbar(x, c4Ax3B +the_shift, yerr=0, linestyle="-", color = "orange", alpha=0.3)
    plt.errorbar(x, chB    +the_shift,    yerr=0, linestyle="-", color = "#32a8a2", alpha=0.3)
    plt.errorbar(x, avg    +the_shift,    yerr=0, linestyle="-", color = colors[i], linewidth=3, label=timestring)
    plt.text(x=20, y=1+the_shift+0.7e-6, s=timestring, color=colors[i])
    
    plt.plot(xplotf,  uti.gauss_shifted(x=xplotf,  a=popt_avg[0],      mu=mu_avg,          sigma=sigma_avg,         shift=i, inverse=True, ntotal=len(chAs)), color="black", linestyle="--", zorder=4)
    #plt.plot(xplotf,  uti.gauss_shifted(x=xplotf,  a=popt_avg_free[0], mu=popt_avg_free[1], sigma=popt_avg_free[2], shift=i, inverse=True, ntotal=len(chAs)), color="red", linestyle="--", zorder=4, alpha=0.4)

    # Subplot for the auto correlations, tbc
    plt.subplot(224)
    plt.errorbar(x, ct3+i*0e-6, yerr=0, marker=".", linestyle="--", color = colors[i], alpha=0.6)
    plt.errorbar(x, ct4+i*0e-6+1e-5, yerr=0, marker=".", linestyle="--", color = colors[i], alpha=0.6)
    #plt.errorbar(x, ct4+i*0e-6+1e-5, yerr=0, marker=".", linestyle="--", label=timestring, color = colors[i], alpha=0.6)

# Finalize analysis of integrated autocorrelations and plot it to the auto correlation plot
# Renormalize ct3 and ct4 autocorrelation data
ct3_sum = ct3_sum/np.mean(ct3_sum[0:4500])
ct4_sum = ct4_sum/np.mean(ct4_sum[0:4500])
plt.subplot(224)
plt.errorbar(x, ct3_sum, yerr=0, marker=".", linestyle="--", color = "black", linewidth=2, alpha=1)
plt.errorbar(x, ct4_sum+1e-5, yerr=0, marker=".", linestyle="--", color = "black", linewidth=2, alpha=1)

np.savetxt("autocorrelation_{}.txt".format(star), np.c_[ct3_sum, ct4_sum])

# Figure stuff
def cc_plots(xlims):
    plt.grid()
    plt.ticklabel_format(useOffset=False)
    plt.xlabel("Time difference (ns)")
    plt.ylabel("$g^{(2)}$")
    #plt.legend(loc="upper right")
    plt.xlim(xlims[0],xlims[1])
    #plt.tight_layout()

plt.subplot(121); plt.title("Cross correlations of {}".format(star)); cc_plots((-150,150))
plt.yticks(np.arange(1,1+2e-6*len(chAs),2e-6))

plt.subplot(224); plt.title("Auto correlations of {}".format(star)); cc_plots((0,200))

# store cleaned data
np.savetxt("g2_functions/{}/ChA_clean.txt".format(star), np.c_[chA_clean], header="{} Channel A cleaned".format(star) )
np.savetxt("g2_functions/{}/ChB_clean.txt".format(star), np.c_[chB_clean], header="{} Channel B cleaned".format(star) )
np.savetxt("g2_functions/{}/CT3_clean.txt".format(star), np.c_[ct3_clean], header="{} CT3 cleaned".format(star) )
np.savetxt("g2_functions/{}/CT4_clean.txt".format(star), np.c_[ct4_clean], header="{} CT4 cleaned".format(star) )

#### making SC plot (spatial coherence) via integral data ####
xplot = np.arange(0.1,300,0.1)
plt.subplot(222)

# get baselines for x axes
baselines = data[:,1]
dbaselines = data[:,2]

# Average over all 4 cross correlations
ints_avg, dints_avg = uti.weighted_avg(intsA,dintsA, intsB,dintsB, ints3Ax4B,dints3Ax4B, ints4Ax3B, dints4Ax3B)

# Add zero-baseline
baselines  = np.append(baselines,0+1e-6)
dbaselines = np.append(dbaselines,0)
ints_fixed = np.append(ints_fixed,41.28)
dints_fixed= np.append(dints_fixed,7.02)

# Calculate SC fit and errorbars for the averaged signal
poptavg, pcov = curve_fit(uti.spatial_coherence, baselines, ints_fixed, sigma=dints_fixed, p0=[25, 2.2e-9])
perravg = np.sqrt(np.diag(pcov))

# Calculate SC fit and errorbars for the averaged signal
#poptavg_free, pcov = curve_fit(uti.spatial_coherence, baselines, ints_free, sigma=dints_free, p0=[25, 2.2e-9])
#perravg_free = np.sqrt(np.diag(pcov))

###############
# Try with ods
# Model object
from scipy import odr
sc_model = odr.Model(uti.spatial_coherence_odr)
# RealData object
rdata = odr.RealData( baselines[:-1], ints_fixed[:-1], sx=dbaselines[:-1], sy=dints_fixed[:-1] )
# Set up ODR with model and data
odr = odr.ODR(rdata, sc_model, beta0=[25,2.2e-9])
# Run the regression
out = odr.run()
# Fit parameters
popt_odr = out.beta
perr_odr = out.sd_beta
###############

deltas_sc_avg = []
for i in xplot:
    deltas_sc_avg.append( np.abs(uti.delta_spatial_coherence(x=i, A=poptavg[0],dA=perravg[0], phi=poptavg[1], dphi=perravg[1])) )
print ("Angular diameter AVG (fixed)   : {:.2f} +/- {:.2f} (mas)".format(uti.rad2mas(poptavg[1]),   uti.rad2mas(perravg[1])))
#print ("Angular diameter AVG (free)    : {:.2f} +/- {:.2f} (mas)".format(uti.rad2mas(poptavg_free[1]),   uti.rad2mas(perravg_free[1])))

print ("Angular diameter AVG (free,odr): {:.2f} +/- {:.2f} (mas)".format(uti.rad2mas(popt_odr[1]),   uti.rad2mas(perr_odr[1])))

# plot datapoints in SC plot and fit to all points
plt.errorbar(x=0, y=41.28, yerr=7.02, marker="o", color="black")
for i in range (0,len(baselines)-1):
    plt.errorbar(baselines[i], ints_fixed[i], yerr=dints_fixed[i], xerr=dbaselines[i], marker="o", linestyle="", color=colors[i])
    #plt.text(baselines[i]+1,ints_fixed[i]+0.5,ephem.Date(data[:,0][i]), color=colors[i])
#plt.errorbar(baselines, ints_free,  yerr=dints_free,  marker="o", linestyle="", color="red", markersize=4, alpha=0.4)
plt.plot(xplot, uti.spatial_coherence(xplot,*poptavg),   label="Fixed parameters", color="red", linewidth=2)
plt.plot(xplot, uti.spatial_coherence(xplot,*popt_odr),   label="ODR (no zero baseline)", color="orange", linewidth=2)
#plt.plot(xplot, uti.spatial_coherence(xplot,*poptavg_free),   label="Free parameters", color="red", linewidth=2, alpha=0.4)

#plt.fill_between(xplot, spatial_coherence(xplot,*popt) + deltas_sc, spatial_coherence(xplot,*popt) - deltas_sc, color="red", alpha=0.2)

plt.xlim(-15,250); plt.ylim(0,50)
plt.xlabel("Baseline (m)"); plt.ylabel("Coherence time (fs)")
plt.legend(loc="upper right")
#plt.tight_layout()
#plt.savefig("{}_crosscorrelation.png".format(star))
plt.savefig("images/{}_sc.png".format(star))
plt.show()

#xfft = np.linspace(0,1./1.6,len(ffts[0]), endpoint=True)
#for i in range (0,len(baselines)):
#    plt.plot(xfft, ffts[i], color=colors[i])
#plt.show()