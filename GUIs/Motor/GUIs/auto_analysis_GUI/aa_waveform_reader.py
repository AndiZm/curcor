import sys
import time as t
from tqdm import tqdm
from multiprocessing import Process, Value, Array
import scipy.signal as ss
import numpy as np
import matplotlib.pyplot as plt

def execute(file, numChan):

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
	return x, a_np, b_np