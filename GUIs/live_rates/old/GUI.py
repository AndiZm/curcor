import numpy as np
#import matplotlib; matplotlib.use("TkAgg")
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#import matplotlib.backends.backend_tkagg as tkagg
#from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import subprocess
import os
import time
from os import listdir
from os.path import isfile, join
from tkinter import *
from tkinter import filedialog
import scipy.signal as ss

import live_offset_meas as off
import live_fit_phd as fphd
import live_peakshape as ps
import live_waveform_reader as wv
import live_wait_for_file as wff
import globals as gl

from threading import Thread

def ADC_to_mV(adc, range):
	return adc*range/127
def mV_to_ADC(mV, range):
	return mV*127/range

root = Tk(); root.wm_title("Almost live measures"); root.geometry("+1600+100")
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
# Binning
binning = StringVar(root); binning.set("1.6 ns")
binningoptions = {"0.8 ns": 0.8e-9, "1.6 ns": 1.6e-9, "3.2 ns": 3.2e-9, "6.4 ns": 6.4e-9}
binningDropdownLabel = Label(commonFrame, text="Time sampling"); binningDropdownLabel.grid(row=1,column=0)
binningDropdown = OptionMenu(commonFrame, binning, *binningoptions)
binningDropdown.grid(row=1, column=1)
# Voltages
voltages = StringVar(root); voltages.set("200 mV")
voltageoptions = {"40 mV": 40, "100 mV": 100, "200 mV": 200, "500 mV": 500}
voltageDropdownLabel = Label(commonFrame, text="Voltage range"); voltageDropdownLabel.grid(row=2,column=0)
voltageDropdown = OptionMenu(commonFrame, voltages, *voltageoptions)
voltageDropdown.grid(row=2, column=1)

# path
basicpath = "E:/"
def selectDirectory():
	global basicpath
	root.directoryname = filedialog.askdirectory(initialdir = basicpath, title = "Select any data directory")
	basicpath = root.directoryname
	pathLabel.config(text=basicpath.split("/")[1])
pathButton = Button(commonFrame, text="Files directory", command=selectDirectory); pathButton.grid(row=3, column=0)
pathLabel = Label(commonFrame, text=basicpath.split("/")[1]); pathLabel.grid(row=3,column=1)

# packet length
packetLengthLabel = Label(commonFrame, text="Packet length"); packetLengthLabel.grid(row=4,column=0)
packetLengthEntry = Entry(commonFrame, width=10); packetLengthEntry.grid(row=4,column=1); packetLengthEntry.insert(0,"1000000")
# npackets
npacketsLabel = Label(commonFrame, text="n Packets"); npacketsLabel.grid(row=5,column=0)
npacketsEntry = Entry(commonFrame, width=10); npacketsEntry.grid(row=5,column=1); npacketsEntry.insert(0,"20")

##################
## OFFSET FRAME ##
##################
offsetFrame = Frame(rootMainFrame, background="#e8fcae"); offsetFrame.grid(row=1,column=0)
offsetHeader = Frame(offsetFrame, background="#e8fcae"); offsetHeader.grid(row=0,column=0)
offsetHeaderLabel = Label(offsetHeader, text="Offset", background="#e8fcae", font=("Helvetica 12 bold")); offsetHeaderLabel.grid(row=0,column=0)
offsetLLabel = Label(offsetHeader, text="l", background="#e8fcae"); offsetLLabel.grid(row=0,column=1)
offsetLEntry = Entry(offsetHeader, width=8); offsetLEntry.grid(row=0,column=2); offsetLEntry.insert(0,"1000000")
offsetPLabel = Label(offsetHeader, text="p", background="#e8fcae"); offsetPLabel.grid(row=0,column=3)
offsetPEntry = Entry(offsetHeader, width=5); offsetPEntry.grid(row=0,column=4); offsetPEntry.insert(0,"200")

off_a = 0.0; off_b = 0.0
offsetBasicFrame = Frame(offsetFrame, background="#e8fcae"); offsetBasicFrame.grid(row=1,column=0)
offsetFile = ""; offsetLoad = ""
def selectOffsetFile():
	global offsetFile
	root.filename = filedialog.askopenfilename(initialdir = basicpath, title = "Select offset file", filetypes = (("binary files","*.bin"),("all files","*.*")))
	offsetFile = root.filename; offsetFileLabel.config(text=offsetFile.split("/")[-1])
