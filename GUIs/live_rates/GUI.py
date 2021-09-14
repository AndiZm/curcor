import numpy as np
import matplotlib; matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends.backend_tkagg as tkagg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import os
import time
from os import listdir
from os.path import isfile, join
from tkinter import *
from tkinter import filedialog

import live_offset_meas as off
import live_fit_phd as fphd
import live_peakshape as ps
import live_waveform_reader as wv
import live_wait_for_file as wff
import globals as gl
import rate_server as svr
import card_commands as cc

from threading import Thread

############################
## SOME GENERAL FUNCTIONS ##
############################
def ADC_to_mV(adc, range):
	return adc*range/127
def mV_to_ADC(mV, range):
	return mV*127/range
# Two functions to create specific filenames out of existing files
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


root = Tk(); root.wm_title("Almost live measures"); root.geometry("+200+10")

#------------#
# Rate frame #
#------------#
r_width  = 20
r_height = 850
rateFrame = Frame(root); rateFrame.grid(row=0,column=1)
rateACanvas = Canvas(rateFrame, width=r_width, height=r_height, bg="gray"); rateACanvas.grid(row=0,column=0)
rateBCanvas = Canvas(rateFrame, width=r_width, height=r_height, bg="gray"); rateBCanvas.grid(row=0,column=1)
# Forbidden rate area is 20% of rate bar
rateAforb = rateACanvas.create_rectangle(0,0,r_width,0.2*r_height, fill="orange", stipple="gray50")
rateBforb = rateBCanvas.create_rectangle(0,0,r_width,0.2*r_height, fill="orange", stipple="gray50")
# Rate displaying lines
rateALine = rateACanvas.create_line(0,r_height,r_width,r_height, fill="red", width=5)
rateBLine = rateBCanvas.create_line(0,r_height,r_width,r_height, fill="red", width=5)
# Calculate maximum rate
def maxRate(avg_charge):
	return -0.000635 * float(ampAEntry.get()) / avg_charge / gl.o_binning / gl.o_voltages
# Calculate positions of rate lines and place them there
def placeRateLineA(rate):
	lineposition = r_height - (rate/gl.rmax_a * 0.8 * r_height)
	rateACanvas.coords(rateALine, 0, lineposition, r_width, lineposition)
def placeRateLineB(rate):
	lineposition = r_height - (rate/gl.rmax_b * 0.8 * r_height)
	rateBCanvas.coords(rateBLine, 0, lineposition, r_width, lineposition)

rmaxaText = rateACanvas.create_text(r_width/2,0.2*r_height, fill="white", text="--")
rmaxbText = rateBCanvas.create_text(r_width/2,0.2*r_height, fill="white", text="--")


rootMainFrame = Frame(root); rootMainFrame.grid(row=0,column=2)

###################
## DISPLAY FRAME ##
###################
displayFrame = Frame(root); displayFrame.grid(row=0,column=0)
wf_fig = Figure(figsize=(5,5))
wf_a = []
wf_b = []
wf_sub = wf_fig.add_subplot(111)
wf_sub.grid()
gl.wf_a_line, = wf_sub.plot(wf_a)
gl.wf_b_line, = wf_sub.plot(wf_b)
wf_sub.set_xlim(0,1000)
wf_sub.set_ylim(-127,10)
gl.wf_canvas = FigureCanvasTkAgg(wf_fig, master=displayFrame)
gl.wf_canvas.get_tk_widget().grid(row=0,column=0)
gl.wf_canvas.draw()


##################
## COMMON FRAME ##
##################
# The common frame contains the dropdown menu of measurement options
commonFrame = Frame(rootMainFrame); commonFrame.grid(row=0,column=0)

# Samples for each measurement
samples = StringVar(root); samples.set("128 MS")
sampleoptions = {
	"64 S": 64, "128 S": 128, "256 S": 256, "512 S": 512,
	"1 kS": 1024, "2 kS": 2048, "4 kS": 4096, "8 kS": 8192, "16 kS": 16384, "32 kS": 32768, "64 kS": 65536,
	"128 kS": 131072, "256 kS": 262144, "512 kS": 524288,
	"1 MS": 1048576, "2 MS": 2097152, "4 MS": 4194304, "8 MS": 8388608, "16 MS": 16777216, "32 MS": 33554432, "64 MS": 67108864,
	"128 MS": 134217728, "256 MS": 268435456, "512 MS": 536870912,
	"1 GS": 1073741824, "2 GS": 2147483648, "4 GS": 4294967296
}
def new_samples(val):
	gl.o_samples = int((sampleoptions[samples.get()]))
samplesDropdownLabel = Label(commonFrame, text="File Sample Size"); samplesDropdownLabel.grid(row=0,column=0)
samplesDropdown = OptionMenu(commonFrame, samples, *sampleoptions, command=new_samples)
samplesDropdown.grid(row=0, column=1)
# Time binning
binning = StringVar(root); binning.set("1.6 ns")
binningoptions = {"0.8 ns": 0.8e-9, "1.6 ns": 1.6e-9, "3.2 ns": 3.2e-9, "6.4 ns": 6.4e-9}
def new_binning(val):
	gl.o_binning = float((binningoptions[binning.get()]))
binningDropdownLabel = Label(commonFrame, text="Time sampling"); binningDropdownLabel.grid(row=1,column=0)
binningDropdown = OptionMenu(commonFrame, binning, *binningoptions, command=new_binning)
binningDropdown.grid(row=1, column=1)
# Voltage range
voltages = StringVar(root); voltages.set("200 mV")
voltageoptions = {"40 mV": 40, "100 mV": 100, "200 mV": 200, "500 mV": 500}
def new_voltages(val):
	gl.o_voltages = int((voltageoptions[voltages.get()]))
	cc.set_voltage_range(gl.o_voltages)
