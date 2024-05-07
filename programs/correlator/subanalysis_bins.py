import numpy as np
import matplotlib.pyplot as plt
import time
import cupy
import sys
from threading import Thread

import os
import time
from tqdm import tqdm

from optparse import OptionParser

run = 5825
path = "C:/Users/ii/Desktop/GITrepo/curcor/programs/analysis/rates/"
file = "K:/20220419_HESS/shaula_{:05d}.bin".format(run)

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

for i in tqdm(range(0,len(x)-1)): 
    start = x[i]
    end = x[i+1]
    # Calculate means
    meanA[i] = np.mean(dataA[start:end])
    meanB[i] = np.mean(dataB[start:end])
   

np.savetxt(path + "mean_bins_{}.txt".format(run), np.c_[meanA, meanB])

















'''
parser = OptionParser()
parser.add_option("-s", "--start", dest="start")
parser.add_option("-e", "--end",   dest="end")
(options, args) = parser.parse_args()

start = int(options.start)
end   = int(options.end)

# File creation time
def file_time(file1, file2):
    # Check for both file creation times and see whether there is a big difference due to not-synchronized computer clocks or not.
    pc1time = os.path.getctime(file1)
    pc2time = os.path.getctime(file2)
    diff = pc2time - pc1time

    # If the clocks are sufficiently well synchronized, PC1 file creation time is return per default. If not, the mean of both is returned
    if diff < 0.5:
        return pc1time
    else:
        print ("There is a problem with the synchronization of files:")
        print (file1, pc1time)
        print (file2, pc2time)
        print (diff)
        return np.mean([pc1time, pc2time])

##########
## MAIN ##
##########
# Analyzing path
pc1_body = "K:/20220419_HESS/"
pc2_body = "L:/20220419_HESS/"
filepath = "shaula_"


def readfile():
    global pc1_filename, pc2_filename, readfiles, stime, analyzefiles, totalfiles

    this_pc1_filename = pc1_filename
    this_pc2_filename = pc2_filename
    #resultfilename = "../results/20220419_HESS/" + this_pc1_filename.split("/")[-1].split(".")[0] + ".fcorr2"

    data_pc1 = np.fromfile(this_pc1_filename,dtype=np.int8)
    data_pc2 = np.fromfile(this_pc2_filename,dtype=np.int8)
    #endtime = time.time(); dtime = endtime - stime

    data_pc1 = data_pc1.reshape(int(len(data_pc1)/2),2)
    data_pc1A = data_pc1[:,0]; data_pc1B = data_pc1[:,1]

    data_pc2 = data_pc2.reshape(int(len(data_pc2)/2),2)
    data_pc2A = data_pc2[:,0]; data_pc2B = data_pc2[:,1]

    # Calculate means
    mean_pc1A = np.mean(data_pc1A)
    mean_pc1B = np.mean(data_pc1B)
    mean_pc2A = np.mean(data_pc2A)
    mean_pc2B = np.mean(data_pc2B)
    # Get file creation time
    #ctime = file_time(this_pc1_filename, this_pc2_filename)

    readfiles += 1
    #print ("\tReading {} files in {:.2f} seconds : {:.2f} s per file".format(readfiles, dtime, dtime/readfiles))

    iterations=int(len(data_pc2)/length)-1


fileindex = start
while fileindex <= end:

    filesdone=0
    data=[]
    the_filename = ""
    
    readfiles = 0; analyzefiles = 0    
    
    threads = []
    stime = time.time()
    print ("New parallel computing of {} files".format(n_parallel))
    for run in range(fileindex,min(fileindex+n_parallel,end)):
        pc1_filename = pc1_body + filepath + "{:05d}.bin".format(run)
        pc2_filename = pc2_body + filepath + "{:05d}.bin".format(run)
        
        threads.append(Thread(target=readfile, args=()))
        threads[-1].start()

    for i in threads:
        i.join()
    print ("Parallel computing done.\n\n")
    fileindex += n_parallel

endfull = time.time()
fulltime = endfull - startfull
print ("########################################################################")
print ("\tAnalyzing {} files in {:.2f} seconds : {:.2f} s per file".format(totalfiles, fulltime, fulltime/totalfiles))
'''