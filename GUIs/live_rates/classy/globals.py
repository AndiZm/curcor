import time
import sys


stop_calib_thread  = []
stop_offset_thread = []

# General options
class settings():
	def __init__(self):
		self.o_samples 		= 8388608	# Number of samples per file
		self.o_binning  	= 1.6e-9	# Time binning in seconds
		self.o_voltages 	= 200		# Voltage range in mV
		self.o_nchn     	= 2 		# Activated channels
		self.clockmode		= None		# internal or external clock
		self.trigger		= False		# External trigger activated?

# Calibration parameters
class calibs():
	def __init__(self):
		####################
		# Calibration data #
		####################
		self.offsetFile = None
		self.offsetLoad = None
		self.off_a = 0.0
		self.off_b = 0.0

		####################
		# Calibration data #
		####################
		self.calibFile = ""
		self.calibLoad = ""
		# Pulse height distribution histogram
		self.histo_x = []	# x
		self.histo_a = []	# y_a
		self.histo_b = []	# y_b
		# Fit parameter
		self.pa = [0,0,0]
		self.pb = [0,0,0]
		# avg pulse heights
		self.ph_a = []
		self.ph_b = []
		self.xplot= []	# Fit plot x values
		# Pulse shape data
		self.ps_x = []	# x values (in time steps)
		self.ps_a = []	# y_a
		self.ps_b = []	# y_b
		# normalized peak sums
		self.nsum_a = []
		self.nsum_b = []
		# Combined, average charge, will be nsum * ph
		self.avg_charge_a = []
		self.avg_charge_b = []			
		# Maximum rates
		self.rmax_a = None
		self.rmax_b = None


### GUI ELEMENTS ###
#-1-#
statusLabel = []
quickRatesButton = []; singleRatesButton = []; calc_rate = False
startstopButton = []
syncedMeasButton = []
remoteMeasButton = []; remoteMeasName = None; remoteMeasIndex = None; remoteFiles = []

motorServerButton = []


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