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
ct3s  = np.loadtxt("g2_functions/{}/CT3_clean.txt".format(star))
ct4s  = np.loadtxt("g2_functions/{}/CT4_clean.txt".format(star))
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
crossA = ( crossA_0/np.std(crossA_0[0:4500]) + crossA_1/np.std(crossA_1[0:4500]) ); crossA = crossA/np.mean(crossA[0:4500])
crossB = ( crossB_0/np.std(crossB_0[0:4500]) + crossB_1/np.std(crossB_1[0:4500]) ); crossB = crossB/np.mean(crossB[0:4500])
auto3  = ( auto3_0 /np.std(auto3_0 [0:4500]) + auto3_1 /np.std(auto3_1 [0:4500]) ); auto3  = auto3 /np.mean(auto3 [0:4500])
auto4  = ( auto4_0 /np.std(auto4_0 [0:4500]) + auto4_1 /np.std(auto4_1 [0:4500]) ); auto4  = auto4 /np.mean(auto4 [0:4500])

#auto3 = 0.5 * (auto3_0 + auto3_1)
#auto4 = 0.5 * (auto4_0 + auto4_1)
#
#print (np.std(auto3_0[0:4500]))
#print (np.std(auto3_1[0:4500]))

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
ct3s  = np.loadtxt("g2_functions/{}/CT3_clean.txt".format(star))
ct4s  = np.loadtxt("g2_functions/{}/CT4_clean.txt".format(star))
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
crossA = ( crossA_0/np.std(crossA_0[0:4500]) + crossA_1/np.std(crossA_1[0:4500]) ); crossA = crossA/np.mean(crossA[0:4500])
crossB = ( crossB_0/np.std(crossB_0[0:4500]) + crossB_1/np.std(crossB_1[0:4500]) ); crossB = crossB/np.mean(crossB[0:4500])
auto3  = ( auto3_0 /np.std(auto3_0 [0:4500]) + auto3_1 /np.std(auto3_1 [0:4500]) ); auto3  = auto3 /np.mean(auto3 [0:4500])
auto4  = ( auto4_0 /np.std(auto4_0 [0:4500]) + auto4_1 /np.std(auto4_1 [0:4500]) ); auto4  = auto4 /np.mean(auto4 [0:4500])

# Plot each pair of g2 functions
plt.figure("Acrux data", figsize=(24,8))

