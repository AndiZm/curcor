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
pc1_body = "H:/Shared/"
pc2_body = "E:/"
filepath = "2022_Sirius/20220303_roof/sirius_"

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
    resultfilename = "../results/20220303_roof/" + this_pc1_filename.split("/")[-1].split(".")[0] + ".fcorr"

    data_pc1 = np.fromfile(this_pc1_filename,dtype=np.int8)
    data_pc2 = np.fromfile(this_pc2_filename,dtype=np.int8)
    endtime = time.time(); dtime = endtime - stime

    # Calculate means
    mean_pc1 = np.mean(data_pc1)
    mean_pc2 = np.mean(data_pc2)
    # Get file creation time
    ctime = file_time(this_pc1_filename, this_pc2_filename)

    readfiles += 1
    print ("\tReading {} files in {:.2f} seconds : {:.2f} s per file".format(readfiles, dtime, dtime/readfiles))

    iterations=int(len(data_pc2)/length)-1
    this_cor = cupy.zeros((acorlen))
    for i in range(iterations):
        data_pc2_cu=cupy.array(data_pc2[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        data_pc1_cu=cupy.array(data_pc1[length*i:length*(i+1)]).astype(np.float32)
        # Correlate
        this_cor+=cupy.correlate(data_pc2_cu,data_pc1_cu,"valid")

    this_cor = cupy.asnumpy(this_cor)
    np.savetxt(resultfilename, this_cor, header="{} {} {}".format(ctime, mean_pc1, mean_pc2))
    endtime = time.time(); dtime = endtime - stime
    analyzefiles += 1; totalfiles += 1
    del this_cor; del data_pc1_cu; del data_pc2_cu; del data_pc1; del data_pc2
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