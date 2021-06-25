import globs as gl
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

def gauss(x,a,m,s):
	return a * np.exp(-(x-m)**2/2/s/s)
def displayCalib():
	plt.figure("Calibration display", figsize=(13,7))
	if gl.boolSig == True and gl.boolRef == True:
		axphdSig = plt.subplot(221); axpsSig = plt.subplot(222)
		axphdRef = plt.subplot(223); axpsRef = plt.subplot(224)
	elif gl.boolSig == True:
		axphdSig = plt.subplot(121); axpsSig = plt.subplot(122)
	elif gl.boolRef == True:
		axphdRef = plt.subplot(121); axpsRef = plt.subplot(122)

	if gl.boolSig == True:
		axphdSig.plot(gl.histo_x_sig, gl.histo_a_sig, color="blue", label="Channel A: Avg height = {:.2f}".format(gl.ph_a_sig), alpha=0.5)
		axphdSig.plot(gl.histo_x_sig, gl.histo_b_sig, color="red", label="Channel B: Avg height = {:.2f}".format(gl.ph_b_sig), alpha=0.5)
		axphdSig.plot(gl.xplot_sig, gauss(gl.xplot_sig, *gl.pa_sig), color="blue"); axphdSig.plot(gl.xplot_sig, gauss(gl.xplot_sig, *gl.pb_sig), color="red")
		axphdSig.axvline(x=gl.ph_a_sig, color="blue", linestyle="--"); axphdSig.axvline(x=gl.ph_b_sig, color="red", linestyle="--")
		axphdSig.set_ylim(0,1.5*max(gl.pa_sig[0],gl.pb_sig[0])); axphdSig.set_xlim(-128,10); axphdSig.legend(); axphdSig.set_title("Signal Pulse heights")
		
		axpsSig.plot(gl.ps_x_sig,gl.ps_a_sig, color="blue", label="Channel A: Sum = {:.2f}".format(gl.nsum_a_sig)); axpsSig.plot(gl.ps_x_sig,gl.ps_b_sig, color="red", label="Channel B: Sum = {:.2f}".format(gl.nsum_b_sig))
		axpsSig.plot(gl.peakshape_x, gl.peakshape_y, color="black", label="Correlation Peak Shape")
		axpsSig.set_title("Signal Peak shapes"); axpsSig.legend(); axpsSig.set_xlim(-50,100)

	if gl.boolRef == True:
		axphdRef.plot(gl.histo_x_ref, gl.histo_a_ref, color="blue", label="Channel A: Avg height = {:.2f}".format(gl.ph_a_ref), alpha=0.5)
		axphdRef.plot(gl.histo_x_ref, gl.histo_b_ref, color="red", label="Channel B: Avg height = {:.2f}".format(gl.ph_b_ref), alpha=0.5)
		axphdRef.plot(gl.xplot_ref, gauss(gl.xplot_ref, *gl.pa_ref), color="blue"); axphdRef.plot(gl.xplot_ref, gauss(gl.xplot_ref, *gl.pb_ref), color="red")
		axphdRef.axvline(x=gl.ph_a_ref, color="blue", linestyle="--"); axphdRef.axvline(x=gl.ph_b_ref, color="red", linestyle="--")
		axphdRef.set_ylim(0,1.5*max(gl.pa_ref[0],gl.pb_ref[0])); axphdRef.set_xlim(-128,10); axphdRef.legend(); axphdRef.set_title("Reference Pulse heights")
		
		axpsRef.plot(gl.ps_x_ref,gl.ps_a_ref, color="blue", label="Channel A: Sum = {:.2f}".format(gl.nsum_a_ref)); axpsRef.plot(gl.ps_x_ref,gl.ps_b_ref, color="red", label="Channel B: Sum = {:.2f}".format(gl.nsum_b_ref))
		axpsRef.set_title("Reference Peak shapes"); axpsRef.legend(); axpsRef.set_xlim(-50,100)
	plt.show()

def displayCorrelation():
	plt.figure("Correlations", figsize=(10,7))
	plt.ticklabel_format(useOffset=False)
	plt.xlabel("Time bins"); plt.ylabel("$g^{(2)}$")
	if gl.boolSig == True:
		plt.plot(gl.g2_sig, color="blue", label="Signal")
	if gl.boolRef == True:
		plt.plot(gl.g2_ref, color="grey", label="Reference")
	if gl.boolSig == True and gl.boolRef == True:
		plt.plot(gl.g2_diff, color="#003366", linewidth = 2, label="Difference")
	#try:
	#	gl.fit_plot = plt.plot(gl.fit_plot)
	#except:
	#	pass
	plt.legend(); plt.show()
