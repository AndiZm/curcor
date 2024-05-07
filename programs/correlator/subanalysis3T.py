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
parser.add_option("--t1", dest="ct1_disk")
parser.add_option("--t3", dest="ct3_disk")
parser.add_option("--t4", dest="ct4_disk")
parser.add_option("-d", "--datapath", dest="datapath")
(options, args) = parser.parse_args()

start = int(options.start)
end   = int(options.end)
ct1_disk = str(options.ct1_disk)
ct3_disk = str(options.ct3_disk)
ct4_disk = str(options.ct4_disk)
datapath = str(options.datapath)

# Combine data paths for both telescopes
ct1_path = ct1_disk + ":/ct1/" + datapath
ct3_path = ct3_disk + ":/ct3/" + datapath
ct4_path = ct4_disk + ":/ct4/" + datapath

# File creation time
def file_time(file1, file3, file4):
    # Check for both file creation times and see whether there is a big difference due to not-synchronized computer clocks or not.
    pc1time = os.path.getctime(file1)
    pc3time = os.path.getctime(file3)
    pc4time = os.path.getctime(file4)
    diff31 = np.abs(pc3time - pc1time)
    diff41 = np.abs(pc4time - pc1time)
    diff43 = np.abs(pc4time - pc3time)
    diff = max(diff31,diff41,diff43)

    # If the clocks are sufficiently well synchronized, PC1 file creation time is return per default. If not, the mean of both is returned
    if diff < 50:
        return pc1time
    else:
        print ("There is a problem with the synchronization of files:")
        print (file1, pc1time)
        print (file3, pc3time)
        print (file4, pc4time)
        print (diff)
        return np.mean([pc1time, pc3time, pc4time])

##########
## MAIN ##
##########
# Number of parallel file runs
n_parallel = int(4)

startfull=time.time()

corlen=50000
#files = 10
length=int(2**22)

acorlen=corlen+1
cor_cu=cupy.zeros((acorlen))

totalfiles = 0
bunchtimes = []

