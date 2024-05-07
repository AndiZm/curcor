import sys
import time as t
from tqdm import tqdm
from multiprocessing import Process, Value, Array
import scipy.signal as ss
import numpy as np
from optparse import OptionParser

from corr_lib import corr_CPU

parser = OptionParser()

parser.add_option("-s", "--shift", dest="shift", default='300', help="number of shifts")
parser.add_option("-i", "--input file", dest="file", help='Path to input file')
parser.add_option("-p", "--packets", dest="packets", default='2143', help='Number of data packets')
parser.add_option("-f", "--output", dest="outfile", help='Output txt-file', default="correlation.corr")
parser.add_option("-o", "--offset", dest="offset", help='Offset for correlation function', default="0")
parser.add_option("-l", "--plength", dest="packetlength", default='1000000', help='Length of each packet')
parser.add_option("-a", "--thresa", dest="thresa", default='200', help='Threshold Channel 0')
parser.add_option("-b", "--thresb", dest="thresb", default='200', help='Threshold Channel 3')

(options, args) = parser.parse_args()
test = 0 #test = int(options.test)
shift = int(options.shift)
file = str(options.file)
outfile = str(options.outfile)
npackets = int(options.packets)
packet_length = int(options.packetlength)
offset = int(options.offset)
threshold_a = int(options.thresa)
threshold_b = int(options.thresb)

print ("File = " + file)

if __name__ == '__main__':

    G2_pos = np.zeros(shift+1, dtype=np.int64)#; G2_neg = np.zeros(shift+1, dtype=np.int64)
    packets = np.arange(0, npackets)
    t3 = t.time()

    means_a = []; means_b = []

    # Calculation on CPU using numba.jit
    with open(file, 'rb') as f:
        for allpkt in tqdm(packets):
        	# Read in data
            buf = (f.read(2*packet_length))
            packet = np.frombuffer(buf, dtype=np.int8)
            # Format data; data stream is [8 bit Channel a time 0][8 bit Channel b time 0]-> Continue with time 1
            packet = packet.reshape(packet_length, 2)
            a_np = np.array(packet[:,0]); b_np = np.array(packet[:,1])
            aa_np = a_np[250:packet_length-250]; bb_np = b_np[250:packet_length-250] # Skip margin of files
            #aa_np[aa_np > threshold_a] = 0; bb_np[bb_np > threshold_b] = 0  # Threshold to cut noise
            G2_pos += corr_CPU(aa_np, bb_np, shift, offset)#; G2_neg += corr_CPU(bb_np, aa_np, shift, offset)

            means_a.append(np.mean(aa_np)); means_b.append(np.mean(bb_np))
            del(a_np); del(b_np); del(aa_np); del(bb_np)

    t4 = t.time()
    mean_a = np.mean(means_a); mean_b = np.mean(means_b)
    print('Computation time: {}s'.format(t4-t3))

    #path = 'C:/Users/ii/Documents/stromkorr_auswertungen/20191111_oldPMTs_ref/'
    path = ''
    with open(path+outfile, 'w') as f:
        f.write('# Analysed with numba and curcor_int8.py\n')
        f.write('# Computation time: {}h\n'.format((t4-t3)/3600.))
        f.write('# -------------------------------- #\n')
        f.write('# File:\t\t{}\n'.format(file))
        f.write('# Number of bytes:\t{}\n'.format(npackets*packet_length))
        f.write('# shifts {}\n'.format(shift))
        f.write('# offset {}\n'.format(offset))
        f.write('# -------------------------------- #\n')
        #f.write('# No threshold\n')
        f.write('# CHANNEL A:\n')
        f.write('# ADC to 0 if above {}\n'.format(threshold_a))
        f.write('# CHANNEL B:\n')
        f.write('# ADC to 0 if above {}\n'.format(threshold_b))
        f.write('# -------------------------------- #\n')
        f.write('# MEANS\n')
        f.write('# {}\n'.format(mean_a))
        f.write('# {}\n'.format(mean_b))
        f.write('# -------------------------------- #\n')
        f.write('# Delta_t[bin]\tG2[events]\n')
        #for i in range(len(G2_neg)):
            #f.write('{}\t{}\n'.format(- offset - shift + i, G2_neg[i]))
        for i in range(len(G2_pos)):
            f.write('{}\t{}\n'.format(offset + i, G2_pos[i]))