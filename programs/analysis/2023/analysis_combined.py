import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from matplotlib.pyplot import cm
import matplotlib as mpl
from tqdm import tqdm
from datetime import datetime, timezone
import ephem
import sys

import geometry as geo
import corrections as cor
import utilities as uti

from threading import Thread

star = sys.argv[1]

# Define files to analyze and subpackages
folders   = [] # Data folders for analysis
stepsizes = [] # Number of files for a single g2 function
ends      = [] # Total number of files used from this folder
telcombis = [] # Combination of telescopes (either 14, 34 or 134)

# Open text file with measurement split data and read the data for the specific star
f = open("measurement_chunks.txt")
# Find line for the star
line = f.readline()
while star not in line:
    line = f.readline()
# Fill arrays with the data
line = f.readline()
while "[end]" not in line:
    folders.append(line.split()[0])
    stepsizes.append( int(line.split()[1]) )
    ends.append( int(line.split()[2]) )
    telcombis.append( str(line.split()[3]) )
    line = f.readline()
f.close()

print ("Analyzing {}".format(star))

star_small = star[0].lower() + star[1:]
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
def get_baseline_entry(telcombi):
    if telcombi == "13":
        return int(0)
    elif telcombi == "14":
        return int(1)
    elif telcombi == "34":
        return int(2)

# Initialize parameter arrays for data storing
g2_3s = []
g2_4s = []
g2_As = []
g2_Bs = []
#g2_3Ax4Bs = []
#g2_4Ax3Bs = []
baselines = []; dbaselines = []
time_means = []

# Number of datapoints
N = 2 * 1024**3        # 2G sample file
folderpath = "C:/Users/ii/Documents/curcor/corr_results/results_HESS"

