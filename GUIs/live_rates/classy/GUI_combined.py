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

import utilities as uti

import offset_meas as off
import fit_phd as fphd
import peakshape as ps
import waveform_reader as wv
import globals as gl
import rate_server as svr

import card_commands as cc
import header as header

#import hv_commands as com
#import hv_commands2 as com2

# plotting colors for waveform channels
chAcolor = "green"#"#00008b"
chBcolor = "blue"#"#00bfff"

#----------------#
# Telescope data #
#----------------#
tel_nos = []; tel_names = []; spcm_ports = []; datapaths = []; ports = []; modes = []
# Read in the data of the connected telescopes and digitizer cards
tel_data = np.loadtxt("../../telescopes.conf", dtype={'names': ('tel_nos', 'tel_names', 'spcm_ports', 'datapaths', 'ports', 'modes'), 'formats': ('<f8', 'U15', '<f8', 'U15', '<f8', 'U15')}, ndmin=1)
for i in range (0,len(tel_data)):
	tel_nos.append   (int(tel_data[i][0]))
	tel_names.append (str(tel_data[i][1]))
	spcm_ports.append(int(tel_data[i][2]))
	datapaths.append (str(tel_data[i][3]))
	ports.append     (int(tel_data[i][4]))
	modes.append     (str(tel_data[i][5]))


# Initialize the complete GUI window
root = Tk(); root.wm_title("DAQ Control"); root.geometry("+100+50")
r_width  = 20; r_height = 850 # dimensions of the rate bars

#---------------#
# Project frame #
#---------------#
projectName = None # Will be assigned when creating ore opening a project
# This is the top frame in the GUI which manages the project controls, that is creating
# a new project or opening an existing project
projectFrame = Frame(root); projectFrame.grid(row=0,column=0)
projectLabel = Label(projectFrame, text="Project", font=("Helvetica 12 bold")); projectLabel.grid(row=0,column=0)
copypaths = []

# Assign disks for storage.
basicpaths = [] # main directories of the telescopes
calibpaths = [] # calib directories of the telscopes

def create_project(name,window):
	global projectName, basicpaths, calibpaths
	projectName = name
	# clear paths for new assignmends
	basicpaths = []; calibpaths = []
	# Loop over the telescopes
	for i in range (0,len(tel_nos)):
		projectPath = datapaths[i] + name
		# Create the directory for the telescope
		os.makedirs(projectPath, exist_ok=True)	
		basicpaths.append(projectPath)
		# Create directory for the calibration files
		calibPath = projectPath + "/calibs"
		os.makedirs(calibPath, exist_ok=True)
		calibpaths.append(calibPath)
		# Tell the telescopes their paths
		telescopes[i].basicpath = projectPath
		telescopes[i].calibpath = calibPath

	if window != None:
		window.destroy()
	projectShowLabel.config(text=name)
def open_project():
	root.directoryname = filedialog.askdirectory(initialdir = datapaths[0], title = "Select any project directory")
	name = root.directoryname.split("/")[-1]
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
# This is the second to top frame which control the synchronization of the different digitzer cards.
# The synchronized measurements can be started/stopped, initialized, name can be inserted etc.
syncFrame = Frame(root); syncFrame.grid(row=1, column=0)

# Plot window
class NavigationToolbar(tkagg.NavigationToolbar2Tk):
	toolitems = [t for t in tkagg.NavigationToolbar2Tk.toolitems if t[0] in ('Home','Pan','Zoom','Save')]

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
		for t in telescopes:
			t.waitCanvas.itemconfig(t.waitLED, fill="black")
		tdiffs = []; timestamps_between = []; t_stamps = []
		lastA1 = []; lastB1 = []; lastA2 = []; lastB2 = []
def init_measurement():
	for t in telescopes:
		t.syncedMeasButton.invoke()

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

#--- Now some small stuff for plotting the acquisition times
fig = Figure(figsize=(4*len(tel_nos),0.5))
# For the acquisition times of each individual card
plot_times = fig.add_subplot(111)
#plot_times.set_xticks([])
#plot_times.set_ylim(3.4,5)
plot_times.axhline(y=4, color="black", linestyle="--")
plot_times.grid()
#plot_times2 = fig.add_subplot(122); plot_times2.set_xticks([])

plotCanvas = FigureCanvasTkAgg(fig, master=syncFrame)
plotCanvas.get_tk_widget().grid(row=0,column=2)
plotCanvas.draw()

naviFrame = Frame(syncFrame); naviFrame.grid(row=0,column=3)
navi = NavigationToolbar(plotCanvas, naviFrame)


#-------------#
# Cards frame #
#-------------#
# This is the main frame of the GUI, which contains one control window for each digitizer card attached.
cardsFrame = Frame(root, bg="#003366"); cardsFrame.grid(row=2,column=0)


