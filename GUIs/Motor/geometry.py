import numpy as np
import configparser
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
#          - all calculations here are performed in the               #
#            frame of reference of the setup. If anything             #
#            is ever shifted, it is the incoming light,               #
#            which comes from another FOR                             #
#                                                                     #
#                                                                     #
#######################################################################

#as defined in the sketch
x_len=500
z_len=640

#initialization sequence

#read all required parameters from the config file
#check if config file exists and load it, otherwise standard parameters are kept
motor_pc_no = None
this_config = configparser.ConfigParser()
this_config.read('../../../this_pc.conf')
if "who_am_i" in this_config:
	if this_config["who_am_i"]["type"]!="motor_pc":
		print("According to the 'this_pc.config'-file this pc is not meant as a motor pc! Please fix that!")
		exit()
	motor_pc_no = int(this_config["who_am_i"]["no"])
	print("Motor PC no is {}".format(motor_pc_no))
else:
	print("There is no config file on this computer which specifies the computer function! Please fix that!")
	exit()
global_config = configparser.ConfigParser()
global_config.read('../global.conf')
if "motor_pc_{}".format(motor_pc_no) in global_config:
	if motor_pc_no==1 or motor_pc_no==2:
		#offset values of the focal spot in relation to the setup (due to imprecisions in the mounting of the setup)
		#these values are determined experimentally and then inserted here
		offset_center_x=float(global_config["motor_pc_{}".format(motor_pc_no)]["offset_center_x"])
		offset_center_y=float(global_config["motor_pc_{}".format(motor_pc_no)]["offset_center_y"])
		offset_center_z=float(global_config["motor_pc_{}".format(motor_pc_no)]["offset_center_z"])

		#calculate the position of the center according to the parameters that we inserted before
		center_z=z_len/2+offset_center_z
		center_y=offset_center_y
		center_x=offset_center_x

		#constants due to the geometry of the telescope
		dish_focal_length=15000 #focal length of the dish. Is the same as the distance between the lid and a hypothetical mirror in the middle of the dish
		dish_diameter=13000 # diamter of the dish

		#constants of the setup
		lens_focal_length=float(global_config["motor_pc_{}".format(motor_pc_no)]["lens_focal_lenght"]) #focal length of the lens used in the optics to parralelize the light
		lens_center_offset_y=float(global_config["motor_pc_{}".format(motor_pc_no)]["lens_center_offset_y"]) #height of the lens-center above the lid
		lens_center_offset_z=float(global_config["motor_pc_{}".format(motor_pc_no)]["lens_center_offset_z"]) #dislpacement of the lens center relative to the middle of its carriage
		mirror_ball_offset_x=float(global_config["motor_pc_{}".format(motor_pc_no)]["mirror_ball_offset_x"]) #x position of the ball around which the mirror can be rotated
		mirror_ball_offset_y=float(global_config["motor_pc_{}".format(motor_pc_no)]["mirror_ball_offset_y"]) #y position of the ball around which the mirror can be rotated. Relative to the upper edge of the labjack
		mirror_ball_offset_z=float(global_config["motor_pc_{}".format(motor_pc_no)]["mirror_ball_offset_z"]) #z position of the ball around which the mirror can be rotated. Relative to the nominal position of the mirror-sled
		mirror_ball_seperation=float(global_config["motor_pc_{}".format(motor_pc_no)]["mirror_ball_seperation"]) #length of the vector orthogonal to the plane
	else:
		print("Error in the 'this_pc.config'-file. The number of the Motor PC is neither 1 nor 2. Please correct!")
		exit()
else:
	print("Error in the 'this_pc.config'-file. Section the Motor PC is missing!")
	exit()
print("Initalized geometry for Motor PC / Setup {}".format(motor_pc_no))
        



#returns the incidence angle of the central ray with respect to the normal vector of the lens plane (in degrees) //DOES NOT YET CONSIDER THE ACTUAL ANGLE OF THE INCOMING LIGHT
def getIncidentAngle(mirror_phi, mirror_psi):
	#convert angles so that they are given in the right frame of reference and units (radians)
	psi=np.pi/2-2*(mirror_psi/180*np.pi)
	phi=np.pi/2-2*(mirror_phi/180*np.pi)
	return 90-np.arctan(1/np.sqrt(np.tan(psi)**(-2)+np.tan(phi)**(-2)))/np.pi*180
	