voltageDropdownLabel = Label(commonFrame, text="Voltage range"); voltageDropdownLabel.grid(row=2,column=0)
voltageDropdown = OptionMenu(commonFrame, voltages, *voltageoptions, command=new_voltages)
voltageDropdown.grid(row=2, column=1)
# Number of channels used for measurement
channels = StringVar(root); channels.set("2")
channeloptions = {"1": 1, "2": 2}
def new_nchn(val):
	gl.o_nchn = int((channeloptions[channels.get()]))
	gl.calc_rate = False
	gl.startstopButton.config(state="disabled")
	singleFileButton.config(state="disabled")
	cc.set_channels(gl.o_nchn)
channelDropdownLabel = Label(commonFrame, text="Channels"); channelDropdownLabel.grid(row=3,column=0)
channelDropdown = OptionMenu(commonFrame, channels, *channeloptions, command=new_nchn)
channelDropdown.grid(row=3, column=1)

# Directory
def selectDirectory():
	root.directoryname = filedialog.askdirectory(initialdir = gl.basicpath, title = "Select any data directory")
	gl.basicpath = root.directoryname; gl.calibpath = gl.basicpath+"/calibs"
	pathLabel.config(text=gl.basicpath.split("/")[1])
	if not os.path.exists(gl.calibpath):
		os.mkdir(gl.calibpath)
pathButton = Button(commonFrame, text="Files directory", command=selectDirectory); pathButton.grid(row=4, column=0)
pathLabel = Label(commonFrame, text=gl.basicpath.split("/")[1]); pathLabel.grid(row=4,column=1)


##################
## OFFSET FRAME ##
##################
offsetFrame = Frame(rootMainFrame, background="#e8fcae"); offsetFrame.grid(row=1,column=0)
offsetHeader = Frame(offsetFrame, background="#e8fcae"); offsetHeader.grid(row=0,column=0)
offsetHeaderLabel = Label(offsetHeader, text="Offset", background="#e8fcae", font=("Helvetica 12 bold")); offsetHeaderLabel.grid(row=0,column=0)
offsetLLabel = Label(offsetHeader, text="l", background="#e8fcae"); offsetLLabel.grid(row=0,column=1)
offsetLEntry = Entry(offsetHeader, width=8); offsetLEntry.grid(row=0,column=2); offsetLEntry.insert(0,"1000000")
offsetPLabel = Label(offsetHeader, text="p", background="#e8fcae"); offsetPLabel.grid(row=0,column=3)
offsetPEntry = Entry(offsetHeader, width=5); offsetPEntry.grid(row=0,column=4); offsetPEntry.insert(0,"2000")

offsetBasicFrame = Frame(offsetFrame, background="#e8fcae"); offsetBasicFrame.grid(row=1,column=0)
# Select offset binary file for offset investigations
def selectOffsetFile():
	root.filename = filedialog.askopenfilename(initialdir = gl.basicpath, title = "Select offset file", filetypes = (("binary files","*.bin"),("all files","*.*")))
	gl.offsetFile = root.filename; offsetFileLabel.config(text=gl.offsetFile.split("/")[-1])
selectOffsetFileButton = Button(offsetBasicFrame, text="Select Offset Binary", background="#e8fcae", command=selectOffsetFile); selectOffsetFileButton.grid(row=1,column=0)
offsetFileLabel = Label(offsetBasicFrame, text="no file selected", background="#e8fcae"); offsetFileLabel.grid(row=1,column=1)
# Load already existing .off or .off1 file
def loadOffset():
	if gl.o_nchn == 2:
		root.filename = filedialog.askopenfilename(initialdir = gl.calibpath, title = "Load offset calculation", filetypes = (("calib files","*.off"),("all files","*.*")))
		gl.offsetLoad = root.filename; loadOffsetLabel.config(text=gl.offsetLoad.split("/")[-1])	
		gl.off_a = np.loadtxt(gl.offsetLoad)[0]; parOffsetLabelA.config(text="{:.2f}".format(gl.off_a))
		gl.off_b = np.loadtxt(gl.offsetLoad)[1]; parOffsetLabelB.config(text="{:.2f}".format(gl.off_b))
	if gl.o_nchn == 1:
		root.filename = filedialog.askopenfilename(initialdir = gl.calibpath, title = "Load offset calculation", filetypes = (("calib files","*.off1"),("all files","*.*")))
		gl.offsetLoad = root.filename; loadOffsetLabel.config(text=gl.offsetLoad.split("/")[-1])	
		gl.off_a = np.loadtxt(gl.offsetLoad); parOffsetLabelA.config(text="{:.2f}".format(gl.off_a))
		parOffsetLabelB.config(text="--")
	gl.offsetFile = to_bin(gl.offsetLoad); offsetFileLabel.config(text=gl.offsetFile.split("/")[-1])
loadOffsetButton = Button(offsetBasicFrame, text="Load Offset", background="#e8fcae", command=loadOffset); loadOffsetButton.grid(row=2,column=0)
loadOffsetLabel = Label(offsetBasicFrame, text="no file selected", background="#e8fcae"); loadOffsetLabel.grid(row=2,column=1)
# Display part of the waveform and horizontal offset lines
def displayOffset():
	wv_off_a, wv_off_b = wv.execute(file=gl.offsetFile, length=int(int(offsetLEntry.get())/10))
	plt.figure("Offset calculations", figsize=(10,6))
	plt.plot(wv_off_a, label="Channel A", color="blue", alpha=0.4); plt.axhline(y=gl.off_a, color="blue")
	if gl.o_nchn == 2:
		plt.plot(wv_off_b, label="Channel B", color="red" , alpha=0.4); plt.axhline(y=gl.off_b, color="red")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(gl.offsetFile); plt.show()
displayOffsetButton = Button(offsetBasicFrame, text="Display Offset", background="#e8fcae", command=displayOffset); displayOffsetButton.grid(row=3, column=0)
# Simply display part of the waveform
def displayWaveformOffset():
	if gl.o_nchn == 2:
		wv_off_a, wv_off_b = wv.execute(file=gl.offsetFile, length=int(int(offsetLEntry.get())/10))
	else:
		wv_off_a = wv.execute(file=gl.offsetFile, length=int(int(offsetLEntry.get())/10))
	plt.figure("Offset file waveforms", figsize=(10,6))
	plt.plot(wv_off_a, label="Channel A", color="blue")
	if gl.o_nchn == 2:
		plt.plot(wv_off_b, label="Channel B", color="red")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(gl.offsetFile); plt.show()
