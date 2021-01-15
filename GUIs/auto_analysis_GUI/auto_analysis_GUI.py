from tkinter import *
from tkinter import filedialog
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends.backend_tkagg as tkagg
from matplotlib.figure import Figure
import aa_waveform_reader as waveforms
import aa_read_header as header
import aa_scan_files as scan
import aa_auto_analysis as ana
import os
from distutils.dir_util import copy_tree

class NavigationToolbar(tkagg.NavigationToolbar2Tk):
	toolitems = [t for t in tkagg.NavigationToolbar2Tk.toolitems if t[0] in ('Home','Pan','Zoom','Save')]

root = Tk()
root.wm_title("Correlation Analysis GUI")

threshold = 0

# Header details
nCHN=1
nLen=1
nvRange=1
nvOffset=1

def adc2mv (x):
	return x*nvRange/127 - nvOffset
def mv2adc (x):
	return (x + nvOffset)*127/nvRange

mainFrame = Frame(root, width=150,height=300)
mainFrame.grid(row=0,column=0)

fileFrame = Frame(mainFrame, width=180, height=50)
fileFrame.grid(row=0, column=0)
filelabel = Label(fileFrame, text="No file selected")
filelabel.grid(row=0, column=1)

plotFrame = Frame(mainFrame, width=180, height=100)
plotFrame.grid(row=1, column=0)

waveformFrame = Frame(plotFrame, width=90, height=100)
waveformFrame.grid(row=0,column=0)

fig = Figure(figsize=[5.5,4])
a = fig.add_subplot(111)
px  = [0,1]
py0 = [0,1]
py3 = [0,1]
a.set_title("Waveforms"); a.set_xlabel("Time [microseconds]"); a.set_ylabel("ADC counts")
a2 = a.secondary_yaxis('right', functions=(adc2mv,mv2adc)); a2.set_ylabel("Voltage [mV]")
fig.subplots_adjust(left=0.2,right=0.8)

#global tl
tl = a.axhline(y=threshold)

canvas = FigureCanvasTkAgg(fig, master=waveformFrame)
canvas.get_tk_widget().grid(row=1, column=0)
canvas.draw()

filebody = ""; folder = ""
filearray = []; numbers = []
resultfilepath = ""
resultfilepath_body = "C:/Users/ii/Documents/curcor/python/results/"
def select_file():
	global binFile;	global nCHN; global nLen; global nvRange; global nvOffset; global filearray; global numbers; global f_min; global f_max
	root.filename = filedialog.askopenfilename(initialdir = "E:/", title = "Select any file", filetypes = (("binary files","*.bin"),("all files","*.*")))
	binFile = root.filename
	filebody = root.filename[:-10]
	folder = filebody.split("/")[-3]
	resultfilepath = resultfilepath_body + folder
	filebody = filebody.split("/")[-1]
	filearray = []; f_min, f_max, filearray, numbers = scan.execute(root.filename)
	filelabel.config(text="Current file: " + str(root.filename))
	fileseries_label.config(text=str(filebody))
	filemin_label.config(text = str(f_min)); filemax_label.config(text = str(f_max))
	filemin_entry.delete(0, END); filemin_entry.insert(0,str(f_min))
	filemax_entry.delete(0,END); filemax_entry.insert(10,str(f_max))
	resultentry.insert(0,resultfilepath)
	# Plot waveforms
	nCHN,nLen,px,py0,py3 = waveforms.execute(root.filename)
	nCHN, nvRange, nvOffset, nLen = header.execute(root.filename)
	nvOffset = nvOffset * 0.001
	a.cla(); a.set_title("Waveforms"); a.set_xlabel("Time [microseconds]"); a.set_ylabel("ADC counts")
	a2 = a.secondary_yaxis('right', functions=(adc2mv, mv2adc)); a2.set_ylabel("Voltage [mV]")
	a.plot(px,py0)
	if nCHN == 2:
		plotCH3 = a.plot(px,py3)
	global tl
	tl.remove(); tl = a.axhline(y=threshold, color="red", linewidth=2)
	canvas.draw()
naviFrame = Frame(waveformFrame, width=80, height=50)
naviFrame.grid(row=0, column=0)
navi = NavigationToolbar(canvas, naviFrame)

button_select_file = Button(fileFrame, text="Select any file", command=select_file)
button_select_file.grid(row=0, column=0)

#------------------------#
# Threshold settings
#------------------------#
def defineThreshold(val):
	global threshold; threshold = thresholdScale.get()
	global tl; tl.remove(); tl = a.axhline(y=threshold, color="red", linewidth=2)
	canvas.draw(); canvas.flush_events()
thresholdFrame = Frame(plotFrame, width=20, height=90, bg="#ccffcc"); thresholdFrame.grid(row=0, column=1)
thresholdLabel = Label(thresholdFrame, text="Threshold", bg="#ccffcc"); thresholdLabel.grid(row=0)
thresholdScale = Scale(thresholdFrame, variable=threshold, from_=128, to=-127, resolution=1, orient=VERTICAL, length=300, command=defineThreshold, bg="#ccffcc")
thresholdScale.grid(row=1); thresholdScale.set(128)
peaks_down = PhotoImage(file= r"images/peaks_down.png")
peaks_up   = PhotoImage(file= r"images/peaks_up.png")
toggle = -1
def toggle_threshold():
	global toggle
	if toggle == -1:
		thresholdButton.config(image=peaks_up); toggle = 1
	else:
		thresholdButton.config(image=peaks_down); toggle = -1