#returns the point at which the central ray hits the mirror
def get_mirror_incidence_point(mirror_phi, mirror_psi, mirror_height, mirror_z, debug=False):
	print("Calculate mirror incidence height for mirr_phi={0}, mirr_psi={1}, mirr_height={2}, mirr_z={3}".format(mirror_phi, mirror_psi, mirror_height, mirror_z))
	#calculate at what height above the focal plane (=lid) the mirror is hit by the central ray
	#Assumptions: The central ray hits the setup perpendicularly on the focal point, as marked in the sketch
	plane_point, direction_psi, direction_phi = get_mirror_plane(mirror_phi, mirror_psi, mirror_height, mirror_z)
	if debug:
		print("*************************************************************")
		print("Calculation of the mirror incidence height")
		print("  Calculate parameters of the mirror plane:")
		print("     Vector of direction (plane) PSI:  {}".format(direction_psi))
		print("     Vector of direction (plane) PHI:  {}".format(direction_phi))
	#calculate a point in the plane by extending the ball-point orthogonally towards the mirror plane
	#calculate cross-product of the span to get a vector which is orthogonal to the plane
	if debug:
		print("    Position of the tilt ball:  {}".format(point_in_mirror_plane))
		print("  The full plane can now be written as:")
		print("      {0} + a * {1} + b * {2}:".format(point_in_mirror_plane, direction_psi, direction_phi))
		print("  Now find intersection of the plane and a ray comming centrally at the setup:")
		print("    Solve system of linear equations:")
	#now calculate at which point the central ray and the mirror-plane intersect each other
	plane_point = point_in_mirror_plane
	plane_dir1 = direction_phi
	plane_dir2 = direction_psi
	ray_point, ray_dir = get_incoming_ray()
	return ray_intersects_plane(plane_point, plane_dir1, plane_dir2, ray_point, ray_dir)
	
#returns the incidence point on the mirror plane /// STILL needs to be tested
def get_lens_incidence_point(mirror_phi, mirror_psi, mirror_height, mirror_z, camera_z, camera_x):
	#get the reflected central ray after the mirror
	mirror_plane_point, mirror_plane_dir1, mirror_plane_dir1 = get_mirror_plane(mirror_phi, mirror_psi, mirror_height, mirror_z)
	incoming_ray_point , incoming_ray_dir = get_incoming_ray()
	refelected_ray_point, reflected_ray_dir = mirror_ray_on_plane(mirror_plane_point, mirror_plane_dir1, mirror_plane_dir2, incoming_ray_point, incoming_ray_dir)
	#calculate where the ray hits the lens plane
	lens_plane_point, lens_plane_dir1, lens_plane_dir2 = get_lens_plane(camera_z, camera_x)
	lens_hit_point = ray_intersects_plane(lens_plane_point, lens_plane_dir1, lens_plane_dir2, refelected_ray_point, refelected_ray_dir)
	return lens_hit_point

#returns the difference in the pathlenght. It assumes an about perpendcular incoming central ray // STILL needs to be tested
def getPathLengthDelta(mirror_phi, mirror_psi, mirror_height, mirror_z, camera_z, camera_x, shift=0):
	#get the point where the mirror hits the mirror
	mirror_incidence_point = get_mirror_incidence_point(mirror_phi, mirror_psi, mirror_height, mirror_z)
	#get the incidence point on the lens plane
	lens_incidence_point = get_lens_incidence_point(mirror_phi, mirror_psi, mirror_height, mirror_z, camera_z, camera_x)
	#calculate the distance betwee the lens_hit point and the mirror_hit point
	point_to_point=np.sqrt(np.sum((lens_incidence_point-mirror_incidence_point)**2))
	pathlength_delta=point_to_point-mirror_incidence_point[1]+shift
	#return the difference from the originaly choosen pathlength
	return pathlength_delta
	
#returns the distance between the point where the calculated central ray hits the mirror plane and the center of the lens as a 2D array for both dimensions /// STILL needs to be tested 
def get_diff_hit_lens(mirror_phi, mirror_psi, mirror_height, mirror_z, camera_z):
	#get incidence point of the ray in the mirror plane
	lens_incidence_point = get_lens_incidence_point(mirror_phi, mirror_psi, mirror_height, mirror_z, camera_z, camera_x)
	center_of_lens = get_lens_center(camera_z, camera_x)
	return np.sqrt(np.sum((lens_incidence_point-center_of_lens)**2))

#returns the abolute coordinates of the lens-fronts center
def get_lens_center(camera_z, camera_x):
	return np.array([camera_x,lens_center_offset_y,camera_z+lens_center_offset_z])


#the following stuff is mainly internal for this package
	
#returns the point at which a ray pentrates a plane.
def ray_intersects_plane(plane_point, plane_dir1, plane_dir2, ray_point, ray_dir, debug=False):
	#rename all the stuff to make our equations shorter
	p=plane_point
	x=plane_dir1
	y=plane_dir2
	q=ray_point
	z=ray_dir
	#the equation to solve is now given as p+a*x+b*y=c*z+q
	#using the first two dimensions of our vectors we can find an equation for a=c*alpha+beta with
	alpha=(z[0]-(z[1]*y[0])/y[1])/(x[0]-x[1]*y[0]/y[1])
	beta=(q[0]-p[0]-(q[1]-q[1])/y[1]*y[0])/(x[0]-x[1]*y[0]/y[1])
	#using the first two dimensions of our vectors we can find also an equation for b=c*gamma+epsilon with
	gamma=(z[1]-z[0]*x[1]/x[0])/(y[1]-y[0]*x[1]/x[0])
	epsilon=(q[1]-p[1]-(q[0]-p[0])/x[0]*x[1])/(y[1]-y[0]*x[1]/x[0])
	#from the third dimension we get an expression for c that can be calculated from the paramenters and alpha, beta, gamma, epsilon
	c=(p[2]-q[2]+beta*x[2]+epsilon*y[2])/(z[2]-alpha*x[2]-gamma*y[2])
	#now plugging c into the right hand side of the equation yields
	point_right=c*z+q
	#doing the same for our left hand side, we first need to calculate a and b and then plug them into the equation
	if debug:
		a=c*alpha+beta
		b=c*gamma+epsilon
		point_left=p+a*x+b*y
		print("Point right = {0}".format(point_right))
		print("Point left  = {0}".format(point_left))
	#obviously those two should be about the same
	return point_right
	
