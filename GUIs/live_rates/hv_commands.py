import telnetlib
import time
import globals as gl
from threading import Thread
import configparser

host = ""
port = 23
timeout = 100
tn = None

waittime = 0.03 # between commands in seconds
def wait():
	time.sleep(waittime)

def init():
	global host, tn
	this_config = configparser.ConfigParser()
	this_config.read("../../../this_pc.conf")
	if "who_am_i" in this_config:
		cam_pc_no = int(this_config["who_am_i"]["no"])
		if  this_config["who_am_i"]["type"] != "cam_pc" and this_config["who_am_i"]["type"] != "time_harp_pc":
			print("According to the 'this_pc.config'-file this pc is not meant as a camera pc. Please correct the configuarion or start the right GUI!")
			exit()
	else:
		print("There is no config file on this computer which specifies the computer function! Please add a 'this_pc.config' file next to the curcor-directory!")
		exit()
	global_config = configparser.ConfigParser()
	global_config.read('../global.conf')
	if cam_pc_no == 1:
		hv_address = global_config["cam_pc_1"]["hv_address"]
	elif cam_pc_no == 2:
		hv_address = global_config["cam_pc_2"]["hv_address"]
	elif cam_pc_no == 3:
		hv_address = global_config["time_harp_pc"]["hv_address"]
	else:
		print("Error in the 'this_pc.config'-file. The number of the Cam PC is neither 1 nor 2. Please correct!")
	
	host = hv_address

	tn = telnetlib.Telnet(host)
	tn.write("vt100\n".encode()) # For some reasons this must be written ;)

#####################
## Basic functions ##
#####################
def get_status(channel):
	theString = "$CMD:MON,CH:"+str(channel)+",PAR:STAT\n"
	tn.write(theString.encode()); wait(); a=str(tn.read_very_eager())
	b = int(a.split("VAL:")[-1].split(";")[0])
	return b
status_colors = ["light grey","white",2,"#ffdf99",4,"#99ceff",6,7,8]

def set_vset(channel, voltage):
	theString = "$CMD:SET,CH:{},PAR:VSET,VAL:{:.1f}\n".format(channel, voltage)
	tn.write(theString.encode()); wait()
def set_vset_running(channel, voltage):
	theString = "$CMD:SET,CH:{},PAR:VSET,VAL:{:.1f}\n".format(channel, voltage)
	tn.write(theString.encode()); stat_old = gl.scheck; time.sleep(0.5)
	while gl.scheck == stat_old:
		wait()
	while(gl.status[channel] !=1):
		wait()

def get_vset(channel):
	theString = "$CMD:MON,CH:"+str(channel)+",PAR:VSET\n"
	tn.write(theString.encode()); wait(); a=str(tn.read_very_eager())
	b = float(a.split("VAL:")[-1].split(";")[0])
	return b
def get_vmon(channel):
	theString = "$CMD:MON,CH:"+str(channel)+"PAR:VMON\n"
	wait(); tn.write(theString.encode()); wait(); a=str(tn.read_very_eager())
	b = float(a.split("VAL:")[1].split(";")[0])
	return b
def get_imon(channel):
	theString = "$CMD:MON,CH:"+str(channel)+"PAR:IMON\n"
	wait(); tn.write(theString.encode()); wait(); a=str(tn.read_very_eager())
	b = 1e-3 * float(a.split("VAL:")[1].split(";")[0])
	return b

def switch_on(channel):	
	theString = "$CMD:SET,CH:"+str(channel)+",PAR:ON\n"
	tn.write(theString.encode()); stat_old = gl.scheck; time.sleep(0.5)
	while gl.scheck == stat_old:
		wait()
	while(gl.status[channel] != 1):
		wait()
def switch_off(channel):
	theString = "$CMD:SET,CH:"+str(channel)+",PAR:OFF\n"
	tn.write(theString.encode()); stat_old = gl.scheck; time.sleep(0.5)
	while gl.scheck == stat_old:
		wait()
	while(gl.status[channel] != 0):
		wait()

########################
## Advanced functions ##
########################
def apply_ratio_0():
	#wait_frame()
	if gl.vset[0]/gl.vset[1] > gl.ratio01:
		set_vset(0, gl.vset[1]*gl.ratio01)
	elif gl.vset[0]/gl.vset[1] < gl.ratio01:
		set_vset(1, gl.vset[0]/gl.ratio01)
	wait()
def apply_ratio_2():
	#wait_frame()
	if gl.vset[2]/gl.vset[3] > gl.ratio23:
		set_vset(2, gl.vset[3]*gl.ratio01)
	elif gl.vset[2]/gl.vset[3] < gl.ratio01:
		set_vset(3, gl.vset[2]/gl.ratio01)
	wait()

def set_vset_0(voltage):
	voltage_old = gl.vset[0]
	if gl.status0 == True: # PMT should be on
		if voltage > voltage_old: # Start with ramping up channel 1
			set_vset_running(1, voltage/gl.ratio01)
			set_vset_running(0, voltage)
		elif voltage < voltage_old: # Start with ramping down channel 0
			set_vset_running(0, voltage)
			set_vset_running(1, voltage/gl.ratio01)
	elif gl.status0 == False: # PMT off -> Doesn't matter
		set_vset(0, voltage); wait(); set_vset(1, voltage/gl.ratio01)
