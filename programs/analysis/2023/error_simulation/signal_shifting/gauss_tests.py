import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def gauss(x, amp, mean, sig):
	return amp * np.exp( -(x-mean)**2/2/sig/sig )
def gauss_fixed(x, sig):
	return 1 * np.exp( -x**2/2/sig/sig )

x = np.arange(-20,20,1)

sig_big = 3
sig_small = 7


x_sum = np.arange(-30,30,0.1)
dist_sum = np.zeros(len(x_sum))


plt.plot(x, gauss(x, 1, 0, sig_big), "o--")

for i in x:
	xplot = np.arange(i-20,i+20,0.1)

	amp  = gauss(i, 1, 0, sig_big)
	mean = i
	sig  = sig_small

	plt.plot(xplot, gauss(xplot, amp,mean,sig), color="orange")

	single = gauss(x_sum, amp, mean, sig)
	dist_sum += 1./len(x) * single

dist_sum /= np.max(dist_sum)

# fit gauss
popt, pcov = curve_fit( gauss_fixed, x_sum,dist_sum, p0=[sig_big] )
perr = np.sqrt(np.diag(pcov))
print (f"Fitted width: {popt[0]:.2f} +/- {perr[0]:.2f}")

plt.plot(x_sum, dist_sum, color="red")
plt.plot(x_sum, gauss_fixed(x_sum, *popt), color="black", linestyle="--")
plt.show()