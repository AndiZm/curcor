import numpy as np
import globs as gl

# Signal peak shape is a correlation of the single channel pulse shapes in the waveforms
def scalarproduct(a,b):
	return np.sum(a*b)
def corr(a,b,shifts):
	res = np.zeros(shifts+1)
	for i in range (shifts+1):
		res[i] = scalarproduct(a[:len(a)-shifts],b[i:len(b)-shifts+i])
	return res
def correlate_shapes():
	shape_a = gl.ps_a_sig
	shape_b = gl.ps_b_sig
	length = len(gl.ps_x_sig)

	wv_a = np.zeros(length*4)
	wv_b = np.zeros(length*4)
	for i in range (length,2*length):
		wv_a[i] = shape_a[i-length]
		wv_b[i+length] = shape_b[i-length]

	# Actual correlation
	gl.peakshape_y = corr(wv_a,wv_b, 2*length)
	# Move peak zo zero position and rescale it to height 1
	maxx = np.argmax(gl.peakshape_y); maxy = np.max(gl.peakshape_y)
	gl.peakshape_x = np.arange(-maxx,len(gl.peakshape_y)-maxx,1)
	for i in range (0,len(gl.peakshape_x)):
		gl.peakshape_y[i] /= maxy#

def reset_values():
	gl.rates_a_sig = []; gl.rates_b_sig = []; gl.rates_a_ref = []; gl.rates_b_ref = []
	gl.rmssin_sig = []; gl.rmssin_ref = []; gl.rmscum_sig = []; gl.rmscum_ref = [];	gl.rmscum_diff = []
	gl.rmssin_sig_exp = []; gl.rmssin_ref_exp = []; gl.rmscum_sig_exp = []; gl.rmscum_ref_exp = [];	gl.rmscum_diff_exp = []
	gl.rmssin_sig_frac = []; gl.rmssin_ref_frac = []; gl.rmscum_sig_frac = []; gl.rmscum_ref_frac = [];	gl.rmscum_diff_frac = []
	gl.G2_cum_sig = []; gl.G2_cum_ref = []
	gl.rmscum_sig_err = []; gl.rmscum_ref_err = []; gl.rmscum_diff_err = []
	gl.ffts_sig = []
	gl.N_e_sig = 0.; gl.N_e_ref = 0.
	gl.intValLabel.config(text="---.- +/- ---.- fs")
	gl.isum_sig = []; gl.n_N_sig = 0
	gl.isum_ref = []; gl.n_N_ref = 0