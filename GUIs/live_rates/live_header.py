import globals as gl

def execute(file):

	numChan = 0
	vRange   = 0
	vOffset  = 0
	numLen  = 123456789
	sampleRate = 0

	headerfile = file[:-4] + "_binheader.txt"
	headerstring = [line.rstrip('\n') for line in open(headerfile)]
	numChan = int (headerstring[2][-1:])

	for i in range (0, len(headerstring)):
		substr = headerstring[i].split("=")
		if substr[0] == "NumAChannels ":
			numChan = int(substr[1])
		if substr[0] == "OrigMaxRange ":
			vRange = int(substr[1])
		if substr[0] == "UserOffset ":
			vOffset = int(substr[1])
		if substr[0] == "LenL ":
			numLen = int(substr[1])
			if numLen == 0:
				numLen = 4e9
		if substr[0] == "Samplerate ":
			sampleRate = int(substr[1])
	
	return numChan, vRange, vOffset, numLen, sampleRate

def write_header(name):
	f = open(gl.basicpath + "/" + name +".settings","w")
	f.write("NumAChannels = {}\n".format(gl.o_nchn))
	f.write("OrigMaxRange = {}\n".format(gl.o_voltages))
	f.write("UserOffset = {}\n".format(0))
	f.write("LenL = {}\n".format(gl.o_samples))
	f.close()