def readfile():
    global ct1_filename, ct3_filename, ct4_filename, readfiles, stime, analyzefiles, totalfiles

    this_pc1_filename = ct1_filename
    this_pc3_filename = ct3_filename
    this_pc4_filename = ct4_filename

    resultfilename = "C:/Users/ii/Documents/curcor/corr_results/results_HESS/" + datapath + "_" + this_pc1_filename.split("_")[-1].split(".")[0] + ".fcorr3T"

    data_pc1 = np.fromfile(this_pc1_filename,dtype=np.int8)
    data_pc3 = np.fromfile(this_pc3_filename,dtype=np.int8)
    data_pc4 = np.fromfile(this_pc4_filename,dtype=np.int8)
    endtime = time.time(); dtime = endtime - stime


    data_pc1 = data_pc1.reshape(int(len(data_pc1)/2),2)
    data_pc1A = data_pc1[:,0]; data_pc1B = data_pc1[:,1]

    data_pc3 = data_pc3.reshape(int(len(data_pc3)/2),2)
    data_pc3A = data_pc3[:,0]; data_pc3B = data_pc3[:,1]

    data_pc4 = data_pc4.reshape(int(len(data_pc4)/2),2)
    data_pc4A = data_pc4[:,0]; data_pc4B = data_pc4[:,1]

    # Calculate means
    mean_pc1A = np.mean(data_pc1A)
    mean_pc1B = np.mean(data_pc1B)
    mean_pc3A = np.mean(data_pc3A)
    mean_pc3B = np.mean(data_pc3B)
    mean_pc4A = np.mean(data_pc4A)
    mean_pc4B = np.mean(data_pc4B)
    # Get file creation time
    ctime = file_time(this_pc1_filename, this_pc3_filename, this_pc4_filename)

    readfiles += 1
    print ("\tReading {} files in {:.2f} seconds : {:.2f} s per file".format(readfiles, dtime, dtime/readfiles))

    iterations=int(len(data_pc3)/length)-1
    this_corA13 = cupy.zeros((acorlen))
    this_corA14 = cupy.zeros((acorlen))
    this_corA34 = cupy.zeros((acorlen))
    this_corB13 = cupy.zeros((acorlen))
    this_corB14 = cupy.zeros((acorlen))
    this_corB34 = cupy.zeros((acorlen))


    # Do the correlation
    for i in range(iterations):
        # Cross correlation PC1A X PC3A
        data_pc3A_cu = cupy.array(data_pc3A[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        data_pc1A_cu = cupy.array(data_pc1A[length*i:length*(i+1)]).astype(np.float32)
        this_corA13 += cupy.correlate(data_pc3A_cu, data_pc1A_cu, "valid")
        # Cross correlation PC1B X PC3B
        data_pc3B_cu = cupy.array(data_pc3B[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        data_pc1B_cu = cupy.array(data_pc1B[length*i:length*(i+1)]).astype(np.float32)
        this_corB13 += cupy.correlate(data_pc3B_cu, data_pc1B_cu, "valid")

        # Cross correlation PC1A X PC4A
        data_pc4A_cu = cupy.array(data_pc4A[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        data_pc1A_cu = cupy.array(data_pc1A[length*i:length*(i+1)]).astype(np.float32)
        this_corA14 += cupy.correlate(data_pc4A_cu, data_pc1A_cu, "valid")
        # Cross correlation PC1B X PC4B
        data_pc4B_cu = cupy.array(data_pc4B[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        data_pc1B_cu = cupy.array(data_pc1B[length*i:length*(i+1)]).astype(np.float32)
        this_corB14 += cupy.correlate(data_pc4B_cu, data_pc1B_cu, "valid")

        # Cross correlation PC3A X PC4A
        data_pc4A_cu = cupy.array(data_pc4A[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        data_pc3A_cu = cupy.array(data_pc3A[length*i:length*(i+1)]).astype(np.float32)
        this_corA34 += cupy.correlate(data_pc4A_cu, data_pc3A_cu, "valid")
        # Cross correlation PC3B X PC4B
        data_pc4B_cu = cupy.array(data_pc4B[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        data_pc3B_cu = cupy.array(data_pc3B[length*i:length*(i+1)]).astype(np.float32)
        this_corB34 += cupy.correlate(data_pc4B_cu, data_pc3B_cu, "valid")

    this_corA13 = cupy.asnumpy(this_corA13)
    this_corA14 = cupy.asnumpy(this_corA14)
    this_corA34 = cupy.asnumpy(this_corA34)
    this_corB13 = cupy.asnumpy(this_corB13)
    this_corB14 = cupy.asnumpy(this_corB14)
    this_corB34 = cupy.asnumpy(this_corB34)


    np.savetxt(resultfilename, np.c_[this_corA13, this_corB13, this_corA14, this_corB14, this_corA34, this_corB34], header="{} {} {} {} {} {} {}\n13A\t13B\t14A\t14B\t34A\t34B".format(ctime, mean_pc1A, mean_pc1B, mean_pc3A, mean_pc3B, mean_pc4A, mean_pc4B))
    endtime = time.time(); dtime = endtime - stime
    analyzefiles += 1; totalfiles += 1
    del this_corA13; del this_corA14; del this_corA34; del this_corB13; del this_corB14; del this_corB34
    del data_pc1A_cu; data_pc1B_cu; del data_pc3A_cu; del data_pc3B_cu; del data_pc4A_cu; del data_pc4B_cu
    del data_pc1; del data_pc3; del data_pc4; del data_pc1A; del data_pc1B; del data_pc3A; del data_pc3B; data_pc4A; del data_pc4B
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

        ct1_filename = ct1_path + "_{:05d}.bin".format(run)
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
print ("\tAnalyzing {} files in {:.2f} seconds".format(totalfiles, fulltime))
print ("\tAnalyzing {} files in {:.2f} seconds : {:.2f} s per file".format(totalfiles, fulltime, fulltime/totalfiles))