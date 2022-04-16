import globs as gl
import displays as disp
import numpy as np
from operator import add
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.interpolate import interp1d
import basics as bas

# g2 calculations
zeroadder = []
zeroadder.append("0000"); zeroadder.append("0000"); zeroadder.append("000"); zeroadder.append("00"); zeroadder.append("0"); zeroadder.append("")
def number_of_digits (x):
	if x == 0:
		return 0
	else:
		return int (np.floor(np.log10(x)+1))
def file_list_sig():
	beg = int(gl.begSigEntry.get()); end = int(gl.endSigEntry.get())
	gl.files_sig = []	
	for i in range (beg,end+1):
		gl.files_sig.append(gl.body_sig + "_" + zeroadder[number_of_digits(i)] + str(i) + ".corr")
def file_list_ref():
	beg = int(gl.begRefEntry.get()); end = int(gl.endRefEntry.get())
	gl.files_ref = []
	for i in range (beg,end+1):
		gl.files_ref.append(gl.body_ref + "_" + zeroadder[number_of_digits(i)] + str(i) + ".corr")

#---------------------------#
# Low pass and 8 bin filter #
#---------------------------#
def butter_lowpass_filter(data, binning):
	fs = 1./binning
	nyq = 0.5*fs
	cutoff = 1.e9*float(gl.cutOffEntry.get())
	order = int(gl.orderEntry.get())
	normal_cutoff = cutoff / nyq
	# Get the filter coefficients 
	b, a = butter(order, normal_cutoff, btype='low', analog=False)
	y = filtfilt(b, a, data)
	return y
def patternCorrection(data, start,end):
	startbin = int(start); endbin = int(end)
	while startbin % 8 != 0:
		startbin += 1
	while endbin % 8 != 0:
		endbin -= 1
	nsamples = (endbin-startbin)/8
	pattern = np.zeros(8)
	for i in range (startbin, endbin):
		pattern[i%8] += data[i]/nsamples
	data_corrected = []
	for i in range(0, len(data)):
		data_corrected.append(data[i]/pattern[i%8])
	return data_corrected

#------#
# FFTs #
#------#
def fft(binning):
	gl.g2_sig_fft = []; gl.g2_ref_fft = []; gl.g2_diff_fft = []
	lborder = int(gl.rmsRangeLeftEntry.get())
	rborder = int(gl.rmsRangeRightEntry.get())
	formax = 0.
	if gl.boolSig == True:
		gl.g2_sig_fft = np.fft.fft(gl.g2_sig[lborder:rborder])
		formax = max(formax + np.abs(gl.g2_sig_fft[1:]))
		x_fft = np.linspace(0,1e-9/binning, len(gl.g2_sig_fft), endpoint= True)
		#gl.g2_sig_fft_plot = gl.fftAx.plot(x_fft, np.abs(gl.g2_sig_fft), color="blue")
	if gl.boolRef == True:
		gl.g2_ref_fft = np.fft.fft(gl.g2_ref[lborder:rborder])
		formax = max(formax + np.abs(gl.g2_ref_fft[1:]))
		x_fft = np.linspace(0,1e-9/binning, len(gl.g2_ref_fft), endpoint= True)
		#gl.g2_ref_fft_plot = gl.fftAx.plot(x_fft, np.abs(gl.g2_ref_fft), color="grey")
	if gl.boolSig == True and gl.boolRef == True:
		gl.g2_diff_fft = np.fft.fft(gl.g2_diff[lborder:rborder])
		formax = max(formax + np.abs(gl.g2_diff_fft[1:]))
		x_fft = np.linspace(0,1e-9/binning, len(gl.g2_diff_fft), endpoint= True)
		#gl.g2_sig_fft_plot = gl.fftAx.plot(x_fft, np.abs(gl.g2_diff_fft), color="#003366", linewidth=2)
	gl.fftAx.set_xlim(0,0.5e-9/binning)
	gl.fftAx.set_ylim(0,formax)

#--------------#
# Photon rates #
#--------------#
def get_photon_rate_sig(fileindex, binning):
	file = open(gl.files_sig[fileindex]).read(); lines = file.split("\n")
	mean_a = float(lines[14].split(" ")[1]) - gl.offset_a_sig
	mean_b = float(lines[15].split(" ")[1]) - gl.offset_b_sig
	rate_a = mean_a/(binning*gl.avg_charge_a_sig); rate_b = mean_b/(binning*gl.avg_charge_b_sig)
	gl.rates_a_sig.append(1e-6*rate_a); gl.rates_b_sig.append(1e-6*rate_b)
	
