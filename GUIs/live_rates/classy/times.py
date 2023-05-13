import numpy as np
import matplotlib.pyplot as plt
import os

t0 = np.loadtxt("tel_0.txt")
t1 = np.loadtxt("tel_1.txt")
t2 = np.loadtxt("tel_2.txt")

missed_seconds  = 0


for i in range (0,len(t0)):
    if t0[i] >= 4 or t1[i] >= 4:# or t2[i] >= 4:
        #plt.axvline(x=i, color="red", alpha=0.3)
        missed_seconds += 1
        if t0[i] >= 5 or t1[i] >= 5:# or t2[i] >= 5:
            missed_seconds += 1

t_first = os.path.getmtime("G:/ct4/delme/measurement_00000.bin")

t_prev  = os.path.getmtime("G:/ct4/delme/measurement_00000.bin")
t_next = 0
t_diffs = []
t_acs = []; t_acs.append(t_first)
for i in range (1,len(t0)):        
    # Get file time
    t_next = os.path.getmtime("G:/ct4/delme/measurement_{:05d}.bin".format(i))
    t_acs.append(t_next)
    t_diff = t_next - t_prev
    t_prev = t_next
    t_diffs.append(t_diff)

t_last = os.path.getmtime("G:/ct4/delme/measurement_{:05d}.bin".format(len(t0)-1))
t_total = t_last - t_first + 4
print ("Total acquisition time: {:.2f} min".format(t_total/60))
np.savetxt("ac_times.txt", t_acs)


plt.figure(figsize=(15,5))
#plt.fill_between(x=np.arange(1,len(t_diffs)+1, 1), y1=0, y2=t_diffs, color="black", alpha=1, label="Time between two files")
plt.plot(np.arange(1,len(t_diffs)+1, 1), t_diffs, "-", color="black", linewidth=2, label="Time between two files")
plt.plot(t0, color="#34ebb7", alpha=0.7, label="F:")
plt.plot(t1, color="#003366", alpha=0.7, label="G:")
plt.plot(t2, color="red",     alpha=0.7, label="Z: (server)")

plt.ylim(3,)


print ("Number of measurements: {}".format(len(t0)))
print ("Missed seconds: {}".format(missed_seconds))
# Expected acquisition time:
t_exp = 4 * len(t0) + missed_seconds
print ("Should take {} mins to acquire".format(t_exp/60))

plt.xlabel("Measurement index")
plt.ylabel("Acquisition times (s)")

plt.legend()
plt.savefig("actimes.png")



plt.figure()

plt.hist(t_diffs, bins=[0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5])
plt.xlabel("Time between two files")
plt.savefig("actimes_histo.png")
plt.show()

plt.figure(figsize=(15,5))

plt.subplot(131)
plt.plot(t0, t1, "o", markersize=2)
plt.xlabel("Acquisition time for file on   F:")
plt.ylabel("Acquisition time for file on   G:")

plt.subplot(132)
plt.plot(t0, t2, "o", markersize=2)
plt.xlabel("Acquisition time for file on   F:")
plt.ylabel("Acquisition time for file on   Z:")

plt.subplot(133)
plt.plot(t1, t2, "o", markersize=2)
plt.xlabel("Acquisition time for file on   G:")
plt.ylabel("Acquisition time for file on   Z:")

plt.show()