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

#This class contains all the parts for our Main GUI
class GUI:

	client = None

	LEDColors = []
	LEDColors.append("#737373") #Resting
	LEDColors.append("#ff6600") #Moving
	LEDColors.append("#ff0000") #Warning

	ENDSwitchColors = []
	ENDSwitchColors.append("#ff6600")
	ENDSwitchColors.append("#737373")
	ENDSwitchColors.append("#ff0000")


	WarningStatus=[]
	for i in range (0,6):
		WarningStatus.append(0)

	change_mirror_phi=False
	change_mirror_psi=False
	change_mirror_z=False
	change_mirror_height=False
	change_camera_x=False
	change_camera_z=False

	lastpositions=[]
	readpos = open("stepper_items/current_positions.txt","r")
	for line in readpos:
		lastpositions.append(float(line))
		
	#Tkinter open window
	root = Tk()
	root.wm_title("II Motor Control")
	root.config(background = "#003366")

	#motor postions
	mirror_z_pos = DoubleVar()
	mirror_height_pos = DoubleVar()
	mirror_phi_pos = DoubleVar()
	mirror_psi_pos = DoubleVar()
	camera_x_pos = DoubleVar()
	camera_z_pos = DoubleVar()
	servo_pos = IntVar()
	
	#----------------#
	#---- Frames ----#
	#----------------#
	mainFrame = Frame(root, width=200, height = 400)
	mainFrame.grid(row=0, column=0, padx=10,pady=3)
	mainFrame.config(background = "#003366")

	switchFrame = Frame(mainFrame, width=200, height=20)
	switchFrame.grid(row=0,column=0, padx=10, pady=3)

	MirrorTFrame = Frame(mainFrame, width=200, height=400)
	MirrorTFrame.grid(row=1, column=0, padx=10, pady=3)

	MirrorRFrame = Frame(mainFrame, width=200, height=400)
	MirrorRFrame.grid(row=1, column=1, padx=10, pady=3)

	CameraFrame = Frame(mainFrame, width=200, height=400)
	CameraFrame.grid(row=1, column=2, padx=10, pady=3)

	RateFrame = Frame(mainFrame, width=200, height=40)
	RateFrame.grid(row=0, column=1, pady=3)

	ServoFrame = Frame(mainFrame, width=200, height=40)
	ServoFrame.grid(row=2, column=0, pady=3)

	OptFrame = Frame(mainFrame, width=200, height=40)
	OptFrame.grid(row=2, column=1, pady=3)

	#SwitchFrame Content
	ms.init(); ms.motor_on(); motoron = True
	switchLabel = Label(switchFrame, text="Motor is ")
	switchLabel.grid(row=0, column=0)

	onoffButton = Button(switchFrame, text="ON", bg="#91CC66")


	onoffButton.config(command=switchMotor)
	onoffButton.grid(row=0, column=1)



	#MirrorT-Content
	MirrorTHeadFrame = Frame(MirrorTFrame, width=200, height=20); MirrorTHeadFrame.grid(row=0, column=0, padx=10, pady=3)
	leftLabel1 = Label(MirrorTHeadFrame, text="Mirror Height"); leftLabel1.grid(row=0, column=0, padx=10, pady=3)
	MirrorHeightDisplay = Canvas(MirrorTHeadFrame, width=20,height=20); MirrorHeightDisplay.grid(row=0, column=1, padx=3, pady=3)
	MirrorHeightPositionLabel = Label(MirrorTHeadFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_degree(sd.position(a[3])),2))); MirrorHeightPositionLabel.grid(row=0, column=2, padx=10, pady=3)
	MirrorHeightSetButton = Button(MirrorTHeadFrame, text="Set", width=2, command=set_mirror_height); MirrorHeightSetButton.grid(row=0,column=3)
	B1 = Button(MirrorTHeadFrame, text="Ref", width=2, command=refsearch_mirror_height); B1.grid(row=0, column=4) 

	MirrorTUpperFrame = Frame(MirrorTFrame, width=200, height=300); MirrorTUpperFrame.grid(row=1, column=0)
	MirrorHeight_OSTOP = Canvas(MirrorTUpperFrame, bg=ENDSwitchColors[a[3].axis.get(10)], width=20, height=10); MirrorHeight_OSTOP.grid(row=0, column=0)
	MirrorHeight = Scale(MirrorTUpperFrame, variable=mirror_height_pos,from_=40, to=0, resolution=0.1, orient=VERTICAL, length=300); MirrorHeight.grid(row=1, column=0, padx=10, pady=3)
	MirrorHeight.bind("<ButtonRelease-1>", moveto_mirror_height); MirrorHeight.set(lastpositions[3])
	MirrorHeight_USTOP = Canvas(MirrorTUpperFrame, bg=ENDSwitchColors[a[3].axis.get(11)], width=20, height=10); MirrorHeight_USTOP.grid(row=2, column=0)
	MirrorTButtonFrame = Frame(MirrorTUpperFrame, width=100, height=150); MirrorTButtonFrame.grid(row=1, column=1)
	MirrorHeightSpeed = Scale(MirrorTButtonFrame,from_=0, to=5000, resolution=50, variable=v_current[3], orient=HORIZONTAL, length=140, label="Speed"); MirrorHeightSpeed.grid(row=0, column=0, padx=10, pady=3)
	MirrorHeightSpeed.bind("<ButtonRelease-1>", set_max_speed_mirror_height); MirrorHeightSpeed.set(v_start[3])
	MirrorHeightCurrent = Scale(MirrorTButtonFrame,from_=0.06, to=1.92, resolution=0.06, variable=I_current[3], orient=HORIZONTAL, length=140, label="Max I"); MirrorHeightCurrent.grid(row=1, column=0, padx=10, pady=3)
	MirrorHeightAcc = Scale(MirrorTButtonFrame,from_=1, to=300, resolution=1, variable=a_current[3], orient=HORIZONTAL, length=140, label="Acceleration"); MirrorHeightAcc.grid(row=1, column=0, padx=10, pady=3)
	MirrorHeightAcc.bind("<ButtonRelease-1>", set_max_acc_mirror_height); MirrorHeightAcc.set(a_start[3])
	MirrorHeightCurrent = Scale(MirrorTButtonFrame,from_=50, to=300, resolution=1, variable=I_current[3], orient=HORIZONTAL, length=140, label="Max I"); MirrorHeightCurrent.grid(row=2, column=0, padx=10, pady=3)
	MirrorHeightCurrent.bind("<ButtonRelease-1>", set_max_current_mirror_height); MirrorHeightCurrent.set(I_start[3])
	B3 = Button(MirrorTButtonFrame, text="Center Mirror Pos", bg="#C0C0C0", width=16, command=center_mirror_pos); B3.grid(row=2, column=0)
	MirrorZSpeed = Scale(MirrorTButtonFrame,from_=0, to=5000, resolution=50, variable=v_current[2], orient=HORIZONTAL, length=140, label="Speed"); MirrorZSpeed.grid(row=3, column=0, padx=10, pady=3)
	MirrorZSpeed.bind("<ButtonRelease-1>", set_max_speed_mirror_z); MirrorZSpeed.set(v_start[2])
	MirrorZCurrent = Scale(MirrorTButtonFrame,from_=0.06, to=1.44, resolution=0.06, variable=I_current[2], orient=HORIZONTAL, length=140, label="Max I"); MirrorZCurrent.grid(row=4, column=0, padx=10, pady=3)
	MirrorZAcc = Scale(MirrorTButtonFrame,from_=1, to=300, resolution=1, variable=a_current[2], orient=HORIZONTAL, length=140, label="Acceleration"); MirrorZAcc.grid(row=5, column=0, padx=10, pady=3)
	MirrorZAcc.bind("<ButtonRelease-1>", set_max_acc_mirror_z); MirrorZAcc.set(a_start[2])
	MirrorZCurrent = Scale(MirrorTButtonFrame,from_=50, to=300, resolution=1, variable=I_current[2], orient=HORIZONTAL, length=140, label="Max I"); MirrorZCurrent.grid(row=6, column=0, padx=10, pady=3)
	MirrorZCurrent.bind("<ButtonRelease-1>", set_max_current_mirror_z); MirrorZCurrent.set(I_start[2])

	MirrorTLowerFrame = Frame(MirrorTFrame, width=200, height=20); MirrorTLowerFrame.grid(row=2, column=0)
	leftLabel2 = Label(MirrorTLowerFrame, text="Mirror Z"); leftLabel2.grid(row=0, column=0, padx=10, pady=3)
	MirrorZDisplay = Canvas(MirrorTLowerFrame, width=20,height=20); MirrorZDisplay.grid(row=0, column=1, padx=3, pady=3)
	MirrorZPositionLabel = Label(MirrorTLowerFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_mm(sd.position(a[2])),2))); MirrorZPositionLabel.grid(row=0, column=2, padx=10, pady=3)
	MirrorZSetButton = Button(MirrorTLowerFrame, text="Set", width=2, command=set_mirror_z); MirrorZSetButton.grid(row=0,column=3)
	B2 = Button(MirrorTLowerFrame, text="Ref", width=2, command=refsearch_mirror_z); B2.grid(row=0, column=4)

	MirrorTBottomFrame = Frame(MirrorTFrame, width=200, height=60); MirrorTBottomFrame.grid(row=3, column=0)
	MirrorZ_LSTOP = Canvas(MirrorTBottomFrame, bg=ENDSwitchColors[a[2].axis.get(10)], width=10, height=20); MirrorZ_LSTOP.grid(row=0, column=0)
	MirrorZ = Scale(MirrorTBottomFrame, variable=mirror_z_pos, from_=0, to=120, resolution=0.1, orient=HORIZONTAL, length=250); MirrorZ.grid(row=0, column=1, padx=10, pady=3)
	MirrorZ.bind("<ButtonRelease-1>", moveto_mirror_z); MirrorZ.set(lastpositions[2])
	MirrorZ_RSTOP = Canvas(MirrorTBottomFrame, bg=ENDSwitchColors[a[2].axis.get(11)], width=10, height=20); MirrorZ_RSTOP.grid(row=0, column=2)


	#MirrorR-Content
	MirrorRHeadFrame = Frame(MirrorRFrame, width=200, height=20); MirrorRHeadFrame.grid(row=0, column=0)
	midLabel1 = Label(MirrorRHeadFrame, text="Mirror Psi"); midLabel1.grid(row=0, column=0, padx=10, pady=3)
	MirrorPsiDisplay = Canvas(MirrorRHeadFrame, width=20,height=20); MirrorPsiDisplay.grid(row=0, column=1, padx=3, pady=3)
	MirrorPsiPositionLabel = Label(MirrorRHeadFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_degree(sd.position(a[4])),2))); MirrorPsiPositionLabel.grid(row=0, column=2, padx=10, pady=3)
	MirrorPsiSetButton = Button(MirrorRHeadFrame, text="Set", width=2, command=set_mirror_psi); MirrorPsiSetButton.grid(row=0,column=3)
	B4 = Button(MirrorRHeadFrame, text="Ref", width=2, command=refsearch_mirror_psi); B4.grid(row=0, column=4) 

	MirrorRUpperFrame = Frame(MirrorRFrame, width=200, height=300); MirrorRUpperFrame.grid(row=1, column=0)
	MirrorPsi_OSTOP = Canvas(MirrorRUpperFrame, bg=ENDSwitchColors[a[4].axis.get(10)], width=20, height=10); MirrorPsi_OSTOP.grid(row=0, column=0)
	MirrorPsi = Scale(MirrorRUpperFrame, variable=mirror_psi_pos,from_=4.5, to=-4.5, resolution=0.01, orient=VERTICAL, length=300); MirrorPsi.grid(row=1, column=0, padx=10, pady=3)
	MirrorPsi.bind("<ButtonRelease-1>", moveto_mirror_psi); MirrorPsi.set(lastpositions[4])
	MirrorPsi_USTOP = Canvas(MirrorRUpperFrame, bg=ENDSwitchColors[a[4].axis.get(10)], width=20, height=10); MirrorPsi_USTOP.grid(row=2, column=0)
	MirrorRButtonFrame = Frame(MirrorRUpperFrame, width=100, height=150); MirrorRButtonFrame.grid(row=1, column=1)
	MirrorPsiSpeed = Scale(MirrorRButtonFrame,from_=0, to=10000, resolution=500, variable=v_current[4], orient=HORIZONTAL, length=140, label="Speed"); MirrorPsiSpeed.grid(row=0, column=0, padx=10, pady=3)
	MirrorPsiSpeed.bind("<ButtonRelease-1>", set_max_speed_mirror_psi); MirrorPsiSpeed.set(v_start[4])
	MirrorPsiCurrent = Scale(MirrorRButtonFrame,from_=0.06, to=0.66, resolution=0.06, variable=I_current[4], orient=HORIZONTAL, length=140, label="Max I"); MirrorPsiCurrent.grid(row=1, column=0, padx=10, pady=3)
	MirrorPsiCurrent.bind("<ButtonRelease-1>", set_max_current_mirror_psi); MirrorPsiCurrent.set(I_start[4])
	B6 = Button(MirrorRButtonFrame, text="Center Mirror Angle", bg="#C0C0C0", width=16, command=center_mirror_angle); B6.grid(row=2, column=0, padx=10, pady=3)
	MirrorPhiSpeed = Scale(MirrorRButtonFrame,from_=0, to=10000, resolution=500, variable=v_current[5], orient=HORIZONTAL, length=140, label="Speed"); MirrorPhiSpeed.grid(row=3, column=0, padx=10, pady=3)
	MirrorPhiSpeed.bind("<ButtonRelease-1>", set_max_speed_mirror_phi); MirrorPhiSpeed.set(v_start[5])
	MirrorPhiCurrent = Scale(MirrorRButtonFrame,from_=0.06, to=0.66, resolution=0.06, variable=I_current[5], orient=HORIZONTAL, length=140, label="Max I"); MirrorPhiCurrent.grid(row=4, column=0, padx=10, pady=3)
	MirrorPhiCurrent.bind("<ButtonRelease-1>", set_max_current_mirror_phi); MirrorPhiCurrent.set(I_start[5])

	MirrorRLowerFrame = Frame(MirrorRFrame, width=200, height=20); MirrorRLowerFrame.grid(row=2, column=0)
	midLabel2 = Label(MirrorRLowerFrame, text="Mirror Phi"); midLabel2.grid(row=0, column=0, padx=10, pady=3)
	MirrorPhiDisplay = Canvas(MirrorRLowerFrame, width=20,height=20); MirrorPhiDisplay.grid(row=0, column=1, padx=3, pady=3)
	MirrorPhiPositionLabel = Label(MirrorRLowerFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_degree(sd.position(a[5])),2))); MirrorPhiPositionLabel.grid(row=0, column=2, padx=10, pady=3)
	MirrorPhiSetButton = Button(MirrorRLowerFrame, text="Set", width=2, command=set_mirror_phi); MirrorPhiSetButton.grid(row=0,column=3)
	B5 = Button(MirrorRLowerFrame, text="Ref", width=2, command=refsearch_mirror_phi); B5.grid(row=0, column=4)

	MirrorRBottomFrame = Frame(MirrorRFrame, width=200, height=60); MirrorRBottomFrame.grid(row=3, column=0)
	MirrorPhi_LSTOP = Canvas(MirrorRBottomFrame, bg=ENDSwitchColors[a[5].axis.get(10)], width=10, height=20); MirrorPhi_LSTOP.grid(row=0, column=0)
	MirrorPhi = Scale(MirrorRBottomFrame, variable=mirror_phi_pos,from_=-4.5, to=4.5, resolution=0.01, orient=HORIZONTAL, length=300); MirrorPhi.grid(row=0, column=1, padx=10, pady=3)
	MirrorPhi.bind("<ButtonRelease-1>", moveto_mirror_phi); MirrorPhi.set(lastpositions[5])
	MirrorPhi_RSTOP = Canvas(MirrorRBottomFrame, bg=ENDSwitchColors[a[5].axis.get(10)], width=10, height=20); MirrorPhi_RSTOP.grid(row=0, column=2)


	#Camera-Content
	CameraHeadFrame = Frame(CameraFrame, width=200, height=20); CameraHeadFrame.grid(row=0, column=0)
	rightLabel1 = Label(CameraHeadFrame, text="Camera X"); rightLabel1.grid(row=0, column=0, padx=10, pady=3)
	CameraXDisplay = Canvas(CameraHeadFrame, width=20,height=20); CameraXDisplay.grid(row=0, column=1, padx=3, pady=3)
	CameraXPositionLabel = Label(CameraHeadFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_mm(sd.position(a[3])),1))); CameraXPositionLabel.grid(row=0, column=2, padx=10, pady=3)
	CameraXSetButton = Button(CameraHeadFrame, text="Set", width=2, command=set_camera_x); CameraXSetButton.grid(row=0,column=3)
	B7 = Button(CameraHeadFrame, text="Ref", width=2, command=refsearch_camera_x); B7.grid(row=0, column=4)

	CameraUpperFrame = Frame(CameraFrame, width=200, height=300); CameraUpperFrame.grid(row=1, column=0)
	CameraX_OSTOP = Canvas(CameraUpperFrame, bg=ENDSwitchColors[a[1].axis.get(10)], width=20, height=10); CameraX_OSTOP.grid(row=0, column=0)
	CameraX = Scale(CameraUpperFrame, variable=camera_x_pos,from_=130, to=0, resolution=0.1, orient=VERTICAL, length=300); CameraX.grid(row=1, column=0, padx=10, pady=3)
	CameraX.bind("<ButtonRelease-1>", moveto_camera_x); CameraX.set(lastpositions[1])
	CameraX_USTOP = Canvas(CameraUpperFrame, bg=ENDSwitchColors[a[1].axis.get(11)], width=20, height=10); CameraX_USTOP.grid(row=2, column=0)
	CameraButtonFrame = Frame(CameraUpperFrame, width=100, height=150); CameraButtonFrame.grid(row=1, column=1)
	CameraXSpeed = Scale(CameraButtonFrame,from_=0, to=5000, resolution=50, variable=v_current[1], orient=HORIZONTAL, length=140, label="Speed"); CameraXSpeed.grid(row=0, column=0, padx=10, pady=3)
	CameraXSpeed.bind("<ButtonRelease-1>", set_max_speed_camera_x); CameraXSpeed.set(v_start[1])
	CameraXCurrent = Scale(CameraButtonFrame,from_=0.06, to=1.44, resolution=0.06, variable=I_current[1], orient=HORIZONTAL, length=140, label="Max I"); CameraXCurrent.grid(row=1, column=0, padx=10, pady=3)
	CameraXAcc = Scale(CameraButtonFrame,from_=1, to=2047, resolution=1, variable=a_current[1], orient=HORIZONTAL, length=140, label="Acceleration"); CameraXAcc.grid(row=1, column=0, padx=10, pady=3)
	CameraXAcc.bind("<ButtonRelease-1>", set_max_acc_camera_x); CameraXAcc.set(a_start[1])
	CameraXCurrent = Scale(CameraButtonFrame,from_=10, to=255, resolution=1, variable=I_current[1], orient=HORIZONTAL, length=140, label="Max I"); CameraXCurrent.grid(row=2, column=0, padx=10, pady=3)
	CameraXCurrent.bind("<ButtonRelease-1>", set_max_current_camera_x); CameraXCurrent.set(I_start[1])
	B9 = Button(CameraButtonFrame, text="Center Camera", bg="#C0C0C0", width=16, command=center_camera); B9.grid(row=2, column=0, padx=10, pady=3)
	CameraZSpeed = Scale(CameraButtonFrame,from_=0, to=5000, resolution=50, variable=v_current[0], orient=HORIZONTAL, length=140, label="Speed"); CameraZSpeed.grid(row=3, column=0, padx=10, pady=3)
	CameraZSpeed.bind("<ButtonRelease-1>", set_max_speed_camera_z); CameraZSpeed.set(v_start[0])
	CameraZCurrent = Scale(CameraButtonFrame,from_=0.06, to=1.44, resolution=0.06, variable=I_current[0], orient=HORIZONTAL, length=140, label="Max I"); CameraZCurrent.grid(row=4, column=0, padx=10, pady=3)
	CameraZAcc = Scale(CameraButtonFrame,from_=1, to=2047, resolution=1, variable=a_current[0], orient=HORIZONTAL, length=140, label="Acceleration"); CameraZAcc.grid(row=5, column=0, padx=10, pady=3)
	CameraZAcc.bind("<ButtonRelease-1>", set_max_acc_camera_z); CameraZAcc.set(a_start[0])
	CameraZCurrent = Scale(CameraButtonFrame,from_=10, to=255, resolution=1, variable=I_current[0], orient=HORIZONTAL, length=140, label="Max I"); CameraZCurrent.grid(row=6, column=0, padx=10, pady=3)
	CameraZCurrent.bind("<ButtonRelease-1>", set_max_current_camera_z); CameraZCurrent.set(I_start[0])


	CameraLowerFrame = Frame(CameraFrame, width=200, height=20); CameraLowerFrame.grid(row=2, column=0)
	rightLabel2 = Label(CameraLowerFrame, text="Camera Z"); rightLabel2.grid(row=0, column=0, padx=10, pady=3)
	CameraZDisplay = Canvas(CameraLowerFrame, width=20,height=20)
	CameraZDisplay.grid(row=0, column=1, padx=3, pady=3)
	CameraZPositionLabel = Label(CameraLowerFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_mm(sd.position(a[0])),2)))
	CameraZPositionLabel.grid(row=0, column=2, padx=10, pady=3)
	CameraZSetButton = Button(CameraLowerFrame, text="Set", width=2, command=set_camera_z); CameraZSetButton.grid(row=0,column=3)
	B8 = Button(CameraLowerFrame, text="Ref", width=2, command=refsearch_camera_z); B8.grid(row=0, column=4)

	CameraBottomFrame = Frame(CameraFrame, width=200, height=60); CameraBottomFrame.grid(row=3, column=0)
	CameraZ_LSTOP = Canvas(CameraBottomFrame, bg=ENDSwitchColors[a[0].axis.get(10)], width=10, height=20); CameraZ_LSTOP.grid(row=0, column=0)
	CameraZ = Scale(CameraBottomFrame,variable=camera_z_pos, from_= 150, to=0, resolution=0.1, orient=HORIZONTAL, length=250); CameraZ.grid(row=0, column=1, padx=10, pady=3)
	CameraZ.bind("<ButtonRelease-1>", moveto_camera_z); CameraZ.set(lastpositions[0])
	CameraZ_RSTOP = Canvas(CameraBottomFrame, bg=ENDSwitchColors[a[0].axis.get(11)], width=10, height=20); CameraZ_RSTOP.grid(row=0, column=2)

	#Servo Content
	ServoHeadFrame = Frame(ServoFrame, width=200, height=20);
	ServoHeadFrame.grid(row=0, column=0)
	lbl_shutter = Label(ServoHeadFrame, text="Shutter");
	lbl_shutter.grid(row=0, column=0, padx=10, pady=3, columnspan=2)
	#ServoDisplay = Canvas(ServoHeadFrame, width=20,height=20)
	#ServoDisplay.grid(row=0, column=1, padx=3, pady=3)

	OpenButton = Button(ServoHeadFrame, text="Open", width=4, command=open_shutter);
	OpenButton.grid(row=0,column=3)
	CloseButton = Button(ServoHeadFrame, text="Close", width=4, command=close_shutter);
	CloseButton.grid(row=0, column=4)

	ServoUpperFrame = Frame(ServoFrame, width=200, height=300);
	ServoUpperFrame.grid(row=1, column=0)
	lbl_up = Label(ServoUpperFrame, text="0 \N{DEGREE SIGN}")
	lbl_down = Label(ServoUpperFrame, text="180 \N{DEGREE SIGN}")

	Shutter = Scale(ServoUpperFrame,from_=0, to=180, orient=HORIZONTAL, variable=servo_pos);
	Shutter.bind("<ButtonRelease-1>", shutter_scale); 
	lbl_up.grid(row=0, column=0, sticky="e")
	Shutter.grid(row=0, column=1, columnspan=2)
	lbl_down.grid(row=0, column=3, sticky="w")
	ServoPositionLabel = Label(ServoHeadFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(servo_angle));
	ServoPositionLabel.grid(row=0, column=2, padx=10, pady=3)

	#Rate-Content
	desc_Label_rate = Label(RateFrame, text="Photon rate [MHz]"); desc_Label_rate.grid(row=4, column=0, padx=5)
	desc_Label_rate_A = Label(RateFrame, text="Ch A"); desc_Label_rate_A.grid(row=4, column=1, padx=3, pady=3)
	desc_Label_rate_B = Label(RateFrame, text="Ch B"); desc_Label_rate_B.grid(row=4, column=3, padx=3, pady=3)
	CHa_Label_rate = Label(RateFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 15 bold"), width=7);   CHa_Label_rate.grid(row=4, column=2, padx=3, pady=3)
	CHb_Label_rate = Label(RateFrame, text="0.0", fg="orange", bg="black", font=("Helvetica 15 bold"), width=7);   CHb_Label_rate.grid(row=4, column=4, padx=3, pady=3)
	rateClientButton = Button(RateFrame, text="Connect", bg="#cdcfd1", command=startStopClient, width=8); rateClientButton.grid(row=4,column=5, padx=3, pady=3)

	#optimziation content
	optimizationButton = Button(OptFrame, text="optimize Mirrors", bg="#cdcfd1", command=optimize, width=16); optimizationButton.grid(row=4,column=5, padx=3, pady=3)
	scanButton = Button(OptFrame, text="plot Mirrors", bg="#cdcfd1", command=showRateDistribution, width=16); scanButton.grid(row=4,column=6, padx=3, pady=3)
	dummyButton = Button(OptFrame, text="dummy Button", bg="#cdcfd1", command=dummy_button, width=16); dummyButton.grid(row=4,column=7, padx=3, pady=3)


	# Displays with LEDs
	MirrorHeightLED = MirrorHeightDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)
	MirrorZLED = MirrorZDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)
		
	MirrorPhiLED = MirrorPhiDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)
	MirrorPsiLED = MirrorPsiDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)

	CameraXLED = CameraXDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)
	CameraZLED = CameraZDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)

	#ServoLED = ServoDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)
	
	#ButtonFrame
	buttonFrame = Frame(root, width=30, height = 400, bg="#003366"); buttonFrame.grid(row=0, column=1, padx=10,pady=3)
	img=PhotoImage(file="stepper_items/ecap_blue.png")
	ecap = Label(buttonFrame, image=img, bg="#003366"); ecap.grid(row=0,column=0)
	titlelabel= Label(buttonFrame, text="II Motor Control", font="Helvetica 18 bold", fg="white", bg="#003366"); titlelabel.grid(row=1, column=0)
	B10 = Button(buttonFrame, text="STOP", font="Helvetica 10 bold", fg="white", bg="#FF0000", width=17, height=7, command=stop_all); B10.grid(row=8, column=0, padx=10, pady=3)
	B11 = Button(buttonFrame, text ="Update screen", bg="#A9A9A9", width=17, command=update_screen); B11.grid(row=9, column=0, padx=10, pady=3)
	globFrame = Frame(buttonFrame, bg="#003366"); globFrame.grid(row=10,column=0)
	B12 = Button(globFrame, text="Ref All", bg="#A9A9A9", width=6, command=refsearch_all); B12.grid(row=0, column=0, padx=1, pady=3)
	B15 = Button(globFrame, text="Set All", bg="#A9A9A9", width=6, command=set_all); B15.grid(row=0, column=1, padx=1, pady=3)
	B13 = Button(buttonFrame, text="Save current positions", bg="#A9A9A9", width=17, command=save_this_position); B13.grid(row=11, column=0, padx=10, pady=3)
	B14 = Button(buttonFrame, text="Go to saved position", bg = "#A9A9A9", width=17, command=goto_saved_position); B14.grid(row=12, column=0, padx=10, pady=3)
	exit_button = Button(buttonFrame, text="Save Positions and exit", bg="#A9A9A9", width=17, command=exitGUI); exit_button.grid(row=13, column=0, padx=10, pady=3)




	#Hübsche Farben
	MirrorTColor = "#b3daff"
	MirrorTFrame.config(background = MirrorTColor)
	MirrorTHeadFrame.config(background = MirrorTColor)
	leftLabel1.config(background = MirrorTColor)
	MirrorHeightDisplay.config(background = MirrorTColor)
	MirrorTUpperFrame.config(background = MirrorTColor)
	MirrorHeight.config(background = MirrorTColor)
	MirrorHeightSpeed.config(background = MirrorTColor)
	MirrorHeightAcc.config(background = MirrorTColor)
	MirrorHeightCurrent.config(background = MirrorTColor)
	MirrorTButtonFrame.config(background = MirrorTColor)
	MirrorTLowerFrame.config(background = MirrorTColor)
	leftLabel2.config(background = MirrorTColor)
	MirrorZDisplay.config(background = MirrorTColor)
	MirrorTBottomFrame.config(background = MirrorTColor)
	MirrorZ.config(background = MirrorTColor)
	MirrorZSpeed.config(background = MirrorTColor)
	MirrorZAcc.config(background = MirrorTColor)
	MirrorZCurrent.config(background = MirrorTColor)

	MirrorRColor = "#66b5ff"
	MirrorRFrame.config(background = MirrorRColor)
	MirrorRHeadFrame.config(background = MirrorRColor)
	midLabel1.config(background = MirrorRColor)
	MirrorPhiDisplay.config(background = MirrorRColor)
	MirrorRUpperFrame.config(background = MirrorRColor)
	MirrorPhi.config(background = MirrorRColor)
	MirrorPhiSpeed.config(background = MirrorRColor)
	MirrorPhiCurrent.config(background = MirrorRColor)
	MirrorRButtonFrame.config(background = MirrorRColor)
	MirrorRLowerFrame.config(background = MirrorRColor)
	midLabel2.config(background = MirrorRColor)
	MirrorPsiDisplay.config(background = MirrorRColor)
	MirrorRBottomFrame.config(background = MirrorRColor)
	MirrorPsi.config(background = MirrorRColor)
	MirrorPsiSpeed.config(background = MirrorRColor)
	MirrorPsiCurrent.config(background = MirrorRColor)

	CameraColor = "#ccff99"
	CameraFrame.config(background = CameraColor)
	CameraHeadFrame.config(background = CameraColor)
	rightLabel1.config(background = CameraColor)
	CameraXDisplay.config(background = CameraColor)
	CameraUpperFrame.config(background = CameraColor)
	CameraX.config(background = CameraColor)
	CameraXSpeed.config(background = CameraColor)
	CameraXAcc.config(background = CameraColor)
	CameraXCurrent.config(background = CameraColor)
	CameraButtonFrame.config(background = CameraColor)
	CameraLowerFrame.config(background = CameraColor)
	rightLabel2.config(background = CameraColor)
	CameraZDisplay.config(background = CameraColor)
	CameraBottomFrame.config(background = CameraColor)
	CameraZ.config(background = CameraColor)
	CameraZSpeed.config(background = CameraColor)
	CameraZAcc.config(background = CameraColor)
	CameraZCurrent.config(background = CameraColor)

	RateColor = "#b3daff"
	RateFrame.config(background = RateColor)
	desc_Label_rate.config(background = RateColor)
	desc_Label_rate_A.config(background = RateColor)
	desc_Label_rate_B.config(background = RateColor)

	ServoColor = "cornsilk"
	ServoFrame.config(bg=ServoColor)
	ServoHeadFrame.config(bg=ServoColor)
	lbl_shutter.config(bg=ServoColor)
	#ServoDisplay.config(bg=ServoColor)
	ServoUpperFrame.config(bg=ServoColor)
	lbl_up.config(bg=ServoColor)
	lbl_down.config(bg=ServoColor)
	Shutter.config(bg=ServoColor)

	#initalize Fahrbalken correctly
	CameraZ.set(round(steps_to_mm(sd.position(a[0])),2))
	CameraX.set(round(steps_to_mm(sd.position(a[1])),2))
	MirrorZ.set(round(steps_to_mm(sd.position(a[2])),2))
	MirrorHeight.set(round(steps_to_mm(sd.position(a[3])),2))
	MirrorPsi.set(round(steps_to_degree(sd.position(a[4])),2))
	MirrorPhi.set(round(steps_to_degree(sd.position(a[5])),2))
	
	#exit gui
	def exitGUI():
		servo.shutter_clean(90)
		global client
		savepos = open("stepper_items/current_positions.txt","w")
		for i in range (0,3):
		    savepos.write(str(steps_to_mm(sd.position(a[i])))+"\n")
		savepos.write(str(steps_to_hmm(sd.position(a[3])))+"\n")
		for i in range (4,6):
		    savepos.write(str(steps_to_degree(sd.position(a[i])))+"\n")        
		savepos.close()
		if client != None:
		    client.stop()
		    client = None
		root.destroy()

	#save postions
	def save_this_position():
		thispos = open("stepper_items/saved_position.txt","w")
		for i in range (0,3):
		    thispos.write(str(steps_to_mm(sd.position(a[i])))+"\n")
		thispos.write(str(steps_to_hmm(sd.position(a[3])))+"\n")
		for i in range (4,6):
		    thispos.write(str(steps_to_degree(sd.position(a[i])))+"\n")
		    
    
	v_start = []; v_current = []
	for i in range (0,6):
		v_start.append(a[i].axis.max_positioning_speed)
		v_current.append(DoubleVar())
	def set_max_speed_camera_z(val):
		a[0].axis.max_positioning_speed = v_current[0].get()
		print ("Set Camera Z speed limit to {}".format(a[0].axis.max_positioning_speed))
	def set_max_speed_camera_x(val):
		a[1].axis.max_positioning_speed = v_current[1].get()
		print ("Set Camera X speed limit to {}".format(a[1].axis.max_positioning_speed))
	def set_max_speed_mirror_z(val):
		a[2].axis.max_positioning_speed = v_current[2].get()
		print ("Set Mirror Z speed limit to {}".format(a[2].axis.max_positioning_speed))
	def set_max_speed_mirror_height(val):
		a[3].axis.max_positioning_speed = v_current[3].get()
		print ("Set Mirror Height speed limit to {}".format(a[3].axis.max_positioning_speed))
	def set_max_speed_mirror_psi(val):
		a[4].axis.max_positioning_speed = v_current[4].get()
		print ("Set Mirror Psi speed limit to {}".format(a[4].axis.max_positioning_speed))
	def set_max_speed_mirror_phi(val):
		a[5].axis.max_positioning_speed = v_current[5].get()
		print ("Set Mirror Phi speed limit to {}".format(a[5].axis.max_positioning_speed))
		
	
	def startStopClient():
		global client
		if client == None:
		    client_cache = rcl.rate_client()
		    try:
		        client_cache.connect()
		        rateClientButton.config(text="Disconnect")
		        client=client_cache
		        print("Started the rate client. Rates will be displayed once they arrive.")
		    except:
		        print("Could not connect to server. Please check if server address and port are correct!")
		else:
		    client.stop()
		    CHa_Label_rate.config(fg="orange")
		    CHb_Label_rate.config(fg="orange")
		    rateClientButton.config(text="Connect")
		    client = None	
	
	# Current regulation
	I_start = []; I_current = []
	for i in range (0, 6):
		I_start.append(n_to_i(a[i].get_axis_parameter(6)))
		I_current.append(DoubleVar())
	def set_max_current_camera_z(val):
		a[0].set_axis_parameter(6,i_to_n(I_current[0].get()))
		print ("Set Camera Z current limit to {}".format(n_to_i(a[0].get_axis_parameter(6))))
	def set_max_current_camera_x(val):
		a[1].set_axis_parameter(6,i_to_n(I_current[1].get()))
		print ("Set Camera X current limit to {}".format(n_to_i(a[1].get_axis_parameter(6))))
	def set_max_current_mirror_z(val):
		a[2].set_axis_parameter(6,i_to_n(I_current[2].get()))
		print ("Set Mirror Z current limit to {}".format(n_to_i(a[2].get_axis_parameter(6))))
	def set_max_current_mirror_height(val):
		a[3].set_axis_parameter(6,i_to_n(I_current[3].get()))
		print ("Set Mirror Height current limit to {}".format(n_to_i(a[3].get_axis_parameter(6))))
	def set_max_current_mirror_psi(val):
		a[4].set_axis_parameter(6,i_to_n(I_current[4].get()))
		print ("Set Mirror Psi current limit to {}".format(n_to_i(a[4].get_axis_parameter(6))))
	def set_max_current_mirror_phi(val):
		a[5].set_axis_parameter(6,i_to_n(I_current[5].get()))
		print ("Set Mirror Phi current limit to {}".format(n_to_i(a[5].get_axis_parameter(6))))

	# Acceleration Regulation
	a_start = []; a_current = []
	for i in range (0,6):
		a_start.append(a[i].get_axis_parameter(5))
		a_current.append(DoubleVar())
	def set_max_acc_camera_z(val):
		a[0].set_axis_parameter(5,a_current[0].get())
		print ("Set Camera Z acceleration limit to {}".format(a[0].get_axis_parameter(5)))
	def set_max_acc_camera_x(val):
		a[1].set_axis_parameter(5,a_current[1].get())
		print ("Set Camera X acceleration limit to {}".format(a[1].get_axis_parameter(5)))
	def set_max_acc_mirror_z(val):
		a[2].set_axis_parameter(5,a_current[2].get())
		print ("Set Mirror Z acceleration limit to {}".format(a[2].get_axis_parameter(5)))
	def set_max_acc_mirror_height(val):
		a[3].set_axis_parameter(5,a_current[3].get())
		print ("Set Mirror Height acceleration limit to {}".format(a[3].get_axis_parameter(5)))
	def set_max_acc_mirror_psi(val):
		a[4].set_axis_parameter(5,a_current[4].get())
		print ("Set Mirror Psi acceleration limit to {}".format(a[4].get_axis_parameter(5)))
	def set_max_acc_mirror_phi(val):
		a[5].set_axis_parameter(5,a_current[5].get())
		print ("Set Mirror Phi acceleration limit to {}".format(a[5].get_axis_parameter(5)))
		
	#-----------------#
	#---- Movetos ----#
	#-----------------#
	#fahrbalken
	def moveto_mirror_height(val):
		change_camera_height=True
	def moveto_mirror_z(val):
		change_mirror_z=True
	def moveto_mirror_phi(val):
		global change_mirror_phi
		change_mirror_phi=True
	def moveto_mirror_psi(val):
		global change_mirror_psi
		change_mirror_psi=True
	def moveto_camera_x(val):    
		change_camera_x=True  
	def moveto_camera_z(val):
		change_camera_z=True
		
	def center_camera():
		CameraX.set(70)
		moveto_camera_x(70)
		CameraZ.set(70)
		moveto_camera_z(70)    
	def center_mirror_pos():
		MirrorHeight.set(20)
		MirrorZ.set(150)    
	def center_mirror_phi():
		MirrorPhi.set(0)
		moveto_mirror_phi(0)
	def center_mirror_psi():
		MirrorPsi.set(0)
		moveto_mirror_psi(0)
	def center_mirror_angle():
		center_mirror_phi()
		center_mirror_psi()    

	servo_angle=0
	def open_shutter():
		servo.shutter(180)
	def close_shutter():
		servo.shutter(0)
	def shutter_scale(val):
		servo.shutter(servo_pos.get())
		servo_angle=servo_pos.get()
	def shutter_pos(val):
		return servo_pos.get()
	   
	# Set current position
	def set_mirror_height():
		MirrorHeight.set(steps_to_mm(sd.position(a[3])))
		moveto_mirror_height(0)    
	def set_mirror_z():
		MirrorZ.set(steps_to_mm(sd.position(a[2])))
		moveto_mirror_z(0)
	def set_mirror_phi():
		MirrorPhi.set(steps_to_degree(sd.position(a[5])))
		moveto_mirror_phi(0)
	def set_mirror_psi():
		MirrorPsi.set(steps_to_degree(sd.position(a[4])))
		moveto_mirror_psi(0)
	def set_camera_x():
		CameraX.set(steps_to_mm(sd.position(a[1])))
		moveto_camera_x(0)
	def set_camera_z():
		CameraZ.set(steps_to_mm(sd.position(a[0])))
		moveto_camera_z(0)
	def set_all():
		set_mirror_height()
		set_mirror_z()
		set_mirror_phi()
		set_mirror_psi()
		set_camera_x()
		set_camera_z()
		
	def update_motor_status():
		global stop_thread
		stop_thread = False
		while True:
		    if stop_thread:
		        update_screen()
		        break
		    try:
		        update_items()
		    except SerialException:
		        print("Serial Exception. This only causes the GUI to miss one update!")
		    except:
		        print ("\tInformation: screen thread died, create new one")
		        stop_thread = True
		    sleep(0.1)
		    
	        
	def openNewDialogue():
		global root
		dialog=DialogFenster(root)
		
	def dummy_button():
		openNewDialogue()
        
    #-----------------------------------#
	#---- Permanently update screen ----#
	#-----------------------------------#
	def update_items(verbose=False):
		#move all motors due to changes since last time
		global change_mirror_phi
		global change_mirror_psi
		global change_mirror_z
		global change_mirror_height
		global change_camera_x
		global change_camera_z
		if change_mirror_phi:
		    if verbose==False: print("Move mirror phi to",mirror_phi_pos.get(),"in steps",degree_to_steps(mirror_phi_pos.get()))
		    WarningStatus[5]=0
		    a[5].move_absolute(degree_to_steps(mirror_phi_pos.get()))
		    change_mirror_phi=False
		if change_mirror_psi:
		    if verbose==False: print("Move mirror psi to",mirror_psi_pos.get(),"in steps",degree_to_steps(mirror_psi_pos.get()))
		    WarningStatus[4]=0
		    a[4].move_absolute(degree_to_steps(mirror_psi_pos.get()))
		    change_mirror_psi=False
		if change_mirror_z:
		    if verbose==False: print("Move mirror z to",mirror_z_pos.get(),"in steps",mm_to_steps(mirror_z_pos.get()))
		    WarningStatus[2]=0
		    a[2].move_absolute(mm_to_steps(mirror_z_pos.get()))
		    change_mirror_z=False
		if change_mirror_height:
		    if verbose==False: print("Move mirror height to",mirror_height_pos.get(),"in steps",mm_to_steps(mirror_height_pos.get()))
		    WarningStatus[3]=0
		    a[3].move_absolute(hmm_to_steps(mirror_height_pos.get()))   
		    change_mirror_height=False
		if change_camera_z:
		    if verbose==False: print("Move camera z to",camera_z_pos.get(),"in steps",mm_to_steps(camera_z_pos.get()))
		    WarningStatus[0]=0
		    a[0].move_absolute(mm_to_steps(camera_z_pos.get()))
		    change_camera_z=False   
		if change_camera_x:
		    if verbose==False: print("Move camera x to",camera_x_pos.get(), "von" , CameraX.get(),"in steps",mm_to_steps(camera_x_pos.get()))
		    WarningStatus[1]=0
		    a[1].move_absolute(mm_to_steps(camera_x_pos.get()))    
		    change_camera_x=False    
		#print (WarningStatus)
		#for i in range (0,6):
		#    print (str(sd.ismoving(a[i])) + "\t" + str(WarningStatus[i]) + "\t" + str(sd.ismoving(a[i])+WarningStatus[i]))
		#print (" ")
		MHD = sd.ismoving(a[3])+WarningStatus[3]
		#print("MHD",MHD)
		if MHD>2:
		    MHD=2
		MirrorHeightDisplay.itemconfig(MirrorHeightLED, fill=LEDColors[MHD])
		MHP=sd.position(a[3])
		MirrorHeightPositionLabel.config(text=str(round(steps_to_hmm(MHP),1)))
		MirrorHeight_OSTOP.config(bg=ENDSwitchColors[a[3].axis.get(10)])
		MirrorHeight_USTOP.config(bg=ENDSwitchColors[a[3].axis.get(11)])   
		MirrorZDisplay.itemconfig(MirrorZLED, fill=LEDColors[sd.ismoving(a[2])+WarningStatus[2]])
		MirrorZPositionLabel.config(text=str(round(steps_to_mm(sd.position(a[2])),1)))
		MirrorZ_LSTOP.config(bg=ENDSwitchColors[a[2].axis.get(11)])
		MirrorZ_RSTOP.config(bg=ENDSwitchColors[a[2].axis.get(10)])
		MPsiP=sd.position(a[4])
		MirrorPsiPositionLabel.config(text="{0:4.2f}".format(steps_to_degree(MPsiP)))
		MPsiD=sd.ismoving(a[4])+WarningStatus[4]
		if MPsiD>2:
		    MPsiD=2
		MirrorPsiDisplay.itemconfig(MirrorPsiLED, fill=LEDColors[MPsiD])
		MPsiO=a[4].axis.get(10)
		if MPsiO>2:
		    MPsiO=2
		MirrorPsi_OSTOP.config(bg=ENDSwitchColors[MPsiO])
		MPsiU=a[4].axis.get(11)
		if MPsiU>2:
		    MPsiU=2
		MirrorPsi_USTOP.config(bg=ENDSwitchColors[MPsiU])
		MirrorPhiPositionLabel.config(text="{0:4.2f}".format(steps_to_degree(sd.position(a[5]))))
		MirrorPhiDisplay.itemconfig(MirrorPhiLED, fill=LEDColors[sd.ismoving(a[5])+WarningStatus[5]])
		MirrorPhi_LSTOP.config(bg=ENDSwitchColors[a[5].axis.get(11)])
		MirrorPhi_RSTOP.config(bg=ENDSwitchColors[a[5].axis.get(10)])
		CameraXPositionLabel.config(text=str(round(steps_to_mm(sd.position(a[1])),1)))
		CameraXDisplay.itemconfig(CameraXLED, fill=LEDColors[sd.ismoving(a[1])+WarningStatus[1]])
		CameraX_OSTOP.config(bg=ENDSwitchColors[a[1].axis.get(10)])
		CameraX_USTOP.config(bg=ENDSwitchColors[a[1].axis.get(11)]) 
		CameraZPositionLabel.config(text=str(round(steps_to_mm(sd.position(a[0])),1)))
		CameraZDisplay.itemconfig(CameraZLED, fill=LEDColors[sd.ismoving(a[0])+WarningStatus[0]])
		CameraZ_LSTOP.config(bg=ENDSwitchColors[a[0].axis.get(10)])
		time.sleep(.05)
		CameraZ_RSTOP.config(bg=ENDSwitchColors[a[0].axis.get(11)])
		time.sleep(.05)
		if client != None:
		    try:
		        CHa_Label_rate.config(text="{0:5.1f}".format(client.getRateA()), fg="#00ff00")
		        CHb_Label_rate.config(text="{0:5.1f}".format(client.getRateB()), fg="#00ff00")
		    except RuntimeError:
		        startStopClient()
		        
		root.update_idletasks()
	   
	stop_thread = False



	screenthreads = []
	screenthreads.append(Thread(target=update_motor_status, args=()))
	screenthreads[-1].start()

	def update_screen():
		global stop_thread
		stop_thread= True
		screenthreads.append(Thread(target=update_motor_status, args=()))
		screenthreads[-1].start()
	