def get_photon_rate_ref(fileindex, binning):
	file = open(gl.files_ref[fileindex]).read(); lines = file.split("\n")
	mean_a = float(lines[14].split(" ")[1]) - gl.offset_a_ref
	mean_b = float(lines[15].split(" ")[1]) - gl.offset_b_ref
	rate_a = mean_a/(binning*gl.avg_charge_a_ref); rate_b = mean_b/(binning*gl.avg_charge_b_ref)
	gl.rates_a_ref.append(1e-6*rate_a); gl.rates_b_ref.append(1e-6*rate_b)

#------------------------#
# G2 and g2 calculations #
#------------------------#
# Offset correction
def single_G2_offsetcorr_sig(fileindex, binning):
	G2 = np.loadtxt(gl.files_sig[fileindex])[:,1]
	file = open(gl.files_sig[fileindex]).read(); lines = file.split("\n")
	samples = int(lines[4].split("\t")[1])
	# Offset correction
	mean_a = float(lines[14].split(" ")[1])
	mean_b = float(lines[15].split(" ")[1])
	for j in range (0,len(G2)):
		G2[j] -= samples * (mean_a*gl.offset_b_sig + mean_b*gl.offset_a_sig - gl.offset_a_sig*gl.offset_b_sig)
	return G2
def single_G2_offsetcorr_ref(fileindex, binning):
	G2 = np.loadtxt(gl.files_ref[fileindex])[:,1]
	file = open(gl.files_ref[fileindex]).read(); lines = file.split("\n")
	samples = int(lines[4].split("\t")[1])
	# Offset correction
	mean_a = float(lines[14].split(" ")[1])
	mean_b = float(lines[15].split(" ")[1])
	for j in range (0,len(G2)):
		G2[j] -= samples * (mean_a*gl.offset_b_ref + mean_b*gl.offset_a_ref - gl.offset_a_ref*gl.offset_b_ref)
	return G2

# OLD METHOD
#def single_G2_offsetcorr_sig(fileindex, binning): # get_photon_rate_sig() needs to be calculated before
#	G2 = np.loadtxt(gl.files_sig[fileindex])[:,1]
#	file = open(gl.files_sig[fileindex]).read(); lines = file.split("\n")
#	samples = int(lines[4].split("\t")[1])
#	T = binning * samples
#	# Offset correction
#	rate_a = gl.rates_a_sig[fileindex]; rate_b = gl. rates_b_sig[fileindex]
#	ya_x_bb = rate_a*gl.avg_charge_a_sig * T * gl.offset_b_sig
#	yb_x_ba = rate_b*gl.avg_charge_b_sig * T * gl.offset_a_sig
#	ba_x_bb = gl.offset_a_sig * gl.offset_b_sig * T/(binning)
#	for j in range (0,len(G2)):
#		G2[j] -= ya_x_bb + yb_x_ba + ba_x_bb
#	return G2
#def single_G2_offsetcorr_ref(fileindex, binning): # get_photon_rate_ref() needs to be calculated before
#	G2 = np.loadtxt(gl.files_ref[fileindex])[:,1]
#	file = open(gl.files_ref[fileindex]).read(); lines = file.split("\n")
#	samples = int(lines[4].split("\t")[1])
#	T = binning * samples
#	# Offset correction
#	rate_a = gl.rates_a_ref[fileindex]; rate_b = gl. rates_b_ref[fileindex]
#	ya_x_bb = rate_a*gl.avg_charge_a_ref * T * gl.offset_b_ref
#	yb_x_ba = rate_b*gl.avg_charge_b_ref * T * gl.offset_a_ref
#	ba_x_bb = gl.offset_a_ref * gl.offset_b_ref * T/(binning)
#	for j in range (0,len(G2)):
#		G2[j] -= ya_x_bb + yb_x_ba + ba_x_bb
#	return G2

def cumulative_G2_offsetcorr_sig(fileindex, binning):
	gl.G2_cum_sig = list(map(add, gl.G2_cum_sig, single_G2_offsetcorr_sig(fileindex,binning)))
