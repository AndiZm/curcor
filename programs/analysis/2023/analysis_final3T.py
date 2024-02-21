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
import os
from scipy import odr
from collections import OrderedDict
from matplotlib.offsetbox import AnchoredText

import utilities as uti
import corrections as cor
import geometry as geo

star = sys.argv[1]


#bl_HBT = []
## Open text file with star data from HBT
#f = open("stars_HBT.txt")
## Find line for the star
#line = f.readline()
#while star not in line:
#    line = f.readline()
#lam_HBT = line.split()[1]
#ang_HBT = uti.mas2rad(float(line.split()[2]))
#line = f.readline()
#while "[end]" not in line:
#    bl_HBT.append(float(line.split()[0]))
#    line = f.readline()
#f.close()


combicolors = np.zeros((5,5), dtype=object); combicolors[:] = np.nan
combicolors[1,3] = "blue"
combicolors[1,4] = "fuchsia"
combicolors[3,4] = "green"

# Create array of fixed parameters
mu_A = np.zeros((5,5)); mu_A[:] = np.nan
mu_B = np.zeros((5,5)); mu_B[:] = np.nan
sigma_A = np.zeros((5,5)); sigma_A[:] = np.nan
sigma_B = np.zeros((5,5)); sigma_B[:] = np.nan
amp_A = np.zeros((5,5)); amp_A[:] = np.nan
amp_B = np.zeros((5,5)); amp_B[:] = np.nan

lam_g = 470e-9
lam_uv = 375e-9
lam_all = 422.5e-9

################################################
#### Analysis over whole measurement time #####
################################################
plt.figure("CrossCorr", figsize=(12,8))
def par_fixing(star, telcombi):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)
    plotnumber = len(telcombis)*100 + 10 + telcombis.index(telstring) + 1

    # Read in the data g2 functions
    chAs    = np.loadtxt("g2_functions/{}/{}/chA.g2".format(star, telstring))     
    chBs    = np.loadtxt("g2_functions/{}/{}/chB.g2".format(star, telstring))      

    # Demo function for initializing x axis and some stuff
    demo = chAs[0]
    x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)
    
    # Combine all data for channel A and B each for initial parameter estimation and fixing
    g2_allA = np.zeros(len(x)); g2_allB = np.zeros(len(x))
    for i in range (0,len(chAs)):
        #plt.plot(chAs[i]); plt.plot(chBs[i]); plt.show()
        g2_allA += chAs[i]/len(chAs)
        g2_allB += chBs[i]/len(chBs)

    # Fit for gaining mu and sigma to fix these parameters for different baseline combis
    plt.figure("CrossCorr")
    plt.subplot(plotnumber)
    plt.title("Cross correlation data of {} for {}".format(star, telstring))
    print("Fixed parameters")
    # Channel A
    xplot, popt, perr = uti.fit(g2_allA, x, -50, +50)
    mu_A[c1][c2] = popt[1]; sigma_A[c1][c2] = popt[2] # fixing mu and sigma
    amp_A[c1][c2] = popt[0]*1e7
    noise_A = np.std(g2_allA)*1e7
    integral, dintegral = uti.integral(popt, perr)
    print("{} A 470nm amp: {:.2f}e-7 +/- {:.2f}e-7 \t mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs".format(telstring, amp_A[c1][c2], perr[0]*1e7, mu_A[c1][c2], perr[1],sigma_A[c1][c2],perr[2],1e6*integral,1e6*dintegral))
    print("A Noise: {:.2f}".format(noise_A))
    print("Ratio: {:.2f}".format(amp_A[c1][c2]/noise_A))
    plt.plot(x, g2_allA, label=telstring + "A", color="green")
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    # Channel B
    xplot, popt, perr = uti.fit(g2_allB, x, -50, +50)
    mu_B[c1][c2] = popt[1]; sigma_B[c1][c2] = popt[2]
    amp_B[c1][c2] = popt[0]*1e7
    noise_B = np.std(g2_allB)*1e7
    integral, dintegral = uti.integral(popt, perr)
    print ("{} B 375nm amp: {:.2f}e-7 +/- {:.2f}e-7 \t mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs".format(telstring,amp_B[c1][c2], perr[0]*1e7, mu_B[c1][c2],perr[1],sigma_B[c1][c2],perr[2],1e6*integral,1e6*dintegral))
    print("B Noise: {:.2f}".format(noise_B))
    print("Ratio: {:.2f}".format(amp_B[c1][c2]/noise_B))
    plt.plot(x, g2_allB, label=telstring + "B", color="blue")
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    
    plt.legend(); plt.xlim(-100,100); plt.grid()
    plt.ticklabel_format(useOffset=False)
    plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")
    plt.tight_layout()
