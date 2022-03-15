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
import sys
from threading import Thread
import configparser

import live_offset_meas as off
import live_fit_phd as fphd
import live_peakshape as ps
import live_waveform_reader as wv
import live_wait_for_file as wff
import globals as gl
import rate_server as svr

import card_commands as cc
import card_commands2 as cc2

import transfer_files as tf
import live_header as header

import hv_commands as com
import hv_commands2 as com2


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

root = Tk(); root.wm_title("DAQ Control"); root.geometry("+200+10")

#---------------#
# Project frame #
#---------------#
projectFrame = Frame(root); projectFrame.grid(row=0,column=0)
projectLabel = Label(projectFrame, text="Project", font=("Helvetica 12 bold")); projectLabel.grid(row=0,column=0)
copypaths = []

# Assign disks for storage of both cards
global_config = configparser.ConfigParser()
global_config.read('../global.conf')
disk_card1 = str(global_config["controller"]["disk_card1"])
disk_card2 = str(global_config["controller"]["disk_card2"])
print ("Storing data to {}:/ and {}:/".format(disk_card1, disk_card2))

def create_project(name,window):
	if not os.path.exists(disk_card1+":/"+name):
		os.mkdir(disk_card1+":/"+name)
	if not os.path.exists(disk_card2+":/"+name):
		os.mkdir(disk_card2+":/"+name)
	gl.projectName = name
	gl.basicpath  = disk_card1+":/"+name
	gl.basicpath2 = disk_card2+":/"+name
	if not os.path.exists(gl.basicpath+"/calibs"):
		os.mkdir(gl.basicpath+"/calibs")
	if not os.path.exists(gl.basicpath2+"/calibs"):
		os.mkdir(gl.basicpath2+"/calibs")
	gl.calibpath2 = gl.basicpath2+"/calibs"
	if window != None:
		window.destroy()
	projectShowLabel.config(text=name)
def open_project():
	root.directoryname = filedialog.askdirectory(initialdir = disk_card1+":/", title = "Select any project directory")
	gl.basicpath  = root.directoryname; gl.calibpath = gl.basicpath+"/calibs"	
	gl.basicpath2 = disk_card2 + root.directoryname[1:]; gl.calibpath2 = gl.basicpath2+"/calibs"
	name = gl.basicpath.split("/")[-1]
	projectShowLabel.config(text=name)
	create_project(name,None)
def newProject():
	np_dialog = Tk()
	projectNameEntry = Entry(np_dialog); projectNameEntry.grid(row=0,column=0); projectNameEntry.insert(0,"new_project")
	createButton = Button(np_dialog, text="Create", command=lambda:create_project(name=projectNameEntry.get(),window=np_dialog)); createButton.grid(row=0,column=1)
	cancelButton = Button(np_dialog, text="Cancel", command=np_dialog.destroy); cancelButton.grid(row=0,column=2)
	np_dialog.mainloop()
newProjectButton  = Button(projectFrame, text="New Project", command=newProject); newProjectButton.grid(row=0,column=1)
openProjectButton = Button(projectFrame, text="Open Project Folder", command=open_project); openProjectButton.grid(row=0,column=2)
projectShowLabel  = Label(projectFrame, text="no project selected", bg="#f7df72", width=15); projectShowLabel.grid(row=0,column=3,padx=5)

#------------#
# Sync frame #
#------------#
syncFrame = Frame(root); syncFrame.grid(row=1, column=0)

# Last rates
lastA1 = []; lastB1 = []
lastA2 = []; lastB2 = []

measurement = False
def toggle_measure():
	global measurement, tdiffs, timestamps_between, t_stamps
	if measurement == False: # Start measurement
		measurement = True
		singles()
		startStopMeasButton.config(text="Stop Measurement", bg="#f2b4a0")
	elif measurement == True: # Stop measurement
		measurement = False
		startStopMeasButton.config(text="Start Measurement", bg="#92f0eb")
		wait1Canvas.itemconfig(wait1LED, fill="black")
		wait2Canvas.itemconfig(wait2LED, fill="black")
		tdiffs = []; timestamps_between = []; t_stamps = []
		lastA1 = []; lastB1 = []; lastA2 = []; lastB2 = []
def init_measurement():
	gl.syncedMeasButton.invoke()
	gl.syncedMeasButton2.invoke()

measButtonFrame = Frame(syncFrame); measButtonFrame.grid(row=0,column=0)
startStopMeasButton = Button(measButtonFrame, text="Start Measurement", bg="#92f0eb", width=20, height=3, command=toggle_measure)
startStopMeasButton.grid(row=0,column=0)
initMeasButton = Button(measButtonFrame, text="Init new \nmeasurement", height=3, command=init_measurement)
initMeasButton.grid(row=0,column=1)
def enable_buttons():
	initMeasButton.config(state="normal")
	measNameEntry.config(state="normal")
	indexButton.config(state="normal")
def disable_buttons():
	initMeasButton.config(state="disabled")
	measNameEntry.config(state="disabled")
	indexButton.config(state="disabled")

measNameFrame = Frame(measButtonFrame); measNameFrame.grid(row=0,column=2)
measNameEntry = Entry(measNameFrame, width=20); measNameEntry.grid(row=0,column=0, padx=5); measNameEntry.insert(0,"measurement")
indexFrame = Frame(measNameFrame); indexFrame.grid(row=1,column=0)
indexEntry = Entry(indexFrame, width=7); indexEntry.grid(row=0,column=1); indexEntry.insert(0,"0")
def change_index(index):
	indexEntry.delete(0,"end")
	indexEntry.insert(0,"{}".format(index))
def index_up():
	old = int(indexEntry.get())
	change_index(old+1)
def reset_index():
	indexEntry.delete(0,"end")
	indexEntry.insert(0,"0")
indexButton = Button(indexFrame, text="Reset", command=reset_index); indexButton.grid(row=0,column=0)


# Measurement procedure
tdiffs = []; timestamps_between = []; t_stamps = []
awaitR1 = False; awaitR2 = False
def singles():
	theThread = Thread(target=singlesT, args=[])
	theThread.start()
def singlesT():
	global measurement, tdiffs, timestamps_between, t_stamps, awaitR1, awaitR2
	gl.statusLabel.config(text="Remote Measurement", bg="#ff867d")
	gl.statusLabel2.config(text="Remote Measurement", bg="#ff867d")
	disable_buttons()
	time.sleep(0.1)
	
	while measurement == True:
		# Status LEDs to orange
		wait1Canvas.itemconfig(wait1LED, fill="orange")
		wait2Canvas.itemconfig(wait2LED, fill="orange")
		awaitR1 = True; awaitR2 = True
		
		# Send measurement command
		pc1Thread = Thread(target=remote_measurement,  args=(measNameEntry.get(), int(indexEntry.get())))
		pc2Thread = Thread(target=remote_measurement2, args=(measNameEntry.get(), int(indexEntry.get())))

		pc1Thread.start(); pc2Thread.start()
		pc1Thread.join(); pc2Thread.join()

		## Time investigations
		timestamps_between.append(time.time())
		time.sleep(0.1)

		if len(timestamps_between) > 1:
			t_stamps.append(timestamps_between[-1]-timestamps_between[-2])
		else:
			t_stamps.append(4)
		#tdiff = gl.client_PC2.timeR - gl.client_PC1.timeR
		#tdiffs.append(tdiff)
		# Plot
		plot_times.cla(); plot_times.set_xticks([])
		#plot_times.plot(tdiffs, color="blue")
		plot_times2.cla(); plot_times2.set_xticks([])
		plot_times2.plot(t_stamps, color="red")
		if len(tdiffs) > 100:
			#plot_times.set_xlim(len(tdiffs)-99,len(tdiffs))
			plot_times2.set_xlim(len(tdiffs)-99,len(tdiffs))
		plotCanvas.draw()

		index_up()
		
	idle(); idle2()
	enable_buttons()
	

# Plot window
class NavigationToolbar(tkagg.NavigationToolbar2Tk):
	toolitems = [t for t in tkagg.NavigationToolbar2Tk.toolitems if t[0] in ('Home','Pan','Zoom','Save')]


fig = Figure(figsize=(4,0.5))
plot_times = fig.add_subplot(121); plot_times.set_xticks([])
plot_times2 = fig.add_subplot(122); plot_times2.set_xticks([])

plotCanvas = FigureCanvasTkAgg(fig, master=syncFrame)
plotCanvas.get_tk_widget().grid(row=0,column=2)
plotCanvas.draw()

naviFrame = Frame(syncFrame); naviFrame.grid(row=0,column=3)
navi = NavigationToolbar(plotCanvas, naviFrame)


#-------------#
# Cards frame #
#-------------#
cardsFrame = Frame(root, bg="#003366"); cardsFrame.grid(row=2,column=0)
card1Frame = Frame(cardsFrame); card1Frame.grid(row=0, column=0, padx=10, pady=10)
card2Frame = Frame(cardsFrame); card2Frame.grid(row=0, column=1, padx=10, pady=10)

#------------#
# Rate frame #
#------------#
r_width  = 20
r_height = 850

rateFrame = Frame(card1Frame); rateFrame.grid(row=0,column=1)
rateACanvas = Canvas(rateFrame, width=r_width, height=r_height, bg="gray"); rateACanvas.grid(row=0,column=0)
rateBCanvas = Canvas(rateFrame, width=r_width, height=r_height, bg="gray"); rateBCanvas.grid(row=0,column=1)

rateFrame2 = Frame(card2Frame); rateFrame2.grid(row=0,column=1)
rateACanvas2 = Canvas(rateFrame2, width=r_width, height=r_height, bg="gray"); rateACanvas2.grid(row=0,column=0)
rateBCanvas2 = Canvas(rateFrame2, width=r_width, height=r_height, bg="gray"); rateBCanvas2.grid(row=0,column=1)
# Forbidden rate area is 20% of rate bar
rateAforb = rateACanvas.create_rectangle(0,0,r_width,0.2*r_height, fill="orange", stipple="gray50")
rateBforb = rateBCanvas.create_rectangle(0,0,r_width,0.2*r_height, fill="orange", stipple="gray50")

rateAforb2 = rateACanvas2.create_rectangle(0,0,r_width,0.2*r_height, fill="orange", stipple="gray50")
rateBforb2 = rateBCanvas2.create_rectangle(0,0,r_width,0.2*r_height, fill="orange", stipple="gray50")
# Rate displaying lines
rateALine = rateACanvas.create_line(0,r_height,r_width,r_height, fill="red", width=5)
rateBLine = rateBCanvas.create_line(0,r_height,r_width,r_height, fill="red", width=5)

rateALine2 = rateACanvas2.create_line(0,r_height,r_width,r_height, fill="red", width=5)
rateBLine2 = rateBCanvas2.create_line(0,r_height,r_width,r_height, fill="red", width=5)
# Calculate maximum rate
def maxRate(avg_charge):
	return -0.000635 * float(ampAEntry.get()) / avg_charge / gl.o_binning / gl.o_voltages
def maxRate2(avg_charge):
	return -0.000635 * float(ampAEntry2.get()) / avg_charge / gl.o_binning2 / gl.o_voltages2
# Calculate positions of rate lines and place them there
def placeRateLineA(rate):
	lineposition = r_height - (rate/gl.rmax_a * 0.8 * r_height)
	rateACanvas.coords(rateALine, 0, lineposition, r_width, lineposition)
def placeRateLineB(rate):
	lineposition = r_height - (rate/gl.rmax_b * 0.8 * r_height)
	rateBCanvas.coords(rateBLine, 0, lineposition, r_width, lineposition)
def placeRateLineA2(rate):
	lineposition = r_height - (rate/gl.rmax_a2 * 0.8 * r_height)
	rateACanvas2.coords(rateALine2, 0, lineposition, r_width, lineposition)
def placeRateLineB2(rate):
	lineposition = r_height - (rate/gl.rmax_b2 * 0.8 * r_height)
	rateBCanvas2.coords(rateBLine2, 0, lineposition, r_width, lineposition)

rmaxaText = rateACanvas.create_text(r_width/2,0.2*r_height, fill="white", text="--")
rmaxbText = rateBCanvas.create_text(r_width/2,0.2*r_height, fill="white", text="--")

rmaxaText2 = rateACanvas2.create_text(r_width/2,0.2*r_height, fill="white", text="--")
rmaxbText2 = rateBCanvas2.create_text(r_width/2,0.2*r_height, fill="white", text="--")


################
## LEFT FRAME ##
################
leftFrame = Frame(card1Frame); leftFrame.grid(row=0,column=0)
leftFrame2 = Frame(card2Frame); leftFrame2.grid(row=0,column=0)

optionLabel = Label(leftFrame, text="{0} sn {1:05d}\n".format(cc.sCardName,cc.lSerialNumber.value), font=("Helvetica 12 bold")); optionLabel.grid(row=2,column=0)
optionLabel2 = Label(leftFrame2, text="{0} sn {1:05d}\n".format(cc2.sCardName,cc2.lSerialNumber.value), font=("Helvetica 12 bold")); optionLabel2.grid(row=2,column=0)
# Card option Frame #
coptionFrame = Frame(leftFrame); coptionFrame.grid(row=4,column=0)
coptionFrame2 = Frame(leftFrame2); coptionFrame2.grid(row=4,column=0)

# Samples for each measurement
#-1-#
sampleFrame = Frame(coptionFrame); sampleFrame.grid(row=1,column=0)
samples = StringVar(root); samples.set("8 MS")
sampleoptions = {
	"1 MS": 1048576, "2 MS": 2097152, "4 MS": 4194304, "8 MS": 8388608, "16 MS": 16777216, "32 MS": 33554432, "64 MS": 67108864,
	"128 MS": 134217728, "256 MS": 268435456, "512 MS": 536870912,
	"1 GS": 1073741824, "2 GS": 2147483648
}
def new_samples(val):
	gl.o_samples = int((sampleoptions[samples.get()]))
	cc.set_sample_size(gl.o_samples)
samplesDropdownLabel = Label(sampleFrame, text="File Sample Size"); samplesDropdownLabel.grid(row=0,column=0)
samplesDropdown = OptionMenu(sampleFrame, samples, *sampleoptions, command=new_samples)
samplesDropdown.grid(row=0, column=1)

