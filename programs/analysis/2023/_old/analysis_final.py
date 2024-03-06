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
colorB14 = uti.color_chB
colorA34 = 'limegreen'
colorB34 = 'deepskyblue'

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



################################################
#### Analysis over whole measurement time #####
################################################
def par_fixing(star, telcombi):
    # Read in the data g2 functions
    chAs    = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/ChA.txt".format(star, telcombi))     
    chBs    = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/ChB.txt".format(star, telcombi))      
    labelA = str(telcombi) + 'A'
    labelB = str(telcombi) + 'B'

    # Demo function for initializing x axis and some stuff
    demo = chAs[0]
    x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)
    labelA = '{}A 470nm'.format(telcombi)
    labelB = '{}B 375nm'.format(telcombi)
    
    # Combine all data for channel A and B each for initial parameter estimation and fixing
    g2_allA = np.zeros(len(x)); g2_allB = np.zeros(len(x))
    for i in range (0,len(chAs)):
        #plt.plot(chAs[i]); plt.plot(chBs[i]); plt.show()
        g2_allA += chAs[i]/len(chAs)
        g2_allB += chBs[i]/len(chBs)

    # Fit for gaining mu and sigma to fix these parameters for different baseline combis
    if telcombi == 14:
        plt.subplot(211)
        plt.title("Cross correlation data of {} for {}".format(star, telcombi))
        print("Fixed parameters")
        xplot, popt, perr = uti.fit(g2_allA, x, -50, +50)
        mu_A = popt[1]; sigma_A = popt[2]
        integral, dintegral = uti.integral(popt, perr)
        print("{}A 470nm mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs".format(telcombi,mu_A, perr[1],sigma_A,perr[2],1e6*integral,1e6*dintegral))
        plt.plot(x, g2_allA, label=labelA, color=colorA14)
        plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

        xplot, popt, perr = uti.fit(g2_allB, x, -50, +50)
        mu_B = popt[1]; sigma_B = popt[2]
        integral, dintegral = uti.integral(popt, perr)
        print ("{}B 375nm mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs".format(telcombi,mu_B,perr[1],sigma_B,perr[2],1e6*integral,1e6*dintegral))
        plt.plot(x, g2_allB, label=labelB, color=colorB14)
        plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

    elif telcombi == 34:
        plt.subplot(212)
        plt.title("Cross correlation data of {} for {}".format(star, telcombi))
        print("Fixed parameters")
        xplot, popt, perr = uti.fit(g2_allA, x, -50, +50)
        mu_A = popt[1]; sigma_A = popt[2]
        integral, dintegral = uti.integral(popt, perr)
        print("{}A 470nm mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs".format(telcombi,mu_A, perr[1],sigma_A,perr[2],1e6*integral,1e6*dintegral))
        plt.plot(x, g2_allA, label=labelA, color=colorA34)
        plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

        xplot, popt, perr = uti.fit(g2_allB, x, -50, +50)
        mu_B = popt[1]; sigma_B = popt[2]
        integral, dintegral = uti.integral(popt, perr)
        print ("{}B 375nm mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs".format(telcombi,mu_B,perr[1],sigma_B,perr[2],1e6*integral,1e6*dintegral))
        plt.plot(x, g2_allB, label=labelB, color=colorB34)
        plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    
    plt.legend(); plt.xlim(-100,100); plt.grid()
    #plt.ticklabel_format(useOffset=False)
    plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")
    plt.tight_layout()
    plt.plot()
    np.savetxt("g2_functions/fixed_parameters/{}/{}/mu_sig_{}.txt".format(star,telcombi, telcombi), np.c_[mu_A, sigma_A, mu_B, sigma_B], header="muA, sigA, muB, sigB")