displayWaveformOffsetButton = Button(offsetBasicFrame, text="Display Waveform", background="#e8fcae", command=displayWaveformOffset); displayWaveformOffsetButton.grid(row=3,column=1)

# Do the offset measurement
def off_measurement():
	gl.statusLabel.config(text="Calculate Offset", bg="#edda45"); root.update()
	gl.off_a, gl.off_b = off.execute(file=gl.offsetFile, packet_length=int(offsetLEntry.get()), npackets=int(offsetPEntry.get()))
	if gl.stop_offset_thread==False:
		parOffsetLabelA.config(text="{:.2f}".format(gl.off_a))
		if gl.o_nchn == 2:
			parOffsetLabelB.config(text="{:.2f}".format(gl.off_b))
			outfileOff = to_calib(gl.offsetFile,".off")
			np.savetxt(outfileOff, [gl.off_a, gl.off_b])
		else:
			parOffsetLabelB.config(text="--")
			outfileOff = to_calib(gl.offsetFile,".off1")
			np.savetxt(outfileOff, [gl.off_a])
		gl.offsetLoad = outfileOff; loadOffsetLabel.config(text=gl.offsetLoad.split("/")[-1])
	idle()
def start_offset_thread():
	gl.stop_offset_thread = False
	offset_thread = Thread(target=off_measurement, args=())
	offset_thread.start()
def stop_offset_thread():
	gl.stop_offset_thread = True
	gl.stop_wait_for_file_thread = True
def quickOffset():
	gl.statusLabel.config(text="Offset - wait for file", bg="#edda45")
	gl.offsetFile = wff.execute()
	offsetFileLabel.config(text=gl.offsetFile.split("/")[-1])
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
parOffsetLabelA = Label(offsetParamFrame, text="{:.2f}".format(gl.off_a), background="black", fg="orange"); parOffsetLabelA.grid(row=6,column=1)
parOffsetLabelB = Label(offsetParamFrame, text="{:.2f}".format(gl.off_b), background="black", fg="orange"); parOffsetLabelB.grid(row=6,column=2)

# Offset Start and Stop
offsetDoFrame = Frame(offsetFrame, background="#e8fcae"); offsetDoFrame.grid(row=3,column=0)
offsetButton = Button(offsetDoFrame, text="Calc Offset", background="#e8fcae", command=start_offset_thread); offsetButton.grid(row=0,column=0)
stopOffsetButton = Button(offsetDoFrame, text="Abort", background="#fa857a", command=stop_offset_thread); stopOffsetButton.grid(row=0,column=1)
quickOffsetButton = Button(offsetDoFrame, text="Wait for file", background="#e8fcae", command=start_quick_offset_thread, state="disabled"); quickOffsetButton.grid(row=0,column=2)

#######################
## CALIBRATION FRAME ##
#######################
calibFrame = Frame(rootMainFrame, background="#ccf2ff"); calibFrame.grid(row=2, column=0)
calibHeader = Frame(calibFrame, background="#ccf2ff"); calibHeader.grid(row=0,column=0)
calibHeaderLabel = Label(calibHeader, text="Calibration", background="#ccf2ff", font=("Helvetica 12 bold")); calibHeaderLabel.grid(row=0,column=0)
calibLLabel = Label(calibHeader, text="l", background="#ccf2ff"); calibLLabel.grid(row=0,column=1)
calibLEntry = Entry(calibHeader, width=8); calibLEntry.grid(row=0,column=2); calibLEntry.insert(0,"1000000")
calibPLabel = Label(calibHeader, text="p", background="#ccf2ff"); calibPLabel.grid(row=0,column=3)
calibPEntry = Entry(calibHeader, width=5); calibPEntry.grid(row=0,column=4); calibPEntry.insert(0,"200")

def gauss(x,a,m,s):
	return a * np.exp(-(x-m)**2/2/s/s)
# Display pulse height distribution(s) including fit(s) and pulse shape(s)
def displayCalibration():
	plt.figure("Calibration display", figsize=[10,6])
	plt.subplot(211)
	plt.plot(gl.histo_x,gl.histo_a, color="blue", label="Channel A: Avg height = {:.2f}".format(gl.ph_a), alpha=0.5)
	plt.plot(gl.xplot, gauss(gl.xplot, *gl.pa), color="blue")
	plt.axvline(x=gl.ph_a, color="blue", linestyle="--")
	if gl.o_nchn == 2:
		plt.plot(gl.histo_x,gl.histo_b, color="red", label="Channel B: Avg height = {:.2f}".format(gl.ph_b), alpha=0.5)
		plt.plot(gl.xplot, gauss(gl.xplot, *gl.pb), color="red")
		plt.axvline(x=gl.ph_b, color="red", linestyle="--")
		plt.ylim(0,1.5*max(gl.pa[0],gl.pb[0]))
	else:
		plt.ylim(0,1.5*gl.pa[0])
	plt.xlim(-128,10); plt.legend(); plt.title(gl.calibFile)
	plt.subplot(212)
	plt.plot(gl.ps_x,gl.ps_a, color="blue", label="Channel A: Sum = {:.2f}".format(gl.nsum_a))
	if gl.o_nchn == 2:
		plt.plot(gl.ps_x,gl.ps_b, color="red", label="Channel B: Sum = {:.2f}".format(gl.nsum_b))
	plt.legend(); plt.show()
