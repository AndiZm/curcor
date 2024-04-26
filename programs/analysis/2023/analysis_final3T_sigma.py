import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
import ephem
import sys
import os
from scipy import odr
from collections import OrderedDict
from optparse import OptionParser

import utilities as uti
import corrections as cor
import par_fixing_all as pfa

star = sys.argv[1]

# Option parser for options
parser = OptionParser()
parser.add_option("-o", "--only", dest="onlys", help="only telescope combinations")

(options, args) = parser.parse_args()
onlys = str(options.onlys)

if onlys != "None":
    onlys = onlys.split(",")

bl_HBT = []
# Open text file with star data from HBT
f = open("stars_HBT.txt")
# Find line for the star
line = f.readline()
while star not in line:
    line = f.readline()
lam_HBT = line.split()[1]
ang_HBT = uti.mas2rad(float(line.split()[2]))
logg_star = line.split()[3]
temp_star = int(line.split()[4])
line = f.readline()
while "[end]" not in line:
    bl_HBT.append(float(line.split()[0]))
    line = f.readline()
f.close()

combicolorsA = np.zeros((5,5), dtype=object); combicolorsA[:] = np.nan
combicolorsA[1,3] = 'lightblue'
combicolorsA[1,4] = 'deepskyblue'
combicolorsA[3,4] = 'dodgerblue'

combicolorsB = np.zeros((5,5), dtype=object); combicolorsB[:] = np.nan
combicolorsB[1,3] = 'mediumpurple'
combicolorsB[1,4] = 'blueviolet'
combicolorsB[3,4] = 'purple'

combicolors = np.zeros((5,5), dtype=object); combicolors[:] = np.nan
combicolors[1,3] = "blue"
combicolors[1,4] = "fuchsia"
combicolors[3,4] = "turquoise"

lam_g = 470e-9
lam_uv = 375e-9
lam_all = 422.5e-9
amp_g = 21.25
amp_uv = 10

################################################
####### Cleaning the measurement data ##########
################################################
chA_clean = np.zeros((5,5), dtype=object); chA_clean[:] = np.nan 
chB_clean = np.zeros((5,5), dtype=object); chB_clean[:] = np.nan 
def cleaning(star, telcombi):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)  

    chAs = np.loadtxt("g2_functions/{}/{}/chA.g2".format(star, telstring))
    chBs = np.loadtxt("g2_functions/{}/{}/chB.g2".format(star, telstring))
    chA_clean[c1][c2] = np.zeros(len(chAs), dtype=object)
    chB_clean[c1][c2] = np.zeros(len(chBs), dtype=object)

    # loop over every g2 function chunk
    for i in range(0,len(chAs)):
        # Read g2 function
        chA = chAs[i]
        chB = chBs[i]
        # Do some more data cleaning, e.g. lowpass filters
        chA = cor.lowpass(chA)
        chB = cor.lowpass(chB)

        '''
        ### building fft of g2 to cut out noise ###
        F_fft = plt.figure(figsize=(12,7))
        ax1 = F_fft.add_subplot(121)
        stepsize = 1.6e-3                   # sampling bin size
        N = len(chA)
        chAfft = chA # für auto corr teil ohne crosstalk [5500:10000]            
        N = len(chAfft)
        xfft = np.linspace(0.0, stepsize*N, N)
        ax1.plot(xfft, chAfft, label='A') 
        x_fft = np.linspace(0.0, 1./(2.*stepsize), N//2) #N2//2)
        chA_fft = np.abs(np.fft.fft(chAfft)/(N/2)) # ct4_fft = np.abs(np.fft.fft(ct4)/(N2))
        #chA_freq, rest = find_peaks(chA_fft, threshold=[0.5e-8, 1.e-8], width=[0,5])
        #print(chA_freq)
        ax2 = F_fft.add_subplot(122)
        ax2.plot(x_fft, chA_fft[0:N//2], label='A')
        '''
        # more data cleaning with notch filter for higher frequencies
        freqA = [45,95,110,145,155,175,195]
        for j in range(len(freqA)):
            chA = cor.notch(chA, freqA[j]*1e6, 80)
        freqB = [50,90,110]
        for j in range(len(freqB)):
            chB = cor.notch(chB, freqB[j]*1e6, 80)
    
        '''
        ### Plot g2 after cleaning ####
        chAfft = chA
        ax1.plot(xfft, chAfft, label='A')
        ax1.legend()
        ax1.set_xlabel('bins of 1.6ns')
        chA_fft = np.abs(np.fft.fft(chAfft)/(N/2))
        ax2.plot(x_fft, chA_fft[0:N//2], label='A')
        ax2.set_ylim(0,8e-8)
        ax2.legend()
        ax2.set_xlabel('MHz')
        #plt.show()
        plt.close()
        '''    
        chA_clean[c1,c2][i] = chA
        chB_clean[c1,c2][i] = chB
    print("Cleaning done")

