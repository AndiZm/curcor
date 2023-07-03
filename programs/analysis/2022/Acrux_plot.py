import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import  GridSpec
from matplotlib.pyplot import cm
import matplotlib.patches as mpatches

# Read in sc data
data = np.loadtxt("Acrux_sc_data.txt")
# cross correlations
baselines  = data[:,0][:-1]
dbaselines = data[:,1][:-1]
ints       = data[:,2][:-1]
dints      = data[:,3][:-1]
# auto correlation
b0  = data[:,0][-1]
db0 = data[:,1][-1]
i0  = data[:,2][-1]
di0 = data[:,3][-1]

# Read in time data
actimes = np.genfromtxt("actimes_acrux.txt", dtype="str")


grid = GridSpec (1, 10, left=0.1, bottom=0.15, right=0.94, top=0.94, wspace=0.1, hspace=0.3)
fig = plt.figure(figsize=(12,3.5))
fig.suptitle("Spatial coherence of Acrux", x=0.53, y=1.0)


cm_sub = np.linspace(1.0, 0.0, len(baselines))
colors = [cm.viridis(x) for x in cm_sub]

# colors
c1 = colors[2]
c2 = colors[int(len(baselines)/2)]
c3 = colors[-1]
colors = [c1,c1,c1,c1,c1,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c3,c3,c3,c3]

ax_zero   = fig.add_subplot( grid[0:1, 0:1] ); ax_zero.set_ylim(0,30); ax_zero.set_xlim(0,10)
ax_zero.set_ylabel("Coherence time (fs)")

ax_middle = fig.add_subplot( grid[0:1, 1:5] )
ax_middle.set_ylim(0,30); ax_middle.set_xlim(74,113)
ax_middle.get_yaxis().set_visible(False)

ax_right  = fig.add_subplot( grid[0:1, 5:10])
ax_right.set_ylim(0,30); ax_right.set_xlim(113,117)
ax_right.yaxis.tick_right()


# Plot zero baseline
ax_zero.errorbar(b0, i0, yerr=di0, xerr=db0, marker="o", linestyle="", color="black")

# Plot cross correlations
for i in range (0, len(baselines)):
    ax_middle.errorbar(baselines[i], ints[i], yerr=dints[i], xerr=dbaselines[i], marker="o", linestyle="", color=colors[i])
    ax_right.errorbar( baselines[i], ints[i], yerr=dints[i], xerr=dbaselines[i], marker="o", linestyle="", color=colors[i])


c1_patch = mpatches.Patch(color=c1, label='night of 4/16')
c2_patch = mpatches.Patch(color=c2, label='night of 4/17')
c3_patch = mpatches.Patch(color=c3, label='night of 4/18')

#ax_right.legend(handles=[c1_patch, c2_patch, c3_patch], loc="upper left")
plt.figlegend(handles=[c1_patch, c2_patch, c3_patch], bbox_to_anchor=(0.575,0.9), bbox_transform=fig.transFigure, framealpha=1)

fig.supxlabel("Baseline (m)")
plt.tight_layout()
plt.savefig("acrux_zoomed.pdf")
plt.show()