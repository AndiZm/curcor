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


root = Tk(); root.wm_title("II Measurement Control")#; root.geometry("+1600+10")

#############
## Network ##
#############
networkFrame = Frame(root); networkFrame.grid(row=0,column=0)
client_PC1 = None
client_PC2 = None

# Connection to Camera PC 1
pc1Button = Button(networkFrame, text="Start Client PC 1", bg="#cdcfd1"); pc1Button.grid(row=0,column=0)

# Connection to Camera PC 2
def startstopClientPC2():
	global client_PC2
	#check if client is running
	if client_PC2 == None :	
		#start client
		client_PC2=rc.controller_client("client_to_PC2")
		try:
			client_PC2.connect()
			#change button label
			pc2Button.config(text="Stop Client PC 2", bg="#ffc47d")
		except OSError as err:
			print("The OS did not allow start the server on {0}:{1} . Are address and port correct? Maybe an old instance is still blocking this resource?".format(server.address, server.port))
			print(err)
			client_PC2 = None
	else:
		#shutdown server
		client_PC2.stop()
		#change button label
		pc2Button.config(text="Start Client PC 2", bg="#cdcfd1")
		client_PC2 = None
pc2Button = Button(networkFrame, text="Start Client PC 2", bg="#cdcfd1", command=startstopClientPC2); pc2Button.grid(row=1,column=0)




root.mainloop()