def corr_parts(folder, start, stop, telcombi):
    # Define files to be analized for a single g2 function
    files = []
    for i in range (start, stop): 
        files.append("{}/{}/size10000/{}_{:05d}.fcorr6".format(folderpath, folder, star_small, i))

    # Initialize g2 functions for channel A and B which will be filled in for loop
    len_data = len( np.loadtxt(files[0])[:,2] )
    g2_sum_A = np.zeros(len_data)
    g2_sum_B = np.zeros(len_data)
    g2_sum_3 = np.zeros(len_data)
    g2_sum_4 = np.zeros(len_data)
    #g2_sum_3Ax4B = np.zeros(len_data)
    #g2_sum_4Ax3B = np.zeros(len_data)
    times = []; baseline_values = []

    # Read offset data for offset correction
    off3A = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[0]) )[0]
    off3B = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[0]) )[1]
    off4A = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[1]) )[0]
    off4B = np.loadtxt( folderpath + "/" + folder + "/calibs_ct{}/off.off".format(telcombi[1]) )[1]

    # Loop over every file
    for i in tqdm(range ( 0,len(files) )):
        file = files[i]

        # Read in data
        auto3  = np.loadtxt(file)[:,0] # G2 of CT3 A x CT3 B (autocorrelations)
        auto4  = np.loadtxt(file)[:,1] # G2 of CT4 A x CT4 B (autocorrelations)
        crossA = np.loadtxt(file)[:,2] # G2 of CT3 A x CT4 A (crosscorrelations)
        crossB = np.loadtxt(file)[:,3] # G2 of CT3 B x CT4 B (crosscorrelations)
        #c3Ax4B = np.loadtxt(file)[:,4] # G2 of CT3 A x CT4 B (crosscorrelations)
        #c4Ax3B = np.loadtxt(file)[:,5] # G2 of CT4 A x CT3 B (crosscorrelations)

        # Read mean waveform values
        f = open(file)
        line_params = f.readline()[:-1].split(" ") # Read header of fcorr file
        mean3A = float(line_params[2])
        mean3B = float(line_params[3])
        mean4A = float(line_params[4])
        mean4B = float(line_params[5])

        # Apply offset correction
        auto3  -= N * ( mean3A*off3B + mean3B*off3A - off3A*off3B ) # Only CT 3 both channels
        auto4  -= N * ( mean4A*off4B + mean4B*off4A - off4A*off4B ) # Only CT 4 both channels        
        crossA -= N * ( mean3A*off4A + mean4A*off3A - off3A*off4A ) # Only CH A, but CT3 and CT4
        crossB -= N * ( mean3B*off4B + mean4B*off3B - off3B*off4B ) # Only CH B, but CT3 and CT4
        #c3Ax4B -= N * ( mean3A*off4B + mean4B*off3A - off3A*off4B ) # CT3 A X CT4 B
        #c4Ax3B -= N * ( mean4A*off3B + mean3B*off4A - off4A*off3B ) # CT4 A X CT3 B

        # Apply pattern correction
        auto3  = cor.pattern_correction(auto3) # data already normalized
        auto4  = cor.pattern_correction(auto4) # data already normalized
        crossA = cor.pattern_correction(crossA) # data already normalized
        crossB = cor.pattern_correction(crossB) # data already normalized
        #c3Ax4B = cor.pattern_correction(c3Ax4B) # data already normalized
        #c4Ax3B = cor.pattern_correction(c4Ax3B) # data already normalized
    
        # Get file parameters from header and ephem calculations
        if star == "Regor":
            tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params_manual(file, ra=[8,10,12.5], dec=[-47,24,22.2], telcombi=telcombi)
        elif star == "Etacen":
            tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params_manual(file, ra=[14,35,30.42], dec=[-42,9,28.17], telcombi=telcombi)
        else:
            tdiff, mean_1, mean_2, mean_3, mean_4, az, alt, time = geo.get_params(file, starname=star, telcombi=telcombi)
        # Store acquisition times and corresponding baselines for sc plot
        times.append(ephem.Date(time))
        baseline_values.append(uti.get_baseline(date=time, star=star)[get_baseline_entry(telcombi=telcombi)])

        # Apply optical path length correction for cross correlations
        binshift = timebin(tdiff)
        crossA = shift_bins(crossA, binshift)
        crossB = shift_bins(crossB, binshift)
        #c3Ax4B = shift_bins(c3Ax4B, binshift)
        #c4Ax3B = shift_bins(c4Ax3B, -1*binshift) # negative binshift since CT4 is mentioned first
        #c4Ax3B = shift_bins(c4Ax3B, binshift) # for testing
    
        #################################
        # Averaging of the g2 functions #
        #################################
        #--  Autocorrelations --#
        rms = np.std(auto3[0:4500])
        g2_for_averaging = auto3/rms**2
        # Adding the new data to the total g2 function
        g2_sum_3 += g2_for_averaging

        rms = np.std(auto4[0:4500])
        g2_for_averaging = auto4/rms**2
        # Adding the new data to the total g2 function
        g2_sum_4 += g2_for_averaging


        #-- Crosscorrelations --#
        rms = np.std(crossA)
        g2_for_averaging = crossA/rms**2
        # Adding the new data to the total g2 function
        g2_sum_A += g2_for_averaging
    
        rms = np.std(crossB)
        g2_for_averaging = crossB/rms**2
        # Adding the new data to the total g2 function
        g2_sum_B += g2_for_averaging

        #rms = np.std(c3Ax4B)
        #g2_for_averaging = c3Ax4B/rms**2
        ## Adding the new data to the total g2 function
        #g2_sum_3Ax4B += g2_for_averaging

        #rms = np.std(c4Ax3B)
        #g2_for_averaging = c4Ax3B/rms**2
        ## Adding the new data to the total g2 function
        #g2_sum_4Ax3B += g2_for_averaging

    time_mean = np.mean(times)
    # Calculate mean baseline and baseline error
    baseline  = np.mean(baseline_values)
    dbaseline = np.std(baseline_values)
    print ("Telescope combination =  {}".format(telcombi))
    print ("Baseline =  {:.1f} +/- {:.1f}  m".format(baseline, dbaseline))
    print ("Central time = {}".format(ephem.Date(time_mean)))
    
    # Re-normalize for proper g2 function
    g2_sum_3 = g2_sum_3/np.mean(g2_sum_3)
    g2_sum_4 = g2_sum_4/np.mean(g2_sum_4)
    g2_sum_A = g2_sum_A/np.mean(g2_sum_A)
    g2_sum_B = g2_sum_B/np.mean(g2_sum_B)
    #g2_sum_3Ax4B = g2_sum_3Ax4B/np.mean(g2_sum_3Ax4B)
    #g2_sum_4Ax3B = g2_sum_4Ax3B/np.mean(g2_sum_4Ax3B)

    # Save the data of this correlation to the arrays
    g2_3s.append(g2_sum_3)
    g2_4s.append(g2_sum_4)
    g2_As.append(g2_sum_A)
    g2_Bs.append(g2_sum_B)
    #g2_3Ax4Bs.append(g2_sum_3Ax4B)
    #g2_4Ax3Bs.append(g2_sum_4Ax3B)
    baselines.append(baseline)
    dbaselines.append(dbaseline)
    time_means.append(time_mean)  

