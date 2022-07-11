import numpy as np
import matplotlib.pyplot as plt
import time
import cupy
import sys
from threading import Thread

import os
import time

from optparse import OptionParser

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
        print (pc1_file)
        print (pc2_file)
        print (diff)
        return np.mean(pc1time, pc2time)

# Rate calculations
off_1   = -3.603750420000000343e-01
off_2   = 1.352422540000000062e-01
calib_1 = -65.2418293569126
calib_2 = -70.77924338810277
def calculate_rate (filenumber):
    pc1_file = pc1_body + filepath + "{:05d}.bin".format(filenumber)
    pc2_file = pc2_body + filepath + "{:05d}.bin".format(filenumber)

    data_pc1 = np.fromfile(pc1_file,dtype=np.int8)
    data_pc2 = np.fromfile(pc2_file,dtype=np.int8)

    mean_1 = np.mean(data_pc1); mean_2 = np.mean(data_pc2)
    rate_1 = 1e-6 * mean_1/(calib_1 * 1.6e-9)
    rate_2 = 1e-6 * mean_2/(calib_2 * 1.6e-9)

    return rate_1, rate_2

##########
## MAIN ##
##########
# Analyzing path
pc1_body = "G:/20220416_HESS/"
pc2_body = "H:/20220416_HESS/"
filepath = "acrux_combined_"

# Number of parallel file runs
n_parallel = int(5)

startfull=time.time()

corlen=50000
files = 10
length=int(2**22)

acorlen=corlen+1
cor_cu=cupy.zeros((acorlen))

totalfiles = 0
bunchtimes = []

def readfile():
    global pc1_filename, pc2_filename, readfiles, stime, analyzefiles, totalfiles

    this_pc1_filename = pc1_filename
    this_pc2_filename = pc2_filename
    resultfilename = "../results/20220416_HESS/" + this_pc1_filename.split("/")[-1].split(".")[0] + ".fcorr"

    data_pc1 = np.fromfile(this_pc1_filename,dtype=np.int8)
    data_pc2 = np.fromfile(this_pc2_filename,dtype=np.int8)
    endtime = time.time(); dtime = endtime - stime

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
    ctime = file_time(this_pc1_filename, this_pc2_filename)

    readfiles += 1
    print ("\tReading {} files in {:.2f} seconds : {:.2f} s per file".format(readfiles, dtime, dtime/readfiles))

    iterations=int(len(data_pc2)/length)-1
    this_cor1 = cupy.zeros((acorlen))
    this_cor2 = cupy.zeros((acorlen))
    this_corA = cupy.zeros((acorlen))
    this_corB = cupy.zeros((acorlen))    

    # Do the correlation
    for i in range(iterations):
        # Auto correlation PC1A X PC1B
        data_pc1B_cu = cupy.array(data_pc1B[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        data_pc1A_cu = cupy.array(data_pc1A[length*i:length*(i+1)]).astype(np.float32)
        this_cor1 += cupy.correlate(data_pc1B_cu, data_pc1A_cu, "valid")
        # Auto correlation PC2A X PC2B
        data_pc2B_cu = cupy.array(data_pc2B[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        data_pc2A_cu = cupy.array(data_pc2A[length*i:length*(i+1)]).astype(np.float32)
        this_cor2 += cupy.correlate(data_pc2B_cu, data_pc2A_cu, "valid")
        # Cross correlation PC1A X PC2A
        data_pc2A_cu = cupy.array(data_pc2A[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        data_pc1A_cu = cupy.array(data_pc1A[length*i:length*(i+1)]).astype(np.float32)
        this_corA += cupy.correlate(data_pc2A_cu, data_pc1A_cu, "valid")
        # Cross correlation PC1B X PC2B
        data_pc2B_cu = cupy.array(data_pc2B[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        data_pc1B_cu = cupy.array(data_pc1B[length*i:length*(i+1)]).astype(np.float32)
        this_corB += cupy.correlate(data_pc2B_cu, data_pc1B_cu, "valid")    

    this_cor1 = cupy.asnumpy(this_cor1)
    this_cor2 = cupy.asnumpy(this_cor2)
    this_corA = cupy.asnumpy(this_corA)
    this_corB = cupy.asnumpy(this_corB)    

    np.savetxt(resultfilename, np.c_[this_cor1, this_cor2, this_corA, this_corB], header="{} {} {} {} {}".format(ctime, mean_pc1A, mean_pc1B, mean_pc2A, mean_pc2B))
    endtime = time.time(); dtime = endtime - stime
    analyzefiles += 1; totalfiles += 1
    del this_corA; del this_corB; del this_cor1; del this_cor2
    del data_pc1A_cu; data_pc1B_cu; del data_pc2A_cu; del data_pc2B_cu
    del data_pc1; del data_pc2; del data_pc1A; del data_pc1B; del data_pc2A; del data_pc2B
    print ("\tAnalyzing {} files in {:.2f} seconds : {:.2f} s per file. Total files: {}".format(analyzefiles, dtime, dtime/analyzefiles, totalfiles))



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
