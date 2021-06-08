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

class NavigationToolbar(tkagg.NavigationToolbar2Tk):
	toolitems = [t for t in tkagg.NavigationToolbar2Tk.toolitems if t[0] in ("Home","Pan","Zoom","Save")]

root = Tk(); root.wm_title("Correlations")#; root.geometry("+1600+100")
upperFrame = Frame(root); upperFrame.grid(row=0,column=0)
selectFrame = Frame(upperFrame); selectFrame.grid(row=0,column=0)

####################
#### SELECTIONS ####
####################
delSigButton = Button(selectFrame, text="Delete", fg="white", bg="red", command=sel.delSigFiles); delSigButton.grid(row=0,column=0)
bodySigButton = Button(selectFrame, text="SIG files", command=sel.selectBodyFile_sig); bodySigButton.grid(row=0, column=1)
gl.bodySigLabel = Label(selectFrame, text="No files selected"); gl.bodySigLabel.grid(row=0,column=2)
gl.begSigEntry = Entry(selectFrame, width=5); gl.begSigEntry.grid(row=0,column=3)
gl.endSigEntry = Entry(selectFrame, width=5); gl.endSigEntry.grid(row=0,column=4)

# Calibration
calibSigButton = Button(selectFrame, text="Calib", bg="#ccf2ff", command=sel.selectSigCalib); calibSigButton.grid(row=0,column=5)
gl.calibSigLabel = Label(selectFrame, text="No calib selected", bg="#ccf2ff"); gl.calibSigLabel.grid(row=0,column=6)
calibRefButton = Button(selectFrame, text="Calib", bg="#ccf2ff", command=sel.selectRefCalib); calibRefButton.grid(row=1,column=5)
gl.calibRefLabel = Label(selectFrame, text="No calib selected", bg="#ccf2ff"); gl.calibRefLabel.grid(row=1,column=6)
# Offset
offSigButton = Button(selectFrame, text="Offset", bg="#e8fcae", command=sel.selectSigOffset); offSigButton.grid(row=0,column=7)
gl.offSigLabel = Label(selectFrame, text="No off selected", bg="#e8fcae"); gl.offSigLabel.grid(row=0,column=8)
offRefButton = Button(selectFrame, text="Offset", bg="#e8fcae", command=sel.selectRefOffset); offRefButton.grid(row=1,column=7)
gl.offRefLabel = Label(selectFrame, text="No off selected", bg="#e8fcae"); gl.offRefLabel.grid(row=1,column=8)

### Delete data ###
delRefButton = Button(selectFrame, text="Delete", fg="white", bg="red", command=sel.delRefFiles); delRefButton.grid(row=1,column=0)
bodyRefButton = Button(selectFrame, text="REF files", command=sel.selectBodyFile_ref); bodyRefButton.grid(row=1, column=1)
gl.bodyRefLabel = Label(selectFrame, text="No files selected"); gl.bodyRefLabel.grid(row=1,column=2)
gl.begRefEntry = Entry(selectFrame, width=5); gl.begRefEntry.grid(row=1,column=3)
gl.endRefEntry = Entry(selectFrame, width=5); gl.endRefEntry.grid(row=1,column=4)

### Correction factor
corrSigLabel = Label(selectFrame, text="Correction factor"); corrSigLabel.grid(row=0,column=9)
gl.corrSigEntry = Entry(selectFrame, width=5); gl.corrSigEntry.insert(0,"1"); gl.corrSigEntry.grid(row=0,column=10)
corrRefLabel = Label(selectFrame, text="Correction factor"); corrRefLabel.grid(row=1,column=9)
gl.corrRefEntry = Entry(selectFrame, width=5); gl.corrRefEntry.insert(0,"1"); gl.corrRefEntry.grid(row=1,column=10)


####################
#### MAIN  PLOT ####
####################
correlationFrame = Frame(root); correlationFrame.grid(row=1,column=0)
corrFig = Figure(figsize=[13,8])
gl.corrAx = corrFig.add_subplot(221); gl.corrAx.set_title("Correlations"); gl.corrAx.set_xlabel("Time bins"); gl.corrAx.set_ylabel("$g^{(2)}$")
gl.fftAx  = corrFig.add_subplot(223); gl.fftAx.set_xlabel("Frequency [GHz]")
gl.ratesAx = corrFig.add_subplot(322); gl.ratesAx.set_title("Photon rates")
gl.rmssinAx = corrFig.add_subplot(324); gl.rmssinAx.set_ylabel("Single files RMS")
gl.rmscumAx = corrFig.add_subplot(326); gl.rmscumAx.set_ylabel("Cumulative RMS")

