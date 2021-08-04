import numpy as np
import matplotlib; matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends.backend_tkagg as tkagg
from matplotlib.figure import Figure
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
basicpath = "E:/"; calibpath = basicpath+"/calibs"
def selectDirectory():
	global basicpath, calibpath
	root.directoryname = filedialog.askdirectory(initialdir = basicpath, title = "Select any data directory")
	basicpath = root.directoryname; calibpath = basicpath+"/calibs"
	pathLabel.config(text=basicpath.split("/")[1])
	if not os.path.exists(calibpath):
		os.mkdir(calibpath)
pathButton = Button(commonFrame, text="Files directory", command=selectDirectory); pathButton.grid(row=3, column=0)
pathLabel = Label(commonFrame, text=basicpath.split("/")[1]); pathLabel.grid(row=3,column=1)

def to_calib(file, ending):
	fileparts = file.split("/"); fileparts.insert(-1,"calibs")
	fileparts[-1] = fileparts[-1].split(".")[0] + ending
	filebuild = fileparts[0]
	for i in range (1,len(fileparts)):
		filebuild += "/" + fileparts[i]
	return filebuild
def to_bin(file):
	fileparts = file.split("/"); fileparts.remove("calibs")
	fileparts[-1] = fileparts[-1].split(".")[0] + ".bin"
	filebuild = fileparts[0]
	for i in range (1,len(fileparts)):
		filebuild += "/" + fileparts[i]
	return filebuild


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

off_a = 0.0
offsetBasicFrame = Frame(offsetFrame, background="#e8fcae"); offsetBasicFrame.grid(row=1,column=0)
offsetFile = ""; offsetLoad = ""
def selectOffsetFile():
	global offsetFile
	root.filename = filedialog.askopenfilename(initialdir = basicpath, title = "Select offset file", filetypes = (("binary files","*.bin"),("all files","*.*")))
	offsetFile = root.filename; offsetFileLabel.config(text=offsetFile.split("/")[-1])
selectOffsetFileButton = Button(offsetBasicFrame, text="Select Offset Binary", background="#e8fcae", command=selectOffsetFile); selectOffsetFileButton.grid(row=1,column=0)
offsetFileLabel = Label(offsetBasicFrame, text="no file selected", background="#e8fcae"); offsetFileLabel.grid(row=1,column=1)
def loadOffset():
	global off_a, offsetFile, offsetLoad
	root.filename = filedialog.askopenfilename(initialdir = calibpath, title = "Load offset calculation", filetypes = (("one channel offset files","*.off1"),("all files","*.*")))
	offsetLoad = root.filename; loadOffsetLabel.config(text=offsetLoad.split("/")[-1])	
	off_a = np.loadtxt(offsetLoad)
	parOffsetLabelA.config(text="{:.2f}".format(off_a))
	offsetFile = to_bin(offsetLoad); offsetFileLabel.config(text=offsetFile.split("/")[-1])
loadOffsetButton = Button(offsetBasicFrame, text="Load Offset", background="#e8fcae", command=loadOffset); loadOffsetButton.grid(row=2,column=0)
loadOffsetLabel = Label(offsetBasicFrame, text="no file selected", background="#e8fcae"); loadOffsetLabel.grid(row=2,column=1)

def displayOffset():
	wv_off_a = wv.execute_single(file=offsetFile, length=int(int(offsetLEntry.get())/10))
	plt.figure("Offset calculations", figsize=(10,6))
	plt.plot(wv_off_a, color="blue", alpha=0.4)
	plt.axhline(y=off_a, color="blue")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.title(offsetFile); plt.show()
displayOffsetButton = Button(offsetBasicFrame, text="Display Offset", background="#e8fcae", command=displayOffset); displayOffsetButton.grid(row=3, column=0)
def displayWaveformOffset():
	wv_off_a = wv.execute_single(file=offsetFile, length=int(int(offsetLEntry.get())/10))
	plt.figure("Offset file waveforms", figsize=(10,6))
	plt.plot(wv_off_a, color="blue")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.title(offsetFile); plt.show()
displayWaveformOffsetButton = Button(offsetBasicFrame, text="Display Waveform", background="#e8fcae", command=displayWaveformOffset); displayWaveformOffsetButton.grid(row=3,column=1)

