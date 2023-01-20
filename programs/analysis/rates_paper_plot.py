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
date = '20220419'


times = np.loadtxt( "rates/{}/{}_{}.txt".format(star, star, date) )[:,0]
rates_3A= np.loadtxt( "rates/{}/{}_{}.txt".format(star, star, date) )[:,1]
rates_3B= np.loadtxt( "rates/{}/{}_{}.txt".format(star, star, date) )[:,2]

tplot=[]
for i in range(len(times)):
	time = (ephem.Date(times[i]))
	t = str(time) 
	tplot.append(t.split(' ')[1])	# get h:min:sec
print(tplot[-1])


F1 = plt.figure(figsize=(10, 5))
plt.plot(tplot, rates_3A, color=uti.color_3A, label='Channel 3A', marker=".")
plt.plot(tplot, rates_3B, color=uti.color_3B, label="Channel 3B", marker='.')
plt.xticks(tplot[::1000], rotation=45)
#plt.yticks(fontsize=13)
plt.legend()
plt.title("Rates of {}".format(star))
plt.xlabel("Time (UTC)")
plt.ylabel("Rate (MHz)")
plt.tight_layout()
plt.savefig("rates/{}/{}_{}_paper.pdf".format(star, star, date))
plt.show()