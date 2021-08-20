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

from threading import Thread

import rate_client as rc
import globals as gl


root = Tk(); root.wm_title("II Measurement Control")#; root.geometry("+1600+10")

#############
## Network ##
#############
networkFrame = Frame(root); networkFrame.grid(row=0,column=0)
pc1Frame = Frame(networkFrame); pc1Frame.grid(row=0,column=0,padx=5)
pc2Frame = Frame(networkFrame); pc2Frame.grid(row=0,column=1,padx=5)

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
gl.fileRates2Button = Button(Button2Frame, text="Start File", bg="#e8fcae", width=12, state="disabled"); gl.fileRates2Button.grid(row=0,column=0)
gl.quickRates2Button = Button(Button2Frame, text="Start quick", bg="#e8fcae", width=12, state="disabled"); gl.quickRates2Button.grid(row=1,column=0)

#####################
## Synchronization ##
#####################
syncFrame = Frame(root); syncFrame.grid(row=0,column=1)

startStopMeasButton = Button(syncFrame, text="Start Measurement", bg="#92f0eb")
startStopMeasButton.grid(row=0,column=0)
measurement = False
def toggle_measure():
	global measurement
	if measurement == False: # Start measurement
		measurement = True
		#server.measure()
		startStopMeasButton.config(text="Stop Measurement", bg="#f2b4a0")
		mssLabel.config(text="Waiting for {} responses".format(gl.ndevices))
	elif measurement == True: # Stop measurement
		measurement = False
		#server.stop()
		startStopMeasButton.config(text="Start Measurement", bg="#92f0eb")
		mssLabel.config(text="Measurement stopped")
startStopMeasButton.config(command=toggle_measure)

measStatusLabel = Label(syncFrame, text="Measurement Status"); measStatusLabel.grid(row=1,column=0)
measStatusFrame = Frame(syncFrame); measStatusFrame.grid(row=2,column=0)
mssLabel = Label(measStatusFrame, text="Measurement stopped", bg="#f4f7b7", width=20); mssLabel.grid(row=0,column=0)
gl.responsesLabel = Label(measStatusFrame, text="", bg="black", fg="red", width=2); gl.responsesLabel.grid(row=0,column=1)
gl.responsetimesLabel = Label(measStatusFrame, text="", width=4, bg="grey", fg="orange"); gl.responsetimesLabel.grid(row=0,column=2)



root.mainloop()