##########################################
####### Chunk analysis ###################
##########################################
plt.figure('SC', figsize=(12,8))
plt.suptitle("Spatial coherence of {}".format(star))

plt.figure('SC Amp', figsize=(12,8))
plt.suptitle("Spatial coherence of {} with fixed zero baseline".format(star))

ints_fixedA = []; dints_fixedA = []
ints_fixedB = []; dints_fixedB = []
baselines_all = []; dbaselines_all = []
time_all = [] ; telstrings =[]
baselinesA = []; dbaselinesA = []
baselinesB = []; dbaselinesB = []

def chunk_ana(star, telcombi):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)  
    
    chAs = chA_clean[c1,c2]  
    chBs = chB_clean[c1,c2]  

    # Read the telescope data (acquisition times of chunks, baselines and baseline uncertainties)
    timestrings = np.loadtxt("g2_functions/{}/{}/ac_times.txt".format(star,telstring))
    baselines   = np.loadtxt("g2_functions/{}/{}/baselines.txt".format(star,telstring))
    dbaselines  = np.loadtxt("g2_functions/{}/{}/dbaselines.txt".format(star,telstring))
    
    # Demo function for initializing x axis and some stuff
    demo = chAs[0]
    x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)
    
    # loop over every g2 function chunk
    for i in range(0,len(chAs)):
        # Check acquisition time of original data
        timestring = ephem.Date(timestrings[i])
        tstring_short = str(timestring)[5:-3]
        baseline   = baselines[i]
        dbaseline  = dbaselines[i]
        baselines_all.append(baseline); dbaselines_all.append(dbaseline)
        time_all.append(timestring)
        telstrings.append(telstring)  
    
        # Read g2 function
        chA = chAs[i]
        chB = chBs[i]

        ### taking all data into account
        xplotf, popt_A, perr_A = uti.fit_fixed(chA, x, -50, 50,  pfa.avg_sigA)
        Int  = uti.integral_fixed(popt_A, perr_A, pfa.avg_sigA)
        dInt = uti.simulate_uncertainty(g2=chA, x=x, popt=popt_A, sigma=pfa.avg_sigA)
        ints_fixedA.append(1e6*Int); dints_fixedA.append(1e6*dInt)# in femtoseconds
        baselinesA.append(baseline); dbaselinesA.append(dbaseline)
        plt.figure('SC')
        plt.subplot(121)
        plt.title("470nm")
        plt.errorbar(x=baseline, xerr=dbaseline, y=1e6*Int, yerr=1e6*dInt, marker='o', color=combicolors[c1][c2], label=telstring)
        plt.figure('SC Amp')
        plt.subplot(121)
        plt.title("470nm")
        plt.errorbar(x=baseline, xerr=dbaseline, y=1e6*Int, yerr=1e6*dInt, marker='o', color=combicolors[c1][c2], label=telstring)

        xplotf, popt_B, perr_B = uti.fit_fixed(chB, x, -50, 50, pfa.avg_sigB)
        Int  = uti.integral_fixed(popt_B, perr_B, pfa.avg_sigB)
        dInt = uti.simulate_uncertainty(g2=chB, x=x, popt=popt_B, sigma=pfa.avg_sigB)
        ints_fixedB.append(1e6*Int); dints_fixedB.append(1e6*dInt)# in femtoseconds
        baselinesB.append(baseline); dbaselinesB.append(dbaseline)
        plt.figure("SC")
        plt.subplot(122)
        plt.title("375nm")
        plt.errorbar(x=baseline, xerr=dbaseline, y=1e6*Int, yerr=1e6*dInt, marker='o', color=combicolors[c1][c2], label=telstring)
        plt.figure('SC Amp')
        plt.subplot(122)
        plt.title("375nm")
        plt.errorbar(x=baseline, xerr=dbaseline, y=1e6*Int, yerr=1e6*dInt, marker='o', color=combicolors[c1][c2], label=telstring)
        print("{}".format(i), timestring, Int, dInt) 

    print("DONE Chunks {}".format(telcombi))

