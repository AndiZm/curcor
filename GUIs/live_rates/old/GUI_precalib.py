import time
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import os
from os import listdir
from os.path import isfile, join
from tkinter import *
from tkinter import filedialog
import scipy.signal as ss

import live_phd as phd
import live_offset_meas as off
from threading import Thread


#numChan, vRange, vOffset, numLen, sampleRate
vRange = 200
t_bin = 0.8e-9

def ADC_to_mV(adc, range):
	return adc*range/127
def mV_to_ADC(mV, range):
	return mV*127/range

root = Tk(); root.wm_title("Almost live measures")
rootMainFrame = Frame(root); rootMainFrame.grid(row=0,column=0)

## Common Frame ##
commonFrame = Frame(rootMainFrame); commonFrame.grid(row=0,column=0)

# Samples
samples = StringVar(root); samples.set("128 MS")
sampleoptions = {
	"64 S": 64, "128 S": 128, "256 S": 256, "512 S": 512,
	"1 kS": 1024, "2 kS": 2048, "4 kS": 4096, "8 kS": 8192, "16 kS": 16384, "32 kS": 32768, "64 kS": 65536,
	"128 kS": 131072, "256 kS": 262144, "512 kS": 524288,
	"1 MS": 1048576, "2 MS": 2097152, "4 MS": 4194304, "8 MS": 8388608, "16 MS": 16777216, "32 MS": 33554432, "64 MS": 67108864,
	"128 MS": 134217728, "256 MS": 268435456, "512 MS": 536870912,
	"1 GS": 1073741824, "2 GS": 2147483648, "4 GS": 4294967296
}
samplesDropdownLabel = Label(commonFrame, text="File Sample Size"); samplesDropdownLabel.grid(row=0,column=0)
samplesDropdown = OptionMenu(commonFrame, samples, *sampleoptions)
samplesDropdown.grid(row=0, column=1)

# path
basicpath = "E:/"
def selectDirectory():
	global basicpath
	root.directoryname = filedialog.askdirectory(initialdir = basicpath, title = "Select any data directory")
	basicpath = root.directoryname
	pathLabel.config(text=basicpath.split("/")[1])
pathButton = Button(commonFrame, text="Files directory", command=selectDirectory); pathButton.grid(row=1, column=0)
pathLabel = Label(commonFrame, text=basicpath.split("/")[1]); pathLabel.grid(row=1,column=1)

# packet length
packetLengthLabel = Label(commonFrame, text="Packet length"); packetLengthLabel.grid(row=2,column=0)
packetLengthEntry = Entry(commonFrame, width=7); packetLengthEntry.grid(row=2,column=1); packetLengthEntry.insert(0,"100000")
# npackets
npacketsLabel = Label(commonFrame, text="n Packets"); npacketsLabel.grid(row=3,column=0)
npacketsEntry = Entry(commonFrame, width=7); npacketsEntry.grid(row=3,column=1); npacketsEntry.insert(0,"1")

## CHANNEL A/B FRAME ##
abFrame = Frame(rootMainFrame); abFrame.grid(row=1,column=0)

parLabel = Label(abFrame, text="Parameter", font=("Helvetica 12 bold")); parLabel.grid(row=0,column=0)
aLabel = Label(abFrame, text="CHN A", font=("Helvetica 12 bold")); aLabel.grid(row=0,column=1)
bLabel = Label(abFrame, text="CHN B", font=("Helvetica 12 bold")); bLabel.grid(row=0,column=2)

# Amplifiers
ampLabel = Label(abFrame, text="Amp"); ampLabel.grid(row=1, column=0)
ampAEntry = Entry(abFrame, width=5); ampAEntry.grid(row=1, column=1); ampAEntry.insert(0,"10")
ampBEntry = Entry(abFrame, width=5); ampBEntry.grid(row=1, column=2); ampBEntry.insert(0,"10")

# calib file
calibLabel = Label(abFrame, text="Voltage calibration files"); calibLabel.grid(row=2,column=0)
calibfile_A = "in_mV.calib"
def selectCalibFile_A():
	global calibfile_A
	root.filename = filedialog.askopenfilename(initialdir = "C:/Users/ii/Documents/curcor/python/pur_bin/optimiert/live_rates", title = "Select calibration file", filetypes = (("calibration files","*.calib"),("all files","*.*")))
	calibfile_A = root.filename
	calibAButton.config(text=calibfile_A.split("/")[-1])
calibAButton = Button(abFrame, text=calibfile_A, command=selectCalibFile_A); calibAButton.grid(row=2,column=1)