#    np.savetxt("g2_functions/fixed_parameters/{}/{}/mu_sig_{}.txt".format(star,telcombi, telcombi), np.c_[mu_A, sigma_A, mu_B, sigma_B], header="muA, sigA, muB, sigB")

##########################################
####### Chunk analysis ###################
##########################################
#plt.figure("baselines")
#plt.title("{}".format(star))
#plt.xlabel("Acquisition time")
#plt.ylabel("Telescope baseline (m)")

plt.figure('SC', figsize=(12,8))
plt.suptitle("Spatial coherence of {}".format(star))

intsA = []; dintsA = []; times = []
intsB = []; dintsB = []
ints_fixedA = []; dints_fixedA = []
ints_fixedB = []; dints_fixedB = []
baselines_all = []; dbaselines_all = []
time_all = [] ; telstrings =[]

def chunk_ana(star, telcombi):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)  
    
    # initialize cleaned arrays
    chA_clean = []; chB_clean = []; ampA = []; ampB = []; muA = []; muB =[] ; chiA =[]; chiB = []; dmuA = []; dmuB =[]
    ffts = []
    chAs    = np.loadtxt("g2_functions/{}/{}/chA.g2".format(star, telstring))
    chBs    = np.loadtxt("g2_functions/{}/{}/chB.g2".format(star, telstring))

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
    
        #plt.figure('baselines')
        #plt.errorbar(x=tstring_short, y=baseline, yerr=dbaseline, marker="o", linestyle="", label=telstring, color=combicolors[c1][c2])
        #plt.xticks(rotation=45)
    
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
        freqB = [50]
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

        # Fit with fixed mu and sigma
        xplotf, popt_A, perr_A = uti.fit_fixed(chA, x, -50, 50, mu_A[c1][c2], sigma_A[c1][c2])
        Int, dInt = uti.integral_fixed(popt_A, perr_A, sigma_A[c1][c2], factor=2.3)
        #dInt = np.sqrt( dInt**2 + (np.std(chA)*sigma_A[c1][c2]*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
        ints_fixedA.append(1e6*Int); dints_fixedA.append(1e6*dInt)# in femtoseconds

        plt.figure('SC')
        plt.subplot(121)
        plt.title("470nm")
        plt.errorbar(x=baseline, xerr=dbaseline, y=1e6*Int, yerr=1e6*dInt, marker='o', color=combicolors[c1][c2], label=telstring)
        
        xplotf, popt_B, perr_B = uti.fit_fixed(chB, x, -50, 50, mu_B[c1][c2], sigma_B[c1][c2])
        Int, dInt = uti.integral_fixed(popt_B, perr_B, sigma_B[c1][c2], factor=2.38)
        #dInt = np.sqrt( dInt**2 + (np.std(chB)*sigma_B[c1][c2]*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
        ints_fixedB.append(1e6*Int); dints_fixedB.append(1e6*dInt)# in femtoseconds

        plt.figure("SC")
        plt.subplot(122)
        plt.title("375nm")
        plt.errorbar(x=baseline, xerr=dbaseline, y=1e6*Int, yerr=1e6*dInt, marker='o', color=combicolors[c1][c2], label=telstring)

        print("{}".format(i), timestring, Int, dInt) 


#        # save cleaned data and fit parameter
#        chA_clean.append(chA)
#        chB_clean.append(chB)
#        ampA.append(popt_A[0]); ampB.append(popt_B[0])
#      
#    # store cleaned data
#    np.savetxt("g2_functions/fixed_parameters/{}/{}/ChA_clean.txt".format(star,telcombi), np.c_[chA_clean], header="{} Channel A cleaned".format(star) )
#    np.savetxt("g2_functions/fixed_parameters/{}/{}/ChB_clean.txt".format(star,telcombi), np.c_[chB_clean], header="{} Channel B cleaned".format(star) )
#    np.savetxt("g2_functions/fixed_parameters/{}/{}/xplot.txt".format(star,telcombi), np.c_[xplotf])
#    np.savetxt("g2_functions/fixed_parameters/{}/{}/amps.txt".format(star,telcombi), np.c_[ampA, ampB], header='ampA, ampB')
#    np.savetxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombi), np.c_[timestrings,baselines, dbaselines, ints_fixedA, dints_fixedA, ints_fixedB, dints_fixedB])

    print("DONE Chunks {}".format(telcombi))
    #plt.figure("baselines")
    #handles, labels = plt.gca().get_legend_handles_labels()
    #by_label = OrderedDict(zip(labels, handles)) 
    #plt.legend(by_label.values(), by_label.keys()); plt.tight_layout()


