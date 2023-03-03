from multiprocessing import Process, Value, Array
import numpy as np

def execute(file, length, nchn):
    a_np = np.array([]); b_np = np.array([])
    if nchn == 2:        
        with open(file, 'rb') as f:
            buf = (f.read(2*length))
            packet = np.frombuffer(buf, dtype=np.int8)
            packet = packet.reshape(int(length), 2)
            a_np = np.array(packet[:,0]); b_np = np.array(packet[:,1])    

    if nchn == 1:
        with open(file, 'rb') as f:
            buf = (f.read(length))
            packet = np.frombuffer(buf, dtype=np.int8)
            a_np = np.array(packet)
    return a_np, b_np