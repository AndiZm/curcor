#import pyopencl as cl
import numpy as np
from numba import jit, cuda
import scipy.signal as sig


#platform = cl.get_platforms()
#my_gpu_devices = platform[0].get_devices(device_type=cl.device_type.GPU)
#ctx = cl.Context(devices=my_gpu_devices)
#queue = cl.CommandQueue(ctx)

@jit(nopython=True, parallel=True, fastmath=True)
def scalarproduct(chan_a, chan_b):
    return np.sum(chan_a*chan_b)


# offset = <X>: res[0] equal to G2(<X>)
# shift = <Y>: res[0] equal to G2(offset + <Y>)
@jit(nopython=True, parallel=True, fastmath=True)
def corr_CPU(chan_a, chan_b, shifts, offset):
    res = np.zeros(shifts+1, dtype=np.int64)
    for i in range(shifts+1):
        res[i] = scalarproduct(chan_a[:len(chan_a) - offset - shifts],
                               chan_b[offset + i:len(chan_b)-shifts+i])
    return res

@jit(nopython=True, parallel=True, fastmath=True)
def corr_CPU_weight(chan_a, chan_b, shifts, offset, weight):
    res = np.zeros(shifts+1)
    for i in range(shifts+1):
        res[i] = scalarproduct(chan_a[:len(chan_a) - offset - shifts],
                               chan_b[offset + i:len(chan_b)-shifts+i])
    avg = np.mean(res[50:])
    for i in range(shifts+1):
        res[i] = 1.*weight * res[i]/avg
    return res

@jit(nopython=True, parallel=True, fastmath=True)
def corr_CPU_debug(chan_a, chan_b,  shift):
    ntot = len(chan_a)
    a_np = chan_a[:ntot - shift + 1]
    b_np = chan_b
    res = np.zeros(shift, dtype=np.int64)
    for i in range(shift):
        res[i] = np.sum(a_np * b_np[i:ntot - shift + i + 1])
    return res

#@jit(nopython=False, parallel=True, fastmath=True)
def corr_CPU_timestamping(chan_a, chan_b, shift, height_a, height_b):
	peaks_a, _ = sig.find_peaks(-chan_a, height = -height_a)
	peaks_b, _ = sig.find_peaks(-chan_b, height = -height_b)
	time_differences = []
	histobins = np.arange(0, shift+2, 1)
	ind_b = 0
	for i in range (len(peaks_a)):
		bas = peaks_a[i] # Position of current Photon in Channel a
		while peaks_b[ind_b] < bas and ind_b < len(peaks_b)-1:
			ind_b += 1
		b_i = ind_b
		while (peaks_b[b_i] - bas) <= shift and b_i < len(peaks_b)-1: # Store time differences
			time_differences.append(peaks_b[b_i] - bas)
			b_i += 1
	histo = np.histogram(time_differences, bins=histobins)
	return histo[0]