# Do the whole calibration
def calibrate():
	# Create and fit pulse height distribution
	gl.statusLabel.config(text="Calibrating: Pulse heights ...", bg="#edda45"); root.update()
	fphd.execute(packet_length = int(calibLEntry.get()), npackets=int(calibPEntry.get()), range_a=[float(fitRangelowEntryA.get()),float(fitRangehighEntryA.get())], range_b=[float(fitRangelowEntryB.get()),float(fitRangehighEntryB.get())])
	# Create average pulse shape
	if gl.stop_calib_thread == False:
		gl.statusLabel.config(text="Calibrating: Pulse shape ...", bg="#edda45"); root.update()
		ps.execute(min_pulses = [int(minPulsesEntryA.get()),int(minPulsesEntryB.get())], height=[-1*int(minHeightEntryA.get()),-1*int(minHeightEntryB.get())], cleanheight=[-1*int(cleanHeightEntryA.get()),-1*int(cleanHeightEntryB.get())])
	if gl.stop_calib_thread == False:
		finish_calibration()
	# Activate Rate Buttons
	gl.calc_rate = True
	gl.startstopButton.config(state="normal")
	singleFileButton.config(state="normal")

	idle()
def finish_calibration(): # Execute after pulse height distribution and pulse shape calculation are finished
	# Combine pulse height distribution and pulse shape to calculate avg charge
	gl.avg_charge_a = gl.nsum_a * gl.ph_a; avgChargeLabelA.config(text="{:.2f}".format(gl.avg_charge_a))
	gl.rmax_a = maxRate(gl.avg_charge_a) # Maximum rate
	rateACanvas.itemconfig(rmaxaText, text="{:.0f}".format(gl.rmax_a)) # Show on rate bar
	if gl.o_nchn == 2:
		gl.avg_charge_b = gl.nsum_b * gl.ph_b; avgChargeLabelB.config(text="{:.2f}".format(gl.avg_charge_b))
		gl.rmax_b = maxRate(gl.avg_charge_b) # Maximum rate
		rateBCanvas.itemconfig(rmaxbText, text="{:.0f}".format(gl.rmax_b)) # Show in rate bar
	else:
		avgChargeLabelB.config(text="--")

	# Create calibration files
	if gl.o_nchn == 2:
		np.savetxt(to_calib(gl.calibFile, ".phd"),   np.c_[gl.histo_x,gl.histo_a,gl.histo_b])
		np.savetxt(to_calib(gl.calibFile, ".shape"), np.c_[gl.ps_x, gl.ps_a, gl.ps_b])
		np.savetxt(to_calib(gl.calibFile, ".xplot"), gl.xplot)
		with open(to_calib(gl.calibFile, ".calib"), 'w') as f:
			f.write(str(gl.pa[0]) + "\n" + str(gl.pa[1]) + "\n" + str(gl.pa[2]) + "\n")
			f.write(str(gl.pb[0]) + "\n" + str(gl.pb[1]) + "\n" + str(gl.pb[2]) + "\n")
			f.write(str(gl.nsum_a) + "\n" + str(gl.nsum_b) + "\n")
			f.write(str(gl.ph_a) + "\n" + str(gl.ph_b) + "\n")
			f.write(str(gl.avg_charge_a) + "\n" + str(gl.avg_charge_b) + "\n")
		gl.calibLoad = to_calib(gl.calibFile, ".calib")
	else:
		np.savetxt(to_calib(gl.calibFile, ".phd1"),   np.c_[gl.histo_x,gl.histo_a])
		np.savetxt(to_calib(gl.calibFile, ".shape1"), np.c_[gl.ps_x, gl.ps_a])
		np.savetxt(to_calib(gl.calibFile, ".xplot1"), gl.xplot)
		with open(to_calib(gl.calibFile, ".calib1"), 'w') as f:
			f.write(str(gl.pa[0]) + "\n" + str(gl.pa[1]) + "\n" + str(gl.pa[2]) + "\n")
			f.write(str(gl.nsum_a) + "\n")
			f.write(str(gl.ph_a) + "\n")
			f.write(str(gl.avg_charge_a) + "\n")
		gl.calibLoad = to_calib(gl.calibFile, ".calib1")
	loadCalibLabel.config(text=gl.calibLoad.split("/")[-1])
# Only apply new fit range to calibration data
def calibrate_newFit():
	gl.statusLabel.config(text="New fit range ...", bg="#edda45"); root.update()
	fphd.onlyFit(range_a=[float(fitRangelowEntryA.get()),float(fitRangehighEntryA.get())], range_b=[float(fitRangelowEntryB.get()),float(fitRangehighEntryB.get())])
	finish_calibration()
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
	root.filename = filedialog.askopenfilename(initialdir = gl.basicpath, title = "Select calibration file", filetypes = (("binary files","*.bin"),("all files","*.*")))
	gl.calibFile = root.filename; calibFileLabel.config(text=gl.calibFile.split("/")[-1])