class telescope(object):

	def __init__(self, tel_number, tel_name, spcm_port, datapath, port, mode):
		self.tel_number  = int(tel_number)
		self.spcm_port   = int(spcm_port) # Tells the card command file which card to control
		self.server_port = int(port)
		self.mode        = str(mode) # Tells the card whether to use the ethernet data transfer mode
		print ("Initializing new telescope {} at position {}".format(tel_name, tel_number))

		# Plotting objects
		self.wf_canvas = None
		self.wf_a_line = None; self.wf_b_line = None
		self.rates_a_line = None; self.rates_b_line = None
		self.acquisition_times = []; self.acq_plot, = plot_times.plot([0,1,2,3,4],[0,1,4,9,16], ".-"); plotCanvas.draw()
		# Arrays with the photon rates
		self.rates_a = []; self.rates_b = []
		# maximum allowed rates, will be assigned at calibration
		self.rmax_a = None; self.rmax_b = None
		# Initially just fill the rate arrays with zero
		for i in range(0,100):
			self.rates_a.append(0); self.rates_b.append(0)
		# Paths for data storage. Will be assigned when a new project is created
		self.basicpath = None
		self.calibpath = None

		# Initialize some threads
		gl.stop_offset_thread.append(False) # For stopping the offset calculation thread
		gl.stop_calib_thread.append(False)  # For stopping the calibration calculation thread

		# Rate calculation boolean
		self.calc_rate = False
	
		# This is the general frame for this telescope/card
		self.cardFrame = Frame(cardsFrame); self.cardFrame.grid(row=0, column=self.tel_number, padx=10, pady=10)
		self.leftFrame     = Frame(self.cardFrame); self.leftFrame.grid(row=0,column=0)     # for settings and plotting
		self.rateFrame     = Frame(self.cardFrame); self.rateFrame.grid(row=0,column=1)     # for the rate bars
		self.rootMainFrame = Frame(self.cardFrame); self.rootMainFrame.grid(row=0,column=2) # for the calibrations and data acquisition commands

		# Initialize the digitizer card
		self.card = cc.card(spcm_port=self.spcm_port, mode=self.mode)

		################
		## LEFT FRAME ##
		################
		# Display the telescope and the corresponding digitizer card
		self.optionLabel = Label(self.leftFrame, text="{}".format(tel_name)+"\n{0} sn {1:05d}\n".format(self.card.sCardName, self.card.lSerialNumber.value), font=("Helvetica 12 bold")); self.optionLabel.grid(row=2,column=0)
		# The card option frame will contain all the settings for the individual card #
		self.coptionFrame = Frame(self.leftFrame); self.coptionFrame.grid(row=4,column=0)
		# We initialize a settings list for the telescope
		self.settings = gl.settings()
		self.card.init(samples=self.settings.o_samples, nchn=self.settings.o_nchn)

		# Number of samples for each measurement/data acquisition
		self.sampleFrame = Frame(self.coptionFrame); self.sampleFrame.grid(row=1,column=0)
		self.samples = StringVar(root); self.samples.set("8 MS")
		self.sampleoptions = {
			"1 MS": 1048576, "2 MS": 2097152, "4 MS": 4194304, "8 MS": 8388608, "16 MS": 16777216, "32 MS": 33554432, "64 MS": 67108864,
			"128 MS": 134217728, "256 MS": 268435456, "512 MS": 536870912,
			"1 GS": 1073741824, "2 GS": 2147483648
		}		
		self.samplesDropdownLabel = Label(self.sampleFrame, text="File Sample Size"); self.samplesDropdownLabel.grid(row=0,column=0)
		self.samplesDropdown = OptionMenu(self.sampleFrame, self.samples, *self.sampleoptions, command=self.new_samples)
		self.samplesDropdown.grid(row=0, column=1)

		# Sampling frequency
		self.binningFrame = Frame(self.coptionFrame); self.binningFrame.grid(row=1,column=1)
		self.binningLabel = Label(self.binningFrame, text="Time sampling", width=12); self.binningLabel.grid(row=0,column=0)
		self.binning = DoubleVar(root); self.binning.set(1.6e-9)		
		self.binning08Button = Radiobutton(self.binningFrame, width=6, text="0.8 ns", indicatoron=False, variable=self.binning, value=0.8e-9, command=self.new_binning); self.binning08Button.grid(row=0,column=1)
		self.binning16Button = Radiobutton(self.binningFrame, width=6, text="1.6 ns", indicatoron=False, variable=self.binning, value=1.6e-9, command=self.new_binning); self.binning16Button.grid(row=0,column=2)
		self.binning32Button = Radiobutton(self.binningFrame, width=6, text="3.2 ns", indicatoron=False, variable=self.binning, value=3.2e-9, command=self.new_binning); self.binning32Button.grid(row=0,column=3)
		self.binning64Button = Radiobutton(self.binningFrame, width=6, text="6.4 ns", indicatoron=False, variable=self.binning, value=6.4e-9, command=self.new_binning); self.binning64Button.grid(row=0,column=4)

		# Voltage range
		self.voltageFrame = Frame(self.coptionFrame); self.voltageFrame.grid(row=2,column=1)
		self.voltageLabel = Label(self.voltageFrame, text="Voltage range", width=12); self.voltageLabel.grid(row=0,column=0)
		self.voltages = IntVar(root); self.voltages.set(200)
		self.voltage040Button = Radiobutton(self.voltageFrame, width=6, text=" 40 mV", indicatoron=False, variable=self.voltages, value= 40, command=self.new_voltages); self.voltage040Button.grid(row=0,column=1)
		self.voltage100Button = Radiobutton(self.voltageFrame, width=6, text="100 mV", indicatoron=False, variable=self.voltages, value=100, command=self.new_voltages); self.voltage100Button.grid(row=0,column=2)
		self.voltage200Button = Radiobutton(self.voltageFrame, width=6, text="200 mV", indicatoron=False, variable=self.voltages, value=200, command=self.new_voltages); self.voltage200Button.grid(row=0,column=3)
		self.voltage500Button = Radiobutton(self.voltageFrame, width=6, text="500 mV", indicatoron=False, variable=self.voltages, value=500, command=self.new_voltages); self.voltage500Button.grid(row=0,column=4)

		# Channels
		self.channelFrame = Frame(self.coptionFrame); self.channelFrame.grid(row=2,column=0)
		self.channelLabel = Label(self.channelFrame, text="Channels"); self.channelLabel.grid(row=0,column=0)
		self.channels = IntVar(root); self.channels.set(2)
		self.channel1Button = Radiobutton(self.channelFrame, width=5, text="1", indicatoron=False, variable=self.channels, value=1, command=self.new_nchn); self.channel1Button.grid(row=0,column=1)
		self.channel2Button = Radiobutton(self.channelFrame, width=5, text="2", indicatoron=False, variable=self.channels, value=2, command=self.new_nchn); self.channel2Button.grid(row=0,column=2)

		# Clockmode
		self.clockFrame = Frame(self.coptionFrame); self.clockFrame.grid(row=3,column=0)
		self.clockmodeLabel = Label(self.clockFrame, text="Clock"); self.clockmodeLabel.grid(row=0,column=0)
		self.clockmode = IntVar(); self.clockmode.set(2)
		self.clockInternButton = Radiobutton(self.clockFrame, width=8, text="Internal", indicatoron=False, variable=self.clockmode, value=1, command=self.new_clockmode); self.clockInternButton.grid(row=0,column=1)
		self.clockExternButton = Radiobutton(self.clockFrame, width=8, text="External", indicatoron=False, variable=self.clockmode, value=2, command=self.new_clockmode); self.clockExternButton.grid(row=0,column=2)

		# Trigger
		self.triggerFrame = Frame(self.coptionFrame); self.triggerFrame.grid(row=3,column=1)
		self.triggerLabel = Label(self.triggerFrame, text="External Trigger"); self.triggerLabel.grid(row=0,column=0)
		self.triggerButton = Button(self.triggerFrame, text="Off", width=5, command=self.toggle_trigger); self.triggerButton.grid(row=0,column=1)

		# Quick settings
		self.qsettingsFrame = Frame(self.leftFrame); self.qsettingsFrame.grid(row=3,column=0)
		self.quickSettingsLabel   = Label (self.qsettingsFrame, bg="#f5dbff", text="Quick Settings"); self.quickSettingsLabel.grid(row=1,column=0)
		self.checkWaveformsButton = Button(self.qsettingsFrame, bg="#f5dbff", width=18, text="Standard Observe",   command=self.qsettings_checkWaveform);     self.checkWaveformsButton.grid(row=1,column=1)
		self.calibrationsButton   = Button(self.qsettingsFrame, bg="#f5dbff", width=12, text="Calibrations",       command=self.qsettings_calibrations);      self.calibrationsButton.grid(row=1,column=2)
		self.syncedMeasButton     = Button(self.qsettingsFrame, bg="#f5dbff", width=20, text="Synced Measurement", command=self.qsettings_syncedMeasurement); self.syncedMeasButton.grid(row=1,column=3)

		#--- Measurement Frame ---#
		# Single measurement
		self.measurementLabel = Label(self.leftFrame, text="Measurement Control", font=("Helvetica 12 bold")); self.measurementLabel.grid(row=5,column=0)
		self.measurementFrame = Frame(self.leftFrame); self.measurementFrame.grid(row=6,column=0)
		self.singleMeasurementButton = Button(self.measurementFrame, text="Single Measurement", command=self.takeMeasurement); self.singleMeasurementButton.grid(row=0,column=0)
		# Measurement loop
		self.measloop = False
		self.loopMeasurementButton = Button(self.measurementFrame, text="Start Loop", width=10, bg="#e8fcae", command=self.loopMeasurement); self.loopMeasurementButton.grid(row=0,column=1)
		# File name entry
		self.measFileNameEntry = Entry(self.measurementFrame, width=15); self.measFileNameEntry.grid(row=0,column=2,padx=5); self.measFileNameEntry.insert(0,"data")
		# For remote measurements
		self.awaitR = False

		#--- Display Frame ---#
		# Frame for plotting the waveforms and the photon rates
		self.displayFrame = Frame(self.leftFrame); self.displayFrame.grid(row=7,column=0)
		self.wf_fig = Figure(figsize=(5,5))
		# Plot waveforms
		self.wf_a = []; self.wf_b = []
		self.wf_sub = self.wf_fig.add_subplot(211); self.wf_sub.grid()
		self.wf_a_line, = self.wf_sub.plot(self.wf_a, color=chAcolor); self.wf_b_line, = self.wf_sub.plot(self.wf_b, color=chBcolor)
		self.wf_sub.set_xlim(0,1000); self.wf_sub.set_ylim(-127,10)
		# Plot rates
		self.rates_sub = self.wf_fig.add_subplot(212); self.rates_sub.grid()
		self.rates_a_line, = self.rates_sub.plot(self.rates_a, color=chAcolor); self.rates_b_line, = self.rates_sub.plot(self.rates_b, color=chBcolor)
		self.rates_sub.set_xlim(-99,0)
		# Assign plots to canvas/frame
		self.wf_canvas = FigureCanvasTkAgg(self.wf_fig, master=self.displayFrame)
		self.wf_canvas.get_tk_widget().grid(row=0,column=0)
		self.wf_canvas.draw()

		##############
		# Rate frame #
		##############
		# This is the frame containing the small bars which display the rates relative to the maximum allowed rate		
		self.rateACanvas = Canvas(self.rateFrame, width=r_width, height=r_height, bg="gray"); self.rateACanvas.grid(row=0,column=0)
		self.rateBCanvas = Canvas(self.rateFrame, width=r_width, height=r_height, bg="gray"); self.rateBCanvas.grid(row=0,column=1)
		
		# Forbidden rate area is 20% of rate bar
		self.rateAforb = self.rateACanvas.create_rectangle(0,0,r_width,0.2*r_height, fill="orange", stipple="gray50")
		self.rateBforb = self.rateBCanvas.create_rectangle(0,0,r_width,0.2*r_height, fill="orange", stipple="gray50")
		
		# Rate displaying lines
		self.rateALine = self.rateACanvas.create_line(0,r_height,r_width,r_height, fill="red", width=5)
		self.rateBLine = self.rateBCanvas.create_line(0,r_height,r_width,r_height, fill="red", width=5)
		
		# Maximum rate text, set to -- initially
		self.rmaxaText = self.rateACanvas.create_text(r_width/2,0.2*r_height, fill="white", text="--")
		self.rmaxbText = self.rateBCanvas.create_text(r_width/2,0.2*r_height, fill="white", text="--")

		#####################
		## ROOT MAIN FRAME ##
		#####################
		# This is the frame which will contain all the calibration stuff.
		# For historical reasons (bc this is how the whole GUI started), it is called the root main frame

		# Small "LED" indicating if a measurement is running on this telescope
		# It will be used for the synchronized measurements to indicate which telescopes are lacking if it doesn't work properly
		self.ledFrame = Frame(self.rootMainFrame); self.ledFrame.grid(row=0,column=0)
		self.waitCanvas = Canvas(self.ledFrame, width=20,height=20); self.waitCanvas.grid(row=0,column=1)
		self.waitLED = self.waitCanvas.create_rectangle(1,1,20,20, fill="black", width=0)

		# Attribute calibration data for offset and calibration
		self.calibs = gl.calibs()

		#----------------#
		#- OFFSET FRAME -#
		#----------------#
		# Here the offset measurement will be taken and can be analyzed to find the ADC offset values
		self.offsetFrame = Frame(self.rootMainFrame, background="#e8fcae"); self.offsetFrame.grid(row=1,column=0)
		self.offsetHeader = Frame(self.offsetFrame, background="#e8fcae"); self.offsetHeader.grid(row=0,column=0)
		self.offsetHeaderLabel = Label(self.offsetHeader, text="Offset", background="#e8fcae", font=("Helvetica 12 bold")); self.offsetHeaderLabel.grid(row=0,column=0)
		self.offsetLLabel = Label(self.offsetHeader, text="l", background="#e8fcae"); self.offsetLLabel.grid(row=0,column=1)
		self.offsetLEntry = Entry(self.offsetHeader, width=8); self.offsetLEntry.grid(row=0,column=2); self.offsetLEntry.insert(0,"1000000")
		self.offsetPLabel = Label(self.offsetHeader, text="p", background="#e8fcae"); self.offsetPLabel.grid(row=0,column=3)
		self.offsetPEntry = Entry(self.offsetHeader, width=5); self.offsetPEntry.grid(row=0,column=4); self.offsetPEntry.insert(0,"2000")
		
		self.offsetBasicFrame = Frame(self.offsetFrame, background="#e8fcae"); self.offsetBasicFrame.grid(row=1,column=0)
		self.takeOffsetButton = Button(self.offsetBasicFrame, text="Measure", background="#e8fcae", width=15, command=self.takeOffsetMeasurement); self.takeOffsetButton.grid(row=0,column=0)
		self.offsetNameEntry = Entry(self.offsetBasicFrame, width=15); self.offsetNameEntry.grid(row=0,column=1); self.offsetNameEntry.insert(0,"off.bin")
		self.selectOffsetFileButton = Button(self.offsetBasicFrame, text="Select Offset Binary", width=15, background="#e8fcae", command=self.selectOffsetFile); self.selectOffsetFileButton.grid(row=1,column=0)
		self.offsetFileLabel = Label(self.offsetBasicFrame, text="no file selected", background="#e8fcae"); self.offsetFileLabel.grid(row=1,column=1)
		
		self.loadOffsetButton = Button(self.offsetBasicFrame, text="Load Offset", width=15, background="#e8fcae", command=self.loadOffset); self.loadOffsetButton.grid(row=2,column=0)
		self.loadOffsetLabel = Label(self.offsetBasicFrame, text="no file selected", background="#e8fcae"); self.loadOffsetLabel.grid(row=2,column=1)
		self.displayOffsetButton = Button(self.offsetBasicFrame, text="Display Offset", width=15, background="#e8fcae", command=self.displayOffset); self.displayOffsetButton.grid(row=3, column=0)
		self.displayWaveformOffsetButton = Button(self.offsetBasicFrame, text="Display Waveform", background="#e8fcae", command=self.displayWaveformOffset); self.displayWaveformOffsetButton.grid(row=3,column=1)
		# Offset parameters
		self.offsetParamFrame = Frame(self.offsetFrame, background="#e8fcae"); self.offsetParamFrame.grid(row=2,column=0)
		self.offsetParLabel = Label(self.offsetParamFrame, text="Parameter", font=("Helvetica 10 bold"), background="#e8fcae"); self.offsetParLabel.grid(row=0,column=0)
		self.offsetALabel = Label(self.offsetParamFrame, text="CHN A", font=("Helvetica 10 bold"), background="#e8fcae"); self.offsetALabel.grid(row=0,column=1)
		self.offsetBLabel = Label(self.offsetParamFrame, text="CHN B", font=("Helvetica 10 bold"), background="#e8fcae"); self.offsetBLabel.grid(row=0,column=2)
		self.parOffsetLabel = Label(self.offsetParamFrame, text="Baseline offset", background="#e8fcae"); self.parOffsetLabel.grid(row=6,column=0)
		self.parOffsetLabelA = Label(self.offsetParamFrame, text="{:.2f}".format(self.calibs.off_a), background="black", fg="orange"); self.parOffsetLabelA.grid(row=6,column=1)
		self.parOffsetLabelB = Label(self.offsetParamFrame, text="{:.2f}".format(self.calibs.off_b), background="black", fg="orange"); self.parOffsetLabelB.grid(row=6,column=2)
		# Offset Start and Stop
		self.offsetDoFrame = Frame(self.offsetFrame, background="#e8fcae"); self.offsetDoFrame.grid(row=3,column=0)
		self.offsetButton = Button(self.offsetDoFrame, text="Calc Offset", background="#e8fcae", command=self.start_offset_thread); self.offsetButton.grid(row=0,column=0)
		self.stopOffsetButton = Button(self.offsetDoFrame, text="Abort", background="#fa857a", command=self.stop_offset_thread); self.stopOffsetButton.grid(row=0,column=1)

		#---------------------#
		#- CALIBRATION FRAME -#
		#---------------------#
		# Here the calibration measurement will be taken and can be analyzed to find pulse height distribution, peak shape etc.
		self.calibFrame = Frame(self.rootMainFrame, background="#ccf2ff"); self.calibFrame.grid(row=2, column=0)
		self.calibHeader = Frame(self.calibFrame, background="#ccf2ff"); self.calibHeader.grid(row=0,column=0)
		self.calibHeaderLabel = Label(self.calibHeader, text="Calibration", background="#ccf2ff", font=("Helvetica 12 bold")); self.calibHeaderLabel.grid(row=0,column=0)
		self.calibLLabel = Label(self.calibHeader, text="l", background="#ccf2ff"); self.calibLLabel.grid(row=0,column=1)
		self.calibLEntry = Entry(self.calibHeader, width=8); self.calibLEntry.grid(row=0,column=2); self.calibLEntry.insert(0,"1000000")
		self.calibPLabel = Label(self.calibHeader, text="p", background="#ccf2ff"); self.calibPLabel.grid(row=0,column=3)
		self.calibPEntry = Entry(self.calibHeader, width=5); self.calibPEntry.grid(row=0,column=4); self.calibPEntry.insert(0,"200")
		# A thread for calibration procedures
		self.calib_thread = []
		# The frame for buttons etc
		self.calibGeneralFrame = Frame(self.calibFrame, background="#ccf2ff"); self.calibGeneralFrame.grid(row=1,column=0)
		# ... and all the buttons etc
		self.measureCalibButton = Button(self.calibGeneralFrame, text="Measure", width=15, bg="#ccf2ff", command=self.takeCalibMeasurement); self.measureCalibButton.grid(row=0,column=0)
		self.calibNameEntry = Entry(self.calibGeneralFrame, width=15); self.calibNameEntry.grid(row=0,column=1); self.calibNameEntry.insert(0,"calib.bin")
		self.selectCalibFileButton = Button(self.calibGeneralFrame, text="Select Calib Binary", width=15, command=self.selectCalibFile, background="#ccf2ff"); self.selectCalibFileButton.grid(row=1, column=0)
		self.calibFileLabel = Label(self.calibGeneralFrame, text="no file selected", background="#ccf2ff"); self.calibFileLabel.grid(row=1, column=1)
		self.loadCalibButton = Button(self.calibGeneralFrame, text="Load calibration", width=15, command=self.loadCalibration, background="#ccf2ff"); self.loadCalibButton.grid(row=2,column=0)
		self.loadCalibLabel = Label(self.calibGeneralFrame, text="no file selected", background="#ccf2ff"); self.loadCalibLabel.grid(row=2,column=1)		
		self.displayCalibrationButton = Button(self.calibGeneralFrame, text="Display calib", background="#ccf2ff", width=15, command=self.displayCalibration); self.displayCalibrationButton.grid(row=3,column=0)
		self.displayWaveformButton = Button(self.calibGeneralFrame, text="Display waveform", background="#ccf2ff", width=15, command=self.displayWaveform); self.displayWaveformButton.grid(row=3, column=1)
		# Calibration parameters
		self.calibParamFrame = Frame(self.calibFrame, background="#ccf2ff"); self.calibParamFrame.grid(row=2,column=0)
		
		self.calibParLabel      = Label(self.calibParamFrame, text="Parameter", font=("Helvetica 10 bold"), background="#ccf2ff"); self.calibParLabel.grid(row=0,column=0)
		self.calibALabel        = Label(self.calibParamFrame, text="CHN A", font=("Helvetica 10 bold"), background="#ccf2ff"); self.calibALabel.grid(row=0,column=1)
		self.calibBLabel        = Label(self.calibParamFrame, text="CHN B", font=("Helvetica 10 bold"), background="#ccf2ff"); self.calibBLabel.grid(row=0,column=2)		
		self.fitRangeLowLabel   = Label(self.calibParamFrame, text="lower fit border", background="#7ac5fa"); self.fitRangeLowLabel.grid(row=1, column=0)
		self.fitRangelowEntryA  = Entry(self.calibParamFrame, width=5); self.fitRangelowEntryA.grid(row=1, column=1); self.fitRangelowEntryA.insert(0,"-100")
		self.fitRangelowEntryB  = Entry(self.calibParamFrame, width=5); self.fitRangelowEntryB.grid(row=1, column=2); self.fitRangelowEntryB.insert(0,"-100")
		self.fitRangeHighLabel  = Label(self.calibParamFrame, text="upper fit border", background="#7ac5fa"); self.fitRangeHighLabel.grid(row=2, column=0)
		self.fitRangehighEntryA = Entry(self.calibParamFrame, width=5); self.fitRangehighEntryA.grid(row=2, column=1); self.fitRangehighEntryA.insert(0,"-5")
		self.fitRangehighEntryB = Entry(self.calibParamFrame, width=5); self.fitRangehighEntryB.grid(row=2, column=2); self.fitRangehighEntryB.insert(0,"-5")		
		self.minHeightLabel     = Label(self.calibParamFrame, text="Min pulse height", background="#ccf2ff"); self.minHeightLabel.grid(row=3, column=0)
		self.minHeightEntryA    = Entry(self.calibParamFrame, width=5); self.minHeightEntryA.grid(row=3,column=1); self.minHeightEntryA.insert(0,"-25")
		self.minHeightEntryB    = Entry(self.calibParamFrame, width=5); self.minHeightEntryB.grid(row=3,column=2); self.minHeightEntryB.insert(0,"-25")
		self.cleanHeightLabel   = Label(self.calibParamFrame, text="Clean pulse height", background="#ccf2ff"); self.cleanHeightLabel.grid(row=4, column=0)
		self.cleanHeightEntryA  = Entry(self.calibParamFrame, width=5); self.cleanHeightEntryA.grid(row=4,column=1); self.cleanHeightEntryA.insert(0,"-2")
		self.cleanHeightEntryB  = Entry(self.calibParamFrame, width=5); self.cleanHeightEntryB.grid(row=4,column=2); self.cleanHeightEntryB.insert(0,"-2")
		self.minPulsesLabel     = Label(self.calibParamFrame, text="Min pulses", background="#ccf2ff"); self.minPulsesLabel.grid(row=5, column=0)
		self.minPulsesEntryA    = Entry(self.calibParamFrame, width=5); self.minPulsesEntryA.grid(row=5,column=1); self.minPulsesEntryA.insert(0,"100")
		self.minPulsesEntryB    = Entry(self.calibParamFrame, width=5); self.minPulsesEntryB.grid(row=5,column=2); self.minPulsesEntryB.insert(0,"100")		
		self.avgChargeLabel     = Label(self.calibParamFrame, text="Avg charge", background="#ccf2ff"); self.avgChargeLabel.grid(row=6,column=0)
		self.avgChargeLabelA    = Label(self.calibParamFrame, text="--", background="black", fg="orange"); self.avgChargeLabelA.grid(row=6,column=1)
		self.avgChargeLabelB    = Label(self.calibParamFrame, text="--", background="black", fg="orange"); self.avgChargeLabelB.grid(row=6,column=2)
		
		# Calibration Start and Stop
		self.calibDoFrame = Frame(self.calibFrame, background="#ccf2ff"); self.calibDoFrame.grid(row=3,column=0)
		self.recalibrateButton = Button(self.calibDoFrame, text="Calibrate", background="#ccf2ff", command=self.start_calib_thread); self.recalibrateButton.grid(row=0,column=0)
		self.stopCalibrationButton = Button(self.calibDoFrame, text="Abort", background="#fa857a", command=self.stop_calib_thread); self.stopCalibrationButton.grid(row=0,column=1)
		self.CalibFitButton = Button(self.calibDoFrame, text="Only Fit", background="#ccf2ff", command=self.calibrate_newFit); self.CalibFitButton.grid(row=0,column=2)
		self.SecondCalibButton = Button(self.calibDoFrame, text="2nd Calib", background="#ccf2ff", command=self.secondCalibration); self.SecondCalibButton.grid(row=0,column=3)
		self.secondCalibState = False # Parameter checking if the second calibration is currently running

		######################
		### START/STOP FRAME ##
		#######################
		# This is the frame that contains all the 
		self.startstopFrame = Frame(self.rootMainFrame); self.startstopFrame.grid(row=4,column=0)

		self.startstopHeader = Frame(self.startstopFrame); self.startstopHeader.grid(row=0,column=0)
		self.startstopHeaderLabel = Label(self.startstopHeader, text="Rate analysis", font=("Helvetica 12 bold")); self.startstopHeaderLabel.grid(row=0,column=1)
		self.startstopLLabel      = Label(self.startstopHeader, text="l"); self.startstopLLabel.grid(row=0,column=2)
		self.startstopLEntry      = Entry(self.startstopHeader, width=8); self.startstopLEntry.grid(row=0,column=3); self.startstopLEntry.insert(0,"1000000")
		self.startstopPLabel      = Label(self.startstopHeader, text="p"); self.startstopPLabel.grid(row=0,column=4)
		self.startstopPEntry      = Entry(self.startstopHeader, width=5); self.startstopPEntry.grid(row=0,column=5); self.startstopPEntry.insert(0,"1")
		## Param Frame
		self.abFrame = Frame(self.startstopFrame); self.abFrame.grid(row=1,column=0)
		self.parLabel = Label(self.abFrame, text="Parameter", font=("Helvetica 10 bold")); self.parLabel.grid(row=0,column=0)
		self.aLabel   = Label(self.abFrame, text="CHN A", font=("Helvetica 10 bold")); self.aLabel.grid(row=0,column=1)
		self.bLabel   = Label(self.abFrame, text="CHN B", font=("Helvetica 10 bold")); self.bLabel.grid(row=0,column=2)
		# Amplifiers
		self.ampLabel           = Label(self.abFrame, text="Amp"); self.ampLabel.grid(row=1, column=0)
		self.ampAEntry          = Entry(self.abFrame, width=5); self.ampAEntry.grid(row=1, column=1); self.ampAEntry.insert(0,"10")
		self.ampBEntry          = Entry(self.abFrame, width=5); self.ampBEntry.grid(row=1, column=2); self.ampBEntry.insert(0,"10")
		self.desc_Label_mean    = Label(self.abFrame, text="Voltage [mV]"); self.desc_Label_mean.grid(row=2, column=0)
		self.desc_Label_curr    = Label(self.abFrame, text="PMT current [µA]"); self.desc_Label_curr.grid(row=3, column=0)
		self.desc_Label_rate    = Label(self.abFrame, text="Photon rate [MHz]");	self.desc_Label_rate.grid(row=4, column=0)
		self.desc_Label_avgrate = Label(self.abFrame, text="100-Avg rate");	self.desc_Label_avgrate.grid(row=5, column=0)
		#
		self.CHa_Label_mean    = Label(self.abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); self.CHa_Label_mean.grid(row=2, column=1)
		self.CHb_Label_mean    = Label(self.abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); self.CHb_Label_mean.grid(row=2, column=2)
		self.CHa_Label_curr    = Label(self.abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); self.CHa_Label_curr.grid(row=3, column=1, pady=2)
		self.CHb_Label_curr    = Label(self.abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 10 bold")); self.CHb_Label_curr.grid(row=3, column=2, pady=2)
		self.CHa_Label_rate    = Label(self.abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 12 bold"));	self.CHa_Label_rate.grid(row=4, column=1, padx=3)
		self.CHb_Label_rate    = Label(self.abFrame, text="0.0", fg="orange", bg="black", width=5, font=("Helvetica 12 bold"));	self.CHb_Label_rate.grid(row=4, column=2)
		self.CHa_Label_avgrate = Label(self.abFrame, text="0.0", fg="orange", bg="grey", width=5, font=("Helvetica 10 bold"));  self.CHa_Label_avgrate.grid(row=5, column=1, padx=3)
		self.CHb_Label_avgrate = Label(self.abFrame, text="0.0", fg="orange", bg="grey", width=5, font=("Helvetica 10 bold"));  self.CHb_Label_avgrate.grid(row=5, column=2)

		#################################
		## START FRAME AND QUICK FRAME ##
		#################################
		# These two small frames contain functionalities for quickly taking small measurements
		self.startFrame = Frame (self.rootMainFrame); self.startFrame.grid(row=5, column=0)
		self.running = False; self.stop_thread = False; self.plotting = False
		# For plotting
		self.plotFig = []; self.rate_a_plot = []; self.rate_b_plot = []
		self.wav_a = []; self.wav_b = []
	
		self.running_quick = False
		self.quickFrame = Frame(self.rootMainFrame); self.quickFrame.grid(row=6,column=0)
		self.quickRatesButton = Button(self.quickFrame, text="Start quick", bg="#e8fcae", width=9, command=self.startstop_quick); self.quickRatesButton.grid(row=0, column=0)
		self.singleRatesButton = Button(self.quickFrame, text="Single", width=5, command=self.analysis); self.singleRatesButton.grid(row=0,column=1)

		##################
		## Server Stuff ##
		##################
		# This is for the communication with the motor box raspis
		self.server = None
		self.socketFrame = Frame(self.rootMainFrame, bg="#f7df72"); self.socketFrame.grid(row=7,column=0)
		self.socketHeaderLabel = Label(self.socketFrame, text="Network", font=("Helvetica 12 bold"), bg="#f7df72"); self.socketHeaderLabel.grid(row=0,column=0)
		gl.motorServerButton.append( Button(self.socketFrame, text="Start Server (Motor)", bg="#cdcfd1", command=self.startStopServerMotor, width=20) ); gl.motorServerButton[self.tel_number].grid(row=1,column=0)

		#############################
		## STATUS FRAME AND BUTTON ##
		#############################
		self.statusFrame = Frame (self.rootMainFrame); self.statusFrame.grid(row=8, column=0)
		gl.statusLabel.append( Label(self.statusFrame, text="Starting ...", font=("Helvetica 12 bold"), bg="#ffffff") ); gl.statusLabel[self.tel_number].grid(row=0, column=0)

		self.idle()
		

	# --- Functions for applying the settings --- #
	# Function for setting the number of samples per acquisition
	def new_samples(self, val):
		self.settings.o_samples = int((self.sampleoptions[self.samples.get()]))
		self.card.set_sample_size(self.settings.o_samples)
	# Function for setting a new binning = sample frequency
	def new_binning(self):
		self.settings.o_binning = self.binning.get()
		self.card.set_sampling(self.settings.o_binning)
	# Function for setting the voltage range
	def new_voltages(self):
		self.settings.o_voltages = self.voltages.get()
		self.card.set_voltage_range(self.settings.o_voltages)
	# Function for setting the number of channels
	def new_nchn(self):
		ch_old = self.settings.o_nchn
		ch_new = self.channels.get()
		if ch_new != ch_old:
			self.settings.o_nchn = ch_new
			self.calc_rate = False
			self.card.set_channels(self.settings.o_nchn)
	# Function for clock mode
	def new_clockmode(self):
		self.settings.clockmode = self.clockmode.get()
		self.card.set_clockmode(self.settings.clockmode)
	# Function for switching the trigger on/off
	def toggle_trigger(self):
		if self.settings.trigger == False:
			self.settings.trigger = True
			self.triggerButton.config(text="On")
		elif self.settings.trigger == True:
			self.settings.trigger = False
			self.triggerButton.config(text="Off")
		self.card.set_triggermode(self.settings.trigger)

	# --- Functions for applying quick settings --- #
	def qsettings_checkWaveform(self):
		self.samples.set("8 MS"); self.new_samples(0)
		self.binning16Button.invoke()
		self.voltage200Button.invoke()
		if self.settings.trigger == True:
			self.toggle_trigger()
		self.card.init_display(samples=self.settings.o_samples, nchn=self.settings.o_nchn)
	def qsettings_syncedMeasurement(self):
		self.samples.set("2 GS"); self.new_samples(0)
		self.binning16Button.invoke()
		self.voltage200Button.invoke()
		self.clockExternButton.invoke()
		if self.settings.trigger == False:
			self.toggle_trigger()
		self.card.init_storage()
	def qsettings_calibrations(self):
		self.samples.set("2 GS"); self.new_samples(0)
		self.binning16Button.invoke()
		self.voltage200Button.invoke()
		#self.clockExternButton.invoke() # TODO: Find a nice way of not stopping the program if no external clock is found
		#if self.settings.trigger == True:
		#	self.toggle_trigger()
		self.card.init_storage()

	# --- Functions for the measurement frame --- #
	def takeMeasurement(self):
		self.card.init_storage()
		filename = self.basicpath + "/" + self.measFileNameEntry.get() + ".bin"
		ma, mb, a_rec, b_rec, t_acq = self.card.measurement(filename, nchn=self.settings.o_nchn, samples=self.settings.o_samples)
		self.update_waveform(a_rec, b_rec)
		self.calculate_data(ma, mb)
		self.card.init_display(samples=self.settings.o_samples, nchn=self.settings.o_nchn)
	def loopMeasurement(self):
		if self.measloop == False:
			self.measloop = True
			self.loopMeasurementButton.config(text="Stop loop", bg="#fa857a")
			self.loopThread = Thread(target=self.doLoopMeasurement)
			self.loopThread.start()
		elif self.measloop == True:
			self.measloop = False
			self.loopMeasurementButton.config(text="Start loop", bg="#e8fcae")
	def doLoopMeasurement(self):
		self.card.init_storage()
		header.write_header(name=self.measFileNameEntry.get(), path=self.basicpath, nchn=self.settings.o_nchn, voltages=self.settings.o_voltages, samples=self.settings.o_samples)
		fileindex = 0
		while self.measloop == True:
			filename = self.basicpath + "/" + self.measFileNameEntry.get() + "_" + uti.numberstring(fileindex) + ".bin"
			ma, mb, rec_a, rec_b, t_acq = self.card.measurement(filename, nchn=self.settings.o_nchn, samples=self.settings.o_samples)
			self.calculate_data(ma, mb)
			fileindex += 1	
		self.card.init_display(samples=self.settings.o_samples, nchn=self.settings.o_nchn)
	def remote_measurement(self, name, index):
		filename = self.basicpath + "/" + name + "_" + uti.numberstring(index) + ".bin"
		ma, mb, a_rec, b_rec, t_acq = self.card.measurement(filename, nchn=self.settings.o_nchn, samples=self.settings.o_samples)
		self.update_waveform(a_rec, b_rec)
		self.calculate_data(ma, mb)
		self.acquisition_times.append(t_acq)
		self.awaitR = False; self.waitCanvas.itemconfig(self.waitLED, fill="green"); root.update()

	# --- Functions for the display frame --- #
	def update_waveform(self, a,b):
		self.wf_a_line.set_xdata(np.arange(0,len(a))); self.wf_a_line.set_ydata(a)
		self.wf_b_line.set_xdata(np.arange(0,len(b))); self.wf_b_line.set_ydata(b)
		self.wf_canvas.draw()
	def update_rate_plot(self):
		self.rates_a_line.set_xdata(np.arange(-len(self.rates_a),0)); self.rates_a_line.set_ydata(self.rates_a)
		self.rates_b_line.set_xdata(np.arange(-len(self.rates_b),0)); self.rates_b_line.set_ydata(self.rates_b)
		self.wf_canvas.draw()
		self.rates_sub.set_ylim( np.min( [np.min(self.rates_a),np.min(self.rates_b)] ), np.max( [np.max(self.rates_a),np.max(self.rates_b)]) )

	# --- Functions for the rate bars: maximum rate ans position of indicators --- #
	# Calculate maximum allowed rate
	def maxRate(self, avg_charge):
		return -0.000635 * float(self.ampAEntry.get()) / avg_charge / self.settings.o_binning / self.settings.o_voltages
	# Calculate positions of rate lines and place them there
	def placeRateLineA(self, rate):
		lineposition = r_height - (rate/self.rmax_a * 0.8 * r_height)
		self.rateACanvas.coords(self.rateALine, 0, lineposition, r_width, lineposition)
	def placeRateLineB(self, rate):
		lineposition = r_height - (rate/self.rmax_b * 0.8 * r_height)
		self.rateBCanvas.coords(self.rateBLine, 0, lineposition, r_width, lineposition)

	#-----------------------------------------------#
	# --- Functions for the offset measurements --- #
	#-----------------------------------------------#
	# Take offset measurement
	def takeOffsetMeasurement(self):
		self.qsettings_calibrations()
		filename = self.basicpath + "/" + self.offsetNameEntry.get()
		# Send the command to take data. The return parameters are the mean of both channels (ma, mb) and 1000 datapoints of each channel for plotting the waveforms
		ma, mb, a_rec, b_rec, t_acq = self.card.measurement(filename, nchn=self.settings.o_nchn, samples=self.settings.o_samples)
		self.update_waveform(a_rec, b_rec)
		self.calculate_data(ma, mb)
		self.qsettings_checkWaveform()
		self.calibs.offsetFile = filename; self.offsetFileLabel.config(text=self.calibs.offsetFile.split("/")[-1])
	# Select offset binary file for offset investigations
	def selectOffsetFile(self):
		root.filename = filedialog.askopenfilename(initialdir = self.basicpath, title = "Select offset file", filetypes = (("binary files","*.bin"),("all files","*.*")))
		self.calibs.offsetFile = root.filename; self.offsetFileLabel.config(text=self.calibs.offsetFile.split("/")[-1])
	# Load already existing .off or .off1 file
	def loadOffset(self):
		if self.settings.o_nchn == 2:
			root.filename = filedialog.askopenfilename(initialdir = self.calibpath, title = "Load offset calculation", filetypes = (("calib files","*.off"),("all files","*.*")))
			self.calibs.offsetLoad = root.filename; self.loadOffsetLabel.config(text=self.calibs.offsetLoad.split("/")[-1])	
			self.calibs.off_a = np.loadtxt(self.calibs.offsetLoad)[0]; self.parOffsetLabelA.config(text="{:.2f}".format(self.calibs.off_a))
			self.calibs.off_b = np.loadtxt(self.calibs.offsetLoad)[1]; self.parOffsetLabelB.config(text="{:.2f}".format(self.calibs.off_b))
		if self.settings.o_nchn == 1:
			root.filename = filedialog.askopenfilename(initialdir = self.calibpath, title = "Load offset calculation", filetypes = (("calib files","*.off1"),("all files","*.*")))
			self.calibs.offsetLoad = root.filename; self.loadOffsetLabel.config(text=self.calibs.offsetLoad.split("/")[-1])	
			self.calibs.off_a = np.loadtxt(self.calibs.offsetLoad); self.parOffsetLabelA.config(text="{:.2f}".format(self.calibs.off_a))
			self.parOffsetLabelB.config(text="--")
		self.calibs.offsetFile = uti.to_bin(self.calibs.offsetLoad); self.offsetFileLabel.config(text=self.calibs.offsetFile.split("/")[-1])
	# Display part of the waveform and horizontal offset lines
	def displayOffset(self):
		wv_off_a, wv_off_b = wv.execute(file=self.calibs.offsetFile, length=int(int(self.offsetLEntry.get())/10), nchn=self.settings.o_nchn)
		plt.figure("Offset calculations", figsize=(10,6))
		print (wv_off_a)
		plt.plot(wv_off_a, label="Channel A", color=chAcolor, alpha=0.4); plt.axhline(y=self.calibs.off_a, color=chAcolor)
		if self.settings.o_nchn == 2:
			plt.plot(wv_off_b, label="Channel B", color=chBcolor , alpha=0.4); plt.axhline(y=self.calibs.off_b, color=chBcolor)
		plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(self.calibs.offsetFile); plt.show()
	# Simply display part of the waveform
	def displayWaveformOffset(self):
		wv_off_a, wv_off_b = wv.execute(file=self.calibs.offsetFile, length=int(int(self.offsetLEntry.get())/10), nchn=self.settings.o_nchn)
		plt.figure("Offset file waveforms", figsize=(10,6))
		plt.plot(wv_off_a, label="Channel A", color=chAcolor)
		if self.settings.o_nchn == 2:
			plt.plot(wv_off_b, label="Channel B", color=chBcolor)
		plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(self.calibs.offsetFile); plt.show()
	# Do the offset measurement
	def off_measurement(self):
		gl.statusLabel[self.tel_number].config(text="Calculate Offset", bg="#edda45"); root.update()
		self.calibs.off_a, self.calibs.off_b = off.execute(file=self.calibs.offsetFile, packet_length=int(self.offsetLEntry.get()), npackets=int(self.offsetPEntry.get()), nchn=self.settings.o_nchn, tel_number=self.tel_number)
		if gl.stop_offset_thread[self.tel_number]==False:
			self.parOffsetLabelA.config(text="{:.2f}".format(self.calibs.off_a))
			if self.settings.o_nchn == 2:
				self.parOffsetLabelB.config(text="{:.2f}".format(self.calibs.off_b))
				outfileOff = uti.to_calib(self.calibs.offsetFile,".off")
				np.savetxt(outfileOff, [self.calibs.off_a, self.calibs.off_b])
			else:
				self.parOffsetLabelB.config(text="--")
				outfileOff = uti.to_calib(self.calibs.offsetFile,".off1")
				np.savetxt(outfileOff, [self.calibs.off_a])
			self.calibs.offsetLoad = outfileOff; self.loadOffsetLabel.config(text=self.calibs.offsetLoad.split("/")[-1])
		self.idle()
	def start_offset_thread(self):
		gl.stop_offset_thread[self.tel_number] = False
		self.offset_thread = Thread(target=self.off_measurement, args=())
		self.offset_thread.start()
	def stop_offset_thread(self):
		gl.stop_offset_thread[self.tel_number] = True


	#----------------------------------------------------#
	# --- Functions for the calibration measurements --- #
	#----------------------------------------------------#
	# Display pulse height distribution(s) including fit(s) and pulse shape(s)
	def displayCalibration(self):
		plt.figure("Calibration display", figsize=[10,6])
		plt.subplot(211)
		plt.plot(self.calibs.histo_x, self.calibs.histo_a, color=chAcolor, label="Channel A: Avg height = {:.2f}".format(self.calibs.ph_a), alpha=0.5)
		plt.plot(self.calibs.xplot, uti.gauss(self.calibs.xplot, *self.calibs.pa), color=chAcolor)
		plt.axvline(x=self.calibs.ph_a, color=chAcolor, linestyle="--")
		if self.settings.o_nchn == 2:
			plt.plot(self.calibs.histo_x, self.calibs.histo_b, color=chBcolor, label="Channel B: Avg height = {:.2f}".format(self.calibs.ph_b), alpha=0.5)
			plt.plot(self.calibs.xplot, uti.gauss(self.calibs.xplot, *self.calibs.pb), color=chBcolor)
			plt.axvline(x=self.calibs.ph_b, color=chBcolor, linestyle="--")
			plt.ylim(0,1.5*max(self.calibs.pa[0], self.calibs.pb[0]))
		else:
			plt.ylim(0,1.5*self.calibs.pa[0])
		plt.xlim(-128,10); plt.legend(); plt.title(self.calibs.calibFile)
		plt.subplot(212)
		plt.plot(self.calibs.ps_x, self.calibs.ps_a, color=chAcolor, label="Channel A: Sum = {:.2f}".format(self.calibs.nsum_a))
		if self.settings.o_nchn == 2:
			plt.plot(self.calibs.ps_x, self.calibs.ps_b, color=chBcolor, label="Channel B: Sum = {:.2f}".format(self.calibs.nsum_b))
		plt.legend(); plt.show()
	# Do the whole calibration
	def calibrate(self):
		# Create and fit pulse height distribution
		gl.statusLabel[self.tel_number].config(text="Calibrating: Pulse heights ...", bg="#edda45"); root.update()
		self.calibs.histo_x, self.calibs.histo_a, self.calibs.histo_b, self.calibs.pa, self.calibs.pb, self.calibs.ph_a, self.calibs.ph_b, self.calibs.xplot = fphd.execute(file=self.calibs.calibFile, nchn=self.settings.o_nchn, packet_length = int(self.calibLEntry.get()), npackets=int(self.calibPEntry.get()), range_a=[float(self.fitRangelowEntryA.get()),float(self.fitRangehighEntryA.get())], range_b=[float(self.fitRangelowEntryB.get()),float(self.fitRangehighEntryB.get())], tel_number=self.tel_number)
		# Create average pulse shape
		if gl.stop_calib_thread[self.tel_number] == False:
			gl.statusLabel[self.tel_number].config(text="Calibrating: Pulse shape ...", bg="#edda45"); root.update()
			self.calibs.nsum_a, self.calibs.nsum_b, self.calibs.ps_x, self.calibs.ps_a, self.calibs.ps_b = ps.execute(file=self.calibs.calibFile, nchn=self.settings.o_nchn, min_pulses = [int(self.minPulsesEntryA.get()),int(self.minPulsesEntryB.get())], height=[-1*int(self.minHeightEntryA.get()),-1*int(self.minHeightEntryB.get())], cleanheight=[-1*int(self.cleanHeightEntryA.get()),-1*int(self.cleanHeightEntryB.get())], tel_number=self.tel_number, off_a=self.calibs.off_a, off_b=self.calibs.off_b)
		if gl.stop_calib_thread[self.tel_number] == False:
			self.finish_calibration()
		# Activate Rate Buttons
		self.calc_rate = True
	
		self.idle()
	def finish_calibration(self): # Execute after pulse height distribution and pulse shape calculation are finished
		# Combine pulse height distribution and pulse shape to calculate avg charge
		self.calibs.avg_charge_a = self.calibs.nsum_a * self.calibs.ph_a; self.avgChargeLabelA.config(text="{:.2f}".format(self.calibs.avg_charge_a))
		self.rmax_a = self.maxRate(self.calibs.avg_charge_a) # Maximum rate
		self.rateACanvas.itemconfig(self.rmaxaText, text="{:.0f}".format(self.rmax_a)) # Show on rate bar
		if self.settings.o_nchn == 2:
			self.calibs.avg_charge_b = self.calibs.nsum_b * self.calibs.ph_b; self.avgChargeLabelB.config(text="{:.2f}".format(self.calibs.avg_charge_b))
			self.rmax_b = self.maxRate(self.calibs.avg_charge_b) # Maximum rate
			self.rateBCanvas.itemconfig(self.rmaxbText, text="{:.0f}".format(self.rmax_b)) # Show in rate bar
		else:
			self.avgChargeLabelB.config(text="--")
	
		# Create calibration files
		if self.settings.o_nchn == 2:
			np.savetxt(uti.to_calib(self.calibs.calibFile, ".phd"),   np.c_[self.calibs.histo_x, self.calibs.histo_a, self.calibs.histo_b])
			np.savetxt(uti.to_calib(self.calibs.calibFile, ".shape"), np.c_[self.calibs.ps_x, self.calibs.ps_a, self.calibs.ps_b])
			np.savetxt(uti.to_calib(self.calibs.calibFile, ".xplot"), self.calibs.xplot)
			with open(uti.to_calib(self.calibs.calibFile, ".calib"), 'w') as f:
				f.write("# Gaussian fit parameters of pulse height distribution Ch A\n")
				f.write(str(self.calibs.pa[0]) + "\t# Amplitude\n" +  str(self.calibs.pa[1]) + "\t# Mean\n" + str(self.calibs.pa[2]) + "\t# Sigma\n")
				f.write("# Gaussian fit parameters of pulse height distribution Ch B\n")
				f.write(str(self.calibs.pb[0]) + "\t# Amplitude\n" +  str(self.calibs.pb[1]) + "\t# Mean\n" + str(self.calibs.pb[2]) + "\t# Sigma\n")
				f.write("# Integrals of normalized pulses (nsum)\n")
				f.write(str(self.calibs.nsum_a) + "\t# Ch A\n" + str(self.calibs.nsum_b) + "\t# Ch B\n")
				f.write("# Pulse heights of phd (ph)\n")
				f.write(str(self.calibs.ph_a) + "\t# Ch A\n" +   str(self.calibs.ph_b) + "\t# Ch B\n")
				f.write("# Average Charges\n")
				f.write(str(self.calibs.avg_charge_a) + "\t# Ch A\n" + str(self.calibs.avg_charge_b) + "\t# Ch B\n")
				f.write("# 2nd stage calibration factors\n")
				f.write(str(self.calibs.corr_rates_a) + "\t# Ch A\n" + str(self.calibs.corr_rates_b) + "\t# Ch B")
			self.calibs.calibLoad = uti.to_calib(self.calibs.calibFile, ".calib")
		else:
			np.savetxt(uti.to_calib(self.calibs.calibFile, ".phd1"),   np.c_[self.calibs.histo_x, self.calibs.histo_a])
			np.savetxt(uti.to_calib(self.calibs.calibFile, ".shape1"), np.c_[self.calibs.ps_x, self.calibs.ps_a])
			np.savetxt(uti.to_calib(self.calibs.calibFile, ".xplot1"), self.calibs.xplot)
			with open(uti.to_calib(self.calibs.calibFile, ".calib1"), 'w') as f:
				f.write("# Gaussian fit parameters of pulse height distribution Ch A\n")
				f.write(str(self.calibs.pa[0]) + "\t# Amplitude\n" +  str(self.calibs.pa[1]) + "\t# Mean\n" + str(self.calibs.pa[2]) + "\t# Sigma\n")
				f.write("# Integral of normalized pulse (nsum)\n")
				f.write(str(self.calibs.nsum_a) + "\n")
				f.write("# Pulse height of phd (ph)\n")
				f.write(str(self.calibs.ph_a) + "\n")
				f.write("# Average Charge\n")
				f.write(str(self.calibs.avg_charge_a) + "\n")
				f.write("# 2nd stage calibration factor\n")
				f.write(str(self.calibs.corr_rates_a))
			self.calibs.calibLoad = uti.to_calib(self.calibs.calibFile, ".calib1")
		self.loadCalibLabel.config(text=self.calibs.calibLoad.split("/")[-1])
	# Only apply new fit range to calibration data
	def calibrate_newFit(self):
		gl.statusLabel[self.tel_number].config(text="New fit range ...", bg="#edda45"); root.update()
		self.calibs.pa, self.calibs.pb, self.calibs.ph_a, self.calibs.ph_b, self.calibs.xplot = fphd.fitDistribution(range_a=[float(self.fitRangelowEntryA.get()),float(self.fitRangehighEntryA.get())], range_b=[float(self.fitRangelowEntryB.get()),float(self.fitRangehighEntryB.get())], histo_x=self.calibs.histo_x, histo_a=self.calibs.histo_a, histo_b=self.calibs.histo_b, nchn=self.settings.o_nchn)
		self.finish_calibration()
		self.idle()
	# Create and start the calibration thread
	def start_calib_thread(self):
		gl.stop_calib_thread[self.tel_number] = False
		self.calib_thread = Thread(target=self.calibrate, args=())
		self.calib_thread.start()
	def stop_calib_thread(self):
		gl.stop_calib_thread[self.tel_number] = True
	# Select calib file
	def selectCalibFile(self):
		root.filename = filedialog.askopenfilename(initialdir = self.basicpath, title = "Select calibration file", filetypes = (("binary files","*.bin"),("all files","*.*")))
		self.calibs.calibFile = root.filename; self.calibFileLabel.config(text=self.calibs.calibFile.split("/")[-1])
	# Load a pre-saved calibration
	def loadCalibration(self):
		if self.settings.o_nchn == 2:
			root.filename = filedialog.askopenfilename(initialdir = self.calibpath, title = "Load calibration", filetypes = (("calib files","*.calib"),("all files","*.*")))
			self.calibs.calibLoad = root.filename; self.loadCalibLabel.config(text=self.calibs.calibLoad.split("/")[-1])
			self.calibs.histo_x = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".phd")[:,0]; self.calibs.histo_a = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".phd")[:,1]; self.calibs.histo_b = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".phd")[:,2]
			self.calibs.ps_x = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".shape")[:,0]; self.calibs.ps_a = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".shape")[:,1]; self.calibs.ps_b = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".shape")[:,2]
			self.calibs.xplot = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".xplot")
			self.calibs.pa[0] = np.loadtxt(self.calibs.calibLoad)[0]; self.calibs.pa[1] = np.loadtxt(self.calibs.calibLoad)[1]; self.calibs.pa[2] = np.loadtxt(self.calibs.calibLoad)[2]
			self.calibs.pb[0] = np.loadtxt(self.calibs.calibLoad)[3]; self.calibs.pb[1] = np.loadtxt(self.calibs.calibLoad)[4];	self.calibs.pb[2] = np.loadtxt(self.calibs.calibLoad)[5]
			self.calibs.nsum_a = np.loadtxt(self.calibs.calibLoad)[6]; self.calibs.nsum_b = np.loadtxt(self.calibs.calibLoad)[7]
			self.calibs.ph_a = np.loadtxt(self.calibs.calibLoad)[8]; self.calibs.ph_b = np.loadtxt(self.calibs.calibLoad)[9]
			self.calibs.avg_charge_a = np.loadtxt(self.calibs.calibLoad)[10]; self.calibs.avg_charge_b = np.loadtxt(self.calibs.calibLoad)[11]
			try:
				self.calibs.corr_rates_a = np.loadtxt(self.calibs.calibLoad)[12]; self.calibs.corr_rates_b = np.loadtxt(self.calibs.calibLoad)[13]
			except:
				print ("Calib file version too old to contain correction factor. Omitting ...")
			self.avgChargeLabelA.config(text="{:.2f}".format(self.calibs.avg_charge_a)); self.avgChargeLabelB.config(text="{:.2f}".format(self.calibs.avg_charge_b))
			self.rmax_b = self.maxRate(self.calibs.avg_charge_b) # Maximum rate
			self.rateBCanvas.itemconfig(self.rmaxbText, text="{:.0f}".format(self.rmax_b)) # Show in rate bar
		else:
			root.filename = filedialog.askopenfilename(initialdir = self.calibpath, title = "Load calibration", filetypes = (("one channel calib files","*.calib1"),("all files","*.*")))
			self.calibs.calibLoad = root.filename; self.loadCalibLabel.config(text=self.calibs.calibLoad.split("/")[-1])
			self.calibs.histo_x = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".phd1")[:,0]; self.calibs.histo_a = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".phd1")[:,1]
			self.calibs.ps_x = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".shape1")[:,0]; self.calibs.ps_a = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".shape1")[:,1]
			self.calibs.xplot = np.loadtxt(self.calibs.calibLoad[0:self.calibs.calibLoad.find(".")]+".xplot1")
			self.calibs.pa[0] = np.loadtxt(self.calibs.calibLoad)[0]; self.calibs.pa[1] = np.loadtxt(self.calibs.calibLoad)[1]; self.calibs.pa[2] = np.loadtxt(self.calibs.calibLoad)[2]
			self.calibs.nsum_a = np.loadtxt(self.calibs.calibLoad)[3]
			self.calibs.ph_a = np.loadtxt(self.calibs.calibLoad)[4]
			self.calibs.avg_charge_a = np.loadtxt(self.calibs.calibLoad)[5]
			try:
				self.calibs.corr_rates_a = np.loadtxt(self.calibs.calibLoad)[6]
			except:
				print ("Calib file version too old to contain correction factor. Omitting ...")
			self.avgChargeLabelA.config(text="{:.2f}".format(self.calibs.avg_charge_a))
			self.avgChargeLabelB.config(text="--")
		self.rmax_a = self.maxRate(self.calibs.avg_charge_a) # Maximum rates
		self.rateACanvas.itemconfig(self.rmaxaText, text="{:.0f}".format(self.rmax_a)) # Show in rate bar
		self.calibs.calibFile = uti.to_bin(self.calibs.calibLoad); self.calibFileLabel.config(text=self.calibs.calibFile.split("/")[-1])
		# Activate Rate Buttons
		self.calc_rate = True
	# Take calib measurement
	def takeCalibMeasurement(self):
		self.qsettings_calibrations()
		filename = self.basicpath + "/" + self.calibNameEntry.get()
		ma, mb, a_rec, b_rec, t_acq = self.card.measurement(filename, nchn=self.settings.o_nchn, samples=self.settings.o_samples)
		self.calculate_data(ma, mb)
		self.qsettings_checkWaveform()
		self.calibs.calibFile = filename; self.calibFileLabel.config(text=self.calibs.calibFile.split("/")[-1])
	# Other commands
	def displayWaveform(self):
		wv_a, wv_b = wv.execute(file=self.calibs.calibFile, length=int(int(self.offsetLEntry.get())/10), nchn=self.settings.o_nchn)
		plt.figure("Calibration file waveforms", figsize=(10,6))
		plt.plot(wv_a, label="Channel A", color=chAcolor)
		if self.settings.o_nchn == 2:
			plt.plot(wv_b, label="Channel B", color=chBcolor)
		plt.xlabel("Time bins"); plt.ylabel("ADC"); plt.legend(); plt.title(self.calibs.calibFile); plt.show()
	def secondCalibration(self):
		if self.secondCalibState == False: # Start the 2nd calibration
			# Get the 100 avg of the current rates
			self.calibs.rates_before_a = np.mean(self.rates_a)
			if self.settings.o_nchn == 2:				
				self.calibs.rates_before_b = np.mean(self.rates_b)
			# Change state and Button
			self.secondCalibState = True
			self.SecondCalibButton.config(text="Stop Calib", background="#fa857a")
		else: # The second calibration is currently running and should be stopped
			self.calibs.rates_afer_a = np.mean(self.rates_a)
			self.calibs.corr_rates_a = self.calibs.rates_before_a/self.calibs.rates_afer_a
			if self.settings.o_nchn == 2:				
				self.calibs.rates_afer_b = np.mean(self.rates_b)				
				self.calibs.corr_rates_b = self.calibs.rates_before_b/self.calibs.rates_afer_b
			# Change state and Button
			self.secondCalibState = False
			self.SecondCalibButton.config(text="2nd Calib", background="#ccf2ff")
			# Write to calibration file
			self.finish_calibration()

	#----------------------------------------------------------------------------------#
	# --- Functions that control the quick measurement stuff and rate calculations --- #
	#----------------------------------------------------------------------------------#
	# This function calculates the various parameters connected to the waveform means, most importantly the photo current and the photon rates
	# Also the rates are displayed and plotted
	def calculate_data(self, mean_a, mean_b):
		vRange   = self.settings.o_voltages
		binRange = self.settings.o_binning
		r_a = None; r_b = None
		#-- Channel A calculations --#
		# Waveform mean
		mean_a = mean_a - self.calibs.off_a
		# Rates
		if self.calc_rate == True:
			r_a = 1e-6 * mean_a/(self.calibs.avg_charge_a*binRange) * self.calibs.corr_rates_a
			# Discard the oldest rate and add the newest rate
			self.rates_a.pop(0)
			self.rates_a.append(r_a)
			self.CHa_Label_rate.config(text="{:.1f}".format(r_a))
			self.CHa_Label_avgrate.config(text="{:.0f}".format(np.mean(self.rates_a)))
			self.placeRateLineA(r_a)
		# mV
		mean_a_mV = uti.ADC_to_mV(adc=mean_a, range=vRange)
		self.CHa_Label_mean.config(text="{:.2f}".format(mean_a_mV))
		# PMT current
		curr_a_microamp = 1e3 * mean_a_mV/float(self.ampAEntry.get())/50
		if curr_a_microamp > -100:      
			self.CHa_Label_curr.config(text="{:.1f}".format(curr_a_microamp), bg="black", fg="orange")
		else:
			self.CHa_Label_curr.config(text="{:.1f}".format(curr_a_microamp), bg="#edd266", fg="red")
	
		#-- Channel B calculations --#
		if self.settings.o_nchn == 2:
			# Waveform mean	
			mean_b = mean_b - self.calibs.off_b
			# Rates
			if self.calc_rate == True:
				r_b = 1e-6 * mean_b/(self.calibs.avg_charge_b*binRange) * self.calibs.corr_rates_b
				# Discard the oldest rate and add the newest rate
				self.rates_b.pop(0)
				self.rates_b.append(r_b)
				self.CHb_Label_rate.config(text="{:.1f}".format(r_b))
				self.CHb_Label_avgrate.config(text="{:.0f}".format(np.mean(self.rates_b)))
				self.placeRateLineB(r_b)
			# mV	
			mean_b_mV = uti.ADC_to_mV(adc=mean_b, range=vRange)	
			self.CHb_Label_mean.config(text="{:.2f}".format(mean_b_mV))
			# PMT current	
			curr_b_microamp = 1e3 * mean_b_mV/float(self.ampBEntry.get())/50
			if curr_b_microamp > -100:
				self.CHb_Label_curr.config(text="{:.1f}".format(curr_b_microamp), bg="black", fg="orange")
			else:
				self.CHb_Label_curr.config(text="{:.1f}".format(curr_b_microamp), bg="#edd266", fg="red")


		if self.calc_rate == True:
			self.update_rate_plot()
			# Communicate with the motor box if connected
			if self.server != None:
				self.server.sendRate(r_a, r_b)
		root.update()

	# This function is for quickly taking single waveform data (no storing to disk)
	def analysis(self):
		# Take a quick waveform
		mean_a_ADC, mean_b_ADC, a_rec, b_rec = self.card.take_data(nchn=self.settings.o_nchn)		
		# Plot and analyze the data
		self.update_waveform(a_rec, b_rec)
		self.calculate_data(mean_a_ADC, mean_b_ADC)
	# Run the quick measurement mode
	def quick_analysis(self):
		while self.stop_thread == False:
			self.analysis()
	# starting or stopping the quick analysis
	def startstop_quick(self):
		global running_quick, stop_thread
		if self.running_quick == False:
			self.running_quick = True	
			self.quickRatesButton.config(text="Stop quick", bg="#fa857a")
			self.stop_thread = False
			gl.statusLabel[self.tel_number].config(text="Quick Rate Mode" , bg="#edda45"); root.update()
			self.the_thread = Thread(target=self.quick_analysis, args=())
			self.the_thread.start()
		else:
			self.running_quick = False
			self.stop_thread = True
			self.quickRatesButton.config(text="Start quick", bg="#e8fcae")
			self.idle()

	#------------------------------------------------#
	# --- Functions for the server communication --- #
	#------------------------------------------------#
	#starts/stops the server which sends the rate to the RASPI
	def startStopServerMotor(self):
		#check if server is running
		if self.server == None :	
			#start server
			self.server=svr.server(port=self.server_port, tel_number=self.tel_number)
			try:
				self.server.start()
				#change button label
				gl.motorServerButton[self.tel_number].config(text="Stop Server (Motor)", bg="#ffc47d")
			except OSError as err:
				print("The OS did not allow start the server on {0}:{1} . Are address and port correct? Maybe an old instance is still blocking this resource?".format(server.address, server.port))
				print(err)
				self.server = None
		else:
			#shutdown server
			self.server.stop()
			#change button label
			gl.motorServerButton[self.tel_number].config(text="Start Server (Motor)", bg="#cdcfd1")		
			self.server = None
	







	# --- Functions for displaying the status --- #
	def idle(self):
		gl.statusLabel[self.tel_number].config(text="Idle", bg="#ffffff"); root.update()	