def displayFFT():
	plt.figure("Fourier Transforms", figsize=(10,7))
	if gl.boolSig == True:
		plt.plot(np.abs(gl.g2_sig_fft), color="blue", label="Signal")
	if gl.boolRef == True:
		plt.plot(np.abs(gl.g2_ref_fft), color="grey", label="Reference")
	if gl.boolSig == True and gl.boolRef == True:
		plt.plot(np.abs(gl.g2_diff_fft), color="#003366", linewidth = 2, label="Difference")
	plt.legend(); plt.show()
def displayRates():
	plt.figure("Photon rates", figsize=(10,7)); plt.ylabel("Photon rates [MHz]")
	if gl.boolSig == True:
		plt.plot(gl.rates_a_sig, color="blue", label="Signal CH A")
		plt.plot(gl.rates_b_sig, color="red", label="Signal CH B")
	if gl.boolRef == True:
		plt.plot(gl.rates_a_ref, color="blue", alpha=0.3, label="Reference CH A")
		plt.plot(gl.rates_b_ref, color="red", alpha = 0.3, label="Reference CH B")
	plt.legend(); plt.show()
def displaySingleRMS():
	plt.figure("Single RMS", figsize=(10,7))
	plt.subplot(211); plt.xlabel("File index"); plt.ylabel("RMS")
	plt.subplot(212); plt.xlabel("File index"); plt.ylabel("RMS fraction")
	if gl.boolSig == True:
		plt.subplot(211)
		plt.plot(gl.rmssin_sig, color="blue", label="Signal", alpha=0.5, zorder=1)
		plt.plot(gl.rmssin_sig_exp, color="blue", linestyle="--", zorder=2)
		plt.subplot(212)
		plt.plot(gl.rmssin_sig_frac, color="blue")
	if gl.boolRef == True:
		plt.subplot(211)
		plt.plot(gl.rmssin_ref, color="grey", label="Reference", alpha=0.5, zorder=1)
		plt.plot(gl.rmssin_ref_exp, color="black", linestyle="--", zorder=2)
		plt.subplot(212)
		plt.plot(gl.rmssin_ref_frac, color="grey")
	plt.subplot(211); plt.legend(); plt.show()
def displayCumulativeRMS():
	plt.figure("Cumulative RMS", figsize=(10,7))
	plt.subplot(211); plt.xlabel("File index"); plt.ylabel("RMS")
	plt.subplot(212); plt.xlabel("File index"); plt.ylabel("RMS fraction")
	plt.axhline(y=1.0, color="grey", linestyle="--")
	if gl.boolSig == True:
		plt.subplot(211)
		plt.fill_between(x=np.arange(0,len(gl.rmscum_sig)), y1=np.array(gl.rmscum_sig)+np.array(gl.rmscum_sig_err), y2=np.array(gl.rmscum_sig)-np.array(gl.rmscum_sig_err), color="blue", alpha=0.1)
		plt.plot(gl.rmscum_sig, color="blue", label="Signal", alpha=0.5, zorder=1)
		plt.plot(gl.rmscum_sig_exp, color="blue", linestyle="--", zorder=2)
		plt.subplot(212)
		plt.plot(gl.rmscum_sig_frac, color="blue")
	if gl.boolRef == True:
		plt.subplot(211)
		plt.plot(gl.rmscum_ref, color="grey", label="Reference", alpha=0.5, zorder=1)
		plt.plot(gl.rmscum_ref_exp, color="black", linestyle="--", zorder=2)
		plt.subplot(212)
		plt.plot(gl.rmscum_ref_frac, color="grey")
		if gl.boolSig == True:
			plt.subplot(211)
			plt.plot(gl.rmscum_diff, color="#003366", linewidth=2, label="Difference")
			plt.plot(gl.rmscum_diff_exp, color="#003366", linestyle="--", zorder=2)
			plt.subplot(212)
			plt.plot(gl.rmscum_diff_frac, color="#003366", zorder=2)
	plt.subplot(211); plt.legend()
	if gl.boolRMSlogx == True:
		plt.xscale("log")
		plt.xlim(1,)
	if gl.boolRMSlogy == True:
		plt.yscale("log")
	plt.show()