def loadCalibration():
	if gl.o_nchn == 2:
		root.filename = filedialog.askopenfilename(initialdir = gl.calibpath, title = "Load calibration", filetypes = (("calib files","*.calib"),("all files","*.*")))
		gl.calibLoad = root.filename; loadCalibLabel.config(text=gl.calibLoad.split("/")[-1])
		gl.histo_x = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".phd")[:,0]; gl.histo_a = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".phd")[:,1]; gl.histo_b = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".phd")[:,2]
		gl.ps_x = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".shape")[:,0]; gl.ps_a = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".shape")[:,1]; gl.ps_b = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".shape")[:,2]
		gl.xplot = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".xplot")
		gl.pa[0] = np.loadtxt(gl.calibLoad)[0]; gl.pa[1] = np.loadtxt(gl.calibLoad)[1]; gl.pa[2] = np.loadtxt(gl.calibLoad)[2]
		gl.pb[0] = np.loadtxt(gl.calibLoad)[3]; gl.pb[1] = np.loadtxt(gl.calibLoad)[4];	gl.pb[2] = np.loadtxt(gl.calibLoad)[5]
		gl.nsum_a = np.loadtxt(gl.calibLoad)[6]; gl.nsum_b = np.loadtxt(gl.calibLoad)[7]
		gl.ph_a = np.loadtxt(gl.calibLoad)[8]; gl.ph_b = np.loadtxt(gl.calibLoad)[9]
		gl.avg_charge_a = np.loadtxt(gl.calibLoad)[10]; gl.avg_charge_b = np.loadtxt(gl.calibLoad)[11]
		avgChargeLabelA.config(text="{:.2f}".format(gl.avg_charge_a)); avgChargeLabelB.config(text="{:.2f}".format(gl.avg_charge_b))
		gl.rmax_b = maxRate(gl.avg_charge_b) # Maximum rate
		rateBCanvas.itemconfig(rmaxbText, text="{:.0f}".format(gl.rmax_b)) # Show in rate bar
	else:
		root.filename = filedialog.askopenfilename(initialdir = gl.calibpath, title = "Load calibration", filetypes = (("one channel calib files","*.calib1"),("all files","*.*")))
		gl.calibLoad = root.filename; loadCalibLabel.config(text=gl.calibLoad.split("/")[-1])
		gl.histo_x = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".phd1")[:,0]; gl.histo_a = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".phd1")[:,1]
		gl.ps_x = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".shape1")[:,0]; gl.ps_a = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".shape1")[:,1]
		gl.xplot = np.loadtxt(gl.calibLoad[0:gl.calibLoad.find(".")]+".xplot1")
		gl.pa[0] = np.loadtxt(gl.calibLoad)[0]; gl.pa[1] = np.loadtxt(gl.calibLoad)[1]; gl.pa[2] = np.loadtxt(gl.calibLoad)[2]
		gl.nsum_a = np.loadtxt(gl.calibLoad)[3]
		gl.ph_a = np.loadtxt(gl.calibLoad)[4]
		gl.avg_charge_a = np.loadtxt(gl.calibLoad)[5]
		avgChargeLabelA.config(text="{:.2f}".format(gl.avg_charge_a))
		avgChargeLabelB.config(text="--")
	gl.rmax_a = maxRate(gl.avg_charge_a) # Maximum rates
	rateACanvas.itemconfig(rmaxaText, text="{:.0f}".format(gl.rmax_a)) # Show in rate bar
	gl.calibFile = to_bin(gl.calibLoad); calibFileLabel.config(text=gl.calibFile.split("/")[-1])
	# Activate Rate Buttons
	gl.calc_rate = True
	gl.startstopButton.config(state="normal")
	singleFileButton.config(state="normal")


calibGeneralFrame = Frame(calibFrame, background="#ccf2ff"); calibGeneralFrame.grid(row=1,column=0)
selectCalibFileButton = Button(calibGeneralFrame, text="Select Calib Binary", command=selectCalibFile, background="#ccf2ff"); selectCalibFileButton.grid(row=0, column=0)
calibFileLabel = Label(calibGeneralFrame, text="no file selected", background="#ccf2ff"); calibFileLabel.grid(row=0, column=1)
loadCalibButton = Button(calibGeneralFrame, text="Load calibration", command=loadCalibration, background="#ccf2ff"); loadCalibButton.grid(row=1,column=0)
loadCalibLabel = Label(calibGeneralFrame, text="no file selected", background="#ccf2ff"); loadCalibLabel.grid(row=1,column=1)

# Other commands
def displayWaveform():
	wv_a, wv_b = wv.execute(file=gl.calibFile, length=int(int(calibLEntry.get())/10))
	plt.figure("Calibration file waveforms", figsize=(10,6))
	plt.plot(wv_a, label="Channel A", color="blue")
	if gl.o_nchn == 2:
		plt.plot(wv_b, label="Channel B", color="red")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(gl.calibFile); plt.show()
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
cleanHeightEntryA = Entry(calibParamFrame, width=5); cleanHeightEntryA.grid(row=4,column=1); cleanHeightEntryA.insert(0,"-2")
cleanHeightEntryB = Entry(calibParamFrame, width=5); cleanHeightEntryB.grid(row=4,column=2); cleanHeightEntryB.insert(0,"-2")
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
bLabel = Label(abFrame, text="CHN B", font=("Helvetica 10 bold")); bLabel.grid(row=0,column=2)

# Amplifiers
ampLabel = Label(abFrame, text="Amp"); ampLabel.grid(row=1, column=0)
ampAEntry = Entry(abFrame, width=5); ampAEntry.grid(row=1, column=1); ampAEntry.insert(0,"10")
ampBEntry = Entry(abFrame, width=5); ampBEntry.grid(row=1, column=2); ampBEntry.insert(0,"10")

desc_Label_mean = Label(abFrame, text="Voltage [mV]"); desc_Label_mean.grid(row=2, column=0)
desc_Label_curr = Label(abFrame, text="PMT current [µA]"); desc_Label_curr.grid(row=3, column=0)
desc_Label_rate = Label(abFrame, text="Photon rate [MHz]");	desc_Label_rate.grid(row=4, column=0)

CHa_Label_mean = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHa_Label_mean.grid(row=2, column=1)
CHb_Label_mean = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHb_Label_mean.grid(row=2, column=2)

CHa_Label_curr = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHa_Label_curr.grid(row=3, column=1, pady=2)
CHb_Label_curr = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHb_Label_curr.grid(row=3, column=2, pady=2)

CHa_Label_rate = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 12 bold"));	CHa_Label_rate.grid(row=4, column=1, padx=3)
CHb_Label_rate = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 12 bold"));	CHb_Label_rate.grid(row=4, column=2)


#################
## START FRAME ##
#################
startFrame = Frame (rootMainFrame); startFrame.grid(row=5, column=0)
running = False; stop_thread = False; plotting = False; server=None; server_controller=None
# For plotting
rates_a = []; rates_b = []
plotFig = []; rate_a_plot = []; rate_b_plot = []
wav_a = []; wav_b = []

