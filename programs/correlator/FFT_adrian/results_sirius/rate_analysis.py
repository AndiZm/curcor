import matplotlib.pyplot as plt
import ephem
from datetime import datetime, timezone
import numpy as np
import matplotlib.dates as mdates
from matplotlib.pyplot import cm
import matplotlib as mpl
from tqdm import tqdm

import geometry as geo

# Ephem parameters
sirius = ephem.star("Sirius")
ECAP_roof = ephem.Observer()
ECAP_roof.lat  = ephem.degrees("49.58068")
ECAP_roof.long = ephem.degrees("11.02771")


def calculations(file):

    global times, rates_1, rates_2, azs, alts, tdiffs, bins

    header = file.readline().split(" ")
    ctime  = float(header[1])
    mean_1 = float(header[2])
    mean_2 = float(header[3])

    # Sirius coordinates
    # Time needs to be transferred to UTC, which is -1 hour
    time = datetime.utcfromtimestamp(ctime)
    ECAP_roof.date = ephem.date(time)
    sirius.compute(ECAP_roof)
    azs.append(180*sirius.az/np.pi); alts.append(180*sirius.alt/np.pi)
    # Time delay between the telescopes
    tdiff = geo.get_time_delay_azalt(sirius.az, sirius.alt)
    tdiffs.append(tdiff)
    bins.append(timebin(tdiff))

    # Calculate rates
    rate_1 = 1e-6 * mean_1/(calib_1 * 1.6e-9)
    rate_2 = 1e-6 * mean_2/(calib_2 * 1.6e-9)

    times.append(time); rates_1.append(rate_1); rates_2.append(rate_2)

def drawlines(axis):
    axis.axhline(y= 0.8, color="grey", linestyle="--")
    axis.axhline(y=-0.8, color="grey", linestyle="--")
    axis.axhline(y=-2.4, color="grey", linestyle="--")
    axis.axhline(y=  -4, color="grey", linestyle="--")
def timebin(tdiff):
    return 1.0* np.floor((tdiff+0.8)/1.6)
# Figure to plot everything
ratesfig = plt.figure(figsize=(24,12))


range_low  = int(20000)
range_high = int(30000)

# Define the G2 functions for all time shifts
lenG2 = len(np.loadtxt("20220223_roof/sirius_00000.fcorr")[range_low:range_high])
G2_1 = np.zeros(lenG2)
G2_0 = np.zeros(lenG2)
G2m1 = np.zeros(lenG2)
G2m2 = np.zeros(lenG2)
G2m3 = np.zeros(lenG2)
def add_to_G2(bin_value, data):
    if bin_value == +1:
        for j in range (0,lenG2):
            G2_1[j] += data[j]
    if bin_value == +0:
        for j in range (0,lenG2):
            G2_0[j] += data[j]
    if bin_value == -1:
        for j in range (0,lenG2):
            G2m1[j] += data[j]
    if bin_value == -2:
        for j in range (0,lenG2):
            G2m2[j] += data[j]
    if bin_value == -3:
        for j in range (0,lenG2):
            G2m3[j] += data[j]
##################
### 2022-02-23 ###
##################
# Rate calculation parameters
off_1   = -1.875039434999999921e-01
off_2   = 2.796415305000000129e-01
calib_1 = -59.111833199224705
calib_2 = -67.38270732002343

times = []; rates_1 = []; rates_2 = []; azs = []; alts = []; tdiffs = []; bins=[]
for i in tqdm(range (0,2191)):
    f = open( "20220223_roof/sirius_{:05d}.fcorr".format(i) )
    calculations(f)
    data = np.loadtxt("20220223_roof/sirius_{:05d}.fcorr".format(i))[range_low:range_high]
    add_to_G2(bins[-1], data)

# Plot Photon rates
ax1 = ratesfig.add_subplot(251); ax12 = ax1.twinx()
ax1.set_title("2022-02-23")
ax1.plot(times, rates_1, "o", markersize=2, label="Rates Tel 1")
ax1.plot(times, rates_2, "o", markersize=2, label="Rates Tel 2")
ax1.legend(loc="lower left")
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax1.set_xlabel("Time (UTC)"); ax1.set_ylabel("Photon rates (MHz)")
ax1.set_ylim(0,400)
ax12.plot(times, alts, color="black", label="Sirius altitude")
ax12.set_ylabel("Sirius altitude (deg)")
ax12.set_ylim(12,24)
ax1.grid()
ax12.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax12.legend(loc="lower right")

axt1 = ratesfig.add_subplot(256)
axt1.plot(times, tdiffs, color="blue")
#axt1.plot(times, bins, color="blue")
axt1.grid()
axt1.set_ylim(-5,2)
drawlines(axt1)
axt1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))




##################
### 2022-02-27 ###
##################
# Rate calculation parameters
off_1   = -3.603750420000000343e-01
off_2   = 1.352422540000000062e-01
calib_1 = -65.2418293569126
calib_2 = -70.77924338810277

times = []; rates_1 = []; rates_2 = []; azs = []; alts = []; tdiffs = []
for i in tqdm(range (0,3670)):
    f = open( "20220227_roof/sirius_{:05d}.fcorr".format(i) )
    calculations(f)
    data = np.loadtxt("20220227_roof/sirius_{:05d}.fcorr".format(i))[range_low:range_high]
    add_to_G2(bins[-1], data)

# Plot Photon rates
ax2 = ratesfig.add_subplot(252); ax22 = ax2.twinx()
ax2.set_title("2022-02-27")
ax2.plot(times, rates_1, "o", markersize=2, label="Rates Tel 1")
ax2.plot(times, rates_2, "o", markersize=2, label="Rates Tel 2")
ax2.legend(loc="lower left")
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax2.set_xlabel("Time (UTC)")
ax2.set_ylabel("Photon rates (MHz)")
ax2.set_ylim(0,400)
ax22.plot(times, alts, color="black", label="Sirius altitude")
ax22.set_ylabel("Sirius altitude (deg)")
ax22.set_ylim(12,24)
ax2.grid()
ax22.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax22.legend(loc="lower right")

