import sys
# import spectrum driver functions
from pyspcm import *
from spcm_tools import *
import time
import matplotlib.pyplot as plt
import numpy as np
import globals as gl

#
# **************************************************************************
# main 
# **************************************************************************
#

szErrorTextBuffer = create_string_buffer (ERRORTEXTLEN)
dwError = uint32 ();
lStatus = int32 ()
lAvailUser = int32 ()
lPCPos = int32 ()
qwTotalMem = uint64 (0);
qwToTransfer = uint64 (MEGA_B(8));

dataSize = []
qwBufferSize = []

# settings for the DMA buffer
lNotifySize = int32 (0); # driver should notify program after all data has been transfered

# define the data buffer
# we try to use continuous memory if available and big enough
pvBuffer = c_void_p ()
qwContBufLen = uint64 (0)

# open card
hCard = spcm_hOpen (create_string_buffer (b'/dev/spcm0'))
if hCard == None:
    sys.stdout.write("no card found...\n")
    exit ()

# read type, function and sn and check for A/D card
lCardType = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_PCITYP, byref (lCardType))
lSerialNumber = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_PCISERIALNO, byref (lSerialNumber))
lFncType = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_FNCTYPE, byref (lFncType))

sCardName = szTypeToName (lCardType.value)
if lFncType.value == SPCM_TYPE_AI:
    sys.stdout.write("Found: {0} sn {1:05d}\n".format(sCardName,lSerialNumber.value))
else:
    sys.stdout.write("This is an example for A/D cards.\nCard: {0} sn {1:05d} not supported by example\n".format(sCardName,lSerialNumber.value))
    exit ()

def init():
    global hCard, pvBuffer, qwContBufLen, lNotifySize, qwBufferSize, dataSize

    dataSize = gl.o_samples_quick 
    qwBufferSize = uint64 (dataSize * 2 * 1); # in bytes. Enough memory for 16384 samples with 2 bytes each, only one channel active    

    # Number of enabled channels:
    if gl.o_nchn == 1:
        spcm_dwSetParam_i32 (hCard, SPC_CHENABLE,       1)                  # just 1 channel enabled
    else:
        spcm_dwSetParam_i32 (hCard, SPC_CHENABLE,       3)                  # Both channels enabled

    spcm_dwSetParam_i32 (hCard, SPC_MEMSIZE,        dataSize)               # acquire 16 kS in total
    spcm_dwSetParam_i32 (hCard, SPC_PRETRIGGER,     32)                     # almost every samples after trigger event
    spcm_dwSetParam_i32 (hCard, SPC_CARDMODE,       SPC_REC_STD_SINGLE)     # single trigger standard mode
    spcm_dwSetParam_i32 (hCard, SPC_TIMEOUT,        5000)                   # timeout 5 s
    spcm_dwSetParam_i32 (hCard, SPC_TRIG_ORMASK,    SPC_TMASK_SOFTWARE)     # trigger set to software
    spcm_dwSetParam_i32 (hCard, SPC_TRIG_ANDMASK,   0)                      # ...
    spcm_dwSetParam_i32 (hCard, SPC_CLOCKMODE,      SPC_CM_EXTREFCLOCK)     # clock mode external
    spcm_dwSetParam_i32 (hCard, SPC_REFERENCECLOCK, 10000000)               # external clock with 10 MHz

    
    spcm_dwSetParam_i32 (hCard, SPC_AMP0,           200)                    # Voltage range of channel 0 set to +/- 200 mV
    spcm_dwSetParam_i32 (hCard, SPC_AMP1,           200)                    # Voltage range of channel 1 set to +/- 200 mV
    
    spcm_dwSetParam_i32 (hCard, SPC_ACDC0,           0)                      # DC coupling
    spcm_dwSetParam_i32 (hCard, SPC_ACDC1,           0)                      # DC coupling
    
    # we try to set the samplerate to 625 MHz on internal PLL, no clock output
    spcm_dwSetParam_i64 (hCard, SPC_SAMPLERATE, MEGA(625))
    spcm_dwSetParam_i32 (hCard, SPC_CLOCKOUT, 0)     # no clock output    
    
    
    spcm_dwGetContBuf_i64 (hCard, SPCM_BUF_DATA, byref(pvBuffer), byref(qwContBufLen))
    #print ("ContBuf length: {0:d}\n".format(qwContBufLen.value))
    if qwContBufLen.value >= qwBufferSize.value:
        #print ("Using continuous buffer\n")
        pass
    else:
        pvBuffer = pvAllocMemPageAligned (qwBufferSize.value)
        #print ("Using buffer allocated by user program\n")

