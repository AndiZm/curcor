import sys
# import spectrum driver functions
from pyspcm import *
from spcm_tools import *
import time
import matplotlib.pyplot as plt
import numpy as np
import globals as gl
import os
#import correlation as corr

#
# **************************************************************************
# main 
# **************************************************************************
#
class card(object):
    
    def __init__(self, spcm_port, mode):
        self.spcm_port = int(spcm_port)
        self.mode = str(mode)

        self.szErrorTextBuffer = create_string_buffer (ERRORTEXTLEN)
        self.dwError = uint32 ();
        self.lStatus = int32 ()
        self.lAvailUser = int32 ()
        self.lPCPos = int32 ()
        self.qwTotalMem = uint64 (0);
        self.qwToTransfer = uint64 (MEGA_B(8));
        
        self.dataSize = []
        self.qwBufferSize = []

        # settings for the DMA buffer
        self.lNotifySize = int32 (0); # driver should notify program after all data has been transfered
        
        # define the data buffer
        # we try to use continuous memory if available and big enough
        self.pvBuffer = c_void_p ()
        self.qwContBufLen = uint64 (0)
    
        self.lCardType = int32 (0)
        self.lSerialNumber = int32 (0)
        self.lFncType = int32 (0)

    
        # open card
        self.hCard = spcm_hOpen (create_string_buffer (b'/dev/spcm%i'%(spcm_port)))
        if self.hCard == None:
            sys.stdout.write("no card found...\n")
            exit ()
    
        # read type, function and sn and check for A/D card        
        spcm_dwGetParam_i32 (self.hCard, SPC_PCITYP, byref (self.lCardType))        
        spcm_dwGetParam_i32 (self.hCard, SPC_PCISERIALNO, byref (self.lSerialNumber))        
        spcm_dwGetParam_i32 (self.hCard, SPC_FNCTYPE, byref (self.lFncType))
    
        self.sCardName = szTypeToName (self.lCardType.value)
        if self.lFncType.value == SPCM_TYPE_AI:
            sys.stdout.write("Found: {0} sn {1:05d}\n".format(self.sCardName,self.lSerialNumber.value))
        else:
            sys.stdout.write("This is an example for A/D cards.\nCard: {0} sn {1:05d} not supported by example\n".format(self.sCardName,self.lSerialNumber.value))
            exit ()
        if mode == 'eth':
            print ("\tUsing ethernet settings")

    
    def init(self, samples, nchn):
    
        self.dataSize = samples
        self.qwBufferSize = uint64 (self.dataSize * 2 * 1); # in bytes. Enough memory for 16384 samples with 2 bytes each, only one channel active    
    
        # Number of enabled channels:
        if nchn == 1:
            spcm_dwSetParam_i32 (self.hCard, SPC_CHENABLE,       1)                  # just 1 channel enabled
        else:
            spcm_dwSetParam_i32 (self.hCard, SPC_CHENABLE,       3)                  # Both channels enabled
    
        spcm_dwSetParam_i32 (self.hCard, SPC_MEMSIZE,        self.dataSize)          # acquire 16 kS in total
        spcm_dwSetParam_i32 (self.hCard, SPC_PRETRIGGER,     32)                     # almost every samples after trigger event
        spcm_dwSetParam_i32 (self.hCard, SPC_CARDMODE,       SPC_REC_STD_SINGLE)     # single trigger standard mode
        spcm_dwSetParam_i32 (self.hCard, SPC_TIMEOUT,        5000)                   # timeout 5 s
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_ORMASK,    SPC_TMASK_SOFTWARE)     # trigger set to software
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_ANDMASK,   0)                      # ...
        spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKMODE,      SPC_CM_EXTREFCLOCK)     # clock mode external
        spcm_dwSetParam_i32 (self.hCard, SPC_REFERENCECLOCK, 10000000)               # external clock with 10 MHz    
        
        spcm_dwSetParam_i32 (self.hCard, SPC_AMP0,           200)                    # Voltage range of channel 0 set to +/- 200 mV
        spcm_dwSetParam_i32 (self.hCard, SPC_AMP1,           200)                    # Voltage range of channel 1 set to +/- 200 mV
        
        spcm_dwSetParam_i32 (self.hCard, SPC_ACDC0,           0)                      # DC coupling
        spcm_dwSetParam_i32 (self.hCard, SPC_ACDC1,           0)                      # DC coupling
        
        # we try to set the samplerate to 625 MHz on internal PLL, no clock output
        spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, MEGA(625))
        spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKOUT, 0)     # no clock output    
        
        
        spcm_dwGetContBuf_i64 (self.hCard, SPCM_BUF_DATA, byref(self.pvBuffer), byref(self.qwContBufLen))
        #print ("ContBuf length: {0:d}\n".format(qwContBufLen.value))
        if self.qwContBufLen.value >= self.qwBufferSize.value:
            #print ("Using continuous buffer\n")
            pass
        else:
            self.pvBuffer = pvAllocMemPageAligned (self.qwBufferSize.value)
            #print ("Using buffer allocated by user program\n")
    
    def set_voltage_range(self, x):
        spcm_dwSetParam_i32 (self.hCard, SPC_AMP0, x)
        spcm_dwSetParam_i32 (self.hCard, SPC_AMP1, x)
    def set_channels(self, x):
        if x == 1:
            spcm_dwSetParam_i32 (self.hCard, SPC_CHENABLE, 1)
        elif x == 2:
            spcm_dwSetParam_i32 (self.hCard, SPC_CHENABLE, 3)
    def set_sample_size(self, x):
        self.dataSize = x   
        self.qwBufferSize = uint64 (self.dataSize * 2 * 1); # in bytes. Enough memory for 16384 samples with 2 bytes each, only one channel active
        spcm_dwSetParam_i32 (self.hCard, SPC_MEMSIZE, self.dataSize)
        spcm_dwGetContBuf_i64 (self.hCard, SPCM_BUF_DATA, byref(self.pvBuffer), byref(self.qwContBufLen))
        print ("ContBuf length: {0:d}\n".format(self.qwContBufLen.value),"qwBuffer length:",self.qwBufferSize.value )
        #if self.qwContBufLen.value >= self.qwBufferSize.value:
        #    print ("Using continuous buffer\n")
        #else:
        #    self.pvBuffer = pvAllocMemPageAligned (self.qwBufferSize.value)
        #    print ("Using buffer allocated by user program\n")
    def set_sampling(self, x):
        if x == 0.8e-9:
            spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, MEGA(1250))
        if x == 1.6e-9:
            spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, MEGA(625))
        if x == 3.2e-9:
            spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, KILO(312500))
        if x == 6.4e-9:
            spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, KILO(156250))
    def set_clockmode(self, x):
        if x == 1: # internal clock
            self.set_clockout_off()
            spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKMODE, SPC_CM_INTPLL)
        if x == 2: # external clock with 10 MHz
            self.set_clockout_off()
            spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKMODE, SPC_CM_EXTREFCLOCK)
            spcm_dwSetParam_i32 (self.hCard, SPC_REFERENCECLOCK, 10000000)
        if x == 3: # use internal clock, and enable clock output
            spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKMODE, SPC_CM_INTPLL)
            self.set_clockout_on()

    def set_clockout_on(self):
            spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKOUT,       1)
            sys.stdout.write("{0} sn {1:05d} - Clockout ON\n".format(self.sCardName,self.lSerialNumber.value))
    def set_clockout_off(self):
            spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKOUT,       0)
            sys.stdout.write("{0} sn {1:05d} - Clockout OFF\n".format(self.sCardName,self.lSerialNumber.value))
    def set_triggermode(self, x):
        if x == True:
            spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_ORMASK,    SPC_TMASK_EXT0)         # trigger set to extern
            spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_TERM,      0)                      # 50 Ohm termination, 1 == active
            spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_EXT0_ACDC, 0)                      # DC coupling
            spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_EXT0_LEVEL0, 700)                  # Trigger level 700 mV
            spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_EXT0_MODE, SPC_TM_POS)             # Trigger set on positive edge
            spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_ANDMASK,   0)

        if x == False:
            spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_ORMASK,    SPC_TMASK_SOFTWARE)     # trigger set to software
            spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_ANDMASK,   0)                      # ...
    
    # This function is called when no data will be saved to disk, but only displayed
    def init_display(self, samples, nchn):
        # settings for the FIFO mode buffer handling
        self.dataSize = samples 
        self.qwBufferSize = uint64 (self.dataSize * 2 * 1); # in bytes. Enough memory for 16384 samples with 2 bytes each, only one channel active
        # Number of enabled channels:
        if nchn == 1:
            spcm_dwSetParam_i32 (self.hCard, SPC_CHENABLE,       1)                  # just 1 channel enabled
        else:
            spcm_dwSetParam_i32 (self.hCard, SPC_CHENABLE,       3)                  # Both channels enabled    
        # define the data buffer
        self.pvBuffer = c_void_p ()
        self.qwContBufLen = uint64 (0)
        spcm_dwGetContBuf_i64 (self.hCard, SPCM_BUF_DATA, byref(self.pvBuffer), byref(self.qwContBufLen))
        if self.qwContBufLen.value >= self.qwBufferSize.value:
            pass
        else:
            self.pvBuffer = pvAllocMemPageAligned (self.qwBufferSize.value)
        spcm_dwGetContBuf_i64 (self.hCard, SPCM_BUF_DATA, byref(self.pvBuffer), byref(self.qwContBufLen))
        spcm_dwSetParam_i32 (self.hCard, SPC_CARDMODE, SPC_REC_STD_SINGLE)
    
    def take_data(self, nchn):
        spcm_dwDefTransfer_i64 (self.hCard, SPCM_BUF_DATA, SPCM_DIR_CARDTOPC, self.lNotifySize, self.pvBuffer, uint64 (0), self.qwBufferSize)
        dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_DATA_STARTDMA )
        
        # check for error
        if dwError != 0: # != ERR_OK
            spcm_dwGetErrorInfo_i32 (self.hCard, None, None, self.szErrorTextBuffer)
            sys.stdout.write("{0}\n".format(self.szErrorTextBuffer.value))
            spcm_vClose (self.hCard)
            exit ()
        
        # wait until acquisition has finished ...
        else:
            dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_WAITREADY)
            if dwError != ERR_OK:
                if dwError == ERR_TIMEOUT:
                    sys.stdout.write ("... Timeout\n")
                else:
                    sys.stdout.write ("... Error: {0:d}\n".format(dwError))
        # ... now create array of data
            else:
                # this is the point to do anything with the data
                pbyData = cast (self.pvBuffer, ptr8) # cast to pointer to 8bit integer
                data = np.ctypeslib.as_array(pbyData, shape=(self.dataSize, 1)) 
    
                if nchn == 2:
                    data = np.array(data)
                    data = data.reshape(int((self.dataSize)/2), 2)
                    a_np = np.array(data[:,0]); b_np = np.array(data[:,1])
                    mean_a = np.mean(a_np); mean_b = np.mean(b_np)
                    a_send = a_np[0:1000]; b_send = b_np[0:1000]
                else:
                    data = np.array(data)
                    a_np = np.array(data)
                    mean_a = np.mean(data); mean_b = 0
                    a_send = a_np[0:1000]; b_send = []             
                return mean_a, mean_b, a_send, b_send
        
    

    # This function is called to initialize the mechanism for data storage to disk
    def init_storage(self):
        # settings for the FIFO mode buffer handling
        
        if self.mode == "eth": # Data transfer via ethernet
            self.lNotifySize = int32 (KILO_B(32768*2))   #was 256
            self.qwBufferSize = uint64 (MEGA_B(256)) # 512
        else :
            self.lNotifySize = int32 (KILO_B(4096))   #was 256
            self.qwBufferSize = uint64 (MEGA_B(64))
        # define the data buffer
        self.pvBuffer = c_void_p ()
        self.qwContBufLen = uint64 (0)
        spcm_dwGetContBuf_i64 (self.hCard, SPCM_BUF_DATA, byref(self.pvBuffer), byref(self.qwContBufLen))
        spcm_dwSetParam_i32 (self.hCard, SPC_CARDMODE, SPC_REC_FIFO_SINGLE)    # single FIFO mode
        self.lBitsPerSample = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_MIINST_BITSPERSAMPLE, byref (self.lBitsPerSample))
        self.lNumSamples = int (self.lNotifySize.value)  # one byte per sample
       
    def measurement(self, filename, nchn, samples):
        t1=-1
        t1 = time.time()
        spcm_dwDefTransfer_i64 (self.hCard, SPCM_BUF_DATA, SPCM_DIR_CARDTOPC, self.lNotifySize, self.pvBuffer, uint64 (0), self.qwBufferSize)
        self.qwTotalMem = uint64 (0)
        self.qwToTransfer = uint64 (nchn * samples)
        
        #newFile = open(filename,"ab")
        flags =  os.O_WRONLY  | os.O_BINARY | os.O_SEQUENTIAL | os.O_CREAT #|os.O_APPEND 
        mode = 0o666
        newFile = os.open(filename,flags,mode)
        #if self.lSerialNumber.value==13100 :
        #    alldata=[]
       #     filename2=("Y:"+filename[2:])
       #     newFile2 = os.open(filename2,flags,mode)

        dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_DATA_STARTDMA)


        # check for error
        if dwError != 0: # != ERR_OK
            spcm_dwGetErrorInfo_i32 (self.hCard, None, None, self.szErrorTextBuffer)
            sys.stdout.write("{0}\n".format(self.szErrorTextBuffer.value))
            spcm_vClose (self.hCard)
            exit ()

        # run the FIFO mode and loop through the data
        else:
            t=0
            #t1 = time.time()
            while self.qwTotalMem.value < self.qwToTransfer.value:   
                if time.time()-t1>10:
                    print("too long")
                    break;
                dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_DATA_WAITDMA)
                if dwError != ERR_OK:
                    if dwError == ERR_TIMEOUT:
                        sys.stdout.write ("... Timeout\n")
                        spcm_vClose (self.hCard); exit ()
                    else:
                        sys.stdout.write ("... Error: {0:d}\n".format(dwError))
                        break;        
                else:
                    # Wait until the new available Data exceeds the defined chunk size
                    spcm_dwGetParam_i32 (self.hCard, SPC_DATA_AVAIL_USER_LEN, byref (self.lAvailUser))
                    spcm_dwGetParam_i32 (self.hCard, SPC_DATA_AVAIL_USER_POS, byref (self.lPCPos))
                    
                    #poss.append(lPCPos.value)
                    if self.lAvailUser.value >= self.lNotifySize.value:

                        #if self.mode == "eth" :
                        #   #print("t",t,"Card",self.lSerialNumber.value,"AvailUser",self.lAvailUser.value, "User Pos", self.lPCPos.value)
                        #   if ((self.lAvailUser.value + self.lPCPos.value) > 201326592+67108864) :
                        #       self.lAvailUser.value = self.lNotifySize.value
                        #   self.qwTotalMem.value += self.lAvailUser.value
                        #   
                        #   t+=1
                        #   pbyData = cast  (self.pvBuffer.value + self.lPCPos.value, ptr8) # cast to pointer to 8bit integer
                        #   np_data = np.ctypeslib.as_array(pbyData, shape=(int(self.lAvailUser.value), 1))
                        #   os.write(newFile,np_data)
                        #   spcm_dwSetParam_i32 (self.hCard, SPC_DATA_AVAIL_CARD_LEN,  self.lAvailUser)
                        #else :
                        if t==0:
                            tfirst=time.time()
                            print("sn {} - First block after {:.2f} seconds".format(self.lSerialNumber.value, tfirst-t1))
                        #if t1==-1:
                        #    pass
                        self.qwTotalMem.value += self.lNotifySize.value 
                        pbyData = cast  (self.pvBuffer.value + self.lPCPos.value, ptr8) # cast to pointer to 8bit integer
                        np_data = np.ctypeslib.as_array(pbyData, shape=(self.lNumSamples, 1))
                            #if self.mode == "eth":
                            #    pass
                             #   if t==0:
                              #      np_all=np.copy(np_data)
                               # else:
                                #    np_all=np.concatenate(np_all,np_data)
                            #else:
                        #os.write(newFile,np_data)
                        spcm_dwSetParam_i32 (self.hCard, SPC_DATA_AVAIL_CARD_LEN,  self.lNotifySize)
                        
                        # Insert auto-correlation here
                        #autocorr += corr.autocorrelation(np_data)
                        #newFile.write(np_data)
                        #if self.mode == "eth":
                        #    if t%2==0:
                        #        alldata=np_data
                        #    else:
                        #        alldata=np.concatenate(alldata,np_data)
                        #        os.write(newFile,alldata)
                        #    #if(t%2==0):
                        #    #    os.write(newFile,np_data)
                        #    #else:
                        #    #    os.write(newFile2,np_data)
                        #else:
                        os.write(newFile,np_data)
                        t+=1
                        #spcm_dwSetParam_i32 (self.hCard, SPC_DATA_AVAIL_CARD_LEN,  self.lNotifySize)
        # send the stop command
        dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_STOP | M2CMD_DATA_STOPDMA)
    
        t2 = time.time()
        #newFile.close()
        #if self.lSerialNumber.value==13100 :
         #   os.write(newFile,alldata)
          #  os.close(newFile)
        #else:
        os.close(newFile)

        #np.savetxt(filename[:-3]+".acorr", autocorr)
        t_acq = t2-t1
        print("sn {} - Finished in {:.2f} seconds".format(self.lSerialNumber.value, t_acq))
        #return 0,0,[0,0,0],[0,0,0]
        # The last part of the data will be used for plotting and rate calculations
        data = np.array(np_data[0:2000])
        shape_x=data.shape[0]
        if nchn == 2:
            #data = data.reshape(int((self.lNotifySize.value)/2), 2)
            data = data.reshape(shape_x//2,2)
            a_np = np.array(data[:,0]); b_np = np.array(data[:,1])
            mean_a = np.mean(a_np); mean_b = np.mean(b_np)
            a_send = a_np[0:1000]; b_send = b_np[0:1000]
        else:
            #data = data.reshape(self.lNotifySize.value,1)
            mean_a = np.mean(data); mean_b = 0
            a_np = data
            a_send = a_np[0:1000]; b_send = []
        #print(mean_a, mean_b, a_send, b_send)
        return mean_a, mean_b, a_send, b_send, t_acq
    
    # clean up
    def close(self):
        spcm_vClose (self.hCard)