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
bl_HBT = []

# Open text file with star data from HBT
f = open("stars_HBT.txt")
# Find line for the star
line = f.readline()
while star not in line:
    line = f.readline()
lam_HBT = line.split()[1]
ang_HBT = uti.mas2rad(float(line.split()[2]))
line = f.readline()
while "[end]" not in line:
    bl_HBT.append(float(line.split()[0]))
    line = f.readline()
f.close()

print(bl_HBT)

##### read in data scaled and unscaled ######

# Open text file with SC values for star 1
f = open("spatial_coherence/{}_scaled.sc".format(star))
header = f.readline()
amp_A = header.split(' ')[1]
amp_B = header.split(' ')[2]
ang_A = header.split(' ')[3]
ang_B = header.split(' ')[4]

baselines    = np.loadtxt("spatial_coherence/{}_scaled.sc".format(star)) [:,0]
dbaselines   = np.loadtxt("spatial_coherence/{}_scaled.sc".format(star)) [:,1]

ints_fixedA_scaled  = np.loadtxt("spatial_coherence/{}_scaled.sc".format(star)) [:,2]
dints_fixedA_scaled = np.loadtxt("spatial_coherence/{}_scaled.sc".format(star)) [:,3]
ints_fixedB_scaled  = np.loadtxt("spatial_coherence/{}_scaled.sc".format(star)) [:,4]
dints_fixedB_scaled = np.loadtxt("spatial_coherence/{}_scaled.sc".format(star)) [:,5]

ints_fixedA  = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,2]
dints_fixedA = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,3]
ints_fixedB  = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,4]
dints_fixedB = np.loadtxt("spatial_coherence/{}_sc_data.txt".format(star)) [:,5]


