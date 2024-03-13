import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl  
from scipy.optimize import curve_fit
from scipy.signal import butter, filtfilt, find_peaks
import scipy.stats as stats
from matplotlib.pyplot import cm
import ephem
import scipy.special as scp
import sys
from brokenaxes import brokenaxes
from matplotlib.gridspec import GridSpec
import os
from scipy import odr
from collections import OrderedDict
from matplotlib.offsetbox import AnchoredText
from optparse import OptionParser

import utilities as uti
import corrections as cor
import geometry as geo



stars = ['Mimosa', 'Etacen']


ampsA = []; dampsA = []; ampsB = []; dampsB = []

plt.figure('Amps')

for i in  range(len(stars)):
	data = np.loadtxt("g2_functions/{}/34/amplitudes.txt".format(stars[i]))

	ampsA.append(data[0])
	dampsA.append(data[1])
	ampsB.append(data[2])
	dampsB.append(data[3])

plt.errorbar(x=stars, y=ampsB, yerr=dampsB, marker='o', linestyle=' ', color=uti.color_chB, label='chB 375nm')
plt.errorbar(x=stars, y=ampsA, yerr=dampsA, marker='o', linestyle=' ', color=uti.color_chA, label='chA 470nm')

# weighted average
ampA = np.average(ampsA, weights=(1/np.array(dampsA))**2)
ampB = np.average(ampsB, weights=(1/np.array(dampsB))**2)

plt.axhline(ampA, color=uti.color_chA, linestyle='--')
plt.axhline(ampB, color=uti.color_chB, ls='--')

#plt.ylim(0,30)
plt.title('Telcombi 14')
plt.legend()
plt.ylabel('zero-baseline coherence time (fs)')
plt.show()