def cumulative_G2_offsetcorr_ref(fileindex, binning):
	gl.G2_cum_ref = list(map(add, gl.G2_cum_ref, single_G2_offsetcorr_ref(fileindex,binning)))
# g2 ----------------------------------------#
def get_cumulative_g2_sig(lowpass, binning):
	range_left = int(gl.rmsRangeLeftEntry.get()); range_right = int(gl.rmsRangeRightEntry.get())
	#corr_factor = float(gl.corrSigEntry.get())
	avg = np.mean(gl.G2_cum_sig[range_left:range_right])
	g2 = []
	for j in range (0, len(gl.G2_cum_sig)):
		g2.append(gl.G2_cum_sig[j]/avg)
	if gl.boolPatCorr == True:
		g2 = patternCorrection(g2, range_left, range_right)
	if lowpass == True:
		g2 = butter_lowpass_filter(g2, binning)
	return g2
def get_cumulative_g2_ref(lowpass, binning):
	range_left = int(gl.rmsRangeLeftEntry.get()); range_right = int(gl.rmsRangeRightEntry.get())
	#corr_factor = float(gl.corrRefEntry.get())
	avg = np.mean(gl.G2_cum_ref[range_left:range_right])
	g2 = []
	for j in range (0, len(gl.G2_cum_ref)):
		g2.append(gl.G2_cum_ref[j]/avg)
	if gl.boolPatCorr == True:
		g2 = patternCorrection(g2, range_left, range_right)
	if lowpass == True:
		g2 = butter_lowpass_filter(g2, binning)
	return g2
def get_cumulative_g2_diff(binning):
	g2_sig = get_cumulative_g2_sig(lowpass = False, binning=binning)
	g2_ref = get_cumulative_g2_ref(lowpass = False, binning=binning)
	g2_diff = []
	for j in range (0,len(g2_sig)):
		g2_diff.append(g2_sig[j]-g2_ref[j] + 1.)
	if gl.boolLP == True:
		g2_diff = butter_lowpass_filter(g2_diff, binning)
	return g2_diff
def get_cumulative_g2_diff_per_file():
	g2_sig = get_g2_per_file_sig()
	g2_ref = get_g2_per_file_ref()
	g2_diff = []
	for j in range (0,len(g2_sig)):
		g2_diff.append(g2_sig[j]-g2_ref[j] + 1.)
	return g2_diff

# ----------------------- #
# g2 per File calculation #
# ------------------------#
def cumulative_g2_per_file_sig(fileindex): # First do single_RMS_sig
	theRMS = gl.rmssin_sig[fileindex]
	gl.n_N_sig += 1./theRMS**2
	for j in range (0,len(gl.isum_sig)):
		gl.isum_sig[j] += gl.g2_current[j]/theRMS**2
def cumulative_g2_per_file_ref(fileindex): # First do single_RMS_ref
	theRMS = gl.rmssin_ref[fileindex]
	gl.n_N_ref += 1./theRMS**2
	for j in range (0,len(gl.isum_ref)):
		gl.isum_ref[j] += gl.g2_current[j]/theRMS**2
def get_g2_per_file_sig():
	g2 = []; n = 1./gl.n_N_sig
	for j in range (0,len(gl.isum_sig)):
		g2.append(n * gl.isum_sig[j])
	return g2
def get_g2_per_file_ref():
	g2 = []; n = 1./gl.n_N_ref
	for j in range (0,len(gl.isum_ref)):
		g2.append(n * gl.isum_ref[j])
	return g2

# --------------- #
# RMS calculation #
# ----------------#
def single_RMS_sig(fileindex, binning):
	G2 = single_G2_offsetcorr_sig(fileindex, binning)
	range_left = int(gl.rmsRangeLeftEntry.get()); range_right = int(gl.rmsRangeRightEntry.get())
	avg = np.mean(G2[range_left:range_right])
	g2 = []
	for j in range (0, len(G2)):
		g2.append(G2[j]/avg)
	if gl.boolPatCorr == True:
		g2 = patternCorrection(g2, range_left, range_right)
	if gl.boolLP == True:
		g2 = butter_lowpass_filter(g2, binning)
	gl.rmssin_sig.append(np.std(g2[range_left:range_right]))
	gl.ffts_sig.append(np.abs(np.fft.fft([x-1 for x in g2][range_left:range_right])))
	gl.g2_current = g2 # for per-file calculation