amplitudes = []

def plotting(star): 
    ##### plot baselines vs time #####
    print('Start plotting')
    print('BASELINES')
    plt.figure("baselines")
    plt.title("{}".format(star))
    plt.xlabel("Acquisition time")
    plt.ylabel("Telescope baseline (m)")

    sorted_indices = np.argsort(time_all)
    sorted_time = np.array(time_all)[sorted_indices]
    sorted_baselines = np.array(baselines_all)[sorted_indices]
    sorted_db = np.array(dbaselines_all)[sorted_indices]
    sorted_telstring = np.array(telstrings)[sorted_indices]

    for i in range(0,len(time_all)):
        # Check acquisition time of original data
        timestring = ephem.Date(sorted_time[i])
        t_short = str(timestring)[5:-3]
        baseline = sorted_baselines[i]
        dbaseline = sorted_db[i]
        telstr = sorted_telstring[i]
        col1, col2 = telstr.split()[0]
        c1 = int(col1)
        c2 = int(col2)

        # Draw "new night" lines into the plot, if there is a new night
        if i != 0:
            t1 = sorted_time[i-1]
            t2 = sorted_time[i]
            if np.floor(t2) - np.floor(t1) > 0:
                plt.axvline(t_short, color='darkgrey', label='new night')

        plt.errorbar(x=t_short, y=baseline, yerr=dbaseline, marker="o", linestyle="", label=telstr, color=combicolors[c1][c2])
        plt.xticks(rotation=45)

    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles)) 
    plt.legend(by_label.values(), by_label.keys()); plt.tight_layout()
    print('LENGTHS', len(baselinesA), len(ints_fixedA), len(baselinesB), len(ints_fixedB), len(baselines_all))

    #--------------------#
    # Try fitting with ods
    # Uniform disk model object    
    sc_modelG = odr.Model(uti.spatial_coherence_odrG)
    # RealData object
    rdataG = odr.RealData( baselinesA, ints_fixedA, sx=dbaselinesA, sy=dints_fixedA )
    # Set up ODR with model and data
    odrODRG = odr.ODR(rdataG, sc_modelG, beta0=[15,2.2e-9])
    # Run the regression
    outG = odrODRG.run()
    # Fit parameters
    popt_odrA = outG.beta
    perr_odrA = outG.sd_beta
    chi_odrA = outG.res_var # chi squared value
    
    sc_modelUV = odr.Model(uti.spatial_coherence_odrUV)
    # RealData object
    rdataUV = odr.RealData( baselinesB, ints_fixedB, sx=dbaselinesB, sy=dints_fixedB )
    # Set up ODR with model and data
    odrODRUV = odr.ODR(rdataUV, sc_modelUV, beta0=[10,3.2e-9])
    # Run the regression
    outUV = odrODRUV.run()
    # Fit parameters
    popt_odrB = outUV.beta
    perr_odrB = outUV.sd_beta
    chi_odrB  = outUV.res_var # chi squared value
    #--------------------#

    print("SC fits")
    print("A 470nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t Amplitude: {:.2f} +/- {:.2f}\t Chi^2 reduced: {:.2f}".format(uti.rad2mas(popt_odrA[1]), uti.rad2mas(perr_odrA[1]), popt_odrA[0], perr_odrA[0], chi_odrA))
    print("B 375nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t Amplitude: {:.2f} +/- {:.2f}\t Chi^2 reduced: {:.2f}".format(uti.rad2mas(popt_odrB[1]), uti.rad2mas(perr_odrB[1]), popt_odrB[0], perr_odrB[0], chi_odrB))
    
    #### Fix the LD issue with u !!!!!
    ## get LD coeff
    #u = uti.get_u(temp_star, logg_star)
    #print(u)

    #--------------------#
    # Try fitting with ods
    # Limb darkening model object
    sc_model_ld = odr.Model(uti.spatial_coherence_odrG_LD)
    # Set up ODR with model and data
    odrODR_ld = odr.ODR(rdataG, sc_model_ld, beta0=[15,2.7e-9])
    # Run the regression
    out_ld = odrODR_ld.run()
    # Fit parameters
    popt_odrG_LD = out_ld.beta
    perr_odrG_LD = out_ld.sd_beta
    chi_odrG_LD  = out_ld.res_var # chi squared value
    #--------------------#

    print("SC fit limb darkening")
    print("A 470nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t Amplitude: {:.2f} +/- {:.2f}\t Chi^2 reduced: {:.2f}".format(uti.rad2mas(popt_odrG_LD[1]), uti.rad2mas(perr_odrG_LD[1]), popt_odrG_LD[0], perr_odrG_LD[0], chi_odrG_LD))

    # save fitted amplitude
    amplitudes.append(popt_odrA[0]); amplitudes.append(perr_odrA[0])
    amplitudes.append(popt_odrB[0]); amplitudes.append(perr_odrB[0])
    #ang_odr.append(popt_odrA[1]); ang_odr.append(perr_odrA[1])
    #ang_odr.append(popt_odrB[1]); ang_odr.append(perr_odrB[1])

    global onlys
    if onlys != "None" and len(onlys) == 1:
        print(onlys, onlys[0])
        np.savetxt('g2_functions/{}/{}/amplitudes.txt'.format(star,onlys[0]), np.c_[amplitudes], header='ampA, dampA, ampB, dampB')

    
    # make x-axis wavelength indepedent 
    xplot = np.arange(0.1,300,0.1)
    xplot_g = np.zeros(len(xplot))
    for j in range(0,len(xplot)):
        xplot_g[j] = xplot[j] / lam_g
    xplot_uv = np.zeros(len(xplot))
    for j in range(0,len(xplot)):
        xplot_uv[j] = xplot[j] /lam_uv
    xplot_all = np.zeros(len(xplot))
    for j in range(0,len(xplot)):
        xplot_all[j] = xplot[j] /lam_all
