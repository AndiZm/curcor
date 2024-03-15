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



stars = ['Mimosa', 'Etacen', 'Nunki']


ampsA = []; dampsA = []; ampsB = []; dampsB = []
musA = []; sigmasA = []; musB = []; sigmasB = []
dmusA = []; dsigmasA = []; dmusB = []; dsigmasB = []

for i in  range(len(stars)):
	data = np.loadtxt("g2_functions/{}/14/amplitudes.txt".format(stars[i]))
	ampsA.append(data[0])
	dampsA.append(data[1])
	ampsB.append(data[2])
	dampsB.append(data[3])
	data = np.loadtxt('g2_functions/{}/14/mu_sig.txt'.format(stars[i]))
	musA.append(data[0])
	dmusA.append(data[1])
	sigmasA.append(data[2])
	dsigmasA.append(data[3])
	musB.append(data[4])
	dmusB.append(data[5])
	sigmasB.append(data[6])
	dsigmasB.append(data[7])

plt.figure('Amps')
plt.subplot(121)
plt.errorbar(x=stars, y=ampsB, yerr=dampsB, marker='o', linestyle=' ', color=uti.color_chB, label='375nm')
plt.errorbar(x=stars, y=ampsA, yerr=dampsA, marker='o', linestyle=' ', color=uti.color_chA, label='470nm')

# weighted average
ampA = np.average(ampsA, weights=(1/np.array(dampsA))**2)
ampB = np.average(ampsB, weights=(1/np.array(dampsB))**2)
plt.axhline(ampA, color=uti.color_chA, linestyle='--')
plt.axhline(ampB, color=uti.color_chB, ls='--')
plt.text( 0.5, y=ampA+1, s='{:.2f}'.format(ampA), color=uti.color_chA)
plt.text( 0.5, y=ampB+1, s='{:.2f}'.format(ampB), color=uti.color_chB)
plt.title('Telcombi 14')
plt.legend()
plt.ylabel('zero-baseline coherence time (fs)')

plt.figure('mu_sig')
plt.subplot(121)
plt.errorbar(x=stars, y=musB, yerr=dmusA, marker='o', linestyle=' ', color=uti.color_chB, label='mean 375nm')
plt.errorbar(x=stars, y=musA, yerr=dmusB, marker='o', linestyle=' ', color=uti.color_chA, label='470nm')
plt.errorbar(x=stars, y=sigmasB, yerr=dsigmasB, marker='x', linestyle=' ', color=uti.color_chB, label='sigma')
plt.errorbar(x=stars, y=sigmasA, yerr=dsigmasA, marker='x', linestyle=' ', color=uti.color_chA)
plt.title('Telcombi 14')
plt.legend()


ampsA = []; dampsA = []; ampsB = []; dampsB = []
musA = []; sigmasA = []; musB = []; sigmasB = []
dmusA = []; dsigmasA = []; dmusB = []; dsigmasB = []

for i in  range(len(stars)):
	data = np.loadtxt("g2_functions/{}/34/amplitudes.txt".format(stars[i]))
	ampsA.append(data[0])
	dampsA.append(data[1])
	ampsB.append(data[2])
	dampsB.append(data[3])
	data = np.loadtxt('g2_functions/{}/34/mu_sig.txt'.format(stars[i]))
	musA.append(data[0])
	dmusA.append(data[1])
	sigmasA.append(data[2])
	dsigmasA.append(data[3])
	musB.append(data[4])
	dmusB.append(data[5])
	sigmasB.append(data[6])
	dsigmasB.append(data[7])

plt.figure('Amps')
plt.subplot(122)
plt.errorbar(x=stars, y=ampsB, yerr=dampsB, marker='o', linestyle=' ', color=uti.color_chB, label='375nm')
plt.errorbar(x=stars, y=ampsA, yerr=dampsA, marker='o', linestyle=' ', color=uti.color_chA, label='470nm')

# weighted average
ampA = np.average(ampsA, weights=(1/np.array(dampsA))**2)
ampB = np.average(ampsB, weights=(1/np.array(dampsB))**2)

plt.axhline(ampA, color=uti.color_chA, linestyle='--')
plt.axhline(ampB, color=uti.color_chB, ls='--')
plt.text( 0.5, y=ampA+1, s='{:.2f}'.format(ampA), color=uti.color_chA)
plt.text( 0.5, y=ampB+1, s='{:.2f}'.format(ampB), color=uti.color_chB)
plt.title('Telcombi 34')
plt.legend()
plt.ylabel('zero-baseline coherence time (fs)')
plt.tight_layout()

plt.figure('mu_sig')
plt.subplot(122)
plt.errorbar(x=stars, y=musB, yerr=dmusA, marker='o', linestyle=' ', color=uti.color_chB, label='mean 375nm')
plt.errorbar(x=stars, y=musA, yerr=dmusB, marker='o', linestyle=' ', color=uti.color_chA, label='470nm')
plt.errorbar(x=stars, y=sigmasB, yerr=dsigmasB, marker='x', linestyle=' ', color=uti.color_chB, label='sigma')
plt.errorbar(x=stars, y=sigmasA, yerr=dsigmasA, marker='x', linestyle=' ', color=uti.color_chA)

plt.title('Telcombi 34')
plt.legend()
plt.tight_layout()

plt.show()