gl.corrCanvas = FigureCanvasTkAgg(corrFig, master=correlationFrame); gl.corrCanvas.get_tk_widget().grid(row=0,column=0); gl.corrCanvas.draw()
naviFrame = Frame(root); naviFrame.grid(row=2,column=0)
navi = NavigationToolbar(gl.corrCanvas, naviFrame)

updateFrame = Frame(upperFrame); updateFrame.grid(row=0,column=1)
binning = StringVar(root); binning.set("Sampling: 1.6 ns")
binningoptions = {"Sampling: 0.8 ns": 0.8e-9, "Sampling: 1.6 ns": 1.6e-9, "Sampling: 3.2 ns": 3.2e-9}
binningDropdown = OptionMenu(updateFrame, binning, *binningoptions); binningDropdown.grid(row=0,column=0)
gl.updateButton = Button(updateFrame, text="Update", bg="green", fg="white", height=3, command=lambda: ana.cumulate_signal(binning = float(binningoptions[binning.get()]))); gl.updateButton.grid(row=0,column=1)
gl.expcorrButton = Button(updateFrame, text="Experimental\ncorr factors", bg="orange", fg="white", height=3, command=ana.experimental_correction_factors); gl.expcorrButton.grid(row=0,column=2)

######################
#### SIDE OPTIONS ####
######################
optionsFrame = Frame(correlationFrame); optionsFrame.grid(row=0,column=1)

# Save and load configuration
saveandloadFrame = Frame(optionsFrame); saveandloadFrame.grid(row=0,column=0)
saveConfButton = Button(saveandloadFrame, text="Save Config", command=sel.save_config); saveConfButton.grid(row=0,column=0)
loadConfButton = Button(saveandloadFrame, text="Load Config", command=sel.load_config); loadConfButton.grid(row=0,column=1)

# Offset and Calibration overview
calibsFrame = Frame(optionsFrame); calibsFrame.grid(row=1,column=0)
chALabel = Label(calibsFrame, text="Ch A"); chALabel.grid(row=0,column=1)
chBLabel = Label(calibsFrame, text="Ch B"); chBLabel.grid(row=0,column=2)
offsetSigLabel = Label(calibsFrame, text="Off Sig", bg="#e8fcae"); offsetSigLabel.grid(row=1,column=0)
offsetRefLabel = Label(calibsFrame, text="Off Ref", bg="#e8fcae"); offsetRefLabel.grid(row=2,column=0)
avgChargeSigLabel = Label(calibsFrame, text="AvgCharge Sig", bg="#ccf2ff"); avgChargeSigLabel.grid(row=3,column=0)
avgChargeRefLabel = Label(calibsFrame, text="AvgCharge Ref", bg="#ccf2ff"); avgChargeRefLabel.grid(row=4,column=0)
gl.offASigLabel = Label(calibsFrame, text="--", bg="#e8fcae"); gl.offASigLabel.grid(row=1,column=1,padx=2)
gl.offBSigLabel = Label(calibsFrame, text="--", bg="#e8fcae"); gl.offBSigLabel.grid(row=1,column=2,padx=2)
gl.offARefLabel = Label(calibsFrame, text="--", bg="#e8fcae"); gl.offARefLabel.grid(row=2,column=1,padx=2)
gl.offBRefLabel = Label(calibsFrame, text="--", bg="#e8fcae"); gl.offBRefLabel.grid(row=2,column=2,padx=2)
gl.avgChargeASigLabel = Label(calibsFrame, text="--", bg="#ccf2ff"); gl.avgChargeASigLabel.grid(row=3,column=1,padx=2)
gl.avgChargeBSigLabel = Label(calibsFrame, text="--", bg="#ccf2ff"); gl.avgChargeBSigLabel.grid(row=3,column=2,padx=2)
gl.avgChargeARefLabel = Label(calibsFrame, text="--", bg="#ccf2ff"); gl.avgChargeARefLabel.grid(row=4,column=1,padx=2)
gl.avgChargeBRefLabel = Label(calibsFrame, text="--", bg="#ccf2ff"); gl.avgChargeBRefLabel.grid(row=4,column=2,padx=2)
displayCalibButton = Button(calibsFrame, text="Display Calib", bg="#ccf2ff", command=disp.displayCalib); displayCalibButton.grid(row=5,column=0)