def refresh_display(binning):
	gl.corrAx.cla(); gl.corrAx.set_title("Correlations"); gl.corrAx.set_xlabel("Time bins"); gl.corrAx.set_ylabel("$g^{(2)}$"); gl.corrAx.ticklabel_format(useOffset=False); gl.corrAx.grid(alpha=0.3)
	gl.fftAx.cla(); gl.fftAx.set_xlabel("Frequency [GHz]")
	gl.rmssinAx.cla(); gl.rmssinAx.set_ylabel("Single files RMS")
	gl.ratesAx.cla(); gl.ratesAx.set_ylabel("Rates [MHz]"); gl.ratesAx.set_title("Photon rates")
	gl.rmscumAx.cla(); gl.rmscumAx.set_ylabel("Cumulative RMS")
	if gl.boolRMSlogx == True:
		gl.rmscumAx.set_xscale("log")
		gl.rmscumAx.set_xlim(1,)
	if gl.boolRMSlogy == True:
		gl.rmscumAx.set_yscale("log")

	formax = 0.
	if gl.boolSig == True:
		# g2
		gl.g2_sig_plot = gl.corrAx.plot(gl.g2_sig, color="blue")
		# FFT
		formax = max(formax + np.abs(gl.g2_sig_fft[1:]))
		x_fft = np.linspace(0,1e-9/binning, len(gl.g2_sig_fft), endpoint= True)
		gl.g2_sig_fft_plot = gl.fftAx.plot(x_fft, np.abs(gl.g2_sig_fft), color="blue")
		# Rates
		gl.rates_a_sig_plot = gl.ratesAx.plot(gl.rates_a_sig, color="blue")
		gl.rates_b_sig_plot = gl.ratesAx.plot(gl.rates_b_sig, color="red")
		# RMS
		gl.rmssin_sig_plot = gl.rmssinAx.plot(gl.rmssin_sig, color="blue", alpha=0.5, zorder=1)
		gl.rmssin_sig_exp_plot = gl.rmssinAx.plot(gl.rmssin_sig_exp, color="blue", linestyle="--", zorder=2)

		gl.rmscum_sig_err_plot = gl.rmscumAx.fill_between(x=np.arange(0,len(gl.rmscum_sig)), y1=np.array(gl.rmscum_sig)+np.array(gl.rmscum_sig_err), y2=np.array(gl.rmscum_sig)-np.array(gl.rmscum_sig_err), color="blue", alpha=0.1)
		gl.rmscum_sig_plot = gl.rmscumAx.plot(gl.rmscum_sig, color="blue", alpha=0.5, zorder=1)		
		gl.rmscum_sig_exp_plot = gl.rmscumAx.plot(gl.rmscum_sig_exp, color="blue", linestyle="--", zorder=2)


	if gl.boolRef == True:
		# g2
		gl.g2_ref_plot = gl.corrAx.plot(gl.g2_ref, color="grey")
		# FFT
		formax = max(formax + np.abs(gl.g2_ref_fft[1:]))
		x_fft = np.linspace(0,1e-9/binning, len(gl.g2_ref_fft), endpoint= True)
		gl.g2_ref_fft_plot = gl.fftAx.plot(x_fft, np.abs(gl.g2_ref_fft), color="grey")
		# Rates
		gl.rates_a_ref_plot = gl.ratesAx.plot(gl.rates_a_ref, color="blue", alpha=0.3)
		gl.rates_b_ref_plot = gl.ratesAx.plot(gl.rates_b_ref, color="red", alpha = 0.3)
		# RMS
		gl.rmssin_ref_plot = gl.rmssinAx.plot(gl.rmssin_ref, color="grey", alpha=0.5, zorder=1)
		gl.rmscum_ref_plot = gl.rmscumAx.plot(gl.rmscum_ref, color="grey", alpha=0.5, zorder=1)
		gl.rmssin_ref_exp_plot = gl.rmssinAx.plot(gl.rmssin_ref_exp, color="black", linestyle="--", zorder=2)
		
		gl.rmscum_sig_err_plot = gl.rmscumAx.fill_between(x=np.arange(0,len(gl.rmscum_ref)), y1=np.array(gl.rmscum_ref)+np.array(gl.rmscum_ref_err), y2=np.array(gl.rmscum_ref)-np.array(gl.rmscum_ref_err), color="grey", alpha=0.1)
		gl.rmscum_ref_exp_plot = gl.rmscumAx.plot(gl.rmscum_ref_exp, color="grey", linestyle="--", zorder=2)
		if gl.boolSig == True:
			gl.rmscum_diff_plot = gl.rmscumAx.plot(gl.rmscum_diff, color="#003366", alpha=0.5, linewidth=2)
			gl.rmscum_diff_exp_plot = gl.rmscumAx.plot(gl.rmscum_diff_exp, color="#003366", linestyle="--")
			# g2
			gl.g2_diff_plot = gl.corrAx.plot(gl.g2_diff, color="#003366", linewidth=2)
			# FFT
			formax = max(formax + np.abs(gl.g2_diff_fft[1:]))
			x_fft = np.linspace(0,1e-9/binning, len(gl.g2_diff_fft), endpoint= True)
			gl.g2_sig_fft_plot = gl.fftAx.plot(x_fft, np.abs(gl.g2_diff_fft), color="#003366", linewidth=2)

	if gl.boolSig == True:
		gl.ffts_sig_plot = gl.fftAx.imshow(gl.ffts_sig, aspect="auto", extent=[0,1e-9/binning,0,formax], cmap=cm.binary, vmin=np.min(gl.ffts_sig), vmax=np.max(gl.ffts_sig))

	gl.fftAx.set_xlim(0,0.5e-9/binning)
	gl.fftAx.set_ylim(0,formax)


	gl.corrCanvas.draw()