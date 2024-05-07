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
parser.add_option("--t", dest="t_disk")
parser.add_option("-d", "--datapath", dest="datapath")
(options, args) = parser.parse_args()

start = int(options.start)
end   = int(options.end)
t_disk = str(options.t_disk)
datapath = str(options.datapath)

# Combine data paths for the telescope
t_path = t_disk + ":/roof_MT1_2/" + datapath

# File creation time
def file_time(file):
    pctime = os.path.getctime(file)
    return pctime

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
    global t_filename, readfiles, stime, analyzefiles, totalfiles

    this_pc_filename = t_filename

    resultfilename = "C:/Users/ii/Documents/curcor/corr_results/results_roof/" + datapath + "_" + this_pc_filename.split("_")[-1].split(".")[0] + ".autocorr"

    data_pc = np.fromfile(this_pc_filename,dtype=np.int8)
    endtime = time.time(); dtime = endtime - stime

    data_pc = data_pc.reshape(int(len(data_pc)/2),2)
    data_pcA = data_pc[:,0]; data_pcB = data_pc[:,1]

    # Calculate means
    mean_pcA = np.mean(data_pcA)
    mean_pcB = np.mean(data_pcB)
    # Get file creation time
    ctime = file_time(this_pc_filename)

    readfiles += 1
    print ("\tReading {} files in {:.2f} seconds : {:.2f} s per file".format(readfiles, dtime, dtime/readfiles))

    iterations=int(len(data_pc)/length)-1
    this_cor = cupy.zeros((acorlen))

    # Do the correlation
    for i in range(iterations):
        # Auto correlation PC1A X PC1B
        data_pcB_cu = cupy.array(data_pcB[ int(corlen/2)+(length*i) : (-1)*int(corlen/2)+(length*(i+1)) ]).astype(np.float32)
        data_pcA_cu = cupy.array(data_pcA[length*i:length*(i+1)]).astype(np.float32)
        this_cor   += cupy.correlate(data_pcB_cu, data_pcA_cu, "valid")

    this_cor = cupy.asnumpy(this_cor)

    np.savetxt(resultfilename, this_cor[20000:30000], header="{} {} {}".format(ctime, mean_pcA, mean_pcB))
    endtime = time.time(); dtime = endtime - stime
    analyzefiles += 1; totalfiles += 1
    del this_cor
    del data_pcA_cu; data_pcB_cu
    del data_pc; del data_pcA; del data_pcB
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

        t_filename = t_path + "_{:05d}.bin".format(run)
        
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