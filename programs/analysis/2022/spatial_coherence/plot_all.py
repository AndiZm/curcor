import numpy as np
import matplotlib.pyplot as plt
import sys
from matplotlib.pyplot import cm


acrux  = np.loadtxt("Acrux_sc_data.txt")
shaula = np.loadtxt("Shaula_sc_data.txt")
nunki  = np.loadtxt("Nunki_sc_data.txt")

plt.figure(figsize=(6,3.5)); plt.title("Spatial coherences")
plt.xlabel("Baseline (m)"); plt.ylabel("Coherence time (fs)")

plt.errorbar(x=acrux[:,0],  y=acrux[:,2],  xerr=acrux[:,1],  yerr=acrux[:,3],  marker="o", linestyle="", color="red", label="Acrux")
plt.errorbar(x=shaula[:,0], y=shaula[:,2], xerr=shaula[:,1], yerr=shaula[:,3], marker="o", linestyle="", color="blue", label="Shaula")
plt.errorbar(x=nunki[:,0],  y=nunki[:,2],  xerr=nunki[:,1],  yerr=nunki[:,3],  marker="o", linestyle="", color="green", label="Nunki")

plt.legend()
plt.show()