##########################################
# Add the number of files to be analyzed #
for i in range(len(folders)):
    folder   = folders[i]
    stepsize = stepsizes[i]
    end      = ends[i]
    telcombi = telcombis[i]

    steps = np.arange(0, end + 1, stepsize)
    for j in range(len(steps)-1):
        start = steps[j]
        stop = steps[j+1]
        corr_parts(folder, start, stop, telcombi)

np.savetxt("g2_functions/weight_rms_squared/{}/CT3.txt".format(star), np.c_[g2_3s], header="{} CT3".format(star))
np.savetxt("g2_functions/weight_rms_squared/{}/CT4.txt".format(star), np.c_[g2_4s], header="{} CT4".format(star))
np.savetxt("g2_functions/weight_rms_squared/{}/ChA.txt".format(star), np.c_[g2_As], header="{} Channel A".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/ChB.txt".format(star), np.c_[g2_Bs], header="{} Channel B".format(star) )
#np.savetxt("g2_functions/weight_rms_squared/{}/c3Ax4B.txt".format(star), np.c_[g2_3Ax4Bs], header="{} CT3 A x CT4 B".format(star) )
#np.savetxt("g2_functions/weight_rms_squared/{}/c4Ax3B.txt".format(star), np.c_[g2_4Ax3Bs], header="{} CT4 A x CT3 B".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/baseline.txt".format(star), np.c_[time_means, baselines, dbaselines], header="Time, baseline, baseline error" )


#######################################################################################################################################################################################################################
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

# Average over all 2 functions - CAUTION: You will never use this for two color measurements!
def average_g2s(cA, cB, c3Ax4B, c4Ax3B):
    g2_avg = np.zeros( len(cA) )
    g2_avg += cA/np.std(cA[0:4500])**2
    g2_avg += cB/np.std(cB[0:4500])**2
    g2_avg += c3Ax4B/np.std(c3Ax4B[0:4500])**2
    g2_avg += c4Ax3B/np.std(c4Ax3B[0:4500])**2

    g2_avg = g2_avg/np.mean(g2_avg[0:4500])

    return g2_avg

print("Final Analysis of {}".format(star))
################################################
#### Analysis over whole measurement time #####
################################################
# Read in the data (g2 functions and time/baseline parameters)
chAs    = g2_As    
chBs    = g2_Bs   
ct3s    = g2_3s   
ct4s    = g2_4s   
#c3Ax4Bs = g2_3Ax4Bs 
#c4Ax3Bs = g2_4Ax3Bs
data    = np.loadtxt("g2_functions/weight_rms_squared/{}/baseline.txt".format(star))

# Demo function for initializing x axis and some stuff
demo = chAs[0]
x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)

# Combine all data for channel A and B each for initial parameter estimation and fixing
plt.figure(figsize=(6,7))
plt.subplot(211)
plt.title("Cumulative cross correlation data of {}".format(star))

g2_allA = np.zeros(len(x)); g2_allB = np.zeros(len(x))
#g2_all3Ax4B = np.zeros(len(x)); g2_all4Ax3B = np.zeros(len(x))
for i in range (0,len(chAs)):
    #plt.plot(chAs[i]); plt.plot(chBs[i]); plt.show()
    g2_allA += chAs[i]/len(chAs)
    g2_allB += chBs[i]/len(chBs)
    #g2_all3Ax4B += c3Ax4Bs[i]/len(c3Ax4Bs)
    #g2_all4Ax3B += c4Ax3Bs[i]/len(c4Ax3Bs)

# Fit for gaining mu and sigma to fix these parameters
xplot, popt, perr = uti.fit(g2_allA, x, -50, +50)
muA = popt[1]; sigmaA = popt[2]
integral, dintegral = uti.integral(popt, perr)
print ("3A x 4A sigma/integral: {:.2f} +/- {:.2f} ns \t {:.2f} +/- {:.2f} fs".format(popt[2],perr[2],1e6*integral,1e6*dintegral))
plt.plot(x, g2_allA, label="3A x 4A", color=uti.color_chA)
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

