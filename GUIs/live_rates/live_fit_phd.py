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
    # Rateloss calculation  
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

def execute(packet_length, npackets, range_a, range_b):

    file = gl.calibFile
    packets = np.arange(0, npackets)
    peak_height_a = []; peak_height_b = []

    if gl.o_nchn == 2:
        with open(file, 'rb') as f:
            for allpkt in tqdm(packets):
                buf = (f.read(2*packet_length))
                packet = np.frombuffer(buf, dtype=np.int8)
                packet = packet.reshape(packet_length, 2)
                a_np = np.array(packet[:,0]).flatten(); b_np = np.array(packet[:,1]).flatten()
                dings_a, _ = ss.find_peaks(-a_np); dings_b, _ = ss.find_peaks(-b_np)
                for i in dings_a:
                    peak_height_a.append(a_np[i])
                for i in dings_b:
                    peak_height_b.append(b_np[i])
                del(a_np); del(b_np)
                if gl.stop_calib_thread == True:
                    break
    else:
        with open(file, 'rb') as f:
            for allpkt in tqdm(packets):
                buf = (f.read(packet_length))
                packet = np.frombuffer(buf, dtype=np.int8)
                a_np = np.array(packet).flatten()
                dings_a, _ = ss.find_peaks(-a_np)
                for i in dings_a:
                    peak_height_a.append(a_np[i])
                del(a_np)
                if gl.stop_calib_thread == True:
                    break
    
    # Do the histogram and fit
    binsx = np.arange(-128,128,1)
    data_a = np.histogram(peak_height_a, binsx)
    gl.histo_x = data_a[1][:-1]; gl.histo_a = data_a[0]
    xfit_a = gl.histo_x[(gl.histo_x>range_a[0]) & (gl.histo_x<range_a[1])]; ayfit = gl.histo_a[(gl.histo_x>range_a[0]) & (gl.histo_x<range_a[1])]
    gl.pa,ca = curve_fit(gauss, xfit_a, ayfit, p0=[ayfit[int(len(xfit_a)/2)],-15,5])
    gl.ph_a = phd(gl.pa[1],gl.pa[2]) # Average height

    if gl.o_nchn == 2:
        data_b = np.histogram(peak_height_b, binsx)
        b_x = data_b[1][:-1]; gl.histo_b = data_b[0]
        xfit_b = gl.histo_x[(gl.histo_x>range_b[0]) & (gl.histo_x<range_b[1])]; byfit = gl.histo_b[(gl.histo_x>range_b[0]) & (gl.histo_x<range_b[1])]
        gl.pb,cb = curve_fit(gauss, xfit_b, byfit, p0=[byfit[int(len(xfit_b)/2)],-15,5])
        gl.ph_b = phd(gl.pb[1],gl.pb[2]) # Average height
    gl.xplot = np.arange(-128,0,0.1)
