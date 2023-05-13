from matplotlib import pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from matplotlib.pyplot import cm
import matplotlib as mpl
from tqdm import tqdm
from datetime import datetime, timezone
import ephem
import math
from scipy.optimize import curve_fit
import sys

import geometry as geo
import corrections as cor
import utilities as uti

from threading import Thread

star = sys.argv[1]
date = 20220421

exp_rates = np.loadtxt("stardata/{}/{}_{}_data.txt".format(star,star, date))[:,5]
realtime  = np.loadtxt("stardata/{}/{}_{}_data.txt".format(star,star, date))[:,0]
hour      = np.loadtxt("stardata/{}/{}_{}_data.txt".format(star,star, date))[:,1]
minute    = np.loadtxt("stardata/{}/{}_{}_data.txt".format(star,star, date))[:,2]

realt   = np.loadtxt("rates/{}/{}_{}.txt".format(star,star, date))[:,0]
rates3A = np.loadtxt("rates/{}/{}_{}.txt".format(star,star, date))[:,1]
rates3B = np.loadtxt("rates/{}/{}_{}.txt".format(star,star, date))[:,2]
rates4A = np.loadtxt("rates/{}/{}_{}.txt".format(star,star, date))[:,3]
rates4B = np.loadtxt("rates/{}/{}_{}.txt".format(star,star, date))[:,4]

times = []
tplot = []
for i in range(len(realtime)):
	times.append(ephem.Date(realtime[i]))
	t = str(times[-1]) 
	tplot.append(t.split(' ')[1])	# get h:min:sec
print(len(realtime), len(tplot))

Figure1 = plt.figure(figsize=(17,12))
plt.plot(realtime, exp_rates, marker='.', color="red", ls='', label="expected rates")
plt.plot(realt, rates3A, marker='.', color="blue", ls='', label="3A")
plt.plot(realt, rates3B, marker='.', color="orange", ls='', label="3B")
plt.plot(realt, rates4A, marker='.', color="green", ls='', label="4A")
plt.plot(realt, rates4B, marker='.', color="purple", ls='', label="4B")
plt.ylabel("Rate (MHz)", fontsize=14)
plt.xlabel("Time UTC", fontsize=14)
plt.xticks(ticks=realtime[::50], labels=tplot[::50], rotation=45, fontsize=13)
plt.yticks(fontsize=13)
plt.title(star +' ' + str(date), fontsize=17)
plt.legend()
plt.savefig("rates/{}/{}_{}_compare.pdf".format(star, star, date))
plt.show()