xplot, popt, perr = uti.fit(g2_allB, x, -50, +50)
muB = popt[1]; sigmaB = popt[2]
integral, dintegral = uti.integral(popt, perr)
print ("3B x 4B sigma/integral: {:.2f} +/- {:.2f} ns \t {:.2f} +/- {:.2f} fs".format(popt[2],perr[2],1e6*integral,1e6*dintegral))
plt.plot(x, g2_allB, label="3B x 4B", color=uti.color_chB)
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

#xplot, popt, perr = uti.fit(g2_all3Ax4B, x, 90, 140, mu_start=115)
#mu3Ax4B = popt[1]; sigma3Ax4B = popt[2]
#integral, dintegral = uti.integral(popt, perr)
#print ("3A x 4B sigma/integral: {:.2f} +/- {:.2f} ns \t {:.2f} +/- {:.2f} fs".format(popt[2],perr[2],1e6*integral,1e6*dintegral))
#plt.plot(x, g2_all3Ax4B, label="3A x 4B", color=uti.color_c3A4B)
#plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
#
#xplot, popt, perr = uti.fit(g2_all4Ax3B, x, 65, 165, mu_start=115)
#mu4Ax3B = popt[1]; sigma4Ax3B = popt[2]
#integral, dintegral = uti.integral(popt, perr)
#print ("4A x 3B sigma/integral: {:.2f} +/- {:.2f} ns \t {:.2f} +/- {:.2f} fs".format(popt[2],perr[2],1e6*integral,1e6*dintegral))
#plt.plot(x, g2_all4Ax3B, label="4A x 3B", color=uti.color_c4A3B)
#plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

plt.legend(); plt.xlim(-100,200); plt.grid()#; plt.tight_layout()
#plt.ticklabel_format(useOffset=False)
plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")

plt.tight_layout()
#########################
# Shift all peaks to zero
#########################
plt.subplot(212); plt.title("Cable-delay corrected cross correlations")

tbin = timebin(muA); g2_allA = shift_bins(g2_allA, tbin)
tbin = timebin(muB); g2_allB = shift_bins(g2_allB, tbin)
#tbin = timebin(mu3Ax4B); g2_all3Ax4B = shift_bins(g2_all3Ax4B, tbin)
#tbin = timebin(mu4Ax3B); g2_all4Ax3B = shift_bins(g2_all4Ax3B, tbin)

# CAUTION: Never use this for two-color measurements
#g2_avg = average_g2s(g2_allA, g2_allB, g2_all3Ax4B, g2_all4Ax3B)

# Fit for gaining mu and sigma to fix these parameters
xplot, poptA, perrA = uti.fit(g2_allA, x, -100, +100)
mu_A = poptA[1]; sigma_A = poptA[2]
print ("Resolution Ch A: {:.2f} +/- {:.2f}  (ns)".format(sigma_A,perrA[2]))

xplot, poptB, perrB = uti.fit(g2_allB, x, -100, +100)
mu_B = poptB[1]; sigma_B = poptB[2]
print ("Resolution Ch B: {:.2f} +/- {:.2f}  (ns)".format(sigma_B,perrB[2]))


plt.plot(x, g2_allA,     label="3A x 4A", zorder=1, color=uti.color_chA)
plt.plot(xplot, uti.gauss(xplot,*poptA), color="black", linestyle="--", label="Gaussian fit")

plt.plot(x, g2_allB,     label="3B x 4B", zorder=1, color=uti.color_chB)
plt.plot(xplot, uti.gauss(xplot,*poptB), color="black", linestyle="--", label="Gaussian fit")
#plt.plot(x, g2_all3Ax4B, label="3A x 4B", zorder=1, color=uti.color_c3A4B)
#plt.plot(x, g2_all4Ax3B, label="4A x 3B", zorder=1, color=uti.color_c4A3B)

#plt.plot(x, g2_avg, color="grey", linewidth="4", label="Average", zorder=2, alpha=0.7)
#plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--", label="Gaussian fit")

plt.legend(); plt.xlim(-100,100); plt.grid()#; plt.tight_layout()
#plt.ticklabel_format(useOffset=False)
plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")