def analysis():
	vRange   = gl.o_voltages
	binRange = gl.o_binning
	mean_a_ADC, mean_b_ADC = cc.take_data()
	#-- Channel A calculations --#
	# Waveform mean
	mean_a_ADC = mean_a_ADC - gl.off_a
	# Rates
	r_a = 1e-6 * mean_a_ADC/(gl.avg_charge_a*binRange)
	CHa_Label_rate.config(text="{:.1f}".format(r_a))
	placeRateLineA(r_a)
	# mV
	mean_a_mV = ADC_to_mV(adc=mean_a_ADC, range=vRange)
	CHa_Label_mean.config(text="{:.2f}".format(mean_a_mV))
	# PMT current
	curr_a_microamp = 1e3 * mean_a_mV/float(ampAEntry.get())/50
	if curr_a_microamp > -100:      
		CHa_Label_curr.config(text="{:.1f}".format(curr_a_microamp), bg="black", fg="orange")
	else:
		CHa_Label_curr.config(text="{:.1f}".format(curr_a_microamp), bg="#edd266", fg="red")

	#-- Channel B calculations --#
	if gl.o_nchn == 2:
		# Waveform mean	
		mean_b_ADC = mean_b_ADC - gl.off_b
		# Rates	
		r_b = 1e-6 * mean_b_ADC/(gl.avg_charge_b*binRange)	
		CHb_Label_rate.config(text="{:.1f}".format(r_b))
		placeRateLineB(r_b)
		# mV	
		mean_b_mV = ADC_to_mV(adc=mean_b_ADC, range=vRange)	
		CHb_Label_mean.config(text="{:.2f}".format(mean_b_mV))
		# PMT current	
		curr_b_microamp = 1e3 * mean_b_mV/float(ampBEntry.get())/50
		if curr_b_microamp > -100:
			CHb_Label_curr.config(text="{:.1f}".format(curr_b_microamp), bg="black", fg="orange")
		else:
			CHb_Label_curr.config(text="{:.1f}".format(curr_b_microamp), bg="#edd266", fg="red")

	if server != None:
		server.sendRate(r_a, r_b)
	if server_controller != None:
		if gl.o_nchn == 1:
			server_controller.sendRate(r_a)
		else:
			server_controller.sendRates(r_a,r_b)
	root.update()
def quick_analysis():
	global stop_thread
	if server_controller != None:
		if gl.o_nchn == 1:
			server_controller.sendMaxRate(gl.rmax_a)
		else:
			server_controller.sendMaxRates(gl.rmax_a, gl.rmax_b)
	while stop_thread == False:
		analysis()
def single_analysis():
	if server_controller != None:
		if gl.o_nchn == 1:
			server_controller.sendMaxRate(gl.rmax_a)
		else:
			server_controller.sendMaxRates(gl.rmax_a, gl.rmax_b)
	analysis()

def analysis_no_rate():
	vRange   = gl.o_voltages
	binRange = gl.o_binning
	mean_a_ADC, mean_b_ADC = cc.take_data()
	#-- Channel A calculations --#
	# Waveform mean
	mean_a_ADC = mean_a_ADC - gl.off_a
	# mV
	mean_a_mV = ADC_to_mV(adc=mean_a_ADC, range=vRange)
	CHa_Label_mean.config(text="{:.2f}".format(mean_a_mV))
	# PMT current
	curr_a_microamp = 1e3 * mean_a_mV/float(ampAEntry.get())/50
	if curr_a_microamp > -100:      
		CHa_Label_curr.config(text="{:.1f}".format(curr_a_microamp), bg="black", fg="orange")
	else:
		CHa_Label_curr.config(text="{:.1f}".format(curr_a_microamp), bg="#edd266", fg="red")

	#-- Channel B calculations --#
	if gl.o_nchn == 2:
		# Waveform mean	
		mean_b_ADC = mean_b_ADC - gl.off_b
		# mV	
		mean_b_mV = ADC_to_mV(adc=mean_b_ADC, range=vRange)	
		CHb_Label_mean.config(text="{:.2f}".format(mean_b_mV))
		# PMT current	
		curr_b_microamp = 1e3 * mean_b_mV/float(ampBEntry.get())/50
		if curr_b_microamp > -100:
			CHb_Label_curr.config(text="{:.1f}".format(curr_b_microamp), bg="black", fg="orange")
		else:
			CHb_Label_curr.config(text="{:.1f}".format(curr_b_microamp), bg="#edd266", fg="red")
	root.update()
def quick_analysis_no_rate():
	global stop_thread
	while stop_thread == False:
		analysis_no_rate()		
def single_analysis_no_rate():
	analysis_no_rate()


