import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
import random
from scipy.optimize import curve_fit
import utilities as uti
from tqdm import tqdm
from matplotlib.pyplot import cm

n_sim = 500
cutoff_freq = 0.04

def lowpass(data, cutoff):    
    fs = 1./1.6
    nyq = 0.5*fs
    cutoff = cutoff # GHz
    order = 1
    normal_cutoff = cutoff / nyq
    # Get the filter coefficients 
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    data = filtfilt(b, a, data)
    return data

######################################
# EXTRACT INFORMATION FROM REAL DATA #
######################################
# Read in sample data, which is a Mimosa chunk with high spatial coherence
data = np.loadtxt("../g2_functions/weight_rms_squared/Mimosa/14/ChB.txt")
g2 = data[13]
x  = np.arange( -1.6*len(g2)//2 , 1.6*len(g2)//2 , 1.6  )

plt.figure(figsize=(12,6))
plt.subplot(211); plt.title("Real g2 function")
plt.plot(x, g2)
plt.xlim(-500,500)
plt.xlabel("Time difference (ns)")
plt.ylabel("$g^{(2)}$")
plt.ticklabel_format(useOffset=False)

# Fit g2 peak for model peak
xplot, popt, perr = uti.fit(data=g2, x=x, s=-100, e=100, mu_start=0)
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
bunching_params = np.array(popt, copy=True)
integral_true, dintegral_true = uti.integral_fixed(popt, [0], bunching_params[2])

# Extract waveform Fourier transform and rms from region without peak
rms = np.std(g2[5100:9000])
print ("Real signal rms:\t{:.8f}".format(rms))
fft  = np.abs(np.fft.fft(g2[5100:9000]-1))
fft[0] = 0.00003 # random value to fit into 
fft = fft[0:len(fft)//2]
xfft = np.linspace(0,1/1.6/2,len(fft),endpoint=True)

plt.subplot(212); plt.title("Fourier transform (off-peak)")
plt.plot(xfft, fft)
plt.xlabel("Frequency (GHz)")
#fft = lowpass(fft, cutoff=0.005)
#plt.plot(xfft, fft)
plt.tight_layout()
plt.savefig("images/original.png")
plt.show()


############################
# INITIAL SIMULATION TESTS #
############################
# Generate simulated signal
simulated = []
for i in range (0,len(g2)):
	simulated.append(random.gauss(1,rms))

plt.figure(figsize=(12,6))
plt.subplot(211); plt.title("Simulated g2 function (no signal)")
plt.plot(x,simulated, label="Random uncorrelated noise")
simulated_low = lowpass(simulated, cutoff=cutoff_freq)


# Check RMS of lowpass noise
rms_lowpass  = np.std(simulated_low)
scale_factor = rms/rms_lowpass

# Build new simulated signal with higher initial rms
simulated_new = []
for i in range (0,len(g2)):
	simulated_new.append(random.gauss(1,scale_factor * rms))
simulated_new = lowpass(simulated_new, cutoff=cutoff_freq)
print ("Simulated signal rms:\t{:.8f}".format(np.std(simulated_new)))

plt.plot(x, simulated_new, label="Random noise with lowpass")
plt.xlim(-700,700)
plt.xlabel("Time difference (ns)")
plt.ylabel("$g^{(2)}$")
plt.ticklabel_format(useOffset=False)
plt.legend()

# FFTs
fft     = np.abs(np.fft.fft(np.array(simulated)-1))
fft_low = np.abs(np.fft.fft(np.array(simulated_new)-1))
xfft    = np.linspace(0,1/1.6,len(fft),endpoint=True)

plt.subplot(212); plt.title("Fourier transform")
plt.plot(xfft, fft)
plt.plot(xfft, fft_low)
plt.xlim(0,0.625/2)
plt.xlabel("Frequency (GHz)")
plt.tight_layout()
plt.savefig("images/simulated_no_signal.png")
plt.show()

#################
# g2 SIMULATION #
#################
scale = 5
def generate_g2():
	array = []
	# First fill random noise
	for i in range (0,len(g2)):
		array.append(1 + random.gauss(0,scale_factor * rms))
	array = lowpass(array, cutoff=cutoff_freq)
	# add bunching peak
	for i in range (0,len(g2)):
		array[i] += scale * uti.gauss(x[i], bunching_params[0], bunching_params[1], bunching_params[2], 0)
	return array

g2_sim = generate_g2()

plt.figure(figsize=(12,6))
plt.subplot(211); plt.title("Comparison of real and simulated data")
plt.plot(x, g2, label="Real data")
plt.plot(x, g2_sim, label="Simulated data")
plt.xlim(-500,500)
plt.xlabel("Time difference (ns)")
plt.ylabel("$g^{(2)}$")
plt.ticklabel_format(useOffset=False)
plt.legend()

fft     = np.abs(np.fft.fft(g2-1))
fft_sim = np.abs(np.fft.fft(g2_sim-1))
xfft    = np.linspace(0,1/1.6,len(fft), endpoint=True)

plt.subplot(212); plt.title("Fourier transform")
plt.plot(xfft, fft)
plt.plot(xfft, fft_sim, alpha=0.7)
plt.xlim(0,0.625/2)
plt.xlabel("Frequency (GHz)")
plt.tight_layout()
plt.savefig("images/comparison.png")
plt.show()

#######################################
# PLOT A FEW SIMULATED g2 FOR THE EYE #
#######################################
nsims = 20
cm_sub = np.linspace(1.0, 0.0, nsims)
colors = [cm.viridis(x) for x in cm_sub]
plt.figure(figsize=(12,6)); plt.title("Simulated samples")
for i in range (0,nsims):
	g2 = generate_g2()
	plt.plot(x, g2, color=colors[i])
xplot = np.arange(-50,50,0.1)
plt.plot(xplot, uti.gauss_fixed(xplot,bunching_params[0],bunching_params[1],bunching_params[2]), color="red", linestyle="--", linewidth=3, label="True curve")

plt.xlabel("Time difference (ns)")
plt.ylabel("$g^{(2)}$")
plt.xlim(-100,100)
plt.ticklabel_format(useOffset=False)
plt.legend()
plt.tight_layout()
plt.savefig("images/simulation_samples.png")
plt.show()

###############################
# HIGH STATISTICS SIMULATIONS #
###############################
scales = np.arange(0,0.5,0.05)
#scales = np.arange(2,10,2)


trues  = []
recos  = []
drecos = []

for sc in scales:
	scale = sc
	true = scale * integral_true
	print ("Scale = {}".format(scale))


	# Do the simulation now multiple times
	ints = []; dints = []
	
	# Initial data for plot definition
	g2_sim = generate_g2()
	xplot, popt, perr = uti.fit_fixed(data=g2_sim, x=x, s=-100, e=100, mu=bunching_params[1], sigma=bunching_params[2])
	
	thex = np.arange(0,n_sim,1)
	for i in tqdm(range (0,n_sim)):
	
		g2_sim = generate_g2()
		# fit into the data, but only amplitude (because this is how we do it for the real data)
		xplot, popt, perr = uti.fit_fixed(data=g2_sim, x=x, s=-100, e=100, mu=bunching_params[1], sigma=bunching_params[2])
	
		Int, dInt = uti.integral_fixed(popt, perr, bunching_params[2])
		ints.append(1e6*Int); dints.append(1e6*dInt)
	
	# Analyze integral data
	mean = np.mean(ints)
	std  = np.std(ints)
	
	############################################
	# A COUPLE OF DIFFERENT ERROR CALCULATIONS #
	############################################
	avg_error = np.mean(dints)
	# Error calculation by assuming that baseline RMS is the uncertainty on the amplitude
	error_by_rms = 1e6*np.std(simulated_new)*bunching_params[2]*np.sqrt(2*np.pi)
	# Error calculation by error propagation in Andi's Master's thesis (eq. 2.29)
	error_prop = 1e6*np.std(simulated_new) * np.sqrt(4 * 1.6 * bunching_params[2])
	
	print ("Datapoint distribution:   {:.3f}  fs".format(std))
	print ("--------------------------------------------------")
	print ("Average fit error:        {:.3f}  fs\t({:.2f})".format(avg_error, std/avg_error))
	print ("Error by RMS baseline:    {:.3f}  fs\t({:.2f})".format(error_by_rms, std/error_by_rms))
	print ("Error by propagation:     {:.3f}  fs\t({:.2f})".format(error_prop, std/error_prop))
	
	
	print ("\n\n\n")
	print ("True coherence time:      {:.2f}          fs".format(1e6*true))
	print ("Reconstructed:            {:.2f} +/- {:.2f} fs".format(mean, std))

	#plt.figure(figsize=(10,6))
	#plt.errorbar(thex, ints, yerr=dints, marker="o", linestyle="", label="Fit results")
	#plt.fill_between(thex, y1=(mean+std), y2=(mean-std), color="red", alpha=0.2, label="datapoint distribution RMS")
	#plt.axhline(y = mean, color="red")
	#plt.axhline(y = 1e6*true, color="black", label="True coherence time")
	#plt.xlabel("Run number")
	#plt.ylabel("Coherence time (fs)")
	#plt.legend()
	#plt.show()

	trues.append(1e6*true)
	recos.append(mean)
	drecos.append(std)

plt.errorbar(x=trues, y=recos, yerr=drecos, marker="o", linestyle="")
plt.plot(trues, trues, marker="", linestyle="--", color="grey", alpha=0.5)
plt.show()