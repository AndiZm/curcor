from scipy.ndimage import gaussian_filter1d
import numpy as np
from scipy.optimize import curve_fit

def gauss_filter(data):
	w = 128
	datagaus=gaussian_filter1d(data,w)
	data_i=data/datagaus
	return data

def pattern_correction(data):
	corrector=np.zeros(8)
	for i in range(0,8000):     # calculate 8 bin correction pattern, did 32 bin pattern here, enough data
	    corrector[i%8]+=data[i]*1./1000.
	#corrector=corrector/np.mean(corrector)

	datacor=[]
	for i in range(len(data)):  # apply 8 bin correction
	    datacor.append(data[i]/corrector[i%8])
	datacor=np.array(datacor)
	return datacor


def gauss(x,a,m,s,d):
	return a * np.exp(-(x-m)**2/2/s/s)+d
def gauss_fit_filter(data):
	xdata = np.arange(0,len(data),1)
	popt, pcov = curve_fit(gauss, xdata, data)
	datacor = []
	for i in range (0,len(data)):
		datacor.append(data[i]/gauss(xdata[i], *popt))
	return datacor