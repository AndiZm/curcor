import numpy as np
import matplotlib.pyplot as plt
from random import randrange
import random
import scipy.signal as sign
from os import listdir
from os.path import isfile, join
from tqdm import tqdm
import cupy

def scalarproduct(vec_1, vec_2):
	return np.sum(np.array(vec_1) * np.array(vec_2))

star = "Shaula"

# Define files to analyze and subpackages
folders   = [] # Data folders for analysis


# Open text file with measurement split data and read the data for the specific star
f = open("../analysis/measurement_chunks.txt")
# Find line for the star
line = f.readline()
while star not in line:
    line = f.readline()
# Fill arrays with the data
line = f.readline()
while "[end]" not in line:
    folders.append(line.split()[0])
    line = f.readline()
f.close()

for i in range(len(folders)):
	factor3s = np.loadtxt("data/{}_{}.txt".format(star, folders[i]))[:,0]
	factor4s = np.loadtxt("data/{}_{}.txt".format(star, folders[i]))[:,1]
	factorAs = np.loadtxt("data/{}_{}.txt".format(star, folders[i]))[:,2]
	factorBs = np.loadtxt("data/{}_{}.txt".format(star, folders[i]))[:,3]
	factor3Ax4Bs = np.loadtxt("data/{}_{}.txt".format(star, folders[i]))[:,4]
	factor4Ax3Bs = np.loadtxt("data/{}_{}.txt".format(star, folders[i]))[:,5]
	
	# Calculate average, mean and std of correction factor
	mean_factor3s = np.mean(factor3s)
	mean_factor4s = np.mean(factor4s)
	mean_factorAs = np.mean(factorAs)
	mean_factorBs = np.mean(factorBs)
	mean_factor3Ax4Bs = np.mean(factor3Ax4Bs)
	mean_factor4Ax3Bs = np.mean(factor4Ax3Bs)

	av_factor3s = np.std(factor3s)
	av_factor4s = np.std(factor4s)
	av_factorAs = np.std(factorAs)
	av_factorBs = np.std(factorBs)
	av_factor3Ax4Bs = np.std(factor3Ax4Bs)
	av_factor4Ax3Bs = np.std(factor4Ax3Bs)


	err_factor3s = np.std(factor3s) / np.sqrt(len(factor3s))
	err_factor4s = np.std(factor4s) / np.sqrt(len(factor3s))
	err_factorAs = np.std(factorAs) / np.sqrt(len(factor3s))
	err_factorBs = np.std(factorBs) / np.sqrt(len(factor3s))
	err_factor3Ax4Bs = np.std(factor3Ax4Bs) / np.sqrt(len(factor3s))
	err_factor4Ax3Bs = np.std(factor4Ax3Bs) / np.sqrt(len(factor3s))


	mean_all = [ mean_factor3s, mean_factor4s, mean_factorAs, mean_factorBs, mean_factor3Ax4Bs, mean_factor4Ax3Bs ]
	av_all = [av_factor3s, av_factor4s, av_factorAs, av_factorBs, av_factor3Ax4Bs, av_factor4Ax3Bs]
	err_all = [err_factor3s, err_factor4s, err_factorAs, err_factorBs, err_factor3Ax4Bs, err_factor4Ax3Bs]

	np.savetxt("data/{}_{}_ana.txt".format(star, folders[i]), np.c_[mean_all, av_all, err_all], header="down: 3, 4, A, B, 3Ax4B, 4Ax3B; right: mean, std, error", fmt='%.4f')