axt2 = ratesfig.add_subplot(257)
axt2.plot(times, tdiffs, color="blue")
axt2.grid()
axt2.set_ylim(-5,2)
drawlines(axt2)
axt2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

##################
### 2022-02-28 ###
##################
# Rate calculation parameters
off_1   = -2.992445699999999320e-01
off_2   = 1.731211954999999914e-01
calib_1 = -64.1976299649758
calib_2 = -72.3535181676592

times = []; rates_1 = []; rates_2 = []; azs = []; alts = []; tdiffs = []
#for i in range (0,220):
#    try:
#        f = open( "20220228_roof/sirius_{:05d}.fcorr".format(i) )
#        calculations(f)
#    except:
#        print ("Error with file 20220228_roof/sirius_{:05d}.fcorr".format(i))
for i in tqdm(range (250,3025)):
    f = open( "20220228_roof/sirius_{:05d}.fcorr".format(i) )
    calculations(f)
    data = np.loadtxt("20220228_roof/sirius_{:05d}.fcorr".format(i))[range_low:range_high]
    add_to_G2(bins[-1], data)

# Plot Photon rates
ax3 = ratesfig.add_subplot(253); ax32 = ax3.twinx()
ax3.set_title("2022-02-28")
ax3.plot(times, rates_1, "o", markersize=2, label="Rates Tel 1")
ax3.plot(times, rates_2, "o", markersize=2, label="Rates Tel 2")
ax3.legend(loc="lower left")
ax3.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax3.set_xlabel("Time (UTC)"); ax3.set_ylabel("Photon rates (MHz)")
ax3.set_ylim(0,400)
ax32.plot(times, alts, color="black", label="Sirius altitude")
ax32.set_ylabel("Sirius altitude (deg)")
ax32.set_ylim(12,24)
ax3.grid()
ax32.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax32.legend(loc="lower right")

axt3 = ratesfig.add_subplot(258)
axt3.plot(times, tdiffs, color="blue")
axt3.grid()
axt3.set_ylim(-5,2)
drawlines(axt3)
axt3.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

##################
### 2022-03-01 ###
##################
# Rate calculation parameters
off_1   = -2.192952975000000138e-01
off_2   = 1.943128819999999923e-01
calib_1 = -64.86034819968731
calib_2 = -66.26559787316005

times = []; rates_1 = []; rates_2 = []; azs = []; alts = []; tdiffs = []
for i in tqdm(range (0,2747)):
    f = open( "20220301_roof/sirius_{:05d}.fcorr".format(i) )
    calculations(f)
    data = np.loadtxt("20220301_roof/sirius_{:05d}.fcorr".format(i))[range_low:range_high]
    add_to_G2(bins[-1], data)

# Plot Photon rates
ax4 = ratesfig.add_subplot(254); ax42 = ax4.twinx()
ax4.set_title("2022-03-01")
ax4.plot(times, rates_1, "o", markersize=2, label="Rates Tel 1")
ax4.plot(times, rates_2, "o", markersize=2, label="Rates Tel 2")
ax4.legend(loc="lower left")
ax4.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax4.set_xlabel("Time (UTC)")
ax4.set_ylabel("Photon rates (MHz)")
ax4.set_ylim(0,400)
ax42.plot(times, alts, color="black", label="Sirius altitude"); ax42.set_ylabel("Sirius altitude (deg)")
ax42.set_ylim(12,24)
ax4.grid()
ax42.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax42.legend(loc="lower right")

axt4 = ratesfig.add_subplot(259)
axt4.plot(times, tdiffs, color="blue")
axt4.grid()
axt4.set_ylim(-5,2)
drawlines(axt4)
axt4.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))


##################
### 2022-03-03 ###
##################
# Rate calculation parameters # TO CHANGE
off_1   = -2.192952975000000138e-01
off_2   = 1.943128819999999923e-01
calib_1 = -64.86034819968731
calib_2 = -66.26559787316005

times = []; rates_1 = []; rates_2 = []; azs = []; alts = []; tdiffs = []
for i in tqdm(range (0,2776)):
    f = open( "20220303_roof/sirius_{:05d}.fcorr".format(i) )
    calculations(f)
    data = np.loadtxt("20220303_roof/sirius_{:05d}.fcorr".format(i))[range_low:range_high]
    add_to_G2(bins[-1], data)

# Plot Photon rates
ax5 = ratesfig.add_subplot(255); ax52 = ax5.twinx()
ax5.set_title("2022-03-01")
ax5.plot(times, rates_1, "o", markersize=2, label="Rates Tel 1")
ax5.plot(times, rates_2, "o", markersize=2, label="Rates Tel 2")
ax5.legend(loc="lower left")
ax5.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax5.set_xlabel("Time (UTC)")
ax5.set_ylabel("Photon rates (MHz)")
ax5.set_ylim(0,400)
ax52.plot(times, alts, color="black", label="Sirius altitude"); ax52.set_ylabel("Sirius altitude (deg)")
ax52.set_ylim(12,24)
ax5.grid()
ax52.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax52.legend(loc="lower right")

axt5 = ratesfig.add_subplot(2510)
axt5.plot(times, tdiffs, color="blue")
axt5.grid()
axt5.set_ylim(-5,2)
drawlines(axt5)
axt5.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))


plt.tight_layout()
plt.savefig("rates.png")
np.savetxt("G2s.txt", np.c_[G2_1, G2_0, G2m1, G2m2, G2m3])
plt.show()