# Digital Low pass filter
lpFrame = Frame(optionsFrame, bg="#f2b2a7"); lpFrame.grid(row=2,column=0)
def switch_patCorrButton():
	if gl.boolPatCorr == False:
		gl.boolPatCorr = True
		patCorrButton.config(text="Pattern Correction  ON", bg="#f77059")
	else:
		gl.boolPatCorr = False
		patCorrButton.config(text="Pattern Correction OFF", bg="#fad1ca")
def switch_lpButton():
	if gl.boolLP == False:
		gl.boolLP = True
		lpButton.config(text="Low pass filter  ON", bg="#f77059")
	else:
		gl.boolLP = False
		lpButton.config(text="Low pass filter OFF", bg="#fad1ca")
patCorrButton = Button(lpFrame, text="Pattern Correction  ON", bg ="#f77059", command=switch_patCorrButton); patCorrButton.grid(row=0,column=0)
lpButton = Button(lpFrame, text="Low pass filter Off", bg="#fad1ca", command=switch_lpButton); lpButton.grid(row=1,column=0)
lpParamFrame = Frame(lpFrame, bg="#f2b2a7"); lpParamFrame.grid(row=2,column=0)
cutOffLabel = Label(lpParamFrame, text="Cut off freq. [GHz]", bg="#f2b2a7"); cutOffLabel.grid(row=0,column=0)
orderLabel = Label(lpParamFrame, text="Order", bg="#f2b2a7"); orderLabel.grid(row=1,column=0)
gl.cutOffEntry = Entry(lpParamFrame, width=5, bg="#f2b2a7"); gl.cutOffEntry.insert(0,"0.2"); gl.cutOffEntry.grid(row=0,column=1)
gl.orderEntry = Entry(lpParamFrame, width=5, bg="#f2b2a7"); gl.orderEntry.insert(0,"2"); gl.orderEntry.grid(row=1,column=1)

# Analysis parameters
paramFrame = Frame(optionsFrame); paramFrame.grid(row=3,column=0)
LeftBorderLabel = Label(paramFrame, text="Left"); LeftBorderLabel.grid(row=0,column=1)
RightBorderLabel = Label(paramFrame, text="Right"); RightBorderLabel.grid(row=0,column=2)
rmsRangeLabel = Label(paramFrame, text="RMS Range"); rmsRangeLabel.grid(row=1,column=0)
fitRangeLabel = Label(paramFrame, text="Fit Range"); fitRangeLabel.grid(row=2,column=0)
gl.rmsRangeLeftEntry = Entry(paramFrame, width=4); gl.rmsRangeLeftEntry.insert(0,"100"); gl.rmsRangeLeftEntry.grid(row=1,column=1)
gl.rmsRangeRightEntry = Entry(paramFrame, width=4); gl.rmsRangeRightEntry.insert(0,"300"); gl.rmsRangeRightEntry.grid(row=1,column=2)
gl.fitRangeLeftEntry = Entry(paramFrame, width=4); gl.fitRangeLeftEntry.insert(0,"60"); gl.fitRangeLeftEntry.grid(row=2,column=1)
gl.fitRangeRightEntry = Entry(paramFrame, width=4); gl.fitRangeRightEntry.insert(0,"75"); gl.fitRangeRightEntry.grid(row=2,column=2)

# Signal fitting
fitFrame = Frame(optionsFrame); fitFrame.grid(row=4, column=0)
def f_signal_gauss():
	ana.fit_signal_gauss(binning = float(binningoptions[binning.get()])); gl.corrCanvas.draw()
def f_difference_gauss():
	ana.fit_difference_gauss(binning = float(binningoptions[binning.get()])); gl.corrCanvas.draw()
def f_signal_shape():
	ana.fit_signal_shape(binning = float(binningoptions[binning.get()])); gl.corrCanvas.draw()
def f_difference_shape():
	ana.fit_difference_shape(binning = float(binningoptions[binning.get()])); gl.corrCanvas.draw()
