import numpy as np
import matplotlib.pyplot as plt
import time
import cupy
import sys
from threading import Thread
import scipy.fftpack as scf

import os
import time
from tqdm import tqdm

from optparse import OptionParser

path = "C:/Users/ii/Desktop/GITrepo/curcor/programs/analysis/rates/"
file = "K:/20220419_HESS/off.bin"

data = np.fromfile(file,dtype=np.int8)

data = data.reshape(int(len(data)/2),2)
dataA = data[:,0] 
dataB = data[:,1]

print(len(dataA))

mean_all = np.mean(dataA)

x = np.arange(0, len(dataA)+1, 1000000)
print(len(x))
meanA = np.zeros(len(x)-1)
meanB = np.zeros(len(x)-1)

for i in tqdm(range(0, 1)): #len(x)-1)): 
    start = x[i]
    end = x[i+1]
    # Calculate means
    meanA[i] = np.mean(dataA[start:end])
    meanB[i] = np.mean(dataB[start:end])
    offA = dataA[start:end]
    offB = dataB[start:end]

    # x Achse erstellen und fft 
    N = len(offA)
    stepsize = 1.6e-3 # 1.6ns pro bin
    xx = np.linspace(0, stepsize*N, N)
    x_fft = np.linspace(0, 1/(2*stepsize),N//2)
    y_fftA = np.abs(np.fft.fft(offA)/(N/2))
    y_fftB = np.abs(np.fft.fft(offB)/(N/2))

    plt.plot(x_fft, y_fftA[0:N//2], label="ChA")
    plt.plot(x_fft, y_fftB[0:N//2], label="ChB")
    plt.title("FFT von off Datei 19.4.")
    plt.xlabel("MHz")
    plt.ylim([0,0.08])
    plt.legend()
    plt.savefig("tests/off_19_4.png")
    plt.show()






#np.savetxt(path + "mean_bins_{}.txt".format(run), np.c_[meanA, meanB])