plt.tight_layout()
plt.savefig("images/{}_cumulative.pdf".format(star))
plt.plot()

#plt.show()


#########################################
###### Chunk analysis ###################
#########################################
# Define colormap for plotting all summarized individual g2 functions
cm_sub = np.linspace(1.0, 0.0, len(chAs))
colors = [cm.viridis(x) for x in cm_sub]

# Define total figure which will show individual g2 cross correlations and averaged auto correlation
# and also the spatial coherence curve (baseline vs. g2 integral)
bigfigure = plt.figure(figsize=(12,7))
# cross correlations
ax_cross = bigfigure.add_subplot(121); ax_cross.set_title("Cross correlations of {}".format(star))
ax_cross.set_xlabel("Time difference (ns)"); ax_cross.set_ylabel("$g^{(2)}$"); ax_cross.ticklabel_format(useOffset=False)
ax_cross.set_xlim(-150,150); ax_cross.set_yticks(np.arange(1,1+2e-6*len(chAs),2e-6))
# spatial coherence
sps1, sps2, sps3, sps4 = GridSpec(2,2)
if star == "Acrux":# broken x axis for better representation later
    ax_sc = brokenaxes(xlims=((0, 10), (73, 120)), subplot_spec=sps2, wspace=0.05, despine=False)
else:
    ax_sc = bigfigure.add_subplot(222)
ax_sc.set_title("Spatial coherence of {}".format(star))
ax_sc.set_xlabel("Baseline (m)"); ax_sc.set_ylabel("Coherence time (fs)")
# auto correlation
ax_auto  = bigfigure.add_subplot(224); ax_auto.set_title("Auto correlation of {}".format(star))
ax_auto.set_xlabel("Time difference (ns)"); ax_auto.set_ylabel("$g^{(2)}$"); ax_auto.ticklabel_format(useOffset=False)
ax_auto.set_xlim(-100,100)
ax_auto.axhline(y=0.0, color='black', linestyle='--')


intsA = []; dintsA = []; times = []
intsB = []; dintsB = []
#ints3Ax4B = []; dints3Ax4B = []
#ints4Ax3B = []; dints4Ax3B = []

ints_fixedA = []; dints_fixedA = []
ints_fixedB = []; dints_fixedB = []

