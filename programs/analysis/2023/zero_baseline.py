import numpy as np
import matplotlib.pyplot as plt
import os
from collections import OrderedDict

import utilities as uti

### compare amplitudes of SC fit between stars and calculate global weighted average for each color ###
def zero_baseline():
	stars = ['Mimosa', 'Etacen', 'Nunki']
	telcombis = ['13', '14', '34']
	
	plt.figure('Zerobaseline', figsize=(9,5))
	plt.suptitle('Zero baseline')
	
	avgA = []; weightA = []; avgB = []; weightB = []
	
	for i in  range(len(stars)):
		data = np.loadtxt(f"g2_functions/{stars[i]}/amplitudes.txt")
		ampsA = (data[0])
		dampsA = (data[1])
		ampsB = (data[2])
		dampsB = (data[3])
	
		avgA.append(ampsA); weightA.append(1/dampsA**2)
		avgB.append(ampsB); weightB.append(1/dampsB**2)
	
		plt.figure('Zerobaseline')
		plt.subplot(121)
		plt.title("470nm")
		plt.errorbar(x=stars[i], y=ampsA, yerr=dampsA, marker='o', linestyle=' ', color=uti.color_chA)
		plt.subplot(122)
		plt.title("375nm")
		plt.errorbar(x=stars[i], y=ampsB, yerr=dampsB, marker='o', linestyle=' ', color=uti.color_chB)
	
	avgA = np.average(avgA, weights=weightA, returned=True)
	avgB = np.average(avgB, weights=weightB, returned=True)
	davgA = np.sqrt(1/avgA[1])
	davgB = np.sqrt(1/avgB[1])
	print("ZB A: {:.2f} +/- {:.2f}".format(avgA[0], davgA))
	print("ZB B: {:.2f} +/- {:.2f}".format(avgB[0], davgB))

	plt.figure('Zerobaseline')
	plt.subplot(121)
	plt.axhline(avgA[0], ls='--', color=uti.color_chA, label='weighted average')
	plt.fill_between(x=stars, y1=(avgA[0]-davgA), y2=(avgA[0]+davgA), alpha=0.5, color=uti.color_chA)
	plt.subplot(122)
	plt.axhline(avgB[0], ls='--', color=uti.color_chB, label='weighted average')
	plt.fill_between(x=stars, y1=(avgB[0]-davgB), y2=(avgB[0]+davgB), alpha=0.5, color=uti.color_chB)
	plt.tight_layout()
	
	return avgA, davgA, avgB, davgB