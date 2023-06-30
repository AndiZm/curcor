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


star = 'Nunki'
xplot = np.arange(0.1,300,0.1)
lam_new = 470e-9
lam_old = 465e-9


# Open text file with SC values for Nunki 2022
f = open("Nunki/{}_sc_data.txt".format(star))
header = f.readline()
amp_A_old = header.split(' ')[1]
ang_A_old = header.split(' ')[2]

baselines_old    = np.loadtxt("Nunki/{}_sc_data.txt".format(star)) [:,0]
dbaselines_old   = np.loadtxt("Nunki/{}_sc_data.txt".format(star)) [:,1]
ints_fixedA_old  = np.loadtxt("Nunki/{}_sc_data.txt".format(star)) [:,2]
dints_fixedA_old = np.loadtxt("Nunki/{}_sc_data.txt".format(star)) [:,3]

for i in range(0,len(baselines_old)):
	ints_fixedA_old[i]  /= float(amp_A_old)
	dints_fixedA_old[i] /= float(amp_A_old)


# Open text file with SC values for Nunki 2023
f = open("sc_measured/{}_scaled.sc".format(star))
header = f.readline()
amp_A = header.split(' ')[1]
ang_A = header.split(' ')[3]

baselines    = np.loadtxt("sc_measured/{}_scaled.sc".format(star)) [:,0]
dbaselines   = np.loadtxt("sc_measured/{}_scaled.sc".format(star)) [:,1]
ints_fixedA  = np.loadtxt("sc_measured/{}_scaled.sc".format(star)) [:,2]
dints_fixedA = np.loadtxt("sc_measured/{}_scaled.sc".format(star)) [:,3]


##############################################
### wavelength dependent plots & scaled ######
##############################################
# spatial coherence
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i], ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
for i in range(0,len(baselines_old)):    
    plt.errorbar(baselines_old[i], ints_fixedA_old[i], yerr=dints_fixedA_old[i], xerr=dbaselines_old[i], marker="o", linestyle="", color=uti.color_chB)
plt.plot(xplot, uti.spatial_coherence(xplot,1, float(ang_A), lam_new),   label="2023 470 nm", color="green", linewidth=2)
plt.plot(xplot, uti.spatial_coherence(xplot,1, float(ang_A_old), lam_old),   label="2022 465 nm", color="blue", linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline (m)")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("Nunki/{}_sc_scaled.pdf".format(star))
plt.savefig("Nunki/{}_sc_scaled.png".format(star))
plt.show()



##############################################
### wavelength independent plots & scaled ####
##############################################

# make x-axis wavelength indepedent 
xplot_new = np.zeros(len(xplot))
for i in range(0,len(xplot)):
    xplot_new[i] = ( xplot[i]/(lam_new) )
xplot_old = np.zeros(len(xplot))
for i in range(0,len(xplot)):
    xplot_old[i] = ( xplot[i]/(lam_old) )

# spatial coherence
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i]/(lam_new), ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i]/(lam_new), marker="o", linestyle="", color=uti.color_chA)
for i in range(0,len(baselines_old)):
    plt.errorbar(baselines_old[i]/(lam_old), ints_fixedA_old[i], yerr=dints_fixedA_old[i], xerr=dbaselines_old[i]/(lam_old), marker="o", linestyle="", color=uti.color_chB)
plt.plot(xplot_new, uti.spatial_coherence(xplot,1, float(ang_A), lam_new),    label="2023 470 nm", color="green", linewidth=2)
plt.plot(xplot_old, uti.spatial_coherence(xplot,1,float(ang_A_old), lam_old), label="2022 465 nm", color="blue",  linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline/Wavelength")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("Nunki/{}_sc_scaled_lamindependent.pdf".format(star))
plt.savefig("Nunki/{}_sc_scaled_lamindependent.png".format(star))
plt.show()



##############################################
### wavelength dependent plots not scaled ######
##############################################
# read in not scaled data from Nunki 2022
baselines_old    = np.loadtxt("Nunki/{}_sc_data.txt".format(star)) [:,0]
dbaselines_old   = np.loadtxt("Nunki/{}_sc_data.txt".format(star)) [:,1]
ints_fixedA_old  = np.loadtxt("Nunki/{}_sc_data.txt".format(star)) [:,2]
dints_fixedA_old = np.loadtxt("Nunki/{}_sc_data.txt".format(star)) [:,3]

# read in not scaled data for Nunki 2023
baselines    = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,0]
dbaselines   = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,1]
ints_fixedA  = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,2]
dints_fixedA = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,3]

# spatial coherence
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i], ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
for i in range(0, len(baselines_old)):
    plt.errorbar(baselines_old[i], ints_fixedA_old[i], yerr=dints_fixedA_old[i], xerr=dbaselines_old[i], marker="o", linestyle="", color=uti.color_chB)
plt.plot(xplot, uti.spatial_coherence(xplot,float(amp_A), float(ang_A), lam_new),   label="2023 470 nm", color="green", linewidth=2)
plt.plot(xplot, uti.spatial_coherence(xplot,float(amp_A_old),float(ang_A_old), lam_old), label="2022 465 nm", color="blue",  linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline (m)")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("Nunki/{}_sc_unscaled_lamdependent.pdf".format(star))
plt.savefig("Nunki/{}_sc_unscaled_lamdependent.png".format(star))
plt.show()


##############################################
### wavelength independent plots not scaled ####
##############################################


# spatial coherence
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i]/(lam_new), ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i]/(lam_new), marker="o", linestyle="", color=uti.color_chA)
for i in range(0,len(baselines_old)):
    plt.errorbar(baselines_old[i]/(lam_old), ints_fixedA_old[i], yerr=dints_fixedA_old[i], xerr=dbaselines_old[i]/(lam_old), marker="o", linestyle="", color=uti.color_chB)
plt.plot(xplot_new, uti.spatial_coherence(xplot,float(amp_A), float(ang_A), lam_new),   label="2023 470 nm", color="green", linewidth=2)
plt.plot(xplot_old, uti.spatial_coherence(xplot,float(amp_A_old),float(ang_A_old), lam_old), label="2022 465 nm", color="blue",  linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline/Wavelength")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("Nunki/{}_sc_unscaled_lamindependent.pdf".format(star))
plt.savefig("Nunki/{}_sc_unscaled_lamindependent.png".format(star))
plt.show()