def analyze_file(newest_file):
	global stop_thread, plotting, rates_a, rates_b, wav_a, wav_b
	
	gl.statusLabel.config(text="New file found" ); root.update()
	with open(newest_file, 'rb') as f:
		means_a = []; means_b = []
		if gl.o_nchn == 2:
			for allpkt in range(0, int(startstopPEntry.get())):
				buf = (f.read(2*int(startstopLEntry.get())))
				packet = np.frombuffer(buf, dtype=np.int8)
				packet = packet.reshape(int(startstopLEntry.get()), 2)
				a_np = np.array(packet[:,0]); b_np = np.array(packet[:,1])
				means_a.append(np.mean(a_np)); means_b.append(np.mean(b_np))
				del(a_np); del(b_np)
		else:
			for allpkt in range(0, int(startstopPEntry.get())):
				buf = (f.read(1*int(startstopLEntry.get())))
				packet = np.frombuffer(buf, dtype=np.int8)
				a_np = np.array(packet)
				means_a.append(np.mean(a_np))
				del(a_np)

	vRange   = gl.o_voltages
	binRange = gl.o_binning
	
	#-- Channel A calculations --#
	# Waveform mean
	mean_a_ADC = np.mean(means_a)
	mean_a_ADC = mean_a_ADC - gl.off_a
	# Rates
	r_a = 1e-6 * mean_a_ADC/(gl.avg_charge_a*binRange)
	CHa_Label_rate.config(text="{:.1f}".format(r_a))
	placeRateLineA(r_a)
	# mV
	mean_a_mV = ADC_to_mV(adc=mean_a_ADC, range=vRange)
	CHa_Label_mean.config(text="{:.2f}".format(mean_a_mV))
	# PMT current
	curr_a_microamp = 1e3 * mean_a_mV/float(ampAEntry.get())/50
	if curr_a_microamp > -100:      
		CHa_Label_curr.config(text="{:.1f}".format(curr_a_microamp), bg="black", fg="orange")
	else:
		CHa_Label_curr.config(text="{:.1f}".format(curr_a_microamp), bg="#edd266", fg="red")

	#-- Channel B calculations --#
	if gl.o_nchn == 2:
		# Waveform mean
		mean_b_ADC = np.mean(means_b)	
		mean_b_ADC = mean_b_ADC - gl.off_b
		# Rates	
		r_b = 1e-6 * mean_b_ADC/(gl.avg_charge_b*binRange)	
		CHb_Label_rate.config(text="{:.1f}".format(r_b))
		placeRateLineB(r_b)
		# mV	
		mean_b_mV = ADC_to_mV(adc=mean_b_ADC, range=vRange)	
		CHb_Label_mean.config(text="{:.2f}".format(mean_b_mV))
		# PMT current	
		curr_b_microamp = 1e3 * mean_b_mV/float(ampBEntry.get())/50
		if curr_b_microamp > -100:
			CHb_Label_curr.config(text="{:.1f}".format(curr_b_microamp), bg="black", fg="orange")
		else:
			CHb_Label_curr.config(text="{:.1f}".format(curr_b_microamp), bg="#edd266", fg="red")

	if server != None:
		server.sendRate(r_a, r_b)
	if server_controller != None:
			if gl.o_nchn == 1:
				server_controller.sendRate(r_a)
			else:
				server_controller.sendRates(r_a,r_b)
	
	
	root.update()
	# Plot rates and waveform slices
	if plotting == True:
		global rate_a_plot, rate_b_plot, wav_a_plot, wav_b_plot		
		wav_a, wav_b = wv.execute(file=newest_file, length=1000)		
		plotFigAxis.cla(); plotFigAxis.set_xlabel("File index"); plotFigAxis.set_ylabel("Rates [MHz]")
		plotWfAxis.cla(); plotWfAxis.set_xlabel("Time bin"); plotWfAxis.set_ylabel("ADC")

		rates_a.append(r_a)
		rate_a_plot = plotFigAxis.plot(rates_a, "o--", color="blue")
		wav_a_plot = plotWfAxis.plot(wav_a, color="blue")
		if gl.o_nchn == 2:
			rates_b.append(r_b)
			rate_b_plot = plotFigAxis.plot(rates_b, "o--", color="red")
			wav_b_plot = plotWfAxis.plot(wav_b, color="red")

		if len(rates_a) > 200:
			plotFigAxis.set_xlim(len(rates_a)-200,)		
		
		plt.draw()
	root.update()

def analyze_files():
	global stop_thread, plotting, rates_a, rates_b, wav_a, wav_b
	if gl.o_nchn == 1:
		CHb_Label_rate.config(text="-.-")
		CHb_Label_mean.config(text="-.-")
		CHb_Label_curr.config(text="-.-")
	if server_controller != None:
		if gl.o_nchn == 1:
			server_controller.sendMaxRate(gl.rmax_a)
		else:
			server_controller.sendMaxRates(gl.rmax_a, gl.rmax_b)

	while(stop_thread == False):
		gl.statusLabel.config(text="Scanning files for Rates..." ); root.update()
		newest_file = wff.execute()
		if gl.stop_wait_for_file_thread == False:
			analyze_file(newest_file)
			gl.statusLabel.config(text="Scanning files for Rates..." ); root.update()	
			#time.sleep(0.2)

def startstop():
	global running, stop_thread
	if running == False:
		running = True
		gl.act_start_file = True
		if server_controller != None:
			server_controller.sendActionInformation()

		gl.startstopButton.config(text="Stop!", bg="#fa857a")
		stop_thread = False; gl.stop_wait_for_file_thread = False
		gl.statusLabel.config(text="Scanning files for Rates..." , bg="#edda45"); root.update()
		the_thread = Thread(target=analyze_files, args=())
		the_thread.start()		
	else:
		running = False
		gl.act_start_file = False
		if server_controller != None:
			server_controller.sendActionInformation()

		stop_thread = True
		gl.stop_wait_for_file_thread = True
		gl.startstopButton.config(text="Start!", bg="#e8fcae")
		idle()

running_quick = False
def startstop_quick():
	global running_quick, stop_thread
	if running_quick == False:
		running_quick = True
		gl.act_start_quick = True
		if server_controller != None:
			server_controller.sendActionInformation()

		gl.quickRatesButton.config(text="Stop quick", bg="#fa857a")
		stop_thread = False
		gl.statusLabel.config(text="Quick Rate Mode" , bg="#edda45"); root.update()
		if gl.calc_rate == True:
			the_thread = Thread(target=quick_analysis, args=())
		else:
			the_thread = Thread(target=quick_analysis_no_rate, args=())
		the_thread.start()
	else:
		running_quick = False
		gl.act_start_quick = False
		if server_controller != None:
			server_controller.sendActionInformation()
		stop_thread = True
		gl.quickRatesButton.config(text="Start quick", bg="#e8fcae")
		idle()



