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

#####################################################################################################################
## First analysis: take Shaula data and divide cross and auto correlation data in 2 bunches of equal measurement time
## to check for systematics in the g2 functions
#####################################################################################################################
star = "Shaula"
print("1. Peak part Analysis of {}".format(star))

# Read in the data (g2 functions and time/baseline parameters)
chAs  = np.loadtxt("g2_functions/{}/ChA.txt".format(star))
chBs  = np.loadtxt("g2_functions/{}/ChB.txt".format(star))
ct3s  = np.loadtxt("g2_functions/{}/CT3.txt".format(star))
ct4s  = np.loadtxt("g2_functions/{}/CT4.txt".format(star))
data  = np.loadtxt("g2_functions/{}/baseline.txt".format(star))

# Demo function for initializing x axis and some stuff
demo = chAs[0]
x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)

# There are 12 chunks of Shaula data, so divide both the cross and the auto-correlations in 2x6 to check for systematics
crossA_0 = np.zeros(len(x)); crossA_1 = np.zeros(len(x))
crossB_0 = np.zeros(len(x)); crossB_1 = np.zeros(len(x))
auto3_0  = np.zeros(len(x)); auto3_1  = np.zeros(len(x))
auto4_0  = np.zeros(len(x)); auto4_1  = np.zeros(len(x))
for i in range (0,6):
    crossA_0 += chAs[i]/np.std(chAs[i][0:4500])
    crossB_0 += chBs[i]/np.std(chBs[i][0:4500])
    auto3_0  += ct3s[i]/np.std(ct3s[i][0:4500])
    auto4_0  += ct4s[i]/np.std(ct4s[i][0:4500])
for i in range (6,12):
    crossA_1 += chAs[i]/np.std(chAs[i][0:4500])
    crossB_1 += chBs[i]/np.std(chBs[i][0:4500])
    auto3_1  += ct3s[i]/np.std(ct3s[i][0:4500])
    auto4_1  += ct4s[i]/np.std(ct4s[i][0:4500])
crossA_0 = crossA_0/np.mean(crossA_0[0:4500]); crossA_1 = crossA_1/np.mean(crossA_1[0:4500]) 
crossB_0 = crossB_0/np.mean(crossB_0[0:4500]); crossB_1 = crossB_1/np.mean(crossB_1[0:4500])
auto3_0  = auto3_0 /np.mean(auto3_0 [0:4500]); auto3_1  = auto3_1 /np.mean(auto3_1 [0:4500])
auto4_0  = auto4_0 /np.mean(auto4_0 [0:4500]); auto4_1  = auto4_1 /np.mean(auto4_1 [0:4500])

# Also combine all g2 together
crossA = ( crossA_0/np.std(crossA_0[0:4500]) + crossA_1/np.std(crossA_1) ); crossA = crossA/np.mean(crossA[0:4500])
crossB = ( crossB_0/np.std(crossB_0[0:4500]) + crossB_1/np.std(crossB_1) ); crossB = crossB/np.mean(crossB[0:4500])
auto3  = ( auto3_0 /np.std(auto3_0 [0:4500]) + auto3_1 /np.std(auto3_1 ) ); auto3  = auto3 /np.mean(auto3 [0:4500])
auto4  = ( auto4_0 /np.std(auto4_0 [0:4500]) + auto4_1 /np.std(auto4_1 ) ); auto4  = auto4 /np.mean(auto4 [0:4500])

# Plot each pair of g2 functions
plt.figure("Shaula data", figsize=(16,8))

