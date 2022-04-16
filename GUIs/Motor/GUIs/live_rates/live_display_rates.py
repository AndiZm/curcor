import time
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import os
from os import listdir
from os.path import isfile, join
from tkinter import *
import scipy.signal as ss
import phd as phd


def execute(path, samples, packet_length, npackets, amp_a, amp_b, calib_a, calib_b, nps_a, nps_b, off_a, off_b, vol_a, vol_b):

channels = 2
t_bin = 0.8e-9 # seconds
mvRange = 200

voltage_a = vol_a; voltage_b = vol_b
normed_peak_sum_a = nps_a; normed_peak_sum_b = nps_b
off_mean_a_ADC = off_a; off_mean_b_ADC = off_b # ADC
# Calibration data
calib = np.loadtxt(calib_a)
c_v = calib[:,0]; c_mean = calib[:,1]; c_sigma = calib[:,2]
#get mean and sigma
mean = []; sigma = []; keep = []; avg = [] # mV
calibrated = False
for i in range (0, len(c_v)):
    if c_v[i] == voltage:
        mean  = c_mean[i]
        sigma = c_sigma[i]
        print ("Mean: {:.2f}\tSigma: {:.2f}".format(mean,sigma))
        keep, avg = phd.execute(mean, sigma)
        print ("Avg peak height: {:.2f}".format(avg))
        calibrated = True
if calibrated == False:
    print ("NO CALIB DATA FOR GIVEN VOLTAGE FOUND!")
    exit(0)

# Average photon charge
C_a = normed_peak_sum * avg # mV
C_b = normed_peak_sum * avg # mV
# Baseline mean in mV
off_mean_a_mV = off_mean_a_ADC * mvRange/127
off_mean_b_mV = off_mean_b_ADC * mvRange/127

def wait_for_file(path):
    # Start files which are not to analyze
    startfiles = [f for f in listdir(path) if isfile(join(path, f))]
    filearray = []
    for i in range (0, len(startfiles)):
        if startfiles[i][-4:] == ".bin":
            filearray.append(path + "/" + startfiles[i])
            print (filearray[-1] + " -- Size: " + str(os.stat(filearray[-1]).st_size))
    print (" ")

root = Tk(); root.geometry("300x100"); root.geometry("+950+820")
mainFrame = Frame(root, width=500, height=200)
mainFrame.grid(row=0,column=0)


desc_Label_mean = Label(mainFrame, text="Voltage")
desc_Label_mean.grid(row=0, column=0)
desc_Label_curr = Label(mainFrame, text="PMT current")
desc_Label_curr.grid(row=0, column=1)
desc_Label_rate = Label(mainFrame, text="Photon rate")
desc_Label_rate.grid(row=0, column=2)

CHa_Label_mean = Label(mainFrame, text="0 mV", fg="orange", bg="black", font=("Helvetica 15 bold"))
CHa_Label_mean.grid(row=1, column=0)
CHb_Label_mean = Label(mainFrame, text="0 mV", fg="orange", bg="black", font=("Helvetica 15 bold"))
CHb_Label_mean.grid(row=2, column=0)

CHa_Label_curr = Label(mainFrame, text="0 µA", fg="red", bg="grey", font=("Helvetica 15 bold"))
CHa_Label_curr.grid(row=1, column=1)
CHb_Label_curr = Label(mainFrame, text="0 µA", fg="red", bg="grey", font=("Helvetica 15 bold"))
CHb_Label_curr.grid(row=2, column=1)

CHa_Label_rate = Label(mainFrame, text="0.0 MHz", fg="orange", bg="black", font=("Helvetica 15 bold"))
CHa_Label_rate.grid(row=1, column=2)
CHb_Label_rate = Label(mainFrame, text="0.0 MHz", fg="orange", bg="black", font=("Helvetica 15 bold"))
CHb_Label_rate.grid(row=2, column=2)
root.update()

# Search for new files
while (True):
    # Search if new files are available
    current_files = [f for f in listdir(path) if isfile(join(path, f))]    
    newfiles = []; modified = []; new = False
    for i in range (0, len(current_files)):
        cfile = path + "/" + current_files[i]
        if cfile not in filearray and os.stat(cfile).st_size > (channels*samples) and cfile[-4:] == ".bin":
            #print ("New file: " + cfile + " -- Size: " + str(os.stat(cfile).st_size) + " -- and: " + str(os.stat(cfile).st_mtime_ns))
            filearray.append(cfile); newfiles.append(cfile); modified.append(os.stat(cfile).st_mtime_ns)
            new = True
    # Find newest file and analyze
    if new == True:
        newest_file = newfiles[np.argmax(modified)]
        print ("Newest file: " + newest_file)
        new = False

        counts_a = 0; counts_b = 0
        with open(newest_file, 'rb') as f:
            for allpkt in range(0, npackets):
                buf = (f.read(2*packet_length))
                packet = np.frombuffer(buf, dtype=np.int8)
                packet = packet.reshape(packet_length, 2)
                a_np = np.array(packet[:,0]).flatten(); b_np = np.array(packet[:,1]).flatten()
                mean_a = np.mean(a_np); mean_b = np.mean(b_np)
                del(a_np); del(b_np)



        means_a_ADC = np.mean(mean_a); means_b_ADC = np.mean(mean_b)
        means_a_mV = means_a_ADC * mvRange/127; means_b_mV = means_b_ADC * mvRange/127

        # mV
        d_means_a_mV = means_a_mV - off_mean_a_mV
        d_means_b_mV = means_b_mV - off_mean_b_mV
        CHa_Label_mean.config(text="{:.1f} mV".format(d_means_a_mV))
        CHb_Label_mean.config(text="{:.1f} mV".format(d_means_b_mV))

        # PMT current
        curr_a_microamp = 1e3 * d_means_a_mV/amp_a/50
        curr_b_microamp = 1e3 * d_means_b_mV/amp_b/50        
        CHa_Label_curr.config(text="{:.1f} µA".format(curr_a_microamp))
        CHb_Label_curr.config(text="{:.1f} µA".format(curr_b_microamp))

        # Rates
        r_a = 1e-6 * d_means_a_mV/(t_bin * C_a)
        r_b = 1e-6 * d_means_b_mV/(t_bin * C_b)      
        CHa_Label_rate.config(text="{:.1f}  MHz".format(r_a))
        CHb_Label_rate.config(text="{:.1f}  MHz".format(r_b))

        root.update()
    time.sleep(0.5)   