calibfile_B = "in_mV.calib"
def selectCalibFile_B():
	global calibfile_B
	root.filename = filedialog.askopenfilename(initialdir = "C:/Users/ii/Documents/curcor/python/pur_bin/optimiert/live_rates", title = "Select calibration file", filetypes = (("calibration files","*.calib"),("all files","*.*")))
	calibfile_B = root.filename
	calibBButton.config(text=calibfile_B.split("/")[-1])
calibBButton = Button(abFrame, text=calibfile_B, command=selectCalibFile_B); calibBButton.grid(row=2,column=2)

# shp file
pulseLabel = Label(abFrame, text="Pulse Integral"); pulseLabel.grid(row=3, column=0)
pulseAEntry = Entry(abFrame, width=5); pulseAEntry.grid(row=3, column=1); pulseAEntry.insert(0, "7.14")
pulseBEntry = Entry(abFrame, width=5); pulseBEntry.grid(row=3, column=2); pulseBEntry.insert(0, "7.14")

# voltage
voltages = {
	"790 V": 790, "800 V": 800, "810 V": 810, "820 V": 820, "830 V": 830, "840 V": 840, "850 V": 850, "860 V": 860, "870 V":870, "880 V": 880, "890 V": 890, "900 V": 900
}
voltageLabel = Label(abFrame, text="Voltages"); voltageLabel.grid(row=4,column=0)
voltageA = StringVar(root); voltageA.set("900 V"); voltageB = StringVar(root); voltageB.set("900 V")
voltageADropdown = OptionMenu(abFrame, voltageA, *voltages); voltageADropdown.grid(row=4,column=1)
voltageBDropdown = OptionMenu(abFrame, voltageB, *voltages); voltageBDropdown.grid(row=4,column=2)

# Baseline offset
offsetLabel = Label(abFrame, text="Basline offset [ADC]"); offsetLabel.grid(row=5,column=0)
offsetAEntry = Entry(abFrame, width=7); offsetAEntry.grid(row=5, column=1); offsetAEntry.insert(0,"0.0")
offsetBEntry = Entry(abFrame, width=7); offsetBEntry.grid(row=5, column=2); offsetBEntry.insert(0,"0.0")

### Start/Stop Frame ###
startstopFrame = Frame(rootMainFrame); startstopFrame.grid(row=2,column=0)
deleteFiles = False
def switch_delete():
	global deleteFiles;
	if deleteFiles == False:
		deleteFiles = True
		deleteButton.config(text="delete ON", bg="#ffbb33")
	else:
		deleteFiles = False
		deleteButton.config(text="delete OFF", bg ="#dedede")
deleteButton = Button(startstopFrame, text="delete OFF", bg="#dedede", command=switch_delete); deleteButton.grid(row=0,column=0)

mean_a = 0.0; mean_b = 0.0
def off_measurement():
	global mean_a, mean_b
	thesamples = int(sampleoptions[samples.get()])
	mean_a, mean_b = off.execute(path=basicpath, samples=thesamples, packet_length=int(packetLengthEntry.get()), npackets=int(npacketsEntry.get()))
	offsetAEntry.delete(0, END); offsetAEntry.insert(0, str(mean_a))
	offsetBEntry.delete(0, END); offsetBEntry.insert(0, str(mean_b))

offButton = Button(startstopFrame, text="Off calibration", bg="#ccf2ff", command=off_measurement); offButton.grid(row=0,column=1)

### Display Frame ###
displayFrame = Frame(rootMainFrame); displayFrame.grid(row=3,column=0)

desc_Label_mean = Label(displayFrame, text="Voltage"); desc_Label_mean.grid(row=0, column=0)
desc_Label_curr = Label(displayFrame, text="PMT current"); desc_Label_curr.grid(row=1, column=0)
desc_Label_rate = Label(displayFrame, text="Photon rate");	desc_Label_rate.grid(row=2, column=0)

CHa_Label_mean = Label(displayFrame, text="0 mV", fg="orange", bg="black", font=("Helvetica 10 bold")); CHa_Label_mean.grid(row=0, column=1)
CHb_Label_mean = Label(displayFrame, text="0 mV", fg="orange", bg="black", font=("Helvetica 10 bold")); CHb_Label_mean.grid(row=0, column=2)

CHa_Label_curr = Label(displayFrame, text="0 µA", fg="red", bg="grey", font=("Helvetica 10 bold")); CHa_Label_curr.grid(row=1, column=1)
CHb_Label_curr = Label(displayFrame, text="0 µA", fg="red", bg="grey", font=("Helvetica 10 bold")); CHb_Label_curr.grid(row=1, column=2)