def switchplot():
	global plotting, plotFig, plotFigAxis, plotWfAxis
	if plotting == False:
		plotting = True
		plotButton.config(text="Plotting on", bg="#edd266")
		plotFig = plt.figure(figsize=(10,6)); plotFigAxis = plotFig.add_subplot(211); plotFigAxis.cla()
		plotFigAxis.set_xlabel("File index"); plotFigAxis.set_ylabel("Rates [MHz]")
		rate_a_plot = plotFigAxis.plot(rates_a, "o--", color="blue", label="Channel A"); rate_b_plot = plotFigAxis.plot(rates_b, "o--", color="red", label="Channel B")
		plt.legend();
		plotWfAxis = plotFig.add_subplot(212); plotWfAxis.cla()
		plotWfAxis.set_xlabel("Time bin"); plotWfAxis.set_ylabel("ADC")
		wav_a_plot = plotWfAxis.plot(wav_a, color="blue"); wav_b_plot = plotWfAxis.plot(wav_b, color="red")
		plt.show()
	else:
		plotting = False
		plt.close(plotFig)
		plotButton.config(text="Plotting off", bg="#cdcfd1")
def clearPlot():
	global rates_a, rates_b, wav_a, wav_b
	rates_a = []; rates_b = []; wav_a = []; wav_b = []
	switchplot(); switchplot()
def singleFileRate():
	global stop_thread, running
	if gl.o_nchn == 1:
		CHb_Label_rate.config(text="-.-")
		CHb_Label_mean.config(text="-.-")
		CHb_Label_curr.config(text="-.-")
	if running == True:
		running = False
		stop_thread = True
		gl.stop_wait_for_file_thread = True
		gl.startstopButton.config(text="Start!", bg="#e8fcae")
	idle()
	root.filename = filedialog.askopenfilename(initialdir = gl.basicpath, title = "Select file for rate", filetypes = (("binary files","*.bin"),("all files","*.*")))
	analyze_file(root.filename)
	idle()

#starts/stops the server which sends the rate to the RASPI
def startStopServerMotor():
	global server
	#check if server is running
	if server == None :	
		#start server
		server=svr.server()
		try:
			server.start()
			#change button label
			gl.motorServerButton.config(text="Stop Server (Motor)", bg="#ffc47d")
		except OSError as err:
			print("The OS did not allow start the server on {0}:{1} . Are address and port correct? Maybe an old instance is still blocking this resource?".format(server.address, server.port))
			print(err)
			server = None
	else:
		#shutdown server
		server.stop()
		#change button label
		gl.motorServerButton.config(text="Start Server (Motor)", bg="#cdcfd1")

		server = None

def startStopServerController():
	global server_controller
	#check if server is running
	if server_controller == None :	
		#start server
		server_controller=svr.server_controller()
		try:
			server_controller.start()
			#change button label
			gl.controllerServerButton.config(text="Stop Server (Controller)", bg="#ffc47d")
		except OSError as err:
			print("The OS did not allow start the server on {0}:{1} . Are address and port correct? Maybe an old instance is still blocking this resource?".format(server.address, server.port))
			print(err)
			server_controller = None
	else:
		#shutdown server
		server_controller.stop()
		#change button label
		gl.controllerServerButton.config(text="Start Server (Controller)", bg="#cdcfd1")
		server_controller = None


clearPlotButon = Button(startFrame, text="Clear", bg="#ccf2ff", command=clearPlot, width=12); clearPlotButon.grid(row=0,column=0)
plotButton = Button(startFrame, text="Plotting off", bg="#cdcfd1", command=switchplot, width=12); plotButton.grid(row=0,column=1)

gl.startstopButton = Button(startFrame, text="Start!", bg="#e8fcae", command=startstop, width=12, state="disabled"); gl.startstopButton.grid(row=1,column=0)
singleFileButton = Button(startFrame, text="Single", bg = "#e8fcae", command=singleFileRate, width=12, state="disabled"); singleFileButton.grid(row=1, column=1)

quickFrame = Frame(rootMainFrame); quickFrame.grid(row=6,column=0)
gl.quickRatesButton = Button(quickFrame, text="Loop quick", bg="#e8fcae", width=9, command=startstop_quick); gl.quickRatesButton.grid(row=0, column=0)
def single():
	if gl.calc_rate == True:
		single_analysis()
	else:
		single_analysis_no_rate()
gl.singleRatesButton = Button(quickFrame, text="Single", width=5, command=single); gl.singleRatesButton.grid(row=0,column=1)
# Samples for quick measurement
samples_quick = StringVar(root); samples_quick.set("16 MS")
sample_quick_options = {
	"1 MS": 1048576, "2 MS": 2097152, "4 MS": 4194304, "8 MS": 8388608,
	"16 MS": 16777216, "32 MS": 33554432, "64 MS": 67108864,
	"128 MS": 134217728, "256 MS": 268435456, "512 MS": 536870912
}
def new_samples_quick(val):
	gl.o_samples_quick = int((sample_quick_options[samples_quick.get()]))
	cc.set_sample_size(gl.o_samples_quick)
samples_quick_Dropdown = OptionMenu(quickFrame, samples_quick, *sample_quick_options, command=new_samples_quick)
samples_quick_Dropdown.grid(row=0, column=2)
##################
## Server Stuff ##
##################
socketFrame = Frame(rootMainFrame, bg="#f7df72"); socketFrame.grid(row=7,column=0)
socketHeaderLabel = Label(socketFrame, text="Network", font=("Helvetica 12 bold"), bg="#f7df72"); socketHeaderLabel.grid(row=0,column=0)
gl.motorServerButton  = Button(socketFrame, text="Start Server (Motor)",      bg="#cdcfd1", command=startStopServerMotor,      width=20); gl.motorServerButton.grid(row=1,column=0)
gl.controllerServerButton = Button(socketFrame, text="Start Server (Controller)", bg="#cdcfd1", command=startStopServerController, width=20); gl.controllerServerButton.grid(row=2,column=0)

#############################
## STATUS FRAME AND BUTTON ##
#############################
statusFrame = Frame (rootMainFrame); statusFrame.grid(row=8, column=0)
gl.statusLabel = Label(statusFrame, text="Starting ...", font=("Helvetica 12 bold"), bg="#ffffff"); gl.statusLabel.grid(row=0, column=0)
def idle():
	gl.statusLabel.config(text="Idle", bg="#ffffff"); root.update()



selectDirectory()
cc.init()
idle()

root.mainloop()
