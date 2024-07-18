import numpy as np
import matplotlib.pyplot as plt

import utilities as uti
import analysis_final_sigma as afs

star = 'Nunki'
xplot = np.arange(0.1,300,0.1)
lam_new = 470e-9
lam_old = 465e-9


# Open text file with SC values for Nunki 2022
f = open("{}/{}_sc_data_2022.txt".format(star,star))
header = f.readline()
amp_A_old = header.split(' ')[1]
ang_A_old = header.split(' ')[2]

baselines_old    = np.loadtxt("{}/{}_sc_data_2022.txt".format(star,star)) [:,0]
dbaselines_old   = np.loadtxt("{}/{}_sc_data_2022.txt".format(star,star)) [:,1]
ints_fixedA_old  = np.loadtxt("{}/{}_sc_data_2022.txt".format(star,star)) [:,2]
dints_fixedA_old = np.loadtxt("{}/{}_sc_data_2022.txt".format(star,star)) [:,3]

ints_fixedA_old_scaled = []; dints_fixedA_old_scaled = []
for i in range(0,len(baselines_old)):
	ints_fixedA_old_scaled.append( ints_fixedA_old[i] / float(amp_A_old) )
	dints_fixedA_old_scaled.append( dints_fixedA_old[i] / float(amp_A_old) )

'''
# Open text file with scaled SC values for Nunki 2023
f = open("spatial_coherence/{}/{}_scaled.sc".format(star,star))
header = f.readline()
ang_A = header.split(' ')[3]

ints_fixedA_scaled  = np.loadtxt("spatial_coherence/{}/{}_scaled.sc".format(star,star)) [:,0]
dints_fixedA_scaled = np.loadtxt("spatial_coherence/{}/{}_scaled.sc".format(star,star)) [:,1]

# read in not scaled data for Nunki 2023 and baselines
baselines    = np.loadtxt("spatial_coherence/{}/{}_sc_data.txt".format(star,star)) [:,0]
dbaselines   = np.loadtxt("spatial_coherence/{}/{}_sc_data.txt".format(star,star)) [:,1]
ints_fixedA  = np.loadtxt("spatial_coherence/{}/{}_sc_data.txt".format(star,star)) [:,2]
dints_fixedA = np.loadtxt("spatial_coherence/{}/{}_sc_data.txt".format(star,star)) [:,3]

# read in amplitude and error
amp_A = np.loadtxt("spatial_coherence/{}/amplitudes_odr.sc".format(star)) [0]
damp_A = np.loadtxt("spatial_coherence/{}/amplitudes_odr.sc".format(star)) [1]
'''

##############################################
### wavelength dependent plots & scaled ######
##############################################
plt.figure("Nunki1", figsize=(5,4))
# spatial coherence
for i in range (0,len(afs.baselinesA)):
    plt.errorbar(afs.baselinesA[i], afs.ints_fixedA_scaled[i], yerr=afs.dints_fixedA_scaled[i], xerr=afs.dbaselinesA[i], marker="o", linestyle="", color=uti.color_chA)
for i in range(0,len(baselines_old)):    
    plt.errorbar(baselines_old[i], ints_fixedA_old_scaled[i], yerr=dints_fixedA_old_scaled[i], xerr=dbaselines_old[i], marker="o", linestyle="", color="blue")
plt.plot(xplot, uti.spatial_coherence(xplot,1, afs.odrA[0][1], lam_new),   label="2023 470 nm", color=uti.color_chA, linewidth=2)
plt.plot(xplot, uti.spatial_coherence(xplot,1, float(ang_A_old), lam_old),   label="2022 465 nm", color="blue", linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline (m)")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("images/{}/{}_sc_scaled.pdf".format(star,star))
plt.savefig("images/{}/{}_sc_scaled.png".format(star,star))
#plt.show()



##############################################
### wavelength independent plots & scaled ####
##############################################
plt.figure("Nunki2", figsize=(5,4))
# make x-axis wavelength indepedent 
xplot_new = np.zeros(len(xplot))
for i in range(0,len(xplot)):
    xplot_new[i] = ( xplot[i]/(lam_new) )
xplot_old = np.zeros(len(xplot))
for i in range(0,len(xplot)):
    xplot_old[i] = ( xplot[i]/(lam_old) )

# spatial coherence
for i in range (0,len(afs.baselinesA)):
    plt.errorbar(afs.baselinesA[i]/(lam_new), afs.ints_fixedA_scaled[i], yerr=afs.dints_fixedA_scaled[i], xerr=afs.dbaselinesA[i]/(lam_new), marker="o", linestyle="", color=uti.color_chA)
for i in range(0,len(baselines_old)):
    plt.errorbar(baselines_old[i]/(lam_old), ints_fixedA_old_scaled[i], yerr=dints_fixedA_old_scaled[i], xerr=dbaselines_old[i]/(lam_old), marker="o", linestyle="", color="blue")
plt.plot(xplot_new, uti.spatial_coherence(xplot,1, afs.odrA[0][1], lam_new),    label="2023 470 nm", color=uti.color_chA, linewidth=2)
plt.plot(xplot_old, uti.spatial_coherence(xplot,1,float(ang_A_old), lam_old), label="2022 465 nm", color="blue",  linewidth=2)

plt.title("{}".format(star))
plt.xlabel("Projected baseline/Wavelength")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("images/{}/{}_sc_scaled_lamindependent.pdf".format(star,star))
plt.savefig("images/{}/{}_sc_scaled_lamindependent.png".format(star,star))
plt.show()


'''
##############################################
### wavelength dependent plots not scaled ######
##############################################

# spatial coherence
for i in range (0,len(baselines)):
    plt.errorbar(baselines[i], ints_fixedA[i], yerr=dints_fixedA[i], xerr=dbaselines[i], marker="o", linestyle="", color=uti.color_chA)
for i in range(0, len(baselines_old)):
    plt.errorbar(baselines_old[i], ints_fixedA_old[i], yerr=dints_fixedA_old[i], xerr=dbaselines_old[i], marker="o", linestyle="", color=uti.color_chB)
plt.plot(xplot, uti.spatial_coherence(xplot,float(amp_A), float(ang_A), lam_new),   label="2023 470 nm", color="green", linewidth=2)
plt.plot(xplot, uti.spatial_coherence(xplot,float(amp_A_old),float(ang_A_old), lam_old), label="2022 465 nm", color="blue",  linewidth=2)
plt.errorbar(xplot[0], uti.spatial_coherence(xplot[0],float(amp_A), float(ang_A), lam_new),  yerr=damp_A, marker='x', color='green' )

plt.title("{}".format(star))
plt.xlabel("Projected baseline (m)")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("images/{}/{}_sc_unscaled_lamdependent.pdf".format(star,star))
plt.savefig("images/{}/{}_sc_unscaled_lamdependent.png".format(star,star))
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
plt.errorbar(xplot_new[0], uti.spatial_coherence(xplot[0],float(amp_A), float(ang_A), lam_new),  yerr=damp_A, marker='x', color='green' )

plt.title("{}".format(star))
plt.xlabel("Projected baseline/Wavelength")
plt.ylabel("Spatial coherence")
plt.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.savefig("images/{}/{}_sc_unscaled_lamindependent.pdf".format(star,star))
plt.savefig("images/{}/{}_sc_unscaled_lamindependent.png".format(star,star))
plt.show()

'''