plt.subplot(221)
plt.title("Cross correlation Ch A")
plt.plot(x, crossA_0, label="First  half")
plt.plot(x, crossA_1, label="Second half")
plt.plot(x, crossA, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()

plt.subplot(222)
plt.title("Cross correlation Ch B")
plt.plot(x, crossB_0, label="First  half")
plt.plot(x, crossB_1, label="Second half")
plt.plot(x, crossB, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()

plt.subplot(223)
plt.title("Auto correlation CT 3")
plt.plot(x, auto3_0, label="First  half")
plt.plot(x, auto3_1, label="Second half")
plt.plot(x, auto3, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()

plt.subplot(224)
plt.title("Auto correlation CT 4")
plt.plot(x, auto4_0, label="First  half")
plt.plot(x, auto4_1, label="Second half")
plt.plot(x, auto4, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()
plt.tight_layout()

#####################################################################################################################
## Second analysis: take Acrux data and analyze the autocorrelations in different aspects
#####################################################################################################################
star = "Acrux"
print("2. Peak part Analysis of {}".format(star))

# Read in the data (g2 functions and time/baseline parameters), only interested in autocorrelations
chAs  = np.loadtxt("g2_functions/{}/ChA.txt".format(star))
chBs  = np.loadtxt("g2_functions/{}/ChB.txt".format(star))
ct3s  = np.loadtxt("g2_functions/{}/CT3.txt".format(star))
ct4s  = np.loadtxt("g2_functions/{}/CT4.txt".format(star))
data  = np.loadtxt("g2_functions/{}/baseline.txt".format(star))

# Demo function for initializing x axis and some stuff
demo = chAs[0]
x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)

# There are 24 chunks of Acrux data, so divide both the cross and the auto-correlations in 2x12 to check for systematics
crossA_0 = np.zeros(len(x)); crossA_1 = np.zeros(len(x))
crossB_0 = np.zeros(len(x)); crossB_1 = np.zeros(len(x))
auto3_0  = np.zeros(len(x)); auto3_1  = np.zeros(len(x))
auto4_0  = np.zeros(len(x)); auto4_1  = np.zeros(len(x))
for i in range (0,12):
    crossA_0 += chAs[i]/np.std(chAs[i][0:4500])
    crossB_0 += chBs[i]/np.std(chBs[i][0:4500])
    auto3_0  += ct3s[i]/np.std(ct3s[i][0:4500])
    auto4_0  += ct4s[i]/np.std(ct4s[i][0:4500])
for i in range (12,24):
    crossA_1 += chAs[i]/np.std(chAs[i][0:4500])
    crossB_1 += chBs[i]/np.std(chBs[i][0:4500])
    auto3_1  += ct3s[i]/np.std(ct3s[i][0:4500])
    auto4_1  += ct4s[i]/np.std(ct4s[i][0:4500])
crossA_0 = crossA_0/np.mean(crossA_0[0:4500]); crossA_1 = crossA_1/np.mean(crossA_1[0:4500]) 
crossB_0 = crossB_0/np.mean(crossB_0[0:4500]); crossB_1 = crossB_1/np.mean(crossB_1[0:4500])
auto3_0  = auto3_0 /np.mean(auto3_0 [0:4500]); auto3_1  = auto3_1 /np.mean(auto3_1 [0:4500])
auto4_0  = auto4_0 /np.mean(auto4_0 [0:4500]); auto4_1  = auto4_1 /np.mean(auto4_1 [0:4500])

# Also combine all g2 together
crossA = ( crossA_0/np.std(crossA_0[0:4500]) + crossA_1/np.std(crossA_1) ); crossA = crossA/np.mean(crossA[0:4500])
crossB = ( crossB_0/np.std(crossB_0[0:4500]) + crossB_1/np.std(crossB_1) ); crossB = crossB/np.mean(crossB[0:4500])
auto3  = ( auto3_0 /np.std(auto3_0 [0:4500]) + auto3_1 /np.std(auto3_1 ) ); auto3  = auto3 /np.mean(auto3 [0:4500])
auto4  = ( auto4_0 /np.std(auto4_0 [0:4500]) + auto4_1 /np.std(auto4_1 ) ); auto4  = auto4 /np.mean(auto4 [0:4500])

# Plot each pair of g2 functions
plt.figure("Acrux data", figsize=(16,8))

plt.subplot(221)
plt.title("Cross correlation Ch A")
plt.plot(x, crossA_0, label="First  half")
plt.plot(x, crossA_1, label="Second half")
plt.plot(x, crossA, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()

plt.subplot(222)
plt.title("Cross correlation Ch B")
plt.plot(x, crossB_0, label="First  half")
plt.plot(x, crossB_1, label="Second half")
plt.plot(x, crossB, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()

plt.subplot(223)
plt.title("Auto correlation CT 3")
plt.plot(x, auto3_0, label="First  half")
plt.plot(x, auto3_1, label="Second half")
plt.plot(x, auto3, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()

plt.subplot(224)
plt.title("Auto correlation CT 4")
plt.plot(x, auto4_0, label="First  half")
plt.plot(x, auto4_1, label="Second half")
plt.plot(x, auto4, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()
plt.tight_layout()





plt.show()



'''
# Fit for gaining mu and sigma to fix these parameters
xplot, popt, perr = uti.fit(g2_allA, x, -40, +40)
muA = popt[1]; sigmaA = popt[2]

plt.plot(x, g2_allA)
plt.plot(xplot, uti.gauss(xplot,*popt), color="black")

xplot, popt, perr = uti.fit(g2_allB, x, -40, +40)
muB = popt[1]; sigmaB = popt[2]

plt.plot(x, g2_allB)
plt.plot(xplot, uti.gauss(xplot,*popt), color="black")
#plt.show()

# Define colormap for plotting all summarized individual g2 functions
cm_sub = np.linspace(1.0, 0.0, len(chAs))
colors = [cm.viridis(x) for x in cm_sub]

# Define total figure which will show individuall g2 functions off cross and auto-correlation
# and also the spatial correlation curve (baseline vs. g2 integral)
plt.figure(figsize=(18,12))
plt.subplot(221)
intsA = []; dintsA = []; times = []
intsB = []; dintsB = []

# initialize CT3 and CT4 sum arrays
ct3_sum = np.zeros(len(ct3s[0]))
ct4_sum = np.zeros(len(ct4s[0]))

# loop over every g2 function chunks
for i in range(0,len(chAs)):
    chA = chAs[i]
    chB = chBs[i]
    ct3 = ct3s[i]
    ct4 = ct4s[i]

    # Do some more data cleaning, e.g. lowpass filters
    ct3 = cor.lowpass(ct3)
    ct4 = cor.lowpass(ct4)

    # more data cleaning with notch filter for higher frequencies
    freq3 = [50, 90, 125, 150]
    for j in range(len(freq3)):
        ct3 = cor.notch(ct3, freq3[j]*1e6, 80)
    freq4 = [50, 90, 110, 130, 150, 250]
    for k in range(len(freq4)):
        ct4 = cor.notch(ct4, freq4[k]*1e6, 80)

    # Apply gaussian fits to cross correlations, keep mu and sigma fixed
    xplotf, poptA, perrA = uti.fit_fixed(chA, x, -100, 100, muA,sigmaA)
    Int, dInt = uti.integral_fixed(poptA, perrA, sigmaA)
    intsA.append(1e6*Int); dintsA.append(1e6*dInt)# in femtoseconds

    xplotf, poptB, perrB = uti.fit_fixed(chB, x, -100, 100, muB,sigmaB)
    Int, dInt = uti.integral_fixed(poptB, perrB, sigmaB)
    intsB.append(1e6*Int); dintsB.append(1e6*dInt)# in femtoseconds


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
plt.errorbar(x, ct4_sum+0e-5, yerr=0, marker=".", linestyle="--", label=timestring, color = "black", linewidth=2, alpha=1)

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
plt.xlim(80,160)

#### making SC plot (spatial coherence) via integral data ####
xplot = np.arange(0.1,300,0.1)
plt.subplot(122)

# get baselines for x axes
baselines = data[:,1]

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
    plt.errorbar(x=baselines[i], y=intsA[i], yerr=dintsA[i], xerr=data[:,2][i], marker="^", linestyle="", color=colors[i])
    plt.errorbar(x=baselines[i], y=intsB[i], yerr=dintsB[i], xerr=data[:,2][i], marker="o", linestyle="", color=colors[i])
plt.plot(xplot, uti.spatial_coherence(xplot,*poptA), color="red")
plt.plot(xplot, uti.spatial_coherence(xplot,*poptB), color="grey")
#plt.fill_between(xplot, spatial_coherence(xplot,*popt) + deltas_sc, spatial_coherence(xplot,*popt) - deltas_sc, color="red", alpha=0.2)

plt.xlim(-15,250)#; plt.ylim(0,30)
plt.xlabel("Baseline (m)"); plt.ylabel("Coherence time (fs)")
plt.tight_layout()
#plt.savefig("{}_crosscorrelation.png".format(star))
plt.show()
'''