selectOffsetFileButton = Button(offsetBasicFrame, text="Select Offset Binary", background="#e8fcae", command=selectOffsetFile); selectOffsetFileButton.grid(row=1,column=0)
offsetFileLabel = Label(offsetBasicFrame, text="no file selected", background="#e8fcae"); offsetFileLabel.grid(row=1,column=1)
def loadOffset():
	global off_a, off_b, offsetFile, offsetLoad
	root.filename = filedialog.askopenfilename(initialdir = basicpath, title = "Load offset calculation", filetypes = (("calib files","*.off"),("all files","*.*")))
	offsetLoad = root.filename; loadOffsetLabel.config(text=offsetLoad.split("/")[-1])	
	off_a = np.loadtxt(offsetLoad)[0]; off_b = np.loadtxt(offsetLoad)[1]	
	parOffsetLabelA.config(text="{:.2f}".format(off_a)); parOffsetLabelB.config(text="{:.2f}".format(off_b))
	offsetFile = offsetLoad[0:offsetLoad.find(".")]+".bin"; offsetFileLabel.config(text=offsetFile.split("/")[-1])
loadOffsetButton = Button(offsetBasicFrame, text="Load Offset", background="#e8fcae", command=loadOffset); loadOffsetButton.grid(row=2,column=0)
loadOffsetLabel = Label(offsetBasicFrame, text="no file selected", background="#e8fcae"); loadOffsetLabel.grid(row=2,column=1)

def displayOffset():
	wv_off_a, wv_off_b = wv.execute(file=offsetFile, length=int(int(offsetLEntry.get())/10))
	plt.figure("Offset calculations", figsize=(10,6))
	plt.plot(wv_off_a, label="Channel A", color="blue", alpha=0.4); plt.plot(wv_off_b, label="Channel B", color="red", alpha=0.4)
	plt.axhline(y=off_a, color="blue"); plt.axhline(y=off_b, color="red")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(offsetFile); plt.show()
displayOffsetButton = Button(offsetBasicFrame, text="Display Offset", background="#e8fcae", command=displayOffset); displayOffsetButton.grid(row=3, column=0)
def displayWaveformOffset():
	wv_off_a, wv_off_b = wv.execute(file=offsetFile, length=int(int(offsetLEntry.get())/10))
	plt.figure("Offset file waveforms", figsize=(10,6))
	plt.plot(wv_off_a, label="Channel A", color="blue"); plt.plot(wv_off_b, label="Channel B", color="red")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(offsetFile); plt.show()
displayWaveformOffsetButton = Button(offsetBasicFrame, text="Display Waveform", background="#e8fcae", command=displayWaveformOffset); displayWaveformOffsetButton.grid(row=3,column=1)

def off_measurement():
	global off_a, off_b
	statusLabel.config(text="Calculate Offset", bg="#edda45"); root.update()
	off_a, off_b = off.execute(file=offsetFile, packet_length=int(offsetLEntry.get()), npackets=int(offsetPEntry.get()))
	if gl.stop_offset_thread==False:
		parOffsetLabelA.config(text="{:.2f}".format(off_a)); parOffsetLabelB.config(text="{:.2f}".format(off_b))
		outfileOff = offsetFile[0:offsetFile.find(".")] + ".off"
		np.savetxt(outfileOff, [off_a, off_b])
		offsetLoad = offsetFile[0:offsetFile.find(".")]+".off"; loadOffsetLabel.config(text=offsetLoad.split("/")[-1])
	idle()
def start_offset_thread():
	gl.stop_offset_thread = False
	offset_thread = Thread(target=off_measurement, args=())
	offset_thread.start()
def stop_offset_thread():
	gl.stop_offset_thread = True
	gl.stop_wait_for_file_thread = True
def quickOffset():
	global offsetFile
	statusLabel.config(text="Offset - wait for file", bg="#edda45")
	offsetFile = wff.execute(basicpath=basicpath, samples=int(sampleoptions[samples.get()]))
	idle()
	if gl.stop_wait_for_file_thread == False:
		start_offset_thread()
