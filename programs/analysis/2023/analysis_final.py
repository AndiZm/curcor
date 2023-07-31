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

colorA14 = uti.color_chA
colorB14 = uti.color_chB
colorA34 = 'limegreen'
colorB34 = 'royalblue'

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

    # Fit for gaining mu and sigma to fix these parameters
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
    np.savetxt("g2_functions/fixed_parameters/{}/mu_sig_{}.txt".format(star,telcombi), np.c_[mu_A, sigma_A, mu_B, sigma_B], header="muA, sigA, muB, sigB")

#########################################
###### Chunk analysis ###################
#########################################
def chunk_ana(star, telcombi):
    intsA = []; dintsA = []; times = []
    intsB = []; dintsB = []
    ints_fixedA = []; dints_fixedA = []
    ints_fixedB = []; dints_fixedB = []
    timestrings = []
    
    # initialize cleaned arrays and read in mu and sigma
    chA_clean = []; chB_clean = []; ampA = []; ampB = []; muA = []; muB =[] ; chiA =[]; chiB = []
    ffts = []
    chAs    = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/ChA.txt".format(star, telcombi))
    chBs    = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/ChB.txt".format(star, telcombi))     
    mu_A, sig_A, mu_B, sig_B = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_{}.txt".format(star,telcombi))
    data      = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/baseline.txt".format(star, telcombi))
    baselines = data[:,1]; dbaselines = data[:,2]

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
        xplotf, popt_A, perr_A, chi_A = uti.fit_fixed1(chA, x, -50, 50, sig_A, mu_start=mu_A, error=error, par=2 )
        Int, dInt = uti.integral_fixed(popt_A, perr_A, sig_A)
        dInt = np.sqrt( dInt**2 + (np.std(chA)*sig_A*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
        ints_fixedA.append(1e6*Int); dints_fixedA.append(1e6*dInt)# in femtoseconds
        print('CHIA = {}'.format(chi_A))


        xplotf, popt_B, perr_B, chi_B = uti.fit_fixed1(chB, x, -50, 50, sig_B, mu_start=mu_B, error=error, par=2)
        Int, dInt = uti.integral_fixed(popt_B, perr_B, sig_B)
        dInt = np.sqrt( dInt**2 + (np.std(chB)*sig_B*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
        ints_fixedB.append(1e6*Int); dints_fixedB.append(1e6*dInt)# in femtoseconds
        print('CHIB = {}'.format(chi_B))
    
        # Check acquisition time of original data
        timestring = ephem.Date(data[:,0][i])
        timestrings.append(timestring)
        print("{}".format(i), timestring, Int, dInt)
        # Shorter timestring for plotting, not showing year and seconds
        tstring_short = str(timestring)[5:-3]

        # save cleaned data and fit parameter
        chA_clean.append(chA)
        chB_clean.append(chB)
        ampA.append(popt_A[0]); ampB.append(popt_B[0])
        muA.append(popt_A[1]); muB.append(popt_B[1])
        chiA.append(chi_A); chiB.append(chi_B)

    # store cleaned data
    np.savetxt("g2_functions/weight_rms_squared/{}/{}/ChA_clean.txt".format(star,telcombi), np.c_[chA_clean], header="{} Channel A cleaned".format(star) )
    np.savetxt("g2_functions/weight_rms_squared/{}/{}/ChB_clean.txt".format(star,telcombi), np.c_[chB_clean], header="{} Channel B cleaned".format(star) )
    np.savetxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star, telcombi), np.c_[muA, ampA, muB, ampB, timestrings], header="muA, ampA, muB, ampB, timestrings")
    np.savetxt("g2_functions/fixed_parameters/{}/chi_squared_{}.txt".format(star, telcombi), np.c_[chiA, chiB], header="chiA, chiB")
    np.savetxt("g2_functions/fixed_parameters/{}/xplot.txt".format(star), np.c_[xplotf])
    np.savetxt("spatial_coherence/{}_{}_sc_data.txt".format(star,telcombi), np.c_[baselines, dbaselines, ints_fixedA, dints_fixedA, ints_fixedB, dints_fixedB])

    print("DONE Chunks {}".format(telcombi))

def plotting(star):
    telcombis = [14,34]
    ticks = []
    ints_fixedA_scaled = []; dints_fixedA_scaled = []; ints_fixedB_scaled = []; dints_fixedB_scaled = []

    # Define figure which will show individual g2 cross correlations
    crossfigure = plt.figure(figsize=(10,7))
    # cross correlations for telcombis
    ax_cross1 = crossfigure.add_subplot(211); ax_cross1.set_title("Cross correlations of {} for {}".format(star, telcombis[0]))
    ax_cross1.set_xlabel("Time difference (ns)"); ax_cross1.set_ylabel("$g^{(2)}$"); ax_cross1.ticklabel_format(useOffset=False)
    ax_cross1.set_xlim(-150,150)
    ax_cross2 = crossfigure.add_subplot(212); ax_cross2.set_title("Cross correlations of {} for {}".format(star, telcombis[1]))
    ax_cross2.set_xlabel("Time difference (ns)"); ax_cross2.set_ylabel("$g^{(2)}$"); ax_cross2.ticklabel_format(useOffset=False)
    ax_cross2.set_xlim(-150,150)
    plt.tight_layout()

    # Define figure which will show the spatial coherence curve (baseline vs. g2 integral)
    scfigure = plt.figure(figsize=(6,7))
    sps1, sps2, sps3, sps4 = GridSpec(2,2)
    ax_sc1 = scfigure.add_subplot(211)
    ax_sc1.set_title("Spatial coherence of {} for 470nm".format(star))
    ax_sc1.set_xlabel("Baseline/Wavelength"); ax_sc1.set_ylabel("Coherence time (fs)")
    ax_sc2 = scfigure.add_subplot(212)
    ax_sc2.set_title("Spatial coherence of {} for 375nm".format(star))
    ax_sc2.set_xlabel("Baseline/Wavelength"); ax_sc2.set_ylabel("Coherence time (fs)")
    plt.tight_layout()

    # Define figure showing mean of g2 fcts
    meanfig = plt.figure(figsize=(10,7))
    ax_mean = plt.subplot(111)
    ax_mean.set_title('Mean of $g^{(2)}$ vs time'); ax_mean.set_xlabel('Time UTC'); ax_mean.set_ylabel('Mean')
    ax_mean.tick_params(labelrotation=45)

    # Define figure showing chi squared of g2 fcts
    chifigure =plt.figure(figsize=(10,7))
    ax_chi = plt.subplot(111)
    ax_chi.set_title('Chi squared of $g^{(2)}$ vs time'); ax_chi.set_xlabel('Time UTC'); ax_chi.set_ylabel('Chi squared')
    ax_chi.tick_params(labelrotation=45)

    
    # for loop over telescope combinations
    for i in range(len(telcombis)):
        # read in all necessary data and parameters
        chAs = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/ChA_clean.txt".format(star,telcombis[i]))
        chBs = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/ChB_clean.txt".format(star,telcombis[i]))
        mu_A, sigA, mu_B, sigB = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_{}.txt".format(star,telcombis[i]))
        muA = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,0]
        ampA = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,1]
        muB = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,2]
        ampB = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,3]
        timestrings  = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,4]
        xplotf = np.loadtxt("g2_functions/fixed_parameters/{}/xplot.txt".format(star))
        chiA = np.loadtxt("g2_functions/fixed_parameters/{}/chi_squared_{}.txt".format(star, telcombis[i]))[:,0]
        chiB = np.loadtxt("g2_functions/fixed_parameters/{}/chi_squared_{}.txt".format(star, telcombis[i]))[:,1]
        baselines = np.loadtxt("spatial_coherence/{}_{}_sc_data.txt".format(star,telcombis[i])) [:,0]
        dbaselines = np.loadtxt("spatial_coherence/{}_{}_sc_data.txt".format(star,telcombis[i])) [:,1]
        ints_fixedA = np.loadtxt("spatial_coherence/{}_{}_sc_data.txt".format(star,telcombis[i])) [:,2]
        dints_fixedA = np.loadtxt("spatial_coherence/{}_{}_sc_data.txt".format(star,telcombis[i])) [:,3]
        ints_fixedB = np.loadtxt("spatial_coherence/{}_{}_sc_data.txt".format(star,telcombis[i])) [:,4]
        dints_fixedB = np.loadtxt("spatial_coherence/{}_{}_sc_data.txt".format(star,telcombis[i])) [:,5]


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
        popt_odrB = outUV.beta
        perr_odrB = outUV.sd_beta
        #--------------------#

        print("SC fits")
        print ("{}A 470nm angular diameter AVG (odr): {:.3f} +/- {:.3f} (mas)".format(telcombis[i], uti.rad2mas(popt_odrA[1]), uti.rad2mas(perr_odrA[1])))
        print("{}A 470nm Amplitude {}".format(telcombis[i], popt_odrA[0]))
        print ("{}B 375nm Angular diameter AVG (odr) B : {:.3f} +/- {:.3f} (mas)".format(telcombis[i], uti.rad2mas(popt_odrB[1]), uti.rad2mas(perr_odrB[1])))
        print("{}B 375nm Amplitude: {}".format(telcombis[i], popt_odrB[0]))


        # Make additional scaled parameters
        for k in range (0,len(ints_fixedA)):
            ints_fixedA_scaled.append(ints_fixedA[k]  / popt_odrA[0])
            dints_fixedA_scaled.append(dints_fixedA[k] / popt_odrA[0])
        
            ints_fixedB_scaled.append(ints_fixedB[k]  / popt_odrB[0])
            dints_fixedB_scaled.append(dints_fixedB[k] / popt_odrB[0])

        # Define colormap for plotting all summarized individual g2 functions
        cm_sub = np.linspace(1.0, 0.0, len(chAs))
        colors = [cm.viridis(x) for x in cm_sub]
        # Demo function for initializing x axis and some stuff
        demo = chAs[0]
        x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)
        error = np.std(chAs[0][0:4000])
        print('ERROR = {}'.format(error))
        xplot = np.arange(0.1,300,0.1)
        lam_g = 470e-9
        lam_uv = 375e-9
        # make x-axis wavelength indepedent 
        xplot_g = np.zeros(len(xplot))
        for j in range(0,len(xplot)):
            xplot_g[j] = xplot[j] / lam_g
        xplot_uv = np.zeros(len(xplot))
        for j in range(0,len(xplot)):
            xplot_uv[j] = xplot[j] /lam_uv
        
        # add HBT measurement to the plot
        xplot_HBT = np.zeros(len(xplot))
        for j in range(0,len(xplot)):
            xplot_HBT[j] = (xplot[j] /float(lam_HBT))


        # Nullstelle for SC plot
        nsA = 1.22*(lam_g/popt_odrA[1])
        nsB = 1.22*(lam_uv/popt_odrB[1])

        # Subplot for all cross correlations for telcombi 14
        if telcombis[i] == 14:
            labelA = '{}A 470nm'.format(telcombis[i])
            labelB = '{}B 375nm'.format(telcombis[i])              
            for j in range(len(chAs)):
                the_shift = (len(chAs)-j-1)*1e-6
                ticks.append(1.+the_shift)
                timestring = ephem.Date(timestrings[j])
                tstring_short = str(timestring)[5:-3]
                ax_cross1.set_yticks(np.arange(1,1+2e-6*len(chAs),2e-6))
                ax_cross1.errorbar(x, chAs[j] + the_shift, yerr=error, linestyle="-", color = colorA14,   alpha=0.7)
                ax_cross1.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampA[j], mu=muA[j], sigma=sigA, shift=j, inverse=True, ntotal=len(chAs)), color=colorA14, linestyle="--", zorder=4)
                ax_cross1.errorbar(x, chBs[j] + the_shift, yerr=error, linestyle="-", color =colorB14,   alpha=0.7)                
                ax_cross1.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampB[j], mu=muB[j], sigma=sigB, shift=j, inverse=True, ntotal=len(chBs)), color=colorB14, linestyle="--", zorder=4)
                ax_cross1.text(x=70, y=1+the_shift+0.4e-6, s=tstring_short, color=colors[j], fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
                p1, = ax_mean.plot(tstring_short, muA[j], color=colorA14, marker='o', label=labelA)
                p2, = ax_mean.plot(tstring_short, muB[j], color=colorB14, marker='o', label=labelB)
                p5, = ax_chi.plot(tstring_short, chiA[j], color=colorA14, marker='o', label=labelA)
                p6, = ax_chi.plot(tstring_short, chiB[j], color=colorB14, marker='o', label=labelB)
                if j==6:
                    ax_mean.axvline(tstring_short, color='black')
                    ax_chi.axvline(tstring_short, color='black')
            # Plot SC data
            for k in range (0,len(baselines)):
                ax_sc1.errorbar(baselines[k]/lam_g, ints_fixedA[k], yerr=dints_fixedA[k], xerr=dbaselines[k]/lam_g, marker="o", linestyle="", color=colorA14)
                ax_sc2.errorbar(baselines[k]/lam_uv, ints_fixedB[k], yerr=dints_fixedB[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB14)
            ax_sc1.plot(xplot_g, uti.spatial_coherence(xplot,*popt_odrA, lam_g), label=labelA, color=colorA14, linewidth=2)
            ax_sc2.plot(xplot_uv, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), label=labelB, color=colorB14, linewidth=2)
            ax_sc1.axvline(x=nsA/lam_g, color='black')
            ax_sc2.axvline(x=nsB/lam_uv, color='black')

        # Subplot for all cross correlations for telcombi 34
        elif telcombis[i] == 34:
            labelA = '{}A 470nm'.format(telcombis[i])
            labelB = '{}B 375nm'.format(telcombis[i])
            for j in range(len(chAs)):
                the_shift = (len(chAs)-j-1)*1e-6
                ticks.append(1.+the_shift)
                timestring = ephem.Date(timestrings[j])
                tstring_short = str(timestring)[5:-3]
                ax_cross2.set_yticks(np.arange(1,1+2e-6*len(chAs),2e-6))
                ax_cross2.errorbar(x, chAs[j] + the_shift, yerr=0, linestyle="-", color = colorA34,   alpha=0.7)
                ax_cross2.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampA[j], mu=muA[j], sigma=sigA, shift=j, inverse=True, ntotal=len(chAs)), color=colorA34, linestyle="--", zorder=4)
                ax_cross2.errorbar(x, chBs[j] + the_shift, yerr=0, linestyle="-", color = colorB34,   alpha=0.7)
                ax_cross2.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampB[j], mu=muB[j], sigma=sigB, shift=j, inverse=True, ntotal=len(chBs)), color=colorB34, linestyle="--", zorder=4)
                ax_cross2.text(x=70, y=1+the_shift+0.4e-6, s=tstring_short, color=colors[j], fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
                p3, = ax_mean.plot(tstring_short, muA[j], color=colorA34, marker='x', label=labelA)
                p4, = ax_mean.plot(tstring_short, muB[j], color=colorB34, marker='x', label=labelB)
                p7, = ax_chi.plot(tstring_short, chiA[j], color=colorA34, marker='x', label=labelA)
                p8, = ax_chi.plot(tstring_short, chiB[j], color=colorB34, marker='x', label=labelB)
                if j==0 or j==4 or j==15 or j==12:
                    ax_mean.axvline(tstring_short, color='black')
                    ax_chi.axvline(tstring_short, color='black')
            # Plot SC data
            for i in range (0,len(baselines)):
                ax_sc1.errorbar(baselines[i]/lam_g, ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i]/lam_g, marker="o", linestyle="", color=colorA34)
                ax_sc2.errorbar(baselines[i]/lam_uv, ints_fixedB[i], yerr=dints_fixedB[i], xerr=dbaselines[i]/lam_uv, marker="o", linestyle="", color=colorB34)
            ax_sc1.plot(xplot_g, uti.spatial_coherence(xplot,*popt_odrA, lam_g), label=labelA, color=colorA34, linewidth=2)
            ax_sc2.plot(xplot_uv, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), label=labelB, color=colorB34, linewidth=2)                
            ax_sc1.axvline(x=nsA/lam_g, color='black')
            ax_sc2.axvline(x=nsB/lam_uv, color='black')
        # SC plot
               #plt.text(baselines[i]+1,ints_fixed[i]+0.5,ephem.Date(data[:,0][i]), color=colors[i])
        #ax_sc.plot(xplot, uti.spatial_coherenceG(xplot,*popt_odrA),   label="470 nm", color="green", linewidth=2)
        #ax_sc.plot(xplot, uti.spatial_coherenceUV(xplot,*popt_odrB), label="375 nm", color="blue",  linewidth=2)
        #ax_sc.plot(xplot, uti.spatial_coherence(xplot, 20, 4.6e-9),   label="fit", color="blue", linewidth=2)
    ax_sc1.axhline(y=0.0, color='black', linestyle='--'); ax_sc2.axhline(y=0.0, color='black', linestyle='--')
    ax_sc1.legend() ; ax_sc2.legend()
    ax_sc1.text()
    plt.tight_layout()
    ax_mean.legend(handles=[p1,p2,p3,p4])
    ax_mean.axhline(0.0, color='black', linestyle='--')
    ax_chi.legend(handles=[p5,p6,p7,p8])
    ax_chi.axhline(0.0, color='black', linestyle='--')
    plt.show()

plt.figure(figsize=(6,7))
par_fixing(star, 14)
par_fixing(star, 34)
plt.savefig("images/ana_final/{}_fixed_par.pdf".format(star))
chunk_ana(star, 14)
chunk_ana(star, 34)
plotting(star)