#########################################
###### Chunk analysis ###################
#########################################
def chunk_ana(star, telcombi):
    intsA = []; dintsA = []; times = []
    intsB = []; dintsB = []
    ints_fixedA = []; dints_fixedA = []
    ints_fixedB = []; dints_fixedB = []
    
    
    # initialize cleaned arrays and read in mu and sigma
    chA_clean = []; chB_clean = []; ampA = []; ampB = []; muA = []; muB =[] ; chiA =[]; chiB = []; dmuA = []; dmuB =[]
    ffts = []
    chAs    = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/ChA.txt".format(star, telcombi))
    chBs    = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/ChB.txt".format(star, telcombi)) 
    data      = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/baseline.txt".format(star, telcombi))
    timestrings = data [:,0] ; baselines = data[:,1]; dbaselines = data[:,2]    
    mu_A, sig_A, mu_B, sig_B = np.loadtxt("g2_functions/fixed_parameters/{}/{}/mu_sig_{}.txt".format(star,telcombi,telcombi))
    
    # Demo function for initializing x axis and some stuff
    demo = chAs[0]
    x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)
    error = np.std(chAs[0][0:4000])
    
    # loop over every g2 function chunks
    for i in range(0,len(chAs)):
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
        xplotf, popt_A, perr_A = uti.fit_fixed(chA, x, -50, 50, mu_A, sig_A)
        Int, dInt = uti.integral_fixed(popt_A, perr_A, sig_A, factor=2.3)
        #dInt = np.sqrt( dInt**2 + (np.std(chA)*sig_A*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
        #dInt = 2.2*dInt # this is the empirical formula from the simulations which has changed form 2022 to 2023
        ints_fixedA.append(1e6*Int); dints_fixedA.append(1e6*dInt)# in femtoseconds
        
        xplotf, popt_B, perr_B = uti.fit_fixed(chB, x, -50, 50, mu_B, sig_B)
        Int, dInt = uti.integral_fixed(popt_B, perr_B, sig_B, factor=2.38)
        #dInt = np.sqrt( dInt**2 + (np.std(chB)*sig_B*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
        #dInt = 2.2*dInt # this is the empirical formula from the simulations which has changed from 2022 to 2023
        ints_fixedB.append(1e6*Int); dints_fixedB.append(1e6*dInt)# in femtoseconds

    
        # Check acquisition time of original data
        timestring = ephem.Date(data[:,0][i])
        print("{}".format(i), timestring, Int, dInt)
        
        # save cleaned data and fit parameter
        chA_clean.append(chA)
        chB_clean.append(chB)
        ampA.append(popt_A[0]); ampB.append(popt_B[0])
        

    # store cleaned data
    np.savetxt("g2_functions/fixed_parameters/{}/{}/ChA_clean.txt".format(star,telcombi), np.c_[chA_clean], header="{} Channel A cleaned".format(star) )
    np.savetxt("g2_functions/fixed_parameters/{}/{}/ChB_clean.txt".format(star,telcombi), np.c_[chB_clean], header="{} Channel B cleaned".format(star) )
    np.savetxt("g2_functions/fixed_parameters/{}/{}/xplot.txt".format(star,telcombi), np.c_[xplotf])
    np.savetxt("g2_functions/fixed_parameters/{}/{}/amps.txt".format(star,telcombi), np.c_[ampA, ampB], header='ampA, ampB')
    np.savetxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombi), np.c_[timestrings,baselines, dbaselines, ints_fixedA, dints_fixedA, ints_fixedB, dints_fixedB])

    print("DONE Chunks {}".format(telcombi))

