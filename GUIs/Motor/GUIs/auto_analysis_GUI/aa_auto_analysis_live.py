import subprocess
from pathlib import Path
from tqdm import tqdm
import numpy as np
import os
import sys
#sys.path.append("mnt/c/Users/ii/Documents/curcor/python/pur_bin")
import curcor_int8_cpu_V2_function as curcor
import matplotlib.pyplot as plt

zeroadder = []
zeroadder.append("0000")
zeroadder.append("0000") # einstellig
zeroadder.append("000")  # zweistellig
zeroadder.append("00")   # dreistellig
zeroadder.append("0")    # vierstellig
zeroadder.append("")     # fuenfstellig

def number_of_digits (x):
	if x == 0:
		return 1
	else:
		return int (np.floor(np.log10(x)+1))

def execute(infiles, outfilepath, shifts, offset, packetlength, npackets, threshold):
	#print ("\nThreshold: "+ str(threshold))
	#print ("Shifts: " + str(shifts))
	#print ("Offset: " + str(offset))
	#print ("Packetlength: " + str(packetlength))
	#print ("npackets: " + str(npackets))

	#commands = []

	for i in range (0, len(infiles)):
		
		infile = infiles[i]
		outfile = infile.split("/")[-1]
		outfile = outfile[:-3] + "corr"
		resultpath = outfilepath + "/" + outfile		
	
		#print (infile); print ("\t" + resultpath)
		G2 = curcor.execute(infile, resultpath, shifts, offset, packetlength, npackets)

def execute_openEnd(infiles, outfilepath, shifts, offset, packetlength, npackets, threshold):
	#print ("\nThreshold: "+ str(threshold))
	#print ("Shifts: " + str(shifts))
	#print ("Offset: " + str(offset))
	#print ("Packetlength: " + str(packetlength))
	#print ("npackets: " + str(npackets))

	#commands = []
	G2_ges = np.zeros(shifts)
	plt.ion()
	fig = plt.figure(); ax = fig.add_subplot(211); ax_fft = fig.add_subplot(212); ax_fft.set_xlim(0,0.625/2); ax_fft.set_xlabel("Frequency [GHz]")
	G2_plot, = ax.plot(0,0); fft_plot, = ax_fft.plot(0,0)

	counter = int(0)
	while (True):

		infile = infiles[0][:-9] + zeroadder[number_of_digits(counter)] + str(counter) + ".bin"
		outfile = infile.split("/")[-1]
		outfile = outfile[:-3] + "corr"
		resultpath = outfilepath + "/live/" + outfile
		try:	
			print ("TRY\t" + infile)#; print ("\t" + resultpath)
			G2 = curcor.execute(infile, resultpath, shifts, offset, packetlength, npackets)

		except:
			print ("No further file found - end analysis")
			break

		#G2 analysis
		for i in range (0,shifts):
			G2_ges[i] += G2[i]
		#g2
		g2 = []; norm = np.mean(G2_ges[100:])
		for i in range (0,shifts):
			g2.append(G2_ges[i]/norm)
		#fft
		g2_fft = []
		for i in range (100,shifts):
			g2_fft.append(g2[i]-1.)
		fft = np.fft.fft(g2_fft)
		xfft = np.linspace(0,1./1.6,len(g2_fft),endpoint=True)

		G2_plot.remove(); fft_plot.remove()
		G2_plot, = ax.plot(g2, color="red"); ax.set_ylim(np.min(g2), np.max(g2))
		fft_plot, = ax_fft.plot(xfft,np.abs(fft), color="red")
		fig.canvas.draw(); fig.canvas.flush_events()

		counter += 1
		