def start_quick_offset_thread():
	gl.stop_wait_for_file_thread = False
	gl.stop_offset_thread = False
	quick_offset_thread = Thread(target=quickOffset, args=())
	quick_offset_thread.start()
def stop_quick_offset_thread():
	gl.stop_wait_for_file_thread = True


# Offset parameters
offsetParamFrame = Frame(offsetFrame, background="#e8fcae"); offsetParamFrame.grid(row=2,column=0)
offsetParLabel = Label(offsetParamFrame, text="Parameter", font=("Helvetica 10 bold"), background="#e8fcae"); offsetParLabel.grid(row=0,column=0)
offsetALabel = Label(offsetParamFrame, text="CHN A", font=("Helvetica 10 bold"), background="#e8fcae"); offsetALabel.grid(row=0,column=1)
offsetBLabel = Label(offsetParamFrame, text="CHN B", font=("Helvetica 10 bold"), background="#e8fcae"); offsetBLabel.grid(row=0,column=2)
parOffsetLabel = Label(offsetParamFrame, text="Baseline offset", background="#e8fcae"); parOffsetLabel.grid(row=6,column=0)
parOffsetLabelA = Label(offsetParamFrame, text="{:.2f}".format(off_a), background="black", fg="orange"); parOffsetLabelA.grid(row=6,column=1)
parOffsetLabelB = Label(offsetParamFrame, text="{:.2f}".format(off_b), background="black", fg="orange"); parOffsetLabelB.grid(row=6,column=2)

# Offset Start and Stop
offsetDoFrame = Frame(offsetFrame, background="#e8fcae"); offsetDoFrame.grid(row=3,column=0)
offsetButton = Button(offsetDoFrame, text="Calc Offset", background="#e8fcae", command=start_offset_thread); offsetButton.grid(row=0,column=0)
stopOffsetButton = Button(offsetDoFrame, text="Abort", background="#fa857a", command=stop_offset_thread); stopOffsetButton.grid(row=0,column=1)
quickOffsetButton = Button(offsetDoFrame, text="Wait for file", background="#e8fcae", command=start_quick_offset_thread); quickOffsetButton.grid(row=0,column=2)

#######################
## CALIBRATION FRAME ##
#######################
calibFrame = Frame(rootMainFrame, background="#ccf2ff"); calibFrame.grid(row=2, column=0)
calibHeader = Frame(calibFrame, background="#ccf2ff"); calibHeader.grid(row=0,column=0)
calibHeaderLabel = Label(calibHeader, text="Calibration", background="#ccf2ff", font=("Helvetica 12 bold")); calibHeaderLabel.grid(row=0,column=0)
calibLLabel = Label(calibHeader, text="l", background="#ccf2ff"); calibLLabel.grid(row=0,column=1)
calibLEntry = Entry(calibHeader, width=8); calibLEntry.grid(row=0,column=2); calibLEntry.insert(0,"1000000")
calibPLabel = Label(calibHeader, text="p", background="#ccf2ff"); calibPLabel.grid(row=0,column=3)
calibPEntry = Entry(calibHeader, width=5); calibPEntry.grid(row=0,column=4); calibPEntry.insert(0,"50")
avg_charge_a = []; avg_charge_b = []

# Calibration files
calibFile = ""; calibLoad = ""
histo_x = []; histo_a = []; histo_b = []; pa = [0,0,0]; pb = [0,0,0]; xplot=[]; nsum_a = []; nsum_b = []; ps_a = []; ps_b = []; ps_x = []
ph_a = []; ph_b = []
def gauss(x,a,m,s):
	return a * np.exp(-(x-m)**2/2/s/s)
def displayCalibration():
	plt.figure("Calibration display", figsize=[10,6])
	plt.subplot(211)
	plt.plot(histo_x,histo_a, color="blue", label="Channel A: Avg height = {:.2f}".format(ph_a), alpha=0.5); plt.plot(histo_x,histo_b, color="red", label="Channel B: Avg height = {:.2f}".format(ph_b), alpha=0.5)
	plt.plot(xplot, gauss(xplot, *pa), color="blue"); plt.plot(xplot, gauss(xplot, *pb), color="red")
	plt.axvline(x=ph_a, color="blue", linestyle="--"); plt.axvline(x=ph_b, color="red", linestyle="--")
	plt.ylim(0,1.5*max(pa[0],pb[0])); plt.xlim(-128,10); plt.legend(); plt.title(calibFile)
	plt.subplot(212)
	plt.plot(ps_x,ps_a, color="blue", label="Channel A: Sum = {:.2f}".format(nsum_a)); plt.plot(ps_x,ps_b, color="red", label="Channel B: Sum = {:.2f}".format(nsum_b))
	plt.legend(); plt.show()