def off_measurement():
	global off_a
	statusLabel.config(text="Calculate Offset", bg="#edda45"); root.update()
	off_a = off.execute_single(file=offsetFile, packet_length=int(offsetLEntry.get()), npackets=int(offsetPEntry.get()))
	if gl.stop_offset_thread==False:
		parOffsetLabelA.config(text="{:.2f}".format(off_a))
		outfileOff = to_calib(offsetFile,".off1")
		np.savetxt(outfileOff, [off_a])
		offsetLoad = outfileOff; loadOffsetLabel.config(text=offsetLoad.split("/")[-1])
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
	offsetFile = wff.execute_single(basicpath=basicpath, samples=int(sampleoptions[samples.get()]))
	offsetFileLabel.config(text=offsetFile.split("/")[-1])
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
parOffsetLabel = Label(offsetParamFrame, text="Baseline offset", background="#e8fcae"); parOffsetLabel.grid(row=6,column=0)
parOffsetLabelA = Label(offsetParamFrame, text="{:.2f}".format(off_a), background="black", fg="orange"); parOffsetLabelA.grid(row=6,column=1)

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
avg_charge_a = []

# Calibration files
calibFile = ""; calibLoad = ""
histo_x = []; histo_a = []; pa = [0,0,0]; xplot=[]; nsum_a = []; ps_a = []; ps_x = []; ph_a = []
def gauss(x,a,m,s):
	return a * np.exp(-(x-m)**2/2/s/s)
def displayCalibration():
	plt.figure("Calibration display", figsize=[10,6])
	plt.subplot(211)
	plt.plot(histo_x,histo_a, color="blue", label="Avg height = {:.2f}".format(ph_a), alpha=0.5)
	plt.plot(xplot, gauss(xplot, *pa), color="blue")
	plt.axvline(x=ph_a, color="blue", linestyle="--")
	plt.ylim(0,1.5*pa[0]); plt.xlim(-128,10); plt.legend(); plt.title(calibFile)
	plt.subplot(212)
	plt.plot(ps_x,ps_a, color="blue", label="Sum = {:.2f}".format(nsum_a))
	plt.legend(); plt.show()
def calibrate():
	global histo_x, histo_a, pa, xplot, nsum_a, ps_a, ps_x, ph_a, avg_charge_a, calibLoad
	statusLabel.config(text="Calibrating: Pulse heights ...", bg="#edda45"); root.update()
	histo_x, histo_a, pa, xplot = fphd.execute_single(file=calibFile, packet_length = int(calibLEntry.get()), npackets=int(calibPEntry.get()), range_a=[float(fitRangelowEntryA.get()),float(fitRangehighEntryA.get())])
	if gl.stop_calib_thread == False:
		ph_a = fphd.phd(pa[1],pa[2])
	if gl.stop_calib_thread == False:
		statusLabel.config(text="Calibrating: Pulse shape ...", bg="#edda45"); root.update()
	if gl.stop_calib_thread == False:
		nsum_a, ps_x, ps_a = ps.execute_single(file=calibFile, min_pulses = int(minPulsesEntryA.get()), offset=off_a, height=-1*int(minHeightEntryA.get()), cleanheight=-1*int(cleanHeightEntryA.get()))
	if gl.stop_calib_thread == False:
		avg_charge_a = nsum_a * ph_a
		avgChargeLabelA.config(text="{:.2f}".format(avg_charge_a))
		outfileCalib = to_calib(calibFile, ".calib1")
		outfilePHD   = to_calib(calibFile, ".phd1")
		outfilePS    = to_calib(calibFile, ".shape1")
		outfileXPLOT = to_calib(calibFile, ".xplot1")
		np.savetxt(outfilePHD, np.c_[histo_x,histo_a])
		np.savetxt(outfilePS, np.c_[ps_x, ps_a])
		np.savetxt(outfileXPLOT, xplot)
		with open(outfileCalib, 'w') as f:
			f.write(str(pa[0]) + "\n" + str(pa[1]) + "\n" + str(pa[2]) + "\n")
			f.write(str(nsum_a) + "\n")
			f.write(str(ph_a) + "\n")
			f.write(str(avg_charge_a) + "\n")
		calibLoad = to_calib(calibFile, ".calib1"); loadCalibLabel.config(text=calibLoad.split("/")[-1])
	idle()