#-2-#
sampleFrame2 = Frame(coptionFrame2); sampleFrame2.grid(row=1,column=0)
samples2 = StringVar(root); samples2.set("8 MS")
sampleoptions2 = {
	"1 MS": 1048576, "2 MS": 2097152, "4 MS": 4194304, "8 MS": 8388608, "16 MS": 16777216, "32 MS": 33554432, "64 MS": 67108864,
	"128 MS": 134217728, "256 MS": 268435456, "512 MS": 536870912,
	"1 GS": 1073741824, "2 GS": 2147483648
}
def new_samples2(val):
	gl.o_samples2 = int((sampleoptions2[samples2.get()]))
	cc2.set_sample_size(gl.o_samples2)
samplesDropdownLabel2 = Label(sampleFrame2, text="File Sample Size"); samplesDropdownLabel2.grid(row=0,column=0)
samplesDropdown2 = OptionMenu(sampleFrame2, samples2, *sampleoptions2, command=new_samples2)
samplesDropdown2.grid(row=0, column=1)

# Sampling
#-1-#
binningFrame = Frame(coptionFrame); binningFrame.grid(row=1,column=1)
binningLabel = Label(binningFrame, text="Time sampling", width=12); binningLabel.grid(row=0,column=0)
binning = DoubleVar(root); binning.set(1.6e-9)
def new_binning():
	gl.o_binning = binning.get()
	cc.set_sampling(gl.o_binning)
binning08Button = Radiobutton(binningFrame, width=6, text="0.8 ns", indicatoron=False, variable=binning, value=0.8e-9, command=new_binning); binning08Button.grid(row=0,column=1)
binning16Button = Radiobutton(binningFrame, width=6, text="1.6 ns", indicatoron=False, variable=binning, value=1.6e-9, command=new_binning); binning16Button.grid(row=0,column=2)
binning32Button = Radiobutton(binningFrame, width=6, text="3.2 ns", indicatoron=False, variable=binning, value=3.2e-9, command=new_binning); binning32Button.grid(row=0,column=3)
binning64Button = Radiobutton(binningFrame, width=6, text="6.4 ns", indicatoron=False, variable=binning, value=6.4e-9, command=new_binning); binning64Button.grid(row=0,column=4)
#-2-#
binningFrame2 = Frame(coptionFrame2); binningFrame2.grid(row=1,column=1)
binningLabel2 = Label(binningFrame2, text="Time sampling", width=12); binningLabel2.grid(row=0,column=0)
binning2 = DoubleVar(root); binning2.set(1.6e-9)
def new_binning2():
	gl.o_binning2 = binning2.get()
	cc2.set_sampling(gl.o_binning2)
binning08Button2 = Radiobutton(binningFrame2, width=6, text="0.8 ns", indicatoron=False, variable=binning2, value=0.8e-9, command=new_binning2); binning08Button2.grid(row=0,column=1)
binning16Button2 = Radiobutton(binningFrame2, width=6, text="1.6 ns", indicatoron=False, variable=binning2, value=1.6e-9, command=new_binning2); binning16Button2.grid(row=0,column=2)
binning32Button2 = Radiobutton(binningFrame2, width=6, text="3.2 ns", indicatoron=False, variable=binning2, value=3.2e-9, command=new_binning2); binning32Button2.grid(row=0,column=3)
binning64Button2 = Radiobutton(binningFrame2, width=6, text="6.4 ns", indicatoron=False, variable=binning2, value=6.4e-9, command=new_binning2); binning64Button2.grid(row=0,column=4)

# Voltage range
#-1-#
voltageFrame = Frame(coptionFrame); voltageFrame.grid(row=2,column=1)
voltageLabel = Label(voltageFrame, text="Voltage range", width=12); voltageLabel.grid(row=0,column=0)
voltages = IntVar(root); voltages.set(200)
def new_voltages():
	gl.o_voltages = voltages.get()
	cc.set_voltage_range(gl.o_voltages)
voltage040Button = Radiobutton(voltageFrame, width=6, text=" 40 mV", indicatoron=False, variable=voltages, value= 40, command=new_voltages); voltage040Button.grid(row=0,column=1)
voltage100Button = Radiobutton(voltageFrame, width=6, text="100 mV", indicatoron=False, variable=voltages, value=100, command=new_voltages); voltage100Button.grid(row=0,column=2)
voltage200Button = Radiobutton(voltageFrame, width=6, text="200 mV", indicatoron=False, variable=voltages, value=200, command=new_voltages); voltage200Button.grid(row=0,column=3)
voltage500Button = Radiobutton(voltageFrame, width=6, text="500 mV", indicatoron=False, variable=voltages, value=500, command=new_voltages); voltage500Button.grid(row=0,column=4)
#-2-#
voltageFrame2 = Frame(coptionFrame2); voltageFrame2.grid(row=2,column=1)
voltageLabel2 = Label(voltageFrame2, text="Voltage range", width=12); voltageLabel2.grid(row=0,column=0)
voltages2 = IntVar(root); voltages2.set(200)
def new_voltages2():
	gl.o_voltages2 = voltages2.get()
	cc2.set_voltage_range(gl.o_voltages2)
voltage040Button2 = Radiobutton(voltageFrame2, width=6, text=" 40 mV", indicatoron=False, variable=voltages2, value= 40, command=new_voltages2); voltage040Button2.grid(row=0,column=1)
voltage100Button2 = Radiobutton(voltageFrame2, width=6, text="100 mV", indicatoron=False, variable=voltages2, value=100, command=new_voltages2); voltage100Button2.grid(row=0,column=2)
voltage200Button2 = Radiobutton(voltageFrame2, width=6, text="200 mV", indicatoron=False, variable=voltages2, value=200, command=new_voltages2); voltage200Button2.grid(row=0,column=3)
voltage500Button2 = Radiobutton(voltageFrame2, width=6, text="500 mV", indicatoron=False, variable=voltages2, value=500, command=new_voltages2); voltage500Button2.grid(row=0,column=4)

# Channels
#-1-#
channelFrame = Frame(coptionFrame); channelFrame.grid(row=2,column=0)
channelLabel = Label(channelFrame, text="Channels"); channelLabel.grid(row=0,column=0)
channels = IntVar(root); channels.set(2)
def new_nchn():
	ch_old = gl.o_nchn
	ch_new = channels.get()
	if ch_new != ch_old:
		gl.o_nchn = ch_new
		gl.calc_rate = False
		cc.set_channels(gl.o_nchn)
channel1Button = Radiobutton(channelFrame, width=5, text="1", indicatoron=False, variable=channels, value=1, command=new_nchn); channel1Button.grid(row=0,column=1)
channel2Button = Radiobutton(channelFrame, width=5, text="2", indicatoron=False, variable=channels, value=2, command=new_nchn); channel2Button.grid(row=0,column=2)
#-2-#
channelFrame2 = Frame(coptionFrame2); channelFrame2.grid(row=2,column=0)
channelLabel2 = Label(channelFrame2, text="Channels"); channelLabel2.grid(row=0,column=0)
channels2 = IntVar(root); channels2.set(2)
def new_nchn2():
	ch_old = gl.o_nchn2
	ch_new = channels2.get()
	if ch_new != ch_old:
		gl.o_nchn2 = ch_new
		gl.calc_rate2 = False
		cc2.set_channels(gl.o_nchn2)
channel1Button2 = Radiobutton(channelFrame2, width=5, text="1", indicatoron=False, variable=channels2, value=1, command=new_nchn2); channel1Button2.grid(row=0,column=1)
channel2Button2 = Radiobutton(channelFrame2, width=5, text="2", indicatoron=False, variable=channels2, value=2, command=new_nchn2); channel2Button2.grid(row=0,column=2)

# Clock
#-1-#
clockFrame = Frame(coptionFrame); clockFrame.grid(row=3,column=0)
clockmodeLabel = Label(clockFrame, text="Clock"); clockmodeLabel.grid(row=0,column=0)
gl.clockmode = IntVar(); gl.clockmode.set(2)
clockInternButton = Radiobutton(clockFrame, width=8, text="Internal", indicatoron=False, variable=gl.clockmode, value=1, command=cc.set_clockmode); clockInternButton.grid(row=0,column=1)
clockExternButton = Radiobutton(clockFrame, width=8, text="External", indicatoron=False, variable=gl.clockmode, value=2, command=cc.set_clockmode); clockExternButton.grid(row=0,column=2)
#-2-#
clockFrame2 = Frame(coptionFrame2); clockFrame2.grid(row=3,column=0)
clockmodeLabel2 = Label(clockFrame2, text="Clock"); clockmodeLabel2.grid(row=0,column=0)
gl.clockmode2 = IntVar(); gl.clockmode2.set(2)
clockInternButton2 = Radiobutton(clockFrame2, width=8, text="Internal", indicatoron=False, variable=gl.clockmode2, value=1, command=cc2.set_clockmode); clockInternButton2.grid(row=0,column=1)
clockExternButton2 = Radiobutton(clockFrame2, width=8, text="External", indicatoron=False, variable=gl.clockmode2, value=2, command=cc2.set_clockmode); clockExternButton2.grid(row=0,column=2)

# Trigger
#-1-#
triggerFrame = Frame(coptionFrame); triggerFrame.grid(row=3,column=1)
triggerLabel = Label(triggerFrame, text="External Trigger"); triggerLabel.grid(row=0,column=0)
def toggle_trigger():
	if gl.trigger == False:
		gl.trigger = True
		triggerButton.config(text="On")
	elif gl.trigger == True:
		gl.trigger = False
		triggerButton.config(text="Off")
	cc.set_triggermode()
triggerButton = Button(triggerFrame, text="Off", width=5, command=toggle_trigger); triggerButton.grid(row=0,column=1)
#-2-#
triggerFrame2 = Frame(coptionFrame2); triggerFrame2.grid(row=3,column=1)
triggerLabel2 = Label(triggerFrame2, text="External Trigger"); triggerLabel2.grid(row=0,column=0)
def toggle_trigger2():
	if gl.trigger2 == False:
		gl.trigger2 = True
		triggerButton2.config(text="On")
	elif gl.trigger2 == True:
		gl.trigger2 = False
		triggerButton2.config(text="Off")
	cc2.set_triggermode()
triggerButton2 = Button(triggerFrame2, text="Off", width=5, command=toggle_trigger2); triggerButton2.grid(row=0,column=1)

# Quick settings
#-1-#
qsettingsFrame = Frame(leftFrame); qsettingsFrame.grid(row=3,column=0)
def qsettings_checkWaveform():
	samples.set("8 MS"); new_samples(0)
	binning16Button.invoke()
	voltage200Button.invoke()
	if gl.trigger == True:
		toggle_trigger()
	cc.init_display()
def qsettings_syncedMeasurement():
	samples.set("2 GS"); new_samples(0)
	binning16Button.invoke()
	voltage200Button.invoke()
	clockExternButton.invoke()
	if gl.trigger == False:
		toggle_trigger()
	cc.init_storage()
def qsettings_calibrations():
	samples.set("2 GS"); new_samples(0)
	binning16Button.invoke()
	voltage200Button.invoke()
	clockExternButton.invoke()
	if gl.trigger == True:
		toggle_trigger()
	cc.init_storage()
quickSettingsLabel = Label(qsettingsFrame, text="Quick Settings", bg="#f5dbff"); quickSettingsLabel.grid(row=1,column=0)
checkWaveformsButton = Button(qsettingsFrame, bg="#f5dbff", width=18, text="Standard Observe",   command=qsettings_checkWaveform); checkWaveformsButton.grid(row=1,column=1)
calibrationsButton   = Button(qsettingsFrame, bg="#f5dbff", width=12, text="Calibrations",       command=qsettings_calibrations); calibrationsButton.grid(row=1,column=2)
gl.syncedMeasButton     = Button(qsettingsFrame, bg="#f5dbff", width=20, text="Synced Measurement", command=qsettings_syncedMeasurement); gl.syncedMeasButton.grid(row=1,column=3)
#-2-#
qsettingsFrame2 = Frame(leftFrame2); qsettingsFrame2.grid(row=3,column=0)
def qsettings_checkWaveform2():
	samples2.set("8 MS"); new_samples2(0)
	binning16Button2.invoke()
	voltage200Button2.invoke()
	if gl.trigger2 == True:
		toggle_trigger2()
	cc2.init_display()
def qsettings_syncedMeasurement2():
	samples2.set("2 GS"); new_samples2(0)
	binning16Button2.invoke()
	voltage200Button2.invoke()
	clockExternButton2.invoke()
	if gl.trigger2 == False:
		toggle_trigger2()
	cc2.init_storage()
def qsettings_calibrations2():
	samples2.set("2 GS"); new_samples2(0)
	binning16Button2.invoke()
	voltage200Button2.invoke()
	clockExternButton2.invoke()
	if gl.trigger2 == True:
		toggle_trigger2()
	cc2.init_storage()
quickSettingsLabel2 = Label(qsettingsFrame2, text="Quick Settings", bg="#f5dbff"); quickSettingsLabel2.grid(row=1,column=0)
checkWaveformsButton2 = Button(qsettingsFrame2, bg="#f5dbff", width=18, text="Standard Observe",   command=qsettings_checkWaveform2); checkWaveformsButton2.grid(row=1,column=1)
calibrationsButton2   = Button(qsettingsFrame2, bg="#f5dbff", width=12, text="Calibrations",       command=qsettings_calibrations2); calibrationsButton2.grid(row=1,column=2)
gl.syncedMeasButton2     = Button(qsettingsFrame2, bg="#f5dbff", width=20, text="Synced Measurement", command=qsettings_syncedMeasurement2); gl.syncedMeasButton2.grid(row=1,column=3)

# Measurement Frame
#-1-#
measurementLabel = Label(leftFrame, text="Measurement Control", font=("Helvetica 12 bold")); measurementLabel.grid(row=5,column=0)
measurementFrame = Frame(leftFrame); measurementFrame.grid(row=6,column=0)
def takeMeasurement():
	cc.init_storage()
	filename = gl.basicpath + "/" + measFileNameEntry.get() + ".bin"
	ma, mb = cc.measurement(filename)
	calculate_data(ma, mb)
	cc.init_display()
singleMeasurementButton = Button(measurementFrame, text="Single Measurement", command=takeMeasurement); singleMeasurementButton.grid(row=0,column=0)
measloop = False
def loopMeasurement():
	global measloop
	if measloop == False:
		measloop = True
		loopMeasurementButton.config(text="Stop loop", bg="#fa857a")
		loopThread = Thread(target=doLoopMeasurement)
		loopThread.start()
	elif measloop == True:
		measloop = False
		loopMeasurementButton.config(text="Start loop", bg="#e8fcae")