def set_voltage_range(x):
    spcm_dwSetParam_i32 (hCard, SPC_AMP0, x)
    spcm_dwSetParam_i32 (hCard, SPC_AMP1, x)
def set_channels(x):
    if x == 1:
        spcm_dwSetParam_i32 (hCard, SPC_CHENABLE, 1)
    elif x == 2:
        spcm_dwSetParam_i32 (hCard, SPC_CHENABLE, 3)
def set_sample_size(x):
    global pvBuffer, qwContBufLen, qwBufferSize, dataSize
    dataSize = x   
    qwBufferSize = uint64 (dataSize * 2 * 1); # in bytes. Enough memory for 16384 samples with 2 bytes each, only one channel active
    spcm_dwSetParam_i32 (hCard, SPC_MEMSIZE, dataSize)
    spcm_dwGetContBuf_i64 (hCard, SPCM_BUF_DATA, byref(pvBuffer), byref(qwContBufLen))
    print ("ContBuf length: {0:d}\n".format(qwContBufLen.value))
    if qwContBufLen.value >= qwBufferSize.value:
        print ("Using continuous buffer\n")
    else:
        pvBuffer = pvAllocMemPageAligned (qwBufferSize.value)
        print ("Using buffer allocated by user program\n")
def set_sampling(x):
    if x == 0.8e-9:
        spcm_dwSetParam_i64 (hCard, SPC_SAMPLERATE, MEGA(1250))
    if x == 1.6e-9:
        spcm_dwSetParam_i64 (hCard, SPC_SAMPLERATE, MEGA(625))
    if x == 3.2e-9:
        spcm_dwSetParam_i64 (hCard, SPC_SAMPLERATE, KILO(312500))
    if x == 6.4e-9:
        spcm_dwSetParam_i64 (hCard, SPC_SAMPLERATE, KILO(156250))
def set_clockmode():
    if gl.clockmode.get() == 1:
        spcm_dwSetParam_i32 (hCard, SPC_CLOCKMODE, SPC_CM_INTPLL)
    if gl.clockmode.get() == 2:
        spcm_dwSetParam_i32 (hCard, SPC_CLOCKMODE, SPC_CM_EXTREFCLOCK)
        spcm_dwSetParam_i32 (hCard, SPC_REFERENCECLOCK, 10000000)
def set_triggermode():
    if gl.trigger == True:
        spcm_dwSetParam_i32 (hCard, SPC_TRIG_ORMASK,    SPC_TMASK_EXT0)         # trigger set to extern
        spcm_dwSetParam_i32 (hCard, SPC_TRIG_TERM,      1)                      # 50 Ohm termination active
        spcm_dwSetParam_i32 (hCard, SPC_TRIG_EXT0_ACDC, 0)                      # DC coupling
        spcm_dwSetParam_i32 (hCard, SPC_TRIG_EXT0_LEVEL0, 700)                  # Trigger level 700 mV
        spcm_dwSetParam_i32 (hCard, SPC_TRIG_EXT0_MODE, SPC_TM_POS)             # Trigger set on positive edge
        spcm_dwSetParam_i32 (hCard, SPC_TRIG_ANDMASK,   0) 
    if gl.trigger == False:
        spcm_dwSetParam_i32 (hCard, SPC_TRIG_ORMASK,    SPC_TMASK_SOFTWARE)     # trigger set to software
        spcm_dwSetParam_i32 (hCard, SPC_TRIG_ANDMASK,   0)                      # ...