thresholdButton = Button(thresholdFrame, command=toggle_threshold, image=peaks_down)
thresholdButton.grid(row=2)

#------------------------#
# Correlation settings
#------------------------#
correlationFrame = Frame(plotFrame, width=90, height=90); correlationFrame.grid(row=0, column=2)
selected_label = Label(correlationFrame, text="Selected file series:"); selected_label.grid(row=0, column=0)
fileseries_label = Label(correlationFrame, width=40, text="--", bg="black", fg="orange"); fileseries_label.grid(row=1,column=0)

minmaxframe = Frame(correlationFrame); minmaxframe.grid(row=2)

selected_label = Label(minmaxframe, text="Min: "); selected_label.grid(row=0, column=0)
selected_label = Label(minmaxframe, text="Max: "); selected_label.grid(row=0, column=1)
filemin_label  = Label(minmaxframe, width=7, text="--", bg="black", fg="orange"); filemin_label.grid(row=1, column=0)
filemax_label  = Label(minmaxframe, width=7, text="--", bg="black", fg="orange"); filemax_label.grid(row=1, column=1)
filemin_entry  = Entry(minmaxframe, width=7); filemin_entry.grid(row=2, column=0)
filemax_entry  = Entry(minmaxframe, width=7); filemax_entry.grid(row=2, column=1)

def go():
	shifts = int(shiftsEntry.get())
	offset = int(offsetEntry.get())
	packetlength = int(packetlengthEntry.get())
	npackets = int(npacketsEntry.get())

	resultfilepath = resultentry.get()
	
	file_begin = numbers.index(int(filemin_entry.get())); file_end = numbers.index(int(filemax_entry.get()))
	filearray_eval = []
	for i in range (file_begin, file_end+1):
		filearray_eval.append(filearray[i])


	# Create result files directory
	if not os.path.exists(resultentry.get()):
		os.mkdir(resultentry.get())
	# Copy the calibration file directory
	dirparts = filearray_eval[0].split("/")
	dirparts[-1] = "calibs"
	builddir = dirparts[0]
	for i in range (1,len(dirparts)):
		builddir += "/" + dirparts[i]
	print (builddir)
	if not os.path.exists(resultfilepath + "/calibs"):
		os.mkdir(resultfilepath+"/calibs")
	if os.path.exists(builddir):
		copy_tree(builddir, resultfilepath+"/calibs")


	root.destroy()
	ana.execute(filearray_eval, resultfilepath, shifts, offset, packetlength, npackets, threshold)

	

# Resultpath
resultoptions = Frame(correlationFrame); resultoptions.grid(row=3)
resultlabel = Label(resultoptions, text="Result files directory:"); resultlabel.grid(row=0,column=0)
resultentry = Entry(correlationFrame, width=50); resultentry.grid(row=4)
def selectDirectory():
	global resDirectory
	root.directoryname = filedialog.askdirectory(initialdir = "C:/Users/ii/Documents/curcor/python/results/", title = "Select any file")
	resDirectory = root.directoryname
	resultfilepath = resDirectory
	resultentry.delete(0,END); resultentry.insert(0, resultfilepath)
selectDirButton = Button(resultoptions, text="Select directory", command=selectDirectory); selectDirButton.grid(row=0,column=1)

# Further correlation settings
furtherLabel = Label(correlationFrame, text="Further correlation settings", bg="#ccffcc"); furtherLabel.grid(row=5)
settingsFrame = Frame(correlationFrame, bg="#ccffcc"); settingsFrame.grid(row=6)
shiftsLabel = Label(settingsFrame, text="Shfits", bg="#ccffcc"); shiftsLabel.grid(row=0,column=0)
offsetLabel = Label(settingsFrame, text="Offset", bg="#ccffcc"); offsetLabel.grid(row=0,column=1)
packetlengthLabel = Label(settingsFrame, text="Packet length", bg="#ccffcc"); packetlengthLabel.grid(row=0,column=2)
npacketsLabel = Label(settingsFrame, text="Packets", bg="#ccffcc"); npacketsLabel.grid(row=0,column=3)

shiftsEntry = Entry(settingsFrame, width=10); shiftsEntry.grid(row=1, column=0); shiftsEntry.insert(0, "300")
offsetEntry = Entry(settingsFrame, width=10); offsetEntry.grid(row=1, column=1); offsetEntry.insert(0, "0")
packetlengthEntry = Entry(settingsFrame, width=10); packetlengthEntry.grid(row=1, column=2); packetlengthEntry.insert(0, "1000000")
npacketsEntry = Entry(settingsFrame, width=10); npacketsEntry.grid(row=1, column=3); npacketsEntry.insert(0, "2143")



goButton = Button(correlationFrame, text="Go !", command=go, width=20, height=5, bg="#ccf2ff"); goButton.grid(row=7)

root.mainloop()