import time
import sys

#-1-#
stop_calib_thread = False
stop_offset_thread = False
lastfiletime = 1e9*time.time()
stop_wait_for_file_thread = False
#-2-#
stop_calib_thread2 = False
stop_offset_thread2 = False
lastfiletime2 = 1e9*time.time()
stop_wait_for_file_thread2 = False

# General options
#-1-#
o_samples 		= 8388608	# Number of samples per file
o_binning  		= 1.6e-9	# Time binning in seconds
o_voltages 		= 200		# Voltage range in mV
o_nchn     		= 2 		# Activated channels
clockmode		= None
trigger			= False
#-2-#
o_samples2 		= 8388608	# Number of samples per file
o_binning2 		= 1.6e-9	# Time binning in seconds
o_voltages2		= 200		# Voltage range in mV
o_nchn2    		= 2 		# Activated channels
clockmode2		= None
trigger2		= False

# Paths
#-1-#
basicpath = "E:/"
calibpath = basicpath+"/calibs"
#-2-#
basicpath2 = "E:/"
calibpath2 = basicpath2+"/calibs"

### OFFSET DATA ###
#-1-#
offsetFile = ""; offsetLoad = ""			# Files for offset
off_a = 0.0; off_b = 0.0					# Baseline offsets in ADC
#-2-#
offsetFile2 = ""; offsetLoad2 = ""			# Files for offset
off_a2 = 0.0; off_b2 = 0.0					# Baseline offsets in ADC

### CALIBRATION DATA ###
#-1-#
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
#-2-#
# Calibration files
calibFile2 = ""; calibLoad2 = ""
# Pulse height distribution histogram
histo_x2 = []; histo_a2 = []; histo_b2 = []	# x, y_a, y_b
pa2 = [0,0,0]; pb2 = [0,0,0]				 	# Fit parameter
ph_a2 = []; ph_b2 = []						# avg pulse heights
xplot2=[]									# Fit plot x values
# Pulse shape data
ps_x2 = []; ps_a2 = []; ps_b2 = []				# x values (in time steps), y_a, y_b
nsum_a2 = []; nsum_b2 = []					# normalizes peak sums
# Combined
avg_charge_a2 = []; avg_charge_b2 = []		# Average charge, will be nsum * ph
# Maximum rates
rmax_a2 = None; rmax_b2 = None

### GUI ELEMENTS ###
#-1-#
statusLabel = []
quickRatesButton = []; singleRatesButton = []; calc_rate = False
startstopButton = []
syncedMeasButton = []
remoteMeasButton = []; remoteMeasName = None; remoteMeasIndex = None; remoteFiles = []
#-2-#
statusLabel2 = []
quickRatesButton2 = []; singleRatesButton2 = []; calc_rate2 = False
startstopButton2 = []
syncedMeasButton2 = []
remoteMeasButton2 = []; remoteMeasName2 = None; remoteMeasIndex2 = None; remoteFiles2 = []

# Server
motorServerButton = []
motorServerButton2 = []
controllerServerButton = []
controllerServerButton2 = []

# Running actions for communication with controller
act_start_quick =  False
act_start_quick2 =  False
act_start_file = False
act_start_file2 = False

# Wafevorm plot data
#-1-#
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
#-2-#
wf_canvas2 = None
wf_a_line2 = None; wf_b_line2 = None
def update_waveform2(a,b):
	wf_a_line2.set_xdata(np.arange(0,len(a))); wf_a_line2.set_ydata(a)
	wf_b_line2.set_xdata(np.arange(0,len(b))); wf_b_line2.set_ydata(b)
	wf_canvas2.draw()
rates_a_line2 = None; rates_b_line2 = None
rates_a2 = []; rates_b2 = []
for i in range(0,100):
	rates_a2.append(0); rates_b2.append(0)
def update_rate_plot2():
	rates_a_line2.set_xdata(np.arange(-len(rates_a2),0)); rates_a_line2.set_ydata(rates_a2)
	rates_b_line2.set_xdata(np.arange(-len(rates_b2),0)); rates_b_line2.set_ydata(rates_b2)
	wf_canvas2.draw()

copythread = None
copythread2 = None
projectName = None

##################
### HV globals ###
##################
#-1-#
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

#-2-#
ratio012 = 3.34
ratio232 = 3.34

mon_thread2 = False
thread_killed2 = True
root2 = []

vset2 = [0,0,0,0]; vmon2 = [0,0,0,0]; stat2 = []
vmon02 = []; vmon12 = []; vmon22 = []; vmon32 = []
status2 = [0,0,0,0]
scheck2 = 0; failed_check2= 0

status02 = False; status22 = False
# Labels
vMon0Label2 = []; vMon1Label2 = []; vMon2Label2 = []; vMon3Label2 = []
iMon0Label2 = []; iMon1Label2 = []; iMon2Label2 = []; iMon3Label2 = []
vSet0Label2 = []; vSet1Label2 = []; vSet2Label2 = []; vSet3Label2 = []
hv1Label2 = []; hv3Label2 = []
frameLabel2 = []
# Buttons
hv0Button2 = []; hv2Button2 = []