#    # add HBT measurement to the plot
#    xplot_HBT = np.zeros(len(xplot))
#    for j in range(0,len(xplot)):
#        xplot_HBT[j] = (xplot[j] /float(lam_HBT))
#
#        # Nullstelle for SC plot
#        nsA = 1.22*(lam_g/popt_odrA[1])
#        nsB = 1.22*(lam_uv/popt_odrB[1])

    # plot SC fit and error band
    # plot channel A 470nm green
    plt.figure("SC")
    plt.subplot(121)
    plt.plot(xplot, uti.spatial_coherence(xplot,*popt_odrA, lam_g), linewidth=2, color='darkgrey', label='uniform disk')
    plt.fill_between(xplot, uti.spatial_coherence(xplot,popt_odrA[0]+perr_odrA[0],popt_odrA[1]-perr_odrA[1], lam_g), uti.spatial_coherence(xplot,popt_odrA[0]-perr_odrA[0],popt_odrA[1]+perr_odrA[1], lam_g), alpha=0.3, color='darkgrey')
    # get LD coeff
    u = uti.get_u(temp_star, logg_star)
    print(u)
    # plot limb darkening fit
    plt.figure("SC")
    plt.subplot(121)
    plt.plot(xplot, uti.spatial_coherence_LD(xplot,*popt_odrG_LD, lam_g, u=u), linewidth=2, color='orange', label='limb darkening')
    plt.fill_between(xplot, uti.spatial_coherence_LD(xplot,popt_odrG_LD[0]+perr_odrG_LD[0],popt_odrG_LD[1]-perr_odrG_LD[1], lam_g, u=u), uti.spatial_coherence_LD(xplot,popt_odrG_LD[0]-perr_odrG_LD[0],popt_odrG_LD[1]+perr_odrG_LD[1], lam_g, u=0.37), alpha=0.3, color='orange')
    # legend 
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles)) 
    plt.legend(by_label.values(), by_label.keys())
    # text
    ymin, ymax = plt.gca().get_ylim()
    plt.text(80, ymax-3.5, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrA[1]), uti.rad2mas(perr_odrA[1])), color='grey')
    plt.text(80, ymax-4, s='$\chi^2$/dof={:.2f}'.format(chi_odrA), color='grey')
    plt.text(80, ymax-4.5, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrG_LD[1]), uti.rad2mas(perr_odrG_LD[1])), color='orange')
    plt.text(80, ymax-5, s='$\chi^2$/dof={:.2f}'.format(chi_odrG_LD), color='orange')
    plt.xlim(0,200)
    plt.xlabel("Projected baseline (m)")
    plt.ylabel("Spatial coherence (fs)")
    plt.axhline(y=0, color="black", linestyle="--")  
    plt.tight_layout()

    # plot channel B 375nm uv
    plt.subplot(122)
    plt.plot(xplot, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), linewidth=2, color='darkgrey', label='uniform disk')
    plt.fill_between(xplot, uti.spatial_coherence(xplot,popt_odrB[0]+perr_odrB[0],popt_odrB[1]-perr_odrB[1], lam_uv), uti.spatial_coherence(xplot,popt_odrB[0]-perr_odrB[0],popt_odrB[1]+perr_odrB[1], lam_uv), alpha=0.2, color='darkgrey')
    plt.xlabel("Projected baseline (m)")
    plt.ylabel("Spatial coherence (fs)")
    plt.axhline(y=0, color='black', linestyle="--")
    # legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles)) 
    plt.legend(by_label.values(), by_label.keys())
    # text
    ymin, ymax = plt.gca().get_ylim()
    plt.text(80, ymax-5, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrB[1]), uti.rad2mas(perr_odrB[1])), color='grey')
    plt.text(80, ymax-5.5, s='$\chi^2$/dof={:.2f}'.format(chi_odrB), color='grey')
    plt.xlim(0,200)
    plt.tight_layout()

    #### plot both colors in one plot ###
    plt.figure("SC combi")
    # plot channel A 470nm blue and  channel B 375nm uv
    for k in range(len(baselinesA)):
        plt.errorbar(x=baselinesA[k]/lam_g,  xerr=dbaselinesA[k]/lam_g,  y=ints_fixedA[k], yerr=dints_fixedA[k], marker='o', linestyle=' ', color=uti.color_chA)
    for k in range(len(baselinesB)):
        plt.errorbar(x=baselinesB[k]/lam_uv, xerr=dbaselinesB[k]/lam_uv, y=ints_fixedB[k], yerr=dints_fixedB[k], marker='o', linestyle=' ', color=uti.color_chB)

    plt.plot(xplot_g, uti.spatial_coherence(xplot,*popt_odrA, lam_g), linewidth=2, color=uti.color_chA, label='470nm UD')
    plt.fill_between(xplot_g, uti.spatial_coherence(xplot,popt_odrA[0]+perr_odrA[0],popt_odrA[1]-perr_odrA[1], lam_g), uti.spatial_coherence(xplot,popt_odrA[0]-perr_odrA[0],popt_odrA[1]+perr_odrA[1], lam_g), alpha=0.3, color=uti.color_chA)
    plt.plot(xplot_uv, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), linewidth=2, color=uti.color_chB, label='375nm UD')
    plt.fill_between(xplot_uv, uti.spatial_coherence(xplot,popt_odrB[0]+perr_odrB[0],popt_odrB[1]-perr_odrB[1], lam_uv), uti.spatial_coherence(xplot,popt_odrB[0]-perr_odrB[0],popt_odrB[1]+perr_odrB[1], lam_uv), alpha=0.3, color=uti.color_chB)
    plt.title("Spatial coherence of {}".format(star))
    plt.xlabel("Baseline/Wavelength"); plt.ylabel("Spatial coherence (fs)") 
    plt.axhline(y=0, color='black', linestyle="--")
    plt.xlim(0,4e8)
    plt.legend()


    #### Make SC fit with fixed zero baseline ####
    
    #--------------------#
    # Try fitting with ods
    # Uniform disk model object    
    sc_modelG = odr.Model(uti.spatial_coherence_odrG_amp)
    # RealData object
    rdataG = odr.RealData( baselinesA, ints_fixedA, sx=dbaselinesA, sy=dints_fixedA )
    # Set up ODR with model and data
    odrODRG = odr.ODR(rdataG, sc_modelG, beta0=[2.2e-9])
    # Run the regression
    outG = odrODRG.run()
    # Fit parameters
    popt_odrA = outG.beta
    perr_odrA = outG.sd_beta
    chi_odrA = outG.res_var # chi squared value
    
    sc_modelUV = odr.Model(uti.spatial_coherence_odrUV_amp)
    # RealData object
    rdataUV = odr.RealData( baselinesB, ints_fixedB, sx=dbaselinesB, sy=dints_fixedB )
    # Set up ODR with model and data
    odrODRUV = odr.ODR(rdataUV, sc_modelUV, beta0=[3.2e-9])
    # Run the regression
    outUV = odrODRUV.run()
    # Fit parameters
    popt_odrB = outUV.beta
    perr_odrB = outUV.sd_beta
    chi_odrB  = outUV.res_var # chi squared value
    #--------------------#

    print("SC fits")
    print("A 470nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t Chi^2 reduced: {:.2f}".format(uti.rad2mas(popt_odrA[0]), uti.rad2mas(perr_odrA[0]), chi_odrA))
    print("B 375nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t Chi^2 reduced: {:.2f}".format(uti.rad2mas(popt_odrB[0]), uti.rad2mas(perr_odrB[0]), chi_odrB))
    
    # plot SC fit and error band
    # plot channel A 470nm green
    plt.figure("SC Amp")
    plt.subplot(121)
    plt.plot(xplot, uti.spatial_coherence(xplot,amp_g,popt_odrA, lam_g), linewidth=2, color='darkgrey', label='uniform disk')
    plt.fill_between(xplot, uti.spatial_coherence(xplot,amp_g,popt_odrA-perr_odrA, lam_g), uti.spatial_coherence(xplot,amp_g,popt_odrA+perr_odrA, lam_g), alpha=0.3, color='darkgrey')
    # legend 
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles)) 
    plt.legend(by_label.values(), by_label.keys())
    # text
    ymin, ymax = plt.gca().get_ylim()
    plt.text(85, ymax-3.5, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrA[0]), uti.rad2mas(perr_odrA[0])), color='grey')
    plt.text(85, ymax-4, s='$\chi^2$/dof={:.2f}'.format(chi_odrA), color='grey')
    plt.xlim(0,200)
    plt.xlabel("Projected baseline (m)")
    plt.ylabel("Spatial coherence (fs)")
    plt.axhline(y=0, color="black", linestyle="--")  
    plt.tight_layout()

    # plot channel B 375nm uv
    plt.subplot(122)
    plt.plot(xplot, uti.spatial_coherence(xplot,amp_uv,popt_odrB, lam_uv), linewidth=2, color='darkgrey', label='uniform disk')
    plt.fill_between(xplot, uti.spatial_coherence(xplot,amp_uv,popt_odrB-perr_odrB, lam_uv), uti.spatial_coherence(xplot,amp_uv,popt_odrB+perr_odrB, lam_uv), alpha=0.2, color='darkgrey')
    plt.xlabel("Projected baseline (m)")
    plt.ylabel("Spatial coherence (fs)")
    plt.axhline(y=0, color='black', linestyle="--")
    # legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles)) 
    plt.legend(by_label.values(), by_label.keys())
    # text
    ymin, ymax = plt.gca().get_ylim()
    plt.text(80, ymax-3.5, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrB[0]), uti.rad2mas(perr_odrB[0])), color='grey')
    plt.text(80, ymax-4, s='$\chi^2$/dof={:.2f}'.format(chi_odrB), color='grey')
    plt.xlim(0,200)
    plt.tight_layout()