def doLoopMeasurement():
	global measloop
	cc.init_storage()
	header.write_header(name=measFileNameEntry.get())
	fileindex = 0
	while measloop == True:
		filename = gl.basicpath + "/" + measFileNameEntry.get() + "_" + tf.numberstring(fileindex) + ".bin"
		ma, mb = cc.measurement(filename)
		calculate_data(ma, mb)
		fileindex += 1	
	cc.init_display()
loopMeasurementButton = Button(measurementFrame, text="Start Loop", width=10, bg="#e8fcae", command=loopMeasurement); loopMeasurementButton.grid(row=0,column=1)
measFileNameEntry = Entry(measurementFrame, width=15); measFileNameEntry.grid(row=0,column=2,padx=5); measFileNameEntry.insert(0,"data")
def remote_measurement(name, index):
	global awaitR1
	filename = gl.basicpath + "/" + name + "_" + tf.numberstring(index) + ".bin"
	ma, mb = cc.measurement(filename)
	calculate_data(ma, mb)
	awaitR1 = False; wait1Canvas.itemconfig(wait1LED, fill="green"); root.update()

#-2-#
measurementLabel2 = Label(leftFrame2, text="Measurement Control", font=("Helvetica 12 bold")); measurementLabel2.grid(row=5,column=0)
measurementFrame2 = Frame(leftFrame2); measurementFrame2.grid(row=6,column=0)
def takeMeasurement2():
	cc2.init_storage()
	filename = gl.basicpath2 + "/" + measFileNameEntry2.get() + ".bin"
	ma, mb = cc2.measurement(filename)
	calculate_data2(ma, mb)
	cc2.init_display()
singleMeasurementButton2 = Button(measurementFrame2, text="Single Measurement", command=takeMeasurement2); singleMeasurementButton2.grid(row=0,column=0)
measloop2 = False
def loopMeasurement2():
	global measloop2
	if measloop2 == False:
		measloop2 = True
		loopMeasurementButton2.config(text="Stop loop", bg="#fa857a")
		loopThread2 = Thread(target=doLoopMeasurement2)
		loopThread2.start()
	elif measloop2 == True:
		measloop2 = False
		loopMeasurementButton2.config(text="Start loop", bg="#e8fcae")
def doLoopMeasurement2():
	global measloop2
	cc2.init_storage()
	header.write_header2(name=measFileNameEntry2.get())
	fileindex2 = 0
	while measloop2 == True:
		filename2 = gl.basicpath2 + "/" + measFileNameEntry2.get() + "_" + tf.numberstring(fileindex2) + ".bin"
		ma2, mb2 = cc2.measurement(filename2)
		calculate_data2(ma2, mb2)
		fileindex2 += 1
	cc2.init_display()
loopMeasurementButton2 = Button(measurementFrame2, text="Start Loop", width=10, bg="#e8fcae", command=loopMeasurement2); loopMeasurementButton2.grid(row=0,column=1)
measFileNameEntry2 = Entry(measurementFrame2, width=15); measFileNameEntry2.grid(row=0,column=2,padx=5); measFileNameEntry2.insert(0,"data")
def remote_measurement2(name, index):
	filename2 = gl.basicpath2 + "/" + name + "_" + tf.numberstring(index) + ".bin"
	ma2, mb2 = cc2.measurement(filename2)
	calculate_data2(ma2, mb2)
	awaitR2 = False; wait2Canvas.itemconfig(wait2LED, fill="green"); root.update()

# Display Frame #
#-1-#
displayFrame = Frame(leftFrame); displayFrame.grid(row=7,column=0)
wf_fig = Figure(figsize=(5,5))
# Plot waveforms
wf_a = []; wf_b = []
wf_sub = wf_fig.add_subplot(211); wf_sub.grid()
gl.wf_a_line, = wf_sub.plot(wf_a); gl.wf_b_line, = wf_sub.plot(wf_b)
wf_sub.set_xlim(0,1000); wf_sub.set_ylim(-127,10)
# Plot rates
rates_a = []; rates_b = []
rates_sub = wf_fig.add_subplot(212); rates_sub.grid()
gl.rates_a_line, = rates_sub.plot(gl.rates_a); gl.rates_b_line, = rates_sub.plot(gl.rates_b)
rates_sub.set_xlim(-99,0)
gl.wf_canvas = FigureCanvasTkAgg(wf_fig, master=displayFrame)
gl.wf_canvas.get_tk_widget().grid(row=0,column=0)
gl.wf_canvas.draw()
def update_rate_plot():
	gl.update_rate_plot()
	rates_sub.set_ylim( np.min( [np.min(gl.rates_a),np.min(gl.rates_b)] ), np.max( [np.max(gl.rates_a),np.max(gl.rates_b)]) )
#-2-#
displayFrame2 = Frame(leftFrame2); displayFrame2.grid(row=7,column=0)
wf_fig2 = Figure(figsize=(5,5))
# Plot waveforms
wf_a2 = []; wf_b2 = []
wf_sub2 = wf_fig2.add_subplot(211); wf_sub2.grid()
gl.wf_a_line2, = wf_sub2.plot(wf_a2); gl.wf_b_line2, = wf_sub2.plot(wf_b2)
wf_sub2.set_xlim(0,1000); wf_sub2.set_ylim(-127,10)
# Plot rates
rates_a2 = []; rates_b2 = []
rates_sub2 = wf_fig2.add_subplot(212); rates_sub2.grid()
gl.rates_a_line2, = rates_sub2.plot(gl.rates_a2); gl.rates_b_line2, = rates_sub2.plot(gl.rates_b2)
rates_sub2.set_xlim(-99,0)
gl.wf_canvas2 = FigureCanvasTkAgg(wf_fig2, master=displayFrame2)
gl.wf_canvas2.get_tk_widget().grid(row=0,column=0)
gl.wf_canvas2.draw()
def update_rate_plot2():
	gl.update_rate_plot2()
	rates_sub2.set_ylim( np.min( [np.min(gl.rates_a2),np.min(gl.rates_b2)] ), np.max( [np.max(gl.rates_a2),np.max(gl.rates_b2)]) )

##############
## HV FRAME ##
##############
#-1-#
hvaddress_1 = global_config["controller"]["hv_address_card1"]

hvFrame = Frame(leftFrame, bg="#003366"); hvFrame.grid(row=8, column=0)
hvMainFrame = Frame(hvFrame, bg="#003366"); hvMainFrame.grid(row=0,column=1)

gl.hv0Button = Button(hvMainFrame, text="HV 0", font=("Helvetica 12 bold"), bg="grey", command=com.toggle_0); gl.hv0Button.grid(row=0,column=2)
gl.hv1Label = Label(hvMainFrame, text="HV 1", font=("Helvetica 8 italic"), bg="grey"); gl.hv1Label.grid(row=0,column=3)
gl.hv2Button = Button(hvMainFrame, text="HV 2", font=("Helvetica 12 bold"), bg="grey", command=com.toggle_2); gl.hv2Button.grid(row=0,column=4)
gl.hv3Label = Label(hvMainFrame, text="HV 3", font=("Helvetica 8 italic"), bg="grey"); gl.hv3Label.grid(row=0,column=5)
def enableElements(frame):
	frame.config(bg="#003366")
	for child in frame.winfo_children():
		if child.winfo_class() not in ("Frame","Labelframe"):
			child.configure(state="normal")
def disableElements(frame):
	frame.config(bg="grey")
	for child in frame.winfo_children():
		if child.winfo_class() not in ("Frame","Labelframe"):
			child.configure(state="disabled")

def connect_hv():
	hvConnectButton.config(state="disabled")
	time.sleep(1)
	com.init(mode=1)
	gl.vset = [com.get_vset(0),com.get_vset(1),com.get_vset(2),com.get_vset(3)]
	com.apply_ratio_0(); com.apply_ratio_2()
	gl.vmon = [com.get_vmon(0),com.get_vmon(1),com.get_vmon(2),com.get_vmon(3)]
	# Initially on or off
	if com.get_status(0) == 1:
		gl.hv0Button.config(bg="orange")
		gl.hv1Label.config(bg="orange")
		gl.status0 = True
	if com.get_status(2) == 1:
		gl.hv2Button.config(bg="orange")
		gl.hv3Label.config(bg="orange")
		gl.status2 = True
	com.start_monitor()
	enableElements(hvMainFrame); enableElements(quickChange0Frame); enableElements(quickChange2Frame)
	exitButton.config(state="normal")

# Ratio between HV and Booster
def change_ratio():
	cr = Tk()
	cr_label01 = Label(cr, text="Ratio 0/1"); cr_label01.grid(row=0,column=0)
	cr_label23 = Label(cr, text="Ratio 2/3"); cr_label23.grid(row=0,column=1)
	cr_entry01 = Entry(cr, width=5); cr_entry01.grid(row=1,column=0); cr_entry01.insert(0,str(gl.ratio01))
	cr_entry23 = Entry(cr, width=5); cr_entry23.grid(row=1,column=1); cr_entry23.insert(0,str(gl.ratio23))
	def apply_ratio():
		gl.ratio01 = float(cr_entry01.get()); gl.ratio23 = float(cr_entry23.get())
		com.apply_ratio_0(); com.apply_ratio_2()
		cr.destroy()
	cr_Button = Button(cr, text="Apply", command=apply_ratio); cr_Button.grid(row=1,column=2)
ratioButton = Button(hvMainFrame, text="Ratio",command=change_ratio); ratioButton.grid(row=0,column=0)

# Set Voltage
def change_vSet():
	cvset = Tk()
	cvset_label0 = Label(cvset, text="HV 0"); cvset_label0.grid(row=0,column=0)
	cvset_label2 = Label(cvset, text="HV 2"); cvset_label2.grid(row=0,column=1)
	cvset_entry0 = Entry(cvset, width=5); cvset_entry0.grid(row=1,column=0); cvset_entry0.insert(0,str(gl.vset[0]))
	cvset_entry2 = Entry(cvset, width=5); cvset_entry2.grid(row=1,column=1); cvset_entry2.insert(0,str(gl.vset[2]))
	def apply_vSet():
		com.safe_vset_0(float(cvset_entry0.get())); com.safe_vset_2(float(cvset_entry2.get()))
		cvset.destroy()
	cvset_Button = Button(cvset, text="Apply", command=apply_vSet); cvset_Button.grid(row=1,column=2)
vSetButton = Button(hvMainFrame, text="V-Set",command=change_vSet); vSetButton.grid(row=1,column=0)
gl.vSet0Label = Label(hvMainFrame, width=7, text=str(gl.vset[0]), bg="black", fg="orange"); gl.vSet0Label.grid(row=1,column=2)
gl.vSet1Label = Label(hvMainFrame, width=4, text=str(gl.vset[1]), font=("Helvetica 7"), bg="light grey", fg="black"); gl.vSet1Label.grid(row=1,column=3)
gl.vSet2Label = Label(hvMainFrame, width=7, text=str(gl.vset[2]), bg="black", fg="orange"); gl.vSet2Label.grid(row=1,column=4)
gl.vSet3Label = Label(hvMainFrame, width=4, text=str(gl.vset[3]), font=("Helvetica 7"), bg="light grey", fg="black"); gl.vSet3Label.grid(row=1,column=5)

# Quick Change
quickChange0Frame = Frame(hvMainFrame, bg="#003366"); quickChange0Frame.grid(row=2,column=2)
q0_up10Button   = Button(quickChange0Frame, text="+10", font=("Helvetica 7"), width=3, command=lambda:com.safe_vset_0(gl.vset[0]+10)); q0_up10Button.grid(row=0,column=0)
q0_up50Button   = Button(quickChange0Frame, text="+50", font=("Helvetica 7"), width=3, command=lambda:com.safe_vset_0(gl.vset[0]+50)); q0_up50Button.grid(row=0,column=1)
q0_down10Button = Button(quickChange0Frame, text="-10", font=("Helvetica 7"), width=3, command=lambda:com.safe_vset_0(gl.vset[0]-10)); q0_down10Button.grid(row=1,column=0)
q0_down50Button = Button(quickChange0Frame, text="-50", font=("Helvetica 7"), width=3, command=lambda:com.safe_vset_0(gl.vset[0]-50)); q0_down50Button.grid(row=1,column=1)

quickChange2Frame = Frame(hvMainFrame, bg="#003366"); quickChange2Frame.grid(row=2,column=4)
q2_up10Button   = Button(quickChange2Frame, text="+10", font=("Helvetica 7"), width=3, command=lambda:com.safe_vset_2(gl.vset[0]+10)); q2_up10Button.grid(row=0,column=0)
q2_up50Button   = Button(quickChange2Frame, text="+50", font=("Helvetica 7"), width=3, command=lambda:com.safe_vset_2(gl.vset[0]+50)); q2_up50Button.grid(row=0,column=1)
q2_down10Button = Button(quickChange2Frame, text="-10", font=("Helvetica 7"), width=3, command=lambda:com.safe_vset_2(gl.vset[0]-10)); q2_down10Button.grid(row=1,column=0)
q2_down50Button = Button(quickChange2Frame, text="-50", font=("Helvetica 7"), width=3, command=lambda:com.safe_vset_2(gl.vset[0]-50)); q2_down50Button.grid(row=1,column=1)

# MON Voltage
vMonLabel = Label(hvMainFrame, text ="V-Mon", width=10); vMonLabel.grid(row=3,column=0)
gl.vMon0Label = Label(hvMainFrame, width=5, text=str(gl.vmon0), bg="black", fg="red"); gl.vMon0Label.grid(row=3,column=2)
gl.vMon1Label = Label(hvMainFrame, width=4, text=str(gl.vmon1), font=("Helvetica 7"), bg="light grey", fg="red"); gl.vMon1Label.grid(row=3,column=3)
gl.vMon2Label = Label(hvMainFrame, width=5, text=str(gl.vmon2), bg="black", fg="red"); gl.vMon2Label.grid(row=3,column=4)
gl.vMon3Label = Label(hvMainFrame, width=4, text=str(gl.vmon3), font=("Helvetica 7"), bg="light grey", fg="red"); gl.vMon3Label.grid(row=3,column=5)

