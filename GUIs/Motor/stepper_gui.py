from tkinter import *
from tkinter import messagebox
from tkinter import simpledialog
from numpy import random
from time import sleep
import scipy.optimize as opt
import threading
import warnings

from datetime import datetime

import stepper_drive as sd
import motor_switch as ms
import rate_client as rcl
import servo_test as servo
import time
import numpy as np #only needed for simulations
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends.backend_tkagg as tkagg
import matplotlib.patches as patches

import _thread
from threading import Thread
from PIL import Image
import os
from serial.serialutil import SerialException

#this class contains everything that is needed to controll the motorboard
class CONTROLLER():

    #get motors
    a=sd.init()  #stepper_drive
    ms.init()
    ms.motor_on()
    motoron = True
    
    #maximum positioning speed of the motors
    velocities = []
    for i in range (0,6):
        velocities.append(a[i].axis.max_positioning_speed)
        
    #maximum acceleration
    acceleration = []
    for i in range (0,6):
        acceleration.append(a[i].get_axis_parameter(5))
        
    #maximum current of the motors
    # Current regulation
    def i_to_n(cur):
        if  cur < 0.06:
            #print("Cur < 0.06A, set to 0.06")
            return 0
        if cur > 1.92 :
            #print("Cur  > 1.92A, set to 1.92")
            return 255
        return (int(cur/0.06)*8)-1

    def n_to_i(num):
        if num > 255:
            #print("Num > 255")
            return 1.92
        return (int(num/8)+1)*0.06
    current = [] 
    for i in range (0, 6):
        current.append(n_to_i(a[i].get_axis_parameter(6)))
    
    #Umrechnung zwischen motor parametern und python
    microsteps_nano = 32
    microsteps_standa = 16
    offset_standa = 512000
    
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
        for i in range (0,6):   #prueft ob motor an zielposition angekommen war oder nicht 
            if sd.ismoving(self.a[i]) == 1:   #1 wenn noch faehrt und 0 wenn schon angekommen, graues widget
                WarningStatus[i] = 1
        print("Stop all motors!")
        
    def goto_saved_position(self):
        thispositions = []
        readpos = open("stepper_items/saved_position.txt","r")
        for line in readpos:
            thispositions.append(float(line))
        CameraZ.set(thispositions[0])
        CameraX.set(thispositions[1])
        MirrorZ.set(thispositions[2])
        MirrorHeight.set(thispositions[3])
        MirrorPsi.set(thispositions[4])
        MirrorPhi.set(thispositions[5])
        moveto_camera_z()
        moveto_camera_x()
        moveto_mirror_z()
        moveto_mirror_height()
        moveto_mirror_psi()
        moveto_mirror_phi()
        
        

        
        
        
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
    
            
    def set_max_current_camera_z(self, value):
        self.current[0]=value
        self.a[0].set_axis_parameter(6,i_to_n(current[0]))
        print ("Set Camera Z current limit to {}".format(n_to_i(self.a[0].get_axis_parameter(6))))
    def set_max_current_camera_x(self, value):
        self.current[1]=value
        self.a[1].set_axis_parameter(6,i_to_n(current[1]))
        print ("Set Camera X current limit to {}".format(n_to_i(self.a[1].get_axis_parameter(6))))
    def set_max_current_mirror_z(self, value):
        self.current[2]=value
        self.a[2].set_axis_parameter(6,i_to_n(current[2]))
        print ("Set Mirror Z current limit to {}".format(n_to_i(self.a[2].get_axis_parameter(6))))
    def set_max_current_mirror_height(self, value):
        self.current[3]=value
        self.a[3].set_axis_parameter(6,i_to_n(current[3]))
        print ("Set Mirror Height current limit to {}".format(n_to_i(self.a[3].get_axis_parameter(6))))
    def set_max_current_mirror_psi(self, value):
        self.current[4]=value
        self.a[4].set_axis_parameter(6,i_to_n(current[4]))
        print ("Set Mirror Psi current limit to {}".format(n_to_i(self.a[4].get_axis_parameter(6))))
    def set_max_current_mirror_phi(self, value):
        self.current[5]=value
        self.a[5].set_axis_parameter(6,i_to_n(current[5]))
        print ("Set Mirror Phi current limit to {}".format(n_to_i(self.a[5].get_axis_parameter(6))))
        
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

    def set_max_acc_camera_z(self, value):
        acceleration[0]=value
        self.a[0].set_axis_parameter(5,self.acceleration[0])
        print ("Set Camera Z acceleration limit to {}".format(self.a[0].get_axis_parameter(5)))
    def set_max_acc_camera_x(self, value):
        acceleration[1]=value
        self.a[1].set_axis_parameter(5,self.acceleration[1])
        print ("Set Camera X acceleration limit to {}".format(self.a[1].get_axis_parameter(5)))
    def set_max_acc_mirror_z(self, value):
        acceleration[2]=value
        self.a[2].set_axis_parameter(5,self.acceleration[2])
        print ("Set Mirror Z acceleration limit to {}".format(self.a[2].get_axis_parameter(5)))
    def set_max_acc_mirror_height(self, value):
        acceleration[3]=value
        self.a[3].set_axis_parameter(5,self.acceleration[3])
        print ("Set Mirror Height acceleration limit to {}".format(self.a[3].get_axis_parameter(5)))
    def set_max_acc_mirror_psi(self, value):
        acceleration[4]=value
        self.a[4].set_axis_parameter(5,self.acceleration[4])
        print ("Set Mirror Psi acceleration limit to {}".format(self.a[4].get_axis_parameter(5)))
    def set_max_acc_mirror_phi(self, value):
        acceleration[5]=value
        self.a[5].set_axis_parameter(5,self.acceleration[5])
        print ("Set Mirror Phi acceleration limit to {}".format(self.a[5].get_axis_parameter(5)))
        
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
        
    def switchMotor(self):
        global motoron
        if motoron == True:
            ms.motor_off(); motoron = False
            onoffButton.config(text="OFF", bg="#a3a3a3")
        else:
            ms.motor_on(); motoron = True
            onoffButton.config(text="ON", bg="#91CC66")
         
    def set_position_mirror_height(self, position, verbose=False):
        if verbose==False: print("Move camera z to",position)
        self.a[0].move_absolute(self.degree_to_steps(position))   
    def set_position_mirror_height(self, position, verbose=False):
        if verbose==False: print("Move camera x to",position)
        self.a[1].move_absolute(self.degree_to_steps(position))  
    def set_position_mirror_height(self, position, verbose=False):
        if verbose==False: print("Move mirror z to",postion)
        self.a[2].move_absolute(self.degree_to_steps(position))  
    def set_position_mirror_height(self, position, verbose=False):
        if verbose==False: print("Move mirror height to",postiion)
        self.a[3].move_absolute(self.degree_to_steps(position))  
    def set_position_mirror_psi(self, position, verbose=False):
        print(position)
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
    
