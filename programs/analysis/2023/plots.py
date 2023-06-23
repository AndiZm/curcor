import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl  
from scipy.optimize import curve_fit
from scipy.signal import butter, filtfilt, find_peaks
from matplotlib.pyplot import cm
import ephem
import scipy.special as scp
import sys
from brokenaxes import brokenaxes
from matplotlib.gridspec import GridSpec

import utilities as uti
import corrections as cor
import geometry as geo

star = sys.argv[1]

xplot = np.arange(0.1,300,0.1)
lam_g = 470e-9
lam_uv = 375e-9

##############################################
####### wavelength independent plots #########
##############################################

# Open text file with SC values for specific star
f = open("sc_measured/{}_scaled.sc".format(star))
header = f.readline()
amp_A = header.split(' ')[1]
amp_B = header.split(' ')[2]
ang_A = header.split(' ')[3]
ang_B = header.split(' ')[4]

baselines    = np.loadtxt("sc_measured/{}_scaled.sc".format(star)) [:,0]
dbaselines   = np.loadtxt("sc_measured/{}_scaled.sc".format(star)) [:,1]
ints_fixedA  = np.loadtxt("sc_measured/{}_scaled.sc".format(star)) [:,2]
dints_fixedA = np.loadtxt("sc_measured/{}_scaled.sc".format(star)) [:,3]
ints_fixedB  = np.loadtxt("sc_measured/{}_scaled.sc".format(star)) [:,4]
dints_fixedB = np.loadtxt("sc_measured/{}_scaled.sc".format(star)) [:,5]


# Open text file with star data from HBT
f = open("stars_HBT.txt")
# Find line for the star
line = f.readline()
while star not in line:
    line = f.readline()
lam_HBT = line.split()[1]
ang_HBT = uti.mas2rad(float(line.split()[2]))
f.close()

# make x-axis wavelength indepedent 
xplot_g = np.zeros(len(xplot))
for i in range(0,len(xplot)):
    xplot_g[i] = ( xplot[i]/(lam_g) )
xplot_uv = np.zeros(len(xplot))
for i in range(0,len(xplot)):
    xplot_uv[i] = ( xplot[i]/(lam_uv) )

# add HBT measurement to the plot
xplot_HBT = np.zeros(len(xplot))
for i in range(0,len(xplot)):
    xplot_HBT[i] = ( xplot[i]/float(lam_HBT) )

# spatial coherence
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i]/(lam_g), ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i]/(lam_g), marker="o", linestyle="", color=uti.color_chA)
    plt.errorbar(baselines[i]/(lam_uv), ints_fixedB[i], yerr=dints_fixedB[i], xerr=dbaselines[i]/(lam_uv), marker="o", linestyle="", color=uti.color_chB)
plt.plot(xplot_g, uti.spatial_coherenceG(xplot,1, float(ang_A)),   label="470 nm", color="green", linewidth=2)
plt.plot(xplot_uv, uti.spatial_coherenceUV(xplot,1,float(ang_B)), label="375 nm", color="blue",  linewidth=2)
plt.plot(xplot_HBT, uti.spatial_coherence(xplot,1, ang_HBT, float(lam_HBT)), label="HBT nm", color="red",  linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline/Wavelength")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("images/{}_sc_scaled_HBT.pdf".format(star))
plt.show()

################################################
##### plots with different stars not scaled ####
################################################

star2 = sys.argv[2]

# Open text file with SC values for specific star
f = open("sc_measured/{}_scaled.sc".format(star))
header = f.readline()
amp_A = header.split(' ')[1]
amp_B = header.split(' ')[2]
ang_A = header.split(' ')[3]
ang_B = header.split(' ')[4]

baselines    = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,0]
dbaselines   = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,1]
ints_fixedA  = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,2]
dints_fixedA = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,3]
ints_fixedB  = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,4]
dints_fixedB = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,5]

# Open text file with SC values for specific star
f = open("sc_measured/{}_scaled.sc".format(star2))
header = f.readline()
amp_A2 = header.split(' ')[1]
amp_B2 = header.split(' ')[2]
ang_A2 = header.split(' ')[3]
ang_B2 = header.split(' ')[4]

baselines2    = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star2)) [:,0]
dbaselines2   = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star2)) [:,1]
ints_fixedA2  = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star2)) [:,2]
dints_fixedA2 = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star2)) [:,3]
ints_fixedB2  = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star2)) [:,4]
dints_fixedB2 = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star2)) [:,5]


# spatial coherence for 470nm
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i], ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
for i in range (0,len(baselines2)):
    plt.errorbar(baselines2[i], ints_fixedA2[i], yerr=dints_fixedA2[i], xerr=dbaselines2[i], marker="o", linestyle="", color=uti.color_chB)
plt.plot(xplot, uti.spatial_coherenceG(xplot,float(amp_A), float(ang_A)),   label="{}".format(star), color="green", linewidth=2)
plt.plot(xplot, uti.spatial_coherenceG(xplot,float(amp_A2),float(ang_A2)), label="{}".format(star2), color="blue",  linewidth=2)
#plt.plot(xplot_HBT, uti.spatial_coherence(xplot,1, ang_HBT, float(lam_HBT)), label="HBT nm", color="red",  linewidth=2)

plt.title("{} & {} for {}nm".format(star, star2, int(lam_g/1e-9)))
plt.xlabel("Projected baseline")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)
plt.legend()
plt.savefig("images/{}_{}_sc_G.pdf".format(star, star2))
plt.show()


# spatial coherence for 375nm
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i], ints_fixedB[i], yerr=dints_fixedB[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
for i in range (0,len(baselines2)):
    plt.errorbar(baselines2[i], ints_fixedB2[i], yerr=dints_fixedB2[i], xerr=dbaselines2[i], marker="o", linestyle="", color=uti.color_chB)
plt.plot(xplot, uti.spatial_coherenceG(xplot,float(amp_B), float(ang_B)),   label="{}".format(star), color="green", linewidth=2)
plt.plot(xplot, uti.spatial_coherenceG(xplot,float(amp_B2),float(ang_B2)), label="{}".format(star2), color="blue",  linewidth=2)
#plt.plot(xplot_HBT, uti.spatial_coherence(xplot,1, ang_HBT, float(lam_HBT)), label="HBT nm", color="red",  linewidth=2)

plt.title("{} & {} for {}nm".format(star, star2, int(lam_uv/1e-9)))
plt.xlabel("Projected baseline")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)
plt.legend()
plt.savefig("images/{}_{}_sc_UV.pdf".format(star, star2))
plt.show()
