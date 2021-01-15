import numpy as np
import matplotlib; matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends.backend_tkagg as tkagg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import subprocess
import os
import time
from tkinter import *
import scipy.signal as ss
from threading import Thread

# own files
import globs as gl
import selections as sel
import analysis as ana
import displays as disp
import saveandload as sal

root = Tk(); root.wm_title("Correlations")#; root.geometry("+1600+100")

####################
#### MAIN  PLOT ####
####################
correlationFrame = Frame(root); correlationFrame.grid(row=1,column=0)
######################
#### SIDE OPTIONS ####
######################
optionsFrame = Frame(correlationFrame); optionsFrame.grid(row=0,column=1)

# Analysis parameters
paramFrame = Frame(optionsFrame); paramFrame.grid(row=3,column=0)
rmsRangeLabel = Label(paramFrame, text="RMS Range"); rmsRangeLabel.grid(row=1,column=0)
gl.rmsRangeLeftEntry = Entry(paramFrame, width=4); gl.rmsRangeLeftEntry.insert(0,"100"); gl.rmsRangeLeftEntry.grid(row=1,column=1)
gl.rmsRangeRightEntry = Entry(paramFrame, width=4); gl.rmsRangeRightEntry.insert(0,"200"); gl.rmsRangeRightEntry.grid(row=1,column=2)

# Big displays
bigdisplayFrame = Frame(optionsFrame); bigdisplayFrame.grid(row=5,column=0)
bdCorrButton   = Button(bigdisplayFrame, width=20, text="Big display Correlation", command=disp.displayCorrelation); bdCorrButton.grid(row=0,column=0)

root.mainloop()