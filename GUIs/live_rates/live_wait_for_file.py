import time
from os import listdir
from os.path import isfile, join
import os
import numpy as np
import globals as gl

def execute(basicpath, samples):

	gl.lastfiletime = 1e9*time.time()
	while(gl.stop_wait_for_file_thread == False):
		# Search if new files are available
		current_files = [f for f in listdir(basicpath) if isfile(join(basicpath, f))]    
		newfiles = []; modified = []; new = False
		for i in range (0, len(current_files)):
			cfile = basicpath + "/" + current_files[i]
			if os.stat(cfile).st_mtime_ns > gl.lastfiletime and os.stat(cfile).st_size >= (2*samples) and cfile[-4:] == ".bin":
				newfiles.append(cfile); modified.append(os.stat(cfile).st_mtime_ns)
				new = True
		# Find newest file and analyze
		if new == True:
			newest_file = newfiles[np.argmax(modified)]
			gl.lastfiletime = os.stat(newest_file).st_mtime_ns
			new = False
			return newest_file
			break

		#time.sleep(0.5)

def execute_single(basicpath, samples):

	gl.lastfiletime = 1e9*time.time()
	while(gl.stop_wait_for_file_thread == False):
		# Search if new files are available
		current_files = [f for f in listdir(basicpath) if isfile(join(basicpath, f))]    
		newfiles = []; modified = []; new = False
		for i in range (0, len(current_files)):
			cfile = basicpath + "/" + current_files[i]
			if os.stat(cfile).st_mtime_ns > gl.lastfiletime and os.stat(cfile).st_size >= (samples) and cfile[-4:] == ".bin":
				newfiles.append(cfile); modified.append(os.stat(cfile).st_mtime_ns)
				new = True
		# Find newest file and analyze
		if new == True:
			newest_file = newfiles[np.argmax(modified)]
			gl.lastfiletime = os.stat(newest_file).st_mtime_ns
			new = False
			return newest_file
			break

		#time.sleep(0.5)