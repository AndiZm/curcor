import numpy as np
import matplotlib.pyplot as plt

data = np.loadtxt("../g2_functions/weight_rms_squared/Mimosa/14/ChA.txt")

# 12 oder 13
plt.plot(data[12])
plt.plot(data[13])
plt.show()