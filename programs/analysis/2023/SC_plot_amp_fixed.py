import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl  
from scipy.optimize import curve_fit
from scipy.signal import butter, filtfilt, find_peaks
import scipy.stats as stats
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

# make colors for plotting
colorA14 = uti.color_chA
colorA34 = 'limegreen'


# read in amplitudes 
amp_Etacen  = np.loadtxt("spatial_coherence/Etacen/amplitudes_odr.sc") [0]
amp_Etacen1 = np.loadtxt("spatial_coherence/Etacen/amplitudes_odr.sc") [4]
amp_Mimosa  = np.loadtxt("spatial_coherence/Mimosa/amplitudes_odr.sc") [0]
amp_Mimosa1 = np.loadtxt("spatial_coherence/Mimosa/amplitudes_odr.sc") [4]
amp_Nunki   = np.loadtxt("spatial_coherence/Nunki/amplitudes_odr.sc")  [0]

amp_Etacen = amp_Etacen + amp_Etacen1
amp_Mimosa = amp_Mimosa + amp_Mimosa1
amp_all = (amp_Etacen + amp_Mimosa + amp_Nunki)/5
print(amp_all)

telcombis = [14,34]
lam_g = 470e-9       
# make x-axis wavelength indepedent 
xplot = np.arange(0.1,300,0.1)
xplot_g = np.zeros(len(xplot))
for j in range(0,len(xplot)):
    xplot_g[j] = xplot[j] / lam_g

# Define figure showing all tel combos with one fit
SCfigure = plt.figure(figsize=(10,7))
ax_sc = plt.subplot(111)
ax_sc.set_title("Spatial coherence of {}". format(star))
ax_sc.set_xlabel("Baseline/Wavelength"); ax_sc.set_ylabel("Coherence time (fs)") 
ax_sc.set_xlim(-1e7,5e8)

def spatial_coherence(x, ang, amp=amp_all, lam=lam_g):
    return amp * (2*scp.j1(np.pi * x * ang/lam) / (np.pi* x * ang/lam))**2


# for loop over telescope combinations
for i in range(len(telcombis)):
    # read in all necessary data and parameters
    timestrings = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,6]
    baselines     = np.loadtxt("spatial_coherence/{}/{}_{}_data.sc".format(star,star,telcombis[i])) [:,0]
    dbaselines    = np.loadtxt("spatial_coherence/{}/{}_{}_data.sc".format(star,star,telcombis[i])) [:,1]
    ints_fixedA   = np.loadtxt("spatial_coherence/{}/{}_{}_data.sc".format(star,star,telcombis[i])) [:,2]
    dints_fixedA  = np.loadtxt("spatial_coherence/{}/{}_{}_data.sc".format(star,star,telcombis[i])) [:,3]
    ints_fixedA1  = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,2]
    dints_fixedA1 = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,3]
    
    #--------------------#
    # Try fitting with ods
    # Model object
    from scipy import odr
    
    sc_modelG = odr.Model(spatial_coherence)
    # RealData object
    rdataG = odr.RealData( baselines, ints_fixedA, sx=dbaselines, sy=dints_fixedA )
    # Set up ODR with model and data
    odrODRG = odr.ODR(rdataG, sc_modelG, beta0=[2.2e-9])
    # Run the regression
    outG = odrODRG.run()
    # Fit parameters
    popt_odrA = outG.beta
    perr_odrA = outG.sd_beta
    chi_odrA = outG.res_var # chi squared value

    print("SC fits")
    print("{}A 470nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t fixed Amplitude: {:.2f}\t Chi^2 reduced: {:.2f}".format(telcombis[i], uti.rad2mas(float(popt_odrA)), uti.rad2mas(float(perr_odrA)), amp_all, chi_odrA))


    ### Plot SC data ###
    if telcombis[i] == 14:
        color  = colorA14
        amp_A  = np.loadtxt("spatial_coherence/{}/amplitudes_odr.sc".format(star)) [0]
        damp_A = np.loadtxt("spatial_coherence/{}/amplitudes_odr.sc".format(star)) [1]
        ang_A  = np.loadtxt("spatial_coherence/{}/angular_dia_odr.sc".format(star)) [0]
        dang_A = np.loadtxt("spatial_coherence/{}/angular_dia_odr.sc".format(star)) [1]
        a = 0.8
    else:
        color  = 'limegreen'
        amp_A  = np.loadtxt("spatial_coherence/{}/amplitudes_odr.sc".format(star)) [4]
        damp_A = np.loadtxt("spatial_coherence/{}/amplitudes_odr.sc".format(star)) [5]
        ang_A  = np.loadtxt("spatial_coherence/{}/angular_dia_odr.sc".format(star)) [4]
        dang_A = np.loadtxt("spatial_coherence/{}/angular_dia_odr.sc".format(star)) [5]
        a = 0.6
    
    print("{}A 470nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t Amplitude:{:.2f} +/- {:.2f}".format(telcombis[i], uti.rad2mas(float(ang_A)), uti.rad2mas(float(dang_A)), amp_A, damp_A ))
    label = '{}A 470nm'.format(telcombis[i])

    for k in range (0,len(baselines)):
        ax_sc.errorbar(baselines[k]/lam_g, ints_fixedA[k],  yerr=dints_fixedA[k], xerr=dbaselines[k]/lam_g, marker="o", linestyle="", color=color)
    ax_sc.plot(xplot_g, uti.spatial_coherence(xplot, float(amp_A), float(ang_A), lam_g), label=label, color=color, linewidth=2)
    ax_sc.errorbar(xplot_g[0],  uti.spatial_coherence(xplot[0],float(amp_A), float(ang_A), lam_g),  yerr=damp_A, marker='x', color=color )

    #ax_sc.fill_between(xplot_g, uti.spatial_coherence(xplot,amp_A+damp_A, ang_A-dang_A, lam_g), uti.spatial_coherence(xplot, amp_A-damp_A, ang_A+dang_A, lam_g), color=color, alpha=0.3)
    ax_sc.plot(xplot_g, uti.spatial_coherence(xplot, float(amp_all), float(popt_odrA), lam_g), label='fixed amplitude', color=color, linewidth=2, ls='--', alpha=a)


plt.legend()
plt.show()


















