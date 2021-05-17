import rate_client as rcl
import stepper_gui as gui #is this really needed?
import scipy.optimize as opt

#all methods definied in this package take controll of the motors and try to optimze the rate by adjusting the motor-positions

#this method bluntly uses a scipy optimizer to find the optimal parameters for each motor (all motors, no accounting for limited dof)
def optimizeAllBluntly():

	if gui.client == None:
		print("No rate Server connected. The rate can not be optimzied witout knowing the rate!")
		return

	#stop all current movements of the motors
	gui.stop_all()
	
	#set all motors to center position
	gui.center_camera()
	gui.center_mirror_pos()
	gui.center_mirror_angle()
	
	#run an optimizer on the setup
	res=opt.minimize(testState, [gui.mirror_height_pos, gui.mirror_z_pos, gui.mirror_phi_pos, gui.mirror_psi_pos, gui.camera_x_pos, gui.camera_z_pos])
	print("Optimal Position was found to be: {0}".format(res))
	
def testState(mirror_height, mirror_z, mirror_phi, mirror_psi, camera_x, camera_z):
	gui.moveto_mirror_height(mirror_height)
	gui.moveto_mirror_z(mirror_z)
	gui.moveto_mirror_phi(mirror_phi)
	gui.moveto_mirror_psi(mirror_psi)
	gui.moveto_camera_x(camera_x)
	gui.moveto_camera_z(camera_z)
	return 1./gui.client.getRateA()
	