# MON Current
iMonLabel = Label(hvMainFrame, text ="I-Mon (mA)", width=10); iMonLabel.grid(row=4,column=0)
gl.iMon0Label = Label(hvMainFrame, width=5, text="0", font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon0Label.grid(row=4,column=2)
gl.iMon1Label = Label(hvMainFrame, width=4, text="0", font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon1Label.grid(row=4,column=3)
gl.iMon2Label = Label(hvMainFrame, width=5, text="0", font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon2Label.grid(row=4,column=4)
gl.iMon3Label = Label(hvMainFrame, width=4, text="0", font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon3Label.grid(row=4,column=5)

disableElements(hvMainFrame); disableElements(quickChange0Frame); disableElements(quickChange2Frame)


rootExitFrame=Frame(hvFrame, bg="#003366"); rootExitFrame.grid(row=0,column=0)
def exit():
	exitButton.config(state="disabled")
	gl.mon_thread = False
	disableElements(hvMainFrame); disableElements(quickChange0Frame); disableElements(quickChange2Frame)
	gl.scheck = 0; gl.failed_check= 0
	hvConnectButton.config(state="normal")


hvHeaderLabel = Label(rootExitFrame, text="HV", font=("Helvetica 20 bold"), fg="white", bg="#003366"); hvHeaderLabel.grid(row=0,column=0)
hvAddressLabel = Label(rootExitFrame, text=hvaddress_1, fg="white", bg="#003366"); hvAddressLabel.grid(row=1,column=0)
hvConnectButton = Button(rootExitFrame, text="Connect", width=8, bg="#003366", fg="white", command=connect_hv); hvConnectButton.grid(row=2,column=0)
exitButton = Button(rootExitFrame, text="Close", width=8, command=exit, bg="#003366", fg="white", state="disabled"); exitButton.grid(row=3,column=0)
gl.frameLabel = Label(rootExitFrame, text=str(gl.scheck)); gl.frameLabel.grid(row=4, column=0)

#-2-#
hvaddress_2 = global_config["controller"]["hv_address_card2"]

hvFrame2 = Frame(leftFrame2, bg="#003366"); hvFrame2.grid(row=8, column=0)
hvMainFrame2 = Frame(hvFrame2, bg="#003366"); hvMainFrame2.grid(row=0,column=1)

gl.hv0Button2 = Button(hvMainFrame2, text="HV 0", font=("Helvetica 12 bold"), bg="grey", command=com2.toggle_0); gl.hv0Button2.grid(row=0,column=2)
gl.hv1Label2 = Label(hvMainFrame2, text="HV 1", font=("Helvetica 8 italic"), bg="grey"); gl.hv1Label2.grid(row=0,column=3)
gl.hv2Button2 = Button(hvMainFrame2, text="HV 2", font=("Helvetica 12 bold"), bg="grey", command=com2.toggle_2); gl.hv2Button2.grid(row=0,column=4)
gl.hv3Label2 = Label(hvMainFrame2, text="HV 3", font=("Helvetica 8 italic"), bg="grey"); gl.hv3Label2.grid(row=0,column=5)

def connect_hv2():
	hvConnectButton2.config(state="disabled")
	time.sleep(1)
	com2.init(mode=1)
	gl.vset2 = [com2.get_vset(0),com2.get_vset(1),com2.get_vset(2),com2.get_vset(3)]
	com2.apply_ratio_0(); com2.apply_ratio_2()
	gl.vmon2 = [com2.get_vmon(0),com2.get_vmon(1),com2.get_vmon(2),com2.get_vmon(3)]
	# Initially on or off
	if com2.get_status(0) == 1:
		gl.hv0Button2.config(bg="orange")
		gl.hv1Label2.config(bg="orange")
		gl.status02 = True
	if com2.get_status(2) == 1:
		gl.hv2Button2.config(bg="orange")
		gl.hv3Label2.config(bg="orange")
		gl.status22 = True
	com2.start_monitor()
	enableElements(hvMainFrame2); enableElements(quickChange0Frame2); enableElements(quickChange2Frame2)
	exitButton2.config(state="normal")

# Ratio between HV and Booster
def change_ratio2():
	cr2 = Tk()
	cr_label012 = Label(cr2, text="Ratio 0/1"); cr_label012.grid(row=0,column=0)
	cr_label232 = Label(cr2, text="Ratio 2/3"); cr_label232.grid(row=0,column=1)
	cr_entry012 = Entry(cr2, width=5); cr_entry012.grid(row=1,column=0); cr_entry012.insert(0,str(gl.ratio012))
	cr_entry232 = Entry(cr2, width=5); cr_entry232.grid(row=1,column=1); cr_entry232.insert(0,str(gl.ratio232))
	def apply_ratio2():
		gl.ratio012 = float(cr_entry012.get()); gl.ratio232 = float(cr_entry232.get())
		com2.apply_ratio_0(); com2.apply_ratio_2()
		cr2.destroy()
	cr_Button2 = Button(cr2, text="Apply", command=apply_ratio2); cr_Button2.grid(row=1,column=2)
ratioButton2 = Button(hvMainFrame2, text="Ratio",command=change_ratio2); ratioButton2.grid(row=0,column=0)

# Set Voltage
def change_vSet2():
	cvset2 = Tk()
	cvset_label02 = Label(cvset2, text="HV 0"); cvset_label02.grid(row=0,column=0)
	cvset_label22 = Label(cvset2, text="HV 2"); cvset_label22.grid(row=0,column=1)
	cvset_entry02 = Entry(cvset2, width=5); cvset_entry02.grid(row=1,column=0); cvset_entry02.insert(0,str(gl.vset2[0]))
	cvset_entry22 = Entry(cvset2, width=5); cvset_entry22.grid(row=1,column=1); cvset_entry22.insert(0,str(gl.vset2[2]))
	def apply_vSet2():
		com2.safe_vset_0(float(cvset_entry02.get())); com2.safe_vset_2(float(cvset_entry22.get()))
		cvset2.destroy()
	cvset_Button2 = Button(cvset2, text="Apply", command=apply_vSet2); cvset_Button2.grid(row=1,column=2)
vSetButton2 = Button(hvMainFrame2, text="V-Set",command=change_vSet2); vSetButton2.grid(row=1,column=0)
gl.vSet0Label2 = Label(hvMainFrame2, width=7, text=str(gl.vset2[0]), bg="black", fg="orange"); gl.vSet0Label2.grid(row=1,column=2)
gl.vSet1Label2 = Label(hvMainFrame2, width=4, text=str(gl.vset2[1]), font=("Helvetica 7"), bg="light grey", fg="black"); gl.vSet1Label2.grid(row=1,column=3)
gl.vSet2Label2 = Label(hvMainFrame2, width=7, text=str(gl.vset2[2]), bg="black", fg="orange"); gl.vSet2Label2.grid(row=1,column=4)
gl.vSet3Label2 = Label(hvMainFrame2, width=4, text=str(gl.vset2[3]), font=("Helvetica 7"), bg="light grey", fg="black"); gl.vSet3Label2.grid(row=1,column=5)

# Quick Change
quickChange0Frame2 = Frame(hvMainFrame2, bg="#003366"); quickChange0Frame2.grid(row=2,column=2)
q0_up10Button2   = Button(quickChange0Frame2, text="+10", font=("Helvetica 7"), width=3, command=lambda:com2.safe_vset_0(gl.vset2[0]+10)); q0_up10Button2.grid(row=0,column=0)
q0_up50Button2   = Button(quickChange0Frame2, text="+50", font=("Helvetica 7"), width=3, command=lambda:com2.safe_vset_0(gl.vset2[0]+50)); q0_up50Button2.grid(row=0,column=1)
q0_down10Button2 = Button(quickChange0Frame2, text="-10", font=("Helvetica 7"), width=3, command=lambda:com2.safe_vset_0(gl.vset2[0]-10)); q0_down10Button2.grid(row=1,column=0)
q0_down50Button2 = Button(quickChange0Frame2, text="-50", font=("Helvetica 7"), width=3, command=lambda:com2.safe_vset_0(gl.vset2[0]-50)); q0_down50Button2.grid(row=1,column=1)

quickChange2Frame2 = Frame(hvMainFrame2, bg="#003366"); quickChange2Frame2.grid(row=2,column=4)
q2_up10Button2   = Button(quickChange2Frame2, text="+10", font=("Helvetica 7"), width=3, command=lambda:com2.safe_vset_2(gl.vset2[0]+10)); q2_up10Button2.grid(row=0,column=0)
q2_up50Button2   = Button(quickChange2Frame2, text="+50", font=("Helvetica 7"), width=3, command=lambda:com2.safe_vset_2(gl.vset2[0]+50)); q2_up50Button2.grid(row=0,column=1)
q2_down10Button2 = Button(quickChange2Frame2, text="-10", font=("Helvetica 7"), width=3, command=lambda:com2.safe_vset_2(gl.vset2[0]-10)); q2_down10Button2.grid(row=1,column=0)
q2_down50Button2 = Button(quickChange2Frame2, text="-50", font=("Helvetica 7"), width=3, command=lambda:com2.safe_vset_2(gl.vset2[0]-50)); q2_down50Button2.grid(row=1,column=1)

# MON Voltage
vMonLabel2 = Label(hvMainFrame2, text ="V-Mon", width=10); vMonLabel2.grid(row=3,column=0)
gl.vMon0Label2 = Label(hvMainFrame2, width=5, text=str(gl.vmon02), bg="black", fg="red"); gl.vMon0Label2.grid(row=3,column=2)
gl.vMon1Label2 = Label(hvMainFrame2, width=4, text=str(gl.vmon12), font=("Helvetica 7"), bg="light grey", fg="red"); gl.vMon1Label2.grid(row=3,column=3)
gl.vMon2Label2 = Label(hvMainFrame2, width=5, text=str(gl.vmon22), bg="black", fg="red"); gl.vMon2Label2.grid(row=3,column=4)
gl.vMon3Label2 = Label(hvMainFrame2, width=4, text=str(gl.vmon32), font=("Helvetica 7"), bg="light grey", fg="red"); gl.vMon3Label2.grid(row=3,column=5)

# MON Current
iMonLabel2 = Label(hvMainFrame2, text ="I-Mon (mA)", width=10); iMonLabel2.grid(row=4,column=0)
gl.iMon0Label2 = Label(hvMainFrame2, width=5, text="0", font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon0Label2.grid(row=4,column=2)
gl.iMon1Label2 = Label(hvMainFrame2, width=4, text="0", font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon1Label2.grid(row=4,column=3)
gl.iMon2Label2 = Label(hvMainFrame2, width=5, text="0", font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon2Label2.grid(row=4,column=4)
gl.iMon3Label2 = Label(hvMainFrame2, width=4, text="0", font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon3Label2.grid(row=4,column=5)

disableElements(hvMainFrame2); disableElements(quickChange0Frame2); disableElements(quickChange2Frame2)


rootExitFrame2=Frame(hvFrame2, bg="#003366"); rootExitFrame2.grid(row=0,column=0)
def exit2():
	exitButton2.config(state="disabled")
	gl.mon_thread2 = False
	disableElements(hvMainFrame2); disableElements(quickChange0Frame2); disableElements(quickChange2Frame2)
	gl.scheck2 = 0; gl.failed_check2= 0
	hvConnectButton2.config(state="normal")

	
hvHeaderLabel2 = Label(rootExitFrame2, text="HV", font=("Helvetica 20 bold"), fg="white", bg="#003366"); hvHeaderLabel2.grid(row=0,column=0)
hvAddressLabel2 = Label(rootExitFrame2, text=hvaddress_2, fg="white", bg="#003366"); hvAddressLabel2.grid(row=1,column=0)
hvConnectButton2 = Button(rootExitFrame2, text="Connect", width=8, bg="#003366", fg="white", command=connect_hv2); hvConnectButton2.grid(row=2,column=0)
exitButton2 = Button(rootExitFrame2, text="Close", width=8, command=exit2, bg="#003366", fg="white", state="disabled"); exitButton2.grid(row=3,column=0)
gl.frameLabel2 = Label(rootExitFrame2, text=str(gl.scheck2)); gl.frameLabel2.grid(row=4, column=0)


#####################
## ROOT MAIN FRAME ##
#####################
rootMainFrame = Frame(card1Frame); rootMainFrame.grid(row=0,column=2)
rootMainFrame2 = Frame(card2Frame); rootMainFrame2.grid(row=0,column=2)

led1Frame = Frame(rootMainFrame); led1Frame.grid(row=0,column=0)
wait1Canvas = Canvas(led1Frame, width=20,height=20); wait1Canvas.grid(row=0,column=1)
wait1LED = wait1Canvas.create_rectangle(1,1,20,20, fill="black", width=0)

led2Frame = Frame(rootMainFrame2); led2Frame.grid(row=0,column=0)
wait2Canvas = Canvas(led2Frame, width=20,height=20); wait2Canvas.grid(row=0,column=0)
wait2LED = wait2Canvas.create_rectangle(1,1,20,20, fill="black", width=0)
##################
## OFFSET FRAME ##
##################
#-1-#
offsetFrame = Frame(rootMainFrame, background="#e8fcae"); offsetFrame.grid(row=1,column=0)
offsetHeader = Frame(offsetFrame, background="#e8fcae"); offsetHeader.grid(row=0,column=0)
offsetHeaderLabel = Label(offsetHeader, text="Offset", background="#e8fcae", font=("Helvetica 12 bold")); offsetHeaderLabel.grid(row=0,column=0)
offsetLLabel = Label(offsetHeader, text="l", background="#e8fcae"); offsetLLabel.grid(row=0,column=1)
offsetLEntry = Entry(offsetHeader, width=8); offsetLEntry.grid(row=0,column=2); offsetLEntry.insert(0,"1000000")
offsetPLabel = Label(offsetHeader, text="p", background="#e8fcae"); offsetPLabel.grid(row=0,column=3)
offsetPEntry = Entry(offsetHeader, width=5); offsetPEntry.grid(row=0,column=4); offsetPEntry.insert(0,"2000")

offsetBasicFrame = Frame(offsetFrame, background="#e8fcae"); offsetBasicFrame.grid(row=1,column=0)
# Take offset measurement
def takeOffsetMeasurement():
	qsettings_calibrations()
	filename = gl.basicpath + "/" + offsetNameEntry.get()
	ma, mb = cc.measurement(filename)
	calculate_data(ma, mb)
	qsettings_checkWaveform()
	gl.offsetFile = filename; offsetFileLabel.config(text=gl.offsetFile.split("/")[-1])
takeOffsetButton = Button(offsetBasicFrame, text="Measure", background="#e8fcae", width=15, command=takeOffsetMeasurement); takeOffsetButton.grid(row=0,column=0)
offsetNameEntry = Entry(offsetBasicFrame, width=15); offsetNameEntry.grid(row=0,column=1); offsetNameEntry.insert(0,"off.bin")

# Select offset binary file for offset investigations
def selectOffsetFile():
	root.filename = filedialog.askopenfilename(initialdir = gl.basicpath, title = "Select offset file", filetypes = (("binary files","*.bin"),("all files","*.*")))
	gl.offsetFile = root.filename; offsetFileLabel.config(text=gl.offsetFile.split("/")[-1])
selectOffsetFileButton = Button(offsetBasicFrame, text="Select Offset Binary", width=15, background="#e8fcae", command=selectOffsetFile); selectOffsetFileButton.grid(row=1,column=0)
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
loadOffsetButton = Button(offsetBasicFrame, text="Load Offset", width=15, background="#e8fcae", command=loadOffset); loadOffsetButton.grid(row=2,column=0)
loadOffsetLabel = Label(offsetBasicFrame, text="no file selected", background="#e8fcae"); loadOffsetLabel.grid(row=2,column=1)
# Display part of the waveform and horizontal offset lines
def displayOffset():
	wv_off_a, wv_off_b = wv.execute(file=gl.offsetFile, length=int(int(offsetLEntry.get())/10))
	plt.figure("Offset calculations", figsize=(10,6))
	plt.plot(wv_off_a, label="Channel A", color="blue", alpha=0.4); plt.axhline(y=gl.off_a, color="blue")
	if gl.o_nchn == 2:
		plt.plot(wv_off_b, label="Channel B", color="red" , alpha=0.4); plt.axhline(y=gl.off_b, color="red")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(gl.offsetFile); plt.show()
displayOffsetButton = Button(offsetBasicFrame, text="Display Offset", width=15, background="#e8fcae", command=displayOffset); displayOffsetButton.grid(row=3, column=0)
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

#-2-#
offsetFrame2 = Frame(rootMainFrame2, background="#e8fcae"); offsetFrame2.grid(row=1,column=0)
offsetHeader2 = Frame(offsetFrame2, background="#e8fcae"); offsetHeader2.grid(row=0,column=0)
offsetHeaderLabel2 = Label(offsetHeader2, text="Offset", background="#e8fcae", font=("Helvetica 12 bold")); offsetHeaderLabel2.grid(row=0,column=0)
offsetLLabel2 = Label(offsetHeader2, text="l", background="#e8fcae"); offsetLLabel2.grid(row=0,column=1)
offsetLEntry2 = Entry(offsetHeader2, width=8); offsetLEntry2.grid(row=0,column=2); offsetLEntry2.insert(0,"1000000")
offsetPLabel2 = Label(offsetHeader2, text="p", background="#e8fcae"); offsetPLabel2.grid(row=0,column=3)
offsetPEntry2 = Entry(offsetHeader2, width=5); offsetPEntry2.grid(row=0,column=4); offsetPEntry2.insert(0,"2000")

offsetBasicFrame2 = Frame(offsetFrame2, background="#e8fcae"); offsetBasicFrame2.grid(row=1,column=0)
# Take offset measurement
def takeOffsetMeasurement2():
	qsettings_calibrations2()
	filename = gl.basicpath2 + "/" + offsetNameEntry2.get()
	ma, mb = cc2.measurement(filename)
	calculate_data2(ma, mb)
	qsettings_checkWaveform2()
	gl.offsetFile2 = filename; offsetFileLabel2.config(text=gl.offsetFile2.split("/")[-1])
takeOffsetButton2 = Button(offsetBasicFrame2, text="Measure", background="#e8fcae", width=15, command=takeOffsetMeasurement2); takeOffsetButton2.grid(row=0,column=0)
offsetNameEntry2 = Entry(offsetBasicFrame2, width=15); offsetNameEntry2.grid(row=0,column=1); offsetNameEntry2.insert(0,"off.bin")

# Select offset binary file for offset investigations
def selectOffsetFile2():
	root.filename = filedialog.askopenfilename(initialdir = gl.basicpath2, title = "Select offset file", filetypes = (("binary files","*.bin"),("all files","*.*")))
	gl.offsetFile2 = root.filename; offsetFileLabel2.config(text=gl.offsetFile2.split("/")[-1])
selectOffsetFileButton2 = Button(offsetBasicFrame2, text="Select Offset Binary", width=15, background="#e8fcae", command=selectOffsetFile2); selectOffsetFileButton2.grid(row=1,column=0)
offsetFileLabel2 = Label(offsetBasicFrame2, text="no file selected", background="#e8fcae"); offsetFileLabel2.grid(row=1,column=1)
# Load already existing .off or .off1 file
def loadOffset2():
	if gl.o_nchn2 == 2:
		root.filename = filedialog.askopenfilename(initialdir = gl.calibpath2, title = "Load offset calculation", filetypes = (("calib files","*.off"),("all files","*.*")))
		gl.offsetLoad2 = root.filename; loadOffsetLabel2.config(text=gl.offsetLoad2.split("/")[-1])	
		gl.off_a2 = np.loadtxt(gl.offsetLoad2)[0]; parOffsetLabelA2.config(text="{:.2f}".format(gl.off_a2))
		gl.off_b2 = np.loadtxt(gl.offsetLoad2)[1]; parOffsetLabelB2.config(text="{:.2f}".format(gl.off_b2))
	if gl.o_nchn2 == 1:
		root.filename = filedialog.askopenfilename(initialdir = gl.calibpath2, title = "Load offset calculation", filetypes = (("calib files","*.off1"),("all files","*.*")))
		gl.offsetLoad2 = root.filename; loadOffsetLabel2.config(text=gl.offsetLoad2.split("/")[-1])	
		gl.off_a2 = np.loadtxt(gl.offsetLoad2); parOffsetLabelA2.config(text="{:.2f}".format(gl.off_a2))
		parOffsetLabelB2.config(text="--")
	gl.offsetFile2 = to_bin(gl.offsetLoad2); offsetFileLabel2.config(text=gl.offsetFile2.split("/")[-1])
loadOffsetButton2 = Button(offsetBasicFrame2, text="Load Offset", width=15, background="#e8fcae", command=loadOffset2); loadOffsetButton2.grid(row=2,column=0)
loadOffsetLabel2 = Label(offsetBasicFrame2, text="no file selected", background="#e8fcae"); loadOffsetLabel2.grid(row=2,column=1)
# Display part of the waveform and horizontal offset lines
def displayOffset2():
	wv_off_a, wv_off_b = wv.execute(file=gl.offsetFile2, length=int(int(offsetLEntry2.get())/10))
	plt.figure("Offset calculations", figsize=(10,6))
	plt.plot(wv_off_a, label="Channel A", color="blue", alpha=0.4); plt.axhline(y=gl.off_a2, color="blue")
	if gl.o_nchn2 == 2:
		plt.plot(wv_off_b, label="Channel B", color="red" , alpha=0.4); plt.axhline(y=gl.off_b2, color="red")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(gl.offsetFile2); plt.show()
displayOffsetButton2 = Button(offsetBasicFrame2, text="Display Offset", width=15, background="#e8fcae", command=displayOffset2); displayOffsetButton2.grid(row=3, column=0)
# Simply display part of the waveform
def displayWaveformOffset2():
	if gl.o_nchn2 == 2:
		wv_off_a, wv_off_b = wv.execute(file=gl.offsetFile2, length=int(int(offsetLEntry2.get())/10))
	else:
		wv_off_a = wv.execute(file=gl.offsetFile2, length=int(int(offsetLEntry2.get())/10))
	plt.figure("Offset file waveforms", figsize=(10,6))
	plt.plot(wv_off_a, label="Channel A", color="blue")
	if gl.o_nchn2 == 2:
		plt.plot(wv_off_b, label="Channel B", color="red")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(gl.offsetFile2); plt.show()
displayWaveformOffsetButton2 = Button(offsetBasicFrame2, text="Display Waveform", background="#e8fcae", command=displayWaveformOffset2); displayWaveformOffsetButton2.grid(row=3,column=1)

# Do the offset measurement
def off_measurement2():
	gl.statusLabel2.config(text="Calculate Offset", bg="#edda45"); root.update()
	gl.off_a2, gl.off_b2 = off.execute2(file=gl.offsetFile2, packet_length=int(offsetLEntry2.get()), npackets=int(offsetPEntry2.get()))
	if gl.stop_offset_thread2==False:
		parOffsetLabelA2.config(text="{:.2f}".format(gl.off_a2))
		if gl.o_nchn2 == 2:
			parOffsetLabelB2.config(text="{:.2f}".format(gl.off_b2))
			outfileOff = to_calib(gl.offsetFile2,".off")
			np.savetxt(outfileOff, [gl.off_a2, gl.off_b2])
		else:
			parOffsetLabelB2.config(text="--")
			outfileOff = to_calib(gl.offsetFile2,".off1")
			np.savetxt(outfileOff, [gl.off_a2])
		gl.offsetLoad2 = outfileOff; loadOffsetLabel2.config(text=gl.offsetLoad2.split("/")[-1])
	idle2()
def start_offset_thread2():
	gl.stop_offset_thread2 = False
	offset_thread2 = Thread(target=off_measurement2, args=())
	offset_thread2.start()
def stop_offset_thread2():
	gl.stop_offset_thread2 = True
	gl.stop_wait_for_file_thread2 = True

# Offset parameters
offsetParamFrame2 = Frame(offsetFrame2, background="#e8fcae"); offsetParamFrame2.grid(row=2,column=0)
offsetParLabel2 = Label(offsetParamFrame2, text="Parameter", font=("Helvetica 10 bold"), background="#e8fcae"); offsetParLabel2.grid(row=0,column=0)
offsetALabel2 = Label(offsetParamFrame2, text="CHN A", font=("Helvetica 10 bold"), background="#e8fcae"); offsetALabel2.grid(row=0,column=1)
offsetBLabel2 = Label(offsetParamFrame2, text="CHN B", font=("Helvetica 10 bold"), background="#e8fcae"); offsetBLabel2.grid(row=0,column=2)
parOffsetLabel2 = Label(offsetParamFrame2, text="Baseline offset", background="#e8fcae"); parOffsetLabel2.grid(row=6,column=0)
parOffsetLabelA2 = Label(offsetParamFrame2, text="{:.2f}".format(gl.off_a2), background="black", fg="orange"); parOffsetLabelA2.grid(row=6,column=1)
parOffsetLabelB2 = Label(offsetParamFrame2, text="{:.2f}".format(gl.off_b2), background="black", fg="orange"); parOffsetLabelB2.grid(row=6,column=2)

# Offset Start and Stop
offsetDoFrame2 = Frame(offsetFrame2, background="#e8fcae"); offsetDoFrame2.grid(row=3,column=0)
offsetButton2 = Button(offsetDoFrame2, text="Calc Offset", background="#e8fcae", command=start_offset_thread2); offsetButton2.grid(row=0,column=0)
stopOffsetButton2 = Button(offsetDoFrame2, text="Abort", background="#fa857a", command=stop_offset_thread2); stopOffsetButton2.grid(row=0,column=1)

#######################
## CALIBRATION FRAME ##
#######################
#-1-#
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


calibGeneralFrame = Frame(calibFrame, background="#ccf2ff"); calibGeneralFrame.grid(row=1,column=0)
# Take calib measurement
def takeCalibMeasurement():
	qsettings_calibrations()
	filename = gl.basicpath + "/" + calibNameEntry.get()
	ma, mb = cc.measurement(filename)
	calculate_data(ma, mb)
	qsettings_checkWaveform()
	gl.calibFile = filename; calibFileLabel.config(text=gl.calibFile.split("/")[-1])
measureCalibButton = Button(calibGeneralFrame, text="Measure", width=15, bg="#ccf2ff", command=takeCalibMeasurement); measureCalibButton.grid(row=0,column=0)
calibNameEntry = Entry(calibGeneralFrame, width=15); calibNameEntry.grid(row=0,column=1); calibNameEntry.insert(0,"calib.bin")
selectCalibFileButton = Button(calibGeneralFrame, text="Select Calib Binary", width=15, command=selectCalibFile, background="#ccf2ff"); selectCalibFileButton.grid(row=1, column=0)
calibFileLabel = Label(calibGeneralFrame, text="no file selected", background="#ccf2ff"); calibFileLabel.grid(row=1, column=1)
loadCalibButton = Button(calibGeneralFrame, text="Load calibration", width=15, command=loadCalibration, background="#ccf2ff"); loadCalibButton.grid(row=2,column=0)
loadCalibLabel = Label(calibGeneralFrame, text="no file selected", background="#ccf2ff"); loadCalibLabel.grid(row=2,column=1)

# Other commands
def displayWaveform():
	wv_a, wv_b = wv.execute(file=gl.calibFile, length=int(int(calibLEntry.get())/10))
	plt.figure("Calibration file waveforms", figsize=(10,6))
	plt.plot(wv_a, label="Channel A", color="blue")
	if gl.o_nchn == 2:
		plt.plot(wv_b, label="Channel B", color="red")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(gl.calibFile); plt.show()
displayCalibrationButton = Button(calibGeneralFrame, text="Display calib", background="#ccf2ff", width=15, command=displayCalibration); displayCalibrationButton.grid(row=3,column=0)
displayWaveformButton = Button(calibGeneralFrame, text="Display waveform", background="#ccf2ff", width=15, command=displayWaveform); displayWaveformButton.grid(row=3, column=1)

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

#-2-#
calibFrame2 = Frame(rootMainFrame2, background="#ccf2ff"); calibFrame2.grid(row=2, column=0)
calibHeader2 = Frame(calibFrame2, background="#ccf2ff"); calibHeader2.grid(row=0,column=0)
calibHeaderLabel2 = Label(calibHeader2, text="Calibration", background="#ccf2ff", font=("Helvetica 12 bold")); calibHeaderLabel2.grid(row=0,column=0)
calibLLabel2 = Label(calibHeader2, text="l", background="#ccf2ff"); calibLLabel2.grid(row=0,column=1)
calibLEntry2 = Entry(calibHeader2, width=8); calibLEntry2.grid(row=0,column=2); calibLEntry2.insert(0,"1000000")
calibPLabel2 = Label(calibHeader2, text="p", background="#ccf2ff"); calibPLabel2.grid(row=0,column=3)
calibPEntry2 = Entry(calibHeader2, width=5); calibPEntry2.grid(row=0,column=4); calibPEntry2.insert(0,"200")

# Display pulse height distribution(s) including fit(s) and pulse shape(s)
def displayCalibration2():
	plt.figure("Calibration display", figsize=[10,6])
	plt.subplot(211)
	plt.plot(gl.histo_x2,gl.histo_a2, color="blue", label="Channel A: Avg height = {:.2f}".format(gl.ph_a2), alpha=0.5)
	plt.plot(gl.xplot2, gauss(gl.xplot2, *gl.pa2), color="blue")
	plt.axvline(x=gl.ph_a2, color="blue", linestyle="--")
	if gl.o_nchn2 == 2:
		plt.plot(gl.histo_x2,gl.histo_b2, color="red", label="Channel B: Avg height = {:.2f}".format(gl.ph_b2), alpha=0.5)
		plt.plot(gl.xplot2, gauss(gl.xplot2, *gl.pb2), color="red")
		plt.axvline(x=gl.ph_b2, color="red", linestyle="--")
		plt.ylim(0,1.5*max(gl.pa2[0],gl.pb2[0]))
	else:
		plt.ylim(0,1.5*gl.pa2[0])
	plt.xlim(-128,10); plt.legend(); plt.title(gl.calibFile2)
	plt.subplot(212)
	plt.plot(gl.ps_x2,gl.ps_a2, color="blue", label="Channel A: Sum = {:.2f}".format(gl.nsum_a2))
	if gl.o_nchn2 == 2:
		plt.plot(gl.ps_x2,gl.ps_b2, color="red", label="Channel B: Sum = {:.2f}".format(gl.nsum_b2))
	plt.legend(); plt.show()
# Do the whole calibration
def calibrate2():
	# Create and fit pulse height distribution
	gl.statusLabel2.config(text="Calibrating: Pulse heights ...", bg="#edda45"); root.update()
	fphd.execute2(packet_length = int(calibLEntry2.get()), npackets=int(calibPEntry2.get()), range_a=[float(fitRangelowEntryA2.get()),float(fitRangehighEntryA2.get())], range_b=[float(fitRangelowEntryB2.get()),float(fitRangehighEntryB2.get())])
	# Create average pulse shape
	if gl.stop_calib_thread2 == False:
		gl.statusLabel2.config(text="Calibrating: Pulse shape ...", bg="#edda45"); root.update()
		ps.execute2(min_pulses = [int(minPulsesEntryA2.get()),int(minPulsesEntryB2.get())], height=[-1*int(minHeightEntryA2.get()),-1*int(minHeightEntryB2.get())], cleanheight=[-1*int(cleanHeightEntryA2.get()),-1*int(cleanHeightEntryB2.get())])
	if gl.stop_calib_thread2 == False:
		finish_calibration2()
	# Activate Rate Buttons
	gl.calc_rate2 = True

	idle2()
def finish_calibration2(): # Execute after pulse height distribution and pulse shape calculation are finished
	# Combine pulse height distribution and pulse shape to calculate avg charge
	gl.avg_charge_a2 = gl.nsum_a2 * gl.ph_a2; avgChargeLabelA2.config(text="{:.2f}".format(gl.avg_charge_a2))
	gl.rmax_a2 = maxRate2(gl.avg_charge_a2) # Maximum rate
	rateACanvas2.itemconfig(rmaxaText2, text="{:.0f}".format(gl.rmax_a2)) # Show on rate bar
	if gl.o_nchn2 == 2:
		gl.avg_charge_b2 = gl.nsum_b2 * gl.ph_b2; avgChargeLabelB2.config(text="{:.2f}".format(gl.avg_charge_b2))
		gl.rmax_b2 = maxRate2(gl.avg_charge_b2) # Maximum rate
		rateBCanvas2.itemconfig(rmaxbText2, text="{:.0f}".format(gl.rmax_b2)) # Show in rate bar
	else:
		avgChargeLabelB2.config(text="--")

	# Create calibration files
	if gl.o_nchn2 == 2:
		np.savetxt(to_calib(gl.calibFile2, ".phd"),   np.c_[gl.histo_x2,gl.histo_a2,gl.histo_b2])
		np.savetxt(to_calib(gl.calibFile2, ".shape"), np.c_[gl.ps_x2, gl.ps_a2, gl.ps_b2])
		np.savetxt(to_calib(gl.calibFile2, ".xplot"), gl.xplot2)
		with open(to_calib(gl.calibFile2, ".calib"), 'w') as f:
			f.write(str(gl.pa2[0]) + "\n" + str(gl.pa2[1]) + "\n" + str(gl.pa2[2]) + "\n")
			f.write(str(gl.pb2[0]) + "\n" + str(gl.pb2[1]) + "\n" + str(gl.pb2[2]) + "\n")
			f.write(str(gl.nsum_a2) + "\n" + str(gl.nsum_b2) + "\n")
			f.write(str(gl.ph_a2) + "\n" + str(gl.ph_b2) + "\n")
			f.write(str(gl.avg_charge_a2) + "\n" + str(gl.avg_charge_b2) + "\n")
		gl.calibLoad2 = to_calib(gl.calibFile2, ".calib")
	else:
		np.savetxt(to_calib(gl.calibFile2, ".phd1"),   np.c_[gl.histo_x2,gl.histo_a2])
		np.savetxt(to_calib(gl.calibFile2, ".shape1"), np.c_[gl.ps_x2, gl.ps_a2])
		np.savetxt(to_calib(gl.calibFile2, ".xplot1"), gl.xplot2)
		with open(to_calib(gl.calibFile2, ".calib1"), 'w') as f:
			f.write(str(gl.pa2[0]) + "\n" + str(gl.pa2[1]) + "\n" + str(gl.pa2[2]) + "\n")
			f.write(str(gl.nsum_a2) + "\n")
			f.write(str(gl.ph_a2) + "\n")
			f.write(str(gl.avg_charge_a2) + "\n")
		gl.calibLoad2 = to_calib(gl.calibFile2, ".calib1")
	loadCalibLabel2.config(text=gl.calibLoad2.split("/")[-1])
# Only apply new fit range to calibration data
def calibrate_newFit2():
	gl.statusLabel2.config(text="New fit range ...", bg="#edda45"); root.update()
	fphd.onlyFit2(range_a=[float(fitRangelowEntryA2.get()),float(fitRangehighEntryA2.get())], range_b=[float(fitRangelowEntryB2.get()),float(fitRangehighEntryB2.get())])
	finish_calibration2()
	idle2()
calib_thread2 = []
def start_calib_thread2():
	gl.stop_calib_thread2 = False
	calib_thread2 = Thread(target=calibrate2, args=())
	calib_thread2.start()
def stop_calib_thread2():
	gl.stop_calib_thread2 = True
	gl.stop_wait_for_file_thread2 = True
def selectCalibFile2():
	root.filename = filedialog.askopenfilename(initialdir = gl.basicpath2, title = "Select calibration file", filetypes = (("binary files","*.bin"),("all files","*.*")))
	gl.calibFile2 = root.filename; calibFileLabel2.config(text=gl.calibFile2.split("/")[-1])
def loadCalibration2():
	if gl.o_nchn2 == 2:
		root.filename = filedialog.askopenfilename(initialdir = gl.calibpath2, title = "Load calibration", filetypes = (("calib files","*.calib"),("all files","*.*")))
		gl.calibLoad2 = root.filename; loadCalibLabel2.config(text=gl.calibLoad2.split("/")[-1])
		gl.histo_x2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".phd")[:,0]; gl.histo_a2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".phd")[:,1]; gl.histo_b2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".phd")[:,2]
		gl.ps_x2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".shape")[:,0]; gl.ps_a2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".shape")[:,1]; gl.ps_b2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".shape")[:,2]
		gl.xplot2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".xplot")
		gl.pa2[0] = np.loadtxt(gl.calibLoad2)[0]; gl.pa2[1] = np.loadtxt(gl.calibLoad2)[1]; gl.pa2[2] = np.loadtxt(gl.calibLoad2)[2]
		gl.pb2[0] = np.loadtxt(gl.calibLoad2)[3]; gl.pb2[1] = np.loadtxt(gl.calibLoad2)[4];	gl.pb2[2] = np.loadtxt(gl.calibLoad2)[5]
		gl.nsum_a2 = np.loadtxt(gl.calibLoad2)[6]; gl.nsum_b2 = np.loadtxt(gl.calibLoad2)[7]
		gl.ph_a2 = np.loadtxt(gl.calibLoad2)[8]; gl.ph_b2 = np.loadtxt(gl.calibLoad2)[9]
		gl.avg_charge_a2 = np.loadtxt(gl.calibLoad2)[10]; gl.avg_charge_b2 = np.loadtxt(gl.calibLoad2)[11]
		avgChargeLabelA2.config(text="{:.2f}".format(gl.avg_charge_a2)); avgChargeLabelB2.config(text="{:.2f}".format(gl.avg_charge_b2))
		gl.rmax_b2 = maxRate2(gl.avg_charge_b2) # Maximum rate
		rateBCanvas2.itemconfig(rmaxbText2, text="{:.0f}".format(gl.rmax_b2)) # Show in rate bar
	else:
		root.filename = filedialog.askopenfilename(initialdir = gl.calibpath2, title = "Load calibration", filetypes = (("one channel calib files","*.calib1"),("all files","*.*")))
		gl.calibLoad2 = root.filename; loadCalibLabel2.config(text=gl.calibLoad2.split("/")[-1])
		gl.histo_x2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".phd1")[:,0]; gl.histo_a2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".phd1")[:,1]
		gl.ps_x2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".shape1")[:,0]; gl.ps_a2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".shape1")[:,1]
		gl.xplot2 = np.loadtxt(gl.calibLoad2[0:gl.calibLoad2.find(".")]+".xplot1")
		gl.pa2[0] = np.loadtxt(gl.calibLoad2)[0]; gl.pa2[1] = np.loadtxt(gl.calibLoad2)[1]; gl.pa2[2] = np.loadtxt(gl.calibLoad2)[2]
		gl.nsum_a2 = np.loadtxt(gl.calibLoad2)[3]
		gl.ph_a2 = np.loadtxt(gl.calibLoad2)[4]
		gl.avg_charge_a2 = np.loadtxt(gl.calibLoad2)[5]
		avgChargeLabelA2.config(text="{:.2f}".format(gl.avg_charge_a2))
		avgChargeLabelB2.config(text="--")
	gl.rmax_a2 = maxRate2(gl.avg_charge_a2) # Maximum rates
	rateACanvas2.itemconfig(rmaxaText2, text="{:.0f}".format(gl.rmax_a2)) # Show in rate bar
	gl.calibFile2 = to_bin(gl.calibLoad2); calibFileLabel2.config(text=gl.calibFile2.split("/")[-1])
	# Activate Rate Buttons
	gl.calc_rate2 = True


