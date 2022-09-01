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

star = "Shaula"

print("Final Analysis of {}".format(star))

# Read in the data (g2 functions and time/baseline parameters)
chAs  = np.loadtxt("g2_functions/{}/ChA.txt".format(star))
chBs  = np.loadtxt("g2_functions/{}/ChB.txt".format(star))
ct3s  = np.loadtxt("g2_functions/{}/CT3.txt".format(star))
ct4s  = np.loadtxt("g2_functions/{}/CT4.txt".format(star))
c3Ax4Bs = np.loadtxt("g2_functions/{}/c3Ax4B.txt".format(star))
c4Ax3Bs = np.loadtxt("g2_functions/{}/c4Ax3B.txt".format(star))
data  = np.loadtxt("g2_functions/{}/baseline.txt".format(star))

# Demo function for initializing x axis and some stuff
demo = chAs[0]
x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)

# Combine all data for channel A and B each for initial parameter estimation and fixing
plt.figure(figsize=(10,6))
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

# Define colormap for plotting all summarized individual g2 functions
cm_sub = np.linspace(1.0, 0.0, len(chAs))
colors = [cm.viridis(x) for x in cm_sub]

# Define total figure which will show individuall g2 functions off cross and auto-correlation
# and also the spatial correlation curve (baseline vs. g2 integral)
plt.figure(figsize=(18,12))
plt.subplot(221)
intsA = []; dintsA = []; times = []
intsB = []; dintsB = []
ints3Ax4B = []; dints3Ax4B = []
ints4Ax3B = []; dints4Ax3B = []

# initialize CT3 and CT4 sum arrays and cleaned arrays
chA_clean = []
chB_clean = []
ct3_clean = []
ct4_clean = []
ct3_sum = np.zeros(len(ct3s[0]))
ct4_sum = np.zeros(len(ct4s[0]))

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
    # TODO: Add data cleaning for x correlations

    # save cleaned data
    chA_clean.append(chA)
    chB_clean.append(chB)
    ct3_clean.append(ct3)
    ct4_clean.append(ct4)
    # TODO: Save cleaned data for x correlations

    # Apply gaussian fits to cross correlations, keep mu and sigma fixed
    xplotf, poptA, perrA = uti.fit_fixed(chA, x, -100, 100, muA,sigmaA)
    Int, dInt = uti.integral_fixed(poptA, perrA, sigmaA)
    intsA.append(1e6*Int); dintsA.append(1e6*dInt)# in femtoseconds

    xplotf, poptB, perrB = uti.fit_fixed(chB, x, -100, 100, muB,sigmaB)
    Int, dInt = uti.integral_fixed(poptB, perrB, sigmaB)
    intsB.append(1e6*Int); dintsB.append(1e6*dInt)# in femtoseconds

    xplotf, popt3Ax4B, perr3Ax4B = uti.fit_fixed(c3Ax4B, x, 65, 265, mu3Ax4B,sigma3Ax4B)
    Int, dInt = uti.integral_fixed(popt3Ax4B, perr3Ax4B, sigma3Ax4B)
    ints3Ax4B.append(1e6*Int); dints3Ax4B.append(1e6*dInt)# in femtoseconds

    xplotf, popt4Ax3B, perr4Ax3B = uti.fit_fixed(c4Ax3B, x, 65, 265, mu4Ax3B,sigma4Ax3B)
    Int, dInt = uti.integral_fixed(popt4Ax3B, perr4Ax3B, sigma4Ax3B)
    ints4Ax3B.append(1e6*Int); dints4Ax3B.append(1e6*dInt)# in femtoseconds

    # for autocorrelations of CT3 and CT4 we also average over all acquised data and sum all up
    rms = np.std(ct3[0:4500])
    g2_for_averaging = ct3/rms
    ct3_sum += g2_for_averaging

    rms = np.std(ct4[0:4500])
    g2_for_averaging = ct4/rms
    ct4_sum += g2_for_averaging

    # Check acquisition time of original data
    timestring = ephem.Date(data[:,0][i])
    print("{}".format(i), timestring, Int, dInt)
    
    # Subplot for the cross correlations
    plt.subplot(221)
    plt.errorbar(x, chA+i*2e-6, yerr=0, marker=".", linestyle="--", label=timestring, color = colors[i], alpha=0.6)
    #plt.errorbar(x, chB+i*2e-6, yerr=0, marker=".", linestyle="--", label=timestring, color = "black", alpha=0.6)
    plt.plot(xplotf, uti.gauss_shifted(x=xplotf, a=poptA[0], mu=muA, sigma=sigmaA, shift=i), color="black", linestyle="-")

    # Subplot for the auto correlations
    plt.subplot(223)
    plt.errorbar(x, ct4+i*0e-6, yerr=0, marker=".", linestyle="--", label=timestring, color = colors[i], alpha=0.6)
    #plt.errorbar(x, ct4+i*0e-6+1e-5, yerr=0, marker=".", linestyle="--", label=timestring, color = colors[i], alpha=0.6)

