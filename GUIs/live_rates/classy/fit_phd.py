import sys
from tqdm import tqdm
from multiprocessing import Process, Value, Array
import scipy.signal as ss
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

import globals as gl

def gauss(x,a,m,s):
	return a * np.exp(-(x-m)**2/2/s/s)

def phd(mean, sigma):
    sigma = np.abs(sigma)
    # Rateloss calculation: Go from 5 sigma left of maximum to 5 sigma right of maximum and check whether events are in the
    # "forbidden area", which corresponds to positive peak heights w.r.t. the offset
    border_left  = int(mean - 5*sigma)
    border_right = int(mean + 5*sigma)
    
    x_sample = np.arange(border_left,border_right,0.1)
    x_in  = np.arange(border_left,0,0.1)
    x_out = np.arange(0,border_right,0.1)
    sum_tot = 0; sum_sz = 0; sum_xy = 0
    for i in x_sample:
        x = i; y = gauss(i, 1,mean,sigma)
        sum_tot += y
        if i < 0:
            sum_sz += y
            sum_xy += x*y
    keep = sum_sz/sum_tot; loss = 1-keep; avg = sum_xy/sum_sz

    return avg

def execute(file, nchn, packet_length, npackets, range_a, range_b, tel_number):
    packets = np.arange(0, npackets)
    peak_height_a = []; peak_height_b = []

    # Read the data and find the peaks in the waveforms
    if nchn == 2:
        with open(file, 'rb') as f:
            for allpkt in tqdm(packets):
                # Read data and split for the channels
                buf = (f.read(2*packet_length))
                packet = np.frombuffer(buf, dtype=np.int8)
                packet = packet.reshape(packet_length, 2)
                a_np = np.array(packet[:,0]).flatten(); b_np = np.array(packet[:,1]).flatten()
                # Find the peaks in the waveforms and fill to arrays
                dings_a, _ = ss.find_peaks(-a_np); dings_b, _ = ss.find_peaks(-b_np)
                for i in dings_a:
                    peak_height_a.append(a_np[i])
                for i in dings_b:
                    peak_height_b.append(b_np[i])
                del(a_np); del(b_np)
                # Give the operator the chance to cancel the calibration
                if gl.stop_calib_thread[tel_number] == True:
                    break
    else:
        with open(file, 'rb') as f:
            for allpkt in tqdm(packets):
                # Read the data
                buf = (f.read(packet_length))
                packet = np.frombuffer(buf, dtype=np.int8)
                a_np = np.array(packet).flatten()
                # Find the peaks in the waveform and fill to array
                dings_a, _ = ss.find_peaks(-a_np)
                for i in dings_a:
                    peak_height_a.append(a_np[i])
                del(a_np)
                # Give the operator the chance to cancel the calibration
                if gl.stop_calib_thread[tel_number] == True:
                    break
    
    # Do the histogram and fit
    binsx = np.arange(-128,128,1)
    data_a = np.histogram(peak_height_a, binsx)

    histo_x = data_a[1][:-1]; histo_a = data_a[0]
    if nchn == 2:
        data_b = np.histogram(peak_height_b, binsx)
        b_x = data_b[1][:-1]; histo_b = data_b[0]
    else:
        histo_b = None; pb = [0,0,0] # In case only one channel is activated, this will be returned
    # Fit the gaussian to the data
    pa, pb, ph_a, ph_b, xplot = fitDistribution(range_a, range_b, histo_x, histo_a, histo_b, nchn)

    return histo_x, histo_a, histo_b, pa, pb, ph_a, ph_b, xplot

# Apply new fit range to data
def fitDistribution(range_a,range_b, histo_x, histo_a, histo_b, nchn):

    xfit_a = histo_x[(histo_x>range_a[0]) & (histo_x<range_a[1])]; ayfit = histo_a[(histo_x>range_a[0]) & (histo_x<range_a[1])]
    pa,ca = curve_fit(gauss, xfit_a, ayfit, p0=[ayfit[int(len(xfit_a)/2)],-15,5])
    # Get the average photon height
    ph_a = phd(pa[1],pa[2])

    
    if nchn == 2:
        xfit_b = histo_x[(histo_x>range_b[0]) & (histo_x<range_b[1])]; byfit = histo_b[(histo_x>range_b[0]) & (histo_x<range_b[1])]
        pb,cb = curve_fit(gauss, xfit_b, byfit, p0=[byfit[int(len(xfit_b)/2)],-15,5])
        ph_b = phd(pb[1],pb[2]) # Average height
    else:
        histo_b = None; pb = [0,0,0] # In case only one channel is activated, this will be returned
        ph_b = []

    xplot = np.arange(-128,0,0.1)

    return pa, pb, ph_a, ph_b, xplot