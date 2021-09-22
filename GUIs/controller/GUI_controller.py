import numpy as np
import matplotlib; matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends.backend_tkagg as tkagg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import os
import time as t
from os import listdir
from os.path import isfile, join
from tkinter import *
from tkinter import filedialog

import threading

import rate_client as rc
import globals as gl


root = Tk(); root.wm_title("II Measurement Control")#; root.geometry("+1600+10")

zeroadder = ["0000","0000","000","00","0",""]
def numberstring(x):
    if x == 0:
        nod = 1
    else:
        nod = int(np.log10(x))+1
    return zeroadder[nod] + str(x)

#############
## Network ##
#############
networkFrame = Frame(root); networkFrame.grid(row=0,column=0)
pc1Frame = Frame(networkFrame); pc1Frame.grid(row=0,column=0,padx=2)
pc2Frame = Frame(networkFrame); pc2Frame.grid(row=0,column=1,padx=2)

#------------------------#
#-- Connection Buttons --#
#------------------------#
# Connection to Camera PC 1
def startstopClientPC1():
	#check if client is running
	if gl.client_PC1 == None :	
		#start client
		gl.client_PC1=rc.controller_client("client_to_pc1")
		try:
			gl.client_PC1.connect()
		except OSError as err:
			#print("The OS did not allow start the server on {0}:{1} . Are address and port correct? Maybe an old instance is still blocking this resource?".format(server.address, server.port))
			print(err)
			gl.client_PC1 = None
	else:
		#shutdown server
		gl.client_PC1.stop_self()
		#change button label
		gl.pc1Button.config(text="Start Client PC 1", bg="#cdcfd1")
		gl.client_PC1 = None
gl.pc1Button = Button(pc1Frame, text="Start Client PC 1", bg="#cdcfd1", command=startstopClientPC1); gl.pc1Button.grid(row=0,column=0)

# Connection to Camera PC 2
def startstopClientPC2():
	#check if client is running
	if gl.client_PC2 == None :	
		#start client
		gl.client_PC2=rc.controller_client("client_to_pc2")
		try:
			gl.client_PC2.connect()
		except OSError as err:
			#print("The OS did not allow start the server on {0}:{1} . Are address and port correct? Maybe an old instance is still blocking this resource?".format(server.address, server.port))
			print(err)
			gl.client_PC2 = None
	else:
		#shutdown server
		gl.client_PC2.stop_self()
		#change button label
		gl.pc2Button.config(text="Start Client PC 2", bg="#cdcfd1")
		gl.client_PC2 = None
gl.pc2Button = Button(pc2Frame, text="Start Client PC 2", bg="#cdcfd1", command=startstopClientPC2); gl.pc2Button.grid(row=0,column=0)

#-------------------#
#-- Rate displays --#
#-------------------#
rate1Frame = Frame(pc1Frame); rate1Frame.grid(row=1, column=0)
gl.rateA1Label = Label(rate1Frame, text="-.-", fg="orange", bg="black", width=5); gl.rateA1Label.grid(row=0,column=0, padx=3)
gl.rateB1Label = Label(rate1Frame, text="-.-", fg="orange", bg="black", width=5); gl.rateB1Label.grid(row=0,column=1, padx=3)

rate2Frame = Frame(pc2Frame); rate2Frame.grid(row=1, column=0)
gl.rateA2Label = Label(rate2Frame, text="-.-", fg="orange", bg="black", width=5); gl.rateA2Label.grid(row=0,column=0, padx=3)
gl.rateB2Label = Label(rate2Frame, text="-.-", fg="orange", bg="black", width=5); gl.rateB2Label.grid(row=0,column=1, padx=3)
#---------------#
#-- Rate bars --#
#---------------#
gl.rateA1Canvas = Canvas(rate1Frame, width=gl.r_width, height=gl.r_height, bg="gray"); gl.rateA1Canvas.grid(row=1,column=0)
gl.rateB1Canvas = Canvas(rate1Frame, width=gl.r_width, height=gl.r_height, bg="gray"); gl.rateB1Canvas.grid(row=1,column=1)
# Forbidden rate area is 20% of rate bar
rateA1forb = gl.rateA1Canvas.create_rectangle(0,0,gl.r_width,0.2*gl.r_height, fill="orange", stipple="gray50")
rateB1forb = gl.rateB1Canvas.create_rectangle(0,0,gl.r_width,0.2*gl.r_height, fill="orange", stipple="gray50")
# Rate displaying lines
gl.rateA1Line = gl.rateA1Canvas.create_line(0,gl.r_height,gl.r_width,gl.r_height, fill="red", width=5)
gl.rateB1Line = gl.rateB1Canvas.create_line(0,gl.r_height,gl.r_width,gl.r_height, fill="red", width=5)
# Max rate text
gl.rmaxA1Text = gl.rateA1Canvas.create_text(gl.r_width/2,0.2*gl.r_height, fill="white", text="--")
gl.rmaxB1Text = gl.rateB1Canvas.create_text(gl.r_width/2,0.2*gl.r_height, fill="white", text="--")