calibGeneralFrame2 = Frame(calibFrame2, background="#ccf2ff"); calibGeneralFrame2.grid(row=1,column=0)
# Take calib measurement
def takeCalibMeasurement2():
	qsettings_calibrations2()
	filename = gl.basicpath2 + "/" + calibNameEntry2.get()
	ma, mb = cc2.measurement(filename)
	calculate_data2(ma, mb)
	qsettings_checkWaveform2()
	gl.calibFile2 = filename; calibFileLabel2.config(text=gl.calibFile2.split("/")[-1])
measureCalibButton2 = Button(calibGeneralFrame2, text="Measure", width=15, bg="#ccf2ff", command=takeCalibMeasurement2); measureCalibButton2.grid(row=0,column=0)
calibNameEntry2 = Entry(calibGeneralFrame2, width=15); calibNameEntry2.grid(row=0,column=1); calibNameEntry2.insert(0,"calib.bin")
selectCalibFileButton2 = Button(calibGeneralFrame2, text="Select Calib Binary", width=15, command=selectCalibFile2, background="#ccf2ff"); selectCalibFileButton2.grid(row=1, column=0)
calibFileLabel2 = Label(calibGeneralFrame2, text="no file selected", background="#ccf2ff"); calibFileLabel2.grid(row=1, column=1)
loadCalibButton2 = Button(calibGeneralFrame2, text="Load calibration", width=15, command=loadCalibration2, background="#ccf2ff"); loadCalibButton2.grid(row=2,column=0)
loadCalibLabel2 = Label(calibGeneralFrame2, text="no file selected", background="#ccf2ff"); loadCalibLabel2.grid(row=2,column=1)