def init_display():
    global qwBufferSize, lNotifySize, pvBuffer, qwContBufLen, hCard, lBitsPerSample, lNumSamples
    # settings for the FIFO mode buffer handling
    dataSize = gl.o_samples_quick 
    qwBufferSize = uint64 (dataSize * 2 * 1); # in bytes. Enough memory for 16384 samples with 2 bytes each, only one channel active
    # Number of enabled channels:
    if gl.o_nchn == 1:
        spcm_dwSetParam_i32 (hCard, SPC_CHENABLE,       1)                  # just 1 channel enabled
    else:
        spcm_dwSetParam_i32 (hCard, SPC_CHENABLE,       3)                  # Both channels enabled

    # define the data buffer
    pvBuffer = c_void_p ()
    qwContBufLen = uint64 (0)
    spcm_dwGetContBuf_i64 (hCard, SPCM_BUF_DATA, byref(pvBuffer), byref(qwContBufLen))
    #print ("ContBuf length: {0:d}\n".format(qwContBufLen.value))
    if qwContBufLen.value >= qwBufferSize.value:
        #print ("Using continuous buffer\n")
        pass
    else:
        pvBuffer = pvAllocMemPageAligned (qwBufferSize.value)
        #print ("Using buffer allocated by user program\n")
    spcm_dwGetContBuf_i64 (hCard, SPCM_BUF_DATA, byref(pvBuffer), byref(qwContBufLen))
    spcm_dwSetParam_i32 (hCard, SPC_CARDMODE, SPC_REC_STD_SINGLE)

def take_data():
    global hCard, lNotifySize, pvBuffer, qwContBufLen, qwBufferSize, dataSize
    spcm_dwDefTransfer_i64 (hCard, SPCM_BUF_DATA, SPCM_DIR_CARDTOPC, lNotifySize, pvBuffer, uint64 (0), qwBufferSize)
    dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_DATA_STARTDMA )
    
    # check for error
    if dwError != 0: # != ERR_OK
        spcm_dwGetErrorInfo_i32 (hCard, None, None, szErrorTextBuffer)
        sys.stdout.write("{0}\n".format(szErrorTextBuffer.value))
        spcm_vClose (hCard)
        exit ()
    
    # wait until acquisition has finished ...
    else:
        dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_WAITREADY)
        if dwError != ERR_OK:
            if dwError == ERR_TIMEOUT:
                sys.stdout.write ("... Timeout\n")
            else:
                sys.stdout.write ("... Error: {0:d}\n".format(dwError))
    # ... now create array of data
        else:
            # this is the point to do anything with the data
            pbyData = cast (pvBuffer, ptr8) # cast to pointer to 8bit integer
            #data = []
            #for i in range (0, dataSize):
            #    data.append(int(pbyData[i]))
            data = np.ctypeslib.as_array(pbyData, shape=(dataSize, 1)) 

            if gl.o_nchn == 2:
                data = np.array(data)
                data = data.reshape(int((dataSize)/2), 2)
                a_np = np.array(data[:,0]); b_np = np.array(data[:,1])
                mean_a = np.mean(a_np)
                mean_b = np.mean(b_np)

                #plt.plot(a_np[0:5000], alpha=0.3)
                #plt.plot(a_np[-5000:])
                #plt.axhline(y=mean_a, color="red")
                #plt.axhline(y=np.mean(a_np[0:5000]), color="black")
                #plt.show()

                gl.update_waveform(a_np[0:1000],b_np[0:1000])
            else:
                mean_a = np.mean(data)
                mean_b = 0 
                gl.update_waveform(data[0:1000],[])
            return mean_a, mean_b
    