gl.rateA2Canvas = Canvas(rate2Frame, width=gl.r_width, height=gl.r_height, bg="gray"); gl.rateA2Canvas.grid(row=1,column=0)
gl.rateB2Canvas = Canvas(rate2Frame, width=gl.r_width, height=gl.r_height, bg="gray"); gl.rateB2Canvas.grid(row=1,column=1)
# Forbidden rate area is 20% of rate bar
rateA2forb = gl.rateA2Canvas.create_rectangle(0,0,gl.r_width,0.2*gl.r_height, fill="orange", stipple="gray50")
rateB2forb = gl.rateB2Canvas.create_rectangle(0,0,gl.r_width,0.2*gl.r_height, fill="orange", stipple="gray50")
# Rate displaying lines
gl.rateA2Line = gl.rateA2Canvas.create_line(0,gl.r_height,gl.r_width,gl.r_height, fill="red", width=5)
gl.rateB2Line = gl.rateB2Canvas.create_line(0,gl.r_height,gl.r_width,gl.r_height, fill="red", width=5)
# Max rate text
gl.rmaxA2Text = gl.rateA2Canvas.create_text(gl.r_width/2,0.2*gl.r_height, fill="white", text="--")
gl.rmaxB2Text = gl.rateB2Canvas.create_text(gl.r_width/2,0.2*gl.r_height, fill="white", text="--")

#---------------------#
#-- Control Buttons --#
#---------------------#
Button1Frame = Frame(pc1Frame); Button1Frame.grid(row=2, column=0)
gl.fileRates1Button = Button(Button1Frame, text="Start File", bg="#e8fcae", width=12, state="disabled"); gl.fileRates1Button.grid(row=0,column=0)
gl.quickRates1Button = Button(Button1Frame, text="Start quick", bg="#e8fcae", width=12, state="disabled"); gl.quickRates1Button.grid(row=1,column=0)


Button2Frame = Frame(pc2Frame); Button2Frame.grid(row=2, column=0)
gl.fileRates2Button = Button(Button2Frame, text="Start File", bg="#e8fcae", width=12, state="disabled"); gl.fileRates2Button.grid(row=0,column=1)
gl.quickRates2Button = Button(Button2Frame, text="Start quick", bg="#e8fcae", width=12, state="disabled"); gl.quickRates2Button.grid(row=1,column=1)

#####################
## Synchronization ##
#####################
gl.wait1Canvas = Canvas(Button1Frame, width=20,height=20); gl.wait1Canvas.grid(row=0,column=1)
gl.wait1LED = gl.wait1Canvas.create_rectangle(1,1,20,20, fill="black", width=0)
gl.wait2Canvas = Canvas(Button2Frame, width=20,height=20); gl.wait2Canvas.grid(row=0,column=0)
gl.wait2LED = gl.wait2Canvas.create_rectangle(1,1,20,20, fill="black", width=0)


syncFrame = Frame(root); syncFrame.grid(row=0,column=1)

measurement = False
def toggle_measure():
	global measurement, tdiffs, timestamps_between, t_stamps
	if measurement == False: # Start measurement
		measurement = True
		# Activate file rates if not already on
		#if gl.client_PC1 != None and gl.fr1state == False:
		#	gl.client_PC1.filerates()
		#if gl.client_PC2 != None and gl.fr1state == False:
		#	gl.client_PC2.filerates()
		singles()
		startStopMeasButton.config(text="Stop Measurement", bg="#f2b4a0")
	elif measurement == True: # Stop measurement
		measurement = False
		# Deactivate file rates if not already off
		#if gl.client_PC1 != None and gl.fr1state == True:
		#	gl.client_PC1.awaitR = False
		#	gl.client_PC1.filerates()
		#if gl.client_PC2 != None and gl.fr1state == True:
		#	gl.client_PC2.awaitR = False
		#	gl.client_PC2.filerates()
		startStopMeasButton.config(text="Start Measurement", bg="#92f0eb")
		gl.wait1Canvas.itemconfig(gl.wait1LED, fill="black")
		gl.wait2Canvas.itemconfig(gl.wait2LED, fill="black")
		tdiffs = []; timestamps_between = []; t_stamps = []
		gl.lastA1 = []; gl.lastB1 = []; gl.lastA2 = []; gl.lastB2 = []
