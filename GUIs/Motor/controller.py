import os
import stepper_drive as sd
import motor_switch as ms
import servo_test as servo

#this class contains everything that is needed to controll the motorboard
class CONTROLLER():

    def __init__(self):
        self.a=sd.init()  #stepper_drive
        ms.init()
        ms.motor_on()
        self.motoron = True
        self.servo_angle=0
        #initalize maximum positioning speed of the motors
        self.velocities = []
        for i in range (0,6):
            self.velocities.append(self.a[i].axis.max_positioning_speed)
        #initalize maximum acceleration
        self.acceleration = []
        for i in range (0,6):
            self.acceleration.append(self.a[i].get_axis_parameter(5))
        #initalize current  
        self.current = [] 
        for i in range (0, 6):
            self.current.append(self.n_to_i(self.a[i].get_axis_parameter(6)))
            
        #Umrechnung zwischen motor parametern und python
        self.microsteps_nano = 32
        self.microsteps_standa = 16
        self.offset_standa = 512000
        
    #maximum current of the motors
    # Current regulation
    def i_to_n(self, cur):
        if  cur < 0.06:
            #print("Cur < 0.06A, set to 0.06")
            return 0
        if cur > 1.92 :
            #print("Cur  > 1.92A, set to 1.92")
            return 255
        return (int(cur/0.06)*8)-1

    def n_to_i(self, num):
        if num > 255:
            #print("Num > 255")
            return 1.92
        return (int(num/8)+1)*0.06
    
    
    #some basic math
    
    def degree_to_mm(self, degree):
        return (8./9.)*degree ##8mm/9degrees
      
    def mm_to_degree(self, mm):
        return (9./8.)*mm #9degrees/8mm

    def steps_to_degree(self, steps):
        return self.mm_to_degree(steps/(800.*self.microsteps_standa))-4.5  #1mm /800step*microsteps_standa

    def degree_to_steps(self, degree): #800step*microsteps_standa / 1mm
        return int(self.degree_to_mm(degree+4.5)*800*self.microsteps_standa)

    def steps_to_mm(self, steps):
        return steps/(200.*self.microsteps_nano) #1mm / 200steps*microsteps_nano

    def mm_to_steps(self, mm):
        return int(mm*200*self.microsteps_nano) #200steps*microsteps_nano / 1mm

    #Für Höhenmotor
    def steps_to_hmm(self, steps):
        return steps/(200.*self.microsteps_nano) #CHANGE

    def hmm_to_steps(self, mm):
        return int(mm*200*self.microsteps_nano) #CHANGE

    def set_driving_speed(self, motor,speed):
        motor.axis.max_positioning_speed=int(speed)
        motor.set_axis_parameter(194, 300)
    
    #red stop button
    def stop_all(self):
        for motor in self.a:
            motor.stop()
        print("Stop all motors!")
        
    def go_to_saved_position(self, path="stepper_items/saved_position.txt"):
        thispositions = []
        readpos = open(path,"r")
        for line in readpos:
            thispositions.append(float(line))
        self.set_position_camera_z(thispositions[0])
        self.set_position_camera_x(thispositions[1])
        self.set_position_mirror_z(thispositions[2])
        self.set_position_mirror_height(thispositions[3])
        self.set_position_mirror_psi(thispositions[4])
        self.set_position_mirror_phi(thispositions[5])
        return thispositions
    
    def save_this_position(self, path="stepper_items/saved_position.txt"):
        thispos = open(path,"w")
        thispos.write(str(str(self.get_position_camera_z())+"\n"))
        thispos.write(str(str(self.get_position_camera_x())+"\n"))
        thispos.write(str(str(self.get_position_mirror_z())+"\n"))
        thispos.write(str(str(self.get_position_mirror_height())+"\n"))
        thispos.write(str(str(self.get_position_mirror_psi())+"\n"))
        thispos.write(str(str(self.get_position_mirror_phi())+"\n")) 
        
        
    def refsearch_camera_z(self):
        self.a[0].reference_search(0)
    def refsearch_camera_x(self):
        self.a[1].reference_search(0)
    def refsearch_mirror_z(self):
        self.a[2].reference_search(0)
    def refsearch_mirror_height(self):
        self.a[3].reference_search(0)
    def refsearch_mirror_psi(self):
        self.a[4].reference_search(0)
    def refsearch_mirror_phi(self):
        self.a[5].reference_search(0)
    def refsearch_all(self):
        self.refsearch_mirror_height()
        self.refsearch_mirror_z()
        self.refsearch_mirror_phi()
        self.refsearch_mirror_psi()
        self.refsearch_camera_x()
        self.refsearch_camera_z()
            
    def set_max_current_camera_z(self, value, verbose=False):
        self.current[0]=value
        self.a[0].set_axis_parameter(6,self.i_to_n(self.current[0]))
        if verbose==False: print ("Set Camera Z current limit to {}".format(self.current[0]))
    def set_max_current_camera_x(self, value, verbose=False):
        self.current[1]=value
        self.a[1].set_axis_parameter(6,self.i_to_n(self.current[1]))
        if verbose==False: print ("Set Camera X current limit to {}".format(self.current[1]))
    def set_max_current_mirror_z(self, value, verbose=False):
        self.current[2]=value
        self.a[2].set_axis_parameter(6,self.i_to_n(self.current[2]))
        if verbose==False: print ("Set Mirror Z current limit to {}".format(self.current[2]))
    def set_max_current_mirror_height(self, value, verbose=False):
        self.current[3]=value
        self.a[3].set_axis_parameter(6,self.i_to_n(self.current[3]))
        if verbose==False: print ("Set Mirror Height current limit to {}".format(self.current[3]))
    def set_max_current_mirror_psi(self, value, verbose=False):
        self.current[4]=value
        self.a[4].set_axis_parameter(6,self.i_to_n(self.current[4]))
        if verbose==False: print ("Set Mirror Psi current limit to {}".format(self.current[4]))
    def set_max_current_mirror_phi(self, value, verbose=False):
        self.current[5]=value
        self.a[5].set_axis_parameter(6,self.i_to_n(self.current[5]))
        if verbose==False: print ("Set Mirror Phi current limit to {}".format(self.current[5]))
        
    def get_max_current_camera_z(self):
        return self.current[0]
    def get_max_current_camera_x(self):
        return self.current[1]
    def get_max_current_mirror_z(self):
        return self.current[2]
    def get_max_current_mirror_height(self):
        return self.current[3]
    def get_max_current_mirror_psi(self):
        return self.current[4]
    def get_max_current_mirror_phi(self):
        return self.current[5]
    
    def get_camera_z_moving(self):
        return sd.ismoving(self.a[0])
    def get_camera_x_moving(self):
        return sd.ismoving(self.a[1])
    def get_mirror_z_moving(self):
        return sd.ismoving(self.a[2])
    def get_mirror_height_moving(self):
        return sd.ismoving(self.a[3])
    def get_mirror_psi_moving(self):
        return sd.ismoving(self.a[4])
    def get_mirror_phi_moving(self):
        return sd.ismoving(self.a[5])

    def set_max_acceleration_camera_z(self, value, verbose=False):
        self.acceleration[0]=value
        self.a[0].set_axis_parameter(5,self.acceleration[0])
        if verbose==False: print ("Set Camera Z acceleration limit to {}".format(self.acceleration[0]))
    def set_max_acceleration_camera_x(self, value, verbose=False):
        self.acceleration[1]=value
        self.a[1].set_axis_parameter(5,self.acceleration[1])
        if verbose==False: print ("Set Camera X acceleration limit to {}".format(self.acceleration[1]))
    def set_max_acceleration_mirror_z(self, value, verbose=False):
        self.acceleration[2]=value
        self.a[2].set_axis_parameter(5,self.acceleration[2])
        if verbose==False: print ("Set Mirror Z acceleration limit to {}".format(self.acceleration[2]))
    def set_max_acceleration_mirror_height(self, value, verbose=False):
        self.acceleration[3]=value
        self.a[3].set_axis_parameter(5,self.acceleration[3])
        if verbose==False: print ("Set Mirror Height acceleration limit to {}".format(self.acceleration[3]))
    def set_max_acceleration_mirror_psi(self, value, verbose=False):
        self.acceleration[4]=value
        self.a[4].set_axis_parameter(5,self.acceleration[4])
        if verbose==False: print ("Set Mirror Psi acceleration limit to {}".format(self.acceleration[4]))
    def set_max_acceleration_mirror_phi(self, value, verbose=False):
        self.acceleration[5]=value
        self.a[5].set_axis_parameter(5,self.acceleration[5])
        if verbose==False: print ("Set Mirror Phi acceleration limit to {}".format(self.acceleration[5]))
        
    def get_max_acc_camera_z(self):
        return self.acceleration[0]
    def get_max_acc_camera_x(self):
        return self.acceleration[1]
    def get_max_acc_mirror_z(self):
        return self.acceleration[2]
    def get_max_acc_mirror_height(self):
        return self.acceleration[3]
    def get_max_acc_mirror_psi(self):
        return self.acceleration[4]
    def get_max_acc_mirror_phi(self):
        return self.acceleration[5]
                
    def set_max_speed_camera_z(self, value, verbose=False):
        self.velocities[0]=value
        self.a[0].axis.max_positioning_speed = self.velocities[0]
        if verbose==False: print ("Set Camera Z speed limit to {}".format(self.a[0].axis.max_positioning_speed))
    def set_max_speed_camera_x(self, value, verbose=False):
        self.velocities[1]=value
        self.a[1].axis.max_positioning_speed = self.velocities[1]
        if verbose==False: print ("Set Camera X speed limit to {}".format(self.a[1].axis.max_positioning_speed))
    def set_max_speed_mirror_z(self, value, verbose=False):
        self.velocities[2]=value
        self.a[2].axis.max_positioning_speed = self.velocities[2]
        if verbose==False: print ("Set Mirror Z speed limit to {}".format(self.a[2].axis.max_positioning_speed))
    def set_max_speed_mirror_height(self, value, verbose=False):
        self.velocities[3]=value
        self.a[3].axis.max_positioning_speed = self.velocities[3]
        if verbose==False: print ("Set Mirror Height speed limit to {}".format(self.a[3].axis.max_positioning_speed))
    def set_max_speed_mirror_psi(self, value, verbose=False):
        self.velocities[4]=value
        self.a[4].axis.max_positioning_speed = self.velocities[4]
        if verbose==False: print ("Set Mirror Psi speed limit to {}".format(self.a[4].axis.max_positioning_speed))
    def set_max_speed_mirror_phi(self, value, verbose=False):
        self.velocities[5]=value
        self.a[5].axis.max_positioning_speed = self.velocities[5]
        if verbose==False: print ("Set Mirror Phi speed limit to {}".format(self.a[5].axis.max_positioning_speed))
        
    def get_max_speed_camera_z(self):
        return self.velocities[0]
    def get_max_speed_camera_x(self):
        return self.velocities[1]
    def get_max_speed_mirror_z(self):
        return self.velocities[2]
    def get_max_speed_mirror_height(self):
        return self.velocities[3]
    def get_max_speed_mirror_psi(self):
        return self.velocities[4]
    def get_max_speed_mirror_phi(self):
        return self.velocities[5]
        
    def switch_motor(self):
        if self.motoron == True:
            ms.motor_off();
            self.motoron = False
        else:
            ms.motor_on();
            self.motoron = True
            
    def get_motor_on(self):
        return self.motoron
    
    def set_position_camera_z(self, position, verbose=False):
        if verbose==False: print("Move camera z to",position)
        self.a[0].move_absolute(self.degree_to_steps(position))
    def set_position_camera_x(self, position, verbose=False):
        if verbose==False: print("Move camera x to",position)
        self.a[1].move_absolute(self.degree_to_steps(position))  
    def set_position_mirror_z(self, position, verbose=False):
        if verbose==False: print("Move mirror z to",position)
        self.a[2].move_absolute(self.degree_to_steps(position))  
    def set_position_mirror_height(self, position, verbose=False):
        if verbose==False: print("Move mirror height to",position)
        self.a[3].move_absolute(self.degree_to_steps(position))  
    def set_position_mirror_psi(self, position, verbose=False):
        if verbose==False: print("Move mirror psi to",position)
        self.a[4].move_absolute(self.degree_to_steps(position))
    def set_position_mirror_phi(self, position, verbose=False):
        if verbose==False: print("Move mirror phi to",position)
        self.a[5].move_absolute(self.degree_to_steps(position))
        
    def get_position_camera_z(self):
        return round(self.steps_to_mm(sd.position(self.a[0])),2)
    def get_position_camera_x(self):
        return round(self.steps_to_mm(sd.position(self.a[1])),2)
    def get_position_mirror_z(self):
        return round(self.steps_to_mm(sd.position(self.a[2])),2)
    def get_position_mirror_height(self):
        return round(self.steps_to_hmm(sd.position(self.a[3])),2)
    def get_position_mirror_psi(self):
        return round(self.steps_to_degree(sd.position(self.a[4])),2)
    def get_position_mirror_phi(self):
        return round(self.steps_to_degree(sd.position(self.a[5])),2)
    
    #dummy till now
    def get_position_servo(self):
        return -1
    
    #returns the status of the endswith. Meaning: 
    def get_endswitch_upper_camera_z(self):
        return self.a[0].axis.get(10)
    def get_endswitch_upper_camera_x(self):
        return self.a[1].axis.get(10)
    def get_endswitch_upper_mirror_z(self):
        return self.a[2].axis.get(10)
    def get_endswitch_upper_mirror_height(self):
        return self.a[3].axis.get(10)
    def get_endswitch_upper_mirror_psi(self):
        return self.a[4].axis.get(10)
    def get_endswitch_upper_mirror_phi(self):
        return self.a[5].axis.get(10)
    
    def get_endswitch_lower_camera_z(self):
        return self.a[0].axis.get(11)
    def get_endswitch_lower_camera_x(self):
        return self.a[1].axis.get(11)
    def get_endswitch_lower_mirror_z(self):
        return self.a[2].axis.get(11)
    def get_endswitch_lower_mirror_height(self):
        return self.a[3].axis.get(11)
    def get_endswitch_lower_mirror_psi(self):
        return self.a[4].axis.get(11)
    def get_endswitch_lower_mirror_phi(self):
        return self.a[5].axis.get(11)
    
    
    def open_shutter(self):
        servo.shutter(180)
    def close_shutter(self):
        servo.shutter(0)
    def set_servo_angle(self, value):
        self.servo_angle=value
        servo.shutter(value)
    def get_servo_angle(self):
        return self.servo_angle
 