import numpy as np
import os
#import tkFileDialog as filedialog
from tkinter import filedialog
import globs as gl

def maketxtpath():
	txtpath = gl.basicpath_sig + "/saves"
	if not os.path.exists(txtpath):
		os.mkdir(txtpath)

def save_g2():
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
	with open(gl.basicpath_sig + "/saves/g2.txt", "w") as f:
		f.write(header + "\n")
		for j in range (0,len(savearrays[0])):
			for arrays in range(0, len(savearrays)):
				f.write("{}\t".format(savearrays[arrays][j]))
			f.write("\n")
def save_fft():
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
	with open(gl.basicpath_sig + "/saves/fft.txt", "w") as f:
		f.write(header + "\n")
		for j in range (0,len(savearrays[0])):
			for arrays in range(0, len(savearrays)):
				f.write("{}\t".format(savearrays[arrays][j]))
			f.write("\n")
def save_rate():
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
	with open(gl.basicpath_sig + "/saves/rates.txt", "w") as f:
		f.write(header + "\n")
		for j in range (0,len(savearrays[0])):
			for arrays in range(0, len(savearrays)):
				f.write("{}\t".format(savearrays[arrays][j]))
			f.write("\n")
def save_rms_single():
	maketxtpath()
	savearrays = []; header = "#"
	if gl.boolSig == True:
		savearrays.append(gl.rmssin_sig)
		header += "\tSig\t"
	if gl.boolRef == True:
		savearrays.append(gl.rmssin_ref)
		header += "\tRef"
	with open(gl.basicpath_sig + "/saves/rms_single.txt", "w") as f:
		f.write(header + "\n")
		for j in range (0,len(savearrays[0])):
			for arrays in range(0, len(savearrays)):
				f.write("{}\t".format(savearrays[arrays][j]))
			f.write("\n")

def save_rms_cumulative():
	maketxtpath()
	savearrays = []; header = "#"
	if gl.boolSig == True:
		savearrays.append(gl.rmscum_sig)
		savearrays.append(gl.rmscum_sig_exp)
		header += "\tSig\tSig_exp\t"
	if gl.boolRef == True:
		savearrays.append(gl.rmscum_ref)
		header += "\tRef\tRef_exp\t"
	with open(gl.basicpath_sig + "/saves/rms_cumulative.txt", "w") as f:
		f.write(header + "\n")
		for j in range (0,len(savearrays[0])):
			for arrays in range(0, len(savearrays)):
				f.write("{}\t".format(savearrays[arrays][j]))
			f.write("\n")

def saveAll():
	save_g2()
	save_fft()
	save_rate()
	save_rms_single()