# Other commands
def displayWaveform2():
	wv_a, wv_b = wv.execute(file=gl.calibFile2, length=int(int(calibLEntry2.get())/10))
	plt.figure("Calibration file waveforms", figsize=(10,6))
	plt.plot(wv_a, label="Channel A", color="blue")
	if gl.o_nchn2 == 2:
		plt.plot(wv_b, label="Channel B", color="red")
	plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(gl.calibFile2); plt.show()
displayCalibrationButton2 = Button(calibGeneralFrame2, text="Display calib", background="#ccf2ff", width=15, command=displayCalibration2); displayCalibrationButton2.grid(row=3,column=0)
displayWaveformButton2 = Button(calibGeneralFrame2, text="Display waveform", background="#ccf2ff", width=15, command=displayWaveform2); displayWaveformButton2.grid(row=3, column=1)

# Calibration parameters
calibParamFrame2 = Frame(calibFrame2, background="#ccf2ff"); calibParamFrame2.grid(row=2,column=0)

calibParLabel2 = Label(calibParamFrame2, text="Parameter", font=("Helvetica 10 bold"), background="#ccf2ff"); calibParLabel2.grid(row=0,column=0)
calibALabel2 = Label(calibParamFrame2, text="CHN A", font=("Helvetica 10 bold"), background="#ccf2ff"); calibALabel2.grid(row=0,column=1)
calibBLabel2 = Label(calibParamFrame2, text="CHN B", font=("Helvetica 10 bold"), background="#ccf2ff"); calibBLabel2.grid(row=0,column=2)

fitRangeLowLabel2 = Label(calibParamFrame2, text="lower fit border", background="#7ac5fa"); fitRangeLowLabel2.grid(row=1, column=0)
fitRangelowEntryA2 = Entry(calibParamFrame2, width=5); fitRangelowEntryA2.grid(row=1, column=1); fitRangelowEntryA2.insert(0,"-100")
fitRangelowEntryB2 = Entry(calibParamFrame2, width=5); fitRangelowEntryB2.grid(row=1, column=2); fitRangelowEntryB2.insert(0,"-100")
fitRangeHighLabel2 = Label(calibParamFrame2, text="upper fit border", background="#7ac5fa"); fitRangeHighLabel2.grid(row=2, column=0)
fitRangehighEntryA2 = Entry(calibParamFrame2, width=5); fitRangehighEntryA2.grid(row=2, column=1); fitRangehighEntryA2.insert(0,"-5")
fitRangehighEntryB2 = Entry(calibParamFrame2, width=5); fitRangehighEntryB2.grid(row=2, column=2); fitRangehighEntryB2.insert(0,"-5")