def calibrate():
	global histo_x, histo_a, histo_b, pa, pb, xplot, nsum_a, nsum_b, ps_a, ps_b, ps_x, ph_a, ph_b, avg_charge_a, avg_charge_b, calibLoad
	statusLabel.config(text="Calibrating: Pulse heights ...", bg="#edda45"); root.update()
	histo_x, histo_a, histo_b, pa, pb, xplot = fphd.execute(file=calibFile, packet_length = int(calibLEntry.get()), npackets=int(calibPEntry.get()), range_a=[float(fitRangelowEntryA.get()),float(fitRangehighEntryA.get())], range_b=[float(fitRangelowEntryB.get()),float(fitRangehighEntryB.get())])
	if gl.stop_calib_thread == False:
		ph_a = fphd.phd(pa[1],pa[2]); ph_b = fphd.phd(pb[1],pb[2])
	if gl.stop_calib_thread == False:
		statusLabel.config(text="Calibrating: Pulse shape ...", bg="#edda45"); root.update()
	if gl.stop_calib_thread == False:
		nsum_a, nsum_b, ps_x, ps_a, ps_b = ps.execute(file=calibFile, min_pulses = [int(minPulsesEntryA.get()),int(minPulsesEntryB.get())], offset=[off_a,off_b], height=[-1*int(minHeightEntryA.get()),-1*int(minHeightEntryB.get())], cleanheight=[-1*int(cleanHeightEntryA.get()),-1*int(cleanHeightEntryB.get())])
	if gl.stop_calib_thread == False:
		avg_charge_a = nsum_a * ph_a; avg_charge_b = nsum_b * ph_b
		avgChargeLabelA.config(text="{:.2f}".format(avg_charge_a)); avgChargeLabelB.config(text="{:.2f}".format(avg_charge_b))
		outfileCalib = calibFile[0:calibFile.find(".")] + ".calib"
		outfilePHD = calibFile[0:calibFile.find(".")] + ".phd"
		outfilePS = calibFile[0:calibFile.find(".")] + ".shape"
		outfileXPLOT = calibFile[0:calibFile.find(".")] + ".xplot"
		np.savetxt(outfilePHD, np.c_[histo_x,histo_a,histo_b])
		np.savetxt(outfilePS, np.c_[ps_x, ps_a, ps_b])
		np.savetxt(outfileXPLOT, xplot)
		with open(outfileCalib, 'w') as f:
			f.write(str(pa[0]) + "\n" + str(pa[1]) + "\n" + str(pa[2]) + "\n")
			f.write(str(pb[0]) + "\n" + str(pb[1]) + "\n" + str(pb[2]) + "\n")
			f.write(str(nsum_a) + "\n" + str(nsum_b) + "\n")
			f.write(str(ph_a) + "\n" + str(ph_b) + "\n")
			f.write(str(avg_charge_a) + "\n" + str(avg_charge_b) + "\n")
		calibLoad = calibFile[0:calibFile.find(".")]+".calib"; loadCalibLabel.config(text=calibLoad.split("/")[-1])
	idle()
calib_thread = []
def start_calib_thread():
	gl.stop_calib_thread = False
	calib_thread = Thread(target=calibrate, args=())
	calib_thread.start()
def stop_calib_thread():
	gl.stop_calib_thread = True
	gl.stop_wait_for_file_thread = True
def selectCalibFile():
	global calibFile
	root.filename = filedialog.askopenfilename(initialdir = basicpath, title = "Select calibration file", filetypes = (("binary files","*.bin"),("all files","*.*")))
	calibFile = root.filename; calibFileLabel.config(text=calibFile.split("/")[-1])
