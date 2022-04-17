import os
import stepper_drive as sd
import motor_switch as ms
import servo_test as servo
import powersupp_halogen as psupp
import numpy as np
import configparser


#this class contains everything that is needed to controll the motorboard
class CONTROLLER():

    bussy=False
    batch=False
    
    motor=None
    
    dist_max_mirr_cam=439 #mm maximum distance between the "left" edge of the mirror sled and the cam sled 
    dist_min_mirr_cam=308.5 #mm minumum distance that has to be kept between the mirror sled and the cam sled
    offset_camera_x=0 # is replaced with value from config during init 
    offset_mirror_height=146 #mm maximum distance between the upper edge of the jack plate and the lid
    gear_ratio_mirror_height=0 # is replaced with value from config during init 
    #these values were determined by fitting the curve given by ThorLabs for this labjack!
    #mirror_height_A=4.44907206e+00
    #mirror_height_B=-1.53803335e-03
    #mirror_height_C=9.89581577e+01
    #mirror_height_offset_turns=80
    #mirror_height_offset_mm=43.8650828274221
    mirror_height_A=113.00643014078436
    mirror_height_B=-0.9922775931781906
    mirror_height_C=98.95815765034412
    mirror_height_upper_limit_turns=60.966
    mirror_height_upper_limit_mm=np.sqrt(mirror_height_A**2+mirror_height_B*(mirror_height_upper_limit_turns-mirror_height_C)**2)
    mirror_height_total_turns=80
    mirror_height_shift_turns=mirror_height_total_turns-mirror_height_upper_limit_turns

    def __init__(self):
    
    	##############################
    	#  initalize the motorboard  #
    	##############################
    	
        port, self.serial_port=sd.init()  #stepper_drive
        ms.init()
        ms.motor_on()
        self.motoron = True
        self.servo_angle=0
        #initalize maximum positioning speed of the motors
        self.velocities = []
        for i in range (0,6):
            self.velocities.append(self.motor[i].axis.max_positioning_speed)
        #initalize maximum acceleration
        self.acceleration = []
        for i in range (0,6):
            self.acceleration.append(self.motor[i].get_axis_parameter(5))
        #initalize current  
        self.current = [] 
        for i in range (0, 6):
            self.current.append(self.n_to_i(self.motor[i].get_axis_parameter(6)))
            
        #Umrechnung zwischen motor parametern und python
        self.microsteps_nano = 32
        self.microsteps_standa = 16
        self.offset_standa = 512000
        
        ###############################
        #  initalize the halogen box  #
        ###############################        
        
        self.halogen = psupp.powerSupply()
        
        ###########################
        #  load config from file  #
        ###########################
        
        #check if config file exists and load it, otherwise programm exits!
        
        #get number of the motor pc
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
      
      	#get all nessecairy parameters from the global.conf
        global_config = configparser.ConfigParser()
        global_config.read('../global.conf')
       
        if "motor_pc_{}".format(motor_pc_no) in global_config:
            if motor_pc_no==1 or motor_pc_no==2:
            	#set gear ratio
                self.gear_ratio_mirror_height=float(global_config["motor_pc_{}".format(motor_pc_no)]["gear_ratio"])
                #set cam x offset
                self.offset_camera_x=float(global_config["motor_pc_{}".format(motor_pc_no)]["offset_camera_x"])
                #map the ports of the board to the correct motors
                motort0=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor0_port"])
                motor1=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor1_port"])
                motor2=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor2_port"])
                motor3=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor3_port"])
                motor4=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor4_port"])
                motor5=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor5_port"])
                order=[motor0, motor1, motor3, motor4, motor5]
                self.motor=[port[i] for i in order]
            else:
                print("Error in the 'this_pc.config'-file. The number of the Motor PC is neither 1 nor 2. Please correct!")
                exit()
        else:
            print("Error in the 'this_pc.config'-file. Section for this Motor PC is missing!")
            exit()
        print("Initalized controller with gear ratio {}".format(self.gear_ratio_mirror_height))
        
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
    
    
    #conversion between units in deltas 
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
    #this cant be calculated, as the relationship is non-linear 
    #def steps_to_hmm(self, steps):
    #    return steps/(200.*4.66*self.microsteps_nano)
    #def hmm_to_steps(self, mm):
    #    return int(mm*200*4.66*self.microsteps_nano)

    #conversion between units and absolute positions
    def mm_absolute_to_steps_camera_z(self, mm):
        return self.mm_to_steps(mm)
    def mm_absolute_to_steps_mirror_z(self, mm):
        return self.mm_to_steps(self.dist_max_mirr_cam-mm)
    def mm_absolute_to_steps_camera_x(self, mm):
        return self.mm_to_steps(-mm-self.offset_camera_x)
    def mm_absolute_to_steps_mirror_height(self, mm):
        #the function used here is made up due to geometric ideas of the Labjack
        #print("--------------------------")
        #print("got MM: {0}".format(mm))
        turns=self.mirror_height_total_turns-self.mirror_height_shift_turns-self.mirror_height_C+np.sqrt(((mm+self.mirror_height_upper_limit_mm-self.offset_mirror_height)**2-self.mirror_height_A**2)/self.mirror_height_B)
        #turns=np.sqrt((((mm-self.offset_mirror_height+self.mirror_height_offset_mm))**2-self.mirror_height_A**2)/(self.mirror_height_B))+self.mirror_height_offset_turns-self.mirror_height_C
        #(self.mirror_height_A**2+mm-self.offset_mirror_height**2)/self.mirror_height_B+self.mirror_height_C+self.mirror_height_offset_turns
        steps=turns*self.gear_ratio_mirror_height*200*self.microsteps_nano
        #print("calculated STEPS: {0}  , equals TURNS: {1}".format(steps, turns))
        return steps
        #return self.hmm_to_steps(self.offset_mirror_height+self.range_mirror_height-mm)
    def steps_to_mm_absolute_camera_z(self, steps):
        return self.steps_to_mm(steps)
    def steps_to_mm_absolute_mirror_z(self, steps):
        return self.dist_max_mirr_cam-self.steps_to_mm(steps)
    def steps_to_mm_absolute_camera_x(self, steps):
        return -(self.steps_to_mm(steps)+self.offset_camera_x)#+1000
    def steps_to_mm_absolute_mirror_height(self, steps):
        turns=steps/(200.*self.microsteps_nano)/self.gear_ratio_mirror_height
        #print("--------------------------")
        #print("got STEPS: {0}  , equals TURNS:  {1}   ".format(steps, -turns))
        #the function used here is made up due to geometric ideas of the Labjack
        try:
            mm=np.sqrt(self.mirror_height_A**2+self.mirror_height_B*((-turns-self.mirror_height_shift_turns+self.mirror_height_total_turns)-self.mirror_height_C)**2)-self.mirror_height_upper_limit_mm+self.offset_mirror_height
        except:
            mm=self.offset_mirror_height
        #np.sqrt(self.mirror_height_A**2+self.mirror_height_B*(turns+self.mirror_height_offset_turns-self.mirror_height_C))-self.mirror_height_offset_cm  print("calculated MM: {0}".format(mm))
        #print("calculated MM: {0}".format(mm))
        #print("--------------------------")
        return mm
        #return self.hmm_to_steps(self.offset_mirror_height+self.range_mirror_height-mm)
        #return self.offset_mirror_height+self.range_mirror_height-self.steps_to_hmm(steps)
    
    #set methods for all kinds of parameters
    def set_driving_speed(self, motor,speed):
        if motor==3:
            speed=speed*self.gear_ratio_mirror_height/4.66
        motor.axis.max_positioning_speed=int(speed)
        motor.set_axis_parameter(194, 300)
    
    def get_serial_port(self):
        return self.serial_port
    
    #red stop button
    def stop_all(self):
        for motor in self.motor:
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
        self.motor[0].reference_search(0)
    def refsearch_camera_x(self):
        self.motor[1].reference_search(0)
    def refsearch_mirror_z(self):
        self.motor[2].reference_search(0)
    def refsearch_mirror_height(self):
        self.motor[3].reference_search(0)
    def refsearch_mirror_psi(self):
        self.motor[4].reference_search(0)
    def refsearch_mirror_phi(self):
        self.motor[5].reference_search(0)
    def refsearch_all(self):
        self.refsearch_mirror_height()
        self.refsearch_mirror_z()
        self.refsearch_mirror_phi()
        self.refsearch_mirror_psi()
        self.refsearch_camera_x()
        self.refsearch_camera_z()
            
    def set_max_current_camera_z(self, value, verbose=False):
        self.current[0]=value
        self.motor[0].set_axis_parameter(6,self.i_to_n(self.current[0]))
        if verbose==False: print ("Set Camera Z current limit to {}".format(self.current[0]))
    def set_max_current_camera_x(self, value, verbose=False):
        self.current[1]=value
        self.motor[1].set_axis_parameter(6,self.i_to_n(self.current[1]))
        if verbose==False: print ("Set Camera X current limit to {}".format(self.current[1]))
    def set_max_current_mirror_z(self, value, verbose=False):
        self.current[2]=value
        self.motor[2].set_axis_parameter(6,self.i_to_n(self.current[2]))
        if verbose==False: print ("Set Mirror Z current limit to {}".format(self.current[2]))
    def set_max_current_mirror_height(self, value, verbose=False):
        self.current[3]=value
        self.motor[3].set_axis_parameter(6,self.i_to_n(self.current[3]))
        if verbose==False: print ("Set Mirror Height current limit to {}".format(self.current[3]))
    def set_max_current_mirror_psi(self, value, verbose=False):
        self.current[4]=value
        self.motor[4].set_axis_parameter(6,self.i_to_n(self.current[4]))
        if verbose==False: print ("Set Mirror Psi current limit to {}".format(self.current[4]))
    def set_max_current_mirror_phi(self, value, verbose=False):
        self.current[5]=value
        self.motor[5].set_axis_parameter(6,self.i_to_n(self.current[5]))
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
        return sd.ismoving(self.motor[0])
    def get_camera_x_moving(self):
        return sd.ismoving(self.motor[1])
    def get_mirror_z_moving(self):
        return sd.ismoving(self.motor[2])
    def get_mirror_height_moving(self):
        return sd.ismoving(self.motor[3])
    def get_mirror_psi_moving(self):
        return sd.ismoving(self.motor[4])
    def get_mirror_phi_moving(self):
        return sd.ismoving(self.motor[5])

    def set_max_acceleration_camera_z(self, value, verbose=False):
        self.acceleration[0]=value
        self.motor[0].set_axis_parameter(5,self.acceleration[0])
        if verbose==False: print ("Set Camera Z acceleration limit to {}".format(self.acceleration[0]))
    def set_max_acceleration_camera_x(self, value, verbose=False):
        self.acceleration[1]=value
        self.motor[1].set_axis_parameter(5,self.acceleration[1])
        if verbose==False: print ("Set Camera X acceleration limit to {}".format(self.acceleration[1]))
    def set_max_acceleration_mirror_z(self, value, verbose=False):
        self.acceleration[2]=value
        self.motor[2].set_axis_parameter(5,self.acceleration[2])
        if verbose==False: print ("Set Mirror Z acceleration limit to {}".format(self.acceleration[2]))
    def set_max_acceleration_mirror_height(self, value, verbose=False):
        self.acceleration[3]=value
        self.motor[3].set_axis_parameter(5,self.acceleration[3])
        if verbose==False: print ("Set Mirror Height acceleration limit to {}".format(self.acceleration[3]))
    def set_max_acceleration_mirror_psi(self, value, verbose=False):
        self.acceleration[4]=value
        self.motor[4].set_axis_parameter(5,self.acceleration[4])
        if verbose==False: print ("Set Mirror Psi acceleration limit to {}".format(self.acceleration[4]))
    def set_max_acceleration_mirror_phi(self, value, verbose=False):
        self.acceleration[5]=value
        self.motor[5].set_axis_parameter(5,self.acceleration[5])
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
        self.motor[0].axis.max_positioning_speed = self.velocities[0]
        if verbose==False: print ("Set Camera Z speed limit to {}".format(self.motor[0].axis.max_positioning_speed))
    def set_max_speed_camera_x(self, value, verbose=False):
        self.velocities[1]=value
        self.motor[1].axis.max_positioning_speed = self.velocities[1]
        if verbose==False: print ("Set Camera X speed limit to {}".format(self.motor[1].axis.max_positioning_speed))
    def set_max_speed_mirror_z(self, value, verbose=False):
        self.velocities[2]=value
        self.motor[2].axis.max_positioning_speed = self.velocities[2]
        if verbose==False: print ("Set Mirror Z speed limit to {}".format(self.motor[2].axis.max_positioning_speed))
    def set_max_speed_mirror_height(self, value, verbose=False):
        self.velocities[3]=value
        self.motor[3].axis.max_positioning_speed = self.velocities[3]
        if verbose==False: print ("Set Mirror Height speed limit to {}".format(self.motor[3].axis.max_positioning_speed))
    def set_max_speed_mirror_psi(self, value, verbose=False):
        self.velocities[4]=value
        self.motor[4].axis.max_positioning_speed = self.velocities[4]
        if verbose==False: print ("Set Mirror Psi speed limit to {}".format(self.motor[4].axis.max_positioning_speed))
    def set_max_speed_mirror_phi(self, value, verbose=False):
        self.velocities[5]=value
        self.motor[5].axis.max_positioning_speed = self.velocities[5]
        if verbose==False: print ("Set Mirror Phi speed limit to {}".format(self.motor[5].axis.max_positioning_speed))
        
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
        if verbose==False: print("Move camera z to {0:4.2f}".format(position))
        self.motor[0].move_absolute(self.mm_absolute_to_steps_camera_z(position))
    def set_position_camera_x(self, position, verbose=False):
        if verbose==False: print("Move camera x to {0:4.2f}".format(position))
        self.motor[1].move_absolute(self.mm_absolute_to_steps_camera_x(position))  
    def set_position_mirror_z(self, position, verbose=False):
        if verbose==False: print("Move mirror z to {0:4.2f}".format(position))
        self.motor[2].move_absolute(self.mm_absolute_to_steps_mirror_z(position))  
    def set_position_mirror_height(self, position, verbose=False):
        if verbose==False: print("Move mirror height to {0:4.2f}".format(position))
        self.motor[3].move_absolute(self.mm_absolute_to_steps_mirror_height(position))  
    def set_position_mirror_psi(self, position, verbose=False):
        if verbose==False: print("Move mirror psi to {0:4.2f}".format(position))
        self.motor[4].move_absolute(self.degree_to_steps(position))
    def set_position_mirror_phi(self, position, verbose=False):
        if verbose==False: print("Move mirror phi to {0:4.2f}".format(position))
        self.motor[5].move_absolute(self.degree_to_steps(position))
        
    def get_position_camera_z(self):
        return self.steps_to_mm_absolute_camera_z(sd.position(self.motor[0]))
    def get_position_camera_x(self):
        return self.steps_to_mm_absolute_camera_x(sd.position(self.motor[1]))
    def get_position_mirror_z(self):
        return self.steps_to_mm_absolute_mirror_z(sd.position(self.motor[2]))
    def get_position_mirror_height(self):
        return self.steps_to_mm_absolute_mirror_height(sd.position(self.motor[3]))
    def get_position_mirror_psi(self):
        return self.steps_to_degree(sd.position(self.motor[4]))
    def get_position_mirror_phi(self):
        return self.steps_to_degree(sd.position(self.motor[5]))
    
    #dummy till now
    def get_position_servo(self):
        return -1
    
    #returns the status of the endswith. Meaning: 
    def get_endswitch_upper_camera_z(self):
        return self.motor[0].axis.get(10)
    def get_endswitch_upper_camera_x(self):
        return self.motor[1].axis.get(10)
    def get_endswitch_upper_mirror_z(self):
        return self.motor[2].axis.get(10)
    def get_endswitch_upper_mirror_height(self):
        return self.motor[3].axis.get(10)
    def get_endswitch_upper_mirror_psi(self):
        return self.motor[4].axis.get(10)
    def get_endswitch_upper_mirror_phi(self):
        return self.motor[5].axis.get(10)
    
    def get_endswitch_lower_camera_z(self):
        return self.motor[0].axis.get(11)
    def get_endswitch_lower_camera_x(self):
        return self.motor[1].axis.get(11)
    def get_endswitch_lower_mirror_z(self):
        return self.motor[2].axis.get(11)
    def get_endswitch_lower_mirror_height(self):
        return self.motor[3].axis.get(11)
    def get_endswitch_lower_mirror_psi(self):
        return self.motor[4].axis.get(11)
    def get_endswitch_lower_mirror_phi(self):
        return self.motor[5].axis.get(11)
    
    
    def open_shutter(self):
        servo.shutter(180)
    def close_shutter(self):
        servo.shutter(0)
    def set_servo_angle(self, value):
        self.servo_angle=value
        servo.shutter(value)
    def get_servo_angle(self):
        return self.servo_angle
    
    def setBussy(self, bussy):
        self.bussy=bussy
    def isBussy(self):
        return self.bussy
    def setBatch(self, batch):
        self.batch=batch
    def getBatch(self):
        return self.batch
    def psupp_onoff(self):
        self.halogen.onoff()
 
