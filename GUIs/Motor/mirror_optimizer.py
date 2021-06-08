import rate_client as rcl
print("IMPORT1")
import scipy.optimize as opt

print("IMPORT2")

def dummy():
	print("dummy")
#all methods definied in this package take controll of the motors and try to optimze the rate by adjusting the motor-positions

#this method bluntly uses a scipy optimizer to find the optimal parameters for each motor (all motors, no accounting for limited dof)
def optimizeAllBluntly(client):

	if client == None:
		print("No rate Server connected. The rate can not be optimzied witout knowing the rate!")
		return

	#stop all current movements of the motors
	from stepper_gui import (stop_all, center_camera, center_mirror_pos, center_mirror_angle)
	stop_all()
	
	#set all motors to center position
	center_camera()
	center_mirror_pos()
	center_mirror_angle()
	
	#run an optimizer on the setup
	res=opt.minimize(testState, [gui.mirror_height_pos, gui.mirror_z_pos, gui.mirror_phi_pos, gui.mirror_psi_pos, gui.camera_x_pos, gui.camera_z_pos, client])
	print("Optimal Position was found to be: {0}".format(res))

def optimizeBluntlyNoHeight(client):

	from stepper_gui import (stop_all, center_camera, center_mirror_pos, center_mirror_angle)
	print("Bluntly")
	
	if client == None:
			print("No rate Server connected. The rate can not be optimzied witout knowing the rate!")
			return

	#stop all current movements of the motors
	stop_all()
	
	#set all motors to center position
	center_camera()
	#gui.center_mirror_pos()
	center_mirror_angle()
	
	#run an optimizer on the setup
	res=opt.minimize(testStateNoHeight, [gui.mirror_z_pos, gui.mirror_phi_pos, gui.mirror_psi_pos, gui.camera_x_pos, gui.camera_z_pos, client])
	print("Optimal Position was found to be: {0}".format(res))

def testState(mirror_height, mirror_z, mirror_phi, mirror_psi, camera_x, camera_z, client):
	from stepper_gui import (moveto_mirror_height, moveto_mirror_z, moveto_mirror_phi, moveto_camera_x, moveto_camera_z)

	moveto_mirror_height(mirror_height)
	moveto_mirror_z(mirror_z)
	moveto_mirror_phi(mirror_phi)
	moveto_mirror_psi(mirror_psi)
	moveto_camera_x(camera_x)
	moveto_camera_z(camera_z)
	return 1./client.getRateA()

def testStateNoHeight(mirror_z, mirror_phi, mirror_psi, camera_x, camera_z, client):
	from stepper_gui import(moveto_mirror_z, moveto_mirror_phi, moveto_camera_x, moveto_camera_z)

	moveto_mirror_z(mirror_z)
	moveto_mirror_phi(mirror_phi)
	moveto_mirror_psi(mirror_psi)
	moveto_camera_x(camera_x)
	moveto_camera_z(camera_z)
	return 1./client.getRateA()