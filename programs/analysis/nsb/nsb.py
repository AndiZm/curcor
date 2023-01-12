import numpy as np
import matplotlib.pyplot as plt

data = np.loadtxt("nsb_data.txt")

distances = data[:,0]
r3as      = data[:,1]
r3bs      = data[:,2]
r4as      = data[:,3]
r4bs      = data[:,4]

plt.figure(figsize=(5,3.5))
plt.title("Night Sky Background")

plt.plot(distances, r3as, "o--", label="CT3 Ch A", color="#8f0303", markersize=7)
plt.plot(distances, r3bs, "o--", label="CT3 Ch B", color="#f7a488", markersize=7)
plt.plot(distances, r4as, "X--", label="CT4 Ch A", color="#003366", markersize=7)
plt.plot(distances, r4bs, "X--", label="CT4 Ch B", color="#98cced", markersize=7)
plt.xlabel("Separation from moon ($^\circ$)")
plt.ylabel("Photon rates (MHz)")
plt.legend()
#plt.grid()
plt.xlim(11,0)
plt.tight_layout()
plt.savefig("nsb.pdf")
plt.show()