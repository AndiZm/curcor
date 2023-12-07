import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl  
from scipy.optimize import curve_fit
from scipy.signal import butter, filtfilt, find_peaks
from matplotlib.pyplot import cm
import ephem
import scipy.special as scp
import sys
from matplotlib.gridspec import  GridSpec
from matplotlib.transforms import Affine2D

import utilities as uti
import corrections as cor


############################################################################
## take Acrux data and analyze the autocorrelations in different aspects ###
############################################################################
star = "Acrux"
print("Peak part Analysis of {}".format(star))

# Read in the data (g2 functions and time/baseline parameters), only interested in autocorrelations
chAs  = np.loadtxt("g2_functions/weight_rms_squared/{}/ChA.txt".format(star))
chBs  = np.loadtxt("g2_functions/weight_rms_squared/{}/ChB.txt".format(star))
ct3s  = np.loadtxt("g2_functions/weight_rms_squared/{}/CT3_clean.txt".format(star))
ct4s  = np.loadtxt("g2_functions/weight_rms_squared/{}/CT4_clean.txt".format(star))
data  = np.loadtxt("g2_functions/weight_rms_squared/{}/baseline.txt".format(star))

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


# Fit into the combined g2 function for peak integral and parameter fixing ...
# ... and plot autocorrelations of CT3 and CT4 into one plot to check differences
# Fit for gaining mu and sigma to fix these parameters
xplot, popt, perr = uti.fit(auto3, x, 90, 150, 117)
mu3 = popt[1]; sigma3 = popt[2]

xplot, popt, perr = uti.fit(auto4, x, 90, 150, 117)
mu4 = popt[1]; sigma4 = popt[2]

#####################################################################################################################
## Third analysis: take Acrux autocorrelation data analyze chunk bunching peaks quantitatively
#####################################################################################################################
# Define colormap for plotting all summarized individual g2 functions
cm_sub = np.linspace(1.0, 0.0, len(ct3s))
colors = [cm.viridis(x) for x in cm_sub]

# Define figure which will show all autocorrelations of CT3, CT4 and the fit integrals

fig = plt.figure(figsize=(6,7))
grid = GridSpec (2, 20, left=0.1, bottom=0.15, right=0.94, top=0.94, wspace=0.1, hspace=0.3)

ax_upper = fig.add_subplot( grid[0:1, 2:20] )
ax_upper.set_title("CT3 auto-correlations of Acrux")

ints3 = []; dints3 = []; times = []
ints4 = []; dints4 = []

timestrings = []

# loop over every g2 function chunks
for i in range(0,len(ct3s)):
    ct3 = ct3s[i]#[5025:5125]
    ct4 = ct4s[i]#[5025:5125]

    #x_small = np.arange(-50*1.6,50*1.6,1.6)

    # Apply gaussian fits to auto correlations
    xplotf, popt3, perr3 = uti.fit_fixed(ct3, x, 80, 160, mu3,sigma3)
    Int, dInt = uti.integral_fixed(popt3, perr3, sigma3)
    ints3.append(1e6*Int); dints3.append(1e6*dInt)# in femtoseconds

    xplotf, popt4, perr4 = uti.fit_fixed(ct4, x, 80, 160, mu4,sigma4)
    Int, dInt = uti.integral_fixed(popt4, perr4, sigma4)
    ints4.append(1e6*Int); dints4.append(1e6*dInt)# in femtoseconds

    # Check acquisition time of original data
    timestring = str( ephem.Date(data[:,0][i]) )[5:-3]
    timestrings.append(timestring)
    print("{}".format(i), timestring, Int, dInt)

    the_shift = ( len(ct3s)-i-2 ) * 0.5e-6
    #the_shift = 0
    

    if i%3 == 0:
        # Subplot for the auto correlation CT3
        ax_upper.plot(x-mu3, ct3+the_shift, "o-", label=timestring, color = colors[i], alpha=0.5)
        ax_upper.plot(xplotf-mu3, uti.gauss_shifted(x=xplotf-mu3, a=popt3[0], mu=0, sigma=sigma3, shift=0.5e6*the_shift), color=colors[i], linestyle="-")
        
        ax_upper.text(x=30, y=1+the_shift+0.2e-6, s=timestring, color=colors[i], fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))

        ## Subplot for the auto correlation CT4
        #plt.subplot(222)
        #plt.errorbar(x, ct4+i*2e-6, yerr=0, marker=".", linestyle="--", label=timestring, color = colors[i], alpha=0.6)
        #plt.plot(xplotf, uti.gauss_shifted(x=xplotf, a=popt4[0], mu=mu4, sigma=sigma4, shift=i), color="black", linestyle="-")

