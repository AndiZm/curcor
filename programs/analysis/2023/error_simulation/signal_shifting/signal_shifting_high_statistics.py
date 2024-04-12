import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from tqdm import tqdm
from scipy.interpolate import interp1d


def gauss(x, amp, mu, sigma):
    return amp * np.exp(-(x-mu)**2/(2*sigma**2)) + 1
def fit(data, x, s, e, mu_start=-2):
	xfit = x[(x>s) & (x<e)]
	yfit = data[(x>s) & (x<e)]	
	xplot = np.arange(s, e, 0.01)
	popt, cov = curve_fit(gauss, xfit, yfit, p0=[1e-6,mu_start,5])
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

# define noise template as measurement - model peak
noise = []
for i in range (0,len(g2_orig)):
	noise.append(g2_orig[i] - gauss(x[i], *popt) + 1)
rms_noise = np.std(noise)

# Build noise template interpolation function for correlation analysis
f_noise = interp1d(x, noise)



# Modify amplitude
popt[0] *= 1.2

amp_orig  = popt[0]
mean_orig = popt[1]
sig_orig  = popt[2]
int_orig, dint_orig = integral(popt, perr)



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

for i in tqdm( range (-7000,7000) ):
	shift = i
	g2 = generate_g2(shift=shift)
	xplot, popt, perr = fit(data=g2, x=x, s=-50+shift, e=50+shift, mu_start=shift)
	amp  = popt[0]; damp  = perr[0]
	mean = popt[1]; dmean = perr[1]
	sig  = popt[2]; dsig  = perr[2]
	Int, dInt = integral(popt, perr)

	if dInt < np.inf:
		shifts.append(shift)
		means.append(mean-shift); dmeans.append(dmean)
		sigmas.append(sig-sig_orig); dsigmas.append(dsig)
		ints.append(1e6*(Int-int_orig)); dints.append(1e6*dInt)
		noise_template.append(f_noise(i)-1)

##############
# Histograms #
##############
plt.figure(figsize=(12,4))

# mean
plt.subplot(131)
histogram = np.histogram(means, bins=20)
histo_mean = histogram[0]; x_mean = histogram[1][:-1]
mean_avg_error = np.nanmean(dmeans)

plt.plot(x_mean, histo_mean, color="#002ead")
plt.errorbar(x=0, y=0.5*np.max(histo_mean), xerr=mean_avg_error, marker="o", color="#002ead")

# sigma
plt.subplot(132)
histogram = np.histogram(sigmas, bins=20)
histo_sigma = histogram[0]; x_sigma = histogram[1][:-1]
sigma_avg_error = np.nanmean(dsigmas)

plt.plot(x_sigma, histo_sigma, color="#03d7fc")
plt.errorbar(x=0, y=0.5*np.max(histo_sigma), xerr=sigma_avg_error, marker="^", color="#03d7fc")

# integral
plt.subplot(133)
histogram = np.histogram(ints, bins=20)
histo_int = histogram[0]; x_int = histogram[1][:-1]
int_avg_error = np.nanmean(dints)

plt.plot(x_int, histo_int, color="#02aab0")
plt.errorbar(x=0, y=0.5*np.max(histo_int), xerr=int_avg_error, marker="d", color="#02aab0")

plt.tight_layout()

# Distribution of integrals
ints_rms = np.std(ints)
print ("Integrals:")
print ("Average single fit error:      {:.2f}".format(int_avg_error))
print ("RMS distribution of integrals: {:.2f}".format(ints_rms))
print ("Uncertainty factor:            {:.2f}".format(ints_rms/int_avg_error))

#####################
# Correlation plots #
#####################
# Linear correlation fit function
def linear(x, m, t):
	return m*x + t

# Fit linear functions to the three observables
popt_mean, cov_mean = curve_fit(linear, noise_template, means,  p0=[1e6,0])
popt_sig , cov_sig  = curve_fit(linear, noise_template, sigmas, p0=[1e6,0])
popt_int,  cov_int  = curve_fit(linear, noise_template, ints,   p0=[1e6,0])
xplot = np.arange(np.min(noise_template),np.max(noise_template), 1e-10)


plt.figure(figsize=(10,6))

plt.errorbar(x=noise_template, y=means, yerr=dmeans, color="#002ead",   marker="o", zorder=2, alpha=0.25, linestyle="", label="Mean")
plt.errorbar(x=noise_template, y=sigmas, yerr=dsigmas, color="#03d7fc", marker="^", zorder=2, alpha=0.25, linestyle="", label="Sigma")
plt.errorbar(x=noise_template, y=ints, yerr=dints, color="#02aab0",     marker="d", zorder=2, alpha=0.25, linestyle="", label="Integral")

plt.plot(xplot, linear(xplot, *popt_mean), color="#002ead", linewidth=2, zorder=0)
plt.plot(xplot, linear(xplot, *popt_sig),  color="#03d7fc", linewidth=2, zorder=0)
plt.plot(xplot, linear(xplot, *popt_int),  color="#02aab0", linewidth=2, zorder=0)

plt.axhline(y=0, color="grey", linestyle="--")
plt.axvline(x=0, color="grey", linestyle="--")
plt.xlabel("Noise template value")
plt.ylabel("reco - true (ns)")
plt.legend()
plt.tight_layout()
plt.savefig("correlation_plot_high_statistics.png")

plt.show()

# Check the distribution of integrals relative to the linear fit
ints_relative = []
for i in range (0,len(ints)):
	ints_relative.append( ints[i] - linear(x=noise_template[i], m=popt_int[0], t=popt_int[1]) )
ints_relative_rms = np.nanstd(ints_relative)
print ("RMS distribution of integrals relative to correlation fit: {:.2f}".format(ints_relative_rms))