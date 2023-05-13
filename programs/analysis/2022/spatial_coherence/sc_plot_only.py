import numpy as np
import matplotlib.pyplot as plt
import sys
from matplotlib.pyplot import cm

star = sys.argv[1]
# read in data
data = np.loadtxt("{}_sc_data.txt".format(star))
baselines  = data[:,0]
dbaselines = data[:,1]
ctimes     = data[:,2]
dctimes    = data[:,3]

# Define colormap for plotting all summarized individual g2 functions
cm_sub = np.linspace(1.0, 0.0, len(baselines-1))
colors = [cm.viridis(x) for x in cm_sub]
colors.append("black")

def axis_scale(x):
	return np.sin(x)

plt.figure(figsize=(6,3.5)); plt.title("Spatial coherence of {}".format(star))
plt.xlabel("Baseline (m)"); plt.ylabel("Coherence time (fs)")
for i in range (0,len(baselines)):
	plt.errorbar(x=120-baselines[i], y=ctimes[i], xerr=dbaselines[i], yerr=dctimes[i], marker="o", linestyle="", color=colors[i])
plt.xscale("log")
plt.show()