'''
    # Make additional scaled parameters
    ints_fixedA_scaled = []; dints_fixedA_scaled = []; ints_fixedB_scaled = []; dints_fixedB_scaled = []
    #ints_fixed_all_scaled = []; dints_fixed_all_scaled = []
    #baselines_all2 = []
    for k in range (0,len(ints_fixedA)):
        ints_fixedA_scaled.append(ints_fixedA[k]  / popt_odrA[0])
        dints_fixedA_scaled.append(dints_fixedA[k] / popt_odrA[0])
        
        ints_fixedB_scaled.append(ints_fixedB[k]  / popt_odrB[0])
        dints_fixedB_scaled.append(dints_fixedB[k] / popt_odrB[0])

        #ints_fixed_all_scaled.append(ints_fixedA[k]/ popt_odrA[0])
        #dints_fixed_all_scaled.append(dints_fixedA[k]/ popt_odrA[0])
        #ints_fixed_all_scaled.append(ints_fixedB[k]/ popt_odrB[0])
        #dints_fixed_all_scaled.append(ints_fixedB[k]/ popt_odrB[0])
        #baselines_all2.append(baselines_all[k])
    #np.savetxt("spatial_coherence/{}/{}_{}_scaled.sc".format(star,star, telcombis[i]), np.c_[ints_fixedA_scaled, dints_fixedA_scaled, ints_fixedB_scaled, dints_fixedB_scaled], header="{} {} {} {}\nscA\tdscA\tscB\tdscB".format(popt_odrA[0], popt_odrB[0], popt_odrA[1],popt_odrB[1]))
    # add scaled data of all tel combis to one list
    #ints_fixed_all_scaled.append(ints_fixedA_scaled); ints_fixed_all_scaled.append(ints_fixedB_scaled); dints_fixed_all_scaled.append(dints_fixedA_scaled); dints_fixed_all_scaled.append(dints_fixedB_scaled)
    
    print(len(baselines_all), len(ints_fixedA_scaled))
    
    # Figure showing both colors in one plot scaled
    plt.figure('combi', figsize=(10,7))
    plt.title("Spatial coherence of {}". format(star))
    plt.xlabel("Baseline/Wavelength"); plt.ylabel("Normalized coherence time") 
    plt.axhline(y=0, color='black', linestyle="--")
    plt.xlim(0,5e8)

    for k in range(0, len(baselines_all)):
        # all SC curves in one plot
        plt.errorbar(baselines_all[k]/lam_g, ints_fixedA_scaled[k], yerr=dints_fixedA_scaled[k], xerr=dbaselines_all[k]/lam_g, marker="o", color='green')
        plt.errorbar(baselines_all[k]/lam_uv, ints_fixedB_scaled[k], yerr=dints_fixedB_scaled[k], xerr=dbaselines_all[k]/lam_uv, marker="o", color='blue')
    plt.plot(xplot_g, uti.spatial_coherence(xplot, 1, popt_odrA[1], lam_g), linewidth=2, color='green', label='470nm')
    plt.fill_between(xplot_g, uti.spatial_coherence(xplot, 1, popt_odrA[1]+perr_odrA[1], lam_g), uti.spatial_coherence(xplot, 1, popt_odrA[1]-perr_odrA[1], lam_g), alpha=0.3, color='green')
    plt.plot(xplot_uv, uti.spatial_coherence(xplot, 1, popt_odrB[1], lam_uv), linewidth=2, color='blue', label='375nm')
    plt.fill_between(xplot_uv, uti.spatial_coherence(xplot, 1, popt_odrB[1]+perr_odrB[1], lam_uv), uti.spatial_coherence(xplot, 1, popt_odrB[1]-perr_odrB[1], lam_uv), alpha=0.3, color='blue')
    plt.legend()

'''

