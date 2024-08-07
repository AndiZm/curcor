import threading
import scipy.optimize as opt
from numpy import random
from tkinter import *
from tkinter import simpledialog
from tkinter import filedialog
import configparser
import logging

from time import sleep
import time
import os
import warnings
from serial.serialutil import SerialException
from pyTMCL.reply import TrinamicException

import numpy as np #only needed for simulations
from PIL import Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math

import geometry as geo
import log as gloab_log
import position as pos
import pointing

#updating=False


class RATE_ANALYZER():
    
    client=None
    controller=None
    log=None
    position=None
    change_mirror_psi=False
    change_mirror_phi=False
    
    #measurement mode
    mode=None
    
    #currently loaded distribution / plot
    rates=None
    spacing_0=np.nan
    spacing_1=np.nan
    min_0=-10
    max_0=-min_0
    min_1=-10
    max_1=-min_1
    camera_z=-1
    camera_x=-1
    mirror_z=-1
    mirror_y=-1
    mirror_psi=-1
    mirror_phi=-1
    offset=-1
    
    #currently set rectangle
    min_1_rect=None
    max_1_rect=None
    min_0_rect=None
    max_0_rect=None
    
    #Stuff for the GUI
    master=None
    window=None
    main_frame=None
    plot_frame=None
    control_frame=None
    fit_frame=None
    results_frame=None
    findAreaButton=None
    fitButton=None
    loadButton=None
    saveButton=None
    recordButton=None
    crazyBatchButton=None
    label_min_0=None
    label_max_0=None
    label_min_1=None
    label_max_1=None
    label_spacing_0=None
    label_spacing_1=None
    label_spacing_x=None
    label_spacing_y=None
    checkbutton_live=None
    adoptButton=None 
    box_min_0=None
    box_max_0=None
    box_min_1=None
    box_max_1=None
    box_spacing_0=None
    box_spacing_1=None
    checked=None
    offset_bool=None
    resultsHeadLabel=None
    resultsCenterPhiLabel=None
    resultsCenterPsiLabel=None
    resultsSigmaPhiLabel=None
    resultsSigmaPsiLabel=None
    resultsOffsetLabel=None
    resultsPrefactorPhiLabel=None
    camZLabel = None
    camXLabel = None
    mirZLabel = None
    mirYLabel = None
    mirPhiLabel = None
    mirPsiLabel = None
    offsetLabel = None
    label_starting_psi = None
    label_starting_phi = None
    label_starting_mir_z = None
    label_starting_mir_y = None
    label_starting_cam_z = None
    label_starting_cam_x = None
    label_starting_cam_x = None
    box_starting_psi = None
    box_starting_phi = None
    box_starting_mir_z = None
    box_starting_mir_y = None
    box_starting_cam_z = None
    box_starting_cam_x = None
    box_starting_cam_x = None
    label_guess_head = None
    label_guess_psi = None
    label_guess_phi = None
    label_guess_mir_z = None
    label_guess_mir_y = None
    label_guess_cam_z = None
    label_guess_cam_x = None
    full_optimization_button =None
    deviation_desc_Label_alt = None
    deviation_desc_Label_az = None
    deviation_alt_Label_pos = None
    deviation_az_Label_pos = None

    
    #values for (live) recording
    still_recording=False
    new_record=False

    figure=None
    subplot=None
    legend=None
    
    def __init__(self, master, controller=None, client=None, log=None, position=None):
        #copy stuff
        self.controller=controller
        self.client=client
        self.master=master
        self.log=log
        self.position=position
        
        #ask which measurement mode should be used
        mode_dialog = initDialog(master)
        if mode_dialog.result != None:
            if mode_dialog.result.get() == 1:
                self.mode="x-y"
                print("set mode to X - Y")
            elif mode_dialog.result.get() == 2:
                self.mode="psi-phi"
                print("set mode to PSI - Phi")
            elif mode_dialog.result.get() == 3:
                self.mode="x-z"
            else:
                raise RuntimeError("Something went wrong with the selection of the measuring mode!")
            print("Start Rate Analyzer in measuring mode {0}".format(self.mode))
        else:
            raise RuntimeError("Something went wrong with the selection of the measuring mode!")
        
        #create new window and frames
        
        # STRUCTURE
        # Window
        # ->Main Frame
        #   -> Plot Frame
        #     -> Canvas
        #     -> Positions Frame
        #       -> pos line 1 Frame
        #       -> pos line 2 Frame
        #   -> Control Frame
        #     -> Load buttonbox
        #     -> Save button
        #     -> Record Frame
        #     -> Fit Frame
        #       -> Results Frame
        #     -> Variables Frame
        #     -> Current Guess Frame
        
        self.window = Toplevel(master)
        self.main_frame = Frame(self.window, width=1180, height = 1000)
        self.main_frame.grid(row=0, column=0)
        self.main_frame.config(background = "#003366")
        
        self.plot_frame = Frame(self.main_frame, width=1000, height=900)
        self.plot_frame.grid(row=0, column=0, padx=10,pady=10)
        self.plot_frame.config(background = "#003366")
        
        self.positions_frame = Frame(self.plot_frame, width=1000, height=100)
        self.positions_frame.grid(row=1, column=0, padx=10,pady=5)
        self.positions_frame.config(background = "#FFFFFF")
        
        self.pos_line_1_frame = Frame(self.positions_frame, width=1000, height=100)
        self.pos_line_1_frame.grid(row=0, column=0, padx=0,pady=0)
        self.pos_line_1_frame.config(background = "#FFFFFF")
        
        #self.pos_line_2_frame = Frame(self.positions_frame, width=600, height=100)
        #self.pos_line_2_frame.grid(row=1, column=0, padx=0,pady=0)
        #self.pos_line_2_frame.config(background = "#FFFFFF")
        
        self.control_frame = Frame(self.main_frame, width=320, height=900)
        self.control_frame.grid(row=0, column=1)
        self.control_frame.config(background = "#003366")
        
        self.record_frame = Frame(self.control_frame, width=300, height=200)
        self.record_frame.grid(row=1, column=0, padx=10, pady=10)
        self.record_frame.config(background = "#DBDBDB")
        
        self.fit_frame = Frame(self.control_frame, width=300, height=200)
        self.fit_frame.grid(row=3, column=0, padx=10, pady=10)
        self.fit_frame.config(background = "#003366")
        
        self.results_frame = Frame(self.fit_frame, width=290, height=120)
        self.results_frame.grid(row=3, column=0, padx=10, pady=10)
        self.results_frame.config(background = "#DBDBDB")
        
        self.deviation_frame = Frame(self.control_frame, width=290, height=100)
        self.deviation_frame.grid(row=2, column=1, padx=10, pady=10)
        self.deviation_frame.config(background = "#DBDBDB")
        
        self.deviation_head_frame = Frame(self.deviation_frame, width=290, height=50)
        self.deviation_head_frame.grid(row=0, padx=0, pady=0)
        self.deviation_head_frame.config(background = "#DBDBDB")
        
        self.deviation_base_frame = Frame(self.deviation_frame, width=290, height=50)
        self.deviation_base_frame.grid(row=1, padx=0, pady=0)
        self.deviation_base_frame.config(background = "#DBDBDB")
        
        self.variables_frame  = Frame(self.control_frame, width=320, height=600)
        self.variables_frame.grid(row=1, column=1, padx=10)
        self.variables_frame.config(background = "#DBDBDB")
        
        self.current_guess_frame  = Frame(self.control_frame, width=320, height=120)
        self.current_guess_frame.grid(row=3, column=1, padx=10, pady=10)
        self.current_guess_frame.config(background = "#DBDBDB")
        
        self.checked=IntVar()
        self.offset_bool=IntVar()
        
        ##############
        # PLOT FRAME #
        ##############
        
        #create the plot
        self.figure=plt.Figure(figsize=(6,6))
        self.subplot = self.figure.add_subplot(111)
        self.subplot.set_title("Heatmap of the mirror Positions")
        '''if self.mode == "psi-phi":
            self.subplot.set_xlabel("$\phi$ [°]")
            self.subplot.set_ylabel("$\psi$ [°]")
        elif self.mode == "x-y":
            self.subplot.set_xlabel("x [mm]")
            self.subplot.set_ylabel("y [mm]")
        elif self.mode == "x-z":
            self.subplot.set_xlabel("z [mm]")
            self.subplot.set_ylabel("x [mm]")
            self.subplot.invert_xaxis()
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")'''
        #set initial limits on the plot
        self.subplot.set_xlim((self.min_0, self.max_0))
        self.subplot.set_ylim((self.min_1, self.max_1))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.canvas.draw()
        
        
        ###################
        # POSITIONS FRAME #
        ###################
        
        #create labels
        self.camXLabel = Label(self.pos_line_1_frame, pady=5, text='Camera X: {0:4.1f}'.format(self.camera_x), width="18", background ="#FFFFFF")
        self.mirZLabel = Label(self.pos_line_1_frame, pady=5, text='Mirror Z: {0:4.1f}'.format(self.mirror_z), width="18", background ="#FFFFFF")
        self.mirYLabel = Label(self.pos_line_1_frame, pady=5, text='Mirror Y: {0:4.1f}'.format(self.mirror_y), width="18", background ="#FFFFFF")
        self.mirPhiLabel = Label(self.pos_line_1_frame, pady=5, text='Mirror PSI: {0:4.1f}'.format(self.mirror_psi), width="18", background ="#FFFFFF")
        self.mirPsiLabel = Label(self.pos_line_1_frame, pady=5, text='Mirror PHI: {0:4.1f}'.format(self.mirror_phi), width="18", background ="#FFFFFF")
        self.camZLabel = Label(self.pos_line_1_frame, pady=5, text='Camera Z: {0:4.1f}'.format(self.camera_z), width="15", background ="#FFFFFF")
                
        #place labels
        self.camXLabel.grid(row=0, column=0)
        self.mirZLabel.grid(row=0, column=1)
        self.mirYLabel.grid(row=0, column=2)
        self.mirPhiLabel.grid(row=1, column=0)
        self.mirPsiLabel.grid(row=1, column=1)
        self.camZLabel.grid(row=1, column=2)
        
        ##############
        # FILE FRAME #
        ##############
        
        #add GUI elements
        self.loadButton = Button(self.control_frame, text="Load Rate Distribution", width=31, pady=3, padx=3, command=self.loadRates)
        self.loadButton.grid(row=0,column=0)
        self.saveButton = Button(self.control_frame, text="Save Rate Distribution", width=31, pady=3, padx=3, command=self.saveRates)
        self.saveButton.grid(row=0,column=1)
        
        
        ###################
        # DEVIATION FRAME #
        ###################
        
        #create labels
        self.label_deviation_head = Label(self.deviation_head_frame, text='DEVIATION ACC. TO TRACKING [mm]:', width="31")
        self.deviation_desc_Label_alt = Label(self.deviation_base_frame, text="Alt:")
        self.deviation_desc_Label_az = Label(self.deviation_base_frame, text="Az:")
        self.deviation_alt_Label_pos = Label(self.deviation_base_frame, text="0.0", fg="orange", bg="black", font=("Helvetica 15 bold"), width=5)
        self.deviation_az_Label_pos = Label(self.deviation_base_frame, text="0.0", fg="orange", bg="black", font=("Helvetica 15 bold"), width=6)

        #place labels
        self.label_deviation_head.grid(row=0)
        self.deviation_desc_Label_alt.grid(row=0, column=0, padx=3, pady=3)
        self.deviation_alt_Label_pos.grid(row=0, column=1, padx=3, pady=3)
        self.deviation_desc_Label_az.grid(row=0, column=2, padx=3, pady=3)
        self.deviation_az_Label_pos.grid(row=0, column=3, padx=3, pady=3)
        
        #create thread that updates the deviations
        if self.position!=None:
            t_deviation = threading.Thread(target= self.updateDeviation)
            t_deviation.start()
        else:
            print("No position object was passed on. Therefore no deviation can be calculated!")
            self.deviation_alt_Label_pos.config( fg="red")
            self.deviation_az_Label_pos.config( fg="red")
        
        
        #######################
        # CURRENT GUESS FRAME #
        #######################
        
        #here we just change the text of the labels to keep everything easy with the fit methods!
        
        #create labels
        self.label_guess_head = Label(self.current_guess_frame, text='CURRENT GUESS:', width="15")
        self.label_guess_psi  = Label(self.current_guess_frame, text='PHI:  ', width="15")
        self.label_guess_phi = Label(self.current_guess_frame, text='PSI:  ', width="15")
        self.label_guess_mir_z = Label(self.current_guess_frame, text='Mirror Z:  ', width="15")
        self.label_guess_mir_y = Label(self.current_guess_frame, text='Mirror Y:  ', width="15")
        self.label_guess_cam_z = Label(self.current_guess_frame, text='Camera Z:  ', width="15")
        self.label_guess_cam_x = Label(self.current_guess_frame, text='Camera X:  ', width="15")
        
        #place labels
        self.label_guess_head.grid(row=0)
        self.label_guess_psi.grid(row=1, column=0)
        self.label_guess_phi.grid(row=1, column=1)
        self.label_guess_mir_z.grid(row=2, column=0)
        self.label_guess_mir_y.grid(row=2, column=1)
        self.label_guess_cam_z.grid(row=3, column=0)
        self.label_guess_cam_x.grid(row=3, column=1)


        ################
        # RECORD FRAME #
        ################

        #add record elements        
        spacing_0=10
        spacing_1=11
        if self.mode == "psi-phi":
            #create labels
            min_phi=-4.4
            max_phi=4.4
            min_psi=-4.4
            max_psi=4.4
            self.label_min_0 = Label(self.record_frame, text='Min PHI:  ')
            self.label_max_0 = Label(self.record_frame, text='Max PHI:  ')
            self.label_min_1 = Label(self.record_frame, text='Min PSI:  ')
            self.label_max_1 = Label(self.record_frame, text='Max PSI:  ')
            self.label_spacing_0 = Label(self.record_frame, text='Spacing PHI:  ')
            self.label_spacing_1 = Label(self.record_frame, text='Spacing PSI:  ')
            #create sliders
            self.box_min_0 = Scale(self.record_frame, from_=min_phi, to=max_phi, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_0 = Scale(self.record_frame, from_=min_phi, to=max_phi, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_min_1 = Scale(self.record_frame, from_=min_psi, to=max_psi, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_1 = Scale(self.record_frame, from_=min_psi, to=max_psi, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_spacing_0 = Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            self.box_spacing_1 = Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            #set initial values
            self.box_min_0.set(min_phi)
            self.box_max_0.set(max_phi)
            self.box_min_1.set(min_psi)
            self.box_max_1.set(max_psi)
        elif self.mode == "x-y":
            min_x=-80
            max_x=80
            min_y=-25
            max_y=25
            #create labels
            self.label_min_0 = Label(self.record_frame, text='Min X:  ')
            self.label_max_0 = Label(self.record_frame, text='Max X:  ')
            self.label_min_1 = Label(self.record_frame, text='Min Y:  ')
            self.label_max_1 = Label(self.record_frame, text='Max Y:  ')
            self.label_spacing_0 = Label(self.record_frame, text='Spacing X:  ')
            self.label_spacing_1 = Label(self.record_frame, text='Spacing Y:  ')
            #create sliders
            self.box_min_0 = Scale(self.record_frame, from_=min_x, to=max_x, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_0 = Scale(self.record_frame, from_=min_x, to=max_x, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_min_1 = Scale(self.record_frame, from_=min_y, to=max_y, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_1 = Scale(self.record_frame, from_=min_y, to=max_y, orient=HORIZONTAL, length=150, resolution=0.1)

            self.box_spacing_0= Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            self.box_spacing_1 = Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            #set initial values
            self.box_min_0.set(min_x)
            self.box_max_0.set(max_x)
            self.box_min_1.set(min_y)
            self.box_max_1.set(max_y)
        elif self.mode == "x-z":
            min_z=-100
            max_z=100
            min_x=-120
            max_x=120
            #create labels
            self.label_min_0 = Label(self.record_frame, text='Min Z:  ')
            self.label_max_0 = Label(self.record_frame, text='Max Z:  ')
            self.label_min_1 = Label(self.record_frame, text='Min X:  ')
            self.label_max_1 = Label(self.record_frame, text='Max X:  ')
            self.label_spacing_0 = Label(self.record_frame, text='Spacing Z:  ')
            self.label_spacing_1 = Label(self.record_frame, text='Spacing X:  ')
            #create sliders
            self.box_min_0 = Scale(self.record_frame, from_=min_z, to=max_z, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_0 = Scale(self.record_frame, from_=min_z, to=max_z, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_min_1 = Scale(self.record_frame, from_=min_x, to=max_x, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_1 = Scale(self.record_frame, from_=min_x, to=max_x, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_spacing_0  = Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            self.box_spacing_1 = Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            #set initial values
            self.box_min_0.set(min_z)
            self.box_max_0.set(max_z)
            self.box_min_1.set(min_x)
            self.box_max_1.set(max_x)
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")
        #set initial values for spacing
        self.box_spacing_0.set(spacing_0)
        self.box_spacing_1.set(spacing_1)
        #place labels in grid
        self.label_min_0.grid(row=0, column=0, padx=10, pady=3)
        self.label_max_0.grid(row=1, column=0, padx=10, pady=3)
        self.label_min_1.grid(row=2, column=0, padx=10, pady=3)
        self.label_max_1.grid(row=3, column=0, padx=10, pady=3)
        self.label_spacing_0.grid(row=4, column=0, padx=10, pady=3)
        self.label_spacing_1.grid(row=5, column=0, padx=10, pady=3)
        #place sliders in grid
        self.box_min_0.grid(row=0, column=1, padx=10, pady=3)
        self.box_max_0.grid(row=1, column=1, padx=10, pady=3)
        self.box_min_1.grid(row=2, column=1, padx=10, pady=3)
        self.box_max_1.grid(row=3, column=1, padx=10, pady=3)
        self.box_spacing_0.grid(row=4, column=1, padx=10, pady=3)
        self.box_spacing_1.grid(row=5, column=1, padx=10, pady=3)
            
        #create and place checkbutton
        self.checkbutton_live = Checkbutton(self.record_frame, text="draw live", onvalue = 1, offvalue = 0, variable=self.checked)
        self.checkbutton_live.select()
        self.checkbutton_live.grid(row=6, column=0, padx=10, pady=3)

        #create and place button for recomended parameter adoption
        self.adoptButton = Button(self.record_frame, text="adopt red box", command=self.adoptProposal)
        self.adoptButton.grid(row=6, column=1, padx=10, pady=3)
        
        ###################
        # VARIABLES FRAME #
        ###################
        
        #create labels
        self.label_starting_psi = Label(self.variables_frame, text='PSI:  ')
        self.label_starting_phi = Label(self.variables_frame, text='PHI:  ')
        self.label_starting_mir_z = Label(self.variables_frame, text='Mirror Z:  ')
        self.label_starting_mir_y = Label(self.variables_frame, text='Mirror Y:  ')
        self.label_starting_cam_z = Label(self.variables_frame, text='Camera Z:  ')
        self.label_starting_cam_x = Label(self.variables_frame, text='Camera X:  ')
        #place labels in grid
        self.label_starting_psi.grid(row=0, column=0, padx=10, pady=3)
        self.label_starting_phi.grid(row=1, column=0, padx=10, pady=3)
        self.label_starting_mir_z.grid(row=2, column=0, padx=10, pady=3)
        self.label_starting_mir_y.grid(row=3, column=0, padx=10, pady=3)
        self.label_starting_cam_z.grid(row=4, column=0, padx=10, pady=3)
        self.label_starting_cam_x.grid(row=5, column=0, padx=10, pady=3)
        #create sliders
        self.box_starting_psi = Scale(self.variables_frame, from_=-4.4, to=4.4, orient=HORIZONTAL, length=150, resolution=0.1)
        self.box_starting_phi = Scale(self.variables_frame, from_=-4.5, to=4.4, orient=HORIZONTAL, length=150, resolution=0.1)
        self.box_starting_mir_z = Scale(self.variables_frame, from_=308, to=439, orient=HORIZONTAL, length=150, resolution=0.1)
        self.box_starting_mir_y = Scale(self.variables_frame, from_=119, to=146, orient=HORIZONTAL, length=150, resolution=0.1)
        self.box_starting_cam_z = Scale(self.variables_frame, from_=0, to=139, orient=HORIZONTAL, length=150, resolution=0.1)
        self.box_starting_cam_x = Scale(self.variables_frame, from_=-125, to=125, orient=HORIZONTAL, length=150, resolution=0.1)
        #place sliders in grid
        self.box_starting_psi.grid(row=0, column=1, padx=10, pady=3)
        self.box_starting_phi.grid(row=1, column=1, padx=10, pady=3)
        self.box_starting_mir_z.grid(row=2, column=1, padx=10, pady=3)
        self.box_starting_mir_y.grid(row=3, column=1, padx=10, pady=3)
        self.box_starting_cam_z.grid(row=4, column=1, padx=10, pady=3)
        self.box_starting_cam_x.grid(row=5, column=1, padx=10, pady=3)
        #set initial values
        self.box_starting_psi.set(0)
        self.box_starting_phi.set(0)
        self.box_starting_mir_z.set(360)
        self.box_starting_mir_y.set(120)
        self.box_starting_cam_z.set(0)
        self.box_starting_cam_x.set(0)
        
        #create and place checkbutton
        if self.mode == "psi-phi":
            self.checkbutton_offset = Checkbutton(self.variables_frame, text="use offset", command=self.offsetMode, onvalue = 1, offvalue = 0, variable=self.offset_bool)
            self.checkbutton_offset.deselect()
            self.checkbutton_offset.grid(row=6, column=0, padx=10, pady=3)        

        #create and place button for recomended parameter adoption
        self.adoptButton = Button(self.variables_frame, text="adopt current guess", command=self.adoptCurrentGuess)
        self.adoptButton.grid(row=6, column=1, padx=10, pady=3)
        
        
        #############
        # FIT FRAME #
        #############
        
        self.findAreaButton = Button(self.fit_frame, text="Find Area of Interest", width=31, pady=3, padx=3, command=self.findRectangle)
        self.findAreaButton.grid(row=0)
        self.fitButton = Button(self.fit_frame, text="Fit Gaussian", width=31, pady=3, padx=3, command=self.fitGaussian)
        self.fitButton.grid(row=1)
        
        
        #################
        # RESULTS FRAME #
        #################
        
        #here we just change the text of the labels to keep everything easy with the fit methods!
        
        #create labels
        self.resultsHeadLabel = Label(self.results_frame, text='RESULTS:', width="15")
        self.resultsCenterPhiLabel  = Label(self.results_frame, text='Center PHI:  ', width="15")
        self.resultsCenterPsiLabel = Label(self.results_frame, text='Center PSI:  ', width="15")
        self.resultsSigmaPhiLabel = Label(self.results_frame, text='Sigma PHI:  ', width="15")
        self.resultsSigmaPsiLabel = Label(self.results_frame, text='Sigma PSI:  ', width="15")
        self.resultsOffsetLabel = Label(self.results_frame, text='Offset:  ', width="15")
        self.resultsPrefactorPhiLabel = Label(self.results_frame, text='Prefactor:  ', width="15")
        
        '''if self.mode=="x-y":
            self.resultsCenterPhiLabel.config(text='Center X:    ')
            self.resultsCenterPsiLabel.config(text='Center Y:    ')
            self.resultsSigmaPhiLabel.config(text='Sigma X:    ')
            self.resultsSigmaPsiLabel.config(text='Sigma Y:    ')
        
        if self.mode=="x-z":
            self.resultsCenterPhiLabel.config(text='Center X:    ')
            self.resultsCenterPsiLabel.config(text='Center Z:    ')
            self.resultsSigmaPhiLabel.config(text='Sigma X:    ')
            self.resultsSigmaPsiLabel.config(text='Sigma Z:    ')'''
        
        #place labels
        self.resultsHeadLabel.grid(row=0)
        self.resultsCenterPhiLabel.grid(row=1, column=0)
        self.resultsCenterPsiLabel.grid(row=1, column=1)
        self.resultsSigmaPhiLabel.grid(row=2, column=0)
        self.resultsSigmaPsiLabel.grid(row=2, column=1)
        self.resultsOffsetLabel.grid(row=3, column=0)
        self.resultsPrefactorPhiLabel.grid(row=3, column=1)
        
        #############
        # LEFTOVERS #
        #############
        
        #record button
        self.recordButton = Button(self.control_frame, text="record rate Distribution", width=31, pady=3, padx=3)
        self.recordButton.grid(row=2)
        self.recordButton["command"]= self.recordRateDistributionRead
        
        #crazy batch button
        self.crazyBatchButton = Button(self.control_frame, text="Crazy Batch", width=31, pady=3, padx=3)
        self.crazyBatchButton.grid(row=5, column=0)
        self.crazyBatchButton["command"]= self.crazyBatch
        
        #Full optimzation button
        self.full_optimization_button = Button(self.control_frame, text="Full Optimization", width=31, pady=3, padx=3)
        self.full_optimization_button.grid(row=5, column=1)
        self.full_optimization_button["command"]= self.runOptimizer
        
        #correction button
        self.correction_button = Button(self.control_frame, text="Correct pointing", width=31, pady=3, padx=3)
        self.correction_button.grid(row=4, column=1)
        self.correction_button["command"]= self.correctPointing
        
        #customize everything so it works in every mode
        self.changeMode(self.mode)
  
    def replotRates(self):
        #update the other parameters
        self.camXLabel.config(text='Camera X: {0:4.1f}'.format(self.camera_x))
        self.camZLabel.config(text='Camera Z: {0:4.1f}'.format(self.camera_z))
        self.mirZLabel.config(text='Mirror Z: {0:4.1f}'.format(self.mirror_z))
        self.mirYLabel.config(text='Mirror Height: {0:4.1f}'.format(self.mirror_y))
        self.mirPhiLabel.config(text='Mirror PSI: {0:4.1f}'.format(self.mirror_psi))
        self.mirPsiLabel.config(text='Mirror PHI: {0:4.1f}'.format(self.mirror_phi))
        #make a nice plot
        if self.figure==None:
            self.figure=plt.Figure(figsize=(6,6))
        else:
            self.figure.clf()
        self.subplot = self.figure.add_subplot(111)
        self.subplot.set_title("Heatmap of the mirror positions")
        if self.mode=="psi-phi":
            self.subplot.imshow(self.rates, cmap='cool', extent=( self.min_0-(self.max_0-self.min_0)/(self.spacing_0)/2, self.max_0+(self.max_0-self.min_0)/(self.spacing_0)/2, self.min_1-(self.max_1-self.min_1)/(self.spacing_1)/2, self.max_1+(self.max_1-self.min_1)/(self.spacing_1)/2))
            self.subplot.set_xlabel("$\phi$ [°]")
            self.subplot.set_ylabel("$\psi$ [°]")
        elif self.mode=="x-y":
            self.subplot.imshow(self.rates, cmap='cool', extent=( self.min_0-(self.max_0-self.min_0)/(self.spacing_0)/2, self.max_0+(self.max_0-self.min_0)/(self.spacing_0)/2, self.min_1-(self.max_1-self.min_1)/(self.spacing_1)/2, self.max_1+(self.max_1-self.min_1)/(self.spacing_1)/2))
            self.subplot.set_xlabel("X [mm]")
            self.subplot.set_ylabel("Y [mm]")
        elif self.mode=="x-z":
            self.subplot.imshow(self.rates, cmap='cool', extent=( self.max_0+(self.max_0-self.min_0)/(self.spacing_0)/2, self.min_0-(self.max_0-self.min_0)/(self.spacing_0)/2, self.min_1-(self.max_1-self.min_1)/(self.spacing_1)/2, self.max_1+(self.max_1-self.min_1)/(self.spacing_1)/2))
            self.subplot.set_xlabel("Z [mm]")
            self.subplot.set_ylabel("X [mm]")
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")
        plt.draw()
        if self.canvas==None:
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.canvas.draw()
        self.master.update()
        #print("replotted the canvas")
    
    def replotRatesUpdate(self):
        print("started updating")
        while self.still_recording:
            sleep(0.05)
            if self.new_record:
                self.replotRates()
                self.new_record=False
                #print("replotted")
        print(self.rates)
        print("stopped updating")
    
    def recordRateDistributionRead(self):
        if self.checked.get()==1:
            self.still_recording=True
            new_record=False
            #get all the general parmeters
            cam_x=self.box_starting_cam_x.get()
            mir_z=self.box_starting_mir_z.get()
            mir_y=self.box_starting_mir_y.get()
            mir_psi=self.box_starting_psi.get()
            mir_phi=self.box_starting_phi.get()
            if self.offset_bool.get() == 1:
                offset_cam_z=self.box_starting_cam_z.get()
                cam_z=geo.get_camera_z_position_offset(mir_phi, mir_psi, mir_y, mir_z, offset_cam_z)
            else:
                cam_z=self.box_starting_cam_z.get()
                offset_cam_z=geo.get_path_length_delta(mir_phi, mir_psi, mir_y, mir_z, cam_z, cam_x)
            #get variables and spacing
            min_0=self.box_min_0.get()
            max_0=self.box_max_0.get()
            min_1=self.box_min_1.get()
            max_1=self.box_max_1.get()
            spacing_0=int(self.box_spacing_0.get())
            spacing_1=int(self.box_spacing_1.get())
            #print("Cam X: {0} Mir Z: {1} Mir Y: {2} Mir Psi: {3} Mir Phi {4} MIN0: {5} MAX0: {6} MIN1: {7} MAX1: {8}".format(cam_x, mir_z, mir_y, mir_psi, mir_phi, min_0, max_0, min_1, max_1))
            if self.mode=="psi-phi":
                t1 = threading.Thread(target= lambda arg_spacing_phi=spacing_0, arg_spacing_psi=spacing_1, arg_min_phi=min_0, arg_max_phi=max_0, arg_min_psi=min_1, arg_max_psi=max_1, arg_cam_x=cam_x, arg_mir_y=mir_y, arg_cam_z=cam_z, arg_mir_z=mir_z, arg_phi=mir_phi, arg_psi=mir_psi : self.recordRateDistributionPhiPsi(spacing_phi=arg_spacing_phi, spacing_psi=arg_spacing_psi, min_phi=arg_min_phi, max_phi=arg_max_phi, min_psi=arg_min_psi, max_psi=arg_max_psi, cam_x=arg_cam_x, mir_y=arg_mir_y, cam_z=arg_cam_z, mir_z=arg_mir_z, phi=arg_phi, psi=arg_psi))
            elif self.mode=="x-y":
                t1 = threading.Thread(target= lambda arg_spacing_x=spacing_0, arg_spacing_y=spacing_1, arg_min_cam_x=min_0, arg_max_cam_x=max_0, arg_min_mir_y=min_1, arg_max_mir_y=max_1, arg_cam_x=cam_x, arg_mir_y=mir_y, arg_cam_z=cam_z, arg_mir_z=mir_z, arg_phi=mir_phi, arg_psi=mir_psi : self.recordRateDistributionXY(spacing_x=arg_spacing_x, spacing_y=arg_spacing_y, min_cam_x=arg_min_cam_x, max_cam_x=arg_max_cam_x, min_mir_y=arg_min_mir_y, max_mir_y=arg_max_mir_y, cam_x=arg_cam_x, mir_y=arg_mir_y, cam_z=arg_cam_z, mir_z=arg_mir_z, phi=arg_phi, psi=arg_psi))
            elif self.mode=="x-z":
                t1 = threading.Thread(target= lambda arg_spacing_x=spacing_1, arg_spacing_z=spacing_0, arg_min_cam_x=min_1, arg_max_cam_x=max_1, arg_min_mir_z=min_0, arg_max_mir_z=max_0, arg_cam_x=cam_x, arg_mir_y=mir_y, arg_offset_cam_z=offset_cam_z, arg_mir_z=mir_z, arg_phi=mir_phi, arg_psi=mir_psi : self.recordRateDistributionXZ(spacing_x=arg_spacing_x, spacing_z=arg_spacing_z, min_cam_x=arg_min_cam_x, max_cam_x=arg_max_cam_x, min_mir_z=arg_min_mir_z, max_mir_z=arg_max_mir_z, cam_x=arg_cam_x, mir_y=arg_mir_y, offset_cam_z=arg_offset_cam_z, mir_z=arg_mir_z, phi=arg_phi, psi=arg_psi))
            else:
                raise RuntimeError("The measuring mode needs to be definied correctly!")  
            t1.start()
            self.replotRatesUpdate()
        else:
            print("Result will be plotted after everything is measured!")
            self.recordRateDistribution(self.box_spacing_0.get(), self.box_spacing_1.get(), self.box_min_phi.get(), self.box_max_phi.get(), self.box_min_psi.get(), self.box_max_psi.get())
            self.replotRates()
    #STILL NEEDS FINAL DEBUGGING
    def recordRateDistributionXY(self, spacing_x, spacing_y, min_cam_x, max_cam_x, min_mir_y, max_mir_y, cam_x, mir_y, cam_z, mir_z, phi, psi):
        if self.mode!="x-y":
            raise RuntimeError("The method 'recordRateDistributionXY' can only be called in x-y mode! The mode currently is set to {}".format(self.mode))
        if self.client==None:
            self.still_recording=False
            raise RuntimeError("Error when trying to record a rate. Cannot record rate without a client connected")
            
        #FIRST CONTROLL IF THE POSITIONS ARE POSSIBLE BY CHECKING ALL EXTREMAL POINTS!
        min_x=cam_x+min_cam_x
        max_x=cam_x+max_cam_x
        min_y=mir_y+min_mir_y
        max_y=mir_y+max_mir_y
        min_min = geo.check_position_cam_absolute(phi, psi, min_y, mir_z, cam_z, min_x)
        min_max = geo.check_position_cam_absolute(phi, psi, min_y, mir_z, cam_z, max_x)
        max_min = geo.check_position_cam_absolute(phi, psi, max_y, mir_z, cam_z, min_x)
        max_max = geo.check_position_cam_absolute(phi, psi, max_y, mir_z, cam_z, max_x)
        if not min_min and min_max and max_min and max_max:
            raise RuntimeError("The rate distribution can not be recorded because some of the measurement positions are out of range! Min_Min {0}, Min_Max {1}, Max_Min {2}, Max_Max {3}".format(min_min, min_max, max_min, max_max))
        
        
        #change the global parameters so the plot can be redrawn correctly
        self.resetRectangle()
        self.spacing_0=spacing_x
        self.spacing_1=spacing_y
        self.min_0=min_cam_x
        self.max_0=max_cam_x
        self.min_1=min_mir_y
        self.max_1=max_mir_y
        self.camera_z=cam_z
        self.camera_x=cam_x
        self.mirror_z=mir_z
        self.mirror_y=mir_y
        self.mirror_psi=psi
        self.mirror_phi=phi
        
        if cam_z<=max_mir_y:
            raise RuntimeError("The calulated Camera z is smaller than the y-range that is to be surpassed ({0}<={1}). Is the mirror too close to the camera?".format(cam_z, max_mir_y))
        else:
            self.controller.setBussy(True)
            self.controller.set_position_mirror_phi(phi)
            self.controller.set_position_mirror_psi(psi)
            self.controller.set_position_mirror_z(mir_z)
            self.controller.set_position_mirror_height(min_y) #start from minimum
            self.controller.set_position_camera_x(min_cam_x)
            self.controller.set_position_camera_z(cam_z+min_mir_y) #start from minimum
        #wait till every motor has reached its starting position
        moving_all=True
        while moving_all:
            try:
                moving_all=self.controller.get_mirror_phi_moving() or self.controller.get_mirror_psi_moving() or self.controller.get_mirror_height_moving() or self.controller.get_mirror_z_moving() or self.controller.get_camera_x_moving() or self.controller.get_camera_z_moving()
            except TrinamicException:
                print("Trinamic Exception while waiting for camera X, camera Z, mirror Z and mirror height to stop moving")
            except:
                print("Non-Trinamic Exception while waiting for camera X, camera Z, mirror Z and mirror height to stop moving")
        print("Succesfully set all Motors to correct starting positions. Now start Scan!")
        
        #create array of zeros for the rates
        rates=np.zeros(shape=(spacing_y, spacing_x))
        #walk through the whole space of different positions
        #the lesser shifted dimension should be Y, as one needs to move two motors (mirror height, mirror z) to correctly adjust this
        for i in range(0, spacing_y, 1):
            #calculate the position
            pos_y=min_y+(max_y-min_y)/(spacing_y-1)*i
            #move the mirror height accordingly
            self.controller.set_position_mirror_height(pos_y)
            #adjust mirror z so that the pathlength is adjusted for // CURRENTLY ONLY TRUE IF THE INCIDENT ANGLE IS 0!
            self.controller.set_position_camera_z(cam_z+min_mir_y+(max_y-min_y)/(spacing_y-1)*i)
            moving_y=True
            while moving_y:
                sleep(0.05)
                try:
                    moving_y=self.controller.get_camera_z_moving() or self.controller.get_mirror_height_moving()
                except TrinamicException:
                    print("Trinamic Exception while waiting for camera Z and Mirror Height to stop moving")
                except:
                    print("Non-Trinamic Exception while waiting for camera Z and Mirror Height to stop moving")
            #now also move X
            for j in range(0, spacing_x, 1):
                if i%2==0:
                    pos_x=min_x+(max_x-min_x)/(spacing_x-1)*j
                else:
                    pos_x=max_x-(max_x-min_x)/(spacing_x-1)*j
                #print("X: {0} Y: {1}".format(pos_x, pos_y))
                self.controller.set_position_camera_x(pos_x)
                moving_x=True
                try:
                    moving_x=self.controller.get_camera_x_moving()
                except TrinamicException:
                    print("Trinamic Exception while waiting for camera X to stop moving")
                except:
                    print("Non-Trinamic Exception while waiting for camera X to stop moving")
                while moving_x:
                    sleep(0.05)
                    try:
                        moving_x=self.controller.get_camera_x_moving()
                    except TrinamicException:
                        print("Trinamic Exception while waiting for camera X to stop moving")
                    except:
                        print("Non-Trinamic Exception while waiting for camera X to stop moving")
                if i%2==1:
                    rates[spacing_y-i-1][spacing_x-1-j]=self.client.getRateA()+self.client.getRateB()
                else:
                    rates[spacing_y-i-1][j]=self.client.getRateA()+self.client.getRateB()
                self.rates=rates
                self.new_record=True
        sleep(0.1)
        self.still_recording=False
        self.controller.setBussy(False)
        print("Recording of the rate distribution done!")
    #STILL NEEDS FINAL DEBUGGING
    def recordRateDistributionPhiPsi(self, spacing_phi, spacing_psi, min_phi, max_phi, min_psi, max_psi, cam_x, mir_y, cam_z, mir_z, phi, psi):
        if self.mode!="psi-phi":
            raise RuntimeError("The method 'recordRateDistributionPhiPsi' can only be called in psi-phi mode! The mode currently is set to {}".format(self.mode))
        if self.client==None:
            self.still_recording=False
            raise RuntimeError("Error when trying to record a rate. Cannot record rate without a client connected")
        
        #FIRST CONTROLL IF THE POSITIONS ARE POSSIBLE BY CHECKING ALL EXTREMAL POINTS!
        min_x=phi+min_phi
        max_x=phi+max_phi
        min_y=psi+min_psi
        max_y=psi+max_psi
        min_min = geo.check_position_cam_offset(min_phi, min_psi, mir_y, mir_z, cam_z, cam_x)
        min_max = geo.check_position_cam_offset(min_phi, max_psi, mir_y, mir_z, cam_z, cam_x)
        max_min = geo.check_position_cam_offset(max_phi, min_psi, mir_y, mir_z, cam_z, cam_x)
        max_max = geo.check_position_cam_offset(max_phi, max_psi, mir_y, mir_z, cam_z, cam_x)
        if not min_min and min_max and max_min and max_max:
            raise RuntimeError("The rate distribution can not be recorded because some of the measurement positions are out of range! Min_Min {0}, Min_Max {1}, Max_Min {2}, Max_Max {3}".format(min_min, min_max, max_min, max_max))
        
        #change the global parameters so the plot can be redrawn correctly
        self.resetRectangle()
        self.spacing_0=spacing_phi
        self.spacing_1=spacing_psi
        self.min_0=min_phi
        self.max_0=max_phi
        self.min_1=min_psi
        self.max_1=max_psi
        self.camera_z=cam_z
        self.camera_x=cam_x
        self.mirror_z=mir_z
        self.mirror_y=mir_y
        self.mirror_psi=psi
        self.mirror_phi=phi
        self.offset=geo.get_path_length_delta(phi, psi, mir_y, mir_z, cam_z, cam_x)
        
        #set all parameters to the correct positions
        print("Starting to measure the rate distribution. MinPhi={0:4.2f} ; MaxPhi={1:4.2f} ; MinPsi={2:4.2f} ; MaxPsi={3:4.2f} ; SpacingPhi={4} ; SpacingPsi={5}".format(min_phi, max_phi, min_psi, max_psi, spacing_phi, spacing_psi))

        #move psi and phi simultaneously into the starting position
        self.controller.setBussy(True)
        self.controller.set_position_mirror_phi(min_phi) #start from minimum
        self.controller.set_position_mirror_psi(min_psi) #start from minimum
        self.controller.set_position_mirror_height(mir_y)
        self.controller.set_position_mirror_z(mir_z)
        self.controller.set_position_camera_x(cam_x)
        self.controller.set_position_camera_z(cam_z)
        
        #wait till every motor has reached its starting position
        moving_all=True
        while moving_all:
            try:
                moving_all=self.controller.get_mirror_phi_moving() or self.controller.get_mirror_psi_moving() or self.controller.get_mirror_height_moving() or self.controller.get_mirror_z_moving() or self.controller.get_camera_x_moving() or self.controller.get_camera_z_moving()
            except TrinamicException:
                print("Trinamic Exception while waiting for camera X, camera Z, mirror Z and mirror height to stop moving")
            except:
                print("Non-Trinamic Exception while waiting for camera X, camera Z, mirror Z and mirror height to stop moving")
        print("Succesfully set all Motors to correct starting positions. Now start Scan!")
        rates=np.zeros(shape=(spacing_phi, spacing_psi))
        #walk through the whole space of different positions
        for i in range(0, spacing_phi, 1):
            pos_phi=min_phi+(max_phi-min_phi)/(spacing_phi-1)*i
            self.controller.set_position_mirror_phi(pos_phi)
            moving_phi=True
            while moving_phi:
                sleep(0.05)
                try:
                    moving_phi=self.controller.get_mirror_phi_moving()
                except TrinamicException:
                    print("Trinamic Exception while waiting for PHI to stop moving")
                except:
                    print("Non-Trinamic Exception while waiting for PHI to stop moving")
            for j in range(0, spacing_psi, 1):
                if i%2==0:
                    pos_psi=min_psi+(max_psi-min_psi)/(spacing_psi-1)*j
                else:
                    pos_psi=max_psi-(max_psi-min_psi)/(spacing_psi-1)*j
                #print("PSI: {0} PHI: {1}".format(pos_psi, pos_phi))
                self.controller.set_position_mirror_psi(pos_psi)
                moving_psi=True
                try:
                    moving_psi=self.controller.get_mirror_psi_moving()
                except TrinamicException:
                    print("Trinamic Exception while waiting for PSI to stop moving")
                except:
                    print("Non-Trinamic Exception while waiting for PSI to stop moving")
                while moving_psi:
                    sleep(0.05)
                    try:
                        moving_psi=self.controller.get_mirror_psi_moving()
                    except TrinamicException:
                        print("Trinamic Exception while waiting for PSI to stop moving")
                    except:
                        print("Non-Trinamic Exception while waiting for PSI to stop moving")
                if i%2==0:
                    rates[i][spacing_psi-1-j]=self.client.getRateA()+self.client.getRateB()
                else:
                    rates[i][j]=self.client.getRateA()+self.client.getRateB()
                self.rates=np.transpose(rates)
                self.new_record=True
        sleep(0.1)
        self.still_recording=False
        self.controller.setBussy(False)
        print("Recording of the rate distribution done!")
    
    def recordRateDistributionXZ(self, spacing_x, spacing_z, min_cam_x, max_cam_x, min_mir_z, max_mir_z, cam_x, mir_z, offset_cam_z, mir_y, psi, phi):
        if self.mode!="x-z":
            raise RuntimeError("The method 'recordRateDistributionXZ' can only be called in x-z mode! The mode currently is set to {}".format(self.mode))
        if self.client==None:
            self.still_recording=False
            raise RuntimeError("Error when trying to record a rate. Cannot record rate without a client connected")
        
        
        #FIRST CONTROLL IF THE POSITIONS ARE POSSIBLE BY CHECKING ALL EXTREMAL POINTS!
        min_x=cam_x+min_cam_x
        max_x=cam_x+max_cam_x
        min_z=mir_z+min_mir_z
        max_z=mir_z+max_mir_z
        min_min = geo.check_position_cam_offset(phi, psi, mir_y, min_z, offset_cam_z, min_x)
        min_max = geo.check_position_cam_offset(phi, psi, mir_y, max_z, offset_cam_z, max_x)
        max_min = geo.check_position_cam_offset(phi, psi, mir_y, min_z, offset_cam_z, min_x)
        max_max = geo.check_position_cam_offset(phi, psi, mir_y, max_z, offset_cam_z, max_x)
        if not min_min and min_max and max_min and max_max:
            raise RuntimeError("The rate distribution can not be recorded because some of the measurement positions are out of range! Min_Min {0}, Min_Max {1}, Max_Min {2}, Max_Max {3}".format(min_min, min_max, max_min, max_max))

        #change the global parameters so the plot can be redrawn correctly
        self.resetRectangle()
        self.spacing_0=spacing_z
        self.spacing_1=spacing_x
        self.min_0=min_mir_z
        self.max_0=max_mir_z
        self.min_1=min_cam_x
        self.max_1=max_cam_x
        self.camera_z=geo.get_camera_z_position_offset(phi, psi, mir_y, mir_z, offset_pathlength=offset_cam_z)
        self.camera_x=cam_x
        self.mirror_z=mir_z
        self.mirror_y=mir_y
        self.mirror_psi=psi
        self.mirror_phi=phi
        self.offset=offset_cam_z
        
        #set all parameters to the correct starting postions
        self.controller.setBussy(True)
        
        self.controller.set_position_mirror_phi(phi)
        self.controller.set_position_mirror_psi(psi)
        self.controller.set_position_mirror_height(mir_y)
        self.controller.set_position_mirror_z(min_z) #start from minimum
        self.controller.set_position_camera_z(geo.get_camera_z_position_offset(phi, psi, mir_y, min_z, offset_pathlength=offset_cam_z)) # start from minimum
        self.controller.set_position_camera_x(min_x) # start from minimum
        moving_all=True
        while moving_all:
            try:
                moving_all=self.controller.get_mirror_phi_moving() or self.controller.get_mirror_psi_moving() or self.controller.get_mirror_height_moving() or self.controller.get_mirror_z_moving() or self.controller.get_camera_x_moving() or self.controller.get_camera_z_moving()
                debug=False
                if debug:
                    print("Still Moving (PHI, PSI, MIR Y, MIR Z, CAM X, CAM Z) {}{}{}{}{}{}".format(self.controller.get_mirror_phi_moving(), self.controller.get_mirror_psi_moving(), self.controller.get_mirror_height_moving() , self.controller.get_mirror_z_moving(), self.controller.get_camera_x_moving(), self.controller.get_camera_z_moving()))
            except TrinamicException:
                print("Trinamic Exception while waiting for camera X, camera Z, mirror Z and mirror height to stop moving")
            except:
                print("Non-Trinamic Exception while waiting for camera X, camera Z, mirror Z and mirror height to stop moving")
        print("Succesfully set all Motors to correct starting positions. Now start Scan!")
        
        #create array of zeros for the rates
        rates=np.zeros(shape=(spacing_x, spacing_z))
        
        #walk through the whole space of different positions
        #the lesser shifted dimension should be Z, as one needs to move two motors (mirror Z, camera Z) to correctly adjust this
        for j in range(0, spacing_z, 1):
            #calculate the correct x-position (real coord Z) of the mirror
            pos_z=min_z+(max_z-min_z)/(spacing_z-1)*j
            self.controller.set_position_mirror_z(pos_z)
            #also move the camera z along
            self.controller.set_position_camera_z(geo.get_camera_z_position_offset(phi, psi, mir_y, pos_z, offset_pathlength=offset_cam_z))
            moving_z=True
            while moving_z:
                sleep(0.05)
                try:
                    moving_z=self.controller.get_camera_z_moving() or self.controller.get_mirror_z_moving()
                except TrinamicException:
                    print("Trinamic Exception while waiting for camera Z and mirror Z to stop moving")
                except:
                    print("Non-Trinamic Exception while waiting for camera Z and mirror Z to stop moving")
            for i in range(0, spacing_x, 1):
                #calculate the position
                if j%2==0:
                    pos_x=min_x+(max_x-min_x)/(spacing_x-1)*i
                else:
                    pos_x=max_x-(max_x-min_x)/(spacing_x-1)*i
                self.controller.set_position_camera_x(pos_x)
                moving_x=True
                while moving_x:
                    sleep(0.05)
                    try:
                        moving_x=self.controller.get_camera_x_moving()
                    except TrinamicException:
                        print("Trinamic Exception while waiting for camera Z to stop moving")
                    except:
                        print("Non-Trinamic Exception while waiting for camera Z to stop moving")
                if j%2==0:
                    rates[spacing_x-i-1][spacing_z-1-j]=self.client.getRateA()+self.client.getRateB()
                else:
                    rates[i][spacing_z-1-j]=self.client.getRateA()+self.client.getRateB()
                self.rates=rates
                self.new_record=True
        sleep(0.1)
        self.still_recording=False
        self.controller.setBussy(False)
        print("Recording of the rate distribution done!")
        
    def fitGaussian(self):
        #if not done yet: find the rectangle to get some startingvalues
        if self.min_1_rect == None or self.max_1_rect == None or self.min_0_rect == None or self.max_0_rect == None:
            self.findRectangle()
        if self.mode=="psi-phi":
            #calculate starting values for the gaussian
            center_phi=(self.min_0_rect+self.max_0_rect)/2
            center_psi=(self.min_1_rect+self.max_1_rect)/2
            sigma_phi=np.abs(self.min_0_rect-self.max_0_rect)/2
            sigma_psi=np.abs(self.min_1_rect-self.max_1_rect)/2
            offset=0
            prefactor=np.max(self.rates)
            p0=(prefactor, center_phi, sigma_phi, center_psi, sigma_psi, offset)
            print("Starting gaussian fit: p0:   center_phi = {0:5f} ; center_psi = {1:5f} ; sigma_phi = {2:5f} ; sigma_psi = {3:5f} ; offset = {4:5f} ; prefactor = {5:5f}".format(p0[1],p0[3], p0[2], p0[4], p0[5], p0[0]))
            
            #do the fit
            with warnings.catch_warnings(record=True) as w:
                coordinates_phi=np.linspace(self.min_phi, self.max_phi, num=int(self.spacing_phi))
                coordinates_psi=np.linspace(self.min_psi, self.max_psi, num=int(self.spacing_psi))
                x, y=np.meshgrid(coordinates_phi, coordinates_psi)
                #select only the values within the rectangle for the fit
                #if np.size(self.rates)/4>np.sum(mask):
                #    rates_fit=rates[mask]
                #    x_fit=x[mask]
                #    y_fit=y[mask]
                #    print("Only using values within the red square for fit!")
                #else:
                #    rates_fit=rates
                #    x_fit=x
                #    y_fit=y
                x_fit=x
                y_fit=y
                rates_fit=self.rates
                try:
                    popt, pcov = opt.curve_fit(gauss2d, (x_fit,np.flip(y_fit)), rates_fit.ravel(), p0 = p0)
                except RuntimeError as e:
                    w.append(e)
            if len(w)==0:
                data_fitted = gauss2d((x, y), *popt)
                with warnings.catch_warnings(record=True) as w:
                    self.subplot.axes.contour(x, y, data_fitted.reshape(self.spacing_psi, self.spacing_phi), 8, colors='b', label="Gaussian Fit")
                    self.subplot.legend()
                print("Gaussian was fitted and plotted!")
                print("CENTER: phi={0} , psi={1} , SIGMA: phi={2} , psi={3} , CONSTS: prefactor={4} , offset={5}".format(popt[1], popt[3], popt[2], popt[4], popt[0], popt[5]))
                #print("recommended next fit borders: rect_start_phi={0} ; rect_start_psi={1} ; rect_width_phi={2} ; rect_width_psi={3}".format(rect_start_phi, rect_start_psi, rect_width_phi, rect_width_psi))
                self.updateResults(popt)
                self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
                self.canvas.get_tk_widget().grid(row=0, column=0)
                self.canvas.draw()
                self.master.update()
            else:
                print("No Gaussian could be fitted.")
                for warn in w:
                    print(warn)
                popt=[-1, -1, -1, -1, -1, -1]    
            return popt
        elif self.mode=="x-y":
            #calculate starting values for the gaussian
            center_phi=(self.min_0_rect+self.max_0_rect)/2
            center_psi=(self.min_1_rect+self.max_1_rect)/2
            sigma_phi=np.abs(self.min_0_rect-self.max_0_rect)/2
            sigma_psi=np.abs(self.min_1_rect-self.max_1_rect)/2
            offset=0
            prefactor=np.max(self.rates)
            p0=(prefactor, center_phi, sigma_phi, center_psi, sigma_psi, offset)
            print("Starting gaussian fit: p0:   center_x = {0:5f} ; center_y = {1:5f} ; sigma_x = {2:5f} ; sigma_y = {3:5f} ; offset = {4:5f} ; prefactor = {5:5f}".format(p0[1],p0[3], p0[2], p0[4], p0[5], p0[0]))
            
            #do the fit
            with warnings.catch_warnings(record=True) as w:
                coordinates_phi=np.linspace(self.min_0_rect, self.max_0_rect, num=int(self.spacing_0))
                coordinates_psi=np.linspace(self.min_1_rect, self.max_1_rect, num=int(self.spacing_1))
                x, y=np.meshgrid(coordinates_phi, coordinates_psi)
                #select only the values within the rectangle for the fit
                #if np.size(self.rates)/4>np.sum(mask):
                #    rates_fit=rates[mask]
                #    x_fit=x[mask]
                #    y_fit=y[mask]
                #    print("Only using values within the red square for fit!")
                #else:
                #    rates_fit=rates
                #    x_fit=x
                #    y_fit=y
                x_fit=x
                y_fit=y
                rates_fit=self.rates
                try:
                    popt, pcov = opt.curve_fit(gauss2d, (x_fit,np.flip(y_fit)), rates_fit.ravel(), p0 = p0)
                except RuntimeError as e:
                    w.append(e)
            if len(w)==0:
                data_fitted = gauss2d((x, y), *popt)
                with warnings.catch_warnings(record=True) as w:
                    self.subplot.axes.contour(x, y, data_fitted.reshape(self.spacing_1, self.spacing_0), 8, colors='b', label="Gaussian Fit")
                    self.subplot.legend()
                print("Gaussian was fitted and plotted!")
                print("CENTER: x={0} , y={1} , SIGMA: x={2} , y={3} , CONSTS: prefactor={4} , offset={5}".format(popt[1], popt[3], popt[2], popt[4], popt[0], popt[5]))
                #print("recommended next fit borders: rect_start_phi={0} ; rect_start_psi={1} ; rect_width_phi={2} ; rect_width_psi={3}".format(rect_start_phi, rect_start_psi, rect_width_phi, rect_width_psi))
                self.updateResults(popt)
                self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
                self.canvas.get_tk_widget().grid(row=0, column=0)
                self.canvas.draw()
                self.master.update()
            else:
                print("No Gaussian could be fitted.")
                for warn in w:
                    print(warn)
                popt=[-1, -1, -1, -1, -1, -1]    
            return popt
        elif self.mode=="x-z":
            #calculate starting values for the gaussian
            center_phi=(self.min_0_rect+self.max_0_rect)/2
            center_psi=(self.min_1_rect+self.max_1_rect)/2
            sigma_phi=np.abs(self.min_0_rect-self.max_0_rect)/2
            sigma_psi=np.abs(self.min_1_rect-self.max_1_rect)/2
            offset=0
            prefactor=np.max(self.rates)
            p0=(prefactor, center_phi, sigma_phi, center_psi, sigma_psi, offset)
            print("Starting gaussian fit: p0:   center_z = {0:5f} ; center_x = {1:5f} ; sigma_z = {2:5f} ; sigma_x = {3:5f} ; offset = {4:5f} ; prefactor = {5:5f}".format(p0[1],p0[3], p0[2], p0[4], p0[5], p0[0]))
            
            #do the fit
            with warnings.catch_warnings(record=True) as w:
                coordinates_phi=np.linspace(self.max_0, self.min_0, num=int(self.spacing_0))
                coordinates_psi=np.linspace(self.min_1, self.max_1, num=int(self.spacing_1))
                x, y=np.meshgrid(coordinates_phi, coordinates_psi)
                #select only the values within the rectangle for the fit
                #if np.size(self.rates)/4>np.sum(mask):
                #    rates_fit=rates[mask]
                #    x_fit=x[mask]
                #    y_fit=y[mask]
                #    print("Only using values within the red square for fit!")
                #else:
                #    rates_fit=rates
                #    x_fit=x
                #    y_fit=y
                x_fit=x
                y_fit=y
                rates_fit=self.rates
                try:
                    popt, pcov = opt.curve_fit(gauss2d, (x_fit,np.flip(y_fit)), rates_fit.ravel(), p0 = p0)
                except RuntimeError as e:
                    w.append(e)
            if len(w)==0:
                data_fitted = gauss2d((x, y), *popt)
                with warnings.catch_warnings(record=True) as w:
                    self.subplot.axes.contour(x, y, data_fitted.reshape(self.spacing_1, self.spacing_0), 8, colors='b', label="Gaussian Fit")
                    self.subplot.legend()
                print("Gaussian was fitted and plotted!")
                print("CENTER: z={0} , x={1} , SIGMA: z={2} , x={3} , CONSTS: prefactor={4} , offset={5}".format(popt[1], popt[3], popt[2], popt[4], popt[0], popt[5]))
                #print("recommended next fit borders: rect_start_phi={0} ; rect_start_psi={1} ; rect_width_phi={2} ; rect_width_psi={3}".format(rect_start_phi, rect_start_psi, rect_width_phi, rect_width_psi))
                self.updateResults(popt)
                self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
                self.canvas.get_tk_widget().grid(row=0, column=0)
                self.canvas.draw()
                self.master.update()
            else:
                print("No Gaussian could be fitted.")
                for warn in w:
                    print(warn)
                popt=[-1, -1, -1, -1, -1, -1]    
            return popt
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")
    
    def findRectangle(self, contrast_factor=1.5):
        try:
            if len(self.rates)<1:
                raise RuntimeError("The area of interest can't be found if there are no rates! Please load or record a rate file")
        except:
            raise RuntimeError("The area of interest can't be found if there are no rates! Please load or record a rate file")
        rates=self.rates
        if self.mode != "x-z":
            coordinates_phi=np.linspace(self.min_0, self.max_0, num=int(self.spacing_0))
        else:
            coordinates_phi=np.linspace(self.max_0, self.min_0, num=int(self.spacing_0))
        coordinates_psi=np.linspace(self.min_1, self.max_1, num=int(self.spacing_1))
        x, y=np.meshgrid(coordinates_phi, coordinates_psi)
        max_rate=np.max(rates)
        mask=rates>max_rate/contrast_factor
        if np.sum(rates)==len(rates)*len(rates[0])*(-2):
            mask=rates>-3
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
        print(coordinates_phi)
        print(coordinates_psi)
        print("BOX: min_phi={0}; max_phi={1}; min_psi={2}; max_psi={3}".format(coordinates_phi[min_x], coordinates_phi[max_x], coordinates_psi[len(coordinates_psi)-1-max_y], coordinates_psi[len(coordinates_psi)-1-min_y]))
        padding_psi=(coordinates_psi[1]-coordinates_psi[0])/2
        padding_phi=(coordinates_phi[1]-coordinates_phi[0])/2
        rect_start_phi=coordinates_phi[min_x]-padding_phi
        rect_start_psi=coordinates_psi[len(coordinates_psi)-1-min_y]+padding_psi
        rect_width_phi=coordinates_phi[max_x]-coordinates_phi[min_x]+2*padding_phi
        rect_width_psi=coordinates_psi[len(coordinates_psi)-1-max_y]-coordinates_psi[len(coordinates_psi)-1-min_y]-2*padding_psi
        rect = patches.Rectangle((rect_start_phi, rect_start_psi), rect_width_phi, rect_width_psi, edgecolor='r', facecolor='none', label='recommended search area')
        with warnings.catch_warnings(record=True) as w:
            self.subplot.axes.add_patch(rect)
        self.subplot.legend()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.canvas.draw()
        self.master.update()
        print("added rectangle")
        if self.mode=="psi-phi":
            print("rect_start_phi={0} ; rect_start_psi={1} ; rect_width_phi={2} ; rect_width_psi={3}".format(rect_start_phi, rect_start_psi, rect_width_phi, rect_width_psi ))
        elif self.mode=="x-y":
            print("rect_start_x={0} ; rect_start_y={1} ; rect_width_x={2} ; rect_width_y={3}".format(rect_start_phi, rect_start_psi, rect_width_phi, rect_width_psi ))
        elif self.mode=="x-z":
            print("rect_start_x={0} ; rect_start_z={1} ; rect_width_x={2} ; rect_width_z={3}".format(rect_start_phi, rect_start_psi, rect_width_phi, rect_width_psi ))
        self.min_0_rect=rect_start_phi
        self.max_0_rect=rect_start_phi+rect_width_phi
        self.min_1_rect=rect_start_psi+rect_width_psi
        self.max_1_rect=rect_start_psi

    #STILL NEEDS TO BE DEBUGGED
    def changeMode(self, new_mode):
        self.mode=new_mode
        #change labels on the measurement controlls
        if self.mode == "psi-phi":
            #change labels
            min_phi=-4.4
            max_phi=4.4
            min_psi=-4.4
            max_psi=4.4
            self.label_min_0.config(text='Min PHI:  ')
            self.label_max_0.config(text='Max PHI:  ')
            self.label_min_1.config(text='Min PSI:  ')
            self.label_max_1.config(text='Max PSI:  ')
            self.label_spacing_0.config(text='Spacing PHI:  ')
            self.label_spacing_1.config(text='Spacing PSI:  ')
            #change sliders
            self.box_min_0.config(from_=min_phi, to=max_phi, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_0.config(from_=min_phi, to=max_phi, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_min_1.config(from_=min_psi, to=max_psi, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_1.config(from_=min_psi, to=max_psi, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_spacing_0.config(from_=5, to=50, orient=HORIZONTAL, length=150)
            self.box_spacing_1.config(from_=5, to=50, orient=HORIZONTAL, length=150)
            #set initial values
            self.box_min_0.set(min_phi)
            self.box_max_0.set(max_phi)
            self.box_min_1.set(min_psi)
            self.box_max_1.set(max_psi)
        elif self.mode == "x-y":
            min_x=-80
            max_x=80
            min_y=-25
            max_y=25
            #change labels
            self.label_min_0.config(text='Min X:  ')
            self.label_max_0.config(text='Max X:  ')
            self.label_min_1.config(text='Min Y:  ')
            self.label_max_1.config(text='Max Y:  ')
            self.label_spacing_0.config(text='Spacing X:  ')
            self.label_spacing_1.config(text='Spacing Y:  ')
            #change sliders
            self.box_min_0.config(from_=min_x, to=max_x, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_0.config(from_=min_x, to=max_x, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_min_1.config(from_=min_y, to=max_y, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_1.config(from_=min_y, to=max_y, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_spacing_0.config(from_=5, to=50, orient=HORIZONTAL, length=150)
            self.box_spacing_1.config(from_=5, to=50, orient=HORIZONTAL, length=150)
            #set initial values
            self.box_min_0.set(min_x)
            self.box_max_0.set(max_x)
            self.box_min_1.set(min_y)
            self.box_max_1.set(max_y)
        elif self.mode == "x-z":
            min_z=-100
            max_z=100
            min_x=-120
            max_x=120
            #create labels
            self.label_min_0.config(text='Min Z:  ')
            self.label_max_0.config(text='Max Z:  ')
            self.label_min_1.config(text='Min X:  ')
            self.label_max_1.config(text='Max X:  ')
            self.label_spacing_0.config(text='Spacing Z:  ')
            self.label_spacing_1.config(text='Spacing X:  ')
            #create sliders
            self.box_min_0.config(from_=min_z, to=max_z, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_0.config(from_=min_z, to=max_z, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_min_1.config(from_=min_x, to=max_x, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_1.config(from_=min_x, to=max_x, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_spacing_0.config(from_=5, to=50, orient=HORIZONTAL, length=150)
            self.box_spacing_1.config(from_=5, to=50, orient=HORIZONTAL, length=150)
            #set initial values
            self.box_min_0.set(min_z)
            self.box_max_0.set(max_z)
            self.box_min_1.set(min_x)
            self.box_max_1.set(max_x)
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")
       
        #set correct axis to the plot
        if self.mode == "psi-phi":
            self.subplot.set_xlabel("$\phi$ [°]")
            self.subplot.set_ylabel("$\psi$ [°]")
        elif self.mode == "x-y":
            self.subplot.set_xlabel("x [mm]")
            self.subplot.set_ylabel("y [mm]")
        elif self.mode == "x-z":
            self.subplot.set_xlabel("z [mm]")
            self.subplot.set_ylabel("x [mm]")
            self.subplot.invert_xaxis()
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")
        
        if self.mode=="psi-phi":
            self.resultsCenterPhiLabel.config(text='Center PHI:    ')
            self.resultsCenterPsiLabel.config(text='Center PSI:    ')
            self.resultsSigmaPhiLabel.config(text='Sigma PHI:    ')
            self.resultsSigmaPsiLabel.config(text='Sigma PSI:    ')
        elif self.mode=="x-y":
            self.resultsCenterPhiLabel.config(text='Center X:    ')
            self.resultsCenterPsiLabel.config(text='Center Y:    ')
            self.resultsSigmaPhiLabel.config(text='Sigma X:    ')
            self.resultsSigmaPsiLabel.config(text='Sigma Y:    ')
        elif self.mode=="x-z":
            self.resultsCenterPhiLabel.config(text='Center X:    ')
            self.resultsCenterPsiLabel.config(text='Center Z:    ')
            self.resultsSigmaPhiLabel.config(text='Sigma X:    ')
            self.resultsSigmaPsiLabel.config(text='Sigma Z:    ')
        print("Successfully set measurement mode to {0}".format(self.mode))
    
    def loadRates(self):
        if self.mode=="psi-phi": 
            file = filedialog.askopenfile(parent=self.window, initialdir = "../../..", title = "Load Rate Distribution", filetypes = (("universal rate files","*.rateu"),("PSI-PHI rate files","*.ratepp"),("PSI-PHI rate files old","*.rate"),("all files","*.*")))
        elif self.mode=="x-y":
            file = filedialog.askopenfile(parent=self.window, initialdir = "../../..", title = "Load Rate Distribution", filetypes = (("universal rate files","*.rateu"),("X-Y rate files", ".ratexy"),("X-Y rate files old","*.ratel"),("all files","*.*")))
        elif self.mode=="x-z":
            file = filedialog.askopenfile(parent=self.window, initialdir = "../../..", title = "Load Rate Distribution", filetypes = (("universal rate files","*.rateu"),("X-Y rate files","*.ratexz"),("all files","*.*")))
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")  
        if file!=None:
            if ".rateu" in file.name:
                #open the file using the configparser
                config = configparser.ConfigParser()
                config.read(file.name)
                print("Opened file {0} --- now reading.".format(file.name))
                #check if the mode of the file fits the mode of the GUI
                if self.mode != config["meta"]["mode"]:
                    raise RuntimeError("Cannot open this file! The fileformat is not correct. Maybe the Rate Analyzer needs to be in another mode? File mode is {0} but GUI mode is {1}".format(config["meta"]["mode"], self.mode))
                #gather all values from the file
                self.mirror_phi=float(config["position"]["phi"])
                self.mirror_psi=float(config["position"]["psi"])
                self.camera_x=float(config["position"]["camera_x"])
                self.camera_z=float(config["position"]["camera_z"])
                self.offset=float(config["position"]["offset_z"])
                self.mirror_y=float(config["position"]["mirror_y"])
                self.mirror_z=float(config["position"]["mirror_z"])
                self.min_0=float(config["range"]["min_0"])
                self.max_0=float(config["range"]["max_0"])
                self.min_1=float(config["range"]["min_1"])
                self.max_1=float(config["range"]["max_1"])
                self.spacing_0=int(config["range"]["spacing_0"])
                self.spacing_1=int(config["range"]["spacing_1"])
                array_data=config["raw"]["rates"]
                lines=array_data.splitlines()
                rates=np.empty((self.spacing_1, self.spacing_0))
                lines[0]=lines[0].replace("[[", "[")
                lines[-1]=lines[-1].replace("]]", "]")
                for no in range(0, len(lines), 1):
                    lines[no]=lines[no].replace("[","")
                    lines[no]=lines[no].replace("]","")
                    entries=lines[no].split()
                    for no_2 in range(0, len(entries), 1):
                        rates[no][no_2]=float(entries[no_2])
                self.rates=rates
            else:
                string=file.read()
                parts=string.split("~")
                if self.mode=="psi-phi":
                    if ".rate" not in file.name and ".ratepp" not in file.name:
                        raise RuntimeError("Cannot open this file! The fileformat is not correct. Maybe the Rate Analyzer needs to be in another mode?")
                    self.min_0=float(parts[0])
                    self.max_0=float(parts[1])
                    self.min_1=float(parts[2])
                    self.max_1=float(parts[3])
                    self.spacing_1=int(parts[4])
                    self.spacing_0=int(parts[5])
                    if len(parts)==7:
                        self.camera_z=np.nan
                        self.camera_x=np.nan
                        self.mirror_z=np.nan
                        self.mirror_y=np.nan
                        array_data=parts[6]
                    else:
                        self.camera_z=float(parts[6])
                        self.camera_x=float(parts[7])
                        self.mirror_z=float(parts[8])
                        self.mirror_y=float(parts[9])
                        array_data=parts[10]
                    lines=array_data.splitlines()
                    rates=np.empty((self.spacing_1, self.spacing_0))
                    lines[0]=lines[0].replace("[[", "[")
                    lines[-1]=lines[-1].replace("]]", "]")
                    for no in range(0, len(lines), 1):
                        lines[no]=lines[no].replace("[","")
                        lines[no]=lines[no].replace("]","")
                        entries=lines[no].split()
                        for no_2 in range(0, len(entries), 1):
                            rates[no][no_2]=float(entries[no_2])
                    self.rates=rates
                elif self.mode=="x-y" :
                    if ".ratel" not in file.name and ".ratexy" not in file.name:
                        raise RuntimeError("Cannot open this file! The fileformat is not correct. Maybe the Rate Analyzer needs to be in another mode?")
                    self.min_0=float(parts[0])
                    self.max_0=float(parts[1])
                    self.min_1=float(parts[2])
                    self.max_1=float(parts[3])
                    self.spacing_0=int(parts[4])
                    self.spacing_1=int(parts[5])
                    if len(parts)==7:
                        self.psi=np.nan
                        self.phi=np.nan
                        self.mirror_z=np.nan
                        self.offset_pathlength=np.nan
                        array_data=parts[6]
                    else:
                        self.psi=float(parts[6])
                        self.phi=float(parts[7])
                        self.offset_pathlengtht=float(parts[8])
                        self.mirror_z=float(parts[9])
                        array_data=parts[10]
                    lines=array_data.splitlines()
                    rates=np.empty((self.spacing_1, self.spacing_0))
                    lines[0]=lines[0].replace("[[", "[")
                    lines[-1]=lines[-1].replace("]]", "]")
                    for no in range(0, len(lines), 1):
                        lines[no]=lines[no].replace("[","")
                        lines[no]=lines[no].replace("]","")
                        entries=lines[no].split()
                        for no_2 in range(0, len(entries), 1):
                            rates[no][no_2]=float(entries[no_2])
                    self.rates=rates
                elif self.mode=="x-z" :
                    if ".ratexz" not in file.name:
                        raise RuntimeError("Cannot open this file! The fileformat is not correct. Maybe the Rate Analyzer needs to be in another mode?")
                    self.min_0=float(parts[0])
                    self.max_0=float(parts[1])
                    self.min_1=float(parts[2])
                    self.max_1=float(parts[3])
                    self.spacing_1=int(parts[4])
                    self.spacing_0=int(parts[5])
                    self.psi=float(parts[6])
                    self.phi=float(parts[7])
                    self.offset_pathlengtht=float(parts[8])
                    self.mirror_y=float(parts[9])
                    array_data=parts[10]
                    lines=array_data.splitlines()
                    rates=np.empty((self.spacing_0, self.spacing_1))
                    lines[0]=lines[0].replace("[[", "[")
                    lines[-1]=lines[-1].replace("]]", "]")
                    for no in range(0, len(lines), 1):
                        lines[no]=lines[no].replace("[","")
                        lines[no]=lines[no].replace("]","")
                        entries=lines[no].split()
                        for no_2 in range(0, len(entries), 1):
                            rates[no][no_2]=float(entries[no_2])
                    self.rates=rates
                else:
                    raise RuntimeError("The measuring mode needs to be definied correctly!")  
            self.resetRectangle()
            self.replotRates()

    def saveRates(self, path=None):
        if path==None:
            if self.mode=="psi-phi":
                file = filedialog.asksaveasfile(parent=self.window, initialdir = "../../..", title = "Save Rate Distribution", filetypes = (("universal rate files","*.rateu"),("PSI-PHI rate files","*.ratepp"),("all files","*.*")))
            elif self.mode=="x-y":
                file = filedialog.asksaveasfile(parent=self.window, initialdir = "../../..", title = "Save Rate Distribution", filetypes = (("universal rate files","*.rateu"),("X-Y rate files","*.ratexy"),("all files","*.*")))
            elif self.mode=="x-z":
                file = filedialog.asksaveasfile(parent=self.window, initialdir = "../../..", title = "Save Rate Distribution", filetypes = (("universal rate files","*.rateu"),("X-Z rate files","*.ratexz"),("all files","*.*")))
            else:
                raise RuntimeError("The measuring mode needs to be definied correctly!") 
        else:
            file = open(path, "w")
        if file!=None:
            #file=open(filename, "w")
            if ".rateu" in file.name:
                #save as .rateu file
                #create file the configparser
                config = configparser.ConfigParser()
                #save all values of the current plot into the file
                config["meta"]={"mode" : self.mode,
                    "timestamp saved" : time.time()}
                config["position"]={"phi" : self.mirror_phi,
                    "psi" : self.mirror_psi,
                    "camera_x":self.camera_x,
                    "camera_z":self.camera_z,
                    "offset_z":self.offset,
                    "mirror_y":self.mirror_y,
                    "mirror_z":self.mirror_z,}
                config["range"]={"min_0":self.min_0,
                    "max_0":self.max_0,
                    "min_1":self.min_1,
                    "max_1":self.max_1,
                    "spacing_0":self.spacing_0,
                    "spacing_1":self.spacing_1}
                config["raw"]={"rates":self.rates}
                config.write(file)
            elif self.mode=="psi-phi":
                file.write("{0}~{1}~{2}~{3}~{4}~{5}~{6}~{7}~{8}~{9}~{10}".format(self.min_phi, self.max_phi, self.min_psi, self.max_psi, self.spacing_psi, self.spacing_phi, self.camera_z, self.camera_x, self.mirror_z, self.mirror_y, np.array2string(self.rates, threshold=10e9)).replace("\n ", "").replace("]", "]\n").replace("]\n]", "]]"))
            elif self.mode=="x-y":
                file.write("{0}~{1}~{2}~{3}~{4}~{5}~{6}~{7}~{8}~{9}~{10}".format(self.min_x, self.max_x, self.min_y, self.max_y, self.spacing_0, self.spacing_y, self.phi, self.psi, self.offset_pathlength, self.mirror_z, np.array2string(self.rates, threshold=10e9)).replace("\n ", "").replace("]", "]\n").replace("]\n]", "]]"))
            elif self.mode=="x-z":
                file.write("{0}~{1}~{2}~{3}~{4}~{5}~{6}~{7}~{8}~{9}~{10}".format(self.min_x, self.max_x, self.min_z, self.max_z, self.spacing_0, self.spacing_z, self.phi, self.psi, self.offset_pathlength, self.mirror_y, np.array2string(self.rates, threshold=10e9)).replace("\n ", "").replace("]", "]\n").replace("]\n]", "]]"))
            else:
                raise RuntimeError("The measuring mode needs to be definied correctly!")    
            file.close()
            print("Sucessfully saved the current rates as {0}".format(file.name))
    
    def offsetMode(self):
        if self.offset_bool.get() == 1:
            self.label_starting_cam_z.config(text="Offset:")
            self.box_starting_cam_z.config(from_=-10, to=10)
        elif self.offset_bool.get() == 0:
            self.label_starting_cam_z.config(text="Camera Z:")
            self.box_starting_cam_z.config(from_=0, to=139)
    
    def updateDeviation(self):
        while(True):
            sleep(0.1)
            delta_correction=self.getCurrentPointingOffset()
            self.deviation_alt_Label_pos.config(text="{0:4.2f}".format(delta_correction[1]))
            self.deviation_az_Label_pos.config(text="{0:4.2f}".format(delta_correction[0]))
            print(self.box_min_0.get())
        
        
#THIS NEEDS TO BE TESTED
    def adoptCurrentGuess(self):
        cam_x, cam_z, phi, psi, mir_z, mir_y =  geo.get_optimal_parameters_current_guess()
        self.box_starting_cam_x.set(cam_x)
        self.box_starting_cam_z.set(cam_z)
        self.box_starting_phi.set(phi)
        self.box_starting_psi.set(psi)
        self.box_starting_mir_z.set(mir_z)
        self.box_starting_mir_y.set(mir_y)
    
    def adoptProposal(self):
        #set the sliders to the borders of the rectangle
        self.box_min_phi.set(self.min_0_rect)
        self.box_max_phi.set(self.max_0_rect)
        self.box_min_psi.set(self.min_1_rect)
        self.box_max_psi.set(self.max_1_rect)
        
        #do some more complex approximations for the spacing
        spacing_psi=-1
        spacing_phi=-1
        psi_active=None
        if (self.max_0_rect-self.min_0_rect)>(self.max_1_rect-self.min_1_rect):
            #the phi range is larger than the psi range!
            if spacing_phi/spacing_psi>3:
                spacing_psi=4 #because width should be at least 4
                psi_active=True
            else:
                spacing_phi=10 #because length should be at least 10
                psi_active=False
        else:
            #the psi range is larger than the phi range!
            if spacing_psi/spacing_phi>3:
                spacing_phi=4 #because width should be at least 4
                psi_active=False
            else:
                spacing_psi=10 #because length should be at least 10
                psi_active=True
        if psi_active:
            #calculate the correct phi for about square pixels
            spacing_phi=(self.max_0_rect-self.min_0_rect)/(self.max_1_rect-self.min_1_rect)*spacing_psi
        else:
            #calculate the correct psi for about square pixels
            spacing_psi=(self.max_1_rect-self.min_1_rect)/(self.max_0_rect-self.min_0_rect)*spacing_phi
        #set sliders for the spacing
        self.box_spacing_0.set(spacing_phi)
        self.box_spacing_1.set(spacing_psi)
    
    def resetRectangle(self):
        min_1_rect=None
        max_1_rect=None
        min_0_rect=None
        max_0_rect=None
    
    def updateResults(self, results):
        self.resultsCenterPhiLabel['text']='Center PHI: {0:3.2f}'.format(results[1])
        self.resultsCenterPsiLabel['text']='Center PSI: {0:3.2f}'.format(results[3])
        self.resultsSigmaPhiLabel['text']='Sigma PHI:  {0:3.2f}'.format(results[2])
        self.resultsSigmaPsiLabel['text']='Sigma PSI:  {0:3.2f}'.format(results[4])
        self.resultsOffsetLabel['text']='Offset:     {0:3.2f}'.format(results[5])
        self.resultsPrefactorPhiLabel['text']='Prefactor:  {0:3.2f}'.format(results[0])
    
    #NEEDS makeover. Records a batch of measurements that are specified in a file and safes the measured rates.
    def crazyBatch(self):
        #this method is used to get a huge batch of data in many different configuarations of the setup.
        
    
        ########################################################################################
        #  this method will perform all measurements that are listed in the loaded file        #
        #																					   #
        #																					   #
        #  in ANGELD MODE the measurements are to be stored as follows:                        #
        #																					   #
        #            ANGLED MODE                 LINEAR Mode                                   #
        #	     [0] position_camera_z        // PHI                                           #
        #	     [1] position_camera_x        // PSI                                           #
        #	     [2] position_mirror_z        // offset pathlength                             #
        #	     [3] position_mirror_y        // mirror Z                                      #
        #	     [4] phi_min                  // min X                                         #
        #	     [5] phi_max                  // max X                                         #
        #	     [6] psi_min                  // min Y                                         #
        #	     [7] psi_max                  // max Y                                         #
        #	     [8] spacing_phi              // spacing X                                     #
        #	     [9] spacing_psi              // spacing Y                                     #
        #	  the results are stored in the same way, but additionally contain:                #
        #	     [10] id / number of measurement                                               #
        #	     [11] center_phi              // center X                                      #
        #	     [12] center_psi              // center X                                      #
        #	     [13] sigma_phi               // sigma X                                       #
        #	     [14] sigma_psi               // sigma Y                                       #
        #	     [15] prefactor                                                                #
        #	     [16] offset                                                                   #
        #	     [17] timestamp                                                                #
        #	                                                                                   #
        #	     The mode of measurement can be differentiated by checking the                 #
        #	     header of the csv file for the column names                                   #
        #	                                                                                   #
        ########################################################################################
            
        if self.mode=="psi-phi": 
            file = filedialog.askopenfile(parent=self.window, initialdir = "../../..", title = "Load Rate Distribution", filetypes = (("Angular batch csv","*.csv"),("all files","*.*")))
        elif self.mode=="x-y":
            file = filedialog.askopenfile(parent=self.window, initialdir = "../../..", title = "Load Rate Distribution", filetypes = (("X-Y batch csv","*.csv"),("all files","*.*")))
        elif self.mode=="x-z":
            file = filedialog.askopenfile(parent=self.window, initialdir = "../../..", title = "Load Rate Distribution", filetypes = (("X-Z batch csv","*.csv"),("all files","*.*")))
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")  
        if file!=None:
            first_line=file.read()
            if "position_camera_z" in first_line:
                file_mode="psi-phi"
            elif "PHI" in first_line:
                file_mode="x-y"
            elif "min_z" in first_line:
                file_mode="x-z"
            else:
                raise RuntimeError("The loaded .csv file contains an incorrect header! Please check the file formating!")
            if file_mode is not self.mode:
                raise RuntimeError("You tried to load a file of the {0} mode type but the current mode is {1}".format(file_mode, self.mode))
            name=file.name
            print("Openend file {0}".format(name))
            measurements=np.genfromtxt(name, delimiter=',', skip_header = 1)
            print("Start to do a crazy batch!")
            self.controller.setBatch(True)
            path="../../../crazy_batch"
            try:
                #print(path)
                os.mkdir(path, mode=0o777)
                #print("{0}/rates".format(path))
                os.mkdir("{0}/rates".format(path), mode=0o777)
            except:
                raise RuntimeError("Cannot create new directory! Does the directory already exist? Please check and retry!")
                
            results=np.zeros(shape=(len(measurements), 18))
            no=0
            print(measurements)
            if self.mode=="x-y":
                for m in measurements:
                    self.controller.setBussy(True)
                    print("Next measurement is: Phi: {0:5.2f} ; Psi: {1:5.2f} ; offset_pathlength: {2:5.2f}  ; Mirror Z: {3:5.2f} ; x_min: {4:5.2f} ; x_max: {5:5.2f} ; y_min: {6:5.2f} ; y_max: {7:5.2f} ; spacing_x: {8:5.2f} ; spacing_y: {9:5.2f}".format(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9]))
                    
                    #move setup in the right position
                    self.phi=m[0]
                    self.psi=m[1]
                    self.offset_pathlength=m[2]
                    #print("Offset_Pathlength={}".format(self.offset_pathlength))
                    self.mirror_z=m[3]
                    #print("Mirror Z={}".format(self.mirror_z))
                    self.controller.set_position_mirror_phi(self.phi, verbose=False)
                    self.controller.set_position_mirror_psi(self.psi, verbose=False)
                    self.controller.set_position_mirror_z(self.mirror_z, verbose=False)
                    
                    #wait till the setup is in the right position
                    moving_all=True
                    while moving_all:
                        sleep(0.05)
                        try:
                            moving_all=self.controller.get_mirror_phi_moving() or self.controller.get_mirror_psi_moving() or self.controller.get_mirror_z_moving()
                        except TrinamicException:
                            print("Trinamic Exception while waiting for 3 Dimensions to stop moving")
                        except:
                            print("Not Trinamic Exception but something else while waiting for 3 Dimensions to stop moving")
                    try:
                        self.psi=self.controller.get_position_mirror_psi()
                        self.phi=self.controller.get_position_mirror_phi()
                        self.mirror_z=self.controller.get_mirror_z()
                    except TrinamicException:
                        try:
                            self.psi=self.controller.get_position_mirror_psi()
                            self.phi=self.controller.get_position_mirror_phi()
                            self.camera_z=self.controller.get_camera_z()
                        except TrinamicException:
                            print("Tried twice to get the Positions but failed both times (Trinamic Exception)! Instead take the ones that were initally set!")
                            self.psi=m[0]
                            self.phi=m[1]
                            self.mirror_z=m[3]
                        except:
                            print("Tried twice to get the Positions but failed both times (But not Trinamic Exception)! Instead take the ones that were initally set!")
                            self.psi=m[0]
                            self.phi=m[1]
                            self.mirror_z=m[3]
                    except:
                        print("Tried to get the Positions but failed both times (No Trinamic Exception)! Instead take the ones that were initally set!")
                        self.psi=m[0]
                        self.psi=m[1]
                        self.mirror_z=m[3]
            
                    #measure the rate distribution
                    #set the sliders to the borders of the rectangle
                    self.box_min_0.set(m[4])
                    self.box_max_0.set(m[5])
                    self.box_min_1.set(m[6])
                    self.box_max_1.set(m[7])
                    self.box_spacing_0.set(m[8])
                    self.box_spacing_1.set(m[9])
                    
                    #record the distribution
                    self.recordRateDistributionRead()
                    self.controller.setBussy(True)
                    #save the rates
                    save_path="{0}/rates/{1:03d}_individual.ratel".format(path, no)
                    self.saveRates(save_path)
                    
                    #do the gauss-fit
                    try:
                        gaussian=self.fitGaussian()
                    except:
                        gaussian=np.array(['nan','nan','nan','nan','nan','nan'])
                        print("No Gaussian could be fitted. No worries. Maybe it works for the next plot..")
                    
                    #save the parameters of the gaussian to the results array
                    for i in range(0,10,1):
                        results[no][i]=m[i]
                    results[no][10]=no
                    results[no][11]=gaussian[1]
                    results[no][12]=gaussian[3]
                    results[no][13]=gaussian[2]
                    results[no][14]=gaussian[4]
                    results[no][15]=gaussian[0]
                    results[no][16]=gaussian[5]
                    results[no][17]=time.time()
                    np.savetxt("{0}/results.txt".format(path), results, delimiter=',')
                    no+=1
            elif self.mode=="psi-phi":
                for m in measurements:
                    self.controller.setBussy(True)
                    print("Next measurement is: Pos_Cam_Z: {0:5.2f} ; Pos_Cam_X: {1:5.2f} ; Pos_mirr_Z: {2:5.2f}  ; Pos_mirr_Height: {3:5.2f} ; phi_min: {4:5.2f} ; phi_max: {5:5.2f} ; psi_min: {6:5.2f} ; psi_max: {7:5.2f} ; spacing_psi: {8:5.2f} ; spacing_phi: {9:5.2f}".format(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9]))
                    
                    #move setup in the right position
                    self.camera_z=m[0]
                    self.camera_x=m[1]
                    self.mirror_z=m[2]
                    self.mirror_y=m[3]
                    self.controller.set_position_camera_z(self.camera_z, verbose=True)
                    self.controller.set_position_camera_x(self.camera_x, verbose=True)
                    self.controller.set_position_mirror_z(self.mirror_z, verbose=True)
                    self.controller.set_position_mirror_height(self.mirror_y, verbose=True)
                    
                    #wait till the setup is in the right position
                    moving_all=True
                    try:
                        moving_all=self.controller.get_camera_z_moving() or self.controller.get_camera_x_moving() or self.controller.get_mirror_z_moving() or self.controller.get_mirror_height_moving()
                    except TrinamicException:
                        print("Trinamic Exception while waiting for 4 Dimensions to stop moving")
                    except:
                        print("Not Trinamic Exception but something else while waiting for 4 Dimensions to stop moving")
                    while moving_all:
                        sleep(0.05)
                        try:
                            moving_all=self.controller.get_camera_z_moving() or self.controller.get_camera_x_moving() or self.controller.get_mirror_z_moving() or self.controller.get_mirror_height_moving()
                        except TrinamicException:
                            print("Trinamic Exception while waiting for 4 Dimensions to stop moving")
                        except:
                            print("Not Trinamic Exception but something else while waiting for 4 Dimensions to stop moving")
                    try:
                        self.camera_z=self.controller.get_position_camera_z()
                        self.camera_x=self.controller.get_position_camera_x()
                        self.mirror_z=self.controller.get_position_mirror_z()
                        self.mirror_y=self.controller.get_position_mirror_height()
                    except TrinamicException:
                        try:
                            self.camera_z=self.controller.get_position_camera_z()
                            self.camera_x=self.controller.get_position_camera_x()
                            self.mirror_z=self.controller.get_position_mirror_z()
                            self.mirror_y=self.controller.get_position_mirror_height()
                        except TrinamicException:
                            print("Tried twice to get the Positions but failed both times (Trinamic Exception)! Instead take the ones that were initally set!")
                            self.camera_z=m[0]
                            self.camera_x=m[1]
                            self.mirror_z=m[2]
                            self.mirror_y=m[3]
                        except:
                            print("Tried twice to get the Positions but failed both times (But notTrinamic Exception)! Instead take the ones that were initally set!")
                            self.camera_z=m[0]
                            self.camera_x=m[1]
                            self.mirror_z=m[2]
                            self.mirror_y=m[3]
                    except:
                        print("Tried to get the Positions but failed both times (No Trinamic Exception)! Instead take the ones that were initally set!")
                        self.camera_z=m[0]
                        self.camera_x=m[1]
                        self.mirror_z=m[2]
                        self.mirror_y=m[3]

            
                    #measure the rate distribution
                    #set the sliders to the borders of the rectangle
                    self.box_min_0.set(m[4])
                    self.box_max_0.set(m[5])
                    self.box_min_1.set(m[6])
                    self.box_max_1.set(m[7])
                    self.box_spacing_0.set(m[8])
                    self.box_spacing_1.set(m[9])
                    
                    #record the distribution
                    self.recordRateDistributionRead()
                    self.controller.setBussy(True)
                    #save the rates
                    save_path="{0}/rates/{1:03d}_individual.rate".format(path, no)
                    self.saveRates(save_path)
                    
                    #do the gauss-fit
                    try:
                        gaussian=self.fitGaussian()
                    except:
                        gaussian=np.array(['nan','nan','nan','nan','nan','nan'])
                        print("No Gaussian could be fitted. No worries. Maybe it works for the next plot..")
                        
                    #save the parameters of the gaussian to the results array
                    for i in range(0,10,1):
                        results[no][i]=m[i]
                    results[no][10]=no
                    results[no][11]=gaussian[1]
                    results[no][12]=gaussian[3]
                    results[no][13]=gaussian[2]
                    results[no][14]=gaussian[4]
                    results[no][15]=gaussian[0]
                    results[no][16]=gaussian[5]
                    results[no][17]=time.time()
                    np.savetxt("{0}/results.txt".format(path), results, delimiter=',')
                    no+=1
            else:
                raise RuntimeError("The measuring mode needs to be definied correctly!")
            self.controller.setBussy(False)
            self.controller.setBatch(False)
            print("The batch is done!")
    #this is meant to be run in a thread of its own, so it can be terminated if needed. It writes a logfile with all releavent measaurements and safes all distributions
    def runOptimizer(self, xz_large=True, xz_small=True, cam_z_opt=True):
        self.log.log("Start a run of runOptimzier.")
        #safe the system time
        start_time=time.time()
        #create directory to which all information is safed
        path="../../../LOG"
        try:
            #print("{0}/rates".format(path))
            #print("{0}/{1}".format(path, start_time))
            os.mkdir("{0}/{1:10.0f}".format(path, start_time), mode=0o777)
            path="{0}/{1:10.0f}".format(path, start_time)
            #print("{0}/{1}/rates".format(path, start_time))
            os.mkdir("{0}/rates".format(path), mode=0o777)
        except:
            raise RuntimeError("Cannot create new directory! Does the directory already exist? Please check and retry!")
        
        #setup logfile
        logging.basicConfig(filename="{0}/log.log".format(path), level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d-%H:%M:%S')
        #get initial guess
        cam_x, cam_z, phi, psi, mir_z, mir_y =  0, 51, 0, 0, 380, 133
        i_cam_x, i_cam_z, i_phi, i_psi, i_mir_z, i_mir_y = cam_x, cam_z, phi, psi, mir_z, mir_y
        message="Initial guess: cam_x={0} cam_z={1} phi={2} psi={3} mir_z={4} mir_y={5}".format(cam_x, cam_z, phi, psi, mir_z, mir_y)
        print(message)
        logging.debug(message)
        
        #run an x-z scan with very low resolution in the range of the expectation (+- 50mm / +- 70mm)
        if xz_large:
            message="Start X-Z  (large) scan now"
            print(message)
            logging.debug(message)
            #set the correct mode for the GUI
            self.changeMode("x-z")
            #input the correct parameters
            self.box_min_0.set(-50) #this is Z
            self.box_max_0.set(50)
            self.box_min_1.set(-70) #this is X
            self.box_max_1.set(70)
            self.box_spacing_0.set(7)
            self.box_spacing_1.set(7)
            self.box_starting_cam_x.set(cam_x)
            self.box_starting_cam_z.set(cam_z)
            self.box_starting_mir_y.set(mir_y)
            self.box_starting_mir_z.set(mir_z)
            self.box_starting_phi.set(phi)
            self.box_starting_psi.set(psi)
            try:
                self.recordRateDistributionRead()
            except:
                return -1
            #save the rates
            save_path="{0}/rates/xz_large.rateu".format(path)
            self.saveRates(save_path)
            #do a rectangle "fit" to find the new center
            self.findRectangle()
            #move MIR Z by shifting it to the center of the rectangle
            mir_z=mir_z+(self.min_0_rect+self.max_0_rect)/2
            #also move the cam_z in accordance with the movement of mir_z so their distance is kept
            cam_z=cam_z+(self.min_0_rect+self.max_0_rect)/2
            #lastly move CAM X by shifting it to the center of the rectangle
            cam_x=cam_x+(self.min_1_rect+self.max_1_rect)/2
            message="Found new center (X-Z large) at X={0} and Z={1}".format(cam_x, mir_z)
            print(message)
            logging.debug(message)
            
        #run an x-z scan with high resoution in closer to the expected center (1.5 times the area of the red box)
        if xz_small:
            message="Start X-Z (small) scan now"
            print(message)
            logging.debug(message)
            #set the correct mode for the GUI
            self.changeMode("x-z")
            #calculate some of the new parameters
            width=abs(self.max_0_rect-self.min_0_rect)*1.5
            height=abs(self.max_1_rect-self.min_1_rect)*1.5
            #check if the size of the red rectangle restricts the next measurement to something meaningful
            if width>(geo.max_cam_z-geo.min_cam_z)*1.1 or width>(geo.max_mir_z-geo.min_mir_z)*1.1:
                message="After the large X-Z scan the rectangle was too large to produce a meaningfull next measurement. Terminated!"
                print(message)
                logging.debug(message)
                return -1
            message="Straight forward calulation of the width resulted in CAM Z: {0} +- {1} and MIR Z {2} +- {3} and CAM X {4} +- {5}".format(cam_x, width/2, mir_z, width/2, cam_x, height/2)
            print(message)
            logging.debug(message)
            #check if the scan exceeds any boarders of the paramters and in this case adjust accordingly
            if cam_z-width/2<geo.min_cam_z:
                old_cam_z=cam_z
                old_mir_z=mir_z
                cam_z+=geo.min_cam_z-(old_cam_z-width/2)+1
                mir_z+=geo.min_cam_z-(old_cam_z-width/2)+1
                message="The next scan would have been to close to the minimum of CAM Z (proposed: CAM Z={0} MIR Z={1}. The scan range was therefore adjusted accordingly (new: CAM Z={2} MIR Z={3}).".format(old_cam_z, old_mir_z, cam_z, mir_z)
                print(message)
                logging.debug(message)
            if mir_z-width/2<geo.min_mir_z:
                old_cam_z=cam_z
                old_mir_z=mir_z
                mir_z+=geo.min_mir_z-(old_mir_z-width/2)+1
                cam_z+=geo.min_mir_z-(old_mir_z-width/2)+1
                message="The next scan would have been to close to the minimum of MIR Z (proposed: CAM Z={0} MIR Z={1}. The scan range was therefore adjusted accordingly (new: CAM Z={2} MIR Z={3}).".format(old_cam_z, old_mir_z, cam_z, mir_z)
                print(message)
                logging.debug(message)
            if cam_z+width/2>geo.max_cam_z:
                old_cam_z=cam_z
                old_mir_z=mir_z
                cam_z+=geo.max_cam_z-(old_cam_z+width/2)-1
                mir_z+=geo.max_cam_z-(old_cam_z+width/2)-1
                message="The next scan would have been to close to the maximum of CAM Z (proposed: CAM Z={0} MIR Z={1}. The scan range was therefore adjusted accordingly (new: CAM Z={2} MIR Z={3}).".format(old_cam_z, old_mir_z, cam_z, mir_z)
                print(message)
                logging.debug(message)
            if mir_z+width/2>geo.max_mir_z:
                old_cam_z=cam_z
                old_mir_z=mir_z
                mir_z+=geo.max_mir_z-(old_mir_z+width/2)-1
                cam_z+=geo.max_mir_z-(old_mir_z+width/2)-1
                message="The next scan would have been to close to the maximum of MIR Z (proposed: CAM Z={0} MIR Z={1}. The scan range was therefore adjusted accordingly (new: CAM Z={2} MIR Z={3}).".format(old_cam_z, old_mir_z, cam_z, mir_z)
                print(message)
                logging.debug(message)

            #input the correct parameters
            self.box_min_0.set(-width/2)
            self.box_max_0.set(width/2)
            self.box_min_1.set(-height/2)
            self.box_max_1.set(height/2)
            self.box_spacing_0.set(7)
            self.box_spacing_1.set(7)
            self.box_starting_cam_x.set(cam_x)
            self.box_starting_cam_z.set(cam_z)
            self.box_starting_mir_y.set(mir_y)
            self.box_starting_mir_z.set(mir_z)
            self.box_starting_phi.set(phi)
            self.box_starting_psi.set(psi)
            try:
                self.recordRateDistributionRead()
            except:
                return -1
            #save the rates
            save_path="{0}/rates/xz_small.rateu".format(path)
            self.saveRates(save_path)
            #do a gaussian fit to find the center
            try:
                self.findRectangle()
                gaussian=self.fitGaussian()
                #fix mir Z and set new guess for cam x
                message="Successfully fitted gaussian!"
                print(message)
                logging.debug(message)
                cam_x=cam_x+gaussian[3]
                mir_z=mir_z+gaussian[1]
            except Exception as e:
                message="No gaussian could be fitted. Instead use center of the box."
                logging.debug(message)
                cam_x=cam_x+(self.max_1_rect-self.min_1_rect)/2
                mir_z=mir_z+(self.max_1_rect-self.min_1_rect)/2
                print(e)

        self.controller.set_position_mirror_phi(phi)
        self.controller.set_position_mirror_psi(psi)
        self.controller.set_position_mirror_z(mir_z)
        self.controller.set_position_mirror_height(mir_y)
        self.controller.set_position_camera_x(cam_x)
        self.controller.set_position_camera_z(cam_z)
        #wait till every motor has reached its position
        moving_all=True
        while moving_all:
            try:
                moving_all=self.controller.get_mirror_phi_moving() or self.controller.get_mirror_psi_moving() or self.controller.get_mirror_height_moving() or self.controller.get_mirror_z_moving() or self.controller.get_camera_x_moving() or self.controller.get_camera_z_moving()
            except TrinamicException:
                print("Trinamic Exception while waiting for camera X, camera Z, mirror Z, mirror Y, Phi and Psi to stop moving")
            except:
                print("Non-Trinamic Exception while waiting for camera X, camera Z, mirror Z, mirror Y, Phi and Psi to stop moving")
        print("Succesfully set all Motors to correct positions.")

	#lastly opimize cam z if stated
        if cam_z_opt:
            self.log.log("Now optimize the cam Z:")
            cam_z_min=cam_z-20
            cam_z_max=cam_z+20
	    #now correct if cam_z would be to close to one end
            if cam_z_min<1:
                delta=abs(cam_z_min-1)
                cam_z_min=1
                cam_z_max+=delta
            if cam_z_max>geo.max_cam_z:
                cam_z_max=geo.cam_z_max-1
            if mir_z-cam_z_max<geo.min_dist_mir_cam_z:
                cam_z_max=mir_z-geo.min_dist_cam_z-1
            self.log.log("Cam Z runs from {0} to {1}".format(cam_z_min, cam_z_max))
            #now slowly walk through the parameterspace for cam_z
            cam_z_values=np.linspace(cam_z_min, cam_z_max, num=30)
            rates=[]
            for pos in cam_z_values:
                self.controller.set_position_camera_z(pos)
                sleep(1)
                rates.append(self.client.getRateA()+self.client.getRateB())
            max_rate=np.amax(rates)
            cam_z=cam_z_values[np.where(rates==max_rate)][0]
            self.log.log("Found optimal cam z at {}".format(cam_z))
            self.controller.set_position_camera_z(cam_z)
        #calcuate how long it took
        duration=time.time()-start_time
        message="The optimisations routine took {0} seconds.".format(duration) #check converions!?
        print(message)
        logging.debug(message)
        self.log.log("Succesfully finished a run of runOptimzier.")
        self.log.log(message)
        self.log.log("The final parameters are: cam_x={0} cam_z={1} phi={2} psi={3} mir_z={4} mir_y={5}".format(cam_x, cam_z, phi, psi, mir_z, mir_y))
        if self.position!=None:
            az, alt= self.position.get_az_alt()
        else:
            az, alt = -1, -1
        self.log.set_experimental(cam_x, cam_z, mir_z, az, alt,  time.time())
        #Terminate and return time (in seconds) if succesfull. Otherwise -1.
        return duration

    #tells you how much the system would be shifted in order to correct the pointing according to the pointing model
    def getCurrentPointingOffset(self):
    #get current az alt position
        current_az, current_alt = self.position.get_az_alt()
        #load the former az alt position and the corresponding time and setup positions from the log
        last_cam_x, last_cam_z, last_mir_z, last_az, last_alt, last_time = self.log.get_last()
        if last_az==None or last_alt==None:
            return (float('NaN'), float('NaN'))
        #find out which pointing file we use by reading the config file
        #first find out which machine this is
        motor_pc_no = None
        this_config = configparser.ConfigParser()
        this_config.read('../../../this_pc.conf')
        if "who_am_i" in this_config:
            if this_config["who_am_i"]["type"]!="motor_pc":
                print("According to the 'this_pc.config'-file this pc is not meant as a motor pc! Please fix that!")
                exit()
            motor_pc_no = int(this_config["who_am_i"]["no"])
        else:
            print("There is no config file on this computer which specifies the computer function! Please fix that!")
            exit()
        this_config = configparser.ConfigParser()
        this_config.read('../global.conf')
        filepath=this_config["motor_pc_{}".format(motor_pc_no)]["pointing_file"]
        #now load the pointing model
        p=pointing.PointingModel()
        print(filepath)
        p.load_from_file(filepath)
        last_correction = p.get_correction(last_az, last_alt)
        current_correction = p.get_correction(current_az, current_alt)
        #calculate from angular values to lateral (rad to mm)
        last_correction*=geo.dish_focal_length
        current_correction*=geo.dish_focal_length
        delta_correction=current_correction-last_correction
        return delta_correction
        
    #corrects the position of cam x, cam z and mir z according to the pointing model
    def correctPointing(self):
        delta_correction=self.getCurrentPointingOffset()
        self.controller.setBussy(True)
        cam_x=self.controller.get_position_camera_x()
        cam_z=self.controller.get_position_camera_z()
        mir_z=self.controller.get_position_mirror_z()
        self.controller.set_position_camera_x(cam_x+delta_correction[0])
        self.controller.set_position_camera_z(cam_z+delta_correction[1])
        self.controller.set_position_mirror_z(mir_z+delta_correction[1])
        self.controller.setBussy(False)
        log.log("Corrected the pointing according to the pointingmodel.")       
        log.log("    Moved cam x = {0} to {1} ({2}) ; cam z = {3} to {4} ({5}) ; mir_z = {6} to {7} ({8})".format(cam_x, cam_x+delta_correction[0], delta_correction[0], cam_z, cam_z+delta_correction[1], delta_correction[1], mir_z, mir_z+delta_correction[1], delta_correction[1]))  

    def runOptimizerOld(self, xz_large=False, xz_small=False, xy=True, xy_dist_closer=0, xy_dist_further=0, optimal_offset=4):
        self.log.log("Start a run of runOptimzier.")
        #safe the system time
        start_time=time.time()
        #create directory to which all information is safed
        path="../../../LOG"
        try:
            #print("{0}/rates".format(path))
            #print("{0}/{1}".format(path, start_time))
            os.mkdir("{0}/{1:10.0f}".format(path, start_time), mode=0o777)
            path="{0}/{1:10.0f}".format(path, start_time)
            #print("{0}/{1}/rates".format(path, start_time))
            os.mkdir("{0}/rates".format(path), mode=0o777)
        except:
            raise RuntimeError("Cannot create new directory! Does the directory already exist? Please check and retry!")
        
        #setup logfile
        logging.basicConfig(filename="{0}/log.log".format(path), level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d-%H:%M:%S')
        #get initial guess
        cam_x, cam_z, phi, psi, mir_z, mir_y =  geo.get_optimal_parameters_current_guess()
        i_cam_x, i_cam_z, i_phi, i_psi, i_mir_z, i_mir_y = cam_x, cam_z, phi, psi, mir_z, mir_y
        message="Initial guess: cam_x={0} cam_z={1} phi={2} psi={3} mir_z={4} mir_y={5}".format(cam_x, cam_z, phi, psi, mir_z, mir_y)
        print(message)
        logging.debug(message)
        
        #run an x-z scan with very low resolution in the range of the expectation (+- 50mm)
        if xz_large:
            message="Start X-Z  (large) scan now"
            print(message)
            logging.debug(message)
            #set the correct mode for the GUI
            self.changeMode("x-z")
            #input the correct parameters
            self.box_min_0.set(-30)
            self.box_max_0.set(30)
            self.box_min_1.set(-30)
            self.box_max_1.set(30)
            self.box_spacing_0.set(6)
            self.box_spacing_1.set(6)
            self.box_starting_cam_x.set(cam_x)
            self.box_starting_cam_z.set(cam_z)
            self.box_starting_mir_y.set(mir_y)
            self.box_starting_mir_z.set(mir_z)
            self.box_starting_phi.set(phi)
            self.box_starting_psi.set(psi)
            try:
                self.recordRateDistributionRead()
            except:
                return -1
            #save the rates
            save_path="{0}/rates/xz_large.rateu".format(path)
            self.saveRates(save_path)
            #do a rectangle "fit" to find the new center
            self.findRectangle()
            #move MIR Z by shifting it to the center of the rectangle
            mir_z=mir_z+(self.min_0_rect+self.max_0_rect)/2
            #also move the cam_z in accordance with the movement of mir_z so their distance is kept
            cam_z=cam_z+(self.min_0_rect+self.max_0_rect)/2
            #lastly move CAM X by shifting it to the center of the rectangle
            cam_x=cam_x+(self.min_1_rect+self.max_1_rect)/2
            message="Found new center (X-Z large) at X={0} and Z={1}".format(cam_x, mir_z)
            print(message)
            logging.debug(message)
            
        #run an x-z scan with high resoution in closer to the expected center (1.5 times the area of the red box)
        if xz_small:
            message="Start X-Z (small) scan now"
            print(message)
            logging.debug(message)
            #set the correct mode for the GUI
            self.changeMode("x-z")
            #calculate some of the new parameters
            width=abs(self.max_0_rect-self.min_0_rect)*1.5
            height=abs(self.max_1_rect-self.min_1_rect)*1.5
            #check if the size of the red rectangle restricts the next measurement to something meaningful
            if width>(geo.max_cam_z-geo.min_cam_z)*1.1 or width>(geo.max_mir_z-geo.min_mir_z)*1.1:
                message="After the large X-Z scan the rectangle was too large to produce a meaningfull next measurement. Terminated!"
                print(message)
                logging.debug(message)
                return -1
            message="Straight forward calulation of the width resulted in CAM Z: {0} +- {1} and MIR Z {2} +- {3} and CAM X {4} +- {5}".format(cam_x, width/2, mir_z, width/2, cam_x, height/2)
            print(message)
            logging.debug(message)
            #check if the scan exceeds any boarders of the paramters and in this case adjust accordingly
            if cam_z-width/2<geo.min_cam_z:
                old_cam_z=cam_z
                old_mir_z=mir_z
                cam_z+=geo.min_cam_z-(old_cam_z-width/2)+1
                mir_z+=geo.min_cam_z-(old_cam_z-width/2)+1
                message="The next scan would have been to close to the minimum of CAM Z (proposed: CAM Z={0} MIR Z={1}. The scan range was therefore adjusted accordingly (new: CAM Z={2} MIR Z={3}).".format(old_cam_z, old_mir_z, cam_z, mir_z)
                print(message)
                logging.debug(message)
            if mir_z-width/2<geo.min_mir_z:
                old_cam_z=cam_z
                old_mir_z=mir_z
                mir_z+=geo.min_mir_z-(old_mir_z-width/2)+1
                cam_z+=geo.min_mir_z-(old_mir_z-width/2)+1
                message="The next scan would have been to close to the minimum of MIR Z (proposed: CAM Z={0} MIR Z={1}. The scan range was therefore adjusted accordingly (new: CAM Z={2} MIR Z={3}).".format(old_cam_z, old_mir_z, cam_z, mir_z)
                print(message)
                logging.debug(message)
            if cam_z+width/2>geo.max_cam_z:
                old_cam_z=cam_z
                old_mir_z=mir_z
                cam_z+=geo.max_cam_z-(old_cam_z+width/2)-1
                mir_z+=geo.max_cam_z-(old_cam_z+width/2)-1
                message="The next scan would have been to close to the maximum of CAM Z (proposed: CAM Z={0} MIR Z={1}. The scan range was therefore adjusted accordingly (new: CAM Z={2} MIR Z={3}).".format(old_cam_z, old_mir_z, cam_z, mir_z)
                print(message)
                logging.debug(message)
            if mir_z+width/2>geo.max_mir_z:
                old_cam_z=cam_z
                old_mir_z=mir_z
                mir_z+=geo.max_mir_z-(old_mir_z+width/2)-1
                cam_z+=geo.max_mir_z-(old_mir_z+width/2)-1
                message="The next scan would have been to close to the maximum of MIR Z (proposed: CAM Z={0} MIR Z={1}. The scan range was therefore adjusted accordingly (new: CAM Z={2} MIR Z={3}).".format(old_cam_z, old_mir_z, cam_z, mir_z)
                print(message)
                logging.debug(message)

            #input the correct parameters
            self.box_min_0.set(-width/2)
            self.box_max_0.set(width/2)
            self.box_min_1.set(-height/2)
            self.box_max_1.set(height/2)
            self.box_spacing_0.set(10)
            self.box_spacing_1.set(10)
            self.box_starting_cam_x.set(cam_x)
            self.box_starting_cam_z.set(cam_z)
            self.box_starting_mir_y.set(mir_y)
            self.box_starting_mir_z.set(mir_z)
            self.box_starting_phi.set(phi)
            self.box_starting_psi.set(psi)
            try:
                self.recordRateDistributionRead()
            except:
                return -1
            #save the rates
            save_path="{0}/rates/xz_small.rateu".format(path)
            self.saveRates(save_path)
            #do a gaussian fit to find the center
            try:
                self.findRectangle()
                gaussian=self.fitGaussian()
                #fix mir Z and set new guess for cam x
                if gaussian == [-1, -1, -1, -1, -1, -1]:
                    message="No gaussian could be fitted. Instead use center of the box."
                    print(message)
                    logging.debug(message)
                    cam_x=cam_x+(self.max_1_rect-self.min_1_rect)/2
                    mir_z=mir_z+(self.max_1_rect-self.min_1_rect)/2
                else:
                    cam_x=cam_x+gaussian[3]
                    mir_z=mir_z+gaussian[1]
            except:
                message="Error while fitting the gaussian. This sucks! No clue what to do now."
                print(message)
                logging.debug(message)
        #run an offset measurement for 2 different distances
        if xy:
            #set the correct mode for the GUI
            self.changeMode("x-y")
            
            ################
            # FIRST OFFSET #
            ################
            
            #the first offset is the closer measurement
            message="Start X-Y scan (closer) now"
            print(message)
            logging.debug(message)
            
            message="Current guess: cam_x={0} cam_z={1} phi={2} psi={3} mir_z={4} mir_y={5}".format(cam_x, cam_z, phi, psi, mir_z, mir_y)
            print(message)
            logging.debug(message)
            
            #calculate the positions of the first scan
            min_0=-20
            max_0=20
            min_1=geo.min_mir_y-mir_y+1
            max_1=geo.max_mir_y-mir_y-1
            spacing_0=10
            spacing_1=10
            cam_z=mir_z-geo.min_dist_mir_cam_z-max_1-xy_dist_closer-1
            print("cam_z=mir_z-geo.min_dist_mir_cam_z-max_1-xy_dist_closer-1_dist_closer-1 equals {0}={1}-{2}-{3}-{4}-1".format(cam_z,mir_z,geo.min_dist_mir_cam_z,max_1,xy_dist_closer))
            cam_z_closer=cam_z
            
            #input the correct parameters
            self.box_min_0.set(min_0)
            self.box_max_0.set(max_0)
            self.box_min_1.set(min_1)
            self.box_max_1.set(max_1)
            self.box_spacing_0.set(spacing_0)
            self.box_spacing_1.set(spacing_1)
            self.box_starting_cam_x.set(cam_x)
            self.box_starting_cam_z.set(cam_z)
            self.box_starting_mir_y.set(mir_y)
            self.offset_bool.set(0)
            self.box_starting_mir_z.set(mir_z)
            self.box_starting_phi.set(phi)
            self.box_starting_psi.set(psi)
            
            message="Start XY closer with: cam_x={0} cam_z={1} phi={2} psi={3} mir_z={4} mir_y={5}".format(cam_x, cam_z, phi, psi, mir_z, mir_y)
            print(message)
            logging.debug(message)
            
            try:
                self.recordRateDistributionRead()
            except:
                return -1
            #save the rates
            save_path="{0}/rates/xy_closer.rateu".format(path)
            self.saveRates(save_path)
            #fit a gaussian and safe its parameters
            self.findRectangle()
            gaussian_closer=self.fitGaussian()
            if gaussian_closer==[-1, -1, -1, -1, -1, -1] :
                message="No gaussian could be fitted to the XY closer. Instead use the brightest pixel as center."
                print(message)
                logging.debug(message)
                brightest=np.max(self.rates)
                mask=self.rates==brightest
                print(mask)
                #need to implement finding of coordinates here
            
            #################
            # SECOND OFFSET #
            #################
            
            #the second offset is the further measurement
            message="Start X-Y scan (further) now"
            print(message)
            logging.debug(message)
            
            
            #calculate the positions of the second scan
            min_0=-20
            max_0=20
            min_1=geo.min_mir_y-mir_y+1
            max_1=geo.max_mir_y-mir_y-1
            spacing_0=10
            spacing_1=10
            cam_z=0+xy_dist_further+max_1+1
            if cam_z<=0:
                cam_z=1
            cam_z_further=cam_z
            #input the correct parameters
            self.box_min_0.set(min_0)
            self.box_max_0.set(max_0)
            self.box_min_1.set(min_1)
            self.box_max_1.set(max_1)
            self.box_spacing_0.set(spacing_0)
            self.box_spacing_1.set(spacing_1)
            self.box_starting_cam_x.set(cam_x)
            self.box_starting_cam_z.set(cam_z)
            self.box_starting_mir_y.set(mir_y)
            self.offset_bool.set(0)
            self.box_starting_mir_z.set(mir_z)
            self.box_starting_phi.set(phi)
            self.box_starting_psi.set(psi)
            
            message="Start XY further with: cam_x={0} cam_z={1} phi={2} psi={3} mir_z={4} mir_y={5}".format(cam_x, cam_z, phi, psi, mir_z, mir_y)
            print(message)
            logging.debug(message)
            try:
                self.recordRateDistributionRead()
            except:
                return -1
            #save the rates
            save_path="{0}/rates/xy_further.rateu".format(path)
            self.saveRates(save_path)
            #fit a gaussian and safe its parameters
            try:
                self.findRectangle()
                gaussian_further=self.fitGaussian()
            except:
                message="No Gaussian could be fitted. This sucks! No clue what to do now."
                print(message)
                logging.debug(message)
                return -1
            
            ######################
            # FIX THE PARAMETERS #
            ######################
            
            #from the shift of the center we can learn about the nesscesairy corrections in PSI and PHI
            #only correct the angles if the divergence is larger than 1mm
            #first do the phi parameter
            if abs(gaussian_closer[1]-gaussian_further[1])>1:
                distance=cam_z_closer-cam_z_further
                difference=gaussian_closer[1]-gaussian_further[1]
                #calculate angle through trigonometry
                phi=phi+math.atan(diffence/distance)*180/math.pi
            #first do the psi parameter
            if abs(gaussian_closer[3]-gaussian_further[3])>1:
                distance=cam_z_closer-cam_z_further
                difference=gaussian_closer[3]-gaussian_further[3]
                #calculate angle through trigonometry
                psi=phi+math.arctan(diffence/distance)*180/math.pi
            
            #from the centers of our fits we can now also calculate the correct position of MIR Y and CAM X
            #MIR Y
            if abs(gaussian_closer[1]-gaussian_further[1])<1:
                #in case we did not change anything in PSI we will just take the center of the closer scan as our MIR Y
                mir_y=mir_y+gaussian_closer[1]
            else:
                #in this case we have to account for the shift in height due to the change in PSI
                mir_y=mir_y+gaussian_closer[1]
                message="WARNING: There is no implementation for this mode yet! Continue as if this was without any change in PSI!"
                print(message)
                logging.debug(message)
            #CAM X
            if abs(gaussian_closer[3]-gaussian_further[3])<1:
                #in case we did not change anything in PHI we will just take the center of the closer scan as our CAM X
                cam_x=cam_x+gaussian_closer[3]
            else:
                #in this case we have to account for the shift in height due to the change in PHI
                cam_x=cam_x+gaussian_closer[3]
                message="WARNING: There is no implementation for this mode yet! Continue as if this was without any change in PHI!"
                print(message)
                logging.debug(message)
            #CAM Z
            #The cam z now needs too be adjusted so it uses the correct pathlength
            #set the correct incoming ray in the geometry package!
            # ---> This needs to be implemented
            #calculate the CAM Z given the other parameters
            cam_z=geo.get_camera_z_position_offset(phi, psi, mir_y, mir_z, offset_pathlength=optimal_offset)
            if(cam_z<0):
                message="Warning: CAM Z should be {0} but this is not possible. We therefore set it to 0".format(cam_z)
                print(message)
                logging.debug(message)
                cam_z=0
        print("New position: cam_x={0} ({1}) cam_z={2} ({3}) phi={4} ({5}) psi={6} ({7}) mir_z={8} ({9}) mir_y={10} ({11})".format(cam_x, cam_x-i_cam_x, cam_z, cam_z-i_cam_z, phi, phi-i_phi, psi, psi-i_psi, mir_z, mir_z-i_mir_z, mir_y, mir_y-i_mir_y))
        #set the positions according to the results of the measurements
        self.controller.setBussy(True)
        
        self.controller.set_position_mirror_phi(phi)
        self.controller.set_position_mirror_psi(psi)
        self.controller.set_position_mirror_z(mir_z)
        self.controller.set_position_mirror_height(mir_y)
        self.controller.set_position_camera_x(cam_x)
        self.controller.set_position_camera_z(cam_z)
        #wait till every motor has reached its starting position
        moving_all=True
        while moving_all:
            try:
                moving_all=self.controller.get_mirror_phi_moving() or self.controller.get_mirror_psi_moving() or self.controller.get_mirror_height_moving() or self.controller.get_mirror_z_moving() or self.controller.get_camera_x_moving() or self.controller.get_camera_z_moving()
            except TrinamicException:
                print("Trinamic Exception while waiting for camera X, camera Z, mirror Z, mirror Y, Phi and Psi to stop moving")
            except:
                print("Non-Trinamic Exception while waiting for camera X, camera Z, mirror Z, mirror Y, Phi and Psi to stop moving")
        print("Succesfully set all Motors to correct positions.")
        #calcuate how long it took
        duration=time.time()-start_time
        message="The optimisations routine took {0} seconds.".format(duration) #check converions!?
        print(message)
        logging.debug(message)
        self.log.log("Succesfully finished a run of runOptimzier.")
        self.log.log(message)
        self.log.log("The final parameters are: cam_x={0} cam_z={1} phi={2} psi={3} mir_z={4} mir_y={5}".format(cam_x, cam_z, phi, psi, mir_z, mir_y))
        az, alt= position.get_az_alt()
        self.log.set_experimental(cam_x, cam_z, mir_z, az, alt,  time.time())
        #Terminate and return time (in seconds) if succesfull. Otherwise -1.
        return duration

    #tells you how much the system would be shifted in order to correct the pointing according to the pointing model
    def getCurrentPointingOffset(self):
    #get current az alt position
        current_az, current_alt = self.position.get_az_alt()
        #load the former az alt position and the corresponding time and setup positions from the log
        last_cam_x, last_cam_z, last_mir_z, last_az, last_alt, last_time = self.log.get_last()
        if last_az==None or last_alt==None:
            return (float('NaN'), float('NaN'))
        #find out which pointing file we use by reading the config file
        #first find out which machine this is
        motor_pc_no = None
        this_config = configparser.ConfigParser()
        this_config.read('../../../this_pc.conf')
        if "who_am_i" in this_config:
            if this_config["who_am_i"]["type"]!="motor_pc":
                print("According to the 'this_pc.config'-file this pc is not meant as a motor pc! Please fix that!")
                exit()
            motor_pc_no = int(this_config["who_am_i"]["no"])
        else:
            print("There is no config file on this computer which specifies the computer function! Please fix that!")
            exit()
        this_config = configparser.ConfigParser()
        this_config.read('../global.conf')
        filepath=this_config["motor_pc_{}".format(motor_pc_no)]["pointing_file"]
        #now load the pointing model
        p=pointing.PointingModel()
        print(filepath)
        p.load_from_file(filepath)
        last_correction = p.get_correction(last_az, last_alt)
        current_correction = p.get_correction(current_az, current_alt)
        #calculate from angular values to lateral (rad to mm)
        last_correction*=geo.dish_focal_length
        current_correction*=geo.dish_focal_length
        delta_correction=current_correction-last_correction
        return delta_correction
        
    #corrects the position of cam x, cam z and mir z according to the pointing model
    def correctPointing(self):
        delta_correction=self.getCurrentPointingOffset()
        self.controller.setBussy(True)
        cam_x=self.controller.get_position_camera_x()
        cam_z=self.controller.get_position_camera_z()
        mir_z=self.controller.get_position_mirror_z()
        self.controller.set_position_camera_x(cam_x+delta_correction[0])
        self.controller.set_position_camera_z(cam_z+delta_correction[1])
        self.controller.set_position_mirror_z(mir_z+delta_correction[1])
        self.controller.setBussy(False)
        log.log("Corrected the pointing according to the pointingmodel.")       
        log.log("    Moved cam x = {0} to {1} ({2}) ; cam z = {3} to {4} ({5}) ; mir_z = {6} to {7} ({8})".format(cam_x, cam_x+delta_correction[0], delta_correction[0], cam_z, cam_z+delta_correction[1], delta_correction[1], mir_z, mir_z+delta_correction[1], delta_correction[1]))       

def gauss2d(datapoints, prefactor=1, x_0=0, x_sigma=1, y_0=0, y_sigma=1, offset=0):
    return offset+prefactor*np.exp(-(np.power(datapoints[0]-x_0, 2)/(2*np.power(x_sigma,2)))-(np.power(datapoints[1]-y_0,2)/(2*np.power(y_sigma,2)))).ravel()
    
class initDialog(simpledialog.Dialog):
    ## this thing inherits stuff from the SimpleDialog class
    def body(self, master):  ## wird ueberschrieben
        self.title('Measurement mode')
        self.mode=IntVar()
        self.label=Label(master, text="Measurement mode", justify = LEFT, padx = 20).pack()
        self.xy=Radiobutton(master, text="X - Y", padx = 20, variable=self.mode, value=1).pack(anchor=W)
        self.psi_phi=Radiobutton(master, text="PSI - PHI", padx = 20, variable=self.mode, value=2).pack(anchor=W)
        self.xz=Radiobutton(master, text="X - Z", padx = 20, variable=self.mode, value=3).pack(anchor=W)

        return self.xy #set focus on the X-Y option


    def apply(self): # override
        self.result = self.mode
