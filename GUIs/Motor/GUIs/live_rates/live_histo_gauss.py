import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.pyplot import cm
import matplotlib as mpl
from scipy.optimize import curve_fit
from pylab import rcParams
import os
rcParams['figure.figsize'] = 13,6
from pylab import *

 
import functions as func

def gauss_function(x, a, x0, sigma):
    return a*np.exp(-(x-x0)**2/(2*sigma**2))

def multi_gauss_function(x, a, x0, sigma, a2, x02, sigma2):
    return gauss_function(x, a, x0, sigma)+gauss_function(x, a2, x02, sigma2)

def gauss_function_e7(x, a, x0, sigma):
    return a*1.e7*np.exp(-(x-x0)**2/(2.*sigma**2))


def main():

    Figure1 = plt.figure(num = None, figsize = (14,7))
    ax1 = Figure1.add_subplot(1,1,1)                                # subplots

    #### files einlesen ####
    T = {} # dictionary wie liste 

    path = '20200120_PMT1_newnewbase_newamp/'

    for file in os.listdir(path):
        if not file.endswith('.txt'):
            continue

        fn =  path + file
        z1, z2 = file.split('.txt')[0].split('_')
        z1, z2 = int(z1), int(z2)

        if not z1 in T.keys():                   # liste von allen ersten 'Zahlen' in dictionary also keys z1, value = z2 wert in keys (1,2,3)
            T[z1] = {}                           # leeres Unterdictionary um anzufangen

        T[z1][z2] = np.genfromtxt(fn)            # fuegt z2 in unterdictionary 
        

    #### colormaps ####

    cm_sub = np.linspace(1.0, 0.0, len(T))                            #len(T)) oder 4
    colors = [cm.viridis(x) for x in cm_sub]

    
    transmission = [0.0001, 0.0003, 0.0005, 0.0007, 0.0012, 0.0014, 0.0016, 0.0019, 0.003, 0.0042, 0.004, 0.0042, 0.008, 0.006, 0.012, 0.016, 0.022, 0.023, 0.029, 0.037, 0.067, 0.072, 0.09, 0.16, 0.23, 0.54]
    rate = [1.15, 1.23, 1.37, 1.6, 1.98, 2.02, 2.26, 2.58, 3.43, 4.03, 3.99, 4.73, 7.31, 5.54, 9.58, 12.42, 16.33, 17.18, 21.17, 25.95, 47.47, 55.96, 62.49, 101.39, 127.40]

    print(len(T))
    x = []
    y = []
    clabels = []
    V = [0, 1150, 1250, 1350]
    d_rate = []
    int_rate = []
    mu1 = []
    d_mu1 = []
    mu2 = []
    d_mu2 = []
    sig1 = []
    d_sig1 = []
    distance = []
    d_distance = []
    ylabels =[]
    sig2 = []
    d_sig2 = []
    mean = []
    peakvalley = []
   

    for j, i in enumerate(sorted(T.keys())):                              #range(1,4):      enumerate(sorted(T.keys())):        
        if i in [47, 49, 53, 56, 60]:                         
            x.append(T[i][1][:,0] - 127)
        else:
            x.append(T[i][1][:,0])
        y.append(T[i][1][:,1])
        ax1.plot(x[-1], y[-1]/0.8, color = colors[j])              #[i-1]  #, label=V[i])
        clabels.append(i)
        


        #### Gauss fit for data and noise ####
        if 0 <= j <= 7: #fuer 2 ->11 
            m = -6
            mask1 = (x[-1]<= -6.) # fuer 2 -> 10                                           # Bereich aendern
            x_fit1 = x[-1][mask1]
            y_fit1 = y[-1][mask1]

            p01 = [1e7, -10, 10]                                                                     # Startparameter aendern
            popt1, pcov1 = curve_fit(gauss_function, x_fit1, y_fit1/0.8, p0= p01, maxfev= 1000000)
            #print("Mittel:\t" + str(j) + '   ' + str(i) + '    ' + str(popt[1]))

            mu1.append( popt1[1] )
            perr1 = np.sqrt(np.diag(pcov1))
            d_mu1.append( perr1[1] )

            sig1.append(popt1[2])
            d_sig1.append(perr1[2])

            peakvalley.append(np.abs(mu1[-1]) - np.abs(m))

            # ax1.plot(x_fit1, gauss_function(x_fit1,*popt1), c='black', zorder=20)
            # ax1.plot(mu1[-1], gauss_function(mu1[-1], *popt1), marker='o',c='black')
            
            int_rate.append( popt1[0] * np.abs(popt1[2]) * np.sqrt(2*np.pi) *1e-6 )
            d_rate.append( np.sqrt( (np.sqrt(2*np.pi) * popt1[2] * perr1[0])**2 + (np.sqrt(2*np.pi) * popt1[0] * perr1[2])**2 ) *1e-6 )

            print "Integrierte Rate:\t %d %d %.2f  MHz  Fehler Rate:\t %.2f MHz" %(j, i, int_rate[j],d_rate[j])
            print "Mittel:\t %d %d %.2f   Fehler:\t %.2f MHz" %(j, i, mu1[j],d_mu1[j])
            print "Breite:\t %d %d %.2f   Fehler:\t %.2f MHz" %(j, i, sig1[j],d_sig1[j])
            print "Peak-Valley:\t %d %d %.2f " %(j, i, peakvalley[j])

            ylabels.append( round(int_rate[-1], 2))
            


            
            #### noise gauss fit ####
            x_plot = np.arange(-15,10,0.01)
            mask2 = (x[-1] <= 10) &  (x[-1] >= -5)
            x_fit2 = x[-1][mask2]
            y_fit2 = y[-1][mask2]

            p02 = [1.6e8, 0.0, 1.1]
            popt2, pcov2 = curve_fit(gauss_function, x_fit2, y_fit2/0.8, p0 = p02) #, bounds= ([1e5, -10, 0.1], [1e9, 5, 10]), maxfev = 1000000)
            # print("Mittel:\t" + str(j) + '   ' + str(i) + '    ' + str(popt2[1]))

            mu2.append( popt2[1] )
            perr2 = np.sqrt(np.diag(pcov2))
            d_mu2.append( perr2[1] )

            sig2.append(popt2[2])
            d_sig2.append(perr2[2])

            # ax1.plot(x_plot, gauss_function(x_plot, *popt2), c='black', zorder=20)
            
            distance.append(mu1[-1] - mu2[-1])
            d_distance.append(d_mu1[-1] - d_mu2[-1])

            print "Noise Mittel:\t %d %d %.2f   Fehler:\t %.2f MHz" %(j, i, mu2[j],d_mu2[j])
            print "Noise Breite:\t %d %d %.2f   Fehler:\t %.2f MHz" %(j, i, sig2[j],d_sig2[j])

        
        if 8 <= j <= 16 :    # fuer 2 bis 14                      # Zahl aendern
            mask1 = (x[-1]<= -6.) # fuer 2 -10        # Bereich aendern
            x_fit1 = x[-1][mask1]
            y_fit1 = y[-1][mask1]

            p01 = [1e6, -10, 10]                  # Startparameter aendern
            popt1, pcov1 = curve_fit(gauss_function, x_fit1, y_fit1/0.8, p0= p01, maxfev= 1000000)
            #print(popt, pcov)
            # print("Mittel:\t" + str(j) + '   ' + str(i) + '    ' + str(popt[1]))

            mu1.append( popt1[1] )
            perr1 = np.sqrt(np.diag(pcov1))
            d_mu1.append( perr1[1] )

            sig1.append(popt1[2])
            d_sig1.append(perr1[2])

            peakvalley.append(np.abs(mu1[-1]) - np.abs(m))


            # ax1.plot(x_fit1, gauss_function(x_fit1,*popt1), c='black', zorder=20)
            # ax1.plot(mu1[-1], gauss_function(mu1[-1], *popt1), marker='o',c='black')
            #except:
                #print('Fit failed')
                #plt.plot(x_fit, gauss_function(x_fit,*p0), c='black')

            int_rate.append( popt1[0] * np.abs(popt1[2]) * np.sqrt(2*np.pi) * 1e-6 )
            d_rate.append( np.sqrt( (np.sqrt(2*np.pi) * popt1[2] * perr1[0])**2 + (np.sqrt(2*np.pi) * popt1[0] * perr1[2])**2 ) * 1e-6 )

            print "Integrierte Rate:\t %d %d %.2f  MHz  Fehler Rate:\t %.2f MHz" %(j, i, int_rate[j],d_rate[j])
            print "Mittel:\t %d %d %.2f   Fehler:\t %.2f MHz" %(j, i, mu1[j],d_mu1[j])
            print "Breite:\t %d %d %.2f   Fehler:\t %.2f MHz" %(j, i, sig1[j],d_sig1[j])
            print "Peak-Valley:\t %d %d %.2f " %(j, i, peakvalley[j])

            ylabels.append( round(int_rate[-1], 2))



            #### noise gauss fit ####
            x_plot = np.arange(-15,15,0.01)
            mask2 = (x[-1] <= 10) &  (x[-1] >= -5)
            x_fit2 = x[-1][mask2]
            y_fit2 = y[-1][mask2]

            p02 = [1.6e8, -2, 1.1]
            popt2, pcov2 = curve_fit(gauss_function, x_fit2, y_fit2/0.8, p0 = p02) #, bounds= ([1e5, -10, 0.1], [1e9, 5, 10]), maxfev = 1000000)
            #print("Mittel:\t" + str(j) + '   ' + str(i) + '    ' + str(popt[1]))

            mu2.append( popt2[1] )
            perr2 = np.sqrt(np.diag(pcov2))
            d_mu2.append( perr2[1] )

            sig2.append(popt2[2])
            d_sig2.append(perr2[2])

            # ax1.plot(x_plot, gauss_function(x_plot, *popt2), c='black', zorder=20)

            distance.append(mu1[-1] - mu2[-1])
            d_distance.append(d_mu1[-1] - d_mu2[-1])



        if 17 <= j <= 18 :                             # Zahl aendern
            mask1 = (x[-1]<= -10.) #fuer 1 -10        # Bereich aendern
            x_fit1 = x[-1][mask1]
            y_fit1 = y[-1][mask1]

            p01 = [1e6, -20, 10]                  # Startparameter aendern
            popt1, pcov1 = curve_fit(gauss_function, x_fit1, y_fit1/0.8, p0= p01, maxfev= 1000000)
            #print(popt, pcov)
            # print("Mittel:\t" + str(j) + '   ' + str(i) + '    ' + str(popt[1]))

            mu1.append( popt1[1] )
            perr1 = np.sqrt(np.diag(pcov1))
            d_mu1.append( perr1[1] )

            sig1.append(popt1[2])
            d_sig1.append(perr1[2])

            peakvalley.append(np.abs(mu1[-1]) - np.abs(m))


            # ax1.plot(x_fit1, gauss_function(x_fit1,*popt1), c='black', zorder=20)
            # ax1.plot(mu1[-1], gauss_function(mu1[-1], *popt1), marker='o',c='black')
            #except:
                #print('Fit failed')
                #plt.plot(x_fit, gauss_function(x_fit,*p0), c='black')

            int_rate.append( popt1[0] * np.abs(popt1[2]) * np.sqrt(2*np.pi) * 1e-6 )
            d_rate.append( np.sqrt( (np.sqrt(2*np.pi) * popt1[2] * perr1[0])**2 + (np.sqrt(2*np.pi) * popt1[0] * perr1[2])**2 ) * 1e-6 )

            print "Integrierte Rate:\t %d %d %.2f  MHz  Fehler Rate:\t %.2f MHz" %(j, i, int_rate[j],d_rate[j])
            print "Mittel:\t %d %d %.2f   Fehler:\t %.2f MHz" %(j, i, mu1[j],d_mu1[j])
            print "Breite:\t %d %d %.2f   Fehler:\t %.2f MHz" %(j, i, sig1[j],d_sig1[j])
            print "Peak-Valley:\t %d %d %.2f " %(j, i, peakvalley[j])

            ylabels.append( round(int_rate[-1], 2))



            #### noise gauss fit ####
            x_plot = np.arange(-15,15,0.01)
            mask2 = (x[-1] <= 10) &  (x[-1] >= -7)
            x_fit2 = x[-1][mask2]
            y_fit2 = y[-1][mask2]

            p02 = [1.6e8, -2, 1.1]
            popt2, pcov2 = curve_fit(gauss_function, x_fit2, y_fit2/0.8, p0 = p02) #, bounds= ([1e5, -10, 0.1], [1e9, 5, 10]), maxfev = 1000000)
            #print("Mittel:\t" + str(j) + '   ' + str(i) + '    ' + str(popt[1]))

            mu2.append( popt2[1] )
            perr2 = np.sqrt(np.diag(pcov2))
            d_mu2.append( perr2[1] )

            sig2.append(popt2[2])
            d_sig2.append(perr2[2])

            # ax1.plot(x_plot, gauss_function(x_plot, *popt2), c='black', zorder=20)

            distance.append(mu1[-1] - mu2[-1])
            d_distance.append(d_mu1[-1] - d_mu2[-1])
    
    print(len(mu1))
    print (len(mu2))
    print (len(d_mu2))
    print(len(transmission[0:19]))
    print(len(int_rate))
    print(len(d_rate))
    print(len(sig1))
    print (len(d_sig1))
    print (len(sig2))
    print (mu1[0])
    print (sig2[0])
   


    #### extrapolation trans ####

    z1 = np.polyfit(transmission[0:19], int_rate,1)
    p1 = np.poly1d(z1) 


    ####  Colorbar ####


    norm = mpl.colors.Normalize( vmin=min(clabels) , vmax=max(clabels))
    #colormap_r = mpl.colors.ListedColormap(col1[::-1])
    cmap = cm.ScalarMappable( norm=norm, cmap=cm.viridis_r)
    cmap.set_array([])
    cbar = Figure1.colorbar( cmap, ticks=[3, 9, 15, 20, 26, 32, 37, 42], format='%d' )
    cbar.ax.set_yticklabels([ylabels[0], ylabels[2], ylabels[5], ylabels[8], ylabels[11], ylabels[14], ylabels[16], ylabels[18] ])                  
    cbar.set_label('Incident rate (MHz)', size=19, labelpad=17)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), fontsize=20)


    #### Plotting ####
    path2 = path + 'PlotsArbeit/'

    func.custom_plot( ax1, Figure1, path2 + 'Histo_PMT1newbase_1100_log', '', 'Pulse height', 'Count rate (MHz)', xlim=[10, -120], ylim=[1.e0, 1.e9], sciy='log')

    Figure2 = plt.figure(num = None, figsize = (14,7))
    ax2 = Figure2.add_subplot(1,1,1)
    ax2.errorbar(transmission[0:19], int_rate, yerr = d_rate , c='blue', marker='.', linestyle='') 
    #ax2.plot(transmission[0:19], p1(transmission[0:19]))  
    func.custom_plot( ax2, Figure2, path2 + 'rates_vs_trans', '', 'Transmission', 'Rate (MHz)')#, [0,0.03], [0,150])           #[0.0, 0.03], [0.0, 170])

    Figure3 = plt.figure(num = None, figsize = (14,7))
    ax3 = Figure3.add_subplot(1,1,1)
    ax3.errorbar(ylabels, mu1, yerr = d_mu1 , c='blue', marker='.', linestyle='')
    ax30=ax3.twinx()
    # make a plot with different y-axis using second axis object
    ax30.set_ylabel("Pulse height (mV)", fontsize=19, labelpad=9)
    mn30, mx30 = ax3.get_ylim()
    ax30.set_ylim((mn30*200)/127, (mx30*200)/127)
    ax30.tick_params(axis='y', labelsize=13)
    func.custom_plot( ax3, Figure3, path2 + 'photonpeak_vs_rate', '', 'Rate (MHz)', 'Pulse height (ADC)')#, [0,150], [-20,-11.5])         #[0.0, 170], [-35, -20])
    
    Figure4 = plt.figure(num = None, figsize = (14,7))
    ax4 = Figure4.add_subplot(1,1,1)
    ax4.errorbar(ylabels, np.abs(sig1), yerr=d_sig1 , c='blue', marker='.', linestyle='')
    ax40=ax4.twinx()
    # make a plot with different y-axis using second axis object
    ax40.set_ylabel("Pulse height (mV)", fontsize=19, labelpad=9)
    mn40, mx40 = ax4.get_ylim()
    ax40.set_ylim((mn40*200)/127, (mx40*200)/127)
    ax40.tick_params(axis='y', labelsize=13)
    func.custom_plot( ax4, Figure4, path2 + 'Sigma_photonpeak_vs_rate', '', 'Rate (MHz)', 'Pulse height (ADC)')#, [0,150], [4,12])    #[0.0, 150], [6, 20])

    Figure5 = plt.figure(num = None, figsize = (14,7))
    ax5 = Figure5.add_subplot(1,1,1)
    ax5.errorbar(ylabels, mu2, yerr = d_mu2 , c='blue', marker='.', linestyle='')
    func.custom_plot( ax5, Figure5, path2 + 'noisepeak_vs_rate', '', 'Rate (MHz)', 'Pulse height (ADC)')#, [0,150], [-5,1])     #[0.0, 170], [-7., 1.])

    
    plt.show()





if __name__ == '__main__':
    main()