def loadCalibration():
	root.filename = filedialog.askopenfilename(initialdir = basicpath, title = "Load calibration", filetypes = (("calib files","*.calib"),("all files","*.*")))
	calibLoad = root.filename; loadCalibLabel.config(text=calibLoad.split("/")[-1])
	global histo_x, histo_a, histo_b, pa, pb, xplot, nsum_a, nsum_b, ps_a, ps_b, ps_x, ph_a, ph_b, avg_charge_a, avg_charge_b, calibFile
	histo_x = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,0]; histo_a = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,1]; histo_b = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,2]
	ps_x = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,0]; ps_a = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,1]; ps_b = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,2]
	xplot = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".xplot")
	pa[0] = np.loadtxt(calibLoad)[0]; pa[1] = np.loadtxt(calibLoad)[1]; pa[2] = np.loadtxt(calibLoad)[2]
	pb[0] = np.loadtxt(calibLoad)[3]; pb[1] = np.loadtxt(calibLoad)[4];	pb[2] = np.loadtxt(calibLoad)[5]
	nsum_a = np.loadtxt(calibLoad)[6]; nsum_b = np.loadtxt(calibLoad)[7]
	ph_a = np.loadtxt(calibLoad)[8]; ph_b = np.loadtxt(calibLoad)[9]
	avg_charge_a = np.loadtxt(calibLoad)[10]; avg_charge_b = np.loadtxt(calibLoad)[11]
	avgChargeLabelA.config(text="{:.2f}".format(avg_charge_a)); avgChargeLabelB.config(text="{:.2f}".format(avg_charge_b))
	calibFile = calibLoad[0:calibLoad.find(".")]+".bin"; calibFileLabel.config(text=calibFile.split("/")[-1])
def quickCalibration():
	global calibFile
	statusLabel.config(text="Calibration - wait for file", bg="#edda45")
	calibFile = wff.execute(basicpath=basicpath, samples=int(sampleoptions[samples.get()]))
	idle()
	if gl.stop_wait_for_file_thread == False:
		start_calib_thread()
def start_quick_calib_thread():
	gl.stop_wait_for_file_thread = False
	gl.stop_calib_thread = False
	quick_calib_thread = Thread(target=quickCalibration, args=())
	quick_calib_thread.start()
def stop_quick_calib_thread():
	gl.stop_wait_for_file_thread = True

calibGeneralFrame = Frame(calibFrame, background="#ccf2ff"); calibGeneralFrame.grid(row=1,column=0)
selectCalibFileButton = Button(calibGeneralFrame, text="Select Calib Binary", command=selectCalibFile, background="#ccf2ff"); selectCalibFileButton.grid(row=0, column=0)
calibFileLabel = Label(calibGeneralFrame, text="no file selected", background="#ccf2ff"); calibFileLabel.grid(row=0, column=1)
loadCalibButton = Button(calibGeneralFrame, text="Load calibration", command=loadCalibration, background="#ccf2ff"); loadCalibButton.grid(row=1,column=0)
loadCalibLabel = Label(calibGeneralFrame, text="no file selected", background="#ccf2ff"); loadCalibLabel.grid(row=1,column=1)

# Other commands
def displayWaveform():
	wv_a, wv_b = wv.execute(file=calibFile, length=int(int(calibLEntry.get())/10))
	plt.figure("Calibration file waveforms", figsize=(10,6))
	plt.plot(wv_a, label="Channel A", color="blue"); plt.plot(wv_b, label="Channel B", color="red")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(calibFile); plt.show()
displayCalibrationButton = Button(calibGeneralFrame, text="Display calib", background="#ccf2ff", command=displayCalibration); displayCalibrationButton.grid(row=2,column=0)
displayWaveformButton = Button(calibGeneralFrame, text="Display waveform", background="#ccf2ff", command=displayWaveform); displayWaveformButton.grid(row=2, column=1)

# Calibration parameters
calibParamFrame = Frame(calibFrame, background="#ccf2ff"); calibParamFrame.grid(row=2,column=0)

calibParLabel = Label(calibParamFrame, text="Parameter", font=("Helvetica 10 bold"), background="#ccf2ff"); calibParLabel.grid(row=0,column=0)
calibALabel = Label(calibParamFrame, text="CHN A", font=("Helvetica 10 bold"), background="#ccf2ff"); calibALabel.grid(row=0,column=1)
calibBLabel = Label(calibParamFrame, text="CHN B", font=("Helvetica 10 bold"), background="#ccf2ff"); calibBLabel.grid(row=0,column=2)

