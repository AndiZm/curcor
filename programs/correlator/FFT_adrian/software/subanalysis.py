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
parser.add_option("--t3", dest="ct3_disk")
parser.add_option("--t4", dest="ct4_disk")
parser.add_option("-d", "--datapath", dest="datapath")
(options, args) = parser.parse_args()

start = int(options.start)
end   = int(options.end)
ct3_disk = str(options.ct3_disk)
ct4_disk = str(options.ct4_disk)
datapath = str(options.datapath)

# Combine data paths for both telescopes
ct3_path = ct3_disk + ":/" + datapath
ct4_path = ct4_disk + ":/" + datapath

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
# Number of parallel file runs
n_parallel = int(5)

startfull=time.time()

corlen=50000
#files = 10
length=int(2**22)

acorlen=corlen+1
cor_cu=cupy.zeros((acorlen))

totalfiles = 0
bunchtimes = []

def readfile():
    global ct3_filename, ct4_filename, readfiles, stime, analyzefiles, totalfiles

    this_pc1_filename = ct3_filename
    this_pc2_filename = ct4_filename

    resultfilename = "C:/Users/ii/Documents/curcor/corr_results/results/" + datapath + "_" + this_pc1_filename.split("_")[-1].split(".")[0] + ".fcorr"

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
        ###data_pc1A_cu = cupy.array(data_pc1A[length*i:length*(i+1)]).astype(np.float32)
        this_corA += cupy.correlate(data_pc2A_cu, data_pc1A_cu, "valid")
        # Cross correlation PC1B X PC2B
        ###data_pc2B_cu = cupy.array(data_pc2B[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
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
    print ("\nNew parallel computing of {} files".format(n_parallel))
    for run in range(fileindex,min(fileindex+n_parallel,end)):

        ct3_filename = ct3_path + "_{:05d}.bin".format(run)
        ct4_filename = ct4_path + "_{:05d}.bin".format(run)
        
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