def safe_vset_0(voltage):
	set_vset_0_thread = Thread(target=set_vset_0, args=[voltage])
	set_vset_0_thread.start()
def set_vset_2(voltage):
	voltage_old = gl.vset[2]
	if gl.status2 == True: # PMT should be on
		if voltage > voltage_old: # Start with ramping up channel 3
			set_vset_running(3, voltage/gl.ratio23)
			set_vset_running(2, voltage)
		elif voltage < voltage_old: # Start with ramping down channel 2
			set_vset_running(2, voltage)
			set_vset_running(3, voltage/gl.ratio23)
	elif gl.status0 == False: # PMT off -> Doesn't matter
		set_vset(2, voltage); wait(); set_vset(3, voltage/gl.ratio23)
def safe_vset_2(voltage):
	set_vset_2_thread = Thread(target=set_vset_2, args=[voltage])
	set_vset_2_thread.start()


def toggle_0():
	try:
		if gl.status0 == False:
			gl.hv0Button.config(bg="orange")
			gl.hv1Label.config(bg="orange")
			safe_on_0()
			gl.status0 = True
		elif gl.status0 == True:
			gl.hv0Button.config(bg="grey")
			gl.hv1Label.config(bg="grey")
			safe_off_0()
			gl.status0 = False
	except:
		pass

def toggle_2():
	try:
		if gl.status2 == False:
			gl.hv2Button.config(bg="orange")
			gl.hv3Label.config(bg="orange")
			safe_on_2()
			gl.status2 = True
		elif gl.status2 == True:
			gl.hv2Button.config(bg="grey")
			gl.hv3Label.config(bg="grey")
			safe_off_2()
			gl.status2 = False
	except:
		pass



def switch_off_0():
	gl.hv0Button.config(state="disabled")
	switch_off(0)
	switch_off(1)
	gl.hv0Button.config(state="normal")
def safe_off_0():
	switch_off_0_thread = Thread(target=switch_off_0, args=())
	switch_off_0_thread.start()

def switch_off_2():
	gl.hv2Button.config(state="disabled")
	switch_off(2)
	switch_off(3)
	gl.hv2Button.config(state="normal")
def safe_off_2():
	switch_off_2_thread = Thread(target=switch_off_2, args=())
	switch_off_2_thread.start()

def switch_on_0():
	#gl.hv0Button.config(state="disabled")
	switch_on(1)
	switch_on(0)
	gl.hv0Button.config(state="normal")
def safe_on_0():
	switch_on_0_thread = Thread(target=switch_on_0, args=())
	switch_on_0_thread.start()

def switch_on_2():
	#gl.hv2Button.config(state="disabled")
	switch_on(3)
	switch_on(2)
	gl.hv2Button.config(state="normal")
def safe_on_2():
	switch_on_2_thread = Thread(target=switch_on_2, args=())
	switch_on_2_thread.start()


def monitor_things():
	try:
		gl.vMon0Label.config(text="{:.1f}".format(get_vmon(0)))
		gl.vMon1Label.config(text="{:.1f}".format(get_vmon(1)))
		gl.vMon2Label.config(text="{:.1f}".format(get_vmon(2)))
		gl.vMon3Label.config(text="{:.1f}".format(get_vmon(3)))

		gl.vset = [get_vset(0),get_vset(1),get_vset(2),get_vset(3)]
		gl.status = [get_status(0), get_status(1), get_status(2), get_status(3)]
		gl.scheck += 1
		gl.frameLabel.config(text="{}/{}".format(gl.scheck,gl.failed_check))

		gl.vSet0Label.config(text=str(gl.vset[0]))
		gl.vSet1Label.config(text=str(gl.vset[1]))
		gl.vSet2Label.config(text=str(gl.vset[2]))
		gl.vSet3Label.config(text=str(gl.vset[3]))

		gl.vMon0Label.config(bg = status_colors[gl.status[0]])
		gl.vMon1Label.config(bg = status_colors[gl.status[1]])
		gl.vMon2Label.config(bg = status_colors[gl.status[2]])
		gl.vMon3Label.config(bg = status_colors[gl.status[3]])

		gl.iMon0Label.config(text="{:.2f}".format(get_imon(0)))
		gl.iMon1Label.config(text="{:.2f}".format(get_imon(1)))
		gl.iMon2Label.config(text="{:.2f}".format(get_imon(2)))
		gl.iMon3Label.config(text="{:.2f}".format(get_imon(3)))
	except:
		gl.failed_check += 1
def monitor():
	while gl.mon_thread == True:
		monitor_things()
	print ("End Monitor")
	gl.thread_killed = True
def start_monitor():
	print ("Start HV Monitor ...")
	if gl.mon_thread == False:
		gl.mon_thread = True; gl.thread_killed = False
		monitor_thread = Thread(target=monitor, args=())
		monitor_thread.start()
	print ("Done")
def wait_frame():
	old = gl.scheck
	while gl.scheck == old:
		wait()