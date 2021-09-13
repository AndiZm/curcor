import sys
# import spectrum driver functions
from pyspcm import *
from spcm_tools import *

import numpy as np
import time
import matplotlib.pyplot as plt

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
qwTotalMem = uint64 (0)
qwToTransfer = uint64 (2*GIGA_B(2))

t_pass = (qwToTransfer.value/2)*1.6e-9
print ("Measure for {:.2f} seconds".format(t_pass))


# settings for the FIFO mode buffer handling
qwBufferSize = uint64 (MEGA_B(512));
lNotifySize = int32 (KILO_B(256));


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


# do a simple standard setup
spcm_dwSetParam_i32 (hCard, SPC_CHENABLE,       3)                      # just 1 channel enabled
spcm_dwSetParam_i32 (hCard, SPC_PRETRIGGER,     32)                     # 1k of pretrigger data at start of FIFO mode
spcm_dwSetParam_i32 (hCard, SPC_CARDMODE,       SPC_REC_FIFO_SINGLE)    # single FIFO mode
spcm_dwSetParam_i32 (hCard, SPC_TIMEOUT,        5000)                   # timeout 5 s
# Triggering
spcm_dwSetParam_i32 (hCard, SPC_TRIG_ORMASK,    SPC_TMASK_EXT0)         # trigger set to extern
spcm_dwSetParam_i32 (hCard, SPC_TRIG_TERM,      1)                      # 50 Ohm termination active
spcm_dwSetParam_i32 (hCard, SPC_TRIG_EXT0_ACDC, 0)                      # DC coupling
spcm_dwSetParam_i32 (hCard, SPC_TRIG_EXT0_LEVEL0, 700)                  # Trigger level 700 mV
spcm_dwSetParam_i32 (hCard, SPC_TRIG_EXT0_MODE, SPC_TM_POS)             # Trigger set on positive edge
spcm_dwSetParam_i32 (hCard, SPC_TRIG_ANDMASK,   0)                      # ...
# Clock
spcm_dwSetParam_i32 (hCard, SPC_CLOCKMODE,      SPC_CM_EXTREFCLOCK)     # clock mode external
spcm_dwSetParam_i32 (hCard, SPC_REFERENCECLOCK, 10000000)               # external clock with 10 MHz
# Voltage range
spcm_dwSetParam_i32 (hCard, SPC_AMP0,           200)                    # Voltage range of channel 0 set to +/- 200 mV
spcm_dwSetParam_i32 (hCard, SPC_AMP1,           200)                    # Voltage range of channel 1 set to +/- 200 mV
# Channel coupling
spcm_dwSetParam_i32 (hCard, SPC_ACDC0,           0)                     # DC coupling channel 0
spcm_dwSetParam_i32 (hCard, SPC_ACDC1,           0)                     # DC coupling channel 1

lBitsPerSample = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_MIINST_BITSPERSAMPLE, byref (lBitsPerSample))

# we try to set the samplerate to 625 MHz, no clock output
spcm_dwSetParam_i64 (hCard, SPC_SAMPLERATE, MEGA(625))
#spcm_dwSetParam_i64 (hCard, SPC_SAMPLERATE, KILO(100))

spcm_dwSetParam_i32 (hCard, SPC_CLOCKOUT, 0)                            # no clock output


# define the data buffer
# we try to use continuous memory if available and big enough
pvBuffer = c_void_p ()
qwContBufLen = uint64 (0)
spcm_dwGetContBuf_i64 (hCard, SPCM_BUF_DATA, byref(pvBuffer), byref(qwContBufLen))
sys.stdout.write ("ContBuf length: {0:d}\n".format(qwContBufLen.value))
print ("We want to use: {0:d}\n".format(qwBufferSize.value))
if qwContBufLen.value >= qwBufferSize.value:
    sys.stdout.write("Using continuous buffer\n")
else:
    pvBuffer = pvAllocMemPageAligned (qwBufferSize.value)
    sys.stdout.write("Using buffer allocated by user program\n")


finish_times = []
# start everything
lNumSamples = int (lNotifySize.value)  # one byte per sample
def measurement(filename):
    global finish_times
    spcm_dwDefTransfer_i64 (hCard, SPCM_BUF_DATA, SPCM_DIR_CARDTOPC, lNotifySize, pvBuffer, uint64 (0), qwBufferSize)
    qwTotalMem = uint64 (0)

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
    finish_times.append(t2)
    newFile.close()
    #
    print (np.mean(np_data))
    print ("Finished in {:.2f} seconds\n".format(t2-t1));

# clean up
def close():
    global finish_times
    spcm_vClose (hCard)
    np.savetxt("finishtimes.txt", finish_times)