#returns the ray as it is mirrored by the plane (first point, second direction vector)
def mirror_ray_on_plane(plane_point, plane_dir1, plane_dir2, ray_point, ray_dir):
	#find the point of the new ray by using the intersection 
	new_ray_point = ray_intersects_plane(plane_point, plane_dir1, plane_dir2, ray_point, ray_dir)
	#calculate the normed normal vector of the plane
	normal_vec = np.cross(plane_dir1, plane_dir2)
	normal_vec = normal_vec/np.sqrt(np.sum((normal_vec)**2))
	#create an auxilary line that is perpendicular to the plane and intersect it with the plane
	aux_line_vec = normal_vec
	aux_line_point = ray_point
	aux_plane_intersection = ray_intersects_plane(plane_point, plane_dir1, plane_dir2, aux_line_point, aux_line_vec)
	#calculate distance between point of the ray and its projection on the plane
	distance = point_to_point=np.sqrt(np.sum((aux_plane_intersection-ray_point)**2))
	#calculate mirror point of the ray point
	#check the direction of the normal vector
	multi=2
	if np.sqrt(np.sum(((ray_point + multi * distance * normal_vec)-aux_plane_intersection)**2))>0.01:
		multi=-2
	mirror_point = ray_point + multi * distance * normal_vec
	new_ray_vector=(mirror_point-new_ray_point)/(np.sqrt(np.sum((mirror_point-new_ray_point)**2)))
	return (new_ray_point,new_ray_vector)
	
#calculates the vector parametrization of the plane from the inserted state of the setup
def get_mirror_plane(mirror_phi, mirror_psi, mirror_height, mirror_z):
	ball_position=np.array([mirror_ball_offset_x,
	mirror_ball_offset_y+mirror_height,
	mirror_ball_offset_z+mirror_z]) #3D vector which marks the center of the ball
	#calculate the two vectors that span the mirror plane
	direction_psi=np.array([0,1,0]) #first define the non-rotated vector in an easier reference frame
	direction_phi=np.array([1,0,0]) #first define the non-rotated vector in an easier reference frame
	#now rotate both vectors using a rotation matrix first assume that PSI rotates aroud the x-axis and PHI around the y-axis
	rotation_psi=np.array( [[1,0,0],
							[0,np.cos(mirror_psi/180*np.pi),-np.sin(mirror_psi/180*np.pi)],
							[0,np.sin(mirror_psi/180*np.pi), np.cos(mirror_psi/180*np.pi)]])
	rotation_phi=np.array( [[np.cos(mirror_phi/180*np.pi),0,np.sin(mirror_phi/180*np.pi)],
							[0,1,0],
							[-np.sin(mirror_phi/180*np.pi),0,np.cos(mirror_phi/180*np.pi)]])
	#rotate the whole plane in the correct reference frame
	rotation_frame=np.array([[1,0,0],
							[0,np.cos(np.pi/4),-np.sin(np.pi/4)],
							[0,np.sin(np.pi/4), np.cos(np.pi/4)]])
	direction_psi=rotation_frame @ rotation_psi @ direction_psi
	direction_phi=rotation_frame @ rotation_phi @ direction_phi
	#calculate the point in the mirror plane using the normal vector, the coordinates of the ball and the planes distance from the ball
	cross=np.cross(direction_psi, direction_phi)
	current_length=np.sqrt(cross[0]**2+cross[1]**2+cross[2]**2)
	factor=mirror_ball_seperation/current_length
	point_in_mirror_plane=ball_position+cross*factor #add the ball-point and the orthogonal vector to get the uppoint of the plane
	return point_in_mirror_plane, direction_psi, direction_phi
	
#returns a vector parametrization of the incoming ray (point, dir)
def get_incoming_ray():
	ray_point=np.array([center_x,0,center_z])
	ray_dir=np.array([0,1,0])
	return ray_point, ray_dir
	
#returns the plane of the lens (point, dir1, dir2) where "point" is also the center of the lens
def get_lens_plane(camera_z, camera_x):
	lens_center=get_lens_center(camera_z, camera_x)
	dir_1=np.array([1,0,0])
	dir_2=np.array([0,1,0])
	return lens_center, dir_1, dir_2
