from tkinter import *
from tkinter import filedialog
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends.backend_tkagg as tkagg
from matplotlib.figure import Figure
import analyzer_waveform_reader as waveforms
import analyzer_rates as rates
import analyzer_read_header as header

class NavigationToolbar(tkagg.NavigationToolbar2Tk):
	toolitems = [t for t in tkagg.NavigationToolbar2Tk.toolitems if t[0] in ('Home','Pan','Zoom','Save')]

root = Tk()
root.wm_title("Waveform Analyzer")

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

fig_histo = Figure(figsize=[5.5,4])
a_histo = fig_histo.add_subplot(111)
a_histo.set_title("Peak height histogram")
a_histo.set_xlabel("Peak heights [ADC counts]")
a_histo.set_ylabel("Counts")
a_histo2 = a_histo.secondary_xaxis('top', functions=(adc2mv,mv2adc)); a_histo2.set_xlabel("Peak heights [mV]")
fig_histo.subplots_adjust(left=0.2,top=0.8,bottom=0.15)

#global tl
tl = a.axhline(y=threshold)

canvas = FigureCanvasTkAgg(fig, master=waveformFrame)
canvas.get_tk_widget().grid(row=1, column=0)
canvas.draw()


def select_file():
	global binFile;	global nCHN; global nLen; global nvRange; global nvOffset
	root.filename = filedialog.askopenfilename(initialdir = "E:/", title = "Select file", filetypes = (("binary files","*.bin"),("all files","*.*")))
	binFile = root.filename
	filelabel.config(text="Current file: " + str(root.filename))
	CH0_Label.config(text="--"); CH3_Label.config(text="--")
	# Plot waveforms
	nCHN,nLen,px,py0,py3 = waveforms.execute(root.filename)
	nCHN, nvRange, nvOffset, nLen = header.execute(root.filename)
	nvOffset = nvOffset * 0.001
	print("Offset:  " + str(nvOffset))
	a.cla(); a.set_title("Waveforms"); a.set_xlabel("Time [microseconds]"); a.set_ylabel("ADC counts")
	a2 = a.secondary_yaxis('right', functions=(adc2mv, mv2adc)); a2.set_ylabel("Voltage [mV]")
	a_histo.cla(); a_histo.set_title("Peak height histogram");
	a_histo.set_xlabel("Peak heights [ADC counts]"); a_histo.set_ylabel("Counts")
	a_histo2 = a_histo.secondary_xaxis('top', functions=(adc2mv,mv2adc)); a_histo2.set_xlabel("Peak heights [mV]")	
	a.plot(px,py0)
	if nCHN == 2:
		plotCH3 = a.plot(px,py3)
	global tl
	tl.remove()
	tl = a.axhline(y=threshold, color="red", linewidth=2)
	canvas.draw(); histo_canvas.draw()
naviFrame = Frame(waveformFrame, width=80, height=50)
naviFrame.grid(row=0, column=0)
navi = NavigationToolbar(canvas, naviFrame)

button_select_file = Button(fileFrame, text="Select file", command=select_file)
button_select_file.grid(row=0, column=0)


#------------------------#
# Threshold settings
#------------------------#
def defineThreshold(val):
	global threshold
	threshold = thresholdScale.get()
	global tl
	tl.remove()
	tl = a.axhline(y=threshold, color="red", linewidth=2)
	canvas.draw()
	canvas.flush_events()
thresholdFrame = Frame(plotFrame, width=20, height=90); thresholdFrame.grid(row=0, column=1)
thresholdLabel = Label(thresholdFrame, text="Threshold"); thresholdLabel.grid(row=0)
thresholdScale = Scale(thresholdFrame, variable=threshold, from_=127, to=-127, resolution=1, orient=VERTICAL, length=300, command=defineThreshold)
thresholdScale.grid(row=1)
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
# Rate calculations
#------------------------#

histogramFrame = Frame(plotFrame, width=80, height=100); histogramFrame.grid(row=0,column=2)
rcLabel = Label(histogramFrame, text="Rate calculations",width=90); rcLabel.grid(row=0)

histo_canvas = FigureCanvasTkAgg(fig_histo, master=histogramFrame)
histo_canvas.get_tk_widget().grid(row=1)
histo_canvas.draw()
histo_naviFrame = Frame(histogramFrame, width=60, height=40); histo_naviFrame.grid(row=0)
histo_navi = NavigationToolbar(histo_canvas, histo_naviFrame); histo_navi.grid(row=0,column=0)




histo_ButtonFrame = Frame(mainFrame, width=180,height=50); histo_ButtonFrame.grid(row=2)
fracEval = 1
Eval_Label = Label(histo_ButtonFrame, text="Evaluation fraction"); Eval_Label.grid(row=0,column=0)
Eval_Range = Scale(histo_ButtonFrame, variable = fracEval, from_=0.001, to=1, resolution=0.001, orient=HORIZONTAL, length=600)
Eval_Range.grid(row=0,column=1)

def rateScan():
	nCHN, rate_0, rate_3, h_x, h_0, h_3 = rates.execute(binFile, Eval_Range.get(), threshold, toggle)
	#print ("Rate 0:  " + str(rate_0) + " MHz")
	CH0_Label.config(text='{:.2f} MHz'.format(rate_0))
	a_histo.cla(); a_histo.set_title("Peak height histogram")
	a_histo.set_xlabel("Peak heights [ADC counts]"); a_histo.set_ylabel("Counts")
	a_histo2 = a_histo.secondary_xaxis('top', functions=(adc2mv,mv2adc)); a_histo2.set_xlabel("Peak heights [mV]")
	a_histo.plot(h_x, h_0)
	if nCHN == 2:
		CH3_Label.config(text='{:.2f} MHz'.format(rate_3))
		a_histo.plot(h_x, h_3)
	histo_canvas.draw(); histo_canvas.flush_events()
RateScan_Button = Button(histo_ButtonFrame, text="Rate Scan", command=rateScan); RateScan_Button.grid(row=0, column=2)

CH0 = Label(histo_ButtonFrame, text="Rate CH 0: ", width=20); CH0.grid(row=0, column=3)
CH0_Label = Label(histo_ButtonFrame, text="--", fg="orange", bg="black", font=("Helvetica 12 bold")); CH0_Label.grid(row=0, column=4)
CH3 = Label(histo_ButtonFrame, text="Rate CH 3: ", width=20); CH3.grid(row=0, column=5)
CH3_Label = Label(histo_ButtonFrame, text="--", fg="orange", bg="black", font=("Helvetica 12 bold")); CH3_Label.grid(row=0, column=6)
unnuetzLabel = Label(histo_ButtonFrame, text="     ", font=("Helvetica 12 bold")); unnuetzLabel.grid(row=0,column=7)

def linScale():
	a_histo.set_yscale('linear'); histo_canvas.draw(); histo_canvas.flush_events()
def logScale():
	a_histo.set_yscale('log'); histo_canvas.draw(); histo_canvas.flush_events()
LinButton = Button(histo_naviFrame, text="Lin", command=linScale); LinButton.grid(row=0,column=1)
LogButton = Button(histo_naviFrame, text="Log", command=logScale); LogButton.grid(row=0,column=2)


root.mainloop()