#    #--------------------#
#    # Try fitting with ods
#    # Model object
#    sc_model = odr.Model(uti.spatial_coherence_odr)
#    # RealData object
#    rdata = odr.RealData( baselines_all, ints_fixed_all_scaled, sx=dbaselines_all, sy=dints_fixed_all_scaled )
#    # Set up ODR with model and data
#    odrODR = odr.ODR(rdata, sc_model, beta0=[22,2.7e-9])
#    # Run the regression
#    out = odrODR.run()
#    # Fit parameters
#    popt_odr_all = out.beta
#    perr_odr_all = out.sd_beta
#    chi_odr_all  = out.res_var # chi squared value
#    
#    # scaled ods model
#    sc_model_sc = odr.Model(uti.spatial_coherence_odr_scaled)
#    # RealData object
#    rdata = odr.RealData( baselines_all, ints_fixed_all_scaled, sx=dbaselines_all, sy=dints_fixed_all_scaled )
#    # Set up ODR with model and data
#    odrODR_sc = odr.ODR(rdata, sc_model_sc, beta0=[2.7e-9])
#    # Run the regression
#    out_sc = odrODR_sc.run()
#    # Fit parameters
#    popt_odr_all_sc = out_sc.beta
#    perr_odr_all_sc = out_sc.sd_beta
#    chi_odr_all_sc  = out_sc.res_var # chi squared value

#    print("SC fit all")
#    print("Angular diameter AVG (odr): {:.3f} +/- {:.3f} (mas)".format(uti.rad2mas(popt_odr_all_sc[0]), uti.rad2mas(perr_odr_all_sc[0])))
#    #print("Amplitude: {:.3f} +/- {:.3f}".format(popt_odr_all[0], perr_odr_all[0]))



# Loop over every potential telescope combination and check if it exists
telcombis = []
for c1 in range (1,5):
    for c2 in range(1,5):
        if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
            telcombis.append("{}{}".format(c1,c2))

for c1 in range (1,5):
    for c2 in range(1,5):
        if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
            telcombi = [c1,c2]
            telcombistring = str(c1) + str(c2)
            print ("Found telescope combination {}".format(telcombi))
            if telcombistring in onlys or onlys == "None":
                cleaning(star, telcombi)
                chunk_ana(star, telcombi)
plotting(star)


plt.show()            