plt.subplot(231)
plt.title("Cross correlation Ch A")
plt.plot(x, crossA_0, label="First  half")
plt.plot(x, crossA_1, label="Second half")
plt.plot(x, crossA, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()

plt.subplot(232)
plt.title("Cross correlation Ch B")
plt.plot(x, crossB_0, label="First  half")
plt.plot(x, crossB_1, label="Second half")
plt.plot(x, crossB, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()

plt.subplot(234)
plt.title("Auto correlation CT 3")
plt.plot(x, auto3_0, label="First  half")
plt.plot(x, auto3_1, label="Second half")
plt.plot(x, auto3, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()

plt.subplot(235)
plt.title("Auto correlation CT 4")
plt.plot(x, auto4_0, label="First  half")
plt.plot(x, auto4_1, label="Second half")
plt.plot(x, auto4, color="black", linewidth=2)
plt.xlim(-200,200); plt.legend()
plt.tight_layout()

# Fit into the combined g2 function for peak integral and parameter fixing ...
# ... and plot autocorrelations of CT3 and CT4 into one plot to check differences
plt.subplot(133)
plt.title("Autocorrelations of CT3 and CT4")
# Fit for gaining mu and sigma to fix these parameters
xplot, popt, perr = uti.fit(auto3, x, 90, 150, 117)
Int, dInt = uti.integral(popt, perr)
mu3 = popt[1]; sigma3 = popt[2]
plt.plot(x, auto3, label="CT3: {:.2f} +/- {:.2f} fs".format(1e6*Int, 1e6*dInt))
plt.plot(xplot, uti.gauss(xplot, *popt), color="black")
xplot, popt, perr = uti.fit(auto4, x, 90, 150, 117)
Int, dInt = uti.integral(popt, perr)
mu4 = popt[1]; sigma4 = popt[2]
plt.plot(xplot, uti.gauss(xplot, *popt), color="black")
plt.plot(x, auto4, label="CT4: {:.2f} +/- {:.2f} fs".format(1e6*Int, 1e6*dInt))
plt.xlim(60,170); plt.legend()

#####################################################################################################################
## Third analysis: take Acrux autocorrelation data analyze chunk bunching peaks quantitatively
#####################################################################################################################
# Define colormap for plotting all summarized individual g2 functions
cm_sub = np.linspace(1.0, 0.0, len(ct3s))
colors = [cm.viridis(x) for x in cm_sub]

# Define figure which will show all autocorrelations of CT3, CT4 and the fit integrals
plt.figure(figsize=(18,12))
plt.subplot(221)
ints3 = []; dints3 = []; times = []
ints4 = []; dints4 = []

# loop over every g2 function chunks
for i in range(0,len(ct3s)):
    ct3 = ct3s[i]
    ct4 = ct4s[i]

    # Apply gaussian fits to auto correlations
    xplotf, popt3, perr3 = uti.fit_fixed(ct3, x, 90, 150, mu3,sigma3)
    Int, dInt = uti.integral_fixed(popt3, perr3, sigma3)
    ints3.append(1e6*Int); dints3.append(1e6*dInt)# in femtoseconds

    xplotf, popt4, perr4 = uti.fit_fixed(ct4, x, 90, 150, mu4,sigma4)
    Int, dInt = uti.integral_fixed(popt4, perr4, sigma4)
    ints4.append(1e6*Int); dints4.append(1e6*dInt)# in femtoseconds

    # Check acquisition time of original data
    timestring = ephem.Date(data[:,0][i])
    print("{}".format(i), timestring, Int, dInt)
    
    # Subplot for the auto correlation CT3
    plt.subplot(221)
    plt.errorbar(x, ct3+i*2e-6, yerr=0, marker=".", linestyle="--", label=timestring, color = colors[i], alpha=0.6)
    plt.plot(xplotf, uti.gauss_shifted(x=xplotf, a=popt3[0], mu=mu3, sigma=sigma3, shift=i), color="black", linestyle="-")

    # Subplot for the auto correlation CT4
    plt.subplot(222)
    plt.errorbar(x, ct4+i*2e-6, yerr=0, marker=".", linestyle="--", label=timestring, color = colors[i], alpha=0.6)
    plt.plot(xplotf, uti.gauss_shifted(x=xplotf, a=popt4[0], mu=mu4, sigma=sigma4, shift=i), color="black", linestyle="-")


# Figure stuff
plt.subplot(221)
plt.title("CT3 autocorrelations on {}".format(star))
plt.grid()
plt.ticklabel_format(useOffset=False)
plt.xlabel("Time difference (ns)")
plt.ylabel("$g^{(2)}$")
plt.legend(loc="lower right")
plt.xlim(70,170)
plt.tight_layout()
plt.subplot(222)
plt.title("CT4 autocorrelations on {}".format(star))
plt.grid()
plt.xlim(70,170)

# plot the peak integrals
plt.subplot(212)
x3 = np.arange(0,len(ints3),1)
x4 = np.arange(0.1,len(ints4)+0.1,1)
m3, dm3 = uti.calc_array_mean(ints3, dints3)
m4, dm4 = uti.calc_array_mean(ints4, dints4)
plt.title("Peak integrals")
plt.errorbar(x3, y=ints3, yerr=dints3, marker="o", linestyle="", label="CT 3", color="blue")
plt.errorbar(x4, y=ints4, yerr=dints4, marker="o", linestyle="", label="CT 4", color="orange")
plt.fill_between(x3, y1=np.mean(ints3)+np.std(ints3), y2=np.mean(ints3)-np.std(ints3), color="blue",   alpha=0.1)
plt.fill_between(x4, y1=np.mean(ints4)+np.std(ints4), y2=np.mean(ints4)-np.std(ints4), color="orange", alpha=0.1)
plt.axhline(y=np.mean(ints3), linestyle="--", alpha=0.5, color="blue")
plt.axhline(y=np.mean(ints4), linestyle="--", alpha=0.5, color="orange")

plt.ylabel("Coherence time (fs)")
#plt.ylim(0,)
plt.legend()
plt.tight_layout()

plt.show()