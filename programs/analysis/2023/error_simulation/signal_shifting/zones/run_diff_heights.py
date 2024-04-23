import numpy as np
import matplotlib.pyplot as plt

import utilities as uti
import corrections as cor


# Hard coded sigma (change later)
sigma = 4.325852372387855027e+00


#################################################
# READ DATA AND EXTRACT PEAK AND NOISE TEMPLATE #
#################################################
# read in data
data = np.loadtxt("../../../g2_functions/Mimosa/34/chA.g2")

# Time axis in ns
x = np.arange(-1.6*len(data[0])//2, +1.6*len(data[0])//2, 1.6)


def single_zone_analysis(g2, center, amp_0, mu_0, ax_plot, plot):

	s = center-50; e = center+50
	# Extract the g2 zone
	x_zone = x[(x>s) & (x<e)]
	y_zone = g2[(x>s) & (x<e)]
	xplot = np.arange(s, e, 0.01)

	#if plot == True:
	#	ax_plot.plot(x_zone, y_zone, linestyle="--", color="black", label="noise")
	#	ax_plot.plot(xplot, uti.gauss(xplot, amp_0, mu_0+center, sigma, 1), linestyle="-", color="grey", alpha=1, label="peak template")
	#	ax_plot.set_xlim(x_zone[0],x_zone[-1])
	# Add the peak
	for i in range (0, len(y_zone)):
		y_zone[i] += uti.gauss(x_zone[i], amp_0, mu_0+center, sigma, 0)
	# Re-fit
	xplotf, popt, perr = uti.fit_fixed(y_zone, x_zone, s, e, sigma, mu_start=center-2)
	Int, dInt = uti.integral_fixed(popt, perr, sigma)

	#if plot == True:
	#	ax_plot.plot(x_zone, y_zone, "o", color="#21d6eb", markersize=4, label="resulting g2")
	#	ax_plot.plot(xplotf, uti.gauss(xplotf, popt[0], popt[1], sigma, popt[2]), color="blue", label="Refitted", alpha=0.8)
	#	
	return Int


def error_analysis(g2, scaler=1):

	# Apply initial fit
	xplotf, popt_orig, perr_orig = uti.fit_fixed(g2, x, -50, 50, sigma, mu_start=0)
	popt_orig[0] *= scaler

	amp_0 = popt_orig[0]
	mu_0  = popt_orig[1]
	Int_orig, dInt_orig = uti.integral_fixed(popt_orig, perr_orig, sigma)

	#plt.figure(figsize=(10,6))
	#plt.plot (x, g2, "o--", label="data")
	#plt.plot(xplotf, uti.gauss(xplotf, popt_orig[0], popt_orig[1], sigma, popt_orig[2]), label="fit")
	#plt.xlim(-150,150)
	#plt.xlabel("Time difference (ns)")
	#plt.ylabel("$g^{(2)}$")
	#plt.legend()
	#plt.ticklabel_format(useOffset=False)
	##plt.savefig("img/peak_extraction.png")
	#plt.show()

	# Now add it onto consecutive g2 sections
	ints = []
	#fig, axs = plt.subplots(1,5, sharey="all", figsize=(15,5))	
	#plt.subplots_adjust(wspace=0.05, hspace=0)
	#fig.supxlabel("Time difference (ns)")
	#fig.supylabel("$g^{(2)}$")
	#plt.tight_layout()
	
	# Positive range
	for j in range (1,80):		
		center = j*100
		if j<=5:
			plot = True
			#ax_plot = axs[j-1]
		else:
			plot = False
			#ax_plot = axs[0]
		#ints.append(1e6*single_zone_analysis(g2, center, amp_0, mu_0, ax_plot, plot))
		ints.append(1e6*single_zone_analysis(g2, center, amp_0, mu_0, ax_plot=None, plot=False))
		
	## Negative range
	for j in range (1,80):	
		center = -j*100
		ints.append(1e6*single_zone_analysis(g2, center, amp_0, mu_0, ax_plot=None, plot=False))

	#axs[0].legend()
	#plt.savefig("img/samples.png")
	#plt.show()

	rms_error = np.std(ints)
	print (f"Reconstruction uncertainty: {rms_error:.2f} fs")
	
	#plt.figure(figsize=(10,6))
	#plt.subplot(211)
	#plt.plot(ints, "o--", color="blue", label="reconstructed integrals", alpha=0.5)
	#plt.axhline(y=1e6*Int_orig, linestyle="--", color="red", label="template integral")
	#plt.ylabel("Spatial coherence (fs)")
	#plt.legend()

	#plt.subplot(212)
	#plt.hist(ints, color="blue", alpha=0.5)
	#plt.xlabel("Spatial coherence (fs)")
	#plt.axvline(x=1e6*Int_orig,  color="red",  linestyle="--")
	#plt.axvline(x=np.mean(ints), color="blue", linestyle="--")
	##plt.savefig("img/reconstructed_integrals.png")

	# Correlation tests
	#plt.figure()
	#plt.axhline(y=np.mean(ints), linestyle="--", color="grey")
	#plt.axvline(x=np.mean(ints), linestyle="--", color="grey")
	#for i in range (1,len(ints)):
	#	plt.plot(ints[i-1],ints[i], "o", color="blue")
	#plt.xlabel("Previous integral (fs)")
	#plt.ylabel("Successive integral (fs)")
	##plt.savefig("img/correlation_test.png")	
	##plt.show()

	return rms_error



g2 = data[7]
freqA = [45,95,110,145,155,175,195]
for j in range(len(freqA)):
	g2 = cor.notch(g2, freqA[j]*1e6, 80)
uncertainties = []
scalers = np.arange(0.01,1,0.001)
for scaler in scalers:
	uncertainties.append(error_analysis(g2, scaler))

plt.figure(figsize=(10,6))
plt.plot(scalers, uncertainties, "o--")
plt.xlabel("relative signal height")
plt.ylabel("Uncertainty (fs)")
plt.tight_layout()
plt.show()