# Finalize analysis of integrated autocorrelations and plot it to the auto correlation plot
# Renormalize ct3 and ct4 autocorrelation data
ct3_sum = ct3_sum/np.mean(ct3_sum[0:4500])
ct4_sum = ct4_sum/np.mean(ct4_sum[0:4500])
plt.subplot(223)
#plt.errorbar(x, ct3_sum, yerr=0, marker=".", linestyle="--", label=timestring, color = "black", linewidth=2, alpha=1)
plt.errorbar(x, ct4_sum+0e-5, yerr=0, marker=".", linestyle="--", label='sum', color = "black", linewidth=2, alpha=1)

# Figure stuff
plt.subplot(221)
plt.title("Cross correlations on {}".format(star))
plt.grid()
plt.ticklabel_format(useOffset=False)
plt.xlabel("Time difference (ns)")
plt.ylabel("$g^{(2)}$")
plt.legend(loc="lower right")
plt.xlim(-300,300)
plt.tight_layout()
plt.subplot(223)
plt.title("Auto correlations on {}".format(star))
plt.grid()
plt.xlabel("Time")
plt.ylabel("$g^{(2)}$")
plt.legend(loc='right')
plt.xlim(80,160)

# store cleaned data
np.savetxt("g2_functions/{}/ChA_clean.txt".format(star), np.c_[chA_clean], header="{} Channel A cleaned".format(star) )
np.savetxt("g2_functions/{}/ChB_clean.txt".format(star), np.c_[chB_clean], header="{} Channel B cleaned".format(star) )
np.savetxt("g2_functions/{}/CT3_clean.txt".format(star), np.c_[ct3_clean], header="{} CT3 cleaned".format(star) )
np.savetxt("g2_functions/{}/CT4_clean.txt".format(star), np.c_[ct4_clean], header="{} CT4 cleaned".format(star) )

#### making SC plot (spatial coherence) via integral data ####
xplot = np.arange(0.1,300,0.1)
plt.subplot(122)

# get baselines for x axes
baselines = data[:,1]

# Average over all 4 cross correlations
ints_avg, dints_avg = uti.weighted_avg(intsA,dintsA, intsB,dintsB, ints3Ax4B,dints3Ax4B, ints4Ax3B, dints4Ax3B)

# calculate SC fit and errorbars
poptA, pcov = curve_fit(uti.spatial_coherence, baselines, intsA, sigma=dintsA, p0=[25, 2.2e-9])
perrA = np.sqrt(np.diag(pcov))

poptB, pcov = curve_fit(uti.spatial_coherence, baselines, intsB, sigma=dintsB, p0=[25, 2.2e-9])
perrB = np.sqrt(np.diag(pcov))

deltas_scA = []
deltas_scB = []
for i in xplot:
    deltas_scA.append( np.abs(uti.delta_spatial_coherence(x=i, A=poptA[0],dA=perrA[0], phi=poptA[1], dphi=perrA[1])) )
    deltas_scB.append( np.abs(uti.delta_spatial_coherence(x=i, A=poptB[0],dA=perrB[0], phi=poptB[1], dphi=perrB[1])) )
print ("Angular diameter Ch A: {:.2f} +/- {:.2f} (mas): ".format(uti.rad2mas(poptA[1]), uti.rad2mas(perrA[1])))
print ("Angular diameter Ch B: {:.2f} +/- {:.2f} (mas): ".format(uti.rad2mas(poptB[1]), uti.rad2mas(perrB[1])))

# plot datapoints in SC plot and fit to all points
for i in range (0,len(baselines)):
    plt.errorbar(x=baselines[i], y=intsA[i], yerr=dintsA[i], xerr=data[:,2][i], marker="^", linestyle="", color="blue")
    plt.errorbar(x=baselines[i], y=intsB[i], yerr=dintsB[i], xerr=data[:,2][i], marker="o", linestyle="", color="#32a8a2")
    plt.errorbar(x=baselines[i], y=ints3Ax4B[i], yerr=dints3Ax4B[i], xerr=data[:,2][i], marker="o", linestyle="", color="red")
    plt.errorbar(x=baselines[i], y=ints4Ax3B[i], yerr=dints4Ax3B[i], xerr=data[:,2][i], marker="o", linestyle="", color="orange")
plt.errorbar(baselines+2, ints_avg, yerr=dints_avg, marker="o", linestyle="", color="black", markersize=10)
plt.plot(xplot, uti.spatial_coherence(xplot,*poptA), color="red")
plt.plot(xplot, uti.spatial_coherence(xplot,*poptB), color="grey")
#plt.fill_between(xplot, spatial_coherence(xplot,*popt) + deltas_sc, spatial_coherence(xplot,*popt) - deltas_sc, color="red", alpha=0.2)

plt.xlim(-15,250)#; plt.ylim(0,30)
plt.xlabel("Baseline (m)"); plt.ylabel("Coherence time (fs)")
plt.tight_layout()
#plt.savefig("{}_crosscorrelation.png".format(star))
plt.show()


# Just testing: correlation plot
plt.plot(intsA, intsB, "o")
plt.plot(intsA, ints3Ax4B, "o")
plt.plot(intsA, ints4Ax3B, "o")
plt.show()