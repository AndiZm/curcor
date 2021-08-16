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


root = Tk(); root.wm_title("II Measurement Control")#; root.geometry("+1600+10")

#############
## Network ##
#############
networkFrame = Frame(root); networkFrame.grid(row=0,column=0)

# Connection to Camera PC 1
pc1Button = Button(networkFrame, text="Client PC 1"); pc1Button.grid(row=0,column=0)
pc1status = Label(networkFrame, text="not connected", bg="grey"); pc1status.grid(row=0,column=1)


pc2Button = Button(networkFrame, text="Client PC 2"); pc2Button.grid(row=1,column=0)
pc2status = Label(networkFrame, text="not connected", bg="grey"); pc2status.grid(row=1,column=1)



root.mainloop()