#ax_upper.grid()
ax_upper.set_xlim(70-mu3,180-mu3); ax_upper.set_ylim(1-2e-6, 1+17e-6)
ax_upper.ticklabel_format(useOffset=False)
#plt.legend()
#plt.tight_layout()
ax_upper.set_xlabel("Time difference (ns)")
ax_upper.set_ylabel("$g^{(2)}$")
    

    


# Figure stuff
ax_lower = fig.add_subplot( grid[1:2, 2:17] )

# plot the peak integrals
x3 = np.arange(0,len(ints3),1)
x4 = np.arange(0.1,len(ints4)+0.1,1)
m3, dm3 = uti.calc_array_mean(ints3, dints3)
m4, dm4 = uti.calc_array_mean(ints4, dints4)
ax_lower.set_title("Peak integrals")
ax_lower.errorbar(x3, y=ints3, yerr=dints3, marker="o", linestyle="", label="CT 3", color="#8f0303")
ax_lower.errorbar(x4, y=ints4, yerr=dints4, marker="o", linestyle="", label="CT 4", color="#003366")
ax_lower.fill_between(x3, y1=np.mean(ints3)+np.std(ints3), y2=np.mean(ints3)-np.std(ints3), color="#8f0303",   alpha=0.1)
ax_lower.fill_between(x4, y1=np.mean(ints4)+np.std(ints4), y2=np.mean(ints4)-np.std(ints4), color="#003366", alpha=0.1)
ax_lower.axhline(y=np.mean(ints3), linestyle="--", alpha=0.5, color="#8f0303")
ax_lower.axhline(y=np.mean(ints4), linestyle="--", alpha=0.5, color="#003366")
ax_lower.set_ylim(16.63, 42.87)

print(np.std(ints3))
print(np.std(ints4))

ax_lower.set_xlabel("Measurement index")
ax_lower.set_ylabel("Coherence time (fs)")
#plt.ylim(0,)
ax_lower.legend(loc="lower left")

ax_right = fig.add_subplot( grid[1:2, 17:20] )
#ax_right.rotate(90)



# Histogram
the_bins=int(1)
binsx = np.arange(13,47,the_bins)
xplot = np.arange(13,47,0.1)
ct3_histo = np.histogram(ints3, bins=binsx)
ct4_histo = np.histogram(ints4, bins=binsx)


histo_x = ct3_histo[1][:-1]; histo_3 = ct3_histo[0]; histo_4 = ct4_histo[0]
# error on y values
histo_3_err = np.sqrt(histo_3); histo_3_err[histo_3_err==0]= 1
histo_4_err = np.sqrt(histo_4); histo_4_err[histo_4_err==0]= 1

# Fit gauss
def gauss(x,a,m,s):
    return a * np.exp( -(x-m)**2/2/s/s )
popt3, pcov3 = curve_fit(gauss, histo_x, histo_3, p0=[10,25,3]); perr3 = np.sqrt(np.diag(pcov3))
popt4, pcov4 = curve_fit(gauss, histo_x, histo_4, p0=[10,25,3]); perr4 = np.sqrt(np.diag(pcov4))

print ("----------------------------------------------------")
print (perr3)
print (perr4)
print ("Gauß fit parameter results")
print ("Mean:")
print ("CT3: {:.2f} +/- {:.2f}".format(popt3[1], perr3[1]))
print ("CT4: {:.2f} +/- {:.2f}".format(popt4[1], perr4[1]))
print ("Sigma:")
print ("CT3: {:.2f} +/- {:.2f}".format(popt3[2], perr3[2]))
print ("CT4: {:.2f} +/- {:.2f}".format(popt4[2], perr4[2]))
print ("----------------------------------------------------")


ax_right.barh(histo_x, histo_3, alpha=0.2, height=the_bins, color="#8f0303")
ax_right.barh(histo_x, histo_4, alpha=0.2, height=the_bins, color="#003366")
ax_right.plot(gauss(xplot, *popt3), xplot, alpha=0.7, color="#8f0303", linestyle="dashdot")
ax_right.plot(gauss(xplot, *popt4), xplot, alpha=0.7, color="#003366", linestyle="dashdot")

ax_right.set_ylim(16.63, 42.87)
ax_right.set_yticks([])
ax_right.set_xlabel("Counts")

plt.tight_layout()
plt.savefig("images/misc/acrux_autocorrelations.pdf")
plt.show()