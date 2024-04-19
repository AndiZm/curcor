
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

### compare amplitudes of SC fit between stars and telcombis and mean and sigma of CrossCorr gaussian fit ###

stars = ['Mimosa', 'Etacen', 'Nunki', 'Dschubba']
telcombis = ['13', '14', '34']

#plt.figure('Amps', figsize=(9,5))
#plt.suptitle('Zero baseline')
plt.figure('mean_all_high', figsize=(9,5))
plt.suptitle('CrossCorr guassian mean')
plt.figure('sigma_all_high', figsize=(9,5))
plt.suptitle('CrossCorr guassian sigma')
    
for i in  range(len(stars)):
	for j in range(len(telcombis)):
		if os.path.isdir(f"g2_functions/{stars[i]}/{telcombis[j]}"):
			telstring = telcombis[j]
			# read in zero baseline amplitudes of SC plots
			data = np.loadtxt(f"g2_functions/{stars[i]}/{telcombis[j]}/amplitudes.txt")
			ampsA = (data[0])
			dampsA = (data[1])
			ampsB = (data[2])
			dampsB = (data[3])
			# read in gaussian mean and sigma for each star and telcombi
			data = np.loadtxt(f'g2_functions/{stars[i]}/{telcombis[j]}/mu_sig.txt')
			musA = (data[0])
			dmusA = (data[1])
			sigmasA = (data[2])
			dsigmasA = (data[3])
			musB = (data[4])
			dmusB = (data[5])
			sigmasB = (data[6])
			dsigmasB = (data[7])

			plotnumber = 100 + len(telcombis)*10 + telcombis.index(telstring) + 1

			#if stars[i] != 'Dschubba':
			#	plt.figure('Amps')
			#	plt.subplot(plotnumber)
			#	plt.title(telstring)
			#	plt.ylabel('zero baseline (fs)')
			#	plt.errorbar(x=stars[i], y=ampsB, yerr=dampsB, marker='o', linestyle=' ', color=uti.color_chB, label='375nm')
			#	plt.errorbar(x=stars[i], y=ampsA, yerr=dampsA, marker='o', linestyle=' ', color=uti.color_chA, label='470nm')
			#	handles1, labels1 = plt.gca().get_legend_handles_labels()
			#	by_label1 = OrderedDict(zip(labels1, handles1))

			plt.figure('mean_all_high')
			plt.subplot(plotnumber)
			plt.title(telstring)
			plt.errorbar(x=stars[i], y=musB, yerr=dmusA, marker='o', linestyle=' ', color=uti.color_chB, label='mean 375nm')
			plt.errorbar(x=stars[i], y=musA, yerr=dmusB, marker='o', linestyle=' ', color=uti.color_chA, label='mean 470nm')
			handles2, labels2 = plt.gca().get_legend_handles_labels()
			by_label2 = OrderedDict(zip(labels2, handles2)) 
			plt.figure('sigma_all_high')
			plt.subplot(plotnumber)
			plt.title(telstring)
			plt.errorbar(x=stars[i], y=sigmasB, yerr=dsigmasB, marker='x', linestyle=' ', color=uti.color_chB, label='sigma 375nm')
			plt.errorbar(x=stars[i], y=sigmasA, yerr=dsigmasA, marker='x', linestyle=' ', color=uti.color_chA, label='sigma 470nm')
			handles3, labels3 = plt.gca().get_legend_handles_labels()
			by_label3 = OrderedDict(zip(labels3, handles3)) 


# mean and sigma for gaussian of all data
for j in range(len(telcombis)):
	telstring = telcombis[j]
	# read in gaussian mean and sigma of all data 
	data = np.loadtxt(f'g2_functions/mu_sig_{telcombis[j]}.txt')
	muA = (data[0])
	dmuA = (data[1])
	sigA = (data[2])
	dsigA = (data[3])
	muB = (data[4])
	dmuB = (data[5])
	sigB = (data[6])
	dsigB = (data[7])
	# read in data when only taking high peaks into account
	data = np.loadtxt(f'g2_functions/mu_sig_{telcombis[j]}_high.txt')
	muA_h = (data[0])
	dmuA_h = (data[1])
	sigA_h = (data[2])
	dsigA_h = (data[3])
	muB_h = (data[4])
	dmuB_h = (data[5])
	sigB_h = (data[6])
	dsigB_h = (data[7])
	# read in only sigma of all data
	data = np.loadtxt(f'g2_functions/sig_{telcombis[j]}.txt')
	sigA_all = data[0]
	dsigA_all = data[1]
	sigB_all = data[2]
	dsigB_all = data[3]

	#print('{} all: {:.2f} +/- {:.2f}'.format(telstring, sigA, dsigA))
	print('A{} all: {:.2f} +/- {:.2f}'.format(telstring, sigA_all, dsigA_all))
	print('A{} high: {:.2f} +/- {:.2f}'.format(telstring, sigA_h, dsigA_h))
	print('B{} all: {:.2f} +/- {:.2f}'.format(telstring, sigB_all, dsigB_all))
	print('B{} high: {:.2f} +/- {:.2f}'.format(telstring, sigB_h, dsigB_h))

	plotnumber = 100 + len(telcombis)*10 + telcombis.index(telstring) + 1
	plt.figure('mean_all_high')
	plt.subplot(plotnumber)
	plt.axhline(y=muA, ls='--', color=uti.color_chA, label='fixed mean')
	plt.axhline(y=muB, ls='--', color=uti.color_chB)
	plt.axhline(y=muA_h, ls='-', color=uti.color_chA, label='fixed mean high')
	plt.axhline(y=muB_h, ls='-', color=uti.color_chB)
	handles4, labels4 = plt.gca().get_legend_handles_labels()
	by_label4 = OrderedDict(zip(labels4, handles4))
	if telstring != '13':
		plt.fill_between(x=stars, y1=(muA-dmuA), y2=(muA+dmuA), alpha=0.5, color=uti.color_chA)
		plt.fill_between(x=stars, y1=(muB-dmuB), y2=(muB+dmuB), alpha=0.5, color=uti.color_chB) 

	plt.figure('sigma_all_high')
	plt.subplot(plotnumber)
	plt.axhline(y=sigA_all, ls='--', color=uti.color_chA, label='fixed sigma')
	plt.axhline(y=sigB_all, ls='--', color=uti.color_chB)
	plt.axhline(y=sigA_h, ls='-', color=uti.color_chA, label='fixed sigma high')
	plt.axhline(y=sigB_h, ls='-', color=uti.color_chB)
	handles5, labels5 = plt.gca().get_legend_handles_labels()
	by_label5 = OrderedDict(zip(labels5, handles5)) 
	#if telstring != '13':
	#	plt.fill_between(x=stars, y1=(sigA-dsigA), y2=(sigA+dsigA), alpha=0.5, color=uti.color_chA)
	#	plt.fill_between(x=stars, y1=(sigB-dsigB), y2=(sigB+dsigB), alpha=0.5, color=uti.color_chB)
	#plt.ylim([3,6])



#plt.figure('Amps')
#plt.legend(by_label1.values(), by_label1.keys())
#plt.tight_layout()
plt.figure('mean_all_high')
plt.legend(by_label2.values(), by_label2.keys())
plt.legend(by_label4.values(), by_label4.keys())
plt.tight_layout()
plt.figure('sigma_all_high')
plt.legend(by_label3.values(), by_label3.keys())
plt.legend(by_label5.values(), by_label5.keys())
plt.tight_layout()



plt.show()