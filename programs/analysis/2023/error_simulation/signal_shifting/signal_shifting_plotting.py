import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from tqdm import tqdm
from scipy.interpolate import interp1d


def gauss(x, amp, mu, sigma):
    return amp * np.exp(-(x-mu)**2/(2*sigma**2)) + 1
def fit(data, x, s, e, mu_start=-2):
	#plt.plot(x,data); plt.show()
	#print (s,e)

	xfit = x[(x>s) & (x<e)]
	yfit = data[(x>s) & (x<e)]
	
	xplot = np.arange(s, e, 0.01)
	popt, cov = curve_fit(gauss, xfit, yfit, p0=[5e-7,mu_start,5])
	perr = np.sqrt(np.diag(cov))
	return xplot, popt, perr
def integral(fitpar, fitpar_err):
    a = fitpar[0]; d_a = fitpar_err[0]
    s = np.abs(fitpar[2]); d_s = fitpar_err[2]
    Int = a*s*np.sqrt(2*np.pi)
    dInt = np.sqrt(2*np.pi)*np.sqrt((a*d_s)**2 + (s*d_a)**2)
    return Int, dInt


#################################################
# READ DATA AND EXTRACT PEAK AND NOISE TEMPLATE #
#################################################
# read in data
data = np.loadtxt("../../g2_functions/Mimosa/34/g2_allA.txt")
x       = data[:,0]
g2_orig = data[:,1]

# define the signal as gaussian function
xplot, popt, perr = fit(data=g2_orig, x=x, s=-50, e=50, mu_start=0)
amp_orig  = popt[0]
mean_orig = popt[1]
sig_orig  = popt[2]
int_orig, dint_orig = integral(popt, perr)

# define noise template as measurement - model peak
noise = []
for i in range (0,len(g2_orig)):
	noise.append(g2_orig[i] - gauss(x[i], *popt) + 1)

# Build noise template interpolation function for correlation analysis
f_noise = interp1d(x, noise)

plt.figure(figsize=(10,6))
plt.plot(x, g2_orig, label="Measurement data", color="grey", linewidth=4)
plt.plot(xplot, gauss(xplot, *popt), label="extracted model peak", color="black")
plt.plot(x, noise, linestyle="--", color="red", label="noise template")

plt.xlim(-200,200)
plt.xlabel("Time difference (ns)")
plt.ylabel("$g^{(2)}$")
plt.legend()
plt.savefig("shift_templates.png")
plt.show()

#########################
# SHIFT THE SIGNAL PEAK #
#########################
def generate_g2(shift):
	g2 = []
	for i in range (0, len(noise)):
		g2.append( noise[i] + gauss(x[i], amp_orig, shift, sig_orig) - 1 )
	return np.array(g2)

shifts = []
means  = []; dmeans = []
sigmas = []; dsigmas = []
ints = []; dints = []
noise_template = []

for i in tqdm( range (-200,200) ):
	shift = i
	g2 = generate_g2(shift=shift)
	xplot, popt, perr = fit(data=g2, x=x, s=-50+shift, e=50+shift, mu_start=shift)
	amp  = popt[0]; damp  = perr[0]
	mean = popt[1]; dmean = perr[1]
	sig  = popt[2]; dsig  = perr[2]
	Int, dInt = integral(popt, perr)

	shifts.append(shift)
	means.append(mean-shift); dmeans.append(dmean)
	sigmas.append(sig-sig_orig); dsigmas.append(dsig)
	ints.append(1e6*(Int-int_orig)); dints.append(1e6*dInt)
	noise_template.append(f_noise(i)-1)

	#if i%20 == 0:
	#plt.plot(x, noise, color="grey")
	#plt.plot(xplot, gauss(xplot, amp_orig, shift, sig_orig), color="orange")
	#plt.axvline(x=shift, color="orange")
#
	#plt.plot(x, g2, color="blue")
	#plt.plot(xplot, gauss(xplot, *popt), color="black", linestyle="--")
	#plt.axvline(x=popt[1], color="black", linestyle="--")
#
	#plt.show()



plt.figure(figsize=(12,6))

plt.errorbar(x=shifts, y=means, yerr=dmeans,   marker="o", linestyle="", color="#002ead", alpha=0.5, label="Mean:     reconstructed - true")
plt.errorbar(x=shifts, y=sigmas, yerr=dsigmas, marker="^", linestyle="", color="#03d7fc", alpha=0.5, label="Sigma:    reconstructed - true")
plt.errorbar(x=shifts, y=ints, yerr=dints,     marker="d", linestyle="", color="#02aab0", alpha=0.5, label="Integral: reconstructed - true ($\cdot 10^6$)")
plt.axhline(y=0, color="grey", linestyle="--")
plt.xlabel("Peak shift (ns)")
plt.ylabel("Reconstructed - true   (ns)")
plt.ylim(-1, 1)
plt.legend(loc="upper left")

plt.twinx()
plt.plot(x, np.array(noise)-1, "o-", markersize=3, color="red", alpha=1, label="noise template")
plt.xlabel("Time difference (ns)")
plt.tick_params(axis="y", colors="red")
plt.ylabel("$g^{(2)}$")
plt.xlim(-100,100)
plt.ylim(-1e-7, 1e-7)
plt.legend(loc="upper right")

plt.tight_layout()

plt.savefig("shift_plot.png")


# Correlation plots
plt.figure(figsize=(10,6))
plt.errorbar(x=noise_template, y=means, yerr=dmeans, color="#002ead",   marker="o", linestyle="", label="Mean")
plt.errorbar(x=noise_template, y=sigmas, yerr=dsigmas, color="#03d7fc", marker="^", linestyle="", label="Sigma")
plt.errorbar(x=noise_template, y=ints, yerr=dints, color="#02aab0",     marker="d", linestyle="", label="Integral")
plt.axhline(y=0, color="grey", linestyle="--")
plt.axvline(x=0, color="grey", linestyle="--")
plt.xlabel("Noise template value")
plt.ylabel("reco - true (ns)")
plt.legend()
plt.tight_layout()
plt.savefig("correlation_plot.png")

plt.show()