# Measurement procedure
tdiffs = []; timestamps_between = []; t_stamps = []
# Parameters which track the acquisition times


def singles():
	theThread = Thread(target=singlesT, args=[])
	theThread.start()
def singlesT():
	global measurement, tdiffs, timestamps_between, t_stamps, plotCanvas, plot_times
	# change all the status labels
	for t in telescopes:
		gl.statusLabel[t.tel_number].config(text="Remote Measurement", bg="#ff867d")
	disable_buttons()
	time.sleep(0.1)
	
	while measurement == True:
		print ("All finished, new measurement :)")
		# Status LEDs to orange and await variable of this telescope to True
		for t in telescopes:
			t.waitCanvas.itemconfig(t.waitLED, fill="orange")
			t.awaitR = True
		
		# Send measurement command
		for t in telescopes:
			t.pcThread = Thread(target=t.remote_measurement,  args=(measNameEntry.get(), int(indexEntry.get())))
			t.pcThread.start()
		for t in telescopes:
			t.pcThread.join()

		## Time investigations
		for t in telescopes:
			t.acq_plot.set_xdata( np.arange(0,len(t.acquisition_times[-100:]),1) )
			t.acq_plot.set_ydata( t.acquisition_times[-100:] )

		plot_times.relim()
		plot_times.autoscale_view(True,True,True)
		#plot_times.set_xlim(0, len(telescopes[0].acquisition_times))
		plotCanvas.draw()
		#timestamps_between.append(time.time())
		#time.sleep(0.1)
		#
		#if len(timestamps_between) > 1:
		#	t_stamps.append(timestamps_between[-1]-timestamps_between[-2])
		#else:
		#	t_stamps.append(4)
		##tdiff = gl.client_PC2.timeR - gl.client_PC1.timeR
		##tdiffs.append(tdiff)
		## Plot
		#plot_times.cla(); plot_times.set_xticks([])
		##plot_times.plot(tdiffs, color="blue")
		#plot_times2.cla(); plot_times2.set_xticks([])
		#plot_times2.plot(t_stamps, color="red")
		#if len(tdiffs) > 100:
		#	#plot_times.set_xlim(len(tdiffs)-99,len(tdiffs))
		#	plot_times2.set_xlim(len(tdiffs)-99,len(tdiffs))
		#plotCanvas.draw()
		#
		index_up()
	
	for t in telescopes:
		t.idle()
		np.savetxt("tel_{}.txt".format(t.tel_number), t.acquisition_times)
	enable_buttons()

		

'''



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

'''


# Add telescopes to the GUI
telescopes = []
for i in range (0,len(tel_nos)):
	telescopes.append( telescope(tel_number=tel_nos[i], tel_name=tel_names[i], spcm_port=spcm_ports[i], datapath=datapaths[i], port=ports[i], mode=modes[i] ))

root.mainloop()