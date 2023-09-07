import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

distribution = np.random.normal(loc=0.0, scale=1.0, size=1000000)

# Histogram
binsx = np.arange(-5,5,0.1)
xplot = np.arange(-5,5,0.01)

histo = np.histogram(distribution, bins=binsx)
histo_x = histo[1][:-1]; histo_y = histo[0]


histo_y_err = np.sqrt(histo_y)
histo_y_err[histo_y_err==0]= 1

# Fit gauss
def gauss(x,a,m,s):
    return a * np.exp( -(x-m)**2/2/s/s )


popt, pcov = curve_fit(gauss,
                        histo_x,
                        histo_y,
                        p0=[10,0.2,2.5],
                        sigma=histo_y_err,
                        absolute_sigma=True
)

perr = np.sqrt(np.diag(pcov))

print (popt)
print (perr)

plt.errorbar(histo_x, histo_y, yerr=np.sqrt(histo_y))
plt.plot(xplot, gauss(xplot, *popt))
plt.show()