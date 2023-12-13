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
ct13 = np.subtract(ct3, ct1)
ct14 = np.subtract(ct4, ct1)
ct34 = np.subtract(ct4, ct3)

# Define plane of incident light from star by normal vector from the telescopes in direction of star
# For the baseline, we define the plane perpendicular to that one
n_vec   = [] # for the optical path delay
def get_plane_vector(az,alt):
	global n_vec
	phi = np.pi - az

	# -- First for the optical path delay -- #
	x = + np.sin(phi)
	y = - np.cos(phi)
	z = + np.tan(alt)
	# Normalize normal vector
	length = np.sqrt(x**2+y**2+z**2)
	x /= length; y /= length; z /= length
	n_vec = [x,y,z]


# Calculate distance of point T2 to plane == distance difference of travelled light
def get_distance():
	# Distance is scalar product of normal vector and T2 vector
	d13 = -1 * np.dot(n_vec, ct13)
	d14 = -1 * np.dot(n_vec, ct14)
	d34 = -1 * np.dot(n_vec, ct34)
	# ... but here for d>0 light is incident on T2 first, therefore the -1
	# Now, negative d means light is incident on T2 first, positive d means light is incident on T1 first
	return d13, d14, d34

# Calculate the projected baseline
def get_baseline():

	# Projection of vector onto plane
	# Start with the projection of a vector onto the norm vector
	proj_13 = np.multiply( np.dot(ct13, n_vec),n_vec )
	proj_14 = np.multiply( np.dot(ct14, n_vec),n_vec )
	proj_34 = np.multiply( np.dot(ct34, n_vec),n_vec )
	# The projection onto the plane is the vector minus the projection
	projP_13 = np.subtract(ct13, proj_13)
	projP_14 = np.subtract(ct14, proj_14)
	projP_34 = np.subtract(ct34, proj_34)
	# normalize
	b13 = np.linalg.norm(projP_13)
	b14 = np.linalg.norm(projP_14)
	b34 = np.linalg.norm(projP_34)
	
	return b13, b14, b34

# Time delay between the two telescopes at any UTC time
def get_time_delay_azalt(az, alt):
	get_plane_vector(az, alt)
	d = get_distance()
	b = get_baseline()
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


# 3 Telescopes

def get_params3T(time, starname, telcombi):
	# Star coordinates
	the_star = ephem.star(starname)
	hess.date = ephem.date(time)

	the_star.compute(hess)
	# Time delay between the telescopes
	tdiff = get_time_delay_azalt(the_star.az, the_star.alt)[get_baseline_entry(telcombi)]

	return tdiff, 180*the_star.az/np.pi, 180*the_star.alt/np.pi

def get_params_manual3T(time, ra, dec, telcombi):
	# Star coordinates
	the_star = ephem.FixedBody()
	the_star._ra  = ephem.hours("{}:{}:{}".format(ra[0],ra[1],ra[2]))
	the_star._dec = ephem.degrees("{}:{}:{}".format(dec[0],dec[1],dec[2]))
	hess.date = ephem.date(time)

	the_star.compute(hess)
	# Time delay between the telescopes
	tdiff = get_time_delay_azalt(the_star.az, the_star.alt)[get_baseline_entry(telcombi)]

	return tdiff, 180*the_star.az/np.pi, 180*the_star.alt/np.pi