CHa_Label_rate = Label(displayFrame, text="0.0 MHz", fg="orange", bg="black", font=("Helvetica 10 bold"));	CHa_Label_rate.grid(row=2, column=1)
CHb_Label_rate = Label(displayFrame, text="0.0 MHz", fg="orange", bg="black", font=("Helvetica 10 bold"));	CHb_Label_rate.grid(row=2, column=2)

running = False; stop_thread = False

def analyze_files(off_mean_a_mV, off_mean_b_mV, C_a, C_b):
	global stop_thread

	# Start files which are not to analyze
	startfiles = [f for f in listdir(basicpath) if isfile(join(basicpath, f))]
	filearray = []
	for i in range (0, len(startfiles)):
		if startfiles[i][-4:] == ".bin":
			filearray.append(basicpath + "/" + startfiles[i])

	channels=int(2)
	while(stop_thread == False):
		# Search if new files are available
		current_files = [f for f in listdir(basicpath) if isfile(join(basicpath, f))]    
		newfiles = []; modified = []; new = False
		for i in range (0, len(current_files)):
			cfile = basicpath + "/" + current_files[i]
			if cfile not in filearray and os.stat(cfile).st_size >= (channels*int(sampleoptions[samples.get()])) and cfile[-4:] == ".bin":
				filearray.append(cfile); newfiles.append(cfile); modified.append(os.stat(cfile).st_mtime_ns)
				new = True
		# Find newest file and analyze
		if new == True:
			newest_file = newfiles[np.argmax(modified)]
			new = False

			with open(newest_file, 'rb') as f:
				means_a = []; means_b = []
				for allpkt in range(0, int(npacketsEntry.get())):
					buf = (f.read(2*int(packetLengthEntry.get())))
					packet = np.frombuffer(buf, dtype=np.int8)
					packet = packet.reshape(int(packetLengthEntry.get()), 2)
					a_np = np.array(packet[:,0]).flatten(); b_np = np.array(packet[:,1]).flatten()
					means_a.append(np.mean(a_np)); means_b.append(np.mean(b_np))
					del(a_np); del(b_np)
	
			mean_a_ADC = np.mean(means_a); mean_b_ADC = np.mean(means_b)
			mean_a_mV = ADC_to_mV(adc=mean_a_ADC, range=vRange); mean_b_mV = ADC_to_mV(adc=mean_b_ADC, range=vRange)
	
			# mV
			d_mean_a_mV = mean_a_mV - off_mean_a_mV; d_mean_b_mV = mean_b_mV - off_mean_b_mV
			CHa_Label_mean.config(text="{:.2f} mV".format(d_mean_a_mV)); CHb_Label_mean.config(text="{:.2f} mV".format(d_mean_b_mV))
			# PMT current
			curr_a_microamp = 1e3 * d_mean_a_mV/float(ampAEntry.get())/50; curr_b_microamp = 1e3 * d_mean_b_mV/float(ampBEntry.get())/50        
			CHa_Label_curr.config(text="{:.1f} µA".format(curr_a_microamp)); CHb_Label_curr.config(text="{:.1f} µA".format(curr_b_microamp))
			# Rates
			r_a = 1e-6 * d_mean_a_mV/(t_bin * C_a); r_b = 1e-6 * d_mean_b_mV/(t_bin * C_b)      
			CHa_Label_rate.config(text="{:.1f}  MHz".format(r_a)); CHb_Label_rate.config(text="{:.1f}  MHz".format(r_b))

			root.update()
		time.sleep(0.5)

def startstop():
	global running, stop_thread
	if running == False:
		running = True

		voltage_a = int(voltages[voltageA.get()]); voltage_b = int(voltages[voltageB.get()])
		avg_a, avg_b = phd.execute(calibfile_A=calibfile_A, calibfile_B=calibfile_B, voltage_a=voltage_a, voltage_b=voltage_b)
		# Average photon charge
		C_a = float(pulseAEntry.get()) * avg_a # mV
		C_b = float(pulseBEntry.get()) * avg_b # mV
		# Baseline off mean in mV
		off_mean_a_mV = ADC_to_mV(adc=float(offsetAEntry.get()), range=vRange)
		off_mean_b_mV = ADC_to_mV(adc=float(offsetBEntry.get()), range=vRange)

		startstopButton.config(text="Stop!", bg="#fa857a")
		stop_thread = False
		the_thread = Thread(target=analyze_files, args=(off_mean_a_mV, off_mean_b_mV, C_a, C_b))
		the_thread.start()		
	else:
		running = False
		stop_thread = True
		startstopButton.config(text="Start!", bg="#e8fcae")

startstopButton = Button(startstopFrame, text="Start!", bg="#e8fcae", command=startstop); startstopButton.grid(row=0,column=2)

# nchannels (binheader)
# t_bin (binheader)
# mVrange (binheader)









root.mainloop()