class controller():

	a=None
	
	def __init__(self):
		# Get motors
		self.a=sd.init()  #stepper_drive
	
	#fkt fuer roten stop button   
	def stop_all(self):
		for motor in a:
		    motor.stop()
		for i in range (0,6):   #prueft ob motor an zielposition angekommen war oder nicht 
		    if sd.ismoving(a[i]) == 1:   #1 wenn noch faehrt und 0 wenn schon angekommen, graues widget
		        WarningStatus[i] = 1
		print("Stop all motors!")
		
	def goto_saved_position():
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
		moveto_camera_z(None)
		moveto_camera_x(None)
		moveto_mirror_z(None)
		moveto_mirror_height(None)
		moveto_mirror_psi(None)
		moveto_mirror_phi(None)

		
	def refsearch_mirror_height():
		print("Searching for mirror height position 0mm")
		WarningStatus[3]=0
		a[3].reference_search(0)
		mirror_height_pos.set(0)
		
	def refsearch_mirror_z():
		print("Searching for mirror z position 0mm")
		WarningStatus[2]=0
		a[2].reference_search(0)
		mirror_z_pos.set(0)

	def refsearch_mirror_phi():
		print("Searching for mirror phi position -4.5°")
		WarningStatus[5]=0
		a[5].reference_search(0)
		mirror_phi_pos.set(-4.5)    
		
	def refsearch_mirror_psi():
		print("Searching for mirror psi -90°")
		WarningStatus[4]=0
		a[4].reference_search(0)
		mirror_psi_pos.set(-4.5)
		
	def refsearch_camera_x():
		print("Searching for camera x-position 0mm")
		WarningStatus[1]=0
		a[1].reference_search(0)
		camera_x_pos.set(0)
		
	def refsearch_camera_z():
		print("Searching for camera z-position 0mm")
		WarningStatus[0]=0
		a[0].reference_search(0)
		camera_z_pos.set(0)
		
	def refsearch_all():
		refsearch_mirror_height()
		refsearch_mirror_z()
		refsearch_mirror_phi()
		refsearch_mirror_psi()
		refsearch_camera_x()
		refsearch_camera_z()
		
	def switchMotor():
		global motoron
		if motoron == True:
		    ms.motor_off(); motoron = False
		    onoffButton.config(text="OFF", bg="#a3a3a3")
		else:
		    ms.motor_on(); motoron = True
		    onoffButton.config(text="ON", bg="#91CC66")
	