# initialize CT3 and CT4 sum arrays and cleaned arrays
chA_clean = []
chB_clean = []
ct3_clean = []
ct4_clean = []
#c3Ax4B_clean = []
#c4Ax3B_clean = []
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
    #c3Ax4B = c3Ax4Bs[i]
    #c4Ax3B = c4Ax3Bs[i]

    # Do some more data cleaning, e.g. lowpass filters
    chA = cor.lowpass(chA)
    chB = cor.lowpass(chB)
    ct3 = cor.lowpass(ct3)
    ct4 = cor.lowpass(ct4)
    #c3Ax4B = cor.lowpass(c3Ax4B)
    #c4Ax3B = cor.lowpass(c4Ax3B)

    # more data cleaning with notch filter for higher frequencies
    #freqA = [90,130,150]
    #for j in range(len(freqA)):
    #    chA = cor.notch(chA, freqA[j]*1e6, 80)
    #freqB = [90, 110, 130, 150, 250]
    #for j in range(len(freqB)):
    #    chB = cor.notch(chB, freqB[j]*1e6, 80)
    #freq3 = [50, 90, 125, 130, 150, 250]
    #for j in range(len(freq3)):
    #    ct3 = cor.notch(ct3, freq3[j]*1e6, 80)
    #freq4 = [90,130,150,250]
    #for j in range(len(freq4)):
    #    ct4 = cor.notch(ct4, freq4[j]*1e6, 80)

    #freqAB = [90,130,150,250]
    #for j in range(len(freqAB)):
    #    c3Ax4B = cor.notch(c3Ax4B, freqAB[j]*1e6, 80)
    #freqBA = [50,90,110,130]
    #for j in range(len(freqBA)):
    #    c4Ax3B = cor.notch(c4Ax3B, freqBA[j]*1e6, 80)

    # save cleaned data
    chA_clean.append(chA)
    chB_clean.append(chB)
    ct3_clean.append(ct3)
    ct4_clean.append(ct4)
    #c3Ax4B_clean.append(c3Ax4B)
    #c4Ax3B_clean.append(c4Ax3B)

    #########################
    # Shift all peaks to zero
    #########################
    tbin = timebin(muA); chA = shift_bins(chA, tbin)
    tbin = timebin(muB); chB = shift_bins(chB, tbin)
    #tbin = timebin(mu3Ax4B); c3Ax4B = shift_bins(c3Ax4B, tbin)
    #tbin = timebin(mu4Ax3B); c4Ax3B = shift_bins(c4Ax3B, tbin)


    # for autocorrelations of CT3 and CT4 we also average over all acquised data and sum all up
    rms = np.std(ct3[0:4500])
    g2_for_averaging = ct3/rms
    ct3_sum += g2_for_averaging

    rms = np.std(ct4[0:4500])
    g2_for_averaging = ct4/rms
    ct4_sum += g2_for_averaging

    # Averaged cross correlations
    #avg = average_g2s(chA, chB, c3Ax4B, c4Ax3B)
    # additional data cleaning
    #freq_avg = [50,110,130,144.4,150,230]
    #for j in range(len(freq_avg)):
    #    avg = cor.notch(avg, freq_avg[j]*1e6, 80)


    # Fit with fixed mu and sigma
    xplotf, popt_A, perr_A = uti.fit_fixed(chA, x, -100, 100, mu_A, sigma_A)
    Int, dInt = uti.integral_fixed(popt_A, perr_A, sigma_A)
    dInt = np.sqrt( dInt**2 + (np.std(chA)*sigma_A*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
    ints_fixedA.append(1e6*Int); dints_fixedA.append(1e6*dInt)# in femtoseconds

    xplotf, popt_B, perr_B = uti.fit_fixed(chB, x, -100, 100, mu_B, sigma_B)
    Int, dInt = uti.integral_fixed(popt_B, perr_B, sigma_B)
    dInt = np.sqrt( dInt**2 + (np.std(chB)*sigma_B*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
    ints_fixedB.append(1e6*Int); dints_fixedB.append(1e6*dInt)# in femtoseconds

    # Check acquisition time of original data
    timestring = ephem.Date(data[:,0][i])
    print("{}".format(i), timestring, Int, dInt)
    # Shorter timestring for plotting, not showing year and seconds
    tstring_short = str(timestring)[5:-3]

    # FFT check
    #fft = np.abs(np.fft.fft(avg-1))
    #ffts.append(fft)
    
    # Subplot for all cross correlations
    the_shift = (len(chAs)-i-1)*1e-6
    ticks.append(1.+the_shift)
    ax_cross.errorbar(x, chA    + the_shift, yerr=0, linestyle="-", color = uti.color_chA,   alpha=0.7)
    ax_cross.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=popt_A[0], mu=mu_A, sigma=sigma_A, shift=i, inverse=True, ntotal=len(chAs)), color=uti.color_chA, linestyle="--", zorder=4)
    #ax_cross.errorbar(x, c3Ax4B + the_shift, yerr=0, linestyle="-", color = uti.color_c3A4B, alpha=0.5)
    #ax_cross.errorbar(x, c4Ax3B + the_shift, yerr=0, linestyle="-", color = uti.color_c4A3B, alpha=0.5)
    ax_cross.errorbar(x, chB    + the_shift, yerr=0, linestyle="-", color = uti.color_chB,   alpha=0.7)
    ax_cross.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=popt_B[0], mu=mu_B, sigma=sigma_B, shift=i, inverse=True, ntotal=len(chBs)), color=uti.color_chB, linestyle="--", zorder=4)
    #ax_cross.errorbar(x, avg    + the_shift, yerr=0, linestyle="-", color = colors[i], linewidth=3, label=timestring)
    ax_cross.text(x=70, y=1+the_shift+0.7e-6, s=tstring_short, color=colors[i], fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
    


# store cleaned data
np.savetxt("g2_functions/weight_rms_squared/{}/ChA_clean.txt".format(star), np.c_[chA_clean], header="{} Channel A cleaned".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/ChB_clean.txt".format(star), np.c_[chB_clean], header="{} Channel B cleaned".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/CT3_clean.txt".format(star), np.c_[ct3_clean], header="{} CT3 cleaned".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/CT4_clean.txt".format(star), np.c_[ct4_clean], header="{} CT4 cleaned".format(star) )
#np.savetxt("g2_functions/weight_rms_squared/{}/C3Ax4B_clean.txt".format(star), np.c_[c3Ax4B_clean], header="{} CT3A x CT4B cleaned".format(star) )
#np.savetxt("g2_functions/weight_rms_squared/{}/C4Ax3B_clean.txt".format(star), np.c_[c4Ax3B_clean], header="{} CT4A x CT3B cleaned".format(star) )

'''
############################
# Autocorrelation analysis #
############################
# ---- This is the new method ---- #
# Read in the autocorrelation functions
try:
    autocorrelation = np.loadtxt("g2_functions/weight_rms_squared/{}/autocorrelation.txt".format(star))
except:
    print ("No autocorrelation found, please make sure it exists")
    exit(1)

x_auto  = autocorrelation[:,0]
c_auto = autocorrelation[:,1]
# Fit gaussian into autocorrelation
xplotf, popt_avg_free, perr_avg_free = uti.fit(c_auto, x_auto, -30, 30)
int_auto, dint_auto = uti.integral(popt_avg_free, perr_avg_free)

ax_auto.plot(x_auto, c_auto, "o-", color="black", alpha=0.5)
ax_auto.plot(xplotf, uti.gauss(xplotf, *popt_avg_free), linestyle="--", color="red")
ax_auto.set_ylim(1-1*popt_avg_free[0] , 1+2*popt_avg_free[0])
'''
##############################################################
#### making SC plot (spatial coherence) via integral data ####
##############################################################
xplot = np.arange(0.1,300,0.1)

# get baselines for x axes
baselines  = data[:,1]
dbaselines = data[:,2]

# Average over all 4 cross correlations
#ints_avg, dints_avg = uti.weighted_avg(intsA,dintsA, intsB,dintsB, ints3Ax4B,dints3Ax4B, ints4Ax3B, dints4Ax3B)

# Add zero-baseline
#baselines   = np.append(baselines, 5.43) # Average photon distance in a 12 m diameter circle
#dbaselines  = np.append(dbaselines,2.50) # rms distance of photon in a 12 m diameter circle
#ints_fixed  = np.append(ints_fixed,  1e6*int_auto)
#dints_fixed = np.append(dints_fixed, 1e6*dint_auto)
#colors.append( (0,0,0,1.) )


# Calculate SC fit and errorbars for the averaged signal
#poptavg, pcov = curve_fit(uti.spatial_coherence, baselines, ints_fixed, sigma=dints_fixed, p0=[25, 2.2e-9])
#perravg = np.sqrt(np.diag(pcov))

#--------------------#
# Try fitting with ods
# Model object
from scipy import odr

sc_model = odr.Model(uti.spatial_coherence_odr)
# RealData object
rdata = odr.RealData( baselines, ints_fixedA, sx=dbaselines, sy=dints_fixedA )
# Set up ODR with model and data
odrODR = odr.ODR(rdata, sc_model, beta0=[25,2.2e-9])
# Run the regression
out = odrODR.run()
# Fit parameters
popt_odrA = out.beta
perr_odrA = out.sd_beta


sc_modelUV = odr.Model(uti.spatial_coherence_odrUV)
# RealData object
rdataUV = odr.RealData( baselines, ints_fixedB, sx=dbaselines, sy=dints_fixedB )
# Set up ODR with model and data
odrODRUV = odr.ODR(rdataUV, sc_modelUV, beta0=[20,3.2e-9])
# Run the regression
outUV = odrODRUV.run()
# Fit parameters
popt_odrB = outUV.beta; print (popt_odrB)
perr_odrB = outUV.sd_beta
#--------------------#

deltas_sc_avg = []
for i in xplot:
    deltas_sc_avg.append( np.abs(uti.delta_spatial_coherence(x=i, A=poptA[0],dA=perrA[0], phi=poptA[1], dphi=perrA[1])) )
#print ("Angular diameter AVG (fixed): {:.2f} +/- {:.2f} (mas)".format(uti.rad2mas(poptavg[1]),  uti.rad2mas(perravg[1])))
print ("Angular diameter AVG (odr) A : {:.3f} +/- {:.3f} (mas)".format(uti.rad2mas(popt_odrA[1]), uti.rad2mas(perr_odrA[1])))
print ("Angular diameter AVG (odr) B : {:.3f} +/- {:.3f} (mas)".format(uti.rad2mas(popt_odrB[1]), uti.rad2mas(perr_odrB[1])))

####################################################
# plot datapoints in SC plot and fit to all points #
####################################################
# cross and auto correlations
for i in range (0,len(baselines)):
    ax_sc.errorbar(baselines[i], ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
    ax_sc.errorbar(baselines[i], ints_fixedB[i], yerr=dints_fixedB[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chB)
    #plt.text(baselines[i]+1,ints_fixed[i]+0.5,ephem.Date(data[:,0][i]), color=colors[i])
ax_sc.plot(xplot, uti.spatial_coherenceG(xplot,*popt_odrA),   label="470 nm", color="green", linewidth=2)
ax_sc.plot(xplot, uti.spatial_coherenceUV(xplot,*popt_odrB), label="375 nm", color="blue",  linewidth=2)
#ax_sc.plot(xplot, uti.spatial_coherence(xplot, 20, 4.6e-9),   label="fit", color="blue", linewidth=2)
ax_sc.axhline(y=0.0, color='black', linestyle='--')

ax_sc.legend()
plt.tight_layout()
np.savetxt("spatial_coherence/{}_sc_data.txt".format(star), np.c_[baselines, dbaselines, ints_fixedA, dints_fixedA, ints_fixedB, dints_fixedB])
'''
# Obtain values for error band
lower = []; upper = []
for i in xplot:
    uncertainty = uti.get_error_numerical(x=i, amp=popt_odr[0], damp=perr_odr[0], ang=popt_odr[1], dang=perr_odr[1])
    uncertainty = uti.get_error_numerical(x=i, amp=popt_odr[0], damp=perr_odr[0], ang=popt_odr[1], dang=perr_odr[1])

    lower.append(uti.spatial_coherence(i, *popt_odr) - uncertainty)
    upper.append(uti.spatial_coherence(i, *popt_odr) + uncertainty)

lower = cor.lowpass(lower, cutoff=0.001)
upper = cor.lowpass(upper, cutoff=0.001)

ax_sc.set_ylim(0,)
# Special treatment of Acrux: do not fit into the spatial coherence data, instead zoom in
if star != "Acrux":
    ax_sc.fill_between(xplot, lower, upper, color="#003366", alpha=0.15)
    ax_sc.plot(xplot, uti.spatial_coherence(xplot,*popt_odr),   label="ODR fit", color="#003366", linewidth=2)
    ax_sc.text(75, 38, "Angular diameter: {:.2f} +/- {:.2f} mas".format(uti.rad2mas(popt_odr[1]), uti.rad2mas(perr_odr[1])), color="#003366", fontsize=10)
    ax_sc.set_xlim(-15,250)
    ax_sc.legend(loc="upper right")
    plt.tight_layout()
'''
plt.savefig("images/{}_sc.pdf".format(star))
plt.savefig("images/{}_sc.png".format(star))


plt.show()

# Make additional plot scaled
for i in range (0,len(baselines)):
    ints_fixedA[i]  /= popt_odrA[0]
    dints_fixedA[i] /= popt_odrA[0]

    ints_fixedB[i]  /= popt_odrB[0]
    dints_fixedB[i] /= popt_odrB[0]

# cross and auto correlations
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i], ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
    plt.errorbar(baselines[i], ints_fixedB[i], yerr=dints_fixedB[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chB)
    #plt.text(baselines[i]+1,ints_fixed[i]+0.5,ephem.Date(data[:,0][i]), color=colors[i])
plt.plot(xplot, uti.spatial_coherenceG(xplot,1, popt_odrA[1]),   label="470 nm", color="green", linewidth=2)
plt.plot(xplot, uti.spatial_coherenceUV(xplot,1,popt_odrB[1]), label="375 nm", color="blue",  linewidth=2)
#ax_sc.plot(xplot, uti.spatial_coherence(xplot, 20, 4.6e-9),   label="fit", color="blue", linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline (m)")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
plt.xlim(0,200)

plt.legend()

plt.show()

# In addition save also only the spatial coherence values
np.savetxt("sc_measured/{}_scaled.sc".format(star), np.c_[baselines, dbaselines, ints_fixedA, dints_fixedA, ints_fixedB, dints_fixedB], header="{} {} {} {}\nbl\tdbl\tscA\tdscA\tscB\tdscB".format(popt_odrA[0], popt_odrB[0], popt_odrA[1],popt_odrB[1]))
