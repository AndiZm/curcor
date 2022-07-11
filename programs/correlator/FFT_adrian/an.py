import numpy as np
import matplotlib.pyplot as plt

fast = np.loadtxt("bunchtimes_fast_raid.txt")
big  = np.loadtxt("bunchtimes_big_raid.txt")
big_cross = np.loadtxt("bunchtimes_big_raid_cross.txt")

plt.plot(fast[0:33], label="Fast raid")
plt.plot(big[0:33], label="Big raid")
plt.plot(big_cross[0:33], label="Big raid Cross correlation")
plt.axhline(y=20, color="grey", linestyle="--", label="Realtime")
plt.xlabel("File bunch index")
plt.ylabel("Analysis time (s)")
plt.legend()
plt.ylim(0,)
plt.show()