#############
# GPU stuff #
#############
'''
prg_uint8 = cl.Program(ctx, """
    __kernel void corr(
    long n, int nsplit, int shift,
    __global unsigned char *a, __global unsigned char *b, __global long *c)
    {
    long split_size = n/nsplit;
    int gid = get_global_id(0);
    int ishift = gid/nsplit;
    int isplit = gid%nsplit;
    long imin = isplit * split_size;
    long imax = (isplit + 1) * split_size;
    c[gid] = 0;
    for(long i=imin; i < imax; i++)
    {
    c[gid] += a[i] * b[i + ishift];
    }
    }
    """).build()

prg_int8 = cl.Program(ctx, """
    __kernel void corr(
    long n, int nsplit, int shift,
    __global char *a, __global char *b, __global long *c)
    {
    long split_size = n/nsplit;
    int gid = get_global_id(0);
    int ishift = gid/nsplit;
    int isplit = gid%nsplit;
    long imin = isplit * split_size;
    long imax = (isplit + 1) * split_size;
    c[gid] = 0;
    for(long i=imin; i < imax; i++)
    {
    c[gid] += a[i] * b[i + ishift];
    }
    }
    """).build()
    
    # the wrapper GPU correlation function
def corr_GPU_uint8(chan_a, chan_b, shift, nsplit, dtype, test=0, alt_order=0):
    ntot = len(chan_a)
    a_np = np.array(chan_a[:ntot - shift + 1], dtype=dtype)
    b_np = np.array(chan_b, dtype=dtype)
    #print('Hier')
    #print(a_np)
    #dtype = np.int8
    # correlate the arrays
    #a_np = np.array(chan_a[:-shift], dtype=np.int8)
    #b_np = np.array(chan_b, dtype=np.int8)
    #output array
    c_np = np.zeros(shift * nsplit, dtype=np.int64)
    #print(c_np)
    
    # define the memory buffers
    mf = cl.mem_flags
    a_buf = cl.Buffer\
        (ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=a_np)
    b_buf = cl.Buffer\
        (ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=b_np)
    c_buf = cl.Buffer(ctx, mf.WRITE_ONLY, c_np.nbytes)

    # run the correlation
    prg_uint8.corr(queue, c_np.shape, None,
                  np.int64(ntot), np.int32(nsplit), np.int32(shift),
                  a_buf, b_buf, c_buf)

    # write the result to the numpy array
    cl.enqueue_copy(queue, c_np, c_buf)
    #print(c_np)
        
    #if test:
        #print "a array", a_np
        #print "b array", b_np
        #print "correlations", c_np

    # reshape the output array
    #if alt_order:
       # c_np = c_np.reshape((nsplit, shift))
   # else:
       # c_np = c_np.reshape((shift, nsplit))
    c_np = c_np.reshape((shift, nsplit))
    
  #  if test:
       # if alt_order:
            #print "correlations as (nsplit x shift) array"
            #print c_np
        #else:
           # print "correlations as (shift x nsplit) array"
           # print c_np
    c_np = np.sum(c_np, axis=1)
    # sum over the data splits to get the final correlations
    #if alt_order:
        #c_np = np.sum(c_np, axis=0)
    #else:
        #c_np = np.sum(c_np, axis=1)

    if test:
        print('final c_np')
        print(c_np)

    return c_np

    # the wrapper GPU correlation function
def corr_GPU_int8(chan_a, chan_b, shift, nsplit, dtype, test=0, alt_order=0):
    ntot = len(chan_a)
    a_np = np.array(chan_a[:ntot - shift + 1], dtype=dtype)
    b_np = np.array(chan_b, dtype=dtype)
    #print('Hier')
    #print(a_np)
    #dtype = np.int8
    # correlate the arrays
    #a_np = np.array(chan_a[:-shift], dtype=np.int8)
    #b_np = np.array(chan_b, dtype=np.int8)
    #output array
    c_np = np.zeros(shift * nsplit, dtype=np.int64)
    #print(c_np)
    
    # define the memory buffers
    mf = cl.mem_flags
    a_buf = cl.Buffer\
        (ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=a_np)
    b_buf = cl.Buffer\
        (ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=b_np)
    c_buf = cl.Buffer(ctx, mf.WRITE_ONLY, c_np.nbytes)

    # run the correlation
    prg_int8.corr(queue, c_np.shape, None,
                  np.int64(ntot), np.int32(nsplit), np.int32(shift),
                  a_buf, b_buf, c_buf)

    # write the result to the numpy array
    cl.enqueue_copy(queue, c_np, c_buf)
    #print(c_np)
        
    #if test:
        #print "a array", a_np
        #print "b array", b_np
        #print "correlations", c_np

    # reshape the output array
    #if alt_order:
       # c_np = c_np.reshape((nsplit, shift))
   # else:
       # c_np = c_np.reshape((shift, nsplit))
    c_np = c_np.reshape((shift, nsplit))
    
  #  if test:
       # if alt_order:
            #print "correlations as (nsplit x shift) array"
            #print c_np
        #else:
           # print "correlations as (shift x nsplit) array"
           # print c_np
    c_np = np.sum(c_np, axis=1)
    # sum over the data splits to get the final correlations
    #if alt_order:
        #c_np = np.sum(c_np, axis=0)
    #else:
        #c_np = np.sum(c_np, axis=1)

    if test:
        print('final c_np')
        print(c_np)

    return c_np
'''