def execute2(packet_length, npackets, range_a, range_b):

    file = gl.calibFile2
    packets = np.arange(0, npackets)
    peak_height_a = []; peak_height_b = []

    if gl.o_nchn2 == 2:
        with open(file, 'rb') as f:
            for allpkt in tqdm(packets):
                buf = (f.read(2*packet_length))
                packet = np.frombuffer(buf, dtype=np.int8)
                packet = packet.reshape(packet_length, 2)
                a_np = np.array(packet[:,0]).flatten(); b_np = np.array(packet[:,1]).flatten()
                dings_a, _ = ss.find_peaks(-a_np); dings_b, _ = ss.find_peaks(-b_np)
                for i in dings_a:
                    peak_height_a.append(a_np[i])
                for i in dings_b:
                    peak_height_b.append(b_np[i])
                del(a_np); del(b_np)
                if gl.stop_calib_thread2 == True:
                    break
    else:
        with open(file, 'rb') as f:
            for allpkt in tqdm(packets):
                buf = (f.read(packet_length))
                packet = np.frombuffer(buf, dtype=np.int8)
                a_np = np.array(packet).flatten()
                dings_a, _ = ss.find_peaks(-a_np)
                for i in dings_a:
                    peak_height_a.append(a_np[i])
                del(a_np)
                if gl.stop_calib_thread2 == True:
                    break
    
    # Do the histogram and fit
    binsx = np.arange(-128,128,1)
    data_a = np.histogram(peak_height_a, binsx)
    gl.histo_x2 = data_a[1][:-1]; gl.histo_a2 = data_a[0]
    xfit_a = gl.histo_x2[(gl.histo_x2>range_a[0]) & (gl.histo_x2<range_a[1])]; ayfit = gl.histo_a2[(gl.histo_x2>range_a[0]) & (gl.histo_x2<range_a[1])]
    gl.pa2,ca = curve_fit(gauss, xfit_a, ayfit, p0=[ayfit[int(len(xfit_a)/2)],-15,5])
    gl.ph_a2 = phd(gl.pa2[1],gl.pa2[2]) # Average height

    if gl.o_nchn2 == 2:
        data_b = np.histogram(peak_height_b, binsx)
        b_x = data_b[1][:-1]; gl.histo_b2 = data_b[0]
        xfit_b = gl.histo_x2[(gl.histo_x2>range_b[0]) & (gl.histo_x2<range_b[1])]
        byfit = gl.histo_b2[(gl.histo_x2>range_b[0]) & (gl.histo_x2<range_b[1])]
        gl.pb2,cb = curve_fit(gauss, xfit_b, byfit, p0=[byfit[int(len(xfit_b)/2)],-15,5])
        gl.ph_b2 = phd(gl.pb2[1],gl.pb2[2]) # Average height
    gl.xplot2 = np.arange(-128,0,0.1)

# Only apply new fit range to data
def onlyFit(range_a,range_b):
    #Fits
    xfit_a = gl.histo_x[(gl.histo_x>range_a[0]) & (gl.histo_x<range_a[1])]; ayfit = gl.histo_a[(gl.histo_x>range_a[0]) & (gl.histo_x<range_a[1])]
    gl.pa,ca = curve_fit(gauss, xfit_a, ayfit, p0=[ayfit[int(len(xfit_a)/2)],-15,5])
    gl.ph_a = phd(gl.pa[1],gl.pa[2]) # Average height
    if gl.o_nchn == 2:
        xfit_b = gl.histo_x[(gl.histo_x>range_b[0]) & (gl.histo_x<range_b[1])]; byfit = gl.histo_b[(gl.histo_x>range_b[0]) & (gl.histo_x<range_b[1])]
        gl.pb,cb = curve_fit(gauss, xfit_b, byfit, p0=[byfit[int(len(xfit_b)/2)],-15,5])
        gl.ph_b = phd(gl.pb[1],gl.pb[2]) # Average height
    gl.xplot = np.arange(-128,0,0.1)
def onlyFit2(range_a,range_b):
    #Fits
    xfit_a = gl.histo_x2[(gl.histo_x2>range_a[0]) & (gl.histo_x2<range_a[1])]; ayfit = gl.histo_a2[(gl.histo_x2>range_a[0]) & (gl.histo_x2<range_a[1])]
    gl.pa2,ca = curve_fit(gauss, xfit_a, ayfit, p0=[ayfit[int(len(xfit_a)/2)],-15,5])
    gl.ph_a2 = phd(gl.pa2[1],gl.pa2[2]) # Average height
    if gl.o_nchn2 == 2:
        xfit_b = gl.histo_x2[(gl.histo_x2>range_b[0]) & (gl.histo_x2<range_b[1])]; byfit = gl.histo_b2[(gl.histo_x2>range_b[0]) & (gl.histo_x2<range_b[1])]
        gl.pb2,cb = curve_fit(gauss, xfit_b, byfit, p0=[byfit[int(len(xfit_b)/2)],-15,5])
        gl.ph_b2 = phd(gl.pb2[1],gl.pb2[2]) # Average height
    gl.xplot2 = np.arange(-128,0,0.1)