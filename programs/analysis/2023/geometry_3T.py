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

# We are going to cartesian coordinates
# HESS coordinates (already transfered so that x is west -> east and y is south -> north)
ct1 = [ 85.04, -0.16,  0.97]
ct2 = [  0.37, 85.07,  0.33]
ct3 = [-85.04,  0.24, -0.82]
ct4 = [ -0.28,-85.04, -0.48]
# with these four telescope vectors we build the list of vectors
# we add an additional nan as 0th element, so that we can attribute each index with the corresponding telescope
ct_locs = [[np.nan], ct1, ct2, ct3, ct4]
# Now we can build the matrix of 3D-telescope seperations
# Each entry is the 3D seperation vector
teldiffs = np.zeros((5,5), dtype=object)
for i in range (1,5):
	for j in range (1,5):
		teldiffs[i][j] = np.subtract(ct_locs[j], ct_locs[i])

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

# Calculate distance of telescope T2 to plane == distance difference of travelled light
def get_distance(telcombi):
	# Distance is scalar product of normal vector and T2 vector
	d = -1 * np.dot(n_vec, teldiffs[telcombi[0]][telcombi[1]])
	# ... but here for d>0 light is incident on T2 first, therefore the -1
	# Now, negative d means light is incident on T2 first, positive d means light is incident on T1 first
	return d

# Calculate the projected baseline
def get_baseline(telcombi):
	# Projection of vector onto plane
	# Start with the projection of a vector onto the norm vector
	proj  = np.multiply( np.dot(teldiffs[telcombi[0]][telcombi[1]], n_vec),n_vec )
	# The projection onto the plane is the vector minus the projection
	projP = np.subtract( teldiffs[telcombi[0]][telcombi[1]], proj)
	# normalize
	b = np.linalg.norm(projP)	
	return b

# Time delay between the two telescopes at any UTC time
def get_time_delay_azalt(az, alt, telcombi):
	get_plane_vector(az, alt)
	d = get_distance(telcombi)
	b = get_baseline(telcombi)
	# Time difference
	t = 1e9*d/299792458 # nanoseconds
	return t,b # nanoseconds

#########################
### STAR CALCULATIONS ###
#########################
# Ephem parameters
hess = ephem.Observer()
hess.lat  = ephem.degrees("-23.271778")
hess.long = ephem.degrees(" 16.50022")

def get_params3T(time, starname, telcombi):
	
	# Star coordinates
	the_star = ephem.star(starname)
	hess.date = ephem.date(time)

	the_star.compute(hess)
	# Time delay between the telescopes
	tdiff, baseline = get_time_delay_azalt(the_star.az, the_star.alt, telcombi)

	return tdiff, baseline, 180*the_star.az/np.pi, 180*the_star.alt/np.pi

def get_params_manual3T(time, ra, dec, telcombi):
	# Star coordinates
	the_star = ephem.FixedBody()
	the_star._ra  = ephem.hours("{}:{}:{}".format(ra[0],ra[1],ra[2]))
	the_star._dec = ephem.degrees("{}:{}:{}".format(dec[0],dec[1],dec[2]))
	hess.date = ephem.date(time)

	the_star.compute(hess)
	# Time delay between the telescopes
	tdiff, baseline = get_time_delay_azalt(the_star.az, the_star.alt, telcombi)

	return tdiff, baseline, 180*the_star.az/np.pi, 180*the_star.alt/np.pi