def single_RMS_ref(fileindex, binning):
	G2 = single_G2_offsetcorr_ref(fileindex, binning)
	range_left = int(gl.rmsRangeLeftEntry.get()); range_right = int(gl.rmsRangeRightEntry.get())
	#corr_factor = float(gl.corrRefEntry.get())
	avg = np.mean(G2[range_left:range_right])
	g2 = []
	for j in range (0, len(G2)):
		g2.append(G2[j]/avg)
	if gl.boolPatCorr == True:
		g2 = patternCorrection(g2, range_left, range_right)
	if gl.boolLP == True:
		g2 = butter_lowpass_filter(g2, binning)
	gl.rmssin_ref.append(np.std(g2[range_left:range_right]))
	gl.g2_current = g2 # for per-file calculation
def cumulative_RMS_sig(binning, method):
	if method == 0: # Conventional calculation
		g2 = get_cumulative_g2_sig(lowpass = gl.boolLP, binning=binning)
	elif method == 1: # per-file calculation
		g2 = get_g2_per_file_sig()
	range_left = int(gl.rmsRangeLeftEntry.get()); range_right = int(gl.rmsRangeRightEntry.get())
	gl.rmscum_sig.append(np.std(g2[range_left:range_right]))
	# Error on RMS is calculated via several ranges of 25 bins
	rmss = []
	i_starts = np.arange(range_left, range_right, 25)
	for i in i_starts:
		rmss.append(np.std(g2[i:i+25]))
	gl.rmscum_sig_err.append(np.std(rmss))
def cumulative_RMS_ref(binning, method):
	if method == 0: # Conventional calculation
		g2 = get_cumulative_g2_ref(lowpass = gl.boolLP, binning=binning)
	elif method == 1: # per-file calculation:
		g2 = get_g2_per_file_ref()
	range_left = int(gl.rmsRangeLeftEntry.get()); range_right = int(gl.rmsRangeRightEntry.get())
	gl.rmscum_ref.append(np.std(g2[range_left:range_right]))
	# Error on RMS is calculated via several ranges of 25 bins
	rmss = []
	i_starts = np.arange(range_left, range_right, 25)
	for i in i_starts:
		rmss.append(np.std(g2[i:i+25]))
	gl.rmscum_ref_err.append(np.std(rmss))
def cumulative_RMS_diff(binning, method):
	if method == 0: # Conventional calculation
		g2 = get_cumulative_g2_diff(binning=binning)
	elif method == 1: # per-file calculation
		g2 = get_cumulative_g2_diff_per_file()
	range_left = int(gl.rmsRangeLeftEntry.get()); range_right = int(gl.rmsRangeRightEntry.get())
	gl.rmscum_diff.append(np.std(g2[range_left:range_right]))
# Expectations
def single_RMS_sig_exp(fileindex, binning):
	corr_factor = float(gl.corrSigEntry.get())
	file = open(gl.files_sig[fileindex]).read(); lines = file.split("\n")
	samples = int(lines[4].split("\t")[1]); T = binning * samples
	rate_a = gl.rates_a_sig[fileindex]; rate_b = gl. rates_b_sig[fileindex]
	rms = corr_factor *  1./np.sqrt(rate_a*rate_b*1e12*binning*T)
	gl.rmssin_sig_exp.append(rms)
	gl.rmssin_sig_frac.append(gl.rmssin_sig[fileindex]/rms)
def single_RMS_ref_exp(fileindex, binning):
	corr_factor = float(gl.corrRefEntry.get())
	file = open(gl.files_ref[fileindex]).read(); lines = file.split("\n")
	samples = int(lines[4].split("\t")[1]); T = binning * samples
	rate_a = gl.rates_a_ref[fileindex]; rate_b = gl. rates_b_ref[fileindex]
	rms = corr_factor * 1./np.sqrt(rate_a*rate_b*1e12*binning*T)
	gl.rmssin_ref_exp.append(rms)
	gl.rmssin_ref_frac.append(gl.rmssin_ref[fileindex]/rms)
def cumulative_RMS_sig_exp(fileindex, binning):
	corr_factor = float(gl.corrSigEntry.get())
	file = open(gl.files_sig[fileindex]).read(); lines = file.split("\n")
	samples = int(lines[4].split("\t")[1]); T = binning * samples
	rate_a = gl.rates_a_sig[fileindex]; rate_b = gl. rates_b_sig[fileindex]
	gl.N_e_sig += rate_a*rate_b*1e12*binning*T; rms = corr_factor * 1./np.sqrt(gl.N_e_sig)
	gl.rmscum_sig_exp.append(rms)
	gl.rmscum_sig_frac.append(gl.rmscum_sig[fileindex]/rms)