minHeightLabel2 = Label(calibParamFrame2, text="Min pulse height", background="#ccf2ff"); minHeightLabel2.grid(row=3, column=0)
minHeightEntryA2 = Entry(calibParamFrame2, width=5); minHeightEntryA2.grid(row=3,column=1); minHeightEntryA2.insert(0,"-25")
minHeightEntryB2 = Entry(calibParamFrame2, width=5); minHeightEntryB2.grid(row=3,column=2); minHeightEntryB2.insert(0,"-25")
cleanHeightLabel2 = Label(calibParamFrame2, text="Clean pulse height", background="#ccf2ff"); cleanHeightLabel2.grid(row=4, column=0)
cleanHeightEntryA2 = Entry(calibParamFrame2, width=5); cleanHeightEntryA2.grid(row=4,column=1); cleanHeightEntryA2.insert(0,"-2")
cleanHeightEntryB2 = Entry(calibParamFrame2, width=5); cleanHeightEntryB2.grid(row=4,column=2); cleanHeightEntryB2.insert(0,"-2")
minPulsesLabel2 = Label(calibParamFrame2, text="Min pulses", background="#ccf2ff"); minPulsesLabel2.grid(row=5, column=0)
minPulsesEntryA2 = Entry(calibParamFrame2, width=5); minPulsesEntryA2.grid(row=5,column=1); minPulsesEntryA2.insert(0,"100")
minPulsesEntryB2 = Entry(calibParamFrame2, width=5); minPulsesEntryB2.grid(row=5,column=2); minPulsesEntryB2.insert(0,"100")

avgChargeLabel2 = Label(calibParamFrame2, text="Avg charge", background="#ccf2ff"); avgChargeLabel2.grid(row=6,column=0)
avgChargeLabelA2 = Label(calibParamFrame2, text="--", background="black", fg="orange"); avgChargeLabelA2.grid(row=6,column=1)
avgChargeLabelB2 = Label(calibParamFrame2, text="--", background="black", fg="orange"); avgChargeLabelB2.grid(row=6,column=2)

# Calibration Start and Stop
calibDoFrame2 = Frame(calibFrame2, background="#ccf2ff"); calibDoFrame2.grid(row=3,column=0)
recalibrateButton2 = Button(calibDoFrame2, text="Calibrate", background="#ccf2ff", command=start_calib_thread2); recalibrateButton2.grid(row=0,column=0)
stopCalibrationButton2 = Button(calibDoFrame2, text="Abort", background="#fa857a", command=stop_calib_thread2); stopCalibrationButton2.grid(row=0,column=1)
CalibFitButton2 = Button(calibDoFrame2, text="Only Fit", background="#ccf2ff", command=calibrate_newFit2); CalibFitButton2.grid(row=0,column=2)


######################
## START/STOP FRAME ##
######################
#-1-#
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
desc_Label_avgrate = Label(abFrame, text="100-Avg rate");	desc_Label_avgrate.grid(row=5, column=0)

CHa_Label_mean = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHa_Label_mean.grid(row=2, column=1)
CHb_Label_mean = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHb_Label_mean.grid(row=2, column=2)

CHa_Label_curr = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHa_Label_curr.grid(row=3, column=1, pady=2)
CHb_Label_curr = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHb_Label_curr.grid(row=3, column=2, pady=2)

