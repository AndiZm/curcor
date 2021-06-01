import numpy as np
import os
from tkinter import filedialog
import globs as gl
from tkinter import *

savename = []; nwindow = []; savefileentry = []
header = []; savearrays = []

def maketxtpath():
	txtpath = gl.basicpath_sig + "/saves"
	if not os.path.exists(txtpath):
		os.mkdir(txtpath)

def confirm_save():
	global savename, nwindow, savefileentry, header, savearrays
	savename = str(savefileentry.get())
	nwindow.destroy()
	with open(gl.basicpath_sig + "/saves/" + savename, "w") as f:
		f.write(header + "\n")
		for j in range (0,len(savearrays[0])):
			for arrays in range(0, len(savearrays)):
				f.write("{}\t".format(savearrays[arrays][j]))
			f.write("\n")

def namewindow(prename):
	global savename, nwindow, savefileentry
	nwindow = Tk()
	savefileentry = Entry(nwindow); savefileentry.grid(row=0,column=0); savefileentry.insert(0,prename)
	okbutton = Button(nwindow, text="OK", command=confirm_save); okbutton.grid(row=0,column=1)
	nwindow.mainloop()

def save_g2():
	global savename, savearrays, header
	maketxtpath()
	savearrays = []; header = "#"
	if gl.boolSig == True:
		savearrays.append(gl.g2_sig)
		header += "\tSig"
	if gl.boolRef == True:
		savearrays.append(gl.g2_ref)
		header += "\tRef"
		if gl.boolSig == True:
			savearrays.append(gl.g2_diff)
			header += "\tDiff"
	namewindow("g2.txt")
	
def save_fft():
	global savename, savearrays, header
	maketxtpath()
	savearrays = []; header = "#"
	if gl.boolSig == True:
		savearrays.append(gl.g2_sig_fft)
		header += "\tSig"
	if gl.boolRef == True:
		savearrays.append(gl.g2_ref_fft)
		header += "\tRef"
		if gl.boolSig == True:
			savearrays.append(gl.g2_diff_fft)
			header += "\tDiff"
	namewindow("fft.txt")

def save_rate():
	global savename, savearrays, header
	maketxtpath()
	savearrays = []; header = "#"
	if gl.boolSig == True:
		savearrays.append(gl.rates_a_sig)
		savearrays.append(gl.rates_b_sig)
		header += "\tSig A\tSig B"
	if gl.boolRef == True:
		savearrays.append(gl.rates_a_ref)
		savearrays.append(gl.rates_b_ref)
		header += "\tRefA\tRefB"
	namewindow("rates.txt")

def save_rms_single():
	global savename, savearrays, header
	maketxtpath()
	savearrays = []; header = "#"
	if gl.boolSig == True:
		savearrays.append(gl.rmssin_sig)
		header += "\tSig\t"
	if gl.boolRef == True:
		savearrays.append(gl.rmssin_ref)
		header += "\tRef"
	namewindow("rms_single.txt")

def save_rms_cumulative():
	global savename, savearrays, header
	maketxtpath()
	savearrays = []; header = "#"
	if gl.boolSig == True:
		savearrays.append(gl.rmscum_sig)
		savearrays.append(gl.rmscum_sig_err) # temporarily?
		savearrays.append(gl.rmscum_sig_exp)
		
		header += "\tSig\tSig_Err\tSig_exp\t"
	if gl.boolRef == True:
		savearrays.append(gl.rmscum_ref)
		header += "\tRef\tRef_exp\t"
	namewindow("rms_cumulative.txt")

def saveAll():
	save_g2()
	save_fft()
	save_rate()
	save_rms_single()
	save_rms_cumulative()