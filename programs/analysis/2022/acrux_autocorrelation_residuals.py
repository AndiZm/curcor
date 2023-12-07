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

fig = plt.figure(figsize=(12,7))
grid = GridSpec (10, 40, left=0.1, bottom=0.15, right=0.94, top=0.94, wspace=0.1, hspace=0.3)

ax3_upper = fig.add_subplot( grid[0:7,  2:20] )
ax3_res   = fig.add_subplot( grid[8:10, 2:20] )
ax3_upper.set_title("CT3 auto-correlations of Acrux")

ax4_upper = fig.add_subplot( grid[0:7,  22:40] )
ax4_res   = fig.add_subplot( grid[8:10, 22:40] )
ax4_upper.set_title("CT4 auto-correlations of Acrux")

ints3 = []; dints3 = []; times = []
ints4 = []; dints4 = []

timestrings = []

# loop over every g2 function chunks
maxis3 = []; minis3 = []
maxis4 = []; minis4 = []

for i in range(0,len(ct3s)):
    ct3 = ct3s[i]#[5025:5125]
    ct4 = ct4s[i]#[5025:5125]

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

    the_shift = 0        

    if i%1 == 0:
        # Subplot for the auto correlation CT3
        ax3_upper.plot(x-mu3, ct3+the_shift, "-", color = colors[i], alpha=0.5)
        ax4_upper.plot(x-mu4, ct4+the_shift, "-", color = colors[i], alpha=0.5)
        
        # Calculate residuals
        res3 = []; res4 = []
        for j in range (0, len(ct3)):
            res3.append(ct3[j] - uti.gauss_shifted(x=x[j]-mu3 , a=popt3[0], mu=0, sigma=sigma3, shift=0) )
            res4.append(ct4[j] - uti.gauss_shifted(x=x[j]-mu4 , a=popt4[0], mu=0, sigma=sigma4, shift=0) )
        res3 = np.array(res3); res4 = np.array(res4)

        # If in plot range, check things
        ax3_res.plot(x-mu3, res3+0+the_shift, "-", color=colors[i], alpha=0.5)
        ax4_res.plot(x-mu4, res4+0+the_shift, "-", color=colors[i], alpha=0.5)
        res3_range = []; res4_range = []
        for j in range (0, len(res3)):            
            if x[j] >= 70 and x[j] <= 180:
                res3_range.append(res3[j]+1)
                res4_range.append(res4[j]+1)

        maxis3.append(np.max(res3_range))
        minis3.append(np.min(res3_range))
        maxis4.append(np.max(res4_range))
        minis4.append(np.min(res4_range))

the_max3 = np.max(maxis3); the_min3 = np.min(minis3)
#ax3_upper.axhline(y = the_max3)
#ax3_upper.axhline(y = the_min3)
ax3_upper.fill_between(x=np.arange(-100,100,0.1), y1=the_max3, y2=the_min3, color="red", alpha=0.1, label="maximum oscillations")

ax3_upper.axhline(y = 1, color="grey", linestyle="--")

the_max4 = np.max(maxis4); the_min4 = np.min(minis4)
#ax4_upper.axhline(y = the_max4)
#ax4_upper.axhline(y = the_min4)
ax4_upper.fill_between(x=np.arange(-100,100,0.1), y1=the_max4, y2=the_min4, color="red", alpha=0.1, label="maximum oscillations")
ax4_upper.axhline(y = 1, color="grey", linestyle="--")

#print ("Maximum fluctuation: {}".format(the_max-1))
#print ("Minimum fluctuation: {}".format(1-the_min))

#########################################
# Do analysis for the averaged function #
#########################################
ax3_upper.plot(x-mu3, auto3, color="black", linewidth=3)
ax4_upper.plot(x-mu4, auto4, color="black", linewidth=3)

