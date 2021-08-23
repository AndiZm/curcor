import sys
import time as t
from tqdm import tqdm
from multiprocessing import Process, Value, Array
import scipy.signal as ss
import numpy as np
#import pyopencl as cl
import matplotlib.pyplot as plt

def execute(file):

	numLen = 123456789
	headerfile = file[:-4] + "_binheader.txt"
	headerstring = [line.rstrip('\n') for line in open(headerfile)]
	numChan = int (headerstring[2][-1:])
	#print (numChan)
	for i in range (0, len(headerstring)):
		substr = headerstring[i].split("=")
		if substr[0] == "LenL ":
			#print (headerstring[i])
			numLen = int(substr[1])
	#numLen = int(substr[1])
	if numLen == 0:
		numLen = 4e9
	#print (str(numLen))

	a_np = np.array([])
	b_np = np.array([])

	length = 10000

	if numChan == 1 :    	
		with open(file, 'rb') as f:
		    f.read(0)
		    buf = (f.read(length))
		    packet = np.frombuffer(buf, dtype=np.int8)
		    a_np = np.array(packet)

	if numChan == 2 :    	
		with open(file, 'rb') as f:
			f.read(0)
			buf = (f.read(2*length))
			packet = np.frombuffer(buf, dtype=np.int8)
			packet = packet.reshape(int(2*length/2), 2)
			a_np = np.array(packet[:,0])
			b_np = np.array(packet[:,1])

	x = np.linspace(0,1e-3*0.8*len(a_np),len(a_np))
	return numChan, numLen, x, a_np, b_np