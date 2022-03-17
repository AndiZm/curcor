import ephem
import os
from datetime import datetime, timezone
import numpy as np

# We are going to cartesian coordinates with first telescope being positioned at (0,0,0)
T1 = [0,0,0]
T2 = [1.573, -0.767, 0.220]


# Define plane of incident light from star by normal vector from T1 in direction of star
n_vec = []
# The normal vector has arbitrary length, the length in XY-Plane is set to 1 at beginning
#def get_plane_vector_old(az,alt):
#	global n_vec
#	phi = az - np.pi/2; print (180*phi/np.pi)
#	x = np.cos(phi)
#	y = np.sin(phi)
#	z = np.tan(alt)
#	# Normalize normal vector
#	length = np.sqrt(x**2+y**2+z**2)
#	x /= length; y /= length; z /= length
#	n_vec = [x,y,z]

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