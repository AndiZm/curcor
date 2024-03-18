import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from tqdm import tqdm


def gauss(x, amp, mu, sigma):
    return amp * np.exp(-(x-mu)**2/(2*sigma**2)) + 1
def fit(data, x, s, e, mu_start=-2):
	#plt.plot(x,data); plt.show()
	#print (s,e)

	xfit = x[(x>s) & (x<e)]
	yfit = data[(x>s) & (x<e)]
	
	xplot = np.arange(s, e, 0.01)
	popt, cov = curve_fit(gauss, xfit, yfit, p0=[1e-6,mu_start,3])
	perr = np.sqrt(np.diag(cov))
	return xplot, popt, perr



#################################################
# READ DATA AND EXTRACT PEAK AND NOISE TEMPLATE #
#################################################
# read in data
data = np.loadtxt("../../g2_functions/Mimosa/14/g2_allA.txt")
x       = data[:,0]
g2_orig = data[:,1]

# define the signal as gaussian function
xplot, popt, perr = fit(data=g2_orig, x=x, s=-50, e=50, mu_start=0)
amp_orig  = popt[0]
mean_orig = popt[1]
sig_orig  = popt[2]

# define noise template as measurement - model peak
noise = []
for i in range (0,len(g2_orig)):
	noise.append(g2_orig[i] - gauss(x[i], *popt) + 1)

plt.figure(figsize=(10,6))
plt.plot(x, g2_orig, label="Measurement data", linewidth=2)
plt.plot(xplot, gauss(xplot, *popt), label="extracted model peak")
plt.plot(x, noise, linestyle="--", color="cyan", label="noise template", alpha=0.5)

plt.xlim(-200,200)
plt.xlabel("Time difference (ns)")
plt.ylabel("$g^{(2)}$")
plt.legend()
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
means  = []
dmeans = []
for i in tqdm( range (-100,100) ):
	shift = i
	g2 = generate_g2(shift=shift)
	xplot, popt, perr = fit(data=g2, x=x, s=-50+shift, e=50+shift, mu_start=shift)
	amp  = popt[0]; damp  = perr[0]
	mean = popt[1]; dmean = perr[1]
	sig  = popt[2]; dsig  = perr[2]

	shifts.append(shift)
	means.append(mean-shift)
	dmeans.append(dmean)

	#if i%10 == 0:
	if i == 26:
		plt.plot(x, noise, color="grey")
		plt.plot(xplot, gauss(xplot, amp_orig, shift, sig_orig), color="orange")
		plt.axvline(x=shift, color="orange")

		plt.plot(x, g2, color="blue")
		plt.plot(xplot, gauss(xplot, *popt), color="black", linestyle="--")
		plt.axvline(x=popt[1], color="black", linestyle="--")


plt.show()



plt.figure(figsize=(10,6))

plt.errorbar(x=shifts, y=means, yerr=dmeans, marker="o", linestyle="", color="blue", label="True - reconstructed shift")
plt.axhline(y=0, color="grey", linestyle="--")
plt.xlabel("Peak shift (ns)")
plt.ylabel("Reconstructed - true   (ns)")
plt.tick_params(axis="y", colors="blue")
plt.ylim(-1, 1)
plt.legend(loc="upper left")

plt.twinx()
plt.plot(x, np.array(noise)-1, color="red", alpha=1, label="noise template")
plt.xlabel("Time difference (ns)")
plt.tick_params(axis="y", colors="red")
plt.ylabel("$g^{(2)}$")
plt.xlim(-100,100)
plt.ylim(-1e-7, 1e-7)
plt.legend(loc="upper right")

plt.show()