fitSigGaussButton = Button(fitFrame, text="Fit Sig [Gauss]", command=f_signal_gauss, width=10); fitSigGaussButton.grid(row=0,column=0)
fitDiffGaussButton = Button(fitFrame, text="Fit Diff [Gauss]", command=f_difference_gauss, width=10); fitDiffGaussButton.grid(row=0,column=1)
fitSigShapeButton = Button(fitFrame, text="Fit Sig [Shape]", command=f_signal_shape, width=10); fitSigShapeButton.grid(row=1,column=0)
fitDiffShapeButton = Button(fitFrame, text="Fit Diff [Shape]", command=f_difference_shape, width=10); fitDiffShapeButton.grid(row=1,column=1)
intLabel = Label(fitFrame, text="Coherence time"); intLabel.grid(row=2,column=0)
#timeResLabel = Label(fitFrame, text="Time resolution"); timeResLabel.grid(row=3,column=0)
gl.intValLabel = Label(fitFrame, text="---.- +/- ---.- fs", fg="orange", bg="black", font="Courier 10"); gl.intValLabel.grid(row=2,column=1)
#gl.timeResValLabel = Label(fitFrame, text="-.-- +/- -.-- ns", fg="orange", bg="black", font="Courier 10"); gl.timeResValLabel.grid(row=3,column=1)

# Big displays
bigdisplayFrame = Frame(optionsFrame); bigdisplayFrame.grid(row=5,column=0)
bdCorrButton   = Button(bigdisplayFrame, width=20, text="Big display Correlation", command=disp.displayCorrelation); bdCorrButton.grid(row=0,column=0)
bdFFTButton    = Button(bigdisplayFrame, width=20, text="Big display FFT", command=disp.displayFFT); bdFFTButton.grid(row=1,column=0)
bdRatesButton  = Button(bigdisplayFrame, width=20, text="Big display Rates", command=disp.displayRates); bdRatesButton.grid(row=2,column=0)
bdSinRMSButton = Button(bigdisplayFrame, width=20, text="Big display Single RMS", command=disp.displaySingleRMS); bdSinRMSButton.grid(row=3,column=0)
bdCumRMSButton = Button(bigdisplayFrame, width=20, text="Big display Cumulative RMS", command=disp.displayCumulativeRMS); bdCumRMSButton.grid(row=4,column=0)

# Save results
corrSaveButton = Button(bigdisplayFrame, text="Save", command=sal.save_g2); corrSaveButton.grid(row=0,column=1)
fftSaveButton = Button(bigdisplayFrame, text="Save", command=sal.save_fft); fftSaveButton.grid(row=1,column=1)
ratesSaveButton = Button(bigdisplayFrame, text="Save", command=sal.save_rate); ratesSaveButton.grid(row=2,column=1)
rmssinSaveButton = Button(bigdisplayFrame, text="Save", command=sal.save_rms_single); rmssinSaveButton.grid(row=3,column=1)
rmscumSaveButton = Button(bigdisplayFrame, text="Save", command=sal.save_rms_cumulative); rmscumSaveButton.grid(row=4,column=1)
saveAllLabel = Label(bigdisplayFrame, text="Save All Results"); saveAllLabel.grid(row=5,column=0)
saveAllButton = Button(bigdisplayFrame, text="Save", command=sal.saveAll); saveAllButton.grid(row=5,column=1)

# RMS Scale Buttons
RMSscaleFrame = Frame(optionsFrame); RMSscaleFrame.grid(row=6, column=0)
def switch_logxButton():
	if gl.boolRMSlogx == False:
		gl.boolRMSlogx = True
		RMSlogxButton.config(text="RMS log(x) ON", bg="#f77059")
	else:
		gl.boolRMSlogx = False
		RMSlogxButton.config(text="RMS log(x) OFF", bg="#fad1ca")
	xlim = gl.corrAx.get_xlim(); ylim = gl.corrAx.get_ylim()
	disp.refresh_display(binning = float(binningoptions[binning.get()]))
	gl.corrAx.set_xlim(xlim); gl.corrAx.set_ylim(ylim)
def switch_logyButton():
	if gl.boolRMSlogy == False:
		gl.boolRMSlogy = True
		RMSlogyButton.config(text="RMS log(y) ON", bg="#f77059")
	else:
		gl.boolRMSlogy = False
		RMSlogyButton.config(text="RMS log(y) OFF", bg="#fad1ca")
	xlim = gl.corrAx.get_xlim(); ylim = gl.corrAx.get_ylim()
	disp.refresh_display(binning = float(binningoptions[binning.get()]))
	gl.corrAx.set_xlim(xlim); gl.corrAx.set_ylim(ylim)
RMSlogxButton = Button(RMSscaleFrame, text= "RMS log(x) ON", bg="#f77059", command=switch_logxButton); RMSlogxButton.grid(row=0,column=0)
RMSlogyButton = Button(RMSscaleFrame, text= "RMS log(y) ON", bg="#f77059", command=switch_logyButton); RMSlogyButton.grid(row=1,column=0)

root.mainloop()