fitRangeLowLabel = Label(calibParamFrame, text="lower fit border", background="#7ac5fa"); fitRangeLowLabel.grid(row=1, column=0)
fitRangelowEntryA = Entry(calibParamFrame, width=5); fitRangelowEntryA.grid(row=1, column=1); fitRangelowEntryA.insert(0,"-100")
fitRangelowEntryB = Entry(calibParamFrame, width=5); fitRangelowEntryB.grid(row=1, column=2); fitRangelowEntryB.insert(0,"-100")
fitRangeHighLabel = Label(calibParamFrame, text="upper fit border", background="#7ac5fa"); fitRangeHighLabel.grid(row=2, column=0)
fitRangehighEntryA = Entry(calibParamFrame, width=5); fitRangehighEntryA.grid(row=2, column=1); fitRangehighEntryA.insert(0,"-5")
fitRangehighEntryB = Entry(calibParamFrame, width=5); fitRangehighEntryB.grid(row=2, column=2); fitRangehighEntryB.insert(0,"-5")

minHeightLabel = Label(calibParamFrame, text="Min pulse height", background="#ccf2ff"); minHeightLabel.grid(row=3, column=0)
minHeightEntryA = Entry(calibParamFrame, width=5); minHeightEntryA.grid(row=3,column=1); minHeightEntryA.insert(0,"-25")
minHeightEntryB = Entry(calibParamFrame, width=5); minHeightEntryB.grid(row=3,column=2); minHeightEntryB.insert(0,"-25")
cleanHeightLabel = Label(calibParamFrame, text="Clean pulse height", background="#ccf2ff"); cleanHeightLabel.grid(row=4, column=0)
cleanHeightEntryA = Entry(calibParamFrame, width=5); cleanHeightEntryA.grid(row=4,column=1); cleanHeightEntryA.insert(0,"-3")
cleanHeightEntryB = Entry(calibParamFrame, width=5); cleanHeightEntryB.grid(row=4,column=2); cleanHeightEntryB.insert(0,"-3")
minPulsesLabel = Label(calibParamFrame, text="Min pulses", background="#ccf2ff"); minPulsesLabel.grid(row=5, column=0)
minPulsesEntryA = Entry(calibParamFrame, width=5); minPulsesEntryA.grid(row=5,column=1); minPulsesEntryA.insert(0,"100")
minPulsesEntryB = Entry(calibParamFrame, width=5); minPulsesEntryB.grid(row=5,column=2); minPulsesEntryB.insert(0,"100")

avgChargeLabel = Label(calibParamFrame, text="Avg charge", background="#ccf2ff"); avgChargeLabel.grid(row=6,column=0)
avgChargeLabelA = Label(calibParamFrame, text="--", background="black", fg="orange"); avgChargeLabelA.grid(row=6,column=1)
avgChargeLabelB = Label(calibParamFrame, text="--", background="black", fg="orange"); avgChargeLabelB.grid(row=6,column=2)

# Calibration Start and Stop
calibDoFrame = Frame(calibFrame, background="#ccf2ff"); calibDoFrame.grid(row=3,column=0)
recalibrateButton = Button(calibDoFrame, text="Calibrate", background="#ccf2ff", command=start_calib_thread); recalibrateButton.grid(row=0,column=0)
stopCalibrationButton = Button(calibDoFrame, text="Abort", background="#fa857a", command=stop_calib_thread); stopCalibrationButton.grid(row=0,column=1)
quickCalibButton = Button(calibDoFrame, text="Wait for file", background="#ccf2ff", command=start_quick_calib_thread); quickCalibButton.grid(row=0,column=2)


######################
## START/STOP FRAME ##
######################
startstopFrame = Frame(rootMainFrame); startstopFrame.grid(row=4,column=0)

