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
		gl.peakshape_y[i] /= maxy