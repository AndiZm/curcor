import numpy as np
import matplotlib.pyplot as plt

import sys; sys.path.append("../")
import utilities as uti

data = np.loadtxt("nsb_data.txt")

distances = data[:,0]
r3as      = data[:,1]
r3bs      = data[:,2]
r4as      = data[:,3]
r4bs      = data[:,4]

plt.figure(figsize=(6,3.5))
plt.title("Night Sky Background")

plt.plot(distances, r3as, "o--", label="CT3 Ch A", color=uti.color_3A, markersize=7)
plt.plot(distances, r3bs, "o--", label="CT3 Ch B", color=uti.color_3B, markersize=7)
plt.plot(distances, r4as, "X--", label="CT4 Ch A", color=uti.color_4A, markersize=7)
plt.plot(distances, r4bs, "X--", label="CT4 Ch B", color=uti.color_4B, markersize=7)
plt.xlabel("Separation from moon ($^\circ$)")
plt.ylabel("Photon rates (MHz)")
plt.legend()
#plt.grid()
plt.xlim(11,0)
plt.tight_layout()
plt.savefig("nsb.pdf")
plt.show()