def calibrate_newFit():
	global histo_x, histo_a, pa, xplot, nsum_a, ps_a, ps_x, ph_a, avg_charge_a, calibLoad
	histo_x, histo_a, pa, xplot = fphd.onlyFit_single(a_x=histo_x, a_y=histo_a, range_a=[float(fitRangelowEntryA.get()),float(fitRangehighEntryA.get())])
	ph_a = fphd.phd(pa[1],pa[2])
	avg_charge_a = nsum_a * ph_a
	avgChargeLabelA.config(text="{:.2f}".format(avg_charge_a))
	outfileCalib = to_calib(calibFile, ".calib1")
	outfilePHD   = to_calib(calibFile, ".phd1")
	outfilePS    = to_calib(calibFile, ".shape1")
	outfileXPLOT = to_calib(calibFile, ".xplot1")
	np.savetxt(outfilePHD, np.c_[histo_x,histo_a])
	np.savetxt(outfilePS, np.c_[ps_x, ps_a])
	np.savetxt(outfileXPLOT, xplot)
	with open(outfileCalib, 'w') as f:
		f.write(str(pa[0]) + "\n" + str(pa[1]) + "\n" + str(pa[2]) + "\n")
		f.write(str(nsum_a) + "\n")
		f.write(str(ph_a) + "\n")
		f.write(str(avg_charge_a) + "\n")
	calibLoad = to_calib(calibFile, ".calib1"); loadCalibLabel.config(text=calibLoad.split("/")[-1])
	print ("New fit range applied")
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
	root.filename = filedialog.askopenfilename(initialdir = calibpath, title = "Load calibration", filetypes = (("one channel calib files","*.calib1"),("all files","*.*")))
	calibLoad = root.filename; loadCalibLabel.config(text=calibLoad.split("/")[-1])
	global histo_x, histo_a, pa, xplot, nsum_a, ps_a, ps_x, ph_a, avg_charge_a, calibFile
	histo_x = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd1")[:,0]; histo_a = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd1")[:,1]
	ps_x = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape1")[:,0]; ps_a = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape1")[:,1]
	xplot = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".xplot1")
	pa[0] = np.loadtxt(calibLoad)[0]; pa[1] = np.loadtxt(calibLoad)[1]; pa[2] = np.loadtxt(calibLoad)[2]
	nsum_a = np.loadtxt(calibLoad)[3]
	ph_a = np.loadtxt(calibLoad)[4]
	avg_charge_a = np.loadtxt(calibLoad)[5]
	avgChargeLabelA.config(text="{:.2f}".format(avg_charge_a))
	calibFile = to_bin(calibLoad); calibFileLabel.config(text=calibFile.split("/")[-1])

calibGeneralFrame = Frame(calibFrame, background="#ccf2ff"); calibGeneralFrame.grid(row=1,column=0)
selectCalibFileButton = Button(calibGeneralFrame, text="Select Calib Binary", command=selectCalibFile, background="#ccf2ff"); selectCalibFileButton.grid(row=0, column=0)
calibFileLabel = Label(calibGeneralFrame, text="no file selected", background="#ccf2ff"); calibFileLabel.grid(row=0, column=1)
loadCalibButton = Button(calibGeneralFrame, text="Load calibration", command=loadCalibration, background="#ccf2ff"); loadCalibButton.grid(row=1,column=0)
loadCalibLabel = Label(calibGeneralFrame, text="no file selected", background="#ccf2ff"); loadCalibLabel.grid(row=1,column=1)

# Other commands
def displayWaveform():
	wv_a = wv.execute_single(file=calibFile, length=int(int(calibLEntry.get())/10))
	plt.figure("Calibration file waveforms", figsize=(10,6))
	plt.plot(wv_a, color="blue")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.title(calibFile); plt.show()
displayCalibrationButton = Button(calibGeneralFrame, text="Display calib", background="#ccf2ff", command=displayCalibration); displayCalibrationButton.grid(row=2,column=0)
displayWaveformButton = Button(calibGeneralFrame, text="Display waveform", background="#ccf2ff", command=displayWaveform); displayWaveformButton.grid(row=2, column=1)

# Calibration parameters
calibParamFrame = Frame(calibFrame, background="#ccf2ff"); calibParamFrame.grid(row=2,column=0)

calibParLabel = Label(calibParamFrame, text="Parameter", font=("Helvetica 10 bold"), background="#ccf2ff"); calibParLabel.grid(row=0,column=0)
calibALabel = Label(calibParamFrame, text="CHN A", font=("Helvetica 10 bold"), background="#ccf2ff"); calibALabel.grid(row=0,column=1)

