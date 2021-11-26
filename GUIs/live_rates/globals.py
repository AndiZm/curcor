import time
import sys

stop_calib_thread = False
stop_offset_thread = False
lastfiletime = 1e9*time.time()
stop_wait_for_file_thread = False

# General options
o_samples 		= 8388608	# Number of samples per file
o_binning  		= 1.6e-9	# Time binning in seconds
o_voltages 		= 200		# Voltage range in mV
o_nchn     		= 2 		# Activated channels
clockmode = None
trigger = False

# Paths
basicpath = "E:/"
calibpath = basicpath+"/calibs"

### OFFSET DATA ###
offsetFile = ""; offsetLoad = ""			# Files for offset
off_a = 0.0; off_b = 0.0					# Baseline offsets in ADC

### CALIBRATION DATA ###
# Calibration files
calibFile = ""; calibLoad = ""
# Pulse height distribution histogram
histo_x = []; histo_a = []; histo_b = []	# x, y_a, y_b
pa = [0,0,0]; pb = [0,0,0]				 	# Fit parameter
ph_a = []; ph_b = []						# avg pulse heights
xplot=[]									# Fit plot x values
# Pulse shape data
ps_x = []; ps_a = []; ps_b = []				# x values (in time steps), y_a, y_b
nsum_a = []; nsum_b = []					# normalizes peak sums
# Combined
avg_charge_a = []; avg_charge_b = []		# Average charge, will be nsum * ph
# Maximum rates
rmax_a = None; rmax_b = None

### GUI ELEMENTS ###
statusLabel = []
quickRatesButton = []; singleRatesButton = []; calc_rate = False
startstopButton = []
syncedMeasButton = []
remoteMeasButton = []; remoteMeasName = None; remoteMeasIndex = None; remoteFiles = []

# Server
motorServerButton = []
controllerServerButton = []

# Running actions for communication with controller
act_start_quick =  False
act_start_file = False

# Wafevorm plot data
wf_canvas = None
wf_a_line = None; wf_b_line = None
import numpy as np
def update_waveform(a,b):
	wf_a_line.set_xdata(np.arange(0,len(a))); wf_a_line.set_ydata(a)
	wf_b_line.set_xdata(np.arange(0,len(b))); wf_b_line.set_ydata(b)
	wf_canvas.draw()
rates_a_line = None; rates_b_line = None
rates_a = []; rates_b = []
for i in range(0,100):
	rates_a.append(0); rates_b.append(0)
def update_rate_plot():
	rates_a_line.set_xdata(np.arange(-len(rates_a),0)); rates_a_line.set_ydata(rates_a)
	rates_b_line.set_xdata(np.arange(-len(rates_b),0)); rates_b_line.set_ydata(rates_b)
	wf_canvas.draw()

copythread = None
projectName = None

##################
### HV globals ###
##################
ratio01 = 3.34
ratio23 = 3.34

mon_thread = False
thread_killed = True
root = []

vset = [0,0,0,0]; vmon = [0,0,0,0]; stat = []
vmon0 = []; vmon1 = []; vmon2 = []; vmon3 = []
status = [0,0,0,0]
scheck = 0; failed_check= 0

status0 = False; status2 = False
# Labels
vMon0Label = []; vMon1Label = []; vMon2Label = []; vMon3Label = []
iMon0Label = []; iMon1Label = []; iMon2Label = []; iMon3Label = []
vSet0Label = []; vSet1Label = []; vSet2Label = []; vSet3Label = []
hv1Label = []; hv3Label = []
frameLabel = []
# Buttons
hv0Button = []; hv2Button = []