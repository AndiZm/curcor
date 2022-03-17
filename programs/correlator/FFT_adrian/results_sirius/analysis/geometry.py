import ephem
import os
from datetime import datetime, timezone
import numpy as np

##################
### TELESCOPES ###
##################
# We are going to cartesian coordinates with first telescope being positioned at (0,0,0)
T1 = [0,0,0]
T2 = [1.573, -0.767, 0.220]

# Define plane of incident light from star by normal vector from T1 in direction of star
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
	d = n_vec[0] * T2[0] + n_vec[1] * T2[1] + n_vec[2] * T2[2]
	# ... but here for d>0 light is incident on T2 first, therefore ...
	d  *= -1
	# Now, negative d means light is incident on T2 first, positive d means light is incident on T1 first
	return d

# Time delay between the two telescopes at any UTC time
def get_time_delay_azalt(az, alt):
	get_plane_vector(az, alt)
	d = get_distance()
	#print ("distance = {}".format(d))
	# Time difference
	t = d/299792458 # seconds
	return 1e9 * t # nanoseconds

#########################
### STAR CALCULATIONS ###
#########################
# Ephem parameters
sirius = ephem.star("Sirius")
ECAP_roof = ephem.Observer()
ECAP_roof.lat  = ephem.degrees("49.58068")
ECAP_roof.long = ephem.degrees("11.02771")

def get_params(file):
	f = open(file)
	header = f.readline().split(" ")
	ctime  = float(header[1])
	mean_1 = float(header[2])
	mean_2 = float(header[3])
	f.close()
	# Sirius coordinates
	time = datetime.utcfromtimestamp(ctime)
	ECAP_roof.date = ephem.date(time)
	sirius.compute(ECAP_roof)
	# Time delay between the telescopes
	tdiff = get_time_delay_azalt(sirius.az, sirius.alt)

	return mean_1, mean_2, tdiff