def init_measurement():
	if gl.client_PC1 != None and gl.client_PC2 != None:
		gl.client_PC1.init_meas(name=measNameEntry.get())
		gl.client_PC2.init_meas(name=measNameEntry.get())
	else:
		print ("Not both PCs connected")

measButtonFrame = Frame(syncFrame); measButtonFrame.grid(row=0,column=0)
startStopMeasButton = Button(measButtonFrame, text="Start Measurement", bg="#92f0eb", width=20, height=5, command=toggle_measure)
startStopMeasButton.grid(row=0,column=0)
initMeasButton = Button(measButtonFrame, text="Init new \nmeasurement", height=5, command=init_measurement)
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
gl.indexEntry = Entry(indexFrame, width=7); gl.indexEntry.grid(row=0,column=1); gl.indexEntry.insert(0,"0")
def reset_index():
	gl.indexEntry.delete(0,"end")
	gl.indexEntry.insert(0,"0")
indexButton = Button(indexFrame, text="Reset", command=reset_index); indexButton.grid(row=0,column=0)


# Measurement procedure
tdiffs = []; timestamps_between = []; t_stamps = []
def singles():
	theThread = threading.Thread(target=singlesT, args=[])
	theThread.start()
def singlesT():
	global measurement, tdiffs, timestamps_between, t_stamps
	if gl.client_PC1 != None and gl.client_PC2 != None:
		gl.client_PC1.send_start_loop()
		gl.client_PC2.send_start_loop()
		disable_buttons()
		t.sleep(0.1)
		while measurement == True:
			# Status LEDs to orange
			gl.wait1Canvas.itemconfig(gl.wait1LED, fill="orange")
			gl.wait2Canvas.itemconfig(gl.wait2LED, fill="orange")
			# Send measurement command
			gl.client_PC1.meas_single(name=measNameEntry.get(), index=gl.indexEntry.get())
			gl.client_PC2.meas_single(name=measNameEntry.get(), index=gl.indexEntry.get())
			# Wait until both PCs respond
			while gl.client_PC1.awaitR == True or gl.client_PC2.awaitR == True:
				if measurement == False:
					break
			if measurement == False:
				break
			# Time investigations
			timestamps_between.append(t.time())
			t.sleep(0.1)
			if len(timestamps_between) > 1:
				t_stamps.append(timestamps_between[-1]-timestamps_between[-2])
			else:
				t_stamps.append(4)
			#tdiff = gl.client_PC2.timeR - gl.client_PC1.timeR
			#tdiffs.append(tdiff)
			## Plot
			#plot_times.cla(); plot_times.set_xticks([])
			#plot_times.plot(tdiffs, color="blue")
			#plot_times2.cla(); plot_times2.set_xticks([])
			#plot_times2.plot(t_stamps, color="red")
			#plot_rates.cla()
			#plot_rates.plot(gl.lastA1, color="black")
			#plot_rates.plot(gl.lastB1, color="black", alpha=0.3)
			#plot_rates.plot(gl.lastA2, color="red")
			#plot_rates.plot(gl.lastB2, color="red", alpha=0.3)
			#if len(tdiffs) > 100:
			#	plot_times.set_xlim(len(tdiffs)-99,len(tdiffs))
			#	plot_times2.set_xlim(len(tdiffs)-99,len(tdiffs))
			#	plot_rates.set_xlim(len(tdiffs)-99,len(tdiffs))
			#plotCanvas.draw()
			gl.index_up()
		gl.client_PC1.send_stop_loop()
		gl.client_PC2.send_stop_loop()
		enable_buttons()
	else:
		print ("Not both PCs connected!")


# Plot window
class NavigationToolbar(tkagg.NavigationToolbar2Tk):
	toolitems = [t for t in tkagg.NavigationToolbar2Tk.toolitems if t[0] in ('Home','Pan','Zoom','Save')]


fig = Figure(figsize=(4,4))
plot_times = fig.add_subplot(411); plot_times.set_xticks([])
plot_times2 = fig.add_subplot(412); plot_times2.set_xticks([])
plot_rates = fig.add_subplot(212)

plotCanvas = FigureCanvasTkAgg(fig, master=syncFrame)
plotCanvas.get_tk_widget().grid(row=1,column=0)
plotCanvas.draw()

naviFrame = Frame(syncFrame); naviFrame.grid(row=2,column=0)
navi = NavigationToolbar(plotCanvas, naviFrame)


root.mainloop()