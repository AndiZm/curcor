import numpy as np
#######################################################################
#                                                                     #
#   The definition of the coordinate system as used here is:          #
#        (Perspective from above)                                     #
#           _____________________________________________             #
#          |                                             |            #
#          |                                             |            #
#          |                                             |            #
#          |                                             |   ^        #
#          |                                             |   |        #
#        ^ |                                             |  x_len     #
# X-AXIS | |                                             |   |        #
#        - |-->Z-AXIS             X                      |   V        #
#          |                                             |            #
#          |                                             |            #
#          |                                             |            #
#          |                                             |            #
#          |                                             |            #
#          |               <-- z_len -->                 |            #
#          |_____________________________________________|            #
#                                                                     #
#          - OUT OF THE PLANE: Y-AXIS   Zero defined @ LID            #
#          - The "X"-symbol marks the theoretically correct           #
#            focal spot of the telescope                              #
#            (coordinates x=0, y=0, z=z_len/2)                        #
#          - all values used here are given in mm                     #
#                                                                     #
#                                                                     #
#######################################################################

#as defined in the sketch
x_len=500
z_len=640

#offset values of the focal spot in relation to the setup (due to imprecisions in the mounting of the setup)
#these values are determined experimentally and then inserted here
offset_center_x=0
offset_center_y=0
offset_center_z=0

#calculate the position of the center according to the parameters that we inserted before
center_z=z_len/2+offset_center_z
center_y=offset_center_y
center_x=offset_center_x

#constants due to the geometry of the telescope
dish_focal_length=1500 #focal length of the dish. Is the same as the distance between the lid and a hypothetical mirror in the middle of the dish
dish_diameter=1300 # diamter of the dish

#constants of the setup
lens_focal_length=100 #focal length of the lens used in the optics to parralelize the light
lens_center_offset_y=128 #height of the lens-center above the lid
#dummy
mirror_ball_offset_x=20 #x position of the ball around which the mirror can be rotated
mirror_ball_offset_y=20 #y position of the ball around which the mirror can be rotated. Relative to the upper edge of the labjack
mirror_ball_offset_z=20 #z position of the ball around which the mirror can be rotated. Relative to the nominal position of the mirror-sled
mirror_ball_seperation=80 #length of the vector orthogonal to the plane


#returns the incidence angle of the central ray with respect to the normal vector of the lens plane (in degrees)
def getIncidentAngle(mirror_phi, mirror_psi):
	#convert angles so that they are given in the right frame of reference and units (radians)
	psi=np.pi/2-2*(mirror_psi/180*np.pi)
	phi=np.pi/2-2*(mirror_phi/180*np.pi)
	return 90-np.arctan(1/np.sqrt(np.tan(psi)**(-2)+np.tan(phi)**(-2)))/np.pi*180

#returns the height at which the central ray hits the mirror
def get_mirror_incidence_height(mirror_phi, mirror_psi, mirror_height, mirror_z, camera_z):
	#calculate at what height above the focal plane (=lid) the mirror is hit by the central ray
	#Assumptions: The central ray hits the setup perpandicularly on the focal point, as marked in the sketch
	ball_position=np.array([mirror_ball_offset_x, mirror_ball_offset_y+mirror_height, mirror_ball_offset_z+mirror_z]) #3D vector which marks the center of the ball
	#calculate the two vectors that span the mirror plane
	direction_psi=np.array([0,1,0]) #first define the non-rotated vector in an easier reference frame
	direction_phi=np.array([1,0,0]) #first define the non-rotated vector in an easier reference frame
	#now rotate both vectors using a rotation matrix first assume that PSI rotates aroud the x-axis and PHI around the y-axis
	rotation_psi=np.array( [[1,0,0],
							[0,np.cos(mirror_psi/180*np.pi),-np.sin(mirror_psi/180*np.pi)],
							[0,np.sin(mirror_psi/180*np.pi), np.cos(mirror_psi/180*np.pi)]]))
	rotation_phi=np.array( [[np.cos(mirror_phi/180*np.pi),0,np.sin(mirror_phi/180*np.pi)],
							[0,1,0],
							[-np.sin(mirror_phi/180*np.pi),0,np.cos(mirror_phi/180*np.pi)]]))
	#rotate the whole plane in the correct reference frame
	rotation_frame=np.array([[1,0,0],
							[0,np.cos(np.pi/4),-np.sin(np.pi/4)],
							[0,np.sin(np.pi/4), np.cos(np.pi/4)]]))
	#finally execute matrix operations
	direction_psi=rotation_frame @ rotation_psi @ direction_psi
	direction_phi=rotation_frame @ rotation_phi @ direction_phi
	#calculate a point in the plane by extending the ball-point othogonally towards the mirror plane
	#calculate cross-product of the span to get a vector which is orthogonal to the plane
	cross=direction_psi @ direction_phi
	#extend the calculated vector to the length that lies between ball and plane
	current_length=np.sqrt(cross[0]**2+cross[1]**2+cross[2]**2)
	factor=mirror_ball_seperation/current_length
	point_in_mirror_plane=ball_position+cross*factor #add the ball-point and the orthogonal vector to get the uppoint of the plane
	#the plane is now defined by point_in_mirror_plane and the thwo vectors direction_psi, diection_phi
	#
	#	We describe this whole mess as the following set of equations:
	#	point_in_mirror_plane + lambda * direction_psi + gamma * direction_phi = center + alpha * (0, 1, 0)
	#
	#now calculate at which point the central ray and the mirror-plane intersect each other
	beta=(center_z-point_in_mirror_plane[2]-(center_x/direction_psi[0])+(point_in_mirror_plane[0]/direction_psi[0]))/(direction_phi[2]-direction_phi[0])
	lambda_=(center_x-beta*direction_phi-point_in_mirror_plane[0])/direction_psi[0]
	return point_in_mirror_plane[1]+lambda_*direction_psi[1]+beta*direction_phi[1]

#returns the difference in the pathlenght fri 
def getPathLengthDelta(mirror_phi, mirror_psi, mirror_height, mirror_z, camera_z, shift):
	#first get the height at which the central ray hits the mirror
	height=get_mirror_incidence_height(mirror_phi, mirror_psi, mirror_height, mirror_z, camera_z)
	#calculate the distance between the mirror incidence point and the lens plane
	distance=1 #dummy
	#return the difference from the originaly choosen pathlength
	return distance-height-shift
	
	
	
#returns a calculated distance which quantifies the distance between the incident ray hitting the lens plane and the center of the lens
def ray_dist_from_center(mirror_phi, mirror_psi, mirror_height, mirror_z, camera_z, camera_x):
	return 100. 
	
	
	
	
	