#This class contains all the parts for our Main GUI
class GUI:
    

    LEDColors = []
    LEDColors.append("#737373") #Resting
    LEDColors.append("#ff6600") #Moving
    LEDColors.append("#ff0000") #Warning

    ENDSwitchColors = []
    ENDSwitchColors.append("#ff6600")
    ENDSwitchColors.append("#737373")
    ENDSwitchColors.append("#ff0000")


    WarningStatus=[0,0,0,0,0,0]
    
    servo_angle=0
    
    change_position_mirror_phi=False
    change_position_mirror_psi=False
    change_position_mirror_z=False
    change_position_mirror_height=False
    change_position_camera_x=False
    change_position_camera_z=False
    
    change_velocity_mirror_phi=False
    change_velocity_mirror_psi=False
    change_velocity_mirror_z=False
    change_velocity_mirror_height=False
    change_velocity_camera_x=False
    change_velocity_camera_z=False
    
    def __init__(self, master, controller, client=None):
        self.master=master
        self.controller=controller
        self.client=client
        self.stop_thread=False
        self.master.wm_title("II Motor Control")
        self.master.config(background = "#003366")        
        
        #read positions from last time
        lastpositions=[]
        readpos = open("stepper_items/current_positions.txt","r")
        for line in readpos:
            lastpositions.append(float(line))
        
        #draw GUI
        
        
        #----------------#
        #---- Frames ----#
        #----------------#
        self.mainFrame = Frame(self.master, width=200, height = 400)
        self.mainFrame.grid(row=0, column=0, padx=10,pady=3)
        self.mainFrame.config(background = "#003366")

        self.switchFrame = Frame(self.mainFrame, width=200, height=20)
        self.switchFrame.grid(row=0,column=0, padx=10, pady=3)

        self.MirrorTFrame = Frame(self.mainFrame, width=200, height=400)
        self.MirrorTFrame.grid(row=1, column=0, padx=10, pady=3)

        self.MirrorRFrame = Frame(self.mainFrame, width=200, height=400)
        self.MirrorRFrame.grid(row=1, column=1, padx=10, pady=3)

        self.CameraFrame = Frame(self.mainFrame, width=200, height=400)
        self.CameraFrame.grid(row=1, column=2, padx=10, pady=3)

        self.RateFrame = Frame(self.mainFrame, width=200, height=40)
        self.RateFrame.grid(row=0, column=1, pady=3)

        self.ServoFrame = Frame(self.mainFrame, width=200, height=40)
        self.ServoFrame.grid(row=2, column=0, pady=3)

        self.OptFrame = Frame(self.mainFrame, width=200, height=40)
        self.OptFrame.grid(row=2, column=1, pady=3)

        #SwitchFrame Content
        self.switchLabel = Label(self.switchFrame, text="Motor is ")
        self.switchLabel.grid(row=0, column=0)

        self.onoffButton = Button(self.switchFrame, text="ON", bg="#91CC66")


        self.onoffButton.config(command=self.controller.switchMotor)
        self.onoffButton.grid(row=0, column=1)



        #MirrorT-Content
        self.MirrorTHeadFrame = Frame(self.MirrorTFrame, width=200, height=20); self.MirrorTHeadFrame.grid(row=0, column=0, padx=10, pady=3)
        self.leftLabel1 = Label(self.MirrorTHeadFrame, text="Mirror Height"); self.leftLabel1.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorHeightDisplay = Canvas(self.MirrorTHeadFrame, width=20,height=20); self.MirrorHeightDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.MirrorHeightPositionLabel = Label(self.MirrorTHeadFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_position_mirror_height())); self.MirrorHeightPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.MirrorHeightSetButton = Button(self.MirrorTHeadFrame, text="Set", width=2, command=self.set_mirror_height); self.MirrorHeightSetButton.grid(row=0,column=3)
        self.MirrorHeightRefsearch = Button(self.MirrorTHeadFrame, text="Ref", width=2, command=self.controller.refsearch_mirror_height()); self.MirrorHeightRefsearch.grid(row=0, column=4) 

        self.MirrorTUpperFrame = Frame(self.MirrorTFrame, width=200, height=300); self.MirrorTUpperFrame.grid(row=1, column=0)
        self.MirrorHeight_OSTOP = Canvas(self.MirrorTUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_height()], width=20, height=10); self.MirrorHeight_OSTOP.grid(row=0, column=0)
        self.MirrorHeight = Scale(self.MirrorTUpperFrame,from_=40, to=0, resolution=0.1, orient=VERTICAL, length=300); self.MirrorHeight.set(self.controller.get_position_mirror_height()); self.MirrorHeight.grid(row=1, column=0, padx=10, pady=3)
        self.MirrorHeight.bind("<ButtonRelease-1>", self.moveto_mirror_height); self.MirrorHeight.set(lastpositions[3])
        self.MirrorHeight_USTOP = Canvas(self.MirrorTUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_height()], width=20, height=10); self.MirrorHeight_USTOP.grid(row=2, column=0)
        self.MirrorTButtonFrame = Frame(self.MirrorTUpperFrame, width=100, height=150); self.MirrorTButtonFrame.grid(row=1, column=1)
        self.MirrorHeightSpeed = Scale(self.MirrorTButtonFrame,from_=0, to=5000, resolution=50, orient=HORIZONTAL, length=140, label="Speed"); self.MirrorHeightSpeed.set(self.controller.get_max_speed_mirror_height()); self.MirrorHeightSpeed.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorHeightSpeed.bind("<ButtonRelease-1>", self.new_velocity_mirror_height); self.MirrorHeightSpeed.set(controller.get_max_speed_mirror_height())
        self.MirrorHeightCurrent = Scale(self.MirrorTButtonFrame,from_=0.06, to=1.92, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I"); self.MirrorHeightCurrent.set(self.controller.get_max_current_mirror_height());self.MirrorHeightCurrent.grid(row=1, column=0, padx=10, pady=3)
        self.MirrorHeightAcc = Scale(self.MirrorTButtonFrame,from_=1, to=300, resolution=1, orient=HORIZONTAL, length=140, label="Acceleration"); self.MirrorHeightAcc.set(self.controller.get_max_acc_mirror_height());self.MirrorHeightAcc.grid(row=1, column=0, padx=10, pady=3)
        self.MirrorHeightAcc.bind("<ButtonRelease-1>", lambda ArgValue=self.MirrorHeightAcc.get() : self.set_max_acc_mirror_height(value=ArgValue)); self.MirrorHeightAcc.set(self.controller.get_max_acc_mirror_height())
        self.MirrorHeightCurrent = Scale(self.MirrorTButtonFrame,from_=50, to=300, resolution=1, orient=HORIZONTAL, length=140, label="Max I"); self.MirrorHeightCurrent.set(controller.get_max_current_mirror_height()); self.MirrorHeightCurrent.grid(row=2, column=0, padx=10, pady=3)
        self.MirrorHeightCurrent.bind("<ButtonRelease-1>", lambda ArgValue=self.MirrorHeightCurrent.get() : self.set_max_current_mirror_height(value=ArgValue)); self.MirrorHeightCurrent.set(controller.get_max_current_mirror_height())
        self.B3 = Button(self.MirrorTButtonFrame, text="Center Mirror Pos", bg="#C0C0C0", width=16, command=self.center_mirror_pos); self.B3.grid(row=2, column=0)
        self.MirrorZSpeed = Scale(self.MirrorTButtonFrame,from_=0, to=5000, resolution=50, orient=HORIZONTAL, length=140, label="Speed");  self.MirrorZSpeed.set(controller.get_max_speed_mirror_z()); self.MirrorZSpeed.grid(row=3, column=0, padx=10, pady=3)
        self.MirrorZSpeed.bind("<ButtonRelease-1>", self.new_velocity_mirror_z); self.MirrorZSpeed.set(controller.get_max_speed_mirror_z())
        self.MirrorZCurrent = Scale(self.MirrorTButtonFrame,from_=0.06, to=1.44, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I"); self.MirrorZCurrent.set(controller.get_max_current_mirror_z()); self.MirrorZCurrent.grid(row=4, column=0, padx=10, pady=3)
        self.MirrorZAcc = Scale(self.MirrorTButtonFrame,from_=1, to=300, resolution=1, orient=HORIZONTAL, length=140, label="Acceleration");  self.MirrorZAcc.set(controller.get_max_acc_mirror_z()); self.MirrorZAcc.grid(row=5, column=0, padx=10, pady=3)
        self.MirrorZAcc.bind("<ButtonRelease-1>", lambda ArgVal=self.MirrorZAcc.get() : self.set_max_acc_mirror_z(value=ArgValue)); self.MirrorZAcc.set(controller.get_max_acc_mirror_z())
        self.MirrorZCurrent = Scale(self.MirrorTButtonFrame,from_=50, to=300, resolution=1, orient=HORIZONTAL, length=140, label="Max I"); self.MirrorZCurrent.set(self.controller.get_max_current_mirror_z()); self.MirrorZCurrent.grid(row=6, column=0, padx=10, pady=3)
        self.MirrorZCurrent.bind("<ButtonRelease-1>", lambda ArgVal=self.MirrorZCurrent.get() : self.set_max_current_mirror_z(value=ArgVal)); self.MirrorZCurrent.set(controller.get_max_current_mirror_z())

        self.MirrorTLowerFrame = Frame(self.MirrorTFrame, width=200, height=20); self.MirrorTLowerFrame.grid(row=2, column=0)
        self.leftLabel2 = Label(self.MirrorTLowerFrame, text="Mirror Z"); self.leftLabel2.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorZDisplay = Canvas(self.MirrorTLowerFrame, width=20,height=20); self.MirrorZDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.MirrorZPositionLabel = Label(self.MirrorTLowerFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_max_acc_mirror_height())); self.MirrorZPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.MirrorZSetButton = Button(self.MirrorTLowerFrame, text="Set", width=2, command=self.set_mirror_z); self.MirrorZSetButton.grid(row=0,column=3)
        self.MirrorZRefsearch = Button(self.MirrorTLowerFrame, text="Ref", width=2, command=self.refsearch_mirror_z); self.MirrorZRefsearch.grid(row=0, column=4)

        self.MirrorTBottomFrame = Frame(self.MirrorTFrame, width=200, height=60); self.MirrorTBottomFrame.grid(row=3, column=0)
        self.MirrorZ_LSTOP = Canvas(self.MirrorTBottomFrame, bg=self.ENDSwitchColors[controller.get_endswitch_upper_mirror_z()], width=10, height=20); self.MirrorZ_LSTOP.grid(row=0, column=0)
        self.MirrorZ = Scale(self.MirrorTBottomFrame, from_=0, to=120, resolution=0.1, orient=HORIZONTAL, length=250); self.MirrorZ.set(self.controller.get_position_mirror_z()); self.MirrorZ.grid(row=0, column=1, padx=10, pady=3)
        self.MirrorZ.bind("<ButtonRelease-1>", self.moveto_mirror_z); self.MirrorZ.set(lastpositions[2])
        self.MirrorZ_RSTOP = Canvas(self.MirrorTBottomFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_z()], width=10, height=20); self.MirrorZ_RSTOP.grid(row=0, column=2)


        #MirrorR-Content
        self.MirrorRHeadFrame = Frame(self.MirrorRFrame, width=200, height=20); self.MirrorRHeadFrame.grid(row=0, column=0)
        self.midLabel1 = Label(self.MirrorRHeadFrame, text="Mirror Psi"); self.midLabel1.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorPsiDisplay = Canvas(self.MirrorRHeadFrame, width=20,height=20); self.MirrorPsiDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.MirrorPsiPositionLabel = Label(self.MirrorRHeadFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_position_mirror_psi())); self.MirrorPsiPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.MirrorPsiSetButton = Button(self.MirrorRHeadFrame, text="Set", width=2, command=self.set_mirror_psi); self.MirrorPsiSetButton.grid(row=0,column=3)
        self.MirrorPsiRefsearch = Button(self.MirrorRHeadFrame, text="Ref", width=2, command=self.refsearch_mirror_psi); self.MirrorPsiRefsearch.grid(row=0, column=4) 

        self.MirrorRUpperFrame = Frame(self.MirrorRFrame, width=200, height=300); self.MirrorRUpperFrame.grid(row=1, column=0)
        self.MirrorPsi_OSTOP = Canvas(self.MirrorRUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_psi()], width=20, height=10); self.MirrorPsi_OSTOP.grid(row=0, column=0)
        self.MirrorPsi = Scale(self.MirrorRUpperFrame, from_=4.5, to=-4.5, resolution=0.01, orient=VERTICAL, length=300); self.MirrorPsi.set(self.controller.get_position_mirror_psi()); self.MirrorPsi.grid(row=1, column=0, padx=10, pady=3)
        self.MirrorPsi.bind("<ButtonRelease-1>", self.moveto_mirror_psi); self.MirrorPsi.set(lastpositions[4])
        self.MirrorPsi_USTOP = Canvas(self.MirrorRUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_psi()], width=20, height=10); self.MirrorPsi_USTOP.grid(row=2, column=0)
        self.MirrorRButtonFrame = Frame(self.MirrorRUpperFrame, width=100, height=150); self.MirrorRButtonFrame.grid(row=1, column=1)
        self.MirrorPsiSpeed = Scale(self.MirrorRButtonFrame,from_=0, to=10000, resolution=500, orient=HORIZONTAL, length=140, label="Speed"); self.MirrorPsiSpeed.set(self.controller.get_max_speed_mirror_psi()); self.MirrorPsiSpeed.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorPsiSpeed.bind("<ButtonRelease-1>", self.new_velocity_mirror_psi); self.MirrorPsiSpeed.set(self.controller.get_max_speed_mirror_psi())
        self.MirrorPsiCurrent = Scale(self.MirrorRButtonFrame,from_=0.06, to=0.66, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I"); self.MirrorPsiCurrent.set(self.controller.get_max_current_mirror_height()); self.MirrorPsiCurrent.grid(row=1, column=0, padx=10, pady=3)
        self.MirrorPsiCurrent.bind("<ButtonRelease-1>", lambda ArgVal=self.MirrorPsiCurrent : self.set_max_current_mirror_psi(value=ArgVal)); self.MirrorPsiCurrent.set(self.controller.get_max_current_mirror_psi())
        self.B6 = Button(self.MirrorRButtonFrame, text="Center Mirror Angle", bg="#C0C0C0", width=16, command=self.center_mirror_angle); self.B6.grid(row=2, column=0, padx=10, pady=3)
        self.MirrorPhiSpeed = Scale(self.MirrorRButtonFrame,from_=0, to=10000, resolution=500, orient=HORIZONTAL, length=140, label="Speed"); self.MirrorPhiSpeed.set(self.controller.get_max_speed_mirror_phi()); self.MirrorPhiSpeed.grid(row=3, column=0, padx=10, pady=3)
        self.MirrorPhiSpeed.bind("<ButtonRelease-1>", self.new_velocity_mirror_phi); self.MirrorPhiSpeed.set(self.controller.get_max_speed_mirror_phi())
        self.MirrorPhiCurrent = Scale(self.MirrorRButtonFrame,from_=0.06, to=0.66, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I"); self.MirrorPhiCurrent.set(self.controller.get_max_current_mirror_phi()); self.MirrorPhiCurrent.grid(row=4, column=0, padx=10, pady=3)
        self.MirrorPhiCurrent.bind("<ButtonRelease-1>", lambda ArgVal=self.MirrorPhiCurrent.get() : self.set_max_current_mirror_phi(value=ArgVal)); self.MirrorPhiCurrent.set(controller.get_max_current_mirror_phi())

        self.MirrorRLowerFrame = Frame(self.MirrorRFrame, width=200, height=20); self.MirrorRLowerFrame.grid(row=2, column=0)
        self.midLabel2 = Label(self.MirrorRLowerFrame, text="Mirror Phi"); self.midLabel2.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorPhiDisplay = Canvas(self.MirrorRLowerFrame, width=20,height=20); self.MirrorPhiDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.MirrorPhiPositionLabel = Label(self.MirrorRLowerFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_position_mirror_phi())); self.MirrorPhiPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.MirrorPhiSetButton = Button(self.MirrorRLowerFrame, text="Set", width=2, command=self.set_mirror_phi); self.MirrorPhiSetButton.grid(row=0,column=3)
        self.MirrorPhiRefsearch = Button(self.MirrorRLowerFrame, text="Ref", width=2, command=self.refsearch_mirror_phi); self.MirrorPhiRefsearch.grid(row=0, column=4)

        self.MirrorRBottomFrame = Frame(self.MirrorRFrame, width=200, height=60); self.MirrorRBottomFrame.grid(row=3, column=0)
        self.MirrorPhi_LSTOP = Canvas(self.MirrorRBottomFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_phi()], width=10, height=20); self.MirrorPhi_LSTOP.grid(row=0, column=0)
        self.MirrorPhi = Scale(self.MirrorRBottomFrame, from_=-4.5, to=4.5, resolution=0.01, orient=HORIZONTAL, length=300); self.MirrorPhi.set(self.controller.get_position_mirror_phi()); self.MirrorPhi.grid(row=0, column=1, padx=10, pady=3)
        self.MirrorPhi.bind("<ButtonRelease-1>", self.moveto_mirror_phi); self.MirrorPhi.set(lastpositions[5])
        self.MirrorPhi_RSTOP = Canvas(self.MirrorRBottomFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_phi()], width=10, height=20); self.MirrorPhi_RSTOP.grid(row=0, column=2)


        #Camera-Content
        self.CameraHeadFrame = Frame(self.CameraFrame, width=200, height=20); self.CameraHeadFrame.grid(row=0, column=0)
        self.rightLabel1 = Label(self.CameraHeadFrame, text="Camera X"); self.rightLabel1.grid(row=0, column=0, padx=10, pady=3)
        self.CameraXDisplay = Canvas(self.CameraHeadFrame, width=20,height=20); self.CameraXDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.CameraXPositionLabel = Label(self.CameraHeadFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_position_mirror_height())); self.CameraXPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.CameraXSetButton = Button(self.CameraHeadFrame, text="Set", width=2, command=self.set_camera_x); self.CameraXSetButton.grid(row=0,column=3)
        self.CameraXRefsearch = Button(self.CameraHeadFrame, text="Ref", width=2, command=self.refsearch_camera_x); self.CameraXRefsearch.grid(row=0, column=4)

        self.CameraUpperFrame = Frame(self.CameraFrame, width=200, height=300); self.CameraUpperFrame.grid(row=1, column=0)
        self.CameraX_OSTOP = Canvas(self.CameraUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_camera_x()], width=20, height=10); self.CameraX_OSTOP.grid(row=0, column=0)
        self.CameraX = Scale(self.CameraUpperFrame, from_=130, to=0, resolution=0.1, orient=VERTICAL, length=300); self.CameraX.set(self.controller.get_position_camera_x()); self.CameraX.grid(row=1, column=0, padx=10, pady=3)
        self.CameraX.bind("<ButtonRelease-1>", self.moveto_camera_x); self.CameraX.set(lastpositions[1])
        self.CameraX_USTOP = Canvas(self.CameraUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_camera_x()], width=20, height=10); self.CameraX_USTOP.grid(row=2, column=0)
        self.CameraButtonFrame = Frame(self.CameraUpperFrame, width=100, height=150); self.CameraButtonFrame.grid(row=1, column=1)
        self.CameraXSpeed = Scale(self.CameraButtonFrame,from_=0, to=5000, resolution=50, orient=HORIZONTAL, length=140, label="Speed"); self.CameraXSpeed.set(self.controller.get_max_speed_camera_x()); self.CameraXSpeed.grid(row=0, column=0, padx=10, pady=3)
        self.CameraXSpeed.bind("<ButtonRelease-1>", self.new_velocity_camera_x); self.CameraXSpeed.set(self.controller.get_max_speed_camera_x())
        self.CameraXCurrent = Scale(self.CameraButtonFrame,from_=0.06, to=1.44, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I"); self.CameraXCurrent.set(self.controller.get_max_current_camera_x()); self.CameraXCurrent.grid(row=1, column=0, padx=10, pady=3)
        self.CameraXAcc = Scale(self.CameraButtonFrame,from_=1, to=2047, resolution=1, orient=HORIZONTAL, length=140, label="Acceleration"); self.CameraXAcc.set(self.controller.get_max_acc_camera_x()); self.CameraXAcc.grid(row=1, column=0, padx=10, pady=3)
        self.CameraXAcc.bind("<ButtonRelease-1>", lambda ArgVal=self.CameraXAcc.get() : self.set_max_acc_camera_x(value=ArgVal)); self.CameraXAcc.set(self.controller.get_max_acc_camera_x())
        self.CameraXCurrent = Scale(self.CameraButtonFrame,from_=10, to=255, resolution=1, orient=HORIZONTAL, length=140, label="Max I"); self.CameraXCurrent.set(controller.get_max_current_camera_x()); self.CameraXCurrent.grid(row=2, column=0, padx=10, pady=3)
        self.CameraXCurrent.bind("<ButtonRelease-1>", lambda ArgVal=self.CameraXCurrent.get() : self.set_max_current_camera_x(value=ArgVal)); self.CameraXCurrent.set(controller.get_max_current_camera_x())
        self.B9 = Button(self.CameraButtonFrame, text="Center Camera", bg="#C0C0C0", width=16, command=self.center_camera); self.B9.grid(row=2, column=0, padx=10, pady=3)
        self.CameraZSpeed = Scale(self.CameraButtonFrame,from_=0, to=5000, resolution=50, orient=HORIZONTAL, length=140, label="Speed"); self.CameraZSpeed.set(self.controller.get_max_speed_camera_z()); self.CameraZSpeed.grid(row=3, column=0, padx=10, pady=3)
        self.CameraZSpeed.bind("<ButtonRelease-1>", self.new_velocity_camera_z); self.CameraZSpeed.set(self.controller.get_max_speed_camera_z())
        self.CameraZCurrent = Scale(self.CameraButtonFrame,from_=0.06, to=1.44, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I");self.CameraZCurrent.set(self.controller.get_max_current_camera_z()); self.CameraZCurrent.grid(row=4, column=0, padx=10, pady=3)
        self.CameraZAcc = Scale(self.CameraButtonFrame,from_=1, to=2047, resolution=1, orient=HORIZONTAL, length=140, label="Acceleration"); self.CameraZAcc.set(controller.get_max_acc_camera_z()); self.CameraZAcc.grid(row=5, column=0, padx=10, pady=3)
        self.CameraZAcc.bind("<ButtonRelease-1>", lambda ArgVal=self.CameraZAcc.get() : self.set_max_acc_camera_z(value=ArgVal)); self.CameraZAcc.set(controller.get_max_acc_camera_z())
        self.CameraZCurrent = Scale(self.CameraButtonFrame,from_=10, to=255, resolution=1, orient=HORIZONTAL, length=140, label="Max I"); self.CameraZCurrent.set(self.controller.get_max_current_camera_z()); self.CameraZCurrent.grid(row=6, column=0, padx=10, pady=3)
        self.CameraZCurrent.bind("<ButtonRelease-1>", lambda ArgVal=self.CameraZCurrent.get() : self.set_max_current_camera_z(value=ArgVal)); self.CameraZCurrent.set(self.controller.get_max_current_camera_z())


        self.CameraLowerFrame = Frame(self.CameraFrame, width=200, height=20); self.CameraLowerFrame.grid(row=2, column=0)
        self.rightLabel2 = Label(self.CameraLowerFrame, text="Camera Z"); self.rightLabel2.grid(row=0, column=0, padx=10, pady=3)
        self.CameraZDisplay = Canvas(self.CameraLowerFrame, width=20,height=20)
        self.CameraZDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.CameraZPositionLabel = Label(self.CameraLowerFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_position_camera_z()))
        self.CameraZPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.CameraZSetButton = Button(self.CameraLowerFrame, text="Set", width=2, command=self.set_camera_z); self.CameraZSetButton.grid(row=0,column=3)
        self.CameraZRefsearch = Button(self.CameraLowerFrame, text="Ref", width=2, command=self.refsearch_camera_z); self.CameraZRefsearch.grid(row=0, column=4)

        self.CameraBottomFrame = Frame(self.CameraFrame, width=200, height=60); self.CameraBottomFrame.grid(row=3, column=0)
        self.CameraZ_LSTOP = Canvas(self.CameraBottomFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_camera_z()], width=10, height=20); self.CameraZ_LSTOP.grid(row=0, column=0)
        self.CameraZ = Scale(self.CameraBottomFrame, from_= 150, to=0, resolution=0.1, orient=HORIZONTAL, length=250); self.CameraZ.set(self.controller.get_position_camera_z()); self.CameraZ.grid(row=0, column=1, padx=10, pady=3)
        self.CameraZ.bind("<ButtonRelease-1>", self.moveto_camera_z); self.CameraZ.set(lastpositions[0])
        self.CameraZ_RSTOP = Canvas(self.CameraBottomFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_camera_z()], width=10, height=20); self.CameraZ_RSTOP.grid(row=0, column=2)

        #Servo Content
        self.ServoHeadFrame = Frame(self.ServoFrame, width=200, height=20);
        self.ServoHeadFrame.grid(row=0, column=0)
        self.lbl_shutter = Label(self.ServoHeadFrame, text="Shutter");
        self.lbl_shutter.grid(row=0, column=0, padx=10, pady=3, columnspan=2)
        #ServoDisplay = Canvas(ServoHeadFrame, width=20,height=20)
        #ServoDisplay.grid(row=0, column=1, padx=3, pady=3)

        self.OpenButton = Button(self.ServoHeadFrame, text="Open", width=4, command=self.open_shutter);
        self.OpenButton.grid(row=0,column=3)
        self.CloseButton = Button(self.ServoHeadFrame, text="Close", width=4, command=self.close_shutter);
        self.CloseButton.grid(row=0, column=4)

        self.ServoUpperFrame = Frame(self.ServoFrame, width=200, height=300);
        self.ServoUpperFrame.grid(row=1, column=0)
        self.lbl_up = Label(self.ServoUpperFrame, text="0 \N{DEGREE SIGN}")
        self.lbl_down = Label(self.ServoUpperFrame, text="180 \N{DEGREE SIGN}")

        self.Shutter = Scale(self.ServoUpperFrame,from_=0, to=180, orient=HORIZONTAL); self.Shutter.set(self.controller.get_position_servo())
        self.Shutter.bind("<ButtonRelease-1>", self.shutter_scale); 
        self.lbl_up.grid(row=0, column=0, sticky="e")
        self.Shutter.grid(row=0, column=1, columnspan=2)
        self.lbl_down.grid(row=0, column=3, sticky="w")
        self.ServoPositionLabel = Label(self.ServoHeadFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.servo_angle));
        self.ServoPositionLabel.grid(row=0, column=2, padx=10, pady=3)

        #Rate-Content
        self.desc_Label_rate = Label(self.RateFrame, text="Photon rate [MHz]"); self.desc_Label_rate.grid(row=4, column=0, padx=5)
        self.desc_Label_rate_A = Label(self.RateFrame, text="Ch A"); self.desc_Label_rate_A.grid(row=4, column=1, padx=3, pady=3)
        self.desc_Label_rate_B = Label(self.RateFrame, text="Ch B"); self.desc_Label_rate_B.grid(row=4, column=3, padx=3, pady=3)
        self.CHa_Label_rate = Label(self.RateFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 15 bold"), width=7);   self.CHa_Label_rate.grid(row=4, column=2, padx=3, pady=3)
        self.CHb_Label_rate = Label(self.RateFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 15 bold"), width=7);   self.CHb_Label_rate.grid(row=4, column=4, padx=3, pady=3)
        self.rateClientButton = Button(self.RateFrame, text="Connect", bg="#cdcfd1", command=self.startStopClient, width=8); self.rateClientButton.grid(row=4,column=5, padx=3, pady=3)

        #optimziation content
        self.optimizationButton = Button(self.OptFrame, text="optimize Mirrors", bg="#cdcfd1", command=self.optimize, width=16); self.optimizationButton.grid(row=4,column=5, padx=3, pady=3)
        self.scanButton = Button(self.OptFrame, text="plot Mirrors", bg="#cdcfd1", command=self.showRateDistribution, width=16); self.scanButton.grid(row=4,column=6, padx=3, pady=3)
        self.dummyButton = Button(self.OptFrame, text="dummy Button", bg="#cdcfd1", command=self.dummy_button, width=16); self.dummyButton.grid(row=4,column=7, padx=3, pady=3)


        # Displays with LEDs
        self.MirrorHeightLED = self.MirrorHeightDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0)
        self.MirrorZLED = self.MirrorZDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0)
            
        self.MirrorPhiLED = self.MirrorPhiDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0)
        self.MirrorPsiLED = self.MirrorPsiDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0)

        self.CameraXLED = self.CameraXDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0)
        self.CameraZLED = self.CameraZDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0)

        #ServoLED = ServoDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)
        
        #ButtonFrame
        self.buttonFrame = Frame(self.master, width=30, height = 400, bg="#003366"); self.buttonFrame.grid(row=0, column=1, padx=10,pady=3)
        self.img=PhotoImage(file="stepper_items/ecap_blue.png")
        self.ecap = Label(self.buttonFrame, image=self.img, bg="#003366"); self.ecap.grid(row=0,column=0)
        self.titlelabel= Label(self.buttonFrame, text="II Motor Control", font="Helvetica 18 bold", fg="white", bg="#003366"); self.titlelabel.grid(row=1, column=0)
        self.B10 = Button(self.buttonFrame, text="STOP", font="Helvetica 10 bold", fg="white", bg="#FF0000", width=17, height=7, command=self.controller.stop_all); self.B10.grid(row=8, column=0, padx=10, pady=3)
        #B11 = Button(buttonFrame, text ="Update screen", bg="#A9A9A9", width=17, command=update_screen); B11.grid(row=9, column=0, padx=10, pady=3)
        self.globFrame = Frame(self.buttonFrame, bg="#003366"); self.globFrame.grid(row=10,column=0)
        self.AllRefsearch = Button(self.globFrame, text="Ref All", bg="#A9A9A9", width=6, command=self.refsearch_all); self.AllRefsearch.grid(row=0, column=0, padx=1, pady=3)
        self.B15 = Button(self.globFrame, text="Set All", bg="#A9A9A9", width=6, command=self.set_all); self.B15.grid(row=0, column=1, padx=1, pady=3)
        self.B13 = Button(self.buttonFrame, text="Save current positions", bg="#A9A9A9", width=17, command=self.save_this_position); self.B13.grid(row=11, column=0, padx=10, pady=3)
        self.B14 = Button(self.buttonFrame, text="Go to saved position", bg = "#A9A9A9", width=17, command=self.controller.goto_saved_position); self.B14.grid(row=12, column=0, padx=10, pady=3)
        self.exit_button = Button(self.buttonFrame, text="Save Positions and exit", bg="#A9A9A9", width=17, command=self.exitGUI); self.exit_button.grid(row=13, column=0, padx=10, pady=3)




        #Hübsche Farben
        MirrorTColor = "#b3daff"
        self.MirrorTFrame.config(background = MirrorTColor)
        self.MirrorTHeadFrame.config(background = MirrorTColor)
        self.leftLabel1.config(background = MirrorTColor)
        self.MirrorHeightDisplay.config(background = MirrorTColor)
        self.MirrorTUpperFrame.config(background = MirrorTColor)
        self.MirrorHeight.config(background = MirrorTColor)
        self.MirrorHeightSpeed.config(background = MirrorTColor)
        self.MirrorHeightAcc.config(background = MirrorTColor)
        self.MirrorHeightCurrent.config(background = MirrorTColor)
        self.MirrorTButtonFrame.config(background = MirrorTColor)
        self.MirrorTLowerFrame.config(background = MirrorTColor)
        self.leftLabel2.config(background = MirrorTColor)
        self.MirrorZDisplay.config(background = MirrorTColor)
        self.MirrorTBottomFrame.config(background = MirrorTColor)
        self.MirrorZ.config(background = MirrorTColor)
        self.MirrorZSpeed.config(background = MirrorTColor)
        self.MirrorZAcc.config(background = MirrorTColor)
        self.MirrorZCurrent.config(background = MirrorTColor)

        MirrorRColor = "#66b5ff"
        self.MirrorRFrame.config(background = MirrorRColor)
        self.MirrorRHeadFrame.config(background = MirrorRColor)
        self.midLabel1.config(background = MirrorRColor)
        self.MirrorPhiDisplay.config(background = MirrorRColor)
        self.MirrorRUpperFrame.config(background = MirrorRColor)
        self.MirrorPhi.config(background = MirrorRColor)
        self.MirrorPhiSpeed.config(background = MirrorRColor)
        self.MirrorPhiCurrent.config(background = MirrorRColor)
        self.MirrorRButtonFrame.config(background = MirrorRColor)
        self.MirrorRLowerFrame.config(background = MirrorRColor)
        self.midLabel2.config(background = MirrorRColor)
        self.MirrorPsiDisplay.config(background = MirrorRColor)
        self.MirrorRBottomFrame.config(background = MirrorRColor)
        self.MirrorPsi.config(background = MirrorRColor)
        self.MirrorPsiSpeed.config(background = MirrorRColor)
        self.MirrorPsiCurrent.config(background = MirrorRColor)

        CameraColor = "#ccff99"
        self.CameraFrame.config(background = CameraColor)
        self.CameraHeadFrame.config(background = CameraColor)
        self.rightLabel1.config(background = CameraColor)
        self.CameraXDisplay.config(background = CameraColor)
        self.CameraUpperFrame.config(background = CameraColor)
        self.CameraX.config(background = CameraColor)
        self.CameraXSpeed.config(background = CameraColor)
        self.CameraXAcc.config(background = CameraColor)
        self.CameraXCurrent.config(background = CameraColor)
        self.CameraButtonFrame.config(background = CameraColor)
        self.CameraLowerFrame.config(background = CameraColor)
        self.rightLabel2.config(background = CameraColor)
        self.CameraZDisplay.config(background = CameraColor)
        self.CameraBottomFrame.config(background = CameraColor)
        self.CameraZ.config(background = CameraColor)
        self.CameraZSpeed.config(background = CameraColor)
        self.CameraZAcc.config(background = CameraColor)
        self.CameraZCurrent.config(background = CameraColor)

        RateColor = "#b3daff"
        self.RateFrame.config(background = RateColor)
        self.desc_Label_rate.config(background = RateColor)
        self.desc_Label_rate_A.config(background = RateColor)
        self.desc_Label_rate_B.config(background = RateColor)

        ServoColor = "cornsilk"
        self.ServoFrame.config(bg=ServoColor)
        self.ServoHeadFrame.config(bg=ServoColor)
        self.lbl_shutter.config(bg=ServoColor)
        #ServoDisplay.config(bg=ServoColor)
        self.ServoUpperFrame.config(bg=ServoColor)
        self.lbl_up.config(bg=ServoColor)
        self.lbl_down.config(bg=ServoColor)
        self.Shutter.config(bg=ServoColor)

        #initalize Fahrbalken correctly
        self.CameraZ.set(self.controller.get_position_camera_z())
        self.CameraX.set(self.controller.get_position_camera_x())
        self.MirrorZ.set(self.controller.get_position_mirror_z())
        self.MirrorHeight.set(self.controller.get_position_mirror_height())
        self.MirrorPsi.set(self.controller.get_position_mirror_psi())
        self.MirrorPhi.set(self.controller.get_position_mirror_phi())
    
    #exit gui
    def exitGUI():
        servo.shutter_clean(90)
        self.save_this_position("stepper_items/current_positions.txt")
        if self.client != None:
            self.client.stop()
            self.client = None
        self.master.destroy()

    #save postions
    def save_this_position(self, path="stepper_items/saved_position.txt"):
        thispos = open(path,"w")
        thispos.write(str(self.controller.get_position_camera_z()+"\n"))
        thispos.write(str(self.controller.get_position_camera_x()+"\n"))
        thispos.write(str(self.controller.get_position_mirror_z()+"\n"))
        thispos.write(str(self.controller.get_position_mirror_height()+"\n"))
        thispos.write(str(self.controller.get_position_mirror_psi()+"\n"))
        thispos.write(str(self.controller.get_position_mirror_phi()+"\n"))           
   
    def startStopClient(self):
        if self.client == None:
            client_cache = rcl.rate_client()
            try:
                client_cache.connect()
                rateClientButton.config(text="Disconnect")
                self.client=client_cache
                print("Started the rate client. Rates will be displayed once they arrive.")
            except:
                print("Could not connect to server. Please check if server address and port are correct!")
        else:
            self.client.stop()
            self.CHa_Label_rate.config(fg="orange")
            self.CHb_Label_rate.config(fg="orange")
            self.rateClientButton.config(text="Connect")
            self.client = None   
    
    #here are the methods triggered by the different button/sclae events
        
    #tells the update routine to move the motors to the new values of the position scale
    def moveto_mirror_height(self, event):
        self.change_position_camera_height=True
    def moveto_mirror_z(self, event):
        self.change_position_mirror_z=True
    def moveto_mirror_phi(self, event):
        self.change_position_mirror_phi=True
    def moveto_mirror_psi(self, event):
        self.change_position_mirror_psi=True
    def moveto_camera_x(self, event):    
        self.change_position_camera_x=True  
    def moveto_camera_z(self, event):
        self.change_position_camera_z=True
        
        
    #tells the update routine to update the maximum velocities 
    def new_velocity_mirror_height(self, event):
        self.change_velocity_mirror_height=True
    def new_velocity_mirror_z(self, event):
        self.change_velocity_mirror_z=True
    def new_velocity_mirror_phi(self, event):
        self.change_velocity_mirror_phi=True
    def new_velocity_mirror_psi(self, event):
        self.change_velocity_mirror_psi=True
    def new_velocity_camera_x(self, event):    
        self.change_velocity_camera_x=True  
    def new_velocity_camera_z(self, event):
        self.change_velocity_camera_z=True
        
    #center each axis
    def center_camera(self):
        self.CameraX.set(70)
        self.moveto_camera_x()
        self.CameraZ.set(70)
        self.moveto_camera_z()    
    def center_mirror_pos(self):
        self.MirrorHeight.set(20)
        self.MirrorZ.set(150)    
    def center_mirror_phi():
        self.MirrorPhi.set(0)
        self.moveto_mirror_phi(0)
    def center_mirror_psi(self):
        self.MirrorPsi.set(0)
        self.moveto_mirror_psi(0)
    def center_mirror_angle(self):
        self.center_mirror_phi()
        self.center_mirror_psi()    

    #start refsearches for each axis
    def refsearch_camera_z(self):
        print("Searching for camera z-position 0mm")
        self.WarningStatus[0]=0
        self.controller.refsearch_camera_z()
        self.camera_z_pos.set(0)
    def refsearch_camera_x(self):
        print("Searching for camera x-position 0mm")
        WarningStatus[1]=0
        controller.refsearch_camera_x()
        camera_x_pos.set(0)  
    def refsearch_mirror_z(self):
        print("Searching for mirror z position 0mm")
        self.WarningStatus[2]=0
        self.controller.refsearch_mirror_z()
        self.mirror_z_pos.set(0)
    def refsearch_mirror_height(self):
        print("Searching for mirror height position 0mm")
        self.WarningStatus[3]=0
        self.controller.refsearch_mirror_height()
    def refsearch_mirror_psi(self):
        print("Searching for mirror psi position -4.5°")
        self.WarningStatus[4]=0
        self.controller.refsearch_mirror_psi()
        self.MirrorPsi.set(-4.5)
    def refsearch_mirror_phi(self):
        print("Searching for mirror phi position -4.5°")
        self.WarningStatus[5]=0
        self.controller.refsearch_mirror_phi()
        self.MirrorPhi.set(-4.5)
    def refsearch_all(self):
        self.refsearch_mirror_height()
        self.refsearch_mirror_z()
        self.refsearch_mirror_phi()
        self.refsearch_mirror_psi()
        self.refsearch_camera_x()
        self.refsearch_camera_z()
               
    # set position sliders to current positions of the motors (NOT TESTED YET)
    def set_mirror_height(self):
        self.MirrorHeight.set(self.controller.get_position_mirror_height())
        self.moveto_mirror_height()    
    def set_mirror_z(self):
        self.MirrorZ.set(self.controller.get_position_mirror_z())
        self.moveto_mirror_z()
    def set_mirror_phi(self):
        self.MirrorPhi.set(self.controller.get_position_mirror_height())
        self.moveto_mirror_phi()
    def set_mirror_psi(self):
        self.MirrorPsi.set(self.controller.get_position_mirror_psi())
        self.moveto_mirror_psi()
    def set_camera_x(self):
        self.CameraX.set(self.controller.get_position_camera_x())
        self.moveto_camera_x()
    def set_camera_z(self):
        self.CameraZ.set(self.controller.get_position_camera_z())
        self.moveto_camera_z()
    def set_all(self):
        self.set_mirror_height()
        self.set_mirror_z()
        self.set_mirror_phi()
        self.set_mirror_psi()
        self.set_camera_x()
        self.set_camera_z()
    
        
            
    def openNewDialogue(self):
        self.dialog=DialogFenster(master)
        
    def dummy_button(self):
        self.openNewDialogue()
        
    def optimize(self):
        return
    
    def showRateDistribution(self):
        return
    
    
    def open_shutter():
        servo.shutter(180)
    def close_shutter():
        servo.shutter(0)
    def shutter_scale(val):
        servo.shutter(servo_pos.get())
        servo_angle=servo_pos.get()
    def shutter_pos(val):
        return servo_pos.get()
    
            
    #-----------------------------------#
    #---- Permanently update screen ----#
    #-----------------------------------#
    def update_items(self, verbose=False):
        #move all motors due to changes since last time
        if self.change_position_camera_z:
            self.controller.set_position_camera_z(self.CameraZ.get(), verbose)
            self.WarningStatus[0]=0
            self.change_position_camera_z=False   
        if self.change_position_camera_x:
            self.controller.set_position_camera_x(self.CameraX.get(), verbose)
            self.WarningStatus[1]=0   
            self.change_position_camera_x=False  
        if self.change_position_mirror_z:
            self.controller.set_position_mirror_z(self.MirrorZ.get(), verbose)
            self.WarningStatus[2]=0
            self.change_position_mirror_z=False
        if self.change_position_mirror_height:
            self.controller.set_position_mirror_height(self.MirrorHeight.get(), verbose)
            self.WarningStatus[3]=0   
            self.change_position_mirror_height=False
        if self.change_position_mirror_psi:
            self.controller.set_position_mirror_psi(self.MirrorPsi.get())
            self.WarningStatus[4]=0
            self.change_position_mirror_psi=False 
        if self.change_position_mirror_phi:
            self.controller.set_position_mirror_phi(self.MirrorPhi.get(), verbose)
            self.WarningStatus[5]=0
            self.change_position_mirror_phi=False
        #change velocities due to changes since last time
        if self.change_velocity_camera_z:
            self.controller.set_max_speed_camera_z(self.CameraZSpeed.get(), verbose)
            self.WarningStatus[0]=0
            self.change_velocity_camera_z=False   
        if self.change_velocity_camera_x:
            self.controller.set_max_speed_camera_x(self.CameraXSpeed.get(), verbose)
            self.WarningStatus[1]=0   
            self.change_velocity_camera_x=False  
        if self.change_velocity_mirror_z:
            self.controller.set_max_speed_mirror_z(self.MirrorZSpeed.get(), verbose)
            self.WarningStatus[2]=0
            self.change_velocity_mirror_z=False
        if self.change_velocity_mirror_height:
            self.controller.set_max_speed_mirror_height(self.MirrorHeightSpeed.get(), verbose)
            self.WarningStatus[3]=0   
            self.change_velocity_mirror_height=False
        if self.change_velocity_mirror_psi:
            self.controller.set_max_speed_mirror_psi(self.MirrorPsiSpeed.get())
            self.WarningStatus[4]=0
            self.change_velocity_mirror_psi=False 
        if self.change_velocity_mirror_phi:
            self.controller.set_max_speed_mirror_phi(self.MirrorPhiSpeed.get(), verbose)
            self.WarningStatus[5]=0
            self.change_velocity_mirror_phi=False
            
        MHD = self.controller.get_mirror_height_moving()+self.WarningStatus[3]
        if MHD>2:
            MHD=2
        self.MirrorHeightDisplay.itemconfig(self.MirrorHeightLED, fill=self.LEDColors[MHD])
        self.MirrorHeightPositionLabel.config(text=str(round(self.controller.get_position_mirror_height(),1)))
        self.MirrorHeight_OSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_height()])
        self.MirrorHeight_USTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_height()])   
        self.MirrorZDisplay.itemconfig(self.MirrorZLED, fill=self.LEDColors[self.controller.get_mirror_z_moving()+self.WarningStatus[2]])
        self.MirrorZPositionLabel.config(text=str(round(self.controller.get_position_mirror_z(),1)))
        self.MirrorZ_LSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_z()])
        self.MirrorZ_RSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_z()])
        self.MirrorPsiPositionLabel.config(text="{0:4.2f}".format(self.controller.get_position_mirror_psi()))
        MPsiD=self.controller.get_mirror_psi_moving()+self.WarningStatus[4]
        if MPsiD>2:
            MPsiD=2
        self.MirrorPsiDisplay.itemconfig(self.MirrorPsiLED, fill=self.LEDColors[MPsiD])
        MPsiO=self.controller.get_endswitch_upper_mirror_phi()
        if MPsiO>2:
            MPsiO=2
        self.MirrorPsi_OSTOP.config(bg=self.ENDSwitchColors[MPsiO])
        MPsiU=self.controller.get_endswitch_lower_mirror_psi()
        if MPsiU>2:
            MPsiU=2
        self.MirrorPsi_USTOP.config(bg=self.ENDSwitchColors[MPsiU])
        self.MirrorPhiPositionLabel.config(text="{0:4.2f}".format(self.controller.get_position_mirror_phi()))
        self.MirrorPhiDisplay.itemconfig(self.MirrorPhiLED, fill=self.LEDColors[self.controller.get_mirror_phi_moving()+self.WarningStatus[5]])
        self.MirrorPhi_LSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_phi()])
        self.MirrorPhi_RSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_phi()])
        self.CameraXPositionLabel.config(text=str(round(self.controller.get_position_camera_x(),1)))
        self.CameraXDisplay.itemconfig(self.CameraXLED, fill=self.LEDColors[self.controller.get_camera_x_moving()+self.WarningStatus[1]])
        self.CameraX_OSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_camera_x()])
        self.CameraX_USTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_camera_x()]) 
        self.CameraZPositionLabel.config(text=str(round(self.controller.get_position_camera_z(),1)))
        self.CameraZDisplay.itemconfig(self.CameraZLED, fill=self.LEDColors[self.controller.get_camera_z_moving()+self.WarningStatus[0]])
        self.CameraZ_LSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_camera_z()])
        time.sleep(.05)
        self.CameraZ_RSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_camera_z()])
        time.sleep(.05)
        if self.client != None:
            try:
                self.CHa_Label_rate.config(text="{0:5.1f}".format(self.client.getRateA()), fg="#00ff00")
                self.CHb_Label_rate.config(text="{0:5.1f}".format(self.client.getRateB()), fg="#00ff00")
            except RuntimeError:
                self.startStopClient()
                
        self.master.update_idletasks()
       

    def update(self):
        self.stop_thread = False
        while True:
            if self.stop_thread:
                sleep(0.1)
                break
            try:
                self.update_items()
            except SerialException:
                print("Serial Exception. This only causes the GUI to miss one update!")
            except Exception as e:
                print(e)
            sleep(0.1)
    
    def run(self):
        thread=threading.Thread(target=self.update)
        thread.start()
        
    