##############################################
### wavelength dependent plots & scaled ######
##############################################
# spatial coherence
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i], ints_fixedA_scaled[i], yerr=dints_fixedA_scaled[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
    plt.errorbar(baselines[i], ints_fixedB_scaled[i], yerr=dints_fixedB_scaled[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chB)
plt.plot(xplot, uti.spatial_coherence(xplot,1, float(ang_A), lam_g),   label="470 nm", color="green", linewidth=2)
plt.plot(xplot, uti.spatial_coherence(xplot,1, float(ang_B), lam_uv), label="375 nm", color="blue",  linewidth=2)
plt.plot(xplot, uti.spatial_coherence(xplot,1, ang_HBT, float(lam_HBT)), label="HBT {}nm".format(lam_HBT[0:3]), color="red", linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline (m)")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("images/{}_sc_scaled_HBT_lamdependent.pdf".format(star))
plt.savefig("images/{}_sc_scaled_HBT_lamdependent.png".format(star))
plt.show()



##############################################
### wavelength independent plots & scaled ####
##############################################

# make x-axis wavelength indepedent 
xplot_g = np.zeros(len(xplot))
for i in range(0,len(xplot)):
    xplot_g[i] = xplot[i] / lam_g
xplot_uv = np.zeros(len(xplot))
for i in range(0,len(xplot)):
    xplot_uv[i] = xplot[i] /lam_uv

# add HBT measurement to the plot
xplot_HBT = np.zeros(len(xplot))
for i in range(0,len(xplot)):
    xplot_HBT[i] = (xplot[i] /float(lam_HBT))

# spatial coherence
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i]/lam_g, ints_fixedA_scaled[i], yerr=dints_fixedA_scaled[i], xerr=dbaselines[i]/lam_g, marker="o", linestyle="", color=uti.color_chA)
    plt.errorbar(baselines[i]/lam_uv, ints_fixedB_scaled[i], yerr=dints_fixedB_scaled[i], xerr=dbaselines[i]/lam_uv, marker="o", linestyle="", color=uti.color_chB)
plt.plot(xplot_g, uti.spatial_coherence(xplot,1, float(ang_A), lam_g),   label="470 nm", color="green", linewidth=2)
plt.plot(xplot_uv, uti.spatial_coherence(xplot,1, float(ang_B), lam_uv), label="375 nm", color="blue",  linewidth=2)
plt.plot(xplot_HBT, uti.spatial_coherence(xplot,1, ang_HBT, float(lam_HBT)), label="HBT {}nm".format(lam_HBT[0:3]), color="red",  linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline/Wavelength")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("images/{}_sc_scaled_HBT_lamindependent.pdf".format(star))
plt.savefig("images/{}_sc_scaled_HBT_lamindependent.png".format(star))
plt.show()


##############################################
### wavelength dependent plots not scaled ######
##############################################

# spatial coherence
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i], ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
    plt.errorbar(baselines[i], ints_fixedB[i], yerr=dints_fixedB[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chB)
plt.plot(xplot, uti.spatial_coherence(xplot,float(amp_A), float(ang_A), lam_g),   label="470 nm", color="green", linewidth=2)
plt.plot(xplot, uti.spatial_coherence(xplot,float(amp_B),float(ang_B), lam_uv), label="375 nm", color="blue",  linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline (m)")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("images/{}_sc_unscaled_lamdependent.pdf".format(star))
plt.savefig("images/{}_sc_unscaled_lamdependent.png".format(star))
plt.show()


##############################################
### wavelength independent plots not scaled ####
##############################################

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
plt.plot(xplot_g, uti.spatial_coherence(xplot,float(amp_A), float(ang_A), lam_g),   label="470 nm", color="green", linewidth=2)
plt.plot(xplot_uv, uti.spatial_coherence(xplot,float(amp_B),float(ang_B), lam_uv), label="375 nm", color="blue",  linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline/Wavelength")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("images/{}_sc_unscaled_lamindependent.pdf".format(star))
plt.savefig("images/{}_sc_unscaled_lamindependent.png".format(star))
plt.show()



################################################
##### plots with different stars not scaled ####
################################################

if sys.argv[2] == 'Etacen':
    star2 = sys.argv[2]
    # Open text file with SC values for star 2
    f = open("spatial_coherence/{}_scaled.sc".format(star2))
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
    
    ints_fixedA2_scaled  = np.loadtxt("spatial_coherence/{}_scaled.sc".format(star2)) [:,2]
    dints_fixedA2_scaled = np.loadtxt("spatial_coherence/{}_scaled.sc".format(star2)) [:,3]
    ints_fixedB2_scaled  = np.loadtxt("spatial_coherence/{}_scaled.sc".format(star2)) [:,4]
    dints_fixedB2_scaled = np.loadtxt("spatial_coherence/{}_scaled.sc".format(star2)) [:,5]

    # Define total figure for plotting all rates of one night for each channel
    plt.rcParams['figure.figsize'] = 22,10
    fig2, (ax1,ax2) = plt.subplots(1,2, sharey='row')
    # add a big axes, hide frame
    fig2.add_subplot(111, frameon=False)
    
    # spatial coherence for 470nm
    for i in range (0,len(baselines)):
        ax1.errorbar(baselines[i], ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
    for i in range (0,len(baselines2)):
        ax1.errorbar(baselines2[i], ints_fixedA2[i], yerr=dints_fixedA2[i], xerr=dbaselines2[i], marker="o", linestyle="", color=uti.color_chB)
    p1, = ax1.plot(xplot, uti.spatial_coherence(xplot,float(amp_A), float(ang_A), lam_g),   label="{}".format(star), color="green", linewidth=2)
    p2, = ax1.plot(xplot, uti.spatial_coherence(xplot,float(amp_A2),float(ang_A2),lam_g ), label="{}".format(star2), color="blue",  linewidth=2)
    
    # spatial coherence for 375nm
    for i in range (0,len(baselines)):
        ax2.errorbar(baselines[i], ints_fixedB[i], yerr=dints_fixedB[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
    for i in range (0,len(baselines2)):
        ax2.errorbar(baselines2[i], ints_fixedB2[i], yerr=dints_fixedB2[i], xerr=dbaselines2[i], marker="o", linestyle="", color=uti.color_chB)
    p3, = ax2.plot(xplot, uti.spatial_coherence(xplot,float(amp_B), float(ang_B) , lam_uv),   label="{}".format(star), color="green", linewidth=2)
    p4, = ax2.plot(xplot, uti.spatial_coherence(xplot,float(amp_B2),float(ang_B2), lam_uv), label="{}".format(star2), color="blue",  linewidth=2)
    
    ax1.tick_params(labelsize=13)
    ax2.tick_params(labelsize=13)
    ax1.legend(handles=[p1,p2], fontsize=13)
    ax2.legend(handles=[p3,p4], fontsize=13)
    ax1.axhline(y=0.0, color='black', linestyle='--')
    ax2.axhline(y=0.0, color='black', linestyle='--')
    # hide tick label of the big axes
    plt.tick_params(labelcolor="none", top=False, bottom=False, left=False, right=False)
    # set labels for figure
    plt.title("{} & {}".format(star, star2 ), fontsize=17)
    ax1.set_title("{}nm".format(int(np.rint(lam_g/1e-9))), fontsize=17)
    ax2.set_title("{}nm".format(int(lam_uv/1e-9)), fontsize=17)
    fig2.supxlabel("Projected baseline (m)", fontsize=14)
    fig2.supylabel("Spatial coherence", fontsize=14)
    plt.tight_layout()
    fig2.savefig("images/{}_{}_sc_unscaled.pdf".format(star, star2))
    fig2.savefig("images/{}_{}_sc_unscaled.png".format(star, star2))
    plt.show()
    plt.close()
    
    ################################################
    ##### plots with different stars scaled ########
    ################################################
    
    # Define total figure for plotting all rates of one night for each channel
    plt.rcParams['figure.figsize'] = 22,10
    fig1, (ax1,ax2) = plt.subplots(1,2, sharey='row')
    # add a big axes, hide frame
    fig1.add_subplot(111, frameon=False)
    
    # spatial coherence for 470nm
    for i in range (0,len(baselines)):
        ax1.errorbar(baselines[i], ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
    for i in range (0,len(baselines2)):
        ax1.errorbar(baselines2[i], ints_fixedA2[i], yerr=dints_fixedA2[i], xerr=dbaselines2[i], marker="o", linestyle="", color=uti.color_chB)
    p1 ,= ax1.plot(xplot, uti.spatial_coherence(xplot,1, float(ang_A), lam_g),   label="{}".format(star), color="green", linewidth=2)
    p2, = ax1.plot(xplot, uti.spatial_coherence(xplot,1,float(ang_A2), lam_g), label="{}".format(star2), color="blue",  linewidth=2)
    
    # spatial coherence for 375nm
    for i in range (0,len(baselines)):
        ax2.errorbar(baselines[i], ints_fixedB[i], yerr=dints_fixedB[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
    for i in range (0,len(baselines2)):
        ax2.errorbar(baselines2[i], ints_fixedB2[i], yerr=dints_fixedB2[i], xerr=dbaselines2[i], marker="o", linestyle="", color=uti.color_chB)
    p3, = ax2.plot(xplot, uti.spatial_coherence(xplot,1, float(ang_B), lam_uv),   label="{}".format(star), color="green", linewidth=2)
    p4, = ax2.plot(xplot, uti.spatial_coherence(xplot,1,float(ang_B2), lam_uv), label="{}".format(star2), color="blue",  linewidth=2)
    
    
    ax1.tick_params(labelsize=13)
    ax2.tick_params(labelsize=13)
    ax1.legend(handles=[p1,p2], fontsize=13)
    ax2.legend(handles=[p3,p4], fontsize=13)
    ax1.axhline(y=0.0, color='black', linestyle='--')
    ax2.axhline(y=0.0, color='black', linestyle='--')
    # hide tick label of the big axes
    plt.tick_params(labelcolor="none", top=False, bottom=False, left=False, right=False)
    # set labels for figure
    plt.title("{} & {}".format(star, star2 ), fontsize=17)
    ax1.set_title("{}nm".format(int(np.rint(lam_g/1e-9))), fontsize=17)
    ax2.set_title("{}nm".format(int(lam_uv/1e-9)), fontsize=17)
    fig1.supxlabel("Projected baseline (m)", fontsize=14)
    fig1.supylabel("Spatial coherence", fontsize=14)
    plt.tight_layout()
    fig1.savefig("images/{}_{}_sc_scaled.pdf".format(star, star2))
    fig1.savefig("images/{}_{}_sc_scaled.png".format(star, star2))
    plt.show()  

else:
    print("No second star chosen")