class rateAnalyzer():
	def showRateDistribution(spacing_phi=25, spacing_psi=26, min_phi=-2., max_phi=2, min_psi=-3.80, max_psi=-0.5, contrast_factor=3):
		#print("You entered the DUMMY-state")
		print("Starting to measure the rate distribution. MinPhi={0:4.2f} ; MaxPhi={1:4.2f} ; MinPsi={2:4.2f} ; MaxPsi={3:4.2f} ; SpacingPhi={4} ; SpacingPsi={5} ; ContrastFactor={6:4.2f}".format(min_phi, max_phi, min_psi, max_psi, spacing_phi, spacing_psi, contrast_factor))
		global client
		global change_mirror_psi
		global change_mirror_phi
		if client==None:
		    print("No client connected! Cannot plot Mirrors")
		    return
		coordinates_phi=np.linspace(min_phi, max_phi, num=spacing_phi)
		coordinates_psi=np.linspace(min_psi, max_psi, num=spacing_psi)
		x, y=np.meshgrid(coordinates_phi, coordinates_psi)
		rates=np.empty(shape=(spacing_phi, spacing_psi))
		for i in range(0, spacing_phi, 1):
		    pos_phi=min_phi+(max_phi-min_phi)/(spacing_phi-1)*i
		    MirrorPhi.set(pos_phi)
		    moveto_mirror_phi(0)
		    update_items(verbose=True)
		    while sd.ismoving(a[5]):
		        sleep(0.05)
		        #print("wait_5_phi")
		    for j in range(0, spacing_psi, 1):
		        if i%2==0:
		            pos_psi=min_psi+(max_psi-min_psi)/(spacing_psi-1)*j
		        else:
		            pos_psi=max_psi-(max_psi-min_psi)/(spacing_psi-1)*j
		        #print("PSI: {0} PHI: {1}".format(pos_psi, pos_phi))
		        MirrorPsi.set(pos_psi)
		        moveto_mirror_psi(0)
		        update_items(verbose=True)
		        while sd.ismoving(a[4]):
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
		plotWindow = Toplevel(root)
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