def cumulative_RMS_ref_exp(fileindex, binning):
	corr_factor = float(gl.corrRefEntry.get())
	file = open(gl.files_ref[fileindex]).read(); lines = file.split("\n")
	samples = int(lines[4].split("\t")[1]); T = binning * samples
	rate_a = gl.rates_a_ref[fileindex]; rate_b = gl. rates_b_ref[fileindex]
	gl.N_e_ref += rate_a*rate_b*1e12*binning*T; rms = corr_factor * 1./np.sqrt(gl.N_e_ref)
	gl.rmscum_ref_exp.append(rms)
	gl.rmscum_ref_frac.append(gl.rmscum_ref[fileindex]/rms)
def cumulative_RMS_diff_exp(fileindex):
	try:
		rms_sig = gl.rmscum_sig_exp[fileindex]
		rms_ref = gl.rmscum_ref_exp[fileindex]
		rms = np.sqrt(rms_sig**2 + rms_ref**2)
		gl.rmscum_diff_exp.append(rms)
		gl.rmscum_diff_frac.append(gl.rmscum_diff[fileindex]/rms)
	except:
		pass

#--------------------#
# Cumulative analyis #
#--------------------#
def cumulate_signal(binning):
	bas.reset_values()

	if gl.boolSig == True:
		print ("Analyze Signal ...")
		file_list_sig()
		gl.G2_cum_sig = np.zeros(len(np.loadtxt(gl.files_sig[0])[:,1]))
		for i in range (0,len(gl.files_sig)):
			get_photon_rate_sig(i, binning)
			single_RMS_sig(i, binning); single_RMS_sig_exp(i, binning)
			cumulative_G2_offsetcorr_sig(i, binning)
			cumulative_RMS_sig(binning, method=0); cumulative_RMS_sig_exp(i, binning)
		gl.g2_sig = get_cumulative_g2_sig(lowpass=gl.boolLP, binning=binning)
		bas.correlate_shapes()

	if gl.boolRef == True:
		print ("Analyze Reference ...")
		file_list_ref()
		gl.G2_cum_ref = np.zeros(len(np.loadtxt(gl.files_ref[0])[:,1]))
		for i in range (0,len(gl.files_ref)):
			get_photon_rate_ref(i, binning)
			single_RMS_ref(i, binning); single_RMS_ref_exp(i, binning)
			cumulative_G2_offsetcorr_ref(i, binning)
			cumulative_RMS_ref(binning, method=0); cumulative_RMS_ref_exp(i, binning)
			if gl.boolSig == True:
				cumulative_RMS_diff(binning, method=0); cumulative_RMS_diff_exp(i)
		gl.g2_ref = get_cumulative_g2_ref(lowpass=gl.boolLP, binning=binning)
		if gl.boolSig == True:
			gl.g2_diff = get_cumulative_g2_diff(binning)

	fft(binning)
	disp.refresh_display(binning)
	print ("Done\n")

def cumulate_signal_per_file(binning):
	bas.reset_values()

	if gl.boolSig == True:
		print ("Analyze Signal ...")
		file_list_sig()
		gl.isum_sig = np.zeros(len(np.loadtxt(gl.files_sig[0])[:,1]))
		for i in range (0,len(gl.files_sig)):
			get_photon_rate_sig(i, binning)
			single_RMS_sig(i, binning); single_RMS_sig_exp(i, binning)
			cumulative_g2_per_file_sig(i)
			cumulative_RMS_sig(binning, method=1); cumulative_RMS_sig_exp(i, binning)
		gl.g2_sig = get_g2_per_file_sig()
		bas.correlate_shapes()

	if gl.boolRef == True:
		print ("Analyze Reference ...")
		file_list_ref()
		gl.isum_ref = np.zeros(len(np.loadtxt(gl.files_ref[0])[:,1]))
		for i in range (0,len(gl.files_ref)):
			get_photon_rate_ref(i, binning)
			single_RMS_ref(i, binning); single_RMS_ref_exp(i, binning)
			cumulative_g2_per_file_ref(i)
			cumulative_RMS_ref(binning, method=1); cumulative_RMS_ref_exp(i, binning)
			if gl.boolSig == True:
				cumulative_RMS_diff(binning, method=1); cumulative_RMS_diff_exp(i)
		gl.g2_ref = get_g2_per_file_ref()
		if gl.boolSig == True:
			gl.g2_diff = get_cumulative_g2_diff_per_file()

	fft(binning)
	disp.refresh_display(binning)
	print ("Done\n")