def init_storage():
    global qwBufferSize, lNotifySize, pvBuffer, qwContBufLen, hCard, lBitsPerSample, lNumSamples
    # settings for the FIFO mode buffer handling
    qwBufferSize = uint64 (MEGA_B(512))
    lNotifySize = int32 (KILO_B(256))

    # define the data buffer
    pvBuffer = c_void_p ()
    qwContBufLen = uint64 (0)
    spcm_dwGetContBuf_i64 (hCard, SPCM_BUF_DATA, byref(pvBuffer), byref(qwContBufLen))
    spcm_dwSetParam_i32 (hCard, SPC_CARDMODE, SPC_REC_FIFO_SINGLE)    # single FIFO mode
    lBitsPerSample = int32 (0)
    spcm_dwGetParam_i32 (hCard, SPC_MIINST_BITSPERSAMPLE, byref (lBitsPerSample))
    lNumSamples = int (lNotifySize.value)  # one byte per sample
   
def measurement(filename):
    spcm_dwDefTransfer_i64 (hCard, SPCM_BUF_DATA, SPCM_DIR_CARDTOPC, lNotifySize, pvBuffer, uint64 (0), qwBufferSize)
    qwTotalMem = uint64 (0)
    qwToTransfer = uint64 (gl.o_nchn * gl.o_samples)

    newFile = open(filename,"ab")
    t1 = time.time()
    dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_DATA_STARTDMA)
    
    # check for error
    if dwError != 0: # != ERR_OK
        spcm_dwGetErrorInfo_i32 (hCard, None, None, szErrorTextBuffer)
        sys.stdout.write("{0}\n".format(szErrorTextBuffer.value))
        spcm_vClose (hCard)
        exit ()
    # run the FIFO mode and loop through the data
    else:
        while qwTotalMem.value < qwToTransfer.value:
        #while lAvailUser.value < qwContBufLen.value:
    
            dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_DATA_WAITDMA)
            if dwError != ERR_OK:
                if dwError == ERR_TIMEOUT:
                    sys.stdout.write ("... Timeout\n")
                else:
                    sys.stdout.write ("... Error: {0:d}\n".format(dwError))
                    break;
    
            else:
                # Wait until the new available Data exceeds the defined chunk size
                spcm_dwGetParam_i32 (hCard, SPC_DATA_AVAIL_USER_LEN, byref (lAvailUser))
                spcm_dwGetParam_i32 (hCard, SPC_DATA_AVAIL_USER_POS, byref (lPCPos))
                #poss.append(lPCPos.value)
                if lAvailUser.value >= lNotifySize.value:
                    qwTotalMem.value += lNotifySize.value
                    #sys.stdout.write ("Stat:{0:08x} Pos:{1:08x} Avail:{2:08x} Total:{3:.2f}MB/{4:.2f}MB\n".format(lStatus.value, lPCPos.value, lAvailUser.value, c_double (qwTotalMem.value).value / MEGA_B(1), c_double (qwToTransfer.value).value / MEGA_B(1)))
                    #print ("Avail:\t{}\t\tPos:\t{}".format(lAvailUser.value,lPCPos.value))
    
                    pbyData = cast  (pvBuffer.value + lPCPos.value, ptr8) # cast to pointer to 8bit integer
                    np_data = np.ctypeslib.as_array(pbyData, shape=(lNumSamples, 1))          
                    newFile.write(np_data)

                    spcm_dwSetParam_i32 (hCard, SPC_DATA_AVAIL_CARD_LEN,  lNotifySize)

    # send the stop command
    dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_STOP | M2CMD_DATA_STOPDMA)
    
    t2 = time.time()
    newFile.close()
    #
    print (np.mean(np_data))
    print ("Finished in {:.2f} seconds\n".format(t2-t1))

# clean up
def close():
    global hCard
    spcm_vClose (hCard)