# Apply gaussian fits to auto correlations
xplotf, popt3, perr3 = uti.fit_fixed(auto3, x, 80, 160, mu3,sigma3)
ax3_upper.plot(xplotf-mu3, uti.gauss_shifted(x=xplotf-mu3, a=popt3[0], mu=0, sigma=sigma3, shift=0.5e6*the_shift), color="red", linestyle="-", linewidth=1)
xplotf, popt4, perr4 = uti.fit_fixed(auto4, x, 80, 160, mu4,sigma4)
ax4_upper.plot(xplotf-mu4, uti.gauss_shifted(x=xplotf-mu4, a=popt4[0], mu=0, sigma=sigma4, shift=0.5e6*the_shift), color="red", linestyle="-", linewidth=1)
# Calculate residuals
res3 = []; res4 = []
for j in range (0, len(auto3)):
    res3.append(auto3[j] - uti.gauss_shifted(x=x[j]-mu3 , a=popt3[0], mu=0, sigma=sigma3, shift=0) )
    res4.append(auto4[j] - uti.gauss_shifted(x=x[j]-mu4 , a=popt4[0], mu=0, sigma=sigma4, shift=0) )
res3 = np.array(res3); res4 = np.array(res4)
ax3_res.plot(x-mu3, res3+0+the_shift, "-", color="black", linewidth=2)
ax4_res.plot(x-mu4, res4+0+the_shift, "-", color="black", linewidth=2)
# Get minimum and maximum oscillation
res3_range = []; res4_range = []
for j in range (0, len(res3)):            
    if x[j] >= 70 and x[j] <= 180:
        res3_range.append(res3[j]+1)
        res4_range.append(res4[j]+1)

max_avg3 = np.max(res3_range)
min_avg3 = np.min(res3_range)
max_avg4 = np.max(res4_range)
min_avg4 = np.min(res4_range)

#ax3_upper.axhline(y=max_avg3, color="black")
#ax3_upper.axhline(y=min_avg3, color="black")
ax3_upper.fill_between(x=np.arange(-100,100,0.1), y1=max_avg3, y2=min_avg3, color="black", alpha=0.2, label="oscillation in averaged $g^{(2)}$")

#ax4_upper.axhline(y=max_avg4, color="black")
#ax4_upper.axhline(y=min_avg4, color="black")
ax4_upper.fill_between(x=np.arange(-100,100,0.1), y1=max_avg4, y2=min_avg4, color="black", alpha=0.2, label="oscillation in averaged $g^{(2)}$")


ax3_upper.set_xlim(70-mu3,180-mu3); ax3_upper.set_ylim(1-2.5e-6, 1+8e-6)
ax3_upper.ticklabel_format(useOffset=False)
ax3_upper.set_xlabel("Time difference (ns)")
ax3_upper.set_ylabel("$g^{(2)}$")

ax3_res.set_xlim(70-mu3,180-mu3); ax3_res.set_ylim(0-2.5e-6, 0+4e-6)
ax3_res.ticklabel_format(useOffset=False)
ax3_res.set_ylabel("residuals")

ax4_upper.set_xlim(70-mu4,180-mu4); ax4_upper.set_ylim(1-2.5e-6, 1+8e-6)
ax4_upper.ticklabel_format(useOffset=False)
ax4_upper.set_xlabel("Time difference (ns)")
ax4_upper.set_yticks([])

ax4_res.set_xlim(70-mu4,180-mu4); ax4_res.set_ylim(0-2.5e-6, 0+4e-6)
ax4_res.ticklabel_format(useOffset=False)
    
# Print Maximum upwards oscillation and downwards oscillation
max_up   = np.max([max_avg3, max_avg4]) - 1.
max_down = np.abs(1. - np.min([min_avg3, min_avg4]))

ax3_upper.legend()
ax4_upper.legend()

print ("Maximum upward   fluctuation: {}".format(max_up))
print ("Maximum downward fluctuation: {}".format(max_down))
np.savetxt("oscillations.txt", np.c_[[max_down, max_up]])
plt.savefig("oscillations.png")
    
plt.show()