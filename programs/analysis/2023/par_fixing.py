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
from optparse import OptionParser

import utilities as uti
import corrections as cor
import geometry as geo

star = sys.argv[1]

# Option parser for options
parser = OptionParser()
parser.add_option("-o", "--only", dest="onlys", help="only telescope combinations")

(options, args) = parser.parse_args()
onlys = str(options.onlys)

if onlys != "None":
    onlys = onlys.split(",")

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

ratioA = []; ratioB = []

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
    xplot, popt, perr = uti.fit(g2_allA, x, -100, +100)
    mu_A[c1][c2] = popt[1]; sigma_A[c1][c2] = popt[2] # fixing mu and sigma
    amp_A[c1][c2] = popt[0]*1e7
    noise_A = np.std(g2_allA)*1e7
    dmuA = []; dsigA = []
    dmuA = perr[1]; dsigA = perr[2]
    integral, dintegral = uti.integral(popt, perr)
    print("{} A mean: {:.3f} +/- {:.3f} \t sigma: {:.3f} +/- {:.3f}".format(telstring, mu_A[c1][c2], perr[1],sigma_A[c1][c2],perr[2]))
    #print("{} A 470nm amp: {:.2f}e-7 +/- {:.2f}e-7 \t mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs \t A Noise: {:.2f} \t Ratio: {:.2f}".format(telstring, amp_A[c1][c2], perr[0]*1e7, mu_A[c1][c2], perr[1],sigma_A[c1][c2],perr[2],1e6*integral,1e6*dintegral, noise_A, amp_A[c1][c2]/noise_A))
    ratioA.append(amp_A[c1][c2]/noise_A)
    plt.plot(x, g2_allA, label=telstring + "A", color=uti.color_chA)
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    # Channel B
    xplot, popt, perr = uti.fit(g2_allB, x, -100, +100)
    mu_B[c1][c2] = popt[1]; sigma_B[c1][c2] = popt[2]
    amp_B[c1][c2] = popt[0]*1e7
    noise_B = np.std(g2_allB)*1e7
    dmuB = []; dsigB = []
    dmuB = perr[1]; dsigB = perr[2]
    integral, dintegral = uti.integral(popt, perr)
    print("{} B mean: {:.3f} +/- {:.3f} \t sigma: {:.3f} +/- {:.3f}".format(telstring, mu_B[c1][c2], perr[1],sigma_B[c1][c2],perr[2]))
    #print ("{} B 375nm amp: {:.2f}e-7 +/- {:.2f}e-7 \t mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs \t B Noise: {:.2f} \t Ratio: {:.2f}".format(telstring,amp_B[c1][c2], perr[0]*1e7, mu_B[c1][c2],perr[1],sigma_B[c1][c2],perr[2],1e6*integral,1e6*dintegral, noise_B, amp_B[c1][c2]/noise_B))
    ratioB.append(amp_B[c1][c2]/noise_B)
    plt.plot(x, g2_allB, label=telstring + "B", color=uti.color_chB)
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    
    plt.legend(); plt.xlim(-100,100); plt.grid()
    plt.ticklabel_format(useOffset=False)
    plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")
    plt.tight_layout()
    
    #np.savetxt("g2_functions/{}/{}/mu_sig.txt".format(star,telstring), np.c_[mu_A[c1][c2], dmuA, sigma_A[c1][c2], dsigA, mu_B[c1][c2], dmuB, sigma_B[c1][c2], dsigB], header="muA, dmuA, sigA, dsigA, muB, dmuB, sigB, dsigB")
    #np.savetxt('g2_functions/{}/{}/g2_allA.txt'.format(star,telstring), np.c_[x, g2_allA])


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
            telcombistring = str(c1) + str(c2)
            print ("Found telescope combination {}".format(telcombi))
            if telcombistring in onlys or onlys == "None":
                par_fixing(star, telcombi)
                #chunk_ana(star, telcombi, ratioA, ratioB)
#plotting(star)

telcombis = ['14','34']
# mean for fit range 50
meanA1 = [2.165,  -0.527]; dmeanA1 = [0.113, 0.072]
meanB1 = [-0.306,  -1.862]; dmeanB1 = [0.383,0.389]
# mean for fit range 100
meanA2 = [2.172, -0.524] ; dmeanA2 = [0.104, 0.102]
meanB2 = [-0.306, -1.841]; dmeanB2 = [0.328, 0.596]


plt.figure('parameters')
plt.errorbar(x=telcombis, y=meanA1, yerr=dmeanA1, marker='o', ls='', label='470nm 50')
plt.errorbar(x=telcombis, y=meanB1, yerr=dmeanB1, marker='o', ls='', label='375nm 50')
plt.errorbar(x=telcombis, y=meanA2, yerr=dmeanA2, marker='x', ls='', label='470nm 100')
plt.errorbar(x=telcombis, y=meanB2, yerr=dmeanB2, marker='x', ls='', label='375nm 100')
plt.title('Mimosa: mean')
plt.xlabel('Telcombis')
plt.legend()




plt.show()            