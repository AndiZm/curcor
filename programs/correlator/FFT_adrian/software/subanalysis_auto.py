<<<<<<< HEAD
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
def file_time(file):
    # Check for both file creation times and see whether there is a big difference due to not-synchronized computer clocks or not.
    pctime = os.path.getctime(file)
    diff = pctime
    return pc1time


# Rate calculations
off   = -3.603750420000000343e-01
calib = -65.2418293569126
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
pc_body = "G:/20220416_halogentest/"
filepath = "halogen_no_ndfilter_"

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
    global pc_filename, readfiles, stime, analyzefiles, totalfiles

    this_pc_filename = pc_filename
    resultfilename = "../results/20220416_halogen/" + this_pc_filename.split("/")[-1].split(".")[0] + ".fcorr"

    data = np.fromfile(this_pc_filename,dtype=np.int8)
    endtime = time.time(); dtime = endtime - stime

    # Calculate means
    #mean_pc1 = np.mean(data_pc1)
    #mean_pc2 = np.mean(data_pc2)
    ## Get file creation time
    #ctime = file_time(this_pc1_filename, this_pc2_filename)

    readfiles += 1
    print ("\tReading {} files in {:.2f} seconds : {:.2f} s per file".format(readfiles, dtime, dtime/readfiles))

    data=data.reshape(int(len(data)/2),2)
    dataA=data[:,0]; dataB=data[:,1]

    iterations=int(len(dataB)/length)-1
    this_cor = cupy.zeros((acorlen))
    for i in range(iterations):
        dataB_cu=cupy.array(dataB[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        dataA_cu=cupy.array(dataA[length*i:length*(i+1)]).astype(np.float32)
        this_cor+=cupy.correlate(dataB_cu,dataA_cu,"valid")

    this_cor = cupy.asnumpy(this_cor)
    #np.savetxt(resultfilename, this_cor, header="{} {} {}".format(ctime, mean_pc1, mean_pc2))
    np.savetxt(resultfilename, this_cor)
    endtime = time.time(); dtime = endtime - stime
    analyzefiles += 1; totalfiles += 1
    del this_cor; del dataA; del dataB
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
        pc_filename = pc_body + filepath + "{:05d}.bin".format(run)
        
        threads.append(Thread(target=readfile, args=()))
        threads[-1].start()

    for i in threads:
        i.join()
    print ("Parallel computing done.\n\n")
    fileindex += n_parallel

endfull = time.time()
fulltime = endfull - startfull
print ("########################################################################")
=======
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
def file_time(file):
    # Check for both file creation times and see whether there is a big difference due to not-synchronized computer clocks or not.
    pctime = os.path.getctime(file)
    diff = pctime
    return pc1time


# Rate calculations
off   = -3.603750420000000343e-01
calib = -65.2418293569126
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
pc_body = "G:/20220416_halogentest/"
filepath = "halogen_no_ndfilter_"

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
    global pc_filename, readfiles, stime, analyzefiles, totalfiles

    this_pc_filename = pc_filename
    resultfilename = "../results/20220416_halogen/" + this_pc_filename.split("/")[-1].split(".")[0] + ".fcorr"

    data = np.fromfile(this_pc_filename,dtype=np.int8)
    endtime = time.time(); dtime = endtime - stime

    # Calculate means
    #mean_pc1 = np.mean(data_pc1)
    #mean_pc2 = np.mean(data_pc2)
    ## Get file creation time
    #ctime = file_time(this_pc1_filename, this_pc2_filename)

    readfiles += 1
    print ("\tReading {} files in {:.2f} seconds : {:.2f} s per file".format(readfiles, dtime, dtime/readfiles))

    data=data.reshape(int(len(data)/2),2)
    dataA=data[:,0]; dataB=data[:,1]

    iterations=int(len(dataB)/length)-1
    this_cor = cupy.zeros((acorlen))
    for i in range(iterations):
        dataB_cu=cupy.array(dataB[int(corlen/2)+(length*i):(-1)*int(corlen/2)+(length*(i+1))]).astype(np.float32)
        dataA_cu=cupy.array(dataA[length*i:length*(i+1)]).astype(np.float32)
        this_cor+=cupy.correlate(dataB_cu,dataA_cu,"valid")

    this_cor = cupy.asnumpy(this_cor)
    #np.savetxt(resultfilename, this_cor, header="{} {} {}".format(ctime, mean_pc1, mean_pc2))
    np.savetxt(resultfilename, this_cor)
    endtime = time.time(); dtime = endtime - stime
    analyzefiles += 1; totalfiles += 1
    del this_cor; del dataA; del dataB
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
        pc_filename = pc_body + filepath + "{:05d}.bin".format(run)
        
        threads.append(Thread(target=readfile, args=()))
        threads[-1].start()

    for i in threads:
        i.join()
    print ("Parallel computing done.\n\n")
    fileindex += n_parallel

endfull = time.time()
fulltime = endfull - startfull
print ("########################################################################")
>>>>>>> refs/remotes/origin/main
print ("\tAnalyzing {} files in {:.2f} seconds : {:.2f} s per file".format(totalfiles, fulltime, fulltime/totalfiles))