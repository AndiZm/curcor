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
gl.pc1Button = Button(networkFrame, text="Start Client PC 1", bg="#cdcfd1", command=startstopClientPC1); gl.pc1Button.grid(row=0,column=0)

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
gl.pc2Button = Button(networkFrame, text="Start Client PC 2", bg="#cdcfd1", command=startstopClientPC2); gl.pc2Button.grid(row=1,column=0)




root.mainloop()
