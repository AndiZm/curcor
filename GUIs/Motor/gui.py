from tkinter import *
#messagebox #is this really needed?
#from tkinter import simpledialog #is this really needed?
import _thread
from threading import Thread
import threading
from serial.serialutil import SerialException
import time
from rate_analyzer import *
import numpy as np
import geometry as geo


import warnings
import traceback
import rate_client as rcl
from time import sleep

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
    
    change_position_mirror_phi=False
    change_position_mirror_psi=False
    change_position_mirror_z=False
    change_position_mirror_height=False
    change_position_camera_x=False
    change_position_camera_x=False
    change_position_camera_z=False
    
    change_velocity_mirror_phi=False
    change_velocity_mirror_psi=False
    change_velocity_mirror_z=False
    change_velocity_mirror_height=False
    change_velocity_camera_x=False
    change_velocity_camera_z=False
    
    change_current_mirror_phi=False
    change_current_mirror_psi=False
    change_current_mirror_z=False
    change_current_mirror_height=False
    change_current_camera_x=False
    change_current_camera_z=False
    
    change_acceleration_mirror_phi=False
    change_acceleration_mirror_psi=False
    change_acceleration_mirror_z=False
    change_acceleration_mirror_height=False
    change_acceleration_camera_x=False
    change_acceleration_camera_z=False

    
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
        
        width_frame=1050
        
        self.overMainFrame = Frame(self.master, width=width_frame, height=40, bg="#003366")
        self.overMainFrame.grid(row=0, column=0, pady=10)
        self.overMainFrame.grid_propagate(0)
            
        self.mainFrame = Frame(self.master, width=width_frame, height = 600)
        self.mainFrame.grid(row=1, column=0)
        self.mainFrame.config(background = "#003366")
        self.mainFrame.grid_propagate(0)
        
        self.belowMainFrame = Frame(self.master, width=width_frame, height=120, bg="#003366")
        self.belowMainFrame.grid(row=2, column=0)
        self.belowMainFrame.grid_propagate(0)

        self.switchFrame = Frame(self.overMainFrame)
        self.switchFrame.grid(row=0,column=0, padx=70, ipady=3) #(325-width_switch_frame)/2
        
        self.RateFrame = Frame(self.overMainFrame)
        self.RateFrame.grid(row=0, column=1, padx=0, pady=3)
        
        #self.centerFrame = Frame(self.mainFrame, width=600, height=400)
        #self.centerFrame.grid(row=1, column=0)
        
        height_controller_frames=590-6
        width_controller_frames=325
        padx_controller_frames=10
        pady_controller_frames=3
        
        self.MirrorTFrame = Frame(self.mainFrame, width=width_controller_frames, height=height_controller_frames)
        self.MirrorTFrame.grid(row=1, column=1, padx=padx_controller_frames, pady=pady_controller_frames)
        self.MirrorTFrame.grid_propagate(0)

        self.MirrorRFrame = Frame(self.mainFrame, width=width_controller_frames, height=height_controller_frames)
        self.MirrorRFrame.grid(row=1, column=2, padx=padx_controller_frames, pady=pady_controller_frames)
        self.MirrorRFrame.grid_propagate(0)

        self.CameraFrame = Frame(self.mainFrame, width=width_controller_frames, height=height_controller_frames)
        self.CameraFrame.grid(row=1, column=0, padx=padx_controller_frames, pady=pady_controller_frames)
        self.CameraFrame.grid_propagate(0)
        
        self.buttonFrame = Frame(self.master, width=30, height = 400, bg="#003366")
        self.buttonFrame.grid(row=1, column=1, padx=10,pady=3)

        self.ServoFrame = Frame(self.belowMainFrame, width=200, height=40)
        self.ServoFrame.grid(row=2, column=0, padx=65, pady=3, sticky=W)

        self.GeometryFrame = Frame(self.belowMainFrame, width=100, height=60)
        self.GeometryFrame.grid(row=2, column=1, padx=10, pady=3)
        
        self.psuppFrame = Frame(self.belowMainFrame, width=200, height=40)
        self.psuppFrame.grid(row=2, column=2, padx=10, pady=3)

        #SwitchFrame Content
        self.switchLabel = Label(self.switchFrame, text="Motor is ", padx=3, pady=3)
        self.switchLabel.grid(row=0, column=0)
        if self.controller.get_motor_on():
            self.onoffButton = Button(self.switchFrame, text="ON", bg="#91CC66", padx=3, pady=3)
        else:
            onoffButton.config(text="OFF", bg="#a3a3a3", padx=3, pady=3)
            

        self.onoffButton.config(command=self.switch_motor)
        self.onoffButton.grid(row=0, column=1)



        #MirrorT-Content
        self.MirrorTHeadFrame = Frame(self.MirrorTFrame, width=200, height=20); self.MirrorTHeadFrame.grid(row=0, column=0, padx=10, pady=3)
        self.leftLabel1 = Label(self.MirrorTHeadFrame, text="Mirror Height"); self.leftLabel1.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorHeightDisplay = Canvas(self.MirrorTHeadFrame, width=20,height=20); self.MirrorHeightDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.MirrorHeightPositionLabel = Label(self.MirrorTHeadFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_position_mirror_height()), width=5); self.MirrorHeightPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.MirrorHeightSetButton = Button(self.MirrorTHeadFrame, text="Set", width=2, command=self.set_mirror_height); self.MirrorHeightSetButton.grid(row=0,column=3)
        self.MirrorHeightRefsearch = Button(self.MirrorTHeadFrame, text="Ref", width=2, command=self.refsearch_mirror_height); self.MirrorHeightRefsearch.grid(row=0, column=4) 

        self.MirrorTUpperFrame = Frame(self.MirrorTFrame, width=200, height=300); self.MirrorTUpperFrame.grid(row=1, column=0)
        self.MirrorHeight_USTOP = Canvas(self.MirrorTUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_height()], width=20, height=10); self.MirrorHeight_USTOP.grid(row=0, column=0)
        self.MirrorHeight= Scale(self.MirrorTUpperFrame,from_=146, to=119, resolution=0.1, orient=VERTICAL, length=400);
        self.MirrorHeight.set(int(self.controller.get_position_mirror_height()));
        self.MirrorHeight.grid(row=1, column=0, padx=10, pady=3)
        self.MirrorHeight.bind("<ButtonRelease-1>", self.moveto_mirror_height); self.MirrorHeight.set(lastpositions[3])
        self.MirrorHeight_OSTOP = Canvas(self.MirrorTUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_height()], width=20, height=10); self.MirrorHeight_OSTOP.grid(row=2, column=0)
        self.MirrorTButtonFrame = Frame(self.MirrorTUpperFrame, width=100, height=150); self.MirrorTButtonFrame.grid(row=1, column=1)
        self.MirrorHeightSpeed = Scale(self.MirrorTButtonFrame,from_=0, to=100000, resolution=1000, orient=HORIZONTAL, length=140, label="Speed"); self.MirrorHeightSpeed.set(self.controller.get_max_speed_mirror_height()); self.MirrorHeightSpeed.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorHeightSpeed.bind("<ButtonRelease-1>", self.new_velocity_mirror_height); self.MirrorHeightSpeed.set(controller.get_max_speed_mirror_height())
        self.MirrorHeightAcc = Scale(self.MirrorTButtonFrame,from_=0, to=20000, resolution=200, orient=HORIZONTAL, length=140, label="Acceleration"); self.MirrorHeightAcc.set(self.controller.get_max_acc_mirror_height());self.MirrorHeightAcc.grid(row=1, column=0, padx=10, pady=3)
        self.MirrorHeightAcc.bind("<ButtonRelease-1>", self.new_acceleration_mirror_height); self.MirrorHeightAcc.set(self.controller.get_max_acc_mirror_height())
        self.MirrorHeightCurrent = Scale(self.MirrorTButtonFrame,from_=0.06, to=1.5, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I"); self.MirrorHeightCurrent.set(self.controller.get_max_current_mirror_height());self.MirrorHeightCurrent.grid(row=2, column=0, padx=10, pady=3)
        self.MirrorHeightCurrent.bind("<ButtonRelease-1>", self.new_current_mirror_height); self.MirrorHeightCurrent.set(controller.get_max_current_mirror_height())
        self.CenterMirrorPos = Button(self.MirrorTButtonFrame, text="Center Mirror Pos", bg="#C0C0C0", width=16, command=self.center_mirror_pos); self.CenterMirrorPos.grid(row=3, column=0)
        self.MirrorZSpeed = Scale(self.MirrorTButtonFrame,from_=0, to=100000, resolution=1000, orient=HORIZONTAL, length=140, label="Speed");  self.MirrorZSpeed.set(controller.get_max_speed_mirror_z()); self.MirrorZSpeed.grid(row=4, column=0, padx=10, pady=3)
        self.MirrorZSpeed.bind("<ButtonRelease-1>", self.new_velocity_mirror_z); self.MirrorZSpeed.set(controller.get_max_speed_mirror_z())
        self.MirrorZAcc = Scale(self.MirrorTButtonFrame,from_=0, to=20000, resolution=200, orient=HORIZONTAL, length=140, label="Acceleration");  self.MirrorZAcc.set(controller.get_max_acc_mirror_z()); self.MirrorZAcc.grid(row=5, column=0, padx=10, pady=3)
        self.MirrorZAcc.bind("<ButtonRelease-1>", self.new_acceleration_mirror_z); self.MirrorZAcc.set(controller.get_max_acc_mirror_z())
        self.MirrorZCurrent = Scale(self.MirrorTButtonFrame,from_=0.06, to=1.44, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I"); self.MirrorZCurrent.grid(row=6, column=0, padx=10, pady=3)
        self.MirrorZCurrent.bind("<ButtonRelease-1>", self.new_current_mirror_z); self.MirrorZCurrent.set(controller.get_max_current_mirror_z())

        self.MirrorTLowerFrame = Frame(self.MirrorTFrame, width=200, height=20); self.MirrorTLowerFrame.grid(row=2, column=0)
        self.leftLabel2 = Label(self.MirrorTLowerFrame, text="Mirror Z"); self.leftLabel2.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorZDisplay = Canvas(self.MirrorTLowerFrame, width=20,height=20); self.MirrorZDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.MirrorZPositionLabel = Label(self.MirrorTLowerFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_max_acc_mirror_height()), width=5); self.MirrorZPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.MirrorZSetButton = Button(self.MirrorTLowerFrame, text="Set", width=2, command=self.set_mirror_z); self.MirrorZSetButton.grid(row=0,column=3)
        self.MirrorZRefsearch = Button(self.MirrorTLowerFrame, text="Ref", width=2, command=self.refsearch_mirror_z); self.MirrorZRefsearch.grid(row=0, column=4)

        self.MirrorTBottomFrame = Frame(self.MirrorTFrame, width=200, height=60); self.MirrorTBottomFrame.grid(row=3, column=0)
        self.MirrorZ_LSTOP = Canvas(self.MirrorTBottomFrame, bg=self.ENDSwitchColors[controller.get_endswitch_lower_mirror_z()], width=10, height=20); self.MirrorZ_LSTOP.grid(row=0, column=0)
        self.MirrorZ = Scale(self.MirrorTBottomFrame, from_=308, to=439, resolution=0.1, orient=HORIZONTAL, length=250); self.MirrorZ.set(self.controller.get_position_mirror_z()); self.MirrorZ.grid(row=0, column=1, padx=10, pady=3)
        self.MirrorZ.bind("<ButtonRelease-1>", self.moveto_mirror_z); self.MirrorZ.set(lastpositions[2])
        self.MirrorZ_RSTOP = Canvas(self.MirrorTBottomFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_z()], width=10, height=20); self.MirrorZ_RSTOP.grid(row=0, column=2)


        #MirrorR-Content
        self.MirrorRHeadFrame = Frame(self.MirrorRFrame, width=200, height=20); self.MirrorRHeadFrame.grid(row=0, column=1)
        self.midLabel1 = Label(self.MirrorRHeadFrame, text="Mirror Psi"); self.midLabel1.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorPsiDisplay = Canvas(self.MirrorRHeadFrame, width=20,height=20); self.MirrorPsiDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.MirrorPsiPositionLabel = Label(self.MirrorRHeadFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_position_mirror_psi()), width=7); self.MirrorPsiPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.MirrorPsiSetButton = Button(self.MirrorRHeadFrame, text="Set", width=2, command=self.set_mirror_psi); self.MirrorPsiSetButton.grid(row=0,column=3)
        self.MirrorPsiRefsearch = Button(self.MirrorRHeadFrame, text="Ref", width=2, command=self.refsearch_mirror_psi); self.MirrorPsiRefsearch.grid(row=0, column=4) 

        self.MirrorRUpperFrame = Frame(self.MirrorRFrame, width=200, height=300); self.MirrorRUpperFrame.grid(row=1, column=1)
        self.MirrorPsi_OSTOP = Canvas(self.MirrorRUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_psi()], width=20, height=10); self.MirrorPsi_OSTOP.grid(row=0, column=0)
        self.MirrorPsi = Scale(self.MirrorRUpperFrame, from_=4.5, to=-4.5, resolution=0.01, orient=VERTICAL, length=400); self.MirrorPsi.set(self.controller.get_position_mirror_psi()); self.MirrorPsi.grid(row=1, column=0, padx=10, pady=3)
        self.MirrorPsi.bind("<ButtonRelease-1>", self.moveto_mirror_psi); self.MirrorPsi.set(lastpositions[4])
        self.MirrorPsi_USTOP = Canvas(self.MirrorRUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_psi()], width=20, height=10); self.MirrorPsi_USTOP.grid(row=2, column=0)
        self.MirrorRButtonFrame = Frame(self.MirrorRUpperFrame, width=100, height=150); self.MirrorRButtonFrame.grid(row=1, column=1)
        self.MirrorPsiSpeed = Scale(self.MirrorRButtonFrame,from_=0, to=10000, resolution=500, orient=HORIZONTAL, length=140, label="Speed"); self.MirrorPsiSpeed.set(self.controller.get_max_speed_mirror_psi()); self.MirrorPsiSpeed.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorPsiSpeed.bind("<ButtonRelease-1>", self.new_velocity_mirror_psi); self.MirrorPsiSpeed.set(self.controller.get_max_speed_mirror_psi())
        self.MirrorPsiAcc = Scale(self.MirrorRButtonFrame,from_=0, to=20000, resolution=200, orient=HORIZONTAL, length=140, label="Motivation");self.MirrorPsiAcc.grid(row=1, column=0, padx=10, pady=3)
        self.MirrorPsiCurrent = Scale(self.MirrorRButtonFrame,from_=0.06, to=0.66, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I"); self.MirrorPsiCurrent.set(self.controller.get_max_current_mirror_height()); self.MirrorPsiCurrent.grid(row=2, column=0, padx=10, pady=3)
        self.MirrorPsiCurrent.bind("<ButtonRelease-1>", self.new_current_mirror_psi); self.MirrorPsiCurrent.set(self.controller.get_max_current_mirror_psi())
        self.B6 = Button(self.MirrorRButtonFrame, text="Center Mirror Angle", bg="#C0C0C0", width=16, command=self.center_mirror_angle); self.B6.grid(row=3, column=0, padx=10, pady=3)
        self.MirrorPhiSpeed = Scale(self.MirrorRButtonFrame,from_=0, to=10000, resolution=500, orient=HORIZONTAL, length=140, label="Speed"); self.MirrorPhiSpeed.set(self.controller.get_max_speed_mirror_phi()); self.MirrorPhiSpeed.grid(row=4, column=0, padx=10, pady=3)
        self.MirrorPhiSpeed.bind("<ButtonRelease-1>", self.new_velocity_mirror_phi); self.MirrorPhiSpeed.set(self.controller.get_max_speed_mirror_phi())
        self.MirrorPhiAcc = Scale(self.MirrorRButtonFrame,from_=0, to=20000, resolution=200, orient=HORIZONTAL, length=140, label="Turning point");self.MirrorPhiAcc.grid(row=5, column=0, padx=10, pady=3)
        self.MirrorPhiCurrent = Scale(self.MirrorRButtonFrame,from_=0.06, to=0.66, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I"); self.MirrorPhiCurrent.set(self.controller.get_max_current_mirror_phi()); self.MirrorPhiCurrent.grid(row=6, column=0, padx=10, pady=3)
        self.MirrorPhiCurrent.bind("<ButtonRelease-1>",self.new_current_mirror_phi); self.MirrorPhiCurrent.set(controller.get_max_current_mirror_phi())

        self.MirrorRLowerFrame = Frame(self.MirrorRFrame, width=200, height=20); self.MirrorRLowerFrame.grid(row=2, column=1)
        self.midLabel2 = Label(self.MirrorRLowerFrame, text="Mirror Phi"); self.midLabel2.grid(row=0, column=0, padx=10, pady=3)
        self.MirrorPhiDisplay = Canvas(self.MirrorRLowerFrame, width=20,height=20); self.MirrorPhiDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.MirrorPhiPositionLabel = Label(self.MirrorRLowerFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_position_mirror_phi()), width=7); self.MirrorPhiPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.MirrorPhiSetButton = Button(self.MirrorRLowerFrame, text="Set", width=2, command=self.set_mirror_phi); self.MirrorPhiSetButton.grid(row=0,column=3)
        self.MirrorPhiRefsearch = Button(self.MirrorRLowerFrame, text="Ref", width=2, command=self.refsearch_mirror_phi); self.MirrorPhiRefsearch.grid(row=0, column=4)

        self.MirrorRBottomFrame = Frame(self.MirrorRFrame, width=200, height=60); self.MirrorRBottomFrame.grid(row=3, column=1)
        self.MirrorPhi_LSTOP = Canvas(self.MirrorRBottomFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_phi()], width=10, height=20); self.MirrorPhi_LSTOP.grid(row=0, column=0)
        self.MirrorPhi = Scale(self.MirrorRBottomFrame, from_=-4.5, to=4.5, resolution=0.01, orient=HORIZONTAL, length=250); self.MirrorPhi.set(self.controller.get_position_mirror_phi()); self.MirrorPhi.grid(row=0, column=1, padx=10, pady=3)
        self.MirrorPhi.bind("<ButtonRelease-1>", self.moveto_mirror_phi); self.MirrorPhi.set(lastpositions[5])
        self.MirrorPhi_RSTOP = Canvas(self.MirrorRBottomFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_phi()], width=10, height=20); self.MirrorPhi_RSTOP.grid(row=0, column=2)


        #Camera-Content
        self.CameraHeadFrame = Frame(self.CameraFrame, width=200, height=20); self.CameraHeadFrame.grid(row=0, column=2)
        self.rightLabel1 = Label(self.CameraHeadFrame, text="Camera X"); self.rightLabel1.grid(row=0, column=0, padx=10, pady=3)
        self.CameraXDisplay = Canvas(self.CameraHeadFrame, width=20,height=20); self.CameraXDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.CameraXPositionLabel = Label(self.CameraHeadFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_position_camera_x()), width=7); self.CameraXPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.CameraXSetButton = Button(self.CameraHeadFrame, text="Set", width=2, command=self.set_camera_x); self.CameraXSetButton.grid(row=0,column=3)
        self.CameraXRefsearch = Button(self.CameraHeadFrame, text="Ref", width=2, command=self.refsearch_camera_x); self.CameraXRefsearch.grid(row=0, column=4)

        self.CameraUpperFrame = Frame(self.CameraFrame, width=200, height=300); self.CameraUpperFrame.grid(row=1, column=2)
        self.CameraX_USTOP = Canvas(self.CameraUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_camera_x()], width=20, height=10); self.CameraX_USTOP.grid(row=0, column=0)
        self.CameraX = Scale(self.CameraUpperFrame, from_=125, to=-127, resolution=0.1, orient=VERTICAL, length=400); self.CameraX.set(self.controller.get_position_camera_x()); self.CameraX.grid(row=1, column=0, padx=10, pady=3)
        self.CameraX.bind("<ButtonRelease-1>", self.moveto_camera_x); self.CameraX.set(lastpositions[1])
        self.CameraX_OSTOP = Canvas(self.CameraUpperFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_camera_x()], width=20, height=10); self.CameraX_OSTOP.grid(row=2, column=0)
        self.CameraButtonFrame = Frame(self.CameraUpperFrame, width=100, height=150); self.CameraButtonFrame.grid(row=1, column=1)
        self.CameraXSpeed = Scale(self.CameraButtonFrame,from_=0, to=100000, resolution=1000, orient=HORIZONTAL, length=140, label="Speed"); self.CameraXSpeed.set(self.controller.get_max_speed_camera_x()); self.CameraXSpeed.grid(row=0, column=0, padx=10, pady=3)
        self.CameraXSpeed.bind("<ButtonRelease-1>", self.new_velocity_camera_x); self.CameraXSpeed.set(self.controller.get_max_speed_camera_x())
        self.CameraXAcc = Scale(self.CameraButtonFrame,from_=1, to=20000, resolution=200, orient=HORIZONTAL, length=140, label="Acceleration"); self.CameraXAcc.set(self.controller.get_max_acc_camera_x()); self.CameraXAcc.grid(row=1, column=0, padx=10, pady=3)
        self.CameraXAcc.bind("<ButtonRelease-1>", self.new_acceleration_camera_x); self.CameraXAcc.set(self.controller.get_max_acc_camera_x())
        self.CameraXCurrent = Scale(self.CameraButtonFrame,from_=0.06, to=1.44, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I"); self.CameraXCurrent.grid(row=2, column=0, padx=10, pady=3)
        self.CameraXCurrent.bind("<ButtonRelease-1>", self.new_current_camera_x); self.CameraXCurrent.set(self.controller.get_max_current_camera_x())
        self.CenterCamera = Button(self.CameraButtonFrame, text="Center Camera X", bg="#C0C0C0", width=16, command=self.center_camera_X); self.CenterCamera.grid(row=3, column=0, padx=10, pady=3)
        self.CameraZSpeed = Scale(self.CameraButtonFrame,from_=0, to=100000, resolution=1000, orient=HORIZONTAL, length=140, label="Speed"); self.CameraZSpeed.set(self.controller.get_max_speed_camera_z()); self.CameraZSpeed.grid(row=4, column=0, padx=10, pady=3)
        self.CameraZSpeed.bind("<ButtonRelease-1>", self.new_velocity_camera_z); self.CameraZSpeed.set(self.controller.get_max_speed_camera_z())
        self.CameraZAcc = Scale(self.CameraButtonFrame,from_=0, to=20000, resolution=200, orient=HORIZONTAL, length=140, label="Acceleration"); self.CameraZAcc.set(controller.get_max_acc_camera_z()); self.CameraZAcc.grid(row=5, column=0, padx=10, pady=3)
        self.CameraZAcc.bind("<ButtonRelease-1>", self.new_acceleration_camera_z); self.CameraZAcc.set(controller.get_max_acc_camera_z())
        self.CameraZCurrent = Scale(self.CameraButtonFrame,from_=0.06, to=1.44, resolution=0.06, orient=HORIZONTAL, length=140, label="Max I"); self.CameraZCurrent.grid(row=6, column=0, padx=10, pady=3)
        self.CameraZCurrent.bind("<ButtonRelease-1>", self.new_current_camera_z); self.CameraZCurrent.set(self.controller.get_max_current_camera_z())


        self.CameraLowerFrame = Frame(self.CameraFrame, width=200, height=20); self.CameraLowerFrame.grid(row=2, column=2)
        self.rightLabel2 = Label(self.CameraLowerFrame, text="Camera Z"); self.rightLabel2.grid(row=0, column=0, padx=10, pady=3)
        self.CameraZDisplay = Canvas(self.CameraLowerFrame, width=20,height=20)
        self.CameraZDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.CameraZPositionLabel = Label(self.CameraLowerFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_position_camera_z()), width=7)
        self.CameraZPositionLabel.grid(row=0, column=2, padx=10, pady=3)
        self.CameraZSetButton = Button(self.CameraLowerFrame, text="Set", width=2, command=self.set_camera_z); self.CameraZSetButton.grid(row=0,column=3)
        self.CameraZRefsearch = Button(self.CameraLowerFrame, text="Ref", width=2, command=self.refsearch_camera_z); self.CameraZRefsearch.grid(row=0, column=4)

        self.CameraBottomFrame = Frame(self.CameraFrame, width=200, height=60); self.CameraBottomFrame.grid(row=3, column=2)
        self.CameraZ_LSTOP = Canvas(self.CameraBottomFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_camera_z()], width=10, height=20); self.CameraZ_LSTOP.grid(row=0, column=0)
        self.CameraZ = Scale(self.CameraBottomFrame, from_= 0, to=131.9, resolution=0.1, orient=HORIZONTAL, length=250); self.CameraZ.set(self.controller.get_position_camera_z()); self.CameraZ.grid(row=0, column=1, padx=10, pady=3)
        self.CameraZ.bind("<ButtonRelease-1>", self.moveto_camera_z); self.CameraZ.set(lastpositions[0])
        self.CameraZ_RSTOP = Canvas(self.CameraBottomFrame, bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_camera_z()], width=10, height=20); self.CameraZ_RSTOP.grid(row=0, column=2)

        #Servo Content
        self.ServoHeadFrame = Frame(self.ServoFrame, width=200, height=20);
        self.ServoHeadFrame.grid(row=0, column=0)
        self.lbl_shutter = Label(self.ServoHeadFrame, text="Shutter");
        self.lbl_shutter.grid(row=0, column=0, padx=10, pady=3, columnspan=2)
        #ServoDisplay = Canvas(ServoHeadFrame, width=20,height=20)
        #ServoDisplay.grid(row=0, column=1, padx=3, pady=3)
        self.ServoOpenButton = Button(self.ServoHeadFrame, text="Open", width=4, command=self.open_shutter);
        self.ServoOpenButton.grid(row=0,column=3)
        self.ServoCloseButton = Button(self.ServoHeadFrame, text="Close", width=4, command=self.close_shutter);
        self.ServoCloseButton.grid(row=0, column=4)

        self.ServoUpperFrame = Frame(self.ServoFrame, width=200, height=300);
        self.ServoUpperFrame.grid(row=1, column=0)
        self.lbl_up = Label(self.ServoUpperFrame, text="0 \N{DEGREE SIGN}")
        self.lbl_down = Label(self.ServoUpperFrame, text="180 \N{DEGREE SIGN}")

        self.Shutter = Scale(self.ServoUpperFrame,from_=0, to=180, orient=HORIZONTAL); self.Shutter.set(self.controller.get_position_servo())
        self.Shutter.bind("<ButtonRelease-1>", self.set_servo); 
        self.lbl_up.grid(row=0, column=0, sticky="e")
        self.Shutter.grid(row=0, column=1, columnspan=2)
        self.lbl_down.grid(row=0, column=3, sticky="w")
        #self.ServoPositionLabel = Label(self.ServoHeadFrame, fg=self.LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(self.controller.get_servo_angle()));
        #self.ServoPositionLabel.grid(row=0, column=2, padx=10, pady=3)

        #Rate-Content
        self.desc_Label_rate = Label(self.RateFrame, text="Photon rate [MHz]"); self.desc_Label_rate.grid(row=4, column=0, padx=5)
        self.desc_Label_rate_A = Label(self.RateFrame, text="Ch A"); self.desc_Label_rate_A.grid(row=4, column=1, padx=3, pady=3)
        self.desc_Label_rate_B = Label(self.RateFrame, text="Ch B"); self.desc_Label_rate_B.grid(row=4, column=3, padx=3, pady=3)
        self.CHa_Label_rate = Label(self.RateFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 15 bold"), width=7);   self.CHa_Label_rate.grid(row=4, column=2, padx=3, pady=3)
        self.CHb_Label_rate = Label(self.RateFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 15 bold"), width=7);   self.CHb_Label_rate.grid(row=4, column=4, padx=3, pady=3)
        self.rateClientButton = Button(self.RateFrame, text="Connect", bg="#cdcfd1", command=self.startStopClient, width=8); self.rateClientButton.grid(row=4,column=5, padx=3, pady=3)

        #Halogen Power supply content
        self.psupp_connectButton = Button(self.psuppFrame, text="Connect\nHalogen", command=self.psupp_connect); self.psupp_connectButton.grid(row=0,column=0)
        self.psupp_onoffButton = Button(self.psuppFrame, command=self.psupp_onoff, state="disabled", text="On/Off"); self.psupp_onoffButton.grid(row=0,column=1)
        self.voltageScale = Scale(self.psuppFrame, from_ = 0.8, to=3.950, resolution=0.05, orient=HORIZONTAL, length=100, label="Voltage (V)", state="disabled")
        self.voltageScale.bind("<ButtonRelease-1>", self.set_step_from_scale)
        self.voltageScale.grid(row=0,column=2)
        
        # Displays with LEDs
        self.MirrorHeightLED = self.MirrorHeightDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0)
        self.MirrorZLED = self.MirrorZDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0) 
        self.MirrorPhiLED = self.MirrorPhiDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0)
        self.MirrorPsiLED = self.MirrorPsiDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0)
        self.CameraXLED = self.CameraXDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0)
        self.CameraZLED = self.CameraZDisplay.create_oval(1,1,19,19, fill=self.LEDColors[0], width=0)

        #Button-Content
        self.img=PhotoImage(file="stepper_items/ecap_blue.png")
        self.ecap = Label(self.buttonFrame, image=self.img, bg="#003366"); self.ecap.grid(row=0,column=0)
        self.titlelabel= Label(self.buttonFrame, text="II Motor Control", font="Helvetica 18 bold", fg="white", bg="#003366"); self.titlelabel.grid(row=1, column=0)
        self.StopAll = Button(self.buttonFrame, text="STOP", font="Helvetica 10 bold", fg="white", bg="#FF0000", width=17, height=7, command=self.stop_all); self.StopAll.grid(row=8, column=0, padx=10, pady=3)
        #B11 = Button(buttonFrame, text ="Update screen", bg="#A9A9A9", width=17, command=update_screen); B11.grid(row=9, column=0, padx=10, pady=3)
        self.globFrame = Frame(self.buttonFrame, bg="#003366"); self.globFrame.grid(row=10,column=0)
        self.AllRefsearch = Button(self.globFrame, text="Ref All", bg="#A9A9A9", width=6, command=self.refsearch_all); self.AllRefsearch.grid(row=0, column=0, padx=1, pady=3)
        self.B15 = Button(self.globFrame, text="Set All", bg="#A9A9A9", width=6, command=self.set_all); self.B15.grid(row=0, column=1, padx=1, pady=3)
        self.optimizationButton = Button(self.buttonFrame, text="Start Rate Analyzer", bg="#A9A9A9", command=self.optimize, width=17); self.optimizationButton.grid(row=11,column=0, padx=1, pady=3)
        self.SavePositions = Button(self.buttonFrame, text="Save current positions", bg="#A9A9A9", width=17, command=self.controller.save_this_position); self.SavePositions.grid(row=12, column=0, padx=10, pady=3)
        self.GoSavedPositions = Button(self.buttonFrame, text="Go to saved position", bg = "#A9A9A9", width=17, command=self.go_to_saved_position); self.GoSavedPositions.grid(row=13, column=0, padx=10, pady=3)
        self.exit_button = Button(self.buttonFrame, text="Save Positions and exit", bg="#A9A9A9", width=17, command=self.exitGUI); self.exit_button.grid(row=14, column=0, padx=10, pady=3)
        
        #Geometry content
        self.desc_Label_pathlength = Label(self.GeometryFrame, text="Estimated Pathlength Difference [mm]"); self.desc_Label_pathlength.grid(row=0, column=0, padx=5)
        self.Label_pathlength = Label(self.GeometryFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 15 bold"), width=7);   self.Label_pathlength.grid(row=0, column=1, padx=3, pady=3)
        self.desc_Label_angle = Label(self.GeometryFrame, text="Estimated Angle of Incidence [degree]"); self.desc_Label_angle.grid(row=1, column=0, padx=5)
        self.Label_angle = Label(self.GeometryFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 15 bold"), width=7);   self.Label_angle.grid(row=1, column=1, padx=3, pady=3)
        self.desc_Label_lens_center = Label(self.GeometryFrame, text="Estimated dist from lens center [mm]"); self.desc_Label_lens_center.grid(row=2, column=0, padx=5)
        self.Label_lens_center = Label(self.GeometryFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 15 bold"), width=7);   self.Label_lens_center.grid(row=2, column=1, padx=3, pady=3)
        


        #Pretty Colors
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
        self.MirrorPsiAcc.config(background = MirrorRColor)
        self.MirrorPhiAcc.config(background = MirrorRColor)

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
        
        GeometryColor = RateColor
        self.GeometryFrame.config(background = GeometryColor)
        self.desc_Label_angle.config(background = GeometryColor)
        self.desc_Label_pathlength.config(background = GeometryColor)
        self.desc_Label_lens_center.config(background = GeometryColor)

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
     
   
    def startStopClient(self):
        if self.client == None:
            client_cache = rcl.rate_client()
            try:
                client_cache.connect()
                self.rateClientButton.config(text="Disconnect")
                self.client=client_cache
                print("Started the rate client. Rates will be displayed once they arrive.")
            except Exception as e:
                print("Could not connect to server. Please check if server address and port are correct!")
                print(e)
        else:
            self.client.stop()
            self.CHa_Label_rate.config(fg="orange")
            self.CHb_Label_rate.config(fg="orange")
            self.rateClientButton.config(text="Connect")
            self.client = None   
    
    #here are the methods triggered by the different button/sclae events
            
    def open_shutter(self):
        self.controller.open_shutter()
        #self.self.Shutter.config(text="180")
        self.Shutter.set(180)
              
    def close_shutter(self):
        self.controller.close_shutter()
        #self.ServoPositionLabel.config(text="0")
        self.Shutter.set(0)
        
    def set_servo(self, event):
        new_pos=int(self.Shutter.get())
        self.controller.set_servo_angle(new_pos)
        self.servoPositionLabel.set(new_pos)
        
    # Halogen power supply commands
    def psupp_connect(self):
        try:
            self.controller.halogen.connect()
        except:
            print ("Error: No power supply found")
        else:
            if self.controller.halogen.on == 1:
                self.psupp_onoffButton.config(text="On")
            else:
                self.psupp_onoffButton.config(text="Off")
            self.psupp_onoffButton.config(state="normal")
            self.voltageScale.config(state="normal")
            self.voltageScale.set(self.controller.halogen.volt)      
            self.psupp_connectButton.config(state="disabled")        
    
    def psupp_onoff(self):
        self.controller.psupp_onoff()
        if self.controller.halogen.on == 1:
            self.psupp_onoffButton.config(text="On")
        else:
            self.psupp_onoffButton.config(text="Off")
            
    def set_step_from_scale(self, val):
        voltage_to_set = float(self.voltageScale.get())
        self.controller.halogen.set_voltage(voltage_to_set)
                  
        
    #tells the update routine to move the motors to the new values of the position scale
    def moveto_mirror_height(self, event):
        self.change_position_mirror_height=True
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
        
    #tells the update routine to update the maximum accelerations 
    def new_acceleration_mirror_height(self, event):
        self.change_acceleration_mirror_height=True
    def new_acceleration_mirror_z(self, event):
        self.change_acceleration_mirror_z=True
    def new_acceleration_mirror_phi(self, event):
        self.change_acceleration_mirror_phi=True
    def new_acceleration_mirror_psi(self, event):
        self.change_acceleration_mirror_psi=True
    def new_acceleration_camera_x(self, event):    
        self.change_acceleration_camera_x=True  
    def new_acceleration_camera_z(self, event):
        self.change_acceleration_camera_z=True
        
    #tells the update routine to update the maximum current 
    def new_current_mirror_height(self, event):
        self.change_current_mirror_height=True
    def new_current_mirror_z(self, event):
        self.change_current_mirror_z=True
    def new_current_mirror_phi(self, event):
        self.change_current_mirror_phi=True
    def new_current_mirror_psi(self, event):
        self.change_current_mirror_psi=True
    def new_current_camera_x(self, event):    
        self.change_current_camera_x=True  
    def new_current_camera_z(self, event):
        self.change_current_camera_z=True
        
    #center each axis
    def center_camera_X(self):
        self.CameraX.set(0)
        self.moveto_camera_x(event=None)
    def center_camera_Z(self):
        self.CameraZ.set(0)
        self.moveto_camera_z(event=None)    
    def center_mirror_pos(self):
        self.MirrorHeight.set(140)
        self.moveto_mirror_height(event=None)
        self.MirrorZ.set(370)    
        self.moveto_mirror_z(event=None)
    def center_mirror_phi(self):
        self.MirrorPhi.set(0)
        self.moveto_mirror_phi(event=None)
    def center_mirror_psi(self):
        self.MirrorPsi.set(0)
        self.moveto_mirror_psi(event=None)
    def center_mirror_angle(self):
        self.center_mirror_phi()
        self.center_mirror_psi()    

    #start refsearches for each axis
    def refsearch_camera_z(self):
        print("Searching for camera z-position 0mm")
        self.WarningStatus[0]=0
        self.controller.refsearch_camera_z()
        self.CameraZ.set(0)
    def refsearch_camera_x(self):
        print("Searching for camera x-position 0mm")
        self.WarningStatus[1]=0
        self.controller.refsearch_camera_x()
        self.CameraX.set(140)  
    def refsearch_mirror_z(self):
        print("Searching for mirror z position 0mm")
        self.WarningStatus[2]=0
        self.controller.refsearch_mirror_z()
        self.MirrorZ.set(100000)
    def refsearch_mirror_height(self):
        print("Searching for mirror height position by moving to the upper limit")
        self.WarningStatus[3]=0
        self.controller.refsearch_mirror_height()
        self.MirrorHeight.set(10000) #This sets the scale to the highest possible value on the scale
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
        self.moveto_mirror_height(event=None)    
    def set_mirror_z(self):
        self.MirrorZ.set(self.controller.get_position_mirror_z())
        self.moveto_mirror_z(event=None)
    def set_mirror_phi(self):
        self.MirrorPhi.set(self.controller.get_position_mirror_height())
        self.moveto_mirror_phi(event=None)
    def set_mirror_psi(self):
        self.MirrorPsi.set(self.controller.get_position_mirror_psi())
        self.moveto_mirror_psi(event=None)
    def set_camera_x(self):
        self.CameraX.set(self.controller.get_position_camera_x())
        self.moveto_camera_x(event=None)
    def set_camera_z(self):
        self.CameraZ.set(self.controller.get_position_camera_z())
        self.moveto_camera_z(event=None)
    def set_all(self):
        self.set_mirror_height()
        self.set_mirror_z()
        self.set_mirror_phi()
        self.set_mirror_psi()
        self.set_camera_x()
        self.set_camera_z()
        
        
    def go_to_saved_position(self):
        new_pos=self.controller.go_to_saved_position()
        self.CameraZ.set(new_pos[0])
        self.CameraX.set(new_pos[1])
        self.MirrorZ.set(new_pos[2])
        self.MirrorHeight.set(new_pos[3])
        self.MirrorPsi.set(new_pos[4])
        self.MirrorPhi.set(new_pos[5])
            
    def openNewDialogue(self):
        self.dialog=DialogFenster(self.master)
        
    def dummy_button(self):
        self.openNewDialogue()
        
    def optimize(self):
        rate_analyzer=RATE_ANALYZER(self.master, self.controller, self.client)
        
    
    def showRateDistribution(self):
        return
    
    def stop_all(self):
        self.controller.stop_all()
        #check if they stopped
        if self.controller.get_camera_z_moving(): self.WarningStatus[0] = 1
        if self.controller.get_camera_x_moving(): self.WarningStatus[1] = 1
        if self.controller.get_mirror_z_moving(): self.WarningStatus[2] = 1
        if self.controller.get_mirror_height_moving(): self.WarningStatus[3] = 1
        if self.controller.get_mirror_psi_moving(): self.WarningStatus[4] = 1
        if self.controller.get_mirror_phi_moving(): self.WarningStatus[5] = 1
    
    def switch_motor(self):
        self.controller.switch_motor()
        if self.controller.get_motor_on():
            self.onoffButton.config(text="ON", bg="#91CC66")
        else:
            self.onoffButton.config(text="OFF", bg="#a3a3a3")
    
    
            
    #-----------------------------------#
    #---- Permanently update screen ----#
    #-----------------------------------#
    def update_items(self, verbose=False):
        #move all positions due to changes since last time
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
            self.change_velocity_camera_z=False   
        if self.change_velocity_camera_x:
            self.controller.set_max_speed_camera_x(self.CameraXSpeed.get(), verbose)
            self.change_velocity_camera_x=False  
        if self.change_velocity_mirror_z:
            self.controller.set_max_speed_mirror_z(self.MirrorZSpeed.get(), verbose)
            self.change_velocity_mirror_z=False
        if self.change_velocity_mirror_height:
            self.controller.set_max_speed_mirror_height(self.MirrorHeightSpeed.get(), verbose)
            self.change_velocity_mirror_height=False
        if self.change_velocity_mirror_psi:
            self.controller.set_max_speed_mirror_psi(self.MirrorPsiSpeed.get(), verbose)
            self.change_velocity_mirror_psi=False 
        if self.change_velocity_mirror_phi:
            self.controller.set_max_speed_mirror_phi(self.MirrorPhiSpeed.get(), verbose)
            self.change_velocity_mirror_phi=False
        #change currents due to changes since last time
        if self.change_current_camera_z:
            self.controller.set_max_current_camera_z(self.CameraZCurrent.get(), verbose)
            self.change_current_camera_z=False   
        if self.change_current_camera_x:
            self.controller.set_max_current_camera_x(self.CameraXCurrent.get(), verbose)
            self.change_current_camera_x=False  
        if self.change_current_mirror_z:
            self.controller.set_max_current_mirror_z(self.MirrorZCurrent.get(), verbose)
            self.change_current_mirror_z=False
        if self.change_current_mirror_height:
            self.controller.set_max_current_mirror_height(self.MirrorHeightCurrent.get(), verbose)
            self.change_current_mirror_height=False
        if self.change_current_mirror_psi:
            self.controller.set_max_current_mirror_psi(self.MirrorPsiCurrent.get(), verbose)
            self.change_current_mirror_psi=False 
        if self.change_current_mirror_phi:
            self.controller.set_max_current_mirror_phi(self.MirrorPhiCurrent.get(), verbose)
            self.change_current_mirror_phi=False
        #change accelerations due to changes since last time
        if self.change_acceleration_camera_z:
            self.controller.set_max_acceleration_camera_z(self.CameraZAcc.get(), verbose)
            self.change_acceleration_camera_z=False   
        if self.change_acceleration_camera_x:
            self.controller.set_max_acceleration_camera_x(self.CameraXAcc.get(), verbose)
            self.change_acceleration_camera_x=False  
        if self.change_acceleration_mirror_z:
            self.controller.set_max_acceleration_mirror_z(self.MirrorZAcc.get(), verbose)
            self.change_acceleration_mirror_z=False
        if self.change_acceleration_mirror_height:
            self.controller.set_max_acceleration_mirror_height(self.MirrorHeightAcc.get(), verbose)
            self.change_acceleration_mirror_height=False
        if self.change_acceleration_mirror_psi:
            self.controller.set_max_acceleration_mirror_psi(self.MirrorPsiAcc.get(), verbose)
            self.change_acceleration_mirror_psi=False 
        if self.change_acceleration_mirror_phi:
            self.controller.set_max_acceleration_mirror_phi(self.MirrorPhiAcc.get(), verbose)
            self.change_acceleration_mirror_phi=False
            
        MHD = self.controller.get_mirror_height_moving()+self.WarningStatus[3]
        if MHD>2:
            MHD=2
        self.MirrorHeightDisplay.itemconfig(self.MirrorHeightLED, fill=self.LEDColors[MHD])
        self.MirrorHeightPositionLabel.config(text="{0:4.1f}".format(self.controller.get_position_mirror_height()))
        self.MirrorHeight_OSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_height()])
        self.MirrorHeight_USTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_height()])   
        self.MirrorZDisplay.itemconfig(self.MirrorZLED, fill=self.LEDColors[self.controller.get_mirror_z_moving()+self.WarningStatus[2]])
        self.MirrorZPositionLabel.config(text="{0:4.1f}".format(self.controller.get_position_mirror_z()))
        self.MirrorZ_LSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_mirror_z()])
        self.MirrorZ_RSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_mirror_z()])
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
        self.CameraXPositionLabel.config(text="{0:4.1f}".format(self.controller.get_position_camera_x()))
        self.CameraXDisplay.itemconfig(self.CameraXLED, fill=self.LEDColors[self.controller.get_camera_x_moving()+self.WarningStatus[1]])
        self.CameraX_OSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_camera_x()])
        self.CameraX_USTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_camera_x()]) 
        self.CameraZPositionLabel.config(text="{0:4.1f}".format(self.controller.get_position_camera_z()))
        self.CameraZDisplay.itemconfig(self.CameraZLED, fill=self.LEDColors[self.controller.get_camera_z_moving()+self.WarningStatus[0]])
        self.CameraZ_LSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_lower_camera_z()])
        self.CameraZ_RSTOP.config(bg=self.ENDSwitchColors[self.controller.get_endswitch_upper_camera_z()])
        
        mirr_phi=self.controller.get_position_mirror_phi()
        mirr_psi=self.controller.get_position_mirror_psi()
        mirr_height=self.controller.get_position_mirror_height()
        mirr_z=self.controller.get_position_mirror_z()
        cam_z=self.controller.get_position_camera_z()
        cam_x=self.controller.get_position_camera_x()
        
        self.Label_angle.config(text="{0:5.2f}".format(geo.get_incident_angle(self.controller.get_position_mirror_phi(), self.controller.get_position_mirror_psi())))
        self.Label_pathlength.config(text="{0:5.2f}".format(geo.get_path_length_delta(mirr_phi, mirr_psi, mirr_height, mirr_z, cam_z, cam_x)))
        lens_dist=geo.get_diff_hit_lens(mirr_phi, mirr_psi, mirr_height, mirr_z, cam_z, cam_x)
        self.Label_lens_center.config(text="{0:5.2f}".format(np.sqrt(lens_dist[0]**2+lens_dist[1]**2)))
       
       
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
            if self.controller.isBussy() or self.controller.getBatch():
                while self.controller.isBussy() or self.controller.getBatch():
                    sleep(1.0)
                    #print("I Know when to stop...")
            #print("update GUI")
            try:
                self.update_items()
            except SerialException:
                print("Serial Exception. This only causes the GUI to miss one update!")
            except IndexError:
                print("Index Error. The reply given by the controller was no valid value. This only causes the GUI to miss one update!")
            except Exception as e:
                print("there was an exception in the update routine of the main GUI. The error was:")
                print(e)
                traceback.print_exc()
            sleep(0.1)
    
    def run(self):
        thread=threading.Thread(target=self.update)
        thread.start()
        