class rateAnalyzer():
    client=None
    change_mirror_psi=False
    change_mirror_phi=False
    
    def showRateDistribution(spacing_phi=25, spacing_psi=26, min_phi=-2., max_phi=2, min_psi=-3.80, max_psi=-0.5, contrast_factor=3):
        #print("You entered the DUMMY-state")
        print("Starting to measure the rate distribution. MinPhi={0:4.2f} ; MaxPhi={1:4.2f} ; MinPsi={2:4.2f} ; MaxPsi={3:4.2f} ; SpacingPhi={4} ; SpacingPsi={5} ; ContrastFactor={6:4.2f}".format(min_phi, max_phi, min_psi, max_psi, spacing_phi, spacing_psi, contrast_factor))
        
        if self.client==None:
            print("No client connected! Cannot plot Mirrors")
            return
        coordinates_phi=np.linspace(min_phi, max_phi, num=spacing_phi)
        coordinates_psi=np.linspace(min_psi, max_psi, num=spacing_psi)
        x, y=np.meshgrid(coordinates_phi, coordinates_psi)
        rates=np.empty(shape=(spacing_phi, spacing_psi))
        for i in range(0, spacing_phi, 1):
            pos_phi=min_phi+(max_phi-min_phi)/(spacing_phi-1)*i
            MirrorPhi.set(pos_phi)
            moveto_mirror_phi()
            update_items(verbose=True)
            while controller.get_mirror_phi_moving():
                sleep(0.05)
                #print("wait_5_phi")
            for j in range(0, spacing_psi, 1):
                if i%2==0:
                    pos_psi=min_psi+(max_psi-min_psi)/(spacing_psi-1)*j
                else:
                    pos_psi=max_psi-(max_psi-min_psi)/(spacing_psi-1)*j
                #print("PSI: {0} PHI: {1}".format(pos_psi, pos_phi))
                MirrorPsi.set(pos_psi)
                moveto_mirror_psi()
                update_items(verbose=True)
                while controller.get_mirror_psi_moving():
                    sleep(0.05)
                    #print("wait_4_psi")
                if i%2==0:
                    rates[i][spacing_psi-1-j]=client.getRateA()+client.getRateB()
                else:
                    rates[i][j]=client.getRateA()+client.getRateB()
        rates=np.transpose(rates)
        print(rates)
        
    #    #generate random rates
    #    noise=np.random.rand(spacing_psi, spacing_phi)
    #    
    #    #generate a gaussian to place within noise
    #    coordinates_psi=np.linspace(min_psi, max_psi, num=spacing_psi)
    #    coordinates_phi=np.linspace(min_psi, max_psi, num=spacing_psi)
    #    x, y=np.meshgrid(coordinates_psi, coordinates_phi)
    #    rates=noise+10*gauss2d((x, y)).reshape(spacing_psi, spacing_phi)
    #    
        #make a nice plot
        fig=plt.Figure(figsize=(6,6))
        sub_plot = fig.add_subplot(111)
        sub_plot.set_title("Heatmap of the mirror Positions")
        sub_plot.imshow(rates, cmap='cool', extent=( min_phi-(max_phi-min_phi)/(spacing_phi)/2, max_phi+(max_phi-min_phi)/(spacing_phi)/2, min_psi-(max_psi-min_psi)/(spacing_psi)/2, max_psi+(max_psi-min_psi)/(spacing_psi)/2))
        sub_plot.set_xlabel("$\phi$ [°]")
        sub_plot.set_ylabel("$\psi$ [°]")
        
        # coordinates_phi=np.linspace(min_phi, max_phi, num=spacing_phi)
        #coordinates_psi=np.linspace(min_psi, max_psi, num=spacing_psi)
        #x, y=np.meshgrid(coordinates_phi, coordinates_psi)

        #do some crude narrowing of the spot
        max_rate=np.max(rates)
        mask=rates>max_rate/contrast_factor
        print(mask)
        min_x=len(rates)
        max_x=-1
        min_y=len(mask[0])
        max_y=-1
        for i in range(0, len(mask)):
            if np.sum(mask[i])>0 and min_y>i:
                min_y=i
            if np.sum(mask[i])>0 and max_y<i:
                max_y=i
        for i in range(0, len(mask[0])):
            if np.sum(mask[:,i])>0 and min_x>i:
                min_x=i
            if np.sum(mask[:,i])>0 and max_x<i:
                max_x=i
        print("min_x={0}; max_x={1}; min_y={2}; max_y={3}".format(min_x, max_x, min_y, max_y))
        print("BOX: min_phi={0}; max_phi={1}; min_psi={2}; max_psi={3}".format(coordinates_phi[min_x], coordinates_phi[max_x], coordinates_psi[len(coordinates_psi)-1-min_y], coordinates_psi[len(coordinates_psi)-1-max_y]))
        print("no1: min_phi={0}; max_phi={1}; min_psi={2}; max_psi={3}".format(coordinates_phi[min_x], coordinates_phi[max_x], coordinates_psi[min_y], coordinates_psi[max_y]))

        #calculate starting values for the gaussian
        center_phi=(coordinates_phi[min_x]+coordinates_phi[max_x])/2
        center_psi=(coordinates_psi[len(coordinates_psi)-1-min_y]+coordinates_psi[len(coordinates_psi)-1-max_y])/2
        sigma_phi=np.abs(coordinates_phi[max_x]-coordinates_phi[min_x])/2
        sigma_psi=np.abs(coordinates_psi[len(coordinates_psi)-1-max_y]-coordinates_psi[len(coordinates_psi)-1-min_y])/2
        offset=0
        prefactor=np.max(rates)

        p0=(prefactor, center_phi, sigma_phi, center_psi, sigma_psi, offset)
        print("Starting gaussian fit: p0:   center_phi = {0:5f} ; center_psi = {1:5f} ; sigma_phi = {2:5f} ; sigma_psi = {3:5f} ; offset = {4:5f} ; prefactor = {5:5f}".format(p0[1],p0[3], p0[2], p0[4], p0[5], p0[0]))
        with warnings.catch_warnings(record=True) as w:
            if np.size(rates)/4>np.sum(mask):
                rates_fit=rates[mask]
                x_fit=x[mask]
                y_fit=y[mask]
                print("Only using values within the red square for fit!")
            else:
                rates_fit=rates
                x_fit=x
                y_fit=y
            try:
                popt, pcov = opt.curve_fit(gauss2d, (x_fit,np.flip(y_fit)), rates_fit.ravel(), p0 = p0)
            except RuntimeError as e:
                w.append(e)
        if len(w)==0:
            data_fitted = gauss2d((x, y), *popt)
            with warnings.catch_warnings(record=True) as w:
                sub_plot.axes.contour(x, y, data_fitted.reshape(spacing_psi, spacing_phi), 8, colors='b')
            padding_psi=(coordinates_psi[1]-coordinates_psi[0])/2
            padding_phi=(coordinates_phi[1]-coordinates_phi[0])/2
            rect_start_phi=coordinates_phi[min_x]-padding_phi
            rect_start_psi=coordinates_psi[len(coordinates_psi)-1-min_y]+padding_psi
            rect_width_phi=coordinates_phi[max_x]-coordinates_phi[min_x]+2*padding_phi
            rect_width_psi=coordinates_psi[len(coordinates_psi)-1-max_y]-coordinates_psi[len(coordinates_psi)-1-min_y]-2*padding_psi
            '''rect_start_phi=popt[1]-np.abs(popt[2])
            rect_start_psi=popt[3]-np.abs(popt[4])
            rect_width_phi=2*np.abs(popt[2])
            rect_width_psi=2*np.abs(popt[4])'''
            print("Gaussian was fitted and plotted!")
            print("CENTER: phi={0} , psi={1} , SIGMA: phi={2} , psi={3} , CONSTS: prefactor={4} , offset={5}".format(popt[1], popt[3], popt[2], popt[4], popt[0], popt[5]))
            #print("recommended next fit borders: rect_start_phi={0} ; rect_start_psi={1} ; rect_width_phi={2} ; rect_width_psi={3}".format(rect_start_phi, rect_start_psi, rect_width_phi, rect_width_psi))
        else:
            print("No Gaussian could be fitted. Draw estimated rectangle instead.")
            for warn in w:
                print(warn)
            padding_psi=(coordinates_psi[1]-coordinates_psi[0])/2
            padding_phi=(coordinates_phi[1]-coordinates_phi[0])/2
            rect_start_phi=coordinates_phi[min_x]-padding_phi
            rect_start_psi=coordinates_psi[len(coordinates_psi)-1-min_y]+padding_psi
            rect_width_phi=coordinates_phi[max_x]-coordinates_phi[min_x]+2*padding_phi
            rect_width_psi=coordinates_psi[len(coordinates_psi)-1-max_y]-coordinates_psi[len(coordinates_psi)-1-min_y]-2*padding_psi
        rect = patches.Rectangle((rect_start_phi, rect_start_psi), rect_width_phi, rect_width_psi, edgecolor='r', facecolor='none', label='recomended search area')
        with warnings.catch_warnings(record=True) as w:
            sub_plot.axes.add_patch(rect)
        sub_plot.legend()
                
        #create new window
        plotWindow = Toplevel(master)
        canvas = FigureCanvasTkAgg(fig, master=plotWindow)
        canvas.get_tk_widget().grid(row=0, column=0)
        canvas.draw()
        
        
        
        #add button for next closer fit
        min_phi=rect_start_phi
        max_phi=rect_start_phi+rect_width_phi
        min_psi=rect_start_psi+rect_width_psi
        max_psi=rect_start_psi
        
        #remove padding if it is lager than the range of the mirrors
        if min_phi>4.5: min_phi=4.5
        if min_phi<-4.5: min_phi=4.5
        if max_phi>4.5: max_phi=4.5
        if max_phi<-4.5: max_phi=4.5
        if min_psi>4.5: min_psi=4.5
        if min_psi<-4.5: min_psi=4.5
        if max_psi>4.5: max_psi=4.5
        if max_psi<-4.5: max_psi=4.5
        
        contrast_factor=contrast_factor/1.5
        spacing_phi=spacing_phi+2
        spacing_psi=spacing_psi+2
        nextIterationButton = Button(plotWindow, text="next Iteration in marked area", width=40, pady=3, padx=3)
        nextIterationButton["command"]= lambda argSpacingPhi=spacing_phi, argSpacingPsi=spacing_psi, argMinPhi=min_phi, argMaxPhi=max_phi, argMinPsi=min_psi, argMaxPsi=max_psi, argContrastFactor=contrast_factor : showRateDistribution(spacing_phi = argSpacingPhi, spacing_psi = argSpacingPsi, min_phi = argMinPhi, max_phi = argMaxPhi, min_psi = argMinPsi, max_psi= argMaxPsi, contrast_factor= argContrastFactor)
        nextIterationButton.grid(row=1,column=0)
        
    def findRectangle(rates, sub_plot , spacing_phi, spacing_psi, min_phi, max_phi, min_psi, max_psi, contrast_factor):
        rates=np.transpose(rates)
        coordinates_phi=np.linspace(min_phi, max_phi, num=spacing_phi)
        coordinates_psi=np.linspace(min_psi, max_psi, num=spacing_psi)
        x, y=np.meshgrid(coordinates_phi, coordinates_psi)
        max_rate=np.max(rates)
        mask=rates>max_rate/contrast_factor
        print(mask)
        min_x=len(rates)
        max_x=-1
        min_y=len(mask[0])
        max_y=-1
        for i in range(0, len(mask)):
            if np.sum(mask[i])>0 and min_y>i:
                min_y=i
            if np.sum(mask[i])>0 and max_y<i:
                max_y=i
        for i in range(0, len(mask[0])):
            if np.sum(mask[:,i])>0 and min_x>i:
                min_x=i
            if np.sum(mask[:,i])>0 and max_x<i:
                max_x=i
        print("min_x={0}; max_x={1}; min_y={2}; max_y={3}".format(min_x, max_x, min_y, max_y))
        print("BOX: min_phi={0}; max_phi={1}; min_psi={2}; max_psi={3}".format(coordinates_phi[min_x], coordinates_phi[max_x], coordinates_psi[len(coordinates_psi)-1-min_y], coordinates_psi[len(coordinates_psi)-1-max_y]))
        padding_psi=(coordinates_psi[1]-coordinates_psi[0])/2
        padding_phi=(coordinates_phi[1]-coordinates_phi[0])/2
        rect_start_phi=coordinates_phi[min_x]-padding_phi
        rect_start_psi=coordinates_psi[len(coordinates_psi)-1-min_y]+padding_psi
        rect_width_phi=coordinates_phi[max_x]-coordinates_phi[min_x]+2*padding_phi
        rect_width_psi=coordinates_psi[len(coordinates_psi)-1-max_y]-coordinates_psi[len(coordinates_psi)-1-min_y]-2*padding_psi
        rect = patches.Rectangle((rect_start_phi, rect_start_psi), rect_width_phi, rect_width_psi, edgecolor='r', facecolor='none', label='recommended search area')
        with warnings.catch_warnings(record=True) as w:
            sub_plot.axes.add_patch(rect)
        sub_plot.legend()
        print("added rectangle")
    
    def gauss2d(datapoints, prefactor=1, x_0=0, x_sigma=1, y_0=0, y_sigma=1, offset=0):
        return offset+prefactor*np.exp(-(np.power(datapoints[0]-x_0, 2)/(2*np.power(x_sigma,2)))-(np.power(datapoints[1]-y_0,2)/(2*np.power(y_sigma,2)))).ravel()

controller=CONTROLLER()
root = Tk()
my_gui=GUI(root,controller)
my_gui.run()  
root.mainloop()
os._exit(0)

    



