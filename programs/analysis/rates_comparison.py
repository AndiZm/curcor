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

exp_rates = np.loadtxt("stardata/{}/{}_19_20_data.txt".format(star,star))[4]
hour = np.loadtxt("stardata/{}/{}_19_20_data.txt".format(star,star))[0]
minute = np.loadtxt("stardata/{}/{}_19_20_data.txt".format(star,star))[1]
rates3A = np.loadtxt("rates/{}/{}_20220419.txt".format(star,star))[0]
rates3B = np.loadtxt("rates/{}/{}_20220419.txt".format(star,star))[1]
rates4A = np.loadtxt("rates/{}/{}_20220419.txt".format(star,star))[2]
rates4B = np.loadtxt("rates/{}/{}_20220419.txt".format(star,star))[3]


plt.plot(hour, exp_rates)
plt.show()
