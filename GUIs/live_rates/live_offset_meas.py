import time
import numpy as np
import subprocess
import os
from os import listdir
from os.path import isfile, join
from tqdm import tqdm

import globals as gl

def execute(file, packet_length, npackets):
    means_a = []; means_b = []
    packets = np.arange(0, npackets)
    if gl.o_nchn == 2:
        with open(file, 'rb') as f:
            for allpkt in tqdm(packets):
                buf = (f.read(2*packet_length))
                packet = np.frombuffer(buf, dtype=np.int8)
                packet = packet.reshape(packet_length, 2)
                a_np = np.array(packet[:,0]).flatten(); b_np = np.array(packet[:,1]).flatten()
                means_a.append(np.mean(a_np)); means_b.append(np.mean(b_np))
                del(a_np); del(b_np)
                if gl.stop_offset_thread == True:
                    break
        mean_a_ADC = np.mean(means_a); mean_b_ADC = np.mean(means_b)        
    else:
        with open(file, 'rb') as f:
            for allpkt in tqdm(packets):
                buf = (f.read(packet_length))
                packet = np.frombuffer(buf, dtype=np.int8)
                a_np = np.array(packet).flatten()
                means_a.append(np.mean(a_np))
                del(a_np)
                if gl.stop_offset_thread == True:
                    break
        mean_a_ADC = np.mean(means_a); mean_b_ADC = None
    return mean_a_ADC, mean_b_ADC