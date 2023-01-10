import numpy as np
import matplotlib.pyplot as plt
import geometry as geo

start = int(0)
end   = int(9)

# Rate calculations
off_3a   = np.loadtxt("../calibs_ct3/off.off")[0]
off_3b   = np.loadtxt("../calibs_ct3/off.off")[1]
off_4a   = np.loadtxt("../calibs_ct4/off.off")[0]
off_4b   = np.loadtxt("../calibs_ct4/off.off")[1]

calib_3a   = np.loadtxt("../calibs_ct3/calib.calib")[10]
calib_3b   = np.loadtxt("../calibs_ct3/calib.calib")[11]
calib_4a   = np.loadtxt("../calibs_ct4/calib.calib")[10]
calib_4b   = np.loadtxt("../calibs_ct4/calib.calib")[11]


def calculate_rates (m3a, m3b, m4a, m4b):
    rate_3a = 1e-6 * (m3a-off_3a)/(calib_3a * 1.6e-9)
    rate_3b = 1e-6 * (m3b-off_3b)/(calib_3b * 1.6e-9)
    rate_4a = 1e-6 * (m4a-off_4a)/(calib_4a * 1.6e-9)
    rate_4b = 1e-6 * (m4b-off_4b)/(calib_4b * 1.6e-9)

    return rate_3a, rate_3b, rate_4a, rate_4b


r3as = []
r3bs = []
r4as = []
r4bs = []
for i in range (start,end+1):
    file = "../moon_nsb_{:05d}.fcorr".format(i)
    tdiff, mean_pc1A, mean_pc1B, mean_pc2A, mean_pc2B, az, alt, thetime = geo.get_params(file)
    
    r3a, r3b, r4a, r4b = calculate_rates(mean_pc1A, mean_pc1B, mean_pc2A, mean_pc2B)
    r3as.append(r3a)
    r3bs.append(r3b)
    r4as.append(r4a)
    r4bs.append(r4b)

x = [10,9,8,7,6,5,4,3,2,1]

plt.title("Night Sky Background")
plt.plot(x,r3as, "o--", label="CT3 Ch A", color="red")
plt.plot(x,r3bs, "o--", label="CT3 Ch B", color="orange")
plt.plot(x,r4as, "x--", label="CT4 Ch A", color="blue")
plt.plot(x,r4bs, "x--", label="CT4 Ch B", color="cyan")
plt.xlabel("Separation from moon ($^\circ$)")
plt.ylabel("Photon rates (MHz)")
plt.legend()
plt.grid()
plt.xlim(10,0)
plt.savefig("nsb.png")
plt.show()