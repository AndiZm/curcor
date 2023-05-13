import ephem
import os
from datetime import datetime, timezone
import numpy as np

# We are going to cartesian coordinates with first telescope being positioned at (0,0,0)
# HESS coordinates
# ct3 = [-85.04,  0.24, -0.82]
# ct4 = [-0.28, -85.04, -0.48]

# But we set ct3 to zero and calculate relative coordinates for ct4
ct3 = [0., 0., 0.]
ct4 = [84.76, -85.28, 0.34]

# Define plane of incident light from star by normal vector from CT3 in direction of star
n_vec = []
def get_plane_vector(az,alt):
	global n_vec
	phi = np.pi - az
	x = + np.sin(phi)
	y = - np.cos(phi)
	z = np.tan(alt)
	# Normalize normal vector
	length = np.sqrt(x**2+y**2+z**2)
	x /= length; y /= length; z /= length
	n_vec = [x,y,z]

# Calculate distance of point T2 to plane == distance difference of travelled light
def get_distance():
	# Distance is scalar product of normal vector and T2 vector
	d = n_vec[0] * ct4[0] + n_vec[1] * ct4[1] + n_vec[2] * ct4[2]
	# ... but here for d>0 light is incident on T2 first, therefore ...
	d  *= -1
	# Now, negative d means light is incident on T2 first, positive d means light is incident on T1 first
	return d

# Time delay between the two telescopes at any UTC time
def get_time_delay_azalt(az, alt):
	get_plane_vector(az, alt)
	d = get_distance()
	#print ("Distance " + str(d))
	#print ("distance = {}".format(d))
	# Time difference
	t = d/299792458 # seconds
	return 1e9 * t # nanoseconds

#########################
### STAR CALCULATIONS ###
#########################
# Ephem parameters
#the_star = ephem.star("Shaula")

hess = ephem.Observer()
hess.lat  = ephem.degrees("-23.271778")
hess.long = ephem.degrees(" 16.50022")
#hess.date = ephem.now()

def get_params(file, starname):
	# Open file
	f = open(file)
	# Read in header, which is the first line of the file
	header = f.readline().split(" ")
	ctime  = float(header[1])
	mean_1 = float(header[2])
	mean_2 = float(header[3])
	mean_3 = float(header[4])
	mean_4 = float(header[5])
	f.close()
	# Star coordinates
	the_star = ephem.star(starname)
	time = datetime.utcfromtimestamp(ctime)
	hess.date = ephem.date(time)

	the_star.compute(hess)
	# Time delay between the telescopes
	tdiff = get_time_delay_azalt(the_star.az, the_star.alt)

	return tdiff, mean_1, mean_2, mean_3, mean_4, 180*the_star.az/np.pi, 180*the_star.alt/np.pi, time

def get_params_manual(file, ra, dec):
	# Open file
	f = open(file)
	# Read in header, which is the first line of the file
	header = f.readline().split(" ")
	ctime  = float(header[1])
	mean_1 = float(header[2])
	mean_2 = float(header[3])
	mean_3 = float(header[4])
	mean_4 = float(header[5])
	f.close()
	# Star coordinates
	the_star = ephem.FixedBody()
	the_star._ra  = ephem.hours("{}:{}:{}".format(ra[0],ra[1],ra[2]))
	the_star._dec = ephem.degrees("{}:{}:{}".format(dec[0],dec[1],dec[2]))
	time = datetime.utcfromtimestamp(ctime)
	hess.date = ephem.date(time)

	the_star.compute(hess)
	# Time delay between the telescopes
	tdiff = get_time_delay_azalt(the_star.az, the_star.alt)

	return tdiff, mean_1, mean_2, mean_3, mean_4, 180*the_star.az/np.pi, 180*the_star.alt/np.pi, time