startstopHeader = Frame(startstopFrame); startstopHeader.grid(row=0,column=0)
startstopHeaderLabel = Label(startstopHeader, text="Rate analysis", font=("Helvetica 12 bold")); startstopHeaderLabel.grid(row=0,column=1)
startstopLLabel = Label(startstopHeader, text="l"); startstopLLabel.grid(row=0,column=2)
startstopLEntry = Entry(startstopHeader, width=8); startstopLEntry.grid(row=0,column=3); startstopLEntry.insert(0,"1000000")
startstopPLabel = Label(startstopHeader, text="p"); startstopPLabel.grid(row=0,column=4)
startstopPEntry = Entry(startstopHeader, width=5); startstopPEntry.grid(row=0,column=5); startstopPEntry.insert(0,"1")

# Param Frame
abFrame = Frame(startstopFrame); abFrame.grid(row=1,column=0)

parLabel = Label(abFrame, text="Parameter", font=("Helvetica 10 bold")); parLabel.grid(row=0,column=0)
aLabel = Label(abFrame, text="CHN A", font=("Helvetica 10 bold")); aLabel.grid(row=0,column=1)
bLabel = Label(abFrame, text="CHN B", font=("Helvetica 10 bold")); bLabel.grid(row=0,column=2)

# Amplifiers
ampLabel = Label(abFrame, text="Amp"); ampLabel.grid(row=1, column=0)
ampAEntry = Entry(abFrame, width=5); ampAEntry.grid(row=1, column=1); ampAEntry.insert(0,"10")
ampBEntry = Entry(abFrame, width=5); ampBEntry.grid(row=1, column=2); ampBEntry.insert(0,"10")

desc_Label_mean = Label(abFrame, text="Voltage [mV]"); desc_Label_mean.grid(row=2, column=0)
desc_Label_curr = Label(abFrame, text="PMT current [µA]"); desc_Label_curr.grid(row=3, column=0)
desc_Label_rate = Label(abFrame, text="Photon rate [MHz]");	desc_Label_rate.grid(row=4, column=0)