#--------------------------------#
# Experimental correction factor #
#--------------------------------#
def experimental_correction_factors():
	if gl.boolSig == True:
		corr_frac_old = float(gl.corrSigEntry.get())
		#print ("corr frac old:\t{}".format(corr_frac_old))
		avg = np.mean(gl.rmssin_sig_frac)
		#print ("avg RMS:\t{}".format(avg))
		corr_frac_new = avg/corr_frac_old
		#print ("New = {:.3f}/{:.3f} = {:.3f}".format(avg,corr_frac_old,corr_frac_new))
		gl.corrSigEntry.delete(0,"end"); gl.corrSigEntry.insert(0,"{}".format(corr_frac_new))
	if gl.boolRef == True:
		corr_frac_old = float(gl.corrRefEntry.get())
		avg = np.mean(gl.rmssin_ref_frac)
		corr_frac_new = avg/corr_frac_old
		gl.corrRefEntry.delete(0,"end"); gl.corrRefEntry.insert(0,"{}".format(corr_frac_new))

#----------------#
# Signal fitting #
#----------------#
# Gauss fit
def gauss(x,a,m,s,d):
	return a * np.exp(-(x-m)**2/2/s/s) + d
def get_integral(fitpar, e_fitpar, binning):# now in femtoseconds
	amp = fitpar[0]; d_amp = e_fitpar[0]
	sig = 1e9*binning * np.abs(fitpar[2]); d_sig = 1e9*binning * e_fitpar[2]

	I = 1e6 * amp * sig * np.sqrt(2*np.pi)
	dI = 1e6 * np.sqrt(2*np.pi) * np.sqrt((amp*d_sig)**2 + (sig*d_amp)**2)
	return I, dI
# Peak shape fit
sum_peak = []; the_peak_fu = []
def make_peak_fu():
	global sum_peak, the_peak_fu
	the_peak_fu = interp1d(gl.peakshape_x, gl.peakshape_y)
	sum_peak = np.sum(gl.peakshape_y)
def peak_fu(x,I,b,d):
	global the_peak_fu
	return I/sum_peak * the_peak_fu(x-b) + d

def fit_signal_gauss(binning):
	xlim = gl.corrAx.get_xlim(); ylim = gl.corrAx.get_ylim()
	disp.refresh_display(binning)
	if gl.boolSig == True:
		lborder = int(gl.fitRangeLeftEntry.get())
		rborder = int(gl.fitRangeRightEntry.get())
		sig_start = 2.
		x_fit = np.arange(lborder,rborder+1,1)
		y_fit = gl.g2_sig[lborder:rborder+1]
		med_start = np.argmax(y_fit)+lborder
		amp_start = np.argmax(y_fit)-1.
		popt, pcov = curve_fit(gauss, x_fit, y_fit, p0=[amp_start,med_start,sig_start,1.]);	perr = np.sqrt(np.diag(pcov))
		gl.x_plot = np.arange(lborder,rborder+1,0.01)
		try:
			gl.corrAx.gl.fit_plot.remove()
		except:
			pass
		gl.fit_plot = gl.corrAx.plot(gl.x_plot, gauss(gl.x_plot, *popt), color="red")
		gl.corrAx.set_xlim(xlim); gl.corrAx.set_ylim(ylim)
		I, dI = get_integral(popt, perr, binning)
		gl.intValLabel.config(text="{:.1f} +/- {:.1f} fs".format(I,dI))
		#gl.timeResValLabel.config(text="{:.2f} +/- {:.2f} ns".format(1e9*binning*popt[2], binning*perr[2]))
 
	else:
		print ("No Signal measurement available")