fitRangeLowLabel = Label(calibParamFrame, text="lower fit border", background="#7ac5fa"); fitRangeLowLabel.grid(row=1, column=0)
fitRangelowEntryA = Entry(calibParamFrame, width=5); fitRangelowEntryA.grid(row=1, column=1); fitRangelowEntryA.insert(0,"-100")
fitRangeHighLabel = Label(calibParamFrame, text="upper fit border", background="#7ac5fa"); fitRangeHighLabel.grid(row=2, column=0)
fitRangehighEntryA = Entry(calibParamFrame, width=5); fitRangehighEntryA.grid(row=2, column=1); fitRangehighEntryA.insert(0,"-5")

minHeightLabel = Label(calibParamFrame, text="Min pulse height", background="#ccf2ff"); minHeightLabel.grid(row=3, column=0)
minHeightEntryA = Entry(calibParamFrame, width=5); minHeightEntryA.grid(row=3,column=1); minHeightEntryA.insert(0,"-25")
cleanHeightLabel = Label(calibParamFrame, text="Clean pulse height", background="#ccf2ff"); cleanHeightLabel.grid(row=4, column=0)
cleanHeightEntryA = Entry(calibParamFrame, width=5); cleanHeightEntryA.grid(row=4,column=1); cleanHeightEntryA.insert(0,"-3")
minPulsesLabel = Label(calibParamFrame, text="Min pulses", background="#ccf2ff"); minPulsesLabel.grid(row=5, column=0)
minPulsesEntryA = Entry(calibParamFrame, width=5); minPulsesEntryA.grid(row=5,column=1); minPulsesEntryA.insert(0,"100")

avgChargeLabel = Label(calibParamFrame, text="Avg charge", background="#ccf2ff"); avgChargeLabel.grid(row=6,column=0)
avgChargeLabelA = Label(calibParamFrame, text="--", background="black", fg="orange"); avgChargeLabelA.grid(row=6,column=1)

# Calibration Start and Stop
calibDoFrame = Frame(calibFrame, background="#ccf2ff"); calibDoFrame.grid(row=3,column=0)
recalibrateButton = Button(calibDoFrame, text="Calibrate", background="#ccf2ff", command=start_calib_thread); recalibrateButton.grid(row=0,column=0)
stopCalibrationButton = Button(calibDoFrame, text="Abort", background="#fa857a", command=stop_calib_thread); stopCalibrationButton.grid(row=0,column=1)
CalibFitButton = Button(calibDoFrame, text="Only Fit", background="#ccf2ff", command=calibrate_newFit); CalibFitButton.grid(row=0,column=2)


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

# Amplifiers
ampLabel = Label(abFrame, text="Amp"); ampLabel.grid(row=1, column=0)
ampAEntry = Entry(abFrame, width=5); ampAEntry.grid(row=1, column=1); ampAEntry.insert(0,"10")

desc_Label_mean = Label(abFrame, text="Voltage [mV]"); desc_Label_mean.grid(row=2, column=0)
desc_Label_curr = Label(abFrame, text="PMT current [µA]"); desc_Label_curr.grid(row=3, column=0)
desc_Label_rate = Label(abFrame, text="Photon rate [MHz]");	desc_Label_rate.grid(row=4, column=0)

