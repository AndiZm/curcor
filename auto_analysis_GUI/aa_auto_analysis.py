import subprocess
from pathlib import Path
from tqdm import tqdm
import numpy as np
import os

zeroadder = []
zeroadder.append("dummy")
zeroadder.append("0000") # einstellig
zeroadder.append("000")  # zweistellig
zeroadder.append("00")   # dreistellig
zeroadder.append("0")    # vierstellig
zeroadder.append("")     # fuenfstellig


def execute(infiles, outfilepath, shifts, offset, packetlength, npackets, threshold):
	#print ("\nThreshold: "+ str(threshold))
	#print ("Shifts: " + str(shifts))
	#print ("Offset: " + str(offset))
	#print ("Packetlength: " + str(packetlength))
	#print ("npackets: " + str(npackets))

	commands = []

	for i in range (0, len(infiles)):
		infile = infiles[i]
		outfile = infile.split("/")[-1]
		outfile = outfile[:-3] + "corr"
		resultpath = outfilepath + "/" + outfile		

		#print (infile); print ("\t" + resultpath)

		commands.append("python.exe ../pur_bin/curcor_int8_cpu_V2.py -i " + infile + " -f " + resultpath + " -a " + str(threshold) + " -b " + str(threshold) + " -s " + str(shifts) + " -o " + str(offset) + " -l " + str(packetlength) + " -p " + str(npackets))		

	# Executing the commands
	for i in tqdm(range(len(commands))):
		runstring = "xterm -e \"" + commands[i] + "\""
		print(commands[i])
		subprocess.run(commands[i])