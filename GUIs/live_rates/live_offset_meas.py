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
    return mean_a_ADC, mean_b_ADC

def execute_single(file, packet_length, npackets):
    means_a = []
    packets = np.arange(0, npackets)
    with open(file, 'rb') as f:
        for allpkt in tqdm(packets):
            buf = (f.read(packet_length))
            packet = np.frombuffer(buf, dtype=np.int8)
            a_np = np.array(packet).flatten()
            means_a.append(np.mean(a_np))
            del(a_np)
            if gl.stop_offset_thread == True:
                break
    mean_a_ADC = np.mean(means_a)
    return mean_a_ADC

def search_and_execute(path, samples, packet_length, npackets):

    channels = 2
    
    # Start files which are not to analyze
    startfiles = [f for f in listdir(path) if isfile(join(path, f))]
    filearray = []
    for i in range (0, len(startfiles)):
        if startfiles[i][-4:] == ".bin":
            filearray.append(path + "/" + startfiles[i])
    
    # Search for new files
    while (True):
        # Search if new files are available
        current_files = [f for f in listdir(path) if isfile(join(path, f))]    
        newfiles = []; modified = []; new = False
        for i in range (0, len(current_files)):
            cfile = path + "/" + current_files[i]
            if cfile not in filearray and os.stat(cfile).st_size >= (channels*samples) and cfile[-4:] == ".bin":
                filearray.append(cfile); newfiles.append(cfile); modified.append(os.stat(cfile).st_mtime_ns)
                new = True
        # Find newest file and analyze
        if new == True:
            newest_file = newfiles[np.argmax(modified)]
            #print ("Newest file: " + newest_file)
            new = False
            means_a = []; means_b = []
    
            with open(newest_file, 'rb') as f:
                for allpkt in range(0, npackets):
                    buf = (f.read(2*packet_length))
                    packet = np.frombuffer(buf, dtype=np.int8)
                    packet = packet.reshape(packet_length, 2)
                    a_np = np.array(packet[:,0]).flatten(); b_np = np.array(packet[:,1]).flatten()
                    means_a.append(np.mean(a_np)); means_b.append(np.mean(b_np))
                    del(a_np); del(b_np)
    
            mean_a_ADC = np.mean(means_a); mean_b_ADC = np.mean(means_b)
            return mean_a_ADC, mean_b_ADC
        time.sleep(0.5)