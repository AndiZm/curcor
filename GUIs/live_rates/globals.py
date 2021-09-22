import time

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
wf_a_line = None
wf_b_line = None
import numpy as np
def update_waveform(a,b):
	wf_a_line.set_xdata(np.arange(0,len(a)))
	wf_a_line.set_ydata(a)
	wf_b_line.set_xdata(np.arange(0,len(b)))
	wf_b_line.set_ydata(b)
	wf_canvas.draw()

copythread = None
projectName = None