def plotting(star):
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


    #--------------------#
    # Try fitting with ods
    # Uniform disk model object    
    sc_modelG = odr.Model(uti.spatial_coherence_odrG)
    # RealData object
    rdataG = odr.RealData( baselines_all, ints_fixedA, sx=dbaselines_all, sy=dints_fixedA )
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
    rdataUV = odr.RealData( baselines_all, ints_fixedB, sx=dbaselines_all, sy=dints_fixedB )
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

#
#        # save fitted amplitude
#        amplitudes_odr.append(popt_odrA[0]); amplitudes_odr.append(perr_odrA[0])
#        amplitudes_odr.append(popt_odrB[0]); amplitudes_odr.append(perr_odrB[0])
#        ang_odr.append(popt_odrA[1]); ang_odr.append(perr_odrA[1])
#        ang_odr.append(popt_odrB[1]); ang_odr.append(perr_odrB[1])
#

    
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
    # plot limb darkening fit
    #plt.plot(xplot, uti.spatial_coherence_LD(xplot,*popt_odrA, lam_g, u=0.2), linewidth=2, color='orange', label='limb darkening')
    plt.xlabel("Baseline (m)")
    plt.ylabel("Spatial coherence (fs)")
    #plt.xlim(0,200)
    plt.axhline(y=0, color="black", linestyle="--")  
    
    # text
    ymin, ymax = plt.gca().get_ylim()
    plt.text(80, ymax-3.5, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrA[1]), uti.rad2mas(perr_odrA[1])), color='grey')
    plt.text(80, ymax-4, s='$\chi^2$/dof={:.2f}'.format(chi_odrA), color='grey')
    #plt.text(80, ymax-4.5, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrG_LD[1]), uti.rad2mas(perr_odrG_LD[1])), color='orange')
    #plt.text(80, ymax-5, s='$\chi^2$/dof={:.2f}'.format(chi_odrG_LD), color='orange')
    plt.tight_layout()

    ### Mimosa ###
    if star == 'Mimosa':
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
        
        print("SC fit limb darkening")
        print("A 470nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t Amplitude: {:.2f} +/- {:.2f}\t Chi^2 reduced: {:.2f}".format(uti.rad2mas(popt_odrG_LD[1]), uti.rad2mas(perr_odrG_LD[1]), popt_odrG_LD[0], perr_odrG_LD[0], chi_odrG_LD))

        # plot SC fit and error band Limb darkening
        plt.figure("SC")
        plt.subplot(121)
        plt.plot(xplot, uti.spatial_coherence_LD(xplot,*popt_odrG_LD, lam_g, u=0.37), linewidth=2, color='orange', label='limb darkening')
        plt.fill_between(xplot, uti.spatial_coherence_LD(xplot,popt_odrG_LD[0]+perr_odrG_LD[0],popt_odrG_LD[1]-perr_odrG_LD[1], lam_g, u=0.37), uti.spatial_coherence_LD(xplot,popt_odrG_LD[0]-perr_odrG_LD[0],popt_odrG_LD[1]+perr_odrG_LD[1], lam_g, u=0.37), alpha=0.3, color='orange')
        plt.text(80, ymax-4.5, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrG_LD[1]), uti.rad2mas(perr_odrG_LD[1])), color='orange')
        plt.text(80, ymax-5, s='$\chi^2$/dof={:.2f}'.format(chi_odrG_LD), color='orange')
        plt.tight_layout()
    # legend 
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles)) 
    plt.legend(by_label.values(), by_label.keys())

    # plot channel B 375nm uv
    plt.subplot(122)
    plt.plot(xplot, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), linewidth=2, color='darkgrey')
    plt.fill_between(xplot, uti.spatial_coherence(xplot,popt_odrB[0]+perr_odrB[0],popt_odrB[1]-perr_odrB[1], lam_uv), uti.spatial_coherence(xplot,popt_odrB[0]-perr_odrB[0],popt_odrB[1]+perr_odrB[1], lam_uv), alpha=0.2, color='darkgrey')
    plt.xlabel("Baseline (m)")
    plt.ylabel("Spatial coherence (fs)")
    #plt.xlim(0,200)
    plt.axhline(y=0, color='black', linestyle="--")
    # legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles)) 
    plt.legend(by_label.values(), by_label.keys())
    # text
    ymin, ymax = plt.gca().get_ylim()
    plt.text(80, ymax-3.5, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrB[1]), uti.rad2mas(perr_odrB[1])), color='grey')
    plt.text(80, ymax-4, s='$\chi^2$/dof={:.2f}'.format(chi_odrB), color='grey')
    plt.tight_layout()


    


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

#plt.figure("CrossCorr", figsize=(12,8))
for c1 in range (1,5):
    for c2 in range(1,5):
        if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
            telcombi = [c1,c2]
            print ("Found telescope combination {}".format(telcombi))
            par_fixing(star, telcombi)
            chunk_ana(star, telcombi)
plotting(star)


plt.show()            