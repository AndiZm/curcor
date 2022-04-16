import numpy as np
from os import listdir
from os.path import isfile, join

def execute(file):

	fileparts = file.split("/")	
	filebody = fileparts[-1]
	filebody = filebody[:-10]
	filepath = ""
	for i in range (0, len(fileparts)-1):
		filepath += fileparts[i] + "/"

	allfiles = [f for f in listdir(filepath) if isfile(join(filepath, f))]
	filearray = []; numbers = []
	for i in range (0, len(allfiles)):
		if allfiles[i][-4:] == ".bin":
			pure_filename = allfiles[i].split("/")[-1]

			pure_filebody = pure_filename[:-10]
			numberstring  = pure_filename[-9:-4]

			if pure_filebody == filebody:
				numbers.append(int(numberstring))
				filearray.append(filepath + allfiles[i])

	min_number = np.min(numbers); max_number = np.max(numbers)
	filearray.sort(); numbers.sort()
	#print ("MIN: " + str(min_number) + "   MAX: " + str(max_number))
	return (min_number, max_number, filearray, numbers)