CHa_Label_rate = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 12 bold"));	CHa_Label_rate.grid(row=4, column=1, padx=3)
CHb_Label_rate = Label(abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 12 bold"));	CHb_Label_rate.grid(row=4, column=2)

CHa_Label_avgrate = Label(abFrame, text="0.0", fg="orange", bg="grey", width=5, font=("Helvetica 10 bold")); CHa_Label_avgrate.grid(row=5, column=1, padx=3)
CHb_Label_avgrate = Label(abFrame, text="0.0", fg="orange", bg="grey", width=5, font=("Helvetica 10 bold")); CHb_Label_avgrate.grid(row=5, column=2)

#-2-#
startstopFrame2 = Frame(rootMainFrame2); startstopFrame2.grid(row=4,column=0)

startstopHeader2 = Frame(startstopFrame2); startstopHeader2.grid(row=0,column=0)
startstopHeaderLabel2 = Label(startstopHeader2, text="Rate analysis", font=("Helvetica 12 bold")); startstopHeaderLabel2.grid(row=0,column=1)
startstopLLabel2 = Label(startstopHeader2, text="l"); startstopLLabel2.grid(row=0,column=2)
startstopLEntry2 = Entry(startstopHeader2, width=8); startstopLEntry2.grid(row=0,column=3); startstopLEntry2.insert(0,"1000000")
startstopPLabel2 = Label(startstopHeader2, text="p"); startstopPLabel2.grid(row=0,column=4)
startstopPEntry2 = Entry(startstopHeader2, width=5); startstopPEntry2.grid(row=0,column=5); startstopPEntry2.insert(0,"1")

# Param Frame
abFrame2 = Frame(startstopFrame2); abFrame2.grid(row=1,column=0)

parLabel2 = Label(abFrame2, text="Parameter", font=("Helvetica 10 bold")); parLabel2.grid(row=0,column=0)
aLabel2 = Label(abFrame2, text="CHN A", font=("Helvetica 10 bold")); aLabel2.grid(row=0,column=1)
bLabel2 = Label(abFrame2, text="CHN B", font=("Helvetica 10 bold")); bLabel2.grid(row=0,column=2)

# Amplifiers
ampLabel2 = Label(abFrame2, text="Amp"); ampLabel2.grid(row=1, column=0)
ampAEntry2 = Entry(abFrame2, width=5); ampAEntry2.grid(row=1, column=1); ampAEntry2.insert(0,"10")
ampBEntry2 = Entry(abFrame2, width=5); ampBEntry2.grid(row=1, column=2); ampBEntry2.insert(0,"10")

desc_Label_mean2 = Label(abFrame2, text="Voltage [mV]"); desc_Label_mean2.grid(row=2, column=0)
desc_Label_curr2 = Label(abFrame2, text="PMT current [µA]"); desc_Label_curr2.grid(row=3, column=0)
desc_Label_rate2 = Label(abFrame2, text="Photon rate [MHz]");	desc_Label_rate2.grid(row=4, column=0)
desc_Label_avgrate2 = Label(abFrame2, text="100-Avg rate");	desc_Label_avgrate2.grid(row=5, column=0)

CHa_Label_mean2 = Label(abFrame2, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHa_Label_mean2.grid(row=2, column=1)
CHb_Label_mean2 = Label(abFrame2, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHb_Label_mean2.grid(row=2, column=2)

CHa_Label_curr2 = Label(abFrame2, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHa_Label_curr2.grid(row=3, column=1, pady=2)
CHb_Label_curr2 = Label(abFrame2, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); CHb_Label_curr2.grid(row=3, column=2, pady=2)

CHa_Label_rate2 = Label(abFrame2, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 12 bold")); CHa_Label_rate2.grid(row=4, column=1, padx=3)
CHb_Label_rate2 = Label(abFrame2, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 12 bold")); CHb_Label_rate2.grid(row=4, column=2)

CHa_Label_avgrate2 = Label(abFrame2, text="0.0", fg="orange", bg="grey", width=5, font=("Helvetica 10 bold")); CHa_Label_avgrate2.grid(row=5, column=1, padx=3)
CHb_Label_avgrate2 = Label(abFrame2, text="0.0", fg="orange", bg="grey", width=5, font=("Helvetica 10 bold")); CHb_Label_avgrate2.grid(row=5, column=2)

#################
## START FRAME ##
#################
#-1-#
startFrame = Frame (rootMainFrame); startFrame.grid(row=5, column=0)
running = False; stop_thread = False; plotting = False; server=None; server_controller=None
# For plotting
rates_a = []; rates_b = []
plotFig = []; rate_a_plot = []; rate_b_plot = []
wav_a = []; wav_b = []

def calculate_data(mean_a, mean_b):
	vRange   = gl.o_voltages
	binRange = gl.o_binning
	#-- Channel A calculations --#
	# Waveform mean
	mean_a = mean_a - gl.off_a
	# Rates
	r_a = None; r_b = None
	if gl.calc_rate == True:
		r_a = 1e-6 * mean_a/(gl.avg_charge_a*binRange)
		gl.rates_a.pop(0)
		gl.rates_a.append(r_a)
		CHa_Label_rate.config(text="{:.1f}".format(r_a))
		CHa_Label_avgrate.config(text="{:.0f}".format(np.mean(gl.rates_a)))
		placeRateLineA(r_a)
	# mV
	mean_a_mV = ADC_to_mV(adc=mean_a, range=vRange)
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
		mean_b = mean_b - gl.off_b
		# Rates
		if gl.calc_rate == True:
			r_b = 1e-6 * mean_b/(gl.avg_charge_b*binRange)
			gl.rates_b.pop(0)
			gl.rates_b.append(r_b)
			CHb_Label_rate.config(text="{:.1f}".format(r_b))
			CHb_Label_avgrate.config(text="{:.0f}".format(np.mean(gl.rates_b)))
			placeRateLineB(r_b)
		# mV	
		mean_b_mV = ADC_to_mV(adc=mean_b, range=vRange)	
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
	update_rate_plot()
	root.update()


def analysis():
	vRange   = gl.o_voltages
	binRange = gl.o_binning
	mean_a_ADC, mean_b_ADC = cc.take_data()
	#-- Channel A calculations --#
	# Waveform mean
	mean_a_ADC = mean_a_ADC - gl.off_a
	# Rates
	r_a = 1e-6 * mean_a_ADC/(gl.avg_charge_a*binRange)
	gl.rates_a.pop(0)
	gl.rates_a.append(r_a)
	CHa_Label_rate.config(text="{:.1f}".format(r_a))
	CHa_Label_avgrate.config(text="{:.0f}".format(np.mean(gl.rates_a)))
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
		gl.rates_b.pop(0)
		gl.rates_b.append(r_b)	
		CHb_Label_rate.config(text="{:.1f}".format(r_b))
		CHb_Label_avgrate.config(text="{:.0f}".format(np.mean(gl.rates_b)))
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
	update_rate_plot()
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
		CHb_Label_avgrate.config(text="-.-")
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

def singleFileRate():
	global stop_thread, running
	if gl.o_nchn == 1:
		CHb_Label_rate.config(text="-.-")
		CHb_Label_avgrate.config(text="-.-")
		CHb_Label_mean.config(text="-.-")
		CHb_Label_curr.config(text="-.-")
	if running == True:
		running = False
		stop_thread = True
		gl.stop_wait_for_file_thread = True
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
		server=svr.server(no=1)
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

quickFrame = Frame(rootMainFrame); quickFrame.grid(row=6,column=0)
gl.quickRatesButton = Button(quickFrame, text="Start quick", bg="#e8fcae", width=9, command=startstop_quick); gl.quickRatesButton.grid(row=0, column=0)
def single():
	if gl.calc_rate == True:
		single_analysis()
	else:
		single_analysis_no_rate()
gl.singleRatesButton = Button(quickFrame, text="Single", width=5, command=single); gl.singleRatesButton.grid(row=0,column=1)

#-2-#
startFrame2 = Frame (rootMainFrame2); startFrame2.grid(row=5, column=0)
running2 = False; stop_thread2 = False; plotting2 = False; server2=None; server_controller2=None
# For plotting
rates_a2 = []; rates_b2 = []
plotFig2 = []; rate_a_plot2 = []; rate_b_plot2 = []
wav_a2 = []; wav_b2 = []

def calculate_data2(mean_a, mean_b):
	vRange   = gl.o_voltages2
	binRange = gl.o_binning2
	#-- Channel A calculations --#
	# Waveform mean
	mean_a = mean_a - gl.off_a2
	# Rates
	r_a = None; r_b = None
	if gl.calc_rate2 == True:
		r_a = 1e-6 * mean_a/(gl.avg_charge_a2*binRange)
		gl.rates_a2.pop(0)
		gl.rates_a2.append(r_a)
		CHa_Label_rate2.config(text="{:.1f}".format(r_a))
		CHa_Label_avgrate2.config(text="{:.0f}".format(np.mean(gl.rates_a2)))
		placeRateLineA2(r_a)
	# mV
	mean_a_mV = ADC_to_mV(adc=mean_a, range=vRange)
	CHa_Label_mean2.config(text="{:.2f}".format(mean_a_mV))
	# PMT current
	curr_a_microamp = 1e3 * mean_a_mV/float(ampAEntry2.get())/50
	if curr_a_microamp > -100:      
		CHa_Label_curr2.config(text="{:.1f}".format(curr_a_microamp), bg="black", fg="orange")
	else:
		CHa_Label_curr2.config(text="{:.1f}".format(curr_a_microamp), bg="#edd266", fg="red")

	#-- Channel B calculations --#
	if gl.o_nchn2 == 2:
		# Waveform mean	
		mean_b = mean_b - gl.off_b
		# Rates
		if gl.calc_rate2 == True:
			r_b = 1e-6 * mean_b/(gl.avg_charge_b2*binRange)
			gl.rates_b2.pop(0)
			gl.rates_b2.append(r_b)
			CHb_Label_rate2.config(text="{:.1f}".format(r_b))
			CHb_Label_avgrate2.config(text="{:.0f}".format(np.mean(gl.rates_b2)))
			placeRateLineB2(r_b)
		# mV	
		mean_b_mV = ADC_to_mV(adc=mean_b, range=vRange)	
		CHb_Label_mean2.config(text="{:.2f}".format(mean_b_mV))
		# PMT current	
		curr_b_microamp = 1e3 * mean_b_mV/float(ampBEntry2.get())/50
		if curr_b_microamp > -100:
			CHb_Label_curr2.config(text="{:.1f}".format(curr_b_microamp), bg="black", fg="orange")
		else:
			CHb_Label_curr2.config(text="{:.1f}".format(curr_b_microamp), bg="#edd266", fg="red")

	if server2 != None:
		server2.sendRate(r_a, r_b)
	if server_controller != None:
		if gl.o_nchn2 == 1:
			server_controller2.sendRate(r_a)
		else:
			server_controller2.sendRates(r_a,r_b)
	update_rate_plot2()
	root.update()


def analysis2():
	vRange   = gl.o_voltages2
	binRange = gl.o_binning2
	mean_a_ADC, mean_b_ADC = cc2.take_data()
	#-- Channel A calculations --#
	# Waveform mean
	mean_a_ADC = mean_a_ADC - gl.off_a2
	# Rates
	r_a = 1e-6 * mean_a_ADC/(gl.avg_charge_a2*binRange)
	gl.rates_a2.pop(0)
	gl.rates_a2.append(r_a)
	CHa_Label_rate2.config(text="{:.1f}".format(r_a))
	CHa_Label_avgrate2.config(text="{:.0f}".format(np.mean(gl.rates_a2)))
	placeRateLineA2(r_a)
	# mV
	mean_a_mV = ADC_to_mV(adc=mean_a_ADC, range=vRange)
	CHa_Label_mean2.config(text="{:.2f}".format(mean_a_mV))
	# PMT current
	curr_a_microamp = 1e3 * mean_a_mV/float(ampAEntry2.get())/50
	if curr_a_microamp > -100:      
		CHa_Label_curr2.config(text="{:.1f}".format(curr_a_microamp), bg="black", fg="orange")
	else:
		CHa_Label_curr2.config(text="{:.1f}".format(curr_a_microamp), bg="#edd266", fg="red")

	#-- Channel B calculations --#
	if gl.o_nchn2 == 2:
		# Waveform mean	
		mean_b_ADC = mean_b_ADC - gl.off_b2
		# Rates	
		r_b = 1e-6 * mean_b_ADC/(gl.avg_charge_b2*binRange)
		gl.rates_b2.pop(0)
		gl.rates_b2.append(r_b)	
		CHb_Label_rate2.config(text="{:.1f}".format(r_b))
		CHb_Label_avgrate2.config(text="{:.0f}".format(np.mean(gl.rates_b2)))
		placeRateLineB2(r_b)
		# mV	
		mean_b_mV = ADC_to_mV(adc=mean_b_ADC, range=vRange)	
		CHb_Label_mean2.config(text="{:.2f}".format(mean_b_mV))
		# PMT current	
		curr_b_microamp = 1e3 * mean_b_mV/float(ampBEntry2.get())/50
		if curr_b_microamp > -100:
			CHb_Label_curr2.config(text="{:.1f}".format(curr_b_microamp), bg="black", fg="orange")
		else:
			CHb_Label_curr2.config(text="{:.1f}".format(curr_b_microamp), bg="#edd266", fg="red")

	if server2 != None:
		server2.sendRate(r_a, r_b)
	if server_controller2 != None:
		if gl.o_nchn2 == 1:
			server_controller2.sendRate(r_a)
		else:
			server_controller2.sendRates(r_a,r_b)
	update_rate_plot2()
	root.update()
def quick_analysis2():
	global stop_thread2
	if server_controller2 != None:
		if gl.o_nchn2 == 1:
			server_controller2.sendMaxRate(gl.rmax_a2)
		else:
			server_controller2.sendMaxRates(gl.rmax_a2, gl.rmax_b2)
	while stop_thread2 == False:
		analysis2()
def single_analysis2():
	if server_controller2 != None:
		if gl.o_nchn2 == 1:
			server_controller2.sendMaxRate(gl.rmax_a2)
		else:
			server_controller2.sendMaxRates(gl.rmax_a2, gl.rmax_b2)
	analysis2()

def analysis_no_rate2():
	vRange   = gl.o_voltages2
	binRange = gl.o_binning2
	mean_a_ADC, mean_b_ADC = cc2.take_data()
	#-- Channel A calculations --#
	# Waveform mean
	mean_a_ADC = mean_a_ADC - gl.off_a2
	# mV
	mean_a_mV = ADC_to_mV(adc=mean_a_ADC, range=vRange)
	CHa_Label_mean2.config(text="{:.2f}".format(mean_a_mV))
	# PMT current
	curr_a_microamp = 1e3 * mean_a_mV/float(ampAEntry2.get())/50
	if curr_a_microamp > -100:      
		CHa_Label_curr2.config(text="{:.1f}".format(curr_a_microamp), bg="black", fg="orange")
	else:
		CHa_Label_curr2.config(text="{:.1f}".format(curr_a_microamp), bg="#edd266", fg="red")

	#-- Channel B calculations --#
	if gl.o_nchn2 == 2:
		# Waveform mean	
		mean_b_ADC = mean_b_ADC - gl.off_b2
		# mV	
		mean_b_mV = ADC_to_mV(adc=mean_b_ADC, range=vRange)	
		CHb_Label_mean2.config(text="{:.2f}".format(mean_b_mV))
		# PMT current	
		curr_b_microamp = 1e3 * mean_b_mV/float(ampBEntry2.get())/50
		if curr_b_microamp > -100:
			CHb_Label_curr2.config(text="{:.1f}".format(curr_b_microamp), bg="black", fg="orange")
		else:
			CHb_Label_curr2.config(text="{:.1f}".format(curr_b_microamp), bg="#edd266", fg="red")
	root.update()
def quick_analysis_no_rate2():
	global stop_thread2
	while stop_thread2 == False:
		analysis_no_rate2()		
def single_analysis_no_rate2():
	analysis_no_rate2()


def analyze_file2(newest_file):
	global stop_thread2, plotting2, rates_a2, rates_b2, wav_a2, wav_b2
	
	gl.statusLabel2.config(text="New file found" ); root.update()
	with open(newest_file, 'rb') as f:
		means_a = []; means_b = []
		if gl.o_nchn2 == 2:
			for allpkt in range(0, int(startstopPEntry2.get())):
				buf = (f.read(2*int(startstopLEntry2.get())))
				packet = np.frombuffer(buf, dtype=np.int8)
				packet = packet.reshape(int(startstopLEntry2.get()), 2)
				a_np = np.array(packet[:,0]); b_np = np.array(packet[:,1])
				means_a.append(np.mean(a_np)); means_b.append(np.mean(b_np))
				del(a_np); del(b_np)
		else:
			for allpkt in range(0, int(startstopPEntry2.get())):
				buf = (f.read(1*int(startstopLEntry2.get())))
				packet = np.frombuffer(buf, dtype=np.int8)
				a_np = np.array(packet)
				means_a.append(np.mean(a_np))
				del(a_np)

	vRange   = gl.o_voltages2
	binRange = gl.o_binning2
	
	#-- Channel A calculations --#
	# Waveform mean
	mean_a_ADC = np.mean(means_a)
	mean_a_ADC = mean_a_ADC - gl.off_a2
	# Rates
	r_a = 1e-6 * mean_a_ADC/(gl.avg_charge_a2*binRange)
	CHa_Label_rate2.config(text="{:.1f}".format(r_a))
	placeRateLineA2(r_a)
	# mV
	mean_a_mV = ADC_to_mV(adc=mean_a_ADC, range=vRange)
	CHa_Label_mean2.config(text="{:.2f}".format(mean_a_mV))
	# PMT current
	curr_a_microamp = 1e3 * mean_a_mV/float(ampAEntry2.get())/50
	if curr_a_microamp > -100:      
		CHa_Label_curr2.config(text="{:.1f}".format(curr_a_microamp), bg="black", fg="orange")
	else:
		CHa_Label_curr2.config(text="{:.1f}".format(curr_a_microamp), bg="#edd266", fg="red")

	#-- Channel B calculations --#
	if gl.o_nchn2 == 2:
		# Waveform mean
		mean_b_ADC = np.mean(means_b)	
		mean_b_ADC = mean_b_ADC - gl.off_b2
		# Rates	
		r_b = 1e-6 * mean_b_ADC/(gl.avg_charge_b2*binRange)	
		CHb_Label_rate2.config(text="{:.1f}".format(r_b))
		placeRateLineB2(r_b)
		# mV	
		mean_b_mV = ADC_to_mV(adc=mean_b_ADC, range=vRange)	
		CHb_Label_mean2.config(text="{:.2f}".format(mean_b_mV))
		# PMT current	
		curr_b_microamp = 1e3 * mean_b_mV/float(ampBEntry2.get())/50
		if curr_b_microamp > -100:
			CHb_Label_curr2.config(text="{:.1f}".format(curr_b_microamp), bg="black", fg="orange")
		else:
			CHb_Label_curr2.config(text="{:.1f}".format(curr_b_microamp), bg="#edd266", fg="red")

	if server2 != None:
		server2.sendRate(r_a, r_b)
	if server_controller2 != None:
			if gl.o_nchn2 == 1:
				server_controller2.sendRate(r_a)
			else:
				server_controller2.sendRates(r_a,r_b)
	root.update()

def analyze_files2():
	global stop_thread2, plotting2, rates_a2, rates_b2, wav_a2, wav_b2
	if gl.o_nchn2 == 1:
		CHb_Label_rate2.config(text="-.-")
		CHb_Label_avgrate2.config(text="-.-")
		CHb_Label_mean2.config(text="-.-")
		CHb_Label_curr2.config(text="-.-")
	if server_controller2 != None:
		if gl.o_nchn2 == 1:
			server_controller2.sendMaxRate(gl.rmax_a)
		else:
			server_controller2.sendMaxRates(gl.rmax_a, gl.rmax_b)

	while(stop_thread2 == False):
		gl.statusLabel2.config(text="Scanning files for Rates..." ); root.update()
		newest_file = wff.execute()
		if gl.stop_wait_for_file_thread2 == False:
			analyze_file(newest_file)
			gl.statusLabel2.config(text="Scanning files for Rates..." ); root.update()	
			#time.sleep(0.2)


running_quick2 = False
def startstop_quick2():
	global running_quick2, stop_thread2
	if running_quick2 == False:
		running_quick2 = True
		gl.act_start_quick2 = True
		if server_controller2 != None:
			server_controller2.sendActionInformation()

		gl.quickRatesButton2.config(text="Stop quick", bg="#fa857a")
		stop_thread2 = False
		gl.statusLabel2.config(text="Quick Rate Mode" , bg="#edda45"); root.update()
		if gl.calc_rate2 == True:
			the_thread2 = Thread(target=quick_analysis2, args=())
		else:
			the_thread2 = Thread(target=quick_analysis_no_rate2, args=())
		the_thread2.start()
	else:
		running_quick2 = False
		gl.act_start_quick2 = False
		if server_controller2 != None:
			server_controller2.sendActionInformation()
		stop_thread2 = True
		gl.quickRatesButton2.config(text="Start quick", bg="#e8fcae")
		idle2()

def singleFileRate2():
	global stop_thread2, running2
	if gl.o_nchn2 == 1:
		CHb_Label_rate2.config(text="-.-")
		CHb_Label_avgrate2.config(text="-.-")
		CHb_Label_mean2.config(text="-.-")
		CHb_Label_curr2.config(text="-.-")
	if running2 == True:
		running2 = False
		stop_thread2 = True
		gl.stop_wait_for_file_thread2 = True
	idle2()
	root.filename = filedialog.askopenfilename(initialdir = gl.basicpath2, title = "Select file for rate", filetypes = (("binary files","*.bin"),("all files","*.*")))
	analyze_file2(root.filename)
	idle2()

#starts/stops the server which sends the rate to the RASPI
def startStopServerMotor2():
	global server2
	#check if server is running
	if server2 == None :	
		#start server
		server2=svr.server(no=2)
		try:
			server2.start()
			#change button label
			gl.motorServerButton2.config(text="Stop Server (Motor)", bg="#ffc47d")
		except OSError as err:
			print("The OS did not allow start the server on {0}:{1} . Are address and port correct? Maybe an old instance is still blocking this resource?".format(server2.address, server2.port))
			print(err)
			server2 = None
	else:
		#shutdown server
		server2.stop()
		#change button label
		gl.motorServerButton2.config(text="Start Server (Motor)", bg="#cdcfd1")

		server2 = None

quickFrame2 = Frame(rootMainFrame2); quickFrame2.grid(row=6,column=0)
gl.quickRatesButton2 = Button(quickFrame2, text="Start quick", bg="#e8fcae", width=9, command=startstop_quick2); gl.quickRatesButton2.grid(row=0, column=0)
def single2():
	if gl.calc_rate2 == True:
		single_analysis2()
	else:
		single_analysis_no_rate2()
gl.singleRatesButton2 = Button(quickFrame2, text="Single", width=5, command=single2); gl.singleRatesButton2.grid(row=0,column=1)
##################
## Server Stuff ##
##################
#-1-#
socketFrame = Frame(rootMainFrame, bg="#f7df72"); socketFrame.grid(row=7,column=0)
socketHeaderLabel = Label(socketFrame, text="Network", font=("Helvetica 12 bold"), bg="#f7df72"); socketHeaderLabel.grid(row=0,column=0)
gl.motorServerButton  = Button(socketFrame, text="Start Server (Motor)",      bg="#cdcfd1", command=startStopServerMotor, width=20); gl.motorServerButton.grid(row=1,column=0)
#-2-#
socketFrame2 = Frame(rootMainFrame2, bg="#f7df72"); socketFrame2.grid(row=7,column=0)
socketHeaderLabel2 = Label(socketFrame2, text="Network", font=("Helvetica 12 bold"), bg="#f7df72"); socketHeaderLabel2.grid(row=0,column=0)
gl.motorServerButton2  = Button(socketFrame2, text="Start Server (Motor)",      bg="#cdcfd1", command=startStopServerMotor2, width=20); gl.motorServerButton2.grid(row=1,column=0)

#############################
## STATUS FRAME AND BUTTON ##
#############################
#-1-#
statusFrame = Frame (rootMainFrame); statusFrame.grid(row=8, column=0)
gl.statusLabel = Label(statusFrame, text="Starting ...", font=("Helvetica 12 bold"), bg="#ffffff"); gl.statusLabel.grid(row=0, column=0)
def idle():
	gl.statusLabel.config(text="Idle", bg="#ffffff"); root.update()
#-2-#
statusFrame2 = Frame (rootMainFrame2); statusFrame2.grid(row=8, column=0)
gl.statusLabel2 = Label(statusFrame2, text="Starting ...", font=("Helvetica 12 bold"), bg="#ffffff"); gl.statusLabel2.grid(row=0, column=0)
def idle2():
	gl.statusLabel2.config(text="Idle", bg="#ffffff"); root.update()

cc.init()
cc2.init()
idle()
idle2()

root.mainloop()