CHa_Label_mean = Label(abFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 10 bold")); CHa_Label_mean.grid(row=2, column=1)
CHb_Label_mean = Label(abFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 10 bold")); CHb_Label_mean.grid(row=2, column=2)

CHa_Label_curr = Label(abFrame, text="0.0", fg="red", bg="grey", font=("Helvetica 10 bold")); CHa_Label_curr.grid(row=3, column=1)
CHb_Label_curr = Label(abFrame, text="0.0", fg="red", bg="grey", font=("Helvetica 10 bold")); CHb_Label_curr.grid(row=3, column=2)

CHa_Label_rate = Label(abFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 12 bold"));	CHa_Label_rate.grid(row=4, column=1, padx=3)
CHb_Label_rate = Label(abFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 12 bold"));	CHb_Label_rate.grid(row=4, column=2)


#################
## START FRAME ##
#################
startFrame = Frame (rootMainFrame); startFrame.grid(row=5, column=0)
running = False; stop_thread = False; plotting = False
# For plotting
rates_a = []; rates_b = []
plotFig = []; rate_a_plot = []; rate_b_plot = []

def analyze_files():
	global stop_thread, plotting, rates_a, rates_b

	# Start files which are not to analyze
	startfiles = [f for f in listdir(basicpath) if isfile(join(basicpath, f))]
	filearray = []
	for i in range (0, len(startfiles)):
		if startfiles[i][-4:] == ".bin":
			filearray.append(basicpath + "/" + startfiles[i])

	while(stop_thread == False):
		# Search if new files are available
		current_files = [f for f in listdir(basicpath) if isfile(join(basicpath, f))]    
		newfiles = []; modified = []; new = False
		for i in range (0, len(current_files)):
			cfile = basicpath + "/" + current_files[i]
			if cfile not in filearray and os.stat(cfile).st_size >= (2*int(sampleoptions[samples.get()])) and cfile[-4:] == ".bin":
				filearray.append(cfile); newfiles.append(cfile); modified.append(os.stat(cfile).st_mtime_ns)
				new = True
		# Find newest file and analyze
		if new == True:
			statusLabel.config(text="New file found" ); root.update()
			newest_file = newfiles[np.argmax(modified)]
			new = False

			with open(newest_file, 'rb') as f:
				means_a = []; means_b = []
				for allpkt in range(0, int(startstopPEntry.get())):
					buf = (f.read(2*int(startstopLEntry.get())))
					packet = np.frombuffer(buf, dtype=np.int8)
					packet = packet.reshape(int(startstopLEntry.get()), 2)
					a_np = np.array(packet[:,0]).flatten(); b_np = np.array(packet[:,1]).flatten()
					means_a.append(np.mean(a_np)); means_b.append(np.mean(b_np))
					del(a_np); del(b_np)

			vRange = int(voltageoptions[voltages.get()])
			binRange = float(binningoptions[binning.get()])
	
			mean_a_ADC = np.mean(means_a); mean_b_ADC = np.mean(means_b)
			mean_a_ADC = mean_a_ADC - off_a; mean_b_ADC = mean_b_ADC - off_b
			# Rates 
			r_a = 1e-6 * mean_a_ADC/(avg_charge_a*binRange); r_b = 1e-6 * mean_b_ADC/(avg_charge_b*binRange)
			CHa_Label_rate.config(text="{:.1f}  MHz".format(r_a)); CHb_Label_rate.config(text="{:.1f}  MHz".format(r_b))				
			# mV
			mean_a_mV = ADC_to_mV(adc=mean_a_ADC, range=vRange); mean_b_mV = ADC_to_mV(adc=mean_b_ADC, range=vRange)
			CHa_Label_mean.config(text="{:.2f} mV".format(mean_a_mV)); CHb_Label_mean.config(text="{:.2f} mV".format(mean_b_mV))
			# PMT current
			curr_a_microamp = 1e3 * mean_a_mV/float(ampAEntry.get())/50; curr_b_microamp = 1e3 * mean_b_mV/float(ampBEntry.get())/50        
			CHa_Label_curr.config(text="{:.1f} µA".format(curr_a_microamp)); CHb_Label_curr.config(text="{:.1f} µA".format(curr_b_microamp))			

			root.update()

			if plotting == True:
				rates_a.append(r_a); rates_b.append(r_b)
				global rate_a_plot, rate_b_plot#; rate_a_plot.remove(); rate_b_plot.remove()
				rate_a_plot = plotFigAxis.plot(rates_a, "o--", color="blue"); rate_b_plot = plotFigAxis.plot(rates_b, "o--", color="red")
				plt.draw()
			statusLabel.config(text="Scanning files for Rates..." ); root.update()

		time.sleep(0.5)

def startstop():
	global running, stop_thread
	if running == False:
		running = True

		startstopButton.config(text="Stop!", bg="#fa857a")
		stop_thread = False
		statusLabel.config(text="Scanning files for Rates..." , bg="#edda45"); root.update()
		the_thread = Thread(target=analyze_files, args=())
		the_thread.start()		
	else:
		running = False
		stop_thread = True
		startstopButton.config(text="Start!", bg="#e8fcae")
		idle()

def switchplot():
	global plotting, plotFig, plotFigAxis
	if plotting == False:
		plotting = True
		plotButton.config(text="Plotting on", bg="#edd266")
		plotFig = plt.figure(); plotFigAxis = plotFig.add_subplot(111); plotFigAxis.cla()
		plotFigAxis.set_xlabel("File index"); plotFigAxis.set_ylabel("Rates [MHz]")
		rate_a_plot = plotFigAxis.plot(rates_a, "o--", color="blue", label="Channel A"); rate_b_plot = plotFigAxis.plot(rates_b, "o--", color="red", label="Channel B")
		plt.legend(); plt.show()
	else:
		plotting = False
		plt.close(plotFig)
		plotButton.config(text="Plotting off", bg="#cdcfd1")

plotButton = Button(startFrame, text="Plotting off", bg="#cdcfd1", width=12, command=switchplot); plotButton.grid(row=0,column=0)
startstopButton = Button(startFrame, text="Start!", bg="#e8fcae", command=startstop, width=12); startstopButton.grid(row=0,column=1)


#############################
## STATUS FRAME AND BUTTON ##
#############################
statusFrame = Frame (rootMainFrame); statusFrame.grid(row=6, column=0)
statusLabel = Label(statusFrame, text="Starting ...", font=("Helvetica 12 bold"), bg="#ffffff"); statusLabel.grid(row=0, column=0)
def idle():
	statusLabel.config(text="Idle", bg="#ffffff"); root.update()

selectDirectory()
idle()

root.mainloop()