#HELPER METHODS (for all)
#Umrechnung zwischen motor parametern und python
microsteps_nano = 32
microsteps_standa = 16
offset_standa = 512000

def degree_to_mm(degree):
    return (8./9.)*degree ##8mm/9degrees
  
def mm_to_degree(mm):
    return (9./8.)*mm #9degrees/8mm

def steps_to_degree(steps):
    return mm_to_degree(steps/(800.*microsteps_standa))-4.5  #1mm /800step*microsteps_standa

def degree_to_steps(degree): #800step*microsteps_standa / 1mm
    return int(degree_to_mm(degree+4.5)*800*microsteps_standa)

def steps_to_mm(steps):
    return steps/(200.*microsteps_nano) #1mm / 200steps*microsteps_nano

def mm_to_steps(mm):
    return int(mm*200*microsteps_nano) #200steps*microsteps_nano / 1mm

#Für Höhenmotor
def steps_to_hmm(steps):
    return steps/(200.*microsteps_nano) #CHANGE

def hmm_to_steps(mm):
    return int(mm*200*microsteps_nano) #CHANGE

def set_driving_speed(motor,speed):
    motor.axis.max_positioning_speed=int(speed)
    motor.set_axis_parameter(194, 300)

#stromrechner
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

    
def optimize():
    optimizeMirrorBluntly()

    


root.mainloop()
os._exit(0)