def plotting(star):
    telcombis = [14,34]
    ticks = []; amplitudes_odr = []; ang_odr = []
    ints_fixed_all = []; dints_fixed_all = []; baselines_all = []; dbaselines_all = []; ints_fixed_all_scaled = []; dints_fixed_all_scaled = []

    # Define figure which will show individual g2 cross correlations
    crossfigure = plt.figure(figsize=(12,8))
    # cross correlations for telcombis
    ax_cross1 = crossfigure.add_subplot(211); ax_cross1.set_title("Cross correlations of {} for {}".format(star, telcombis[0]))
    ax_cross1.set_xlabel("Time difference (ns)"); ax_cross1.set_ylabel("$g^{(2)}$"); ax_cross1.ticklabel_format(useOffset=False)
    ax_cross1.set_xlim(-100,100)
    ax_cross2 = crossfigure.add_subplot(212); ax_cross2.set_title("Cross correlations of {} for {}".format(star, telcombis[1]))
    ax_cross2.set_xlabel("Time difference (ns)"); ax_cross2.set_ylabel("$g^{(2)}$"); ax_cross2.ticklabel_format(useOffset=False)
    ax_cross2.set_xlim(-100,100)
    plt.tight_layout()

    # Define figure which will show the spatial coherence curve (baseline vs. g2 integral)
    scfigure = plt.figure(figsize=(12,8))
    sps1, sps2, sps3, sps4 = GridSpec(2,2)
    ax_sc1 = scfigure.add_subplot(221)
    ax_sc1.set_title("Spatial coherence of {} for 470nm".format(star))
    ax_sc1.set_xlabel("Baseline/Wavelength"); ax_sc1.set_ylabel("Coherence time (fs)")
    ax_sc1.set_xlim(-1e7,6e8)
    ax_sc3 = scfigure.add_subplot(223)
    ax_sc3.set_title("Spatial coherence of {} for 375nm".format(star))
    ax_sc3.set_xlabel("Baseline/Wavelength"); ax_sc3.set_ylabel("Coherence time (fs)")
    ax_sc3.set_xlim(-1e7,6e8)
    ax_sc2 = scfigure.add_subplot(222)
    ax_sc2.set_title("Spatial coherence of {} for 470nm scaled".format(star))
    ax_sc2.set_xlabel("Baseline"); ax_sc2.set_ylabel("Coherence time")
    ax_sc4 = scfigure.add_subplot(224)
    ax_sc4.set_title("Spatial coherence of {} for 375nm scaled".format(star))
    ax_sc4.set_xlabel("Baseline"); ax_sc4.set_ylabel("Coherence time")
    plt.tight_layout()

    # Define figure showing all tel combos with one fit
    combifigure = plt.figure(figsize=(10,7))
    ax_combi = plt.subplot(111)
    ax_combi.set_title("Spatial coherence of {}". format(star))
    ax_combi.set_xlabel("Baseline/Wavelength"); ax_combi.set_ylabel("Normalized coherence time") 
    #ax_combi.set_xlim(-1e7,5e8)

    # Define figure showing all tel combos with one fit
    limbfigure = plt.figure(figsize=(10,7))
    ax_limb = plt.subplot(111)
    ax_limb.set_title("Limb darkening spatial coherence of {}". format(star))
    ax_limb.set_xlabel("Baseline/Wavelength"); ax_limb.set_ylabel("Normalized coherence time") 
    
    # for loop over telescope combinations
    for i in range(len(telcombis)):
        # read in all necessary data and parameters
        chAs_clean = np.loadtxt("g2_functions/fixed_parameters/{}/{}/ChA_clean.txt".format(star,telcombis[i]))
        chBs_clean = np.loadtxt("g2_functions/fixed_parameters/{}/{}/ChB_clean.txt".format(star,telcombis[i]))
        mu_A, sigA, mu_B, sigB = np.loadtxt("g2_functions/fixed_parameters/{}/{}/mu_sig_{}.txt".format(star,telcombis[i],telcombis[i]))
        ampA = np.loadtxt("g2_functions/fixed_parameters/{}/{}/amps.txt".format(star,telcombis[i]))[:,0]
        ampB = np.loadtxt("g2_functions/fixed_parameters/{}/{}/amps.txt".format(star,telcombis[i]))[:,1]
        xplotf = np.loadtxt("g2_functions/fixed_parameters/{}/{}/xplot.txt".format(star,telcombis[i]))
        timestrings  = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,0]
        baselines    = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,1]
        dbaselines   = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,2]
        ints_fixedA  = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,3]
        dints_fixedA = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,4]
        ints_fixedB  = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,5]
        dints_fixedB = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,6]

        # add data of all tel combis to one list
        ints_fixed_all.append(ints_fixedA); ints_fixed_all.append(ints_fixedB); dints_fixed_all.append(dints_fixedA); dints_fixed_all.append(dints_fixedB)
        baselines_all.append(baselines); baselines_all.append(baselines); dbaselines_all.append(dbaselines); dbaselines_all.append(dbaselines)


        #--------------------#
        # Try fitting with ods
        # Model object
        from scipy import odr
        
        sc_modelG = odr.Model(uti.spatial_coherence_odrG)
        # RealData object
        rdataG = odr.RealData( baselines, ints_fixedA, sx=dbaselines, sy=dints_fixedA )
        # Set up ODR with model and data
        odrODRG = odr.ODR(rdataG, sc_modelG, beta0=[25,2.2e-9])
        # Run the regression
        outG = odrODRG.run()
        # Fit parameters
        popt_odrA = outG.beta
        perr_odrA = outG.sd_beta
        chi_odrA = outG.res_var # chi squared value
        
        
        sc_modelUV = odr.Model(uti.spatial_coherence_odrUV)
        # RealData object
        rdataUV = odr.RealData( baselines, ints_fixedB, sx=dbaselines, sy=dints_fixedB )
        # Set up ODR with model and data
        odrODRUV = odr.ODR(rdataUV, sc_modelUV, beta0=[20,3.2e-9])
        # Run the regression
        outUV = odrODRUV.run()
        # Fit parameters
        popt_odrB = outUV.beta
        perr_odrB = outUV.sd_beta
        chi_odrB  = outUV.res_var # chi squared value
        #--------------------#

        print("SC fits")
        print("{}A 470nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t Amplitude: {:.2f} +/- {:.2f}\t Chi^2 reduced: {:.2f}".format(telcombis[i], uti.rad2mas(popt_odrA[1]), uti.rad2mas(perr_odrA[1]), popt_odrA[0], perr_odrA[0], chi_odrA))
        print("{}B 375nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t Amplitude: {:.2f} +/- {:.2f}\t Chi^2 reduced: {:.2f}".format(telcombis[i], uti.rad2mas(popt_odrB[1]), uti.rad2mas(perr_odrB[1]), popt_odrB[0], perr_odrB[0], chi_odrB))

        # save fitted amplitude
        amplitudes_odr.append(popt_odrA[0]); amplitudes_odr.append(perr_odrA[0])
        amplitudes_odr.append(popt_odrB[0]); amplitudes_odr.append(perr_odrB[0])
        ang_odr.append(popt_odrA[1]); ang_odr.append(perr_odrA[1])
        ang_odr.append(popt_odrB[1]); ang_odr.append(perr_odrB[1])

        # Make additional scaled parameters
        ints_fixedA_scaled = []; dints_fixedA_scaled = []; ints_fixedB_scaled = []; dints_fixedB_scaled = []
        for k in range (0,len(ints_fixedA)):
            ints_fixedA_scaled.append(ints_fixedA[k]  / popt_odrA[0])
            dints_fixedA_scaled.append(dints_fixedA[k] / popt_odrA[0])
            
            ints_fixedB_scaled.append(ints_fixedB[k]  / popt_odrB[0])
            dints_fixedB_scaled.append(dints_fixedB[k] / popt_odrB[0])
        np.savetxt("spatial_coherence/{}/{}_{}_scaled.sc".format(star,star, telcombis[i]), np.c_[ints_fixedA_scaled, dints_fixedA_scaled, ints_fixedB_scaled, dints_fixedB_scaled], header="{} {} {} {}\nscA\tdscA\tscB\tdscB".format(popt_odrA[0], popt_odrB[0], popt_odrA[1],popt_odrB[1]))
        # add scaled data of all tel combis to one list
        ints_fixed_all_scaled.append(ints_fixedA_scaled); ints_fixed_all_scaled.append(ints_fixedB_scaled); dints_fixed_all_scaled.append(dints_fixedA_scaled); dints_fixed_all_scaled.append(dints_fixedB_scaled)


        # Define colormap for plotting all summarized individual g2 functions
        cm_sub = np.linspace(1.0, 0.0, len(chAs_clean))
        colors = [cm.viridis(x) for x in cm_sub]
        # Demo function for initializing x axis and some stuff
        demo = chAs_clean[0]
        x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)
        
        lam_g = 470e-9
        lam_uv = 375e-9
        lam_all = 422.5e-9
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
        # add HBT measurement to the plot
        xplot_HBT = np.zeros(len(xplot))
        for j in range(0,len(xplot)):
            xplot_HBT[j] = (xplot[j] /float(lam_HBT))

        # Nullstelle for SC plot
        nsA = 1.22*(lam_g/popt_odrA[1])
        nsB = 1.22*(lam_uv/popt_odrB[1])

        # Make plotting range smaller 
        chAs = []; chBs = []; errorA =[]; errorB = []
        for j in range(0,len(chAs_clean)):
            chA = chAs_clean[j] ; chB = chBs_clean[j]; chAss = []; chBss = []
            # errorbars for g2 fct
            errorA.append(np.std(chAs_clean[j][0:4000]))
            errorB.append(np.std(chBs_clean[j][0:4000]))
            # only plot certain range of g2 fct -> cut data to that range
            for k in range(0, len(x)):
                if -100<= x[k] <=100:
                    chAss.append(chA[k])
                    chBss.append(chB[k])        
            chAs.append(np.array(chAss))
            chBs.append(np.array(chBss))  
        demo = chAs[0]
        xnew = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)     

        # Subplots for telcombi 14
        if telcombis[i] == 14:
            labelA = '{}A 470nm, $\chi^2$/dof={:.2f}'.format(telcombis[i], chi_odrA)
            labelB = '{}B 375nm, $\chi^2$/dof={:.2f}'.format(telcombis[i], chi_odrB) 
            
            # for loop over all chunks 
            for j in range(len(chAs)):
                # plot all g2 fcts together
                the_shift = (len(chAs)-j-1)*1e-6
                ticks.append(1.+the_shift)
                timestring = ephem.Date(timestrings[j])
                tstring_short = str(timestring)[5:-3]
                ax_cross1.set_yticks(np.arange(1,1+2e-6*len(chAs),2e-6))
                ax_cross1.errorbar(xnew, chAs[j] + the_shift, yerr=errorA[j], linestyle="-", color = colors[j],   alpha=0.7)
                ax_cross1.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampA[j], mu=mu_A, sigma=sigA, shift=j, inverse=True, ntotal=len(chAs)), color='black', linestyle="--", zorder=4)
                ax_cross1.errorbar(xnew, chBs[j] + the_shift, yerr=errorB[j], linestyle="-", color =colors[j],   alpha=0.7)                
                ax_cross1.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampB[j], mu=mu_B, sigma=sigB, shift=j, inverse=True, ntotal=len(chBs)), color='black', linestyle="--", zorder=4)
                ax_cross1.text(x=70, y=1+the_shift+0.4e-6, s=tstring_short, color=colors[j], fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
                
            ### Plot SC data ###
            for k in range (0,len(baselines)):
                ax_sc1.errorbar(baselines[k]/lam_g, ints_fixedA[k],  yerr=dints_fixedA[k], xerr=dbaselines[k]/lam_g, marker="o", linestyle="", color=colorA14)
                ax_sc3.errorbar(baselines[k]/lam_uv, ints_fixedB[k], yerr=dints_fixedB[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB14)
                ax_sc2.errorbar(baselines[k], ints_fixedA_scaled[k], yerr=dints_fixedA_scaled[k], xerr=dbaselines[k], marker="o", linestyle="", color=colorA14)
                ax_sc4.errorbar(baselines[k], ints_fixedB_scaled[k], yerr=dints_fixedB_scaled[k], xerr=dbaselines[k], marker="o", linestyle="", color=colorB14)
                # all SC curves in one plot
                #ax_combi.errorbar(baselines[k]/lam_g, ints_fixedA[k],  yerr=dints_fixedA[k], xerr=dbaselines[k]/lam_g,  marker="o", linestyle="", color=colorA14, label=labelA)
                #ax_combi.errorbar(baselines[k]/lam_uv, ints_fixedB[k], yerr=dints_fixedB[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB14, label=labelB)
                ax_combi.errorbar(baselines[k]/lam_g, ints_fixedA_scaled[k], yerr=dints_fixedA_scaled[k], xerr=dbaselines[k]/lam_g, marker="o", linestyle="", color=colorA14)
                ax_combi.errorbar(baselines[k]/lam_uv, ints_fixedB_scaled[k], yerr=dints_fixedB_scaled[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB14)
                ax_limb.errorbar(baselines[k]/lam_g, ints_fixedA_scaled[k], yerr=dints_fixedA_scaled[k], xerr=dbaselines[k]/lam_g, marker="o", linestyle="", color=colorA14)
                ax_limb.errorbar(baselines[k]/lam_uv, ints_fixedB_scaled[k], yerr=dints_fixedB_scaled[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB14)
            # plot SC fit and error band
            ax_sc1.plot(xplot_g, uti.spatial_coherence(xplot,*popt_odrA, lam_g), label=labelA, color=colorA14, linewidth=2)
            ax_sc1.fill_between(xplot_g, uti.spatial_coherence(xplot,popt_odrA[0]+perr_odrA[0],popt_odrA[1]-perr_odrA[1], lam_g), uti.spatial_coherence(xplot,popt_odrA[0]-perr_odrA[0],popt_odrA[1]+perr_odrA[1], lam_g), color=colorA14, alpha=0.3)
            ax_sc3.plot(xplot_uv, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), label=labelB, color=colorB14, linewidth=2)
            ax_sc3.fill_between(xplot_uv, uti.spatial_coherence(xplot,popt_odrB[0]+perr_odrB[0],popt_odrB[1]-perr_odrB[1], lam_uv), uti.spatial_coherence(xplot,popt_odrB[0]-perr_odrB[0],popt_odrB[1]+perr_odrB[1], lam_uv), color=colorB14, alpha=0.2)
            #ax_combi.plot(xplot_g, uti.spatial_coherence(xplot,*popt_odrA, lam_g), label=labelA, color=colorA14, linewidth=2)
            #ax_combi.plot(xplot_uv, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), label=labelB, color=colorB14, linewidth=2)
            # plot scaled version of SC fit
            ax_sc2.plot(xplot, uti.spatial_coherence(xplot,1, float(popt_odrA[1]), lam_g), label=labelA[0:9], color=colorA14, linewidth=2)
            ax_sc4.plot(xplot, uti.spatial_coherence(xplot,1, float(popt_odrB[1]), lam_uv),label=labelB[0:9], color=colorB14,  linewidth=2)
            ax_combi.plot(xplot_g, uti.spatial_coherence(xplot,1, popt_odrA[1], lam_g), label=labelA, color=colorA14, linewidth=2)
            ax_combi.plot(xplot_uv, uti.spatial_coherence(xplot,1, popt_odrB[1], lam_uv), label=labelB, color=colorB14, linewidth=2)
            ax_limb.plot(xplot_g, uti.spatial_coherence(xplot,1, popt_odrA[1], lam_g), label=labelA, color=colorA14, linewidth=2)
            ax_limb.plot(xplot_uv, uti.spatial_coherence(xplot,1, popt_odrB[1], lam_uv), label=labelB, color=colorB14, linewidth=2)
            # add zero baseline data point with error bar
            ax_sc1.errorbar(xplot_g[0],  uti.spatial_coherence(xplot[0],*popt_odrA, lam_g),  yerr=perr_odrA[0], marker='x', color=colorA14 )
            ax_sc3.errorbar(xplot_uv[0], uti.spatial_coherence(xplot[0],*popt_odrB, lam_uv), yerr=perr_odrB[0], marker='x', color=colorB14 )
            # add vertical lines for Nullstellen and text to plots
            ax_sc1.axvline(x=nsA/lam_g, color=colorA14, ymax=0.3); ax_sc3.axvline(x=nsB/lam_uv, color=colorB14, ymax=0.4)
            ax_sc1.text(x=xplot_g[1000], y=20, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrA[1]), uti.rad2mas(perr_odrA[1])), color=colorA14)
            ax_sc1.text(x=xplot_g[1000], y=18, s='Amplitude: {:.3f} +/- {:.3f}'.format(popt_odrA[0], perr_odrA[0]), color=colorA14)
            ax_sc3.text(x=xplot_uv[800], y=20, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrB[1]), uti.rad2mas(perr_odrB[1])), color=colorB14, bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
            ax_sc3.text(x=xplot_uv[800], y=18, s='Amplitude: {:.3f} +/- {:.3f}'.format(popt_odrB[0], perr_odrB[0]), color=colorB14, bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
            
        # Subplots for telcombi 34
        elif telcombis[i] == 34:
            labelA = '{}A 470nm, $\chi^2$/dof={:.2f}'.format(telcombis[i], chi_odrA)
            labelB = '{}B 375nm, $\chi^2$/dof={:.2f}'.format(telcombis[i], chi_odrB)
            
            # for loop over all chunks
            for j in range(len(chAs)):
                # plot all g2 fcts together
                the_shift = (len(chAs)-j-1)*1e-6
                ticks.append(1.+the_shift)
                timestring = ephem.Date(timestrings[j])
                tstring_short = str(timestring)[5:-3]
                ax_cross2.set_yticks(np.arange(1,1+2e-6*len(chAs),2e-6))
                ax_cross2.errorbar(xnew, chAs[j] + the_shift, yerr=errorA[j], linestyle="-", color = colors[j],   alpha=0.7)
                ax_cross2.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampA[j], mu=mu_A, sigma=sigA, shift=j, inverse=True, ntotal=len(chAs)), color='black', linestyle="--", zorder=4)
                ax_cross2.errorbar(xnew, chBs[j] + the_shift, yerr=errorB[j], linestyle="-", color = colors[j],   alpha=0.7)
                ax_cross2.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampB[j], mu=mu_B, sigma=sigB, shift=j, inverse=True, ntotal=len(chBs)), color='black', linestyle="--", zorder=4)
                ax_cross2.text(x=70, y=1+the_shift+0.4e-6, s=tstring_short, color=colors[j], fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
    
            ### Plot SC data ###
            for k in range (0,len(baselines)):
                ax_sc1.errorbar(baselines[k]/lam_g,  ints_fixedA[k], yerr=dints_fixedA[k], xerr=dbaselines[k]/lam_g, marker="o", linestyle="", color=colorA34)
                ax_sc3.errorbar(baselines[k]/lam_uv, ints_fixedB[k], yerr=dints_fixedB[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB34)
                ax_sc2.errorbar(baselines[k], ints_fixedA_scaled[k], yerr=dints_fixedA_scaled[k], xerr=dbaselines[k], marker="o", linestyle="", color=colorA34)
                ax_sc4.errorbar(baselines[k], ints_fixedB_scaled[k], yerr=dints_fixedB_scaled[k], xerr=dbaselines[k], marker="o", linestyle="", color=colorB34)
                # all SC curves in one plot
                #ax_combi.errorbar(baselines[k]/lam_g,  ints_fixedA[k], yerr=dints_fixedA[k], xerr=dbaselines[k]/lam_g,  marker="o", linestyle="", color=colorA34, label=labelA)
                #ax_combi.errorbar(baselines[k]/lam_uv, ints_fixedB[k], yerr=dints_fixedB[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB34, label=labelB)
                ax_combi.errorbar(baselines[k]/lam_g, ints_fixedA_scaled[k], yerr=dints_fixedA_scaled[k], xerr=dbaselines[k]/lam_g, marker="o", linestyle="", color=colorA34)
                ax_combi.errorbar(baselines[k]/lam_uv, ints_fixedB_scaled[k], yerr=dints_fixedB_scaled[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB34)
                ax_limb.errorbar(baselines[k]/lam_g, ints_fixedA_scaled[k], yerr=dints_fixedA_scaled[k], xerr=dbaselines[k]/lam_g, marker="o", linestyle="", color=colorA34)
                ax_limb.errorbar(baselines[k]/lam_uv, ints_fixedB_scaled[k], yerr=dints_fixedB_scaled[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB34)
            # plot SC fit and error band
            ax_sc1.plot(xplot_g, uti.spatial_coherence(xplot,*popt_odrA, lam_g), label=labelA, color=colorA34, linewidth=2)
            ax_sc1.fill_between(xplot_g, uti.spatial_coherence(xplot,popt_odrA[0]+perr_odrA[0],popt_odrA[1]-perr_odrA[1], lam_g), uti.spatial_coherence(xplot,popt_odrA[0]-perr_odrA[0],popt_odrA[1]+perr_odrA[1], lam_g), color=colorA34, alpha=0.3)
            ax_sc3.plot(xplot_uv, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), label=labelB, color=colorB34, linewidth=2)  
            ax_sc3.fill_between(xplot_uv, uti.spatial_coherence(xplot,popt_odrB[0]+perr_odrB[0],popt_odrB[1]-perr_odrB[1], lam_uv), uti.spatial_coherence(xplot,popt_odrB[0]-perr_odrB[0],popt_odrB[1]+perr_odrB[1], lam_uv), color=colorB34, alpha=0.2)
            #ax_combi.plot(xplot_g, uti.spatial_coherence(xplot,*popt_odrA, lam_g), label=labelA, color=colorA34, linewidth=2)
            #ax_combi.plot(xplot_uv, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), label=labelB, color=colorB34, linewidth=2)   
            # plot scaled version of SC fit
            ax_sc2.plot(xplot, uti.spatial_coherence(xplot,1, float(popt_odrA[1]), lam_g), label=labelA[0:9], color=colorA34, linewidth=2)
            ax_sc4.plot(xplot, uti.spatial_coherence(xplot,1, float(popt_odrB[1]), lam_uv),label=labelB[0:9], color=colorB34,  linewidth=2)
            ax_combi.plot(xplot_g, uti.spatial_coherence(xplot,1, popt_odrA[1], lam_g), label=labelA, color=colorA34, linewidth=2)
            ax_combi.plot(xplot_uv, uti.spatial_coherence(xplot,1, popt_odrB[1], lam_uv), label=labelB, color=colorB34, linewidth=2)
            ax_limb.plot(xplot_g, uti.spatial_coherence(xplot,1, popt_odrA[1], lam_g), label=labelA, color=colorA34, linewidth=2)
            ax_limb.plot(xplot_uv, uti.spatial_coherence(xplot,1, popt_odrB[1], lam_uv), label=labelB, color=colorB34, linewidth=2)
            # add zero baseline data point with error bar
            ax_sc1.errorbar(xplot_g[0],  uti.spatial_coherence(xplot[0],*popt_odrA, lam_g),  yerr=perr_odrA[0], marker='x', color=colorA34 )
            ax_sc3.errorbar(xplot_uv[0], uti.spatial_coherence(xplot[0],*popt_odrB, lam_uv), yerr=perr_odrB[0], marker='x', color=colorB34 )
            # add vertical lines for Nullstellen and text to plots
            ax_sc1.axvline(x=nsA/lam_g, color=colorA34,ymax=0.4); ax_sc3.axvline(x=nsB/lam_uv, color=colorB34, ymax=0.4)
            ax_sc1.text(x=xplot_g[1000], y=16, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrA[1]), uti.rad2mas(perr_odrA[1])), color=colorA34)
            ax_sc1.text(x=xplot_g[1000], y=14, s='Amplitude: {:.3f} +/- {:.3f}'.format(popt_odrA[0], perr_odrA[0]), color=colorA34)
            ax_sc3.text(x=xplot_uv[800], y=16, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrB[1]), uti.rad2mas(perr_odrB[1])), color=colorB34, bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
            ax_sc3.text(x=xplot_uv[800], y=14, s='Amplitude: {:.3f} +/- {:.3f}'.format(popt_odrB[0], perr_odrB[0]), color=colorB34, bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
    
    # add HBT curve and making plot pretty        
    ax_sc2.plot(xplot, uti.spatial_coherence(xplot,1, ang_HBT, float(lam_HBT)), label="HBT {}nm".format(lam_HBT[0:3]), color="red", linewidth=2)
    ax_sc1.axhline(y=0.0, color='black', linestyle='--'); ax_sc2.axhline(y=0.0, color='black', linestyle='--'); ax_sc3.axhline(y=0.0, color='black', linestyle='--'); ax_sc4.axhline(y=0.0, color='black', linestyle='--')
    ax_sc1.legend() ; ax_sc2.legend(); ax_sc3.legend(); ax_sc4.legend()

    np.savetxt('spatial_coherence/{}/amplitudes_odr.sc'.format(star), np.c_[amplitudes_odr], header='14: ampA, dampA, ampB, dampB/n 34: ampA, dampA, ampB, dampB')
    np.savetxt('spatial_coherence/{}/angular_dia_odr.sc'.format(star), np.c_[ang_odr], header='14: angA, dangA, angB, dangB/n 34: angA, dangA, angB, dangB')
    
    print(baselines_all)
    print(ints_fixed_all_scaled)
    print(len(baselines_all))
    print(len(ints_fixed_all_scaled))
    print(len(baselines_all[0]), len(ints_fixed_all_scaled[0]))
    #--------------------#
    # Try fitting with ods
    # Model object
    from scipy import odr
    '''
    sc_model = odr.Model(uti.spatial_coherence_odr)
    # RealData object
    rdata = odr.RealData( baselines_all, ints_fixed_all_scaled, sx=dbaselines_all, sy=dints_fixed_all_scaled )
    # Set up ODR with model and data
    odrODR = odr.ODR(rdata, sc_model, beta0=[22,2.7e-9])
    # Run the regression
    out = odrODR.run()
    # Fit parameters
    popt_odr_all = out.beta
    perr_odr_all = out.sd_beta
    chi_odr_all  = out.res_var # chi squared value
    '''
    # scaled ods model
    sc_model_sc = odr.Model(uti.spatial_coherence_odr_scaled)
    # RealData object
    rdata = odr.RealData( baselines_all, ints_fixed_all_scaled, sx=dbaselines_all, sy=dints_fixed_all_scaled )
    # Set up ODR with model and data
    odrODR_sc = odr.ODR(rdata, sc_model_sc, beta0=[2.7e-9])
    # Run the regression
    out_sc = odrODR_sc.run()
    # Fit parameters
    popt_odr_all_sc = out_sc.beta
    perr_odr_all_sc = out_sc.sd_beta
    chi_odr_all_sc  = out_sc.res_var # chi squared value

    print("SC fit all")
    print("Angular diameter AVG (odr): {:.3f} +/- {:.3f} (mas)".format(uti.rad2mas(popt_odr_all_sc[0]), uti.rad2mas(perr_odr_all_sc[0])))
    #print("Amplitude: {:.3f} +/- {:.3f}".format(popt_odr_all[0], perr_odr_all[0]))
    
    ax_combi.plot(xplot_all, uti.spatial_coherence(xplot,1,popt_odr_all_sc, lam_all), color='red', linewidth=2)
    ax_combi.fill_between(xplot_all, uti.spatial_coherence(xplot,1,popt_odr_all_sc[0]-perr_odr_all_sc[0], lam_all), uti.spatial_coherence(xplot,1,popt_odr_all_sc[0]+perr_odr_all_sc[0], lam_all), color='red', alpha=0.5)
    ax_combi.text(x=xplot_all[2000], y=0.75, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odr_all_sc[0]), uti.rad2mas(perr_odr_all_sc[0])), color='red')
    ax_combi.text(x=xplot_all[2000], y=0.7, s='$\chi^2$/dof={:.2f}'.format(chi_odr_all_sc), color='red')
    ax_combi.axhline(0.0, color='black', linestyle='--') 
    ax_combi.legend()

    '''
    #--------------------#
    # Try fitting with ods
    # Limb darkening model object

    sc_model_ld = odr.Model(uti.SC_limb_darkening_odr)
    # Set up ODR with model and data
    odrODR_ld = odr.ODR(rdata, sc_model_ld, beta0=[2.7e-9])
    # Run the regression
    out_ld = odrODR_ld.run()
    # Fit parameters
    popt_odr_all_ld = out_ld.beta
    perr_odr_all_ld = out_ld.sd_beta
    chi_odr_all_ld  = out_ld.res_var # chi squared value

    print("SC fit all limb darkening")
    print("Angular diameter AVG (odr): {:.3f} +/- {:.3f} (mas)".format(uti.rad2mas(popt_odr_all_ld[0]), uti.rad2mas(perr_odr_all_ld[0])))


    ax_limb.plot(xplot_all, uti.SC_limb_darkening(xplot,1,popt_odr_all_ld, lam_all, u=0.8), color='red', linewidth=2)
    ax_limb.fill_between(xplot_all, uti.SC_limb_darkening(xplot,1,popt_odr_all_ld[0]-perr_odr_all_ld[0], lam_all, u=0.8), uti.SC_limb_darkening(xplot,1,popt_odr_all_ld[0]+perr_odr_all_ld[0], lam_all, u=1), color='red', alpha=0.5)
    ax_limb.text(x=xplot_all[2000], y=0.8, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odr_all_ld[0]), uti.rad2mas(perr_odr_all_ld[0])), color='red')
    ax_limb.text(x=xplot_all[2000], y=0.75, s='$\chi^2$/dof={:.2f}'.format(chi_odr_all_ld), color='red')
    ax_limb.axhline(0.0, color='black', linestyle='--') 

    ax_limb.legend()


    '''










    plt.show()

plt.figure(figsize=(6,7))
par_fixing(star, 14)
par_fixing(star, 34)
plt.savefig("images/{}/{}_fixed_par.pdf".format(star,star))
chunk_ana(star, 14)
chunk_ana(star, 34)
plotting(star)