def fit_difference_gauss(binning):
	xlim = gl.corrAx.get_xlim(); ylim = gl.corrAx.get_ylim()
	disp.refresh_display(binning)
	if gl.boolSig == True and gl.boolRef == True:
		lborder = int(gl.fitRangeLeftEntry.get())
		rborder = int(gl.fitRangeRightEntry.get())
		sig_start = 2.
		x_fit = np.arange(lborder,rborder+1,1)
		y_fit = gl.g2_diff[lborder:rborder+1]
		med_start = np.argmax(y_fit)+lborder
		amp_start = np.argmax(y_fit)-1.
		popt, pcov = curve_fit(gauss, x_fit, y_fit, p0=[amp_start,med_start,sig_start,1.]);	perr = np.sqrt(np.diag(pcov))
		gl.x_plot = np.arange(lborder,rborder+1,0.01)
		try:
			gl.corrAx.gl.fit_plot.remove()
		except:
			pass
		gl.fit_plot = gl.corrAx.plot(gl.x_plot, gauss(gl.x_plot, *popt), color="orange")
		gl.corrAx.set_xlim(xlim); gl.corrAx.set_ylim(ylim)
		I, dI = get_integral(popt, perr, binning)
		gl.intValLabel.config(text="{:.1f} +/- {:.1f} fs".format(I,dI))
		#gl.timeResValLabel.config(text="{:.2f} +/- {:.2f} ns".format(1e9*binning*popt[2], 1e9*binning*perr[2]))

	else:
		print ("No Difference measurement available")
def fit_signal_shape(binning):
	make_peak_fu()
	xlim = gl.corrAx.get_xlim(); ylim = gl.corrAx.get_ylim()
	disp.refresh_display(binning)
	if gl.boolSig == True:
		lborder = int(gl.fitRangeLeftEntry.get())
		rborder = int(gl.fitRangeRightEntry.get())
		sig_start = 2.
		x_fit = np.arange(lborder,rborder+1,1)
		y_fit = gl.g2_sig[lborder:rborder+1]
		med_start = np.argmax(y_fit)+lborder
		amp_start = np.argmax(y_fit)-1.
		popt, pcov = curve_fit(peak_fu, x_fit, y_fit, p0=[amp_start,med_start,1.]); perr = np.sqrt(np.diag(pcov))
		gl.x_plot = np.arange(lborder,rborder+1,0.01)
		try:
			gl.corrAx.gl.fit_plot.remove()
		except:
			pass
		gl.fit_plot = gl.corrAx.plot(gl.x_plot, peak_fu(gl.x_plot, *popt), color="red")
		gl.corrAx.set_xlim(xlim); gl.corrAx.set_ylim(ylim)
		I = 1e6*1e9*binning * popt[0]; dI =  1e6*1e9 * binning * perr[0]
		gl.intValLabel.config(text="{:.1f} +/- {:.1f} fs".format(I,dI))
		#gl.timeResValLabel.config(text="{:.2f} +/- {:.2f} ns".format(1e9*binning*popt[2], binning*perr[2]))
 
	else:
		print ("No Signal measurement available")
def fit_difference_shape(binning):
	make_peak_fu()
	xlim = gl.corrAx.get_xlim(); ylim = gl.corrAx.get_ylim()
	disp.refresh_display(binning)
	if gl.boolSig == True and gl.boolRef == True:
		lborder = int(gl.fitRangeLeftEntry.get())
		rborder = int(gl.fitRangeRightEntry.get())
		sig_start = 2.
		x_fit = np.arange(lborder,rborder+1,1)
		y_fit = gl.g2_diff[lborder:rborder+1]
		med_start = np.argmax(y_fit)+lborder
		amp_start = np.argmax(y_fit)-1.
		popt, pcov = curve_fit(peak_fu, x_fit, y_fit, p0=[amp_start,med_start,1.]); perr = np.sqrt(np.diag(pcov))
		gl.x_plot = np.arange(lborder,rborder+1,0.01)
		try:
			gl.corrAx.gl.fit_plot.remove()
		except:
			pass
		gl.fit_plot = gl.corrAx.plot(gl.x_plot, peak_fu(gl.x_plot, *popt), color="orange")
		gl.corrAx.set_xlim(xlim); gl.corrAx.set_ylim(ylim)
		I = 1e6*1e9*binning * popt[0]; dI =  1e6*1e9 * binning * perr[0]
		gl.intValLabel.config(text="{:.1f} +/- {:.1f} fs".format(I,dI))
		#gl.timeResValLabel.config(text="{:.2f} +/- {:.2f} ns".format(1e9*binning*popt[2], 1e9*binning*perr[2]))

	else:
		print ("No Difference measurement available")

