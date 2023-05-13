import ephem
import os
from datetime import datetime, timezone
import numpy as np

def get_baseline_entry(telcombi):
    if telcombi == "13":
        return int(0)
    elif telcombi == "14":
        return int(1)
    elif telcombi == "34":
        return int(2)

# We are going to cartesian coordinates with first telescope being positioned at (0,0,0)
# HESS coordinates (already transfered so that x is west-east and y is south-north)
# ct1 = [ 85.04, -0.16,  0.97]
# ct3 = [-85.04,  0.24, -0.82]
# ct4 = [-0.28, -85.04, -0.48]

# But we set ct3 to zero and calculate relative coordinates for ct1 and ct4
ct1 = [170.08, -0.4, 1.79]
ct3 = [0., 0., 0.]
ct4 = [84.76, -85.28, 0.34]

# Difference vectors
ct13 = [-170.08, 0.4, -1.79]
ct14 = [-85.32, -84.88, -1.45]
ct34 = [84.76, -85.28, 0.34]

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
	d13 = -1 * ( n_vec[0] * ct13[0] + n_vec[1] * ct13[1] + n_vec[2] * ct13[2] )
	d14 = -1 * ( n_vec[0] * ct14[0] + n_vec[1] * ct14[1] + n_vec[2] * ct14[2] )
	d34 = -1 * ( n_vec[0] * ct34[0] + n_vec[1] * ct34[1] + n_vec[2] * ct34[2] )
	# ... but here for d>0 light is incident on T2 first, therefore the -1
	# Now, negative d means light is incident on T2 first, positive d means light is incident on T1 first
	return d13, d14, d34

# Time delay between the two telescopes at any UTC time
def get_time_delay_azalt(az, alt):
	get_plane_vector(az, alt)
	d = get_distance()
	#print ("Distance " + str(d))
	#print ("distance = {}".format(d))
	# Time difference
	t = []
	t.append(1e9*d[0]/299792458) # nanoseconds
	t.append(1e9*d[1]/299792458) # nanoseconds
	t.append(1e9*d[2]/299792458) # nanoseconds
	return t # nanoseconds

#########################
### STAR CALCULATIONS ###
#########################
# Ephem parameters
#the_star = ephem.star("Shaula")

hess = ephem.Observer()
hess.lat  = ephem.degrees("-23.271778")
hess.long = ephem.degrees(" 16.50022")
#hess.date = ephem.now()

def get_params(file, starname, telcombi):
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
	tdiff = get_time_delay_azalt(the_star.az, the_star.alt)[get_baseline_entry(telcombi)]

	return tdiff, mean_1, mean_2, mean_3, mean_4, 180*the_star.az/np.pi, 180*the_star.alt/np.pi, time

def get_params_manual(file, ra, dec, telcombi):
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
	tdiff = get_time_delay_azalt(the_star.az, the_star.alt)[get_baseline_entry(telcombi)]

	return tdiff, mean_1, mean_2, mean_3, mean_4, 180*the_star.az/np.pi, 180*the_star.alt/np.pi, time