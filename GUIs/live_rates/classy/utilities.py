import numpy as np

############################
## SOME GENERAL FUNCTIONS ##
############################
def ADC_to_mV(adc, range):
	return adc*range/127
def mV_to_ADC(mV, range):
	return mV*127/range
# Two functions to create specific filenames out of existing files
def to_calib(file, ending):
	fileparts = file.split("/"); fileparts.insert(-1,"calibs")
	fileparts[-1] = fileparts[-1].split(".")[0] + ending
	filebuild = fileparts[0]
	for i in range (1,len(fileparts)):
		filebuild += "/" + fileparts[i]
	return filebuild
def to_bin(file):
	fileparts = file.split("/"); fileparts.remove("calibs")
	fileparts[-1] = fileparts[-1].split(".")[0] + ".bin"
	filebuild = fileparts[0]
	for i in range (1,len(fileparts)):
		filebuild += "/" + fileparts[i]
	return filebuild

zeroadder = ["0000","0000","000","00","0",""]
def numberstring(x):
    if x == 0:
        nod = 1
    else:
        nod = int(np.log10(x))+1
    return zeroadder[nod] + str(x)

def gauss(x,a,m,s):
	return a * np.exp(-(x-m)**2/2/s/s)