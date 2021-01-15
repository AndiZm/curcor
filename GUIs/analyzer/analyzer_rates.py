import sys
import time as t
from tqdm import tqdm
from multiprocessing import Process, Value, Array
import scipy.signal as ss
import numpy as np
import pyopencl as cl
import matplotlib.pyplot as plt


packet_length = int(1e6)

def execute(file, fracEval, threshold, threshold_toggle):

    numLen = 123
    headerfile = file[:-4] + "_binheader.txt"
    headerstring = [line.rstrip('\n') for line in open(headerfile)]
    numChan = int (headerstring[2][-1:])
    substr = headerstring[37].split("=")
    for i in range (0, len(headerstring)):
        substr = headerstring[i].split("=")
        if substr[0] == "LenL ":
            #print (headerstring[i])
            numLen = int(substr[1])
    #numLen = int(substr[1])
    if numLen == 0:
        numLen = 4e9

    npackets = int(np.floor(fracEval*numLen/packet_length))
    print ("npackets = " + str(npackets))
    packets = np.arange(0, npackets)
    counts_a = 0
    counts_b = 0
    peak_height_a = []
    peak_height_b = []
    binsx = np.arange(-128,127,1) # For histogram
    
    # Channel number = 1
    #----------------------------------------------------------#
    if numChan == 1:
        with open(file, 'rb') as f:
            for allpkt in tqdm(packets):
                buf = (f.read(packet_length))
                packet = np.frombuffer(buf, dtype=np.int8)
                a_np = np.array(packet).flatten()
                if threshold_toggle == 1:
                    a_np[a_np < threshold] = 0
                if threshold_toggle == -1:
                    a_np[a_np > threshold] = 0
                dings_a, _ = ss.find_peaks(-a_np)
                counts_a += len(dings_a)
                for i in dings_a:
                    peak_height_a.append(a_np[i])
                del(a_np)
        r_a = counts_a*1e-6/(800e-12*packet_length*npackets)
        r_b = 0   
        #print('------------------------')
        #print('Rate A:\t\t\t{:.2f} MHz\n'.format(r_a))    
        data_a = np.histogram(peak_height_a, binsx)
        data_b = data_a
        #plt.hist(peak_height_a, bins=binsx)
    #----------------------------------------------------------#
    
    
    # Channel number = 2
    #----------------------------------------------------------#
    if numChan == 2:    
        with open(file, 'rb') as f:
            for allpkt in tqdm(packets):
                buf = (f.read(2*packet_length))
                packet = np.frombuffer(buf, dtype=np.int8)
                packet = packet.reshape(packet_length, 2)
                a_np = np.array(packet[:,0]).flatten()
                b_np = np.array(packet[:,1]).flatten()
                if threshold_toggle == 1:
                    a_np[a_np < threshold] = 0 
                    b_np[b_np < threshold] = 0
                    dings_a, _ = ss.find_peaks(+a_np)
                    dings_b, _ = ss.find_peaks(+b_np)
                if threshold_toggle == -1:
                    a_np[a_np > threshold] = 0 
                    b_np[b_np > threshold] = 0
                    dings_a, _ = ss.find_peaks(-a_np)
                    dings_b, _ = ss.find_peaks(-b_np)                
                counts_a += len(dings_a)
                counts_b += len(dings_b)
                for i in dings_a:
                    peak_height_a.append(a_np[i])
                for i in dings_b:
                    peak_height_b.append(b_np[i])
                del(a_np)
                del(b_np)
        r_a = counts_a*1e-6/(800e-12*packet_length*npackets)
        r_b = counts_b*1e-6/(800e-12*packet_length*npackets)    
        #print('------------------------')
        #print('Rate A:\t\t\t{:.2f} MHz\nRate B:\t\t\t{:.2f} MHz'.format(r_a, r_b))
        
        data_a = np.histogram(peak_height_a, binsx)
        data_b = np.histogram(peak_height_b, binsx)
     #----------------------------------------------------------#

    hist_x_old = data_a[1]
    hist_x = hist_x_old[:-1]
    hist_a = data_a[0]; hist_b = data_b[0]
        
    return numChan, r_a, r_b, hist_x, hist_a, hist_b
    