CHa_Label_mean = Label(abFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 10 bold")); CHa_Label_mean.grid(row=2, column=1)
CHa_Label_curr = Label(abFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 10 bold")); CHa_Label_curr.grid(row=3, column=1, pady=2)
CHa_Label_rate = Label(abFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 12 bold"));	CHa_Label_rate.grid(row=4, column=1, padx=3)


#################
## START FRAME ##
#################
startFrame = Frame (rootMainFrame); startFrame.grid(row=5, column=0)
running = False; stop_thread = False; plotting = False
# For plotting
rates_a = []; plotFig = []; rate_a_plot = []; wav_a = []

def analyze_file(newest_file):
	global stop_thread, plotting, rates_a, wav_a

	statusLabel.config(text="New file found" ); root.update()	
	with open(newest_file, 'rb') as f:
		means_a = []
		for allpkt in range(0, int(startstopPEntry.get())):
			buf = (f.read(int(startstopLEntry.get())))
			packet = np.frombuffer(buf, dtype=np.int8)
			a_np = np.array(packet).flatten()
			means_a.append(np.mean(a_np))
			del(a_np)
	vRange = int(voltageoptions[voltages.get()])
	binRange = float(binningoptions[binning.get()])
	
	mean_a_ADC = np.mean(means_a)
	mean_a_ADC = mean_a_ADC - off_a
	# Rates 
	r_a = 1e-6 * mean_a_ADC/(avg_charge_a*binRange)
	CHa_Label_rate.config(text="{:.1f}".format(r_a))			
	# mV
	mean_a_mV = ADC_to_mV(adc=mean_a_ADC, range=vRange)
	CHa_Label_mean.config(text="{:.2f}".format(mean_a_mV))
	# PMT current
	curr_a_microamp = 1e3 * mean_a_mV/float(ampAEntry.get())/50
	if curr_a_microamp > -100:      
		CHa_Label_curr.config(text="{:.1f}".format(curr_a_microamp), bg="black", fg="orange")
	else:
		CHa_Label_curr.config(text="{:.1f}".format(curr_a_microamp), bg="#edd266", fg="red")
	root.update()
	if plotting == True:
		rates_a.append(r_a)
		wav_a = wv.execute_single(file=newest_file, length=1000)
		global rate_a_plot, wv_a_plot
		plotFigAxis.cla(); plotFigAxis.set_xlabel("File index"); plotFigAxis.set_ylabel("Rates [MHz]")
		rate_a_plot = plotFigAxis.plot(rates_a, "o--", color="blue")
		plotWfAxis.cla(); plotWfAxis.set_xlabel("Time bin"); plotWfAxis.set_ylabel("ADC")
		wv_a_plot = plotWfAxis.plot(wav_a, color="blue");
		plt.draw()
	root.update()

def analyze_files():
	global stop_thread, plotting, rates_a, wav_a

	while(stop_thread == False):
		statusLabel.config(text="Scanning files for Rates..." ); root.update()
		newest_file = wff.execute_single(basicpath=basicpath, samples=int(sampleoptions[samples.get()]))
		if gl.stop_wait_for_file_thread == False:
			analyze_file(newest_file)
			statusLabel.config(text="Scanning files for Rates..." ); root.update()	
			time.sleep(0.2)

def startstop():
	global running, stop_thread
	if running == False:
		running = True

		startstopButton.config(text="Stop!", bg="#fa857a")
		stop_thread = False; gl.stop_wait_for_file_thread = False
		statusLabel.config(text="Scanning files for Rates..." , bg="#edda45"); root.update()
		the_thread = Thread(target=analyze_files, args=())
		the_thread.start()		
	else:
		running = False
		stop_thread = True
		gl.stop_wait_for_file_thread = True
		startstopButton.config(text="Start!", bg="#e8fcae")
		idle()

def switchplot():
	global plotting, plotFig, plotFigAxis, plotWfAxis
	if plotting == False:
		plotting = True
		plotButton.config(text="Plotting on", bg="#edd266")
		plotFig = plt.figure(figsize=(10,6)); plotFigAxis = plotFig.add_subplot(211); plotFigAxis.cla()
		plotFigAxis.set_xlabel("File index"); plotFigAxis.set_ylabel("Rates [MHz]")
		rate_a_plot = plotFigAxis.plot(rates_a, "o--", color="blue")
		plotWfAxis = plotFig.add_subplot(212); plotWfAxis.cla()
		plotWfAxis.set_xlabel("Time bin"); plotWfAxis.set_ylabel("ADC")
		wv_a_plot = plotWfAxis.plot(wav_a, color="blue")
		plt.show()
	else:
		plotting = False
		plt.close(plotFig)
		plotButton.config(text="Plotting off", bg="#cdcfd1")
def clearPlot():
	global rates_a, wav_a
	rates_a = []; wav_a = []
	switchplot(); switchplot()
def singleFileRate():
	global stop_thread, running
	if running == True:
		running = False
		stop_thread = True
		gl.stop_wait_for_file_thread = True
		startstopButton.config(text="Start!", bg="#e8fcae")
	idle()
	root.filename = filedialog.askopenfilename(initialdir = basicpath, title = "Select file for rate", filetypes = (("binary files","*.bin"),("all files","*.*")))
	analyze_file(root.filename)
	idle()

clearPlotButon = Button(startFrame, text="Clear", bg="#ccf2ff", command=clearPlot, width=12); clearPlotButon.grid(row=0,column=0)
plotButton = Button(startFrame, text="Plotting off", bg="#cdcfd1", command=switchplot, width=12); plotButton.grid(row=0,column=1)
startstopButton = Button(startFrame, text="Start!", bg="#e8fcae", command=startstop, width=12); startstopButton.grid(row=1,column=0)
singleFileButton = Button(startFrame, text="Single", bg = "#e8fcae", command=singleFileRate, width=12); singleFileButton.grid(row=1, column=1)


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