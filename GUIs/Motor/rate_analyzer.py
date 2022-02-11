import threading
import scipy.optimize as opt
from numpy import random
from tkinter import *
from tkinter import simpledialog
from tkinter import filedialog

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

import geometry as geo

#updating=False


class RATE_ANALYZER():
    
    client=None
    controller=None
    change_mirror_psi=False
    change_mirror_phi=False
    
    #measurement mode
    mode=None
    
    #currently loaded distribution
    rates=None
    
    #in case of a psi-phi measurement
    min_phi=-4.4
    max_phi=4.4
    min_psi=-4.4
    max_psi=4.4
    spacing_psi=10
    spacing_phi=10
    camera_z=np.nan
    camera_x=np.nan
    mirror_z=np.nan
    mirror_height=np.nan
    #in case of a X-Y measurment
    min_x=-10
    max_x=10
    min_y=-10
    max_y=10
    spacing_x=10
    spacing_y=10
    offset_pathlength=0
    mirror_z=350
    phi=0
    psi=0
    #in case of a X-Z measurement (additional to the ones from an X-Y measurement)
    min_z=-10
    max_z=10
    spacing_z=10
    
    #currently set rectangle
    min_psi_rect=None
    max_psi_rect=None
    min_phi_rect=None
    max_phi_rect=None
    
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
    label_min_psi=None
    label_max_psi=None
    label_min_phi=None
    label_max_phi=None
    label_spacing_phi=None
    label_spacing_psi=None
    label_min_x=None
    label_max_x=None
    label_min_y=None
    label_max_y=None
    label_spacing_x=None
    label_spacing_y=None
    checkbutton_live=None
    adoptButton=None 
    box_min_phi=None
    box_max_phi=None
    box_min_psi=None
    box_max_psi=None
    box_spacing_phi=None
    box_spacing_psi=None
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
    mirHLabel = None
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
    do_magic_button =None
    
    #values for (live) recording
    still_recording=False
    new_record=False

    figure=None
    subplot=None
    legend=None
    
    def __init__(self, master, controller=None, client=None):
        #copy stuff
        self.controller=controller
        self.client=client
        self.master=master
        
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
            
        #get positions of the controller
        self.controller.setBussy(True)
        sleep(0.1)
        self.camera_z=controller.get_position_camera_z()
        self.camera_x=controller.get_position_camera_x()
        self.mirror_z=controller.get_position_mirror_z()
        self.mirror_height=controller.get_position_mirror_height()
        self.controller.setBussy(False)
        
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
        
        self.plot_frame = Frame(self.main_frame, width=600, height=900)
        self.plot_frame.grid(row=0, column=0, padx=10,pady=10)
        self.plot_frame.config(background = "#003366")
        
        self.positions_frame = Frame(self.plot_frame, width=600, height=100)
        self.positions_frame.grid(row=1, column=0, padx=10,pady=5)
        self.positions_frame.config(background = "#FFFFFF")
        
        self.pos_line_1_frame = Frame(self.positions_frame, width=600, height=100)
        self.pos_line_1_frame.grid(row=0, column=0, padx=0,pady=0)
        self.pos_line_1_frame.config(background = "#FFFFFF")
        
        self.pos_line_2_frame = Frame(self.positions_frame, width=600, height=100)
        self.pos_line_2_frame.grid(row=1, column=0, padx=0,pady=0)
        self.pos_line_2_frame.config(background = "#FFFFFF")
        
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
        
        self.variables_frame  = Frame(self.control_frame, width=320, height=600)
        self.variables_frame.grid(row=1, column=1, padx=10)
        self.variables_frame.config(background = "#DBDBDB")
        
        self.current_guess_frame  = Frame(self.control_frame, width=320, height=120)
        self.current_guess_frame.grid(row=3, column=1, padx=10)
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
        if self.mode == "psi-phi":
            self.subplot.set_xlabel("$\phi$ [°]")
            self.subplot.set_ylabel("$\psi$ [°]")
            self.subplot.set_xlim((self.min_phi, self.max_phi))
            self.subplot.set_ylim((self.min_psi, self.max_psi))
        elif self.mode == "x-y":
            self.subplot.set_xlabel("x [mm]")
            self.subplot.set_ylabel("y [mm]")
            self.subplot.set_xlim((self.min_x, self.max_x))
            self.subplot.set_ylim((self.min_y, self.max_y))
        elif self.mode == "x-z":
            self.subplot.set_xlabel("z [mm]")
            self.subplot.set_ylabel("x [mm]")
            self.subplot.invert_xaxis()
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.canvas.draw()
        
        
        ###################
        # POSITIONS FRAME #
        ###################
        
        #create labels
        self.camZLabel = Label(self.pos_line_1_frame, pady=5, text='Camera Z: {0:4.1f}'.format(self.camera_z), width="15", background ="#FFFFFF")
        self.camXLabel = Label(self.pos_line_1_frame, pady=5, text='Camera X: {0:4.1f}'.format(self.camera_x), width="15", background ="#FFFFFF")
        self.mirZLabel = Label(self.pos_line_1_frame, pady=5, text='Mirror Z: {0:4.1f}'.format(self.mirror_z), width="15", background ="#FFFFFF")
        self.mirHLabel = Label(self.pos_line_1_frame, pady=5, text='Mirror Y: {0:4.1f}'.format(self.mirror_height), width="20", background ="#FFFFFF")
        self.mirPhiLabel = Label(self.pos_line_2_frame, pady=5, text='Mirror PSI: {0:4.1f}'.format(self.psi), width="18", background ="#FFFFFF")
        self.mirPsiLabel = Label(self.pos_line_2_frame, pady=5, text='Mirror PHI: {0:4.1f}'.format(self.phi), width="18", background ="#FFFFFF")
        self.offsetLabel = Label(self.pos_line_2_frame, pady=5, text='Offset: {0:4.1f}'.format(geo.get_path_length_delta(self.phi, self.psi, self.mirror_height, self.mirror_z, self.camera_z, self.camera_x), width="18"), background ="#FFFFFF")
        
        #place labels
        self.camZLabel.grid(row=0, column=0)
        self.camXLabel.grid(row=0, column=1)
        self.mirZLabel.grid(row=0, column=2)
        self.mirHLabel.grid(row=0, column=3)
        self.mirPhiLabel.grid(row=0, column=0)
        self.mirPsiLabel.grid(row=0, column=1)
        self.offsetLabel.grid(row=0, column=2)
        
        ##############
        # FILE FRAME #
        ##############
        
        #add GUI elements
        self.loadButton = Button(self.control_frame, text="Load Rate Distribution", width=31, pady=3, padx=3, command=self.loadRates)
        self.loadButton.grid(row=0,column=0)
        self.saveButton = Button(self.control_frame, text="Save Rate Distribution", width=31, pady=3, padx=3, command=self.saveRates)
        self.saveButton.grid(row=0,column=1)
        
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
        #initial values of the scales
        min_phi=-4.4
        max_phi=4.4
        min_psi=-4.4
        max_psi=4.4
        spacing_phi=10
        spacing_psi=11
        
        min_x=-50
        max_x=50
        min_y=121
        max_y=145
        spacing_x=10
        spacing_y=11
        
        min_z=-50
        max_z=50
        spacing_z=11
        
        
        if self.mode == "psi-phi":
            #create labels
            self.label_min_psi = Label(self.record_frame, text='Min PSI:  ')
            self.label_max_psi = Label(self.record_frame, text='Max PSI:  ')
            self.label_min_phi = Label(self.record_frame, text='Min PHI:  ')
            self.label_max_phi = Label(self.record_frame, text='Max PHI:  ')
            self.label_spacing_phi = Label(self.record_frame, text='Spacing PHI:  ')
            self.label_spacing_psi = Label(self.record_frame, text='Spacing PSI:  ')
            #place labels in grid
            self.label_min_phi.grid(row=0, column=0, padx=10, pady=3)
            self.label_max_phi.grid(row=1, column=0, padx=10, pady=3)
            self.label_min_psi.grid(row=2, column=0, padx=10, pady=3)
            self.label_max_psi.grid(row=3, column=0, padx=10, pady=3)
            self.label_spacing_phi.grid(row=4, column=0, padx=10, pady=3)
            self.label_spacing_psi.grid(row=5, column=0, padx=10, pady=3)
            #create sliders
            self.box_min_phi = Scale(self.record_frame, from_=-4.4, to=4.4, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_phi = Scale(self.record_frame, from_=-4.4, to=4.4, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_min_psi = Scale(self.record_frame, from_=-4.4, to=4.4, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_psi = Scale(self.record_frame, from_=-4.4, to=4.4, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_spacing_phi = Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            self.box_spacing_psi = Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            #place sliders in grid
            self.box_min_phi.grid(row=0, column=1, padx=10, pady=3)
            self.box_max_phi.grid(row=1, column=1, padx=10, pady=3)
            self.box_min_psi.grid(row=2, column=1, padx=10, pady=3)
            self.box_max_psi.grid(row=3, column=1, padx=10, pady=3)
            self.box_spacing_phi.grid(row=4, column=1, padx=10, pady=3)
            self.box_spacing_psi.grid(row=5, column=1, padx=10, pady=3)
            #set initial values
            self.box_min_phi.set(min_phi)
            self.box_max_phi.set(max_phi)
            self.box_min_psi.set(min_psi)
            self.box_max_psi.set(max_psi)
            self.box_spacing_phi.set(spacing_phi)
            self.box_spacing_psi.set(spacing_psi)
        elif self.mode == "x-y":
            self.label_min_x = Label(self.record_frame, text='Min X:  ')
            self.label_max_x = Label(self.record_frame, text='Max X:  ')
            self.label_min_y = Label(self.record_frame, text='Min Y:  ')
            self.label_max_y = Label(self.record_frame, text='Max Y:  ')
            self.label_spacing_x = Label(self.record_frame, text='Spacing X:  ')
            self.label_spacing_y = Label(self.record_frame, text='Spacing Y:  ')
            #place labels in grid
            self.label_min_x.grid(row=0, column=0, padx=10, pady=3)
            self.label_max_x.grid(row=1, column=0, padx=10, pady=3)
            self.label_min_y.grid(row=2, column=0, padx=10, pady=3)
            self.label_max_y.grid(row=3, column=0, padx=10, pady=3)
            self.label_spacing_x.grid(row=4, column=0, padx=10, pady=3)
            self.label_spacing_y.grid(row=5, column=0, padx=10, pady=3)
            #create sliders
            self.box_min_x = Scale(self.record_frame, from_=-50, to=50, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_x = Scale(self.record_frame, from_=-50, to=50, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_min_y = Scale(self.record_frame, from_=121, to=145, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_y = Scale(self.record_frame, from_=121, to=145, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_spacing_x= Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            self.box_spacing_y = Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            #place sliders in grid
            self.box_min_x.grid(row=0, column=1, padx=10, pady=3)
            self.box_max_x.grid(row=1, column=1, padx=10, pady=3)
            self.box_min_y.grid(row=2, column=1, padx=10, pady=3)
            self.box_max_y.grid(row=3, column=1, padx=10, pady=3)
            self.box_spacing_x.grid(row=4, column=1, padx=10, pady=3)
            self.box_spacing_y.grid(row=5, column=1, padx=10, pady=3)
            #set initial values
            self.box_min_x.set(min_x)
            self.box_max_x.set(max_x)
            self.box_min_y.set(min_y)
            self.box_max_y.set(max_y)
            self.box_spacing_x.set(spacing_x)
            self.box_spacing_y.set(spacing_y)
        elif self.mode == "x-z":
            self.label_min_z = Label(self.record_frame, text='Min Z:  ')
            self.label_max_z = Label(self.record_frame, text='Max Z:  ')
            self.label_min_x = Label(self.record_frame, text='Min X:  ')
            self.label_max_x = Label(self.record_frame, text='Max X:  ')
            self.label_spacing_z = Label(self.record_frame, text='Spacing Z:  ')
            self.label_spacing_x = Label(self.record_frame, text='Spacing X:  ')
            #place labels in grid
            self.label_min_z.grid(row=0, column=0, padx=10, pady=3)
            self.label_max_z.grid(row=1, column=0, padx=10, pady=3)
            self.label_min_x.grid(row=2, column=0, padx=10, pady=3)
            self.label_max_x.grid(row=3, column=0, padx=10, pady=3)
            self.label_spacing_z.grid(row=4, column=0, padx=10, pady=3)
            self.label_spacing_x.grid(row=5, column=0, padx=10, pady=3)
            #create sliders
            self.box_min_z = Scale(self.record_frame, from_=-100, to=50, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_z = Scale(self.record_frame, from_=-50, to=50, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_min_x = Scale(self.record_frame, from_=-50, to=50, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_max_x = Scale(self.record_frame, from_=-50, to=50, orient=HORIZONTAL, length=150, resolution=0.1)
            self.box_spacing_z= Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            self.box_spacing_x = Scale(self.record_frame, from_=5, to=50, orient=HORIZONTAL, length=150)
            #place sliders in grid
            self.box_min_z.grid(row=0, column=1, padx=10, pady=3)
            self.box_max_z.grid(row=1, column=1, padx=10, pady=3)
            self.box_min_x.grid(row=2, column=1, padx=10, pady=3)
            self.box_max_x.grid(row=3, column=1, padx=10, pady=3)
            self.box_spacing_z.grid(row=4, column=1, padx=10, pady=3)
            self.box_spacing_x.grid(row=5, column=1, padx=10, pady=3)
            #set initial values
            self.box_min_x.set(min_x)
            self.box_max_x.set(max_x)
            self.box_min_z.set(min_z)
            self.box_max_z.set(max_z)
            self.box_spacing_x.set(spacing_x)
            self.box_spacing_z.set(spacing_z)
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")

        #create and place checkbutton
        self.checkbutton_live = Checkbutton(self.record_frame, text="draw live", onvalue = 1, offvalue = 0, variable=self.checked)
        self.checkbutton_live.select()
        self.checkbutton_live.grid(row=6, column=0, padx=10, pady=3)

        #create and place button for recomended parameter adoption
        self.adoptButton = Button(self.record_frame, text="adopt proposal", command=self.adoptProposal)
        self.adoptButton.grid(row=6, column=1, padx=10, pady=3)
        
        ###################
        # VARIABLES FRAME #
        ###################
        
        #create labels
        self.label_starting_psi = Label(self.variables_frame, text='PSI:  ')
        self.label_starting_phi = Label(self.variables_frame, text='PSI:  ')
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
        self.box_starting_phi = Scale(self.variables_frame, from_=-4.4, to=4.4, orient=HORIZONTAL, length=150, resolution=0.1)
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
        self.checkbutton_offset = Checkbutton(self.variables_frame, text="use offset", command=self.offsetMode, onvalue = 1, offvalue = 0, variable=self.offset_bool)
        self.checkbutton_offset.select()
        self.checkbutton_offset.grid(row=6, column=0, padx=10, pady=3)

        #create and place button for recomended parameter adoption
        self.adoptButton = Button(self.variables_frame, text="adopt current guess", command=self.adoptCurrentGuess)
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
        
        if self.mode=="x-y":
            self.resultsCenterPhiLabel.config(text='Center X:    ')
            self.resultsCenterPsiLabel.config(text='Center Y:    ')
            self.resultsSigmaPhiLabel.config(text='Sigma X:    ')
            self.resultsSigmaPsiLabel.config(text='Sigma Y:    ')
        
        if self.mode=="x-z":
            self.resultsCenterPhiLabel.config(text='Center X:    ')
            self.resultsCenterPsiLabel.config(text='Center Z:    ')
            self.resultsSigmaPhiLabel.config(text='Sigma X:    ')
            self.resultsSigmaPsiLabel.config(text='Sigma Z:    ')
        
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
        
        #DO MAGIC button
        self.do_magic_button = Button(self.control_frame, text="Do Magic", width=31, pady=3, padx=3)
        self.do_magic_button.grid(row=5, column=1)
        self.do_magic_button["command"]= self.crazyBatch
  
    def replotRates(self):
        #update the other parameters
        
        self.camZLabel["text"]='Camera Z: {0:4.1f}'.format(self.camera_z)
        self.camXLabel["text"] ='Camera X: {0:4.1f}'.format(self.camera_x)
        self.mirZLabel["text"] ='Mirror Z: {0:4.1f}'.format(self.mirror_z)
        self.mirHLabel["text"] ='Mirror Height: {0:4.1f}'.format(self.mirror_height)
        self.mirPhiLabel["text"] ='Mirror PSI: {0:4.1f}'.format(self.psi)
        self.mirPsiLabel["text"] ='Mirror PHI: {0:4.1f}'.format(self.phi)
        self.offsetLabel["text"] ='Offset: {0:4.1f}'.format(geo.get_path_length_delta(self.phi, self.psi, self.mirror_height, self.mirror_z, self.camera_z, self.camera_x))
        
        #make a nice plot
        if self.figure==None:
            self.figure=plt.Figure(figsize=(6,6))
        else:
            self.figure.clf()
        self.subplot = self.figure.add_subplot(111)
        self.subplot.set_title("Heatmap of the mirror positions")
        if self.mode=="psi-phi":
            self.subplot.imshow(self.rates, cmap='cool', extent=( self.min_phi-(self.max_phi-self.min_phi)/(self.spacing_phi)/2, self.max_phi+(self.max_phi-self.min_phi)/(self.spacing_phi)/2, self.min_psi-(self.max_psi-self.min_psi)/(self.spacing_psi)/2, self.max_psi+(self.max_psi-self.min_psi)/(self.spacing_psi)/2))
            self.subplot.set_xlabel("$\phi$ [°]")
            self.subplot.set_ylabel("$\psi$ [°]")
        elif self.mode=="x-y":
            self.subplot.imshow(self.rates, cmap='cool', extent=( self.min_x-(self.max_x-self.min_x)/(self.spacing_x)/2, self.max_x+(self.max_x-self.min_x)/(self.spacing_x)/2, self.min_y-(self.max_y-self.min_y)/(self.spacing_y)/2, self.max_y+(self.max_y-self.min_y)/(self.spacing_y)/2))
            self.subplot.set_xlabel("X [mm]")
            self.subplot.set_ylabel("Y [mm]")
        elif self.mode=="x-z":
            self.subplot.imshow(self.rates, cmap='cool', extent=( self.max_z+(self.max_z-self.min_z)/(self.spacing_z)/2, self.min_z-(self.max_z-self.min_z)/(self.spacing_z)/2, self.min_x-(self.max_x-self.min_x)/(self.spacing_x)/2, self.max_x+(self.max_x-self.min_x)/(self.spacing_x)/2))
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
            if self.mode=="psi-phi":
                t1 = threading.Thread(target= lambda arg_min_phi=self.box_min_phi.get(), arg_max_phi=self.box_max_phi.get(), arg_min_psi=self.box_min_psi.get(), arg_max_psi=self.box_max_psi.get(), arg_spacing_phi=self.box_spacing_phi.get(), arg_spacing_psi=self.box_spacing_psi.get() : self.recordRateDistribution(spacing_phi=arg_spacing_phi, spacing_psi=arg_spacing_psi, min_phi=arg_min_phi, max_phi=arg_max_phi, min_psi=arg_min_psi, max_psi=arg_max_psi))
            elif self.mode=="x-y":
                t1 = threading.Thread(target= lambda arg_min_x=self.box_min_x.get(), arg_max_x=self.box_max_x.get(), arg_min_y=self.box_min_y.get(), arg_max_y=self.box_max_y.get(), arg_spacing_x=self.box_spacing_x.get(), arg_spacing_y=self.box_spacing_y.get() : self.recordRateDistribution(spacing_phi=arg_spacing_x, spacing_psi=arg_spacing_y, min_phi=arg_min_x, max_phi=arg_max_x, min_psi=arg_min_y, max_psi=arg_max_y))
            elif self.mode=="x-z":
                t1 = threading.Thread(target= lambda arg_min_x=self.box_min_x.get(), arg_max_x=self.box_max_x.get(), arg_min_z=self.box_min_z.get(), arg_max_z=self.box_max_z.get(), arg_spacing_x=self.box_spacing_x.get(), arg_spacing_z=self.box_spacing_z.get() : self.recordRateDistribution(spacing_phi=arg_spacing_x, spacing_psi=arg_spacing_z, min_phi=arg_min_x, max_phi=arg_max_x, min_psi=arg_min_z, max_psi=arg_max_z))
            else:
                raise RuntimeError("The measuring mode needs to be definied correctly!")  
            t1.start()
            self.replotRatesUpdate()
        else:
            print("Result will be plotted after everything is measured!")
            self.recordRateDistribution(self.box_spacing_phi.get(), self.box_spacing_psi.get(), self.box_min_phi.get(), self.box_max_phi.get(), self.box_min_psi.get(), self.box_max_psi.get())
            self.replotRates()
            
         
    def recordRateDistribution(self, spacing_phi=25, spacing_psi=26, min_phi=-2., max_phi=2, min_psi=-3.80, max_psi=-0.5):
        self.resetRectangle()
        if self.client==None:
            print("No client connected! Cannot plot Mirrors")
            self.still_recording=False
            return
        self.controller.setBussy(True)
        sleep(0.02)
        if self.mode=="psi-phi":
            print("Starting to measure the rate distribution. MinPhi={0:4.2f} ; MaxPhi={1:4.2f} ; MinPsi={2:4.2f} ; MaxPsi={3:4.2f} ; SpacingPhi={4} ; SpacingPsi={5}".format(min_phi, max_phi, min_psi, max_psi, spacing_phi, spacing_psi))
            #coordinates_phi=np.linspace(min_phi, max_phi, num=spacing_phi)
            #coordinates_psi=np.linspace(min_psi, max_psi, num=spacing_psi)
            #x, y=np.meshgrid(coordinates_phi, coordinates_psi)
            rates=np.zeros(shape=(spacing_phi, spacing_psi))
            self.rates=np.transpose(rates)
            self.spacing_psi=spacing_psi
            self.spacing_phi=spacing_phi
            self.min_psi=min_psi
            self.max_psi=max_psi
            self.min_phi=min_phi
            self.max_phi=max_phi
            #move psi and phi simultaneously into the starting position
            self.controller.set_position_mirror_phi(min_phi)
            self.controller.set_position_mirror_psi(min_psi)
            moving_both=True
            try:
                moving_both=self.controller.get_mirror_phi_moving() or self.controller.get_mirror_psi_moving() 
            except TrinamicException:
                print("Trinamic Exception while waiting for PHI and PSI to stop moving")
            except:
                print("Non-Trinamic Exception while waiting for PHI and PSI to stop moving")

            while moving_both:
                sleep(0.05)
                try:
                    moving_both=self.controller.get_mirror_phi_moving() or self.controller.get_mirror_psi_moving() 
                except TrinamicException:
                    print("Trinamic Exception while waiting for PHI and PSI to stop moving")
                except:
                    print("Non-Trinamic Exception while waiting for PHI and PSI to stop moving")
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
        elif self.mode=="x-y":
            zeros=geo.get_zero_parameters()
            spacing_x=spacing_phi
            spacing_y=spacing_psi
            min_x=min_phi
            max_x=max_phi
            min_y=min_psi
            max_y=max_psi
            rates=np.zeros(shape=(spacing_y, spacing_x))
            #change the global parameters so the plot can be redrawn correctly
            self.spacing_x=spacing_x
            self.spacing_y=spacing_y
            self.min_x=min_x
            self.max_x=max_x
            self.min_y=min_y
            self.max_y=max_y
            #move x and y simultaneously into the starting position
            self.controller.set_position_camera_x(min_x)
            self.controller.set_position_mirror_height(min_y)
            #while seting camera z to the correct position (also accounting for offset on pathlenght)
            #print("PHI={0} ; PSI={1} ; Height={2} ; Mirr_Z={3} ; Offset={4}".format(self.phi, self.psi, min_y, self.mirror_z, self.offset_pathlength))
            new_cam_z=geo.get_camera_z_position_offset(self.phi, self.psi, min_y, self.mirror_z, offset_pathlength=self.offset_pathlength, debug=False)
            if new_cam_z<=max_y-min_y:
                raise RuntimeError("The calulated Camera z is smaller than the y-range that is to be surpassed ({0}<={1}). Is the mirror too close to the camera?".format(new_cam_z, max_y-min_y))
            self.controller.set_position_camera_z(new_cam_z)
            #self.controller.set_position_mirror_z(zeros[1]-min_y) #SKETCHY! ONLY TRUE FOR INCIDENCE ANGLE = 0
            moving_all=True
            try:
                moving_all=self.controller.get_camera_x_moving() or self.controller.get_mirror_height_moving() or self.controller.get_camera_z_moving()
            except TrinamicException:
                print("Trinamic Exception while waiting for camera X and mirror height to stop moving")
            except:
                print("Non-Trinamic Exception while waiting for camera X and mirror height to stop moving")
            while moving_all:
                try:
                    moving_all=self.controller.get_camera_x_moving() or self.controller.get_mirror_height_moving() or self.controller.get_camera_z_moving()
                except TrinamicException:
                    print("Trinamic Exception while waiting for camera X, camera Z, mirror Z and mirror height to stop moving")
                except:
                    print("Non-Trinamic Exception while waiting for camera X, camera Z, mirror Z and mirror height to stop moving")
            print("Succesfully set all Motors to correct starting positions. Now start Scan!")
            #walk through the whole space of different positions
            #the lesser shifted dimension should be Y, as one needs to move two motors (mirror height, mirror z) to correctly adjust this
            for i in range(0, spacing_y, 1):
                #calculate the position
                pos_y=min_y+(max_y-min_y)/(spacing_y-1)*i
                #move the mirror height accordingly
                self.controller.set_position_mirror_height(pos_y)
                #adjust mirror z so that the pathlength is adjusted for // CURRENTLY ONLY TRUE IF THE INCIDENT ANGLE IS 0!
                self.controller.set_position_camera_z(self.controller.get_position_camera_z()-(max_y-min_y)/(spacing_y-1))
                moving_y=True
                try:
                    moving_y=self.controller.get_camera_z_moving() or self.controller.get_mirror_height_moving()
                except TrinamicException:
                    print("Trinamic Exception while waiting for camera Z and Mirror Height to stop moving")
                except:
                    print("Non-Trinamic Exception while waiting for camera Z and Mirror Height to stop moving")
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
        elif self.mode=="x-z":
            zeros=geo.get_zero_parameters()
            spacing_x=spacing_psi
            spacing_y=spacing_phi
            #attention! This is only correct if the setup is mounted perfectly! Needs to be adjusted when the mirror arrives and optimal spot is found
            min_x=min_psi+geo.z_len/2+70
            max_x=max_psi+geo.z_len/2+70
            min_y=min_phi
            max_y=max_phi
            rates=np.zeros(shape=(spacing_y, spacing_x))
            #change the global parameters so the plot can be redrawn correctly
            self.spacing_x=spacing_x
            self.spacing_y=spacing_y
            self.min_x=min_y
            self.max_x=max_y
            self.min_z=min_x
            self.max_z=max_x
            #move mirror and camera simultaneously into the starting position
            #mirror height and offset stay the same as  set before the start of the measurement
            self.controller.set_position_mirror_z(min_x)
            self.controller.set_position_camera_x(min_y)
            #while seting camera z to the correct position (also accounting for offset on pathlenght)
            #print("PHI={0} ; PSI={1} ; Height={2} ; Mirr_Z={3} ; Offset={4}".format(self.phi, self.psi, min_y, self.mirror_z, self.offset_pathlength))
            new_cam_z=geo.get_camera_z_position_offset(self.phi, self.psi, self.mirror_height, min_x, offset_pathlength=self.offset_pathlength, debug=False)
            if new_cam_z<=0:
                raise RuntimeError("The calulated Camera z is smaller than the allowed range of the camera z ({0}<=0).".format(new_cam_z))
            self.controller.set_position_camera_z(new_cam_z)
            moving_all=True
            try:
                moving_all=self.controller.get_camera_x_moving() or self.controller.get_mirror_z_moving() or self.controller.get_camera_z_moving()
            except TrinamicException:
                print("Trinamic Exception while waiting for camera and mirror to stop moving")
            except:
                print("Non-Trinamic Exception while waiting for camera and mirror to stop moving")
            while moving_all:
                try:
                    moving_all=self.controller.get_camera_x_moving() or self.controller.get_mirror_z_moving() or self.controller.get_camera_z_moving()
                except TrinamicException:
                    print("Trinamic Exception while waiting for camera X, camera Z, mirror Z to stop moving")
                except:
                    print("Non-Trinamic Exception while waiting for camera X, camera Z, mirror Z to stop moving")
            print("Succesfully set all Motors to correct starting positions. Now start Scan!")
            #walk through the whole space of different positions
            #the lesser shifted dimension should be X (actual coordinates Z), as one needs to move two motors (mirror Z, camera Z) to correctly adjust this
            #now also move X
            for j in range(0, spacing_x, 1):
                #calculate the correct x-position (real coord Z) of the mirror
                pos_x=min_x+(max_x-min_x)/(spacing_x-1)*j
                self.controller.set_position_mirror_z(pos_x)
                #also move the camera z along
                self.controller.set_position_camera_z(new_cam_z+(max_x-min_x)/(spacing_x-1)*j)
                moving_x=True
                while moving_x:
                    sleep(0.05)
                    try:
                        moving_x=self.controller.get_camera_z_moving() or self.controller.get_mirror_z_moving()
                    except TrinamicException:
                        print("Trinamic Exception while waiting for camera Z and mirror Z to stop moving")
                    except:
                        print("Non-Trinamic Exception while waiting for camera Z and mirror Z to stop moving")
                for i in range(0, spacing_y, 1):
                    #calculate the position
                    if j%2==0:
                        pos_y=min_y+(max_y-min_y)/(spacing_y-1)*i
                    else:
                        pos_y=max_y-(max_y-min_y)/(spacing_y-1)*i
                    self.controller.set_position_camera_x(pos_y)
                    moving_y=True
                    while moving_y:
                        sleep(0.05)
                        try:
                            moving_y=self.controller.get_camera_x_moving()
                        except TrinamicException:
                            print("Trinamic Exception while waiting for camera Z to stop moving")
                        except:
                            print("Non-Trinamic Exception while waiting for camera Z to stop moving")
                        if j%2==0:
                            rates[spacing_y-i-1][j]=self.client.getRateA()+self.client.getRateB()
                        else:
                            rates[i][j]=self.client.getRateA()+self.client.getRateB()
                        self.rates=rates
                        self.new_record=True
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")
        sleep(0.1)
        self.still_recording=False
        self.controller.setBussy(False)
        # coordinates_phi=np.linspace(min_phi, max_phi, num=spacing_phi)
        #coordinates_psi=np.linspace(min_psi, max_psi, num=spacing_psi)
        #x, y=np.meshgrid(coordinates_phi, coordinates_psi)
        print("Recording of the rate distribution done!")
        
    def fitGaussian(self):
        #if not done yet: find the rectangle to get some startingvalues
        if self.min_psi_rect == None or self.max_psi_rect == None or self.min_phi_rect == None or self.max_phi_rect == None:
            self.findRectangle()
        if self.mode=="psi-phi":
            #calculate starting values for the gaussian
            center_phi=(self.min_phi_rect+self.max_phi_rect)/2
            center_psi=(self.min_psi_rect+self.max_psi_rect)/2
            sigma_phi=np.abs(self.min_phi_rect-self.max_phi_rect)/2
            sigma_psi=np.abs(self.min_psi_rect-self.max_psi_rect)/2
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
            center_phi=(self.min_phi_rect+self.max_phi_rect)/2
            center_psi=(self.min_psi_rect+self.max_psi_rect)/2
            sigma_phi=np.abs(self.min_phi_rect-self.max_phi_rect)/2
            sigma_psi=np.abs(self.min_psi_rect-self.max_psi_rect)/2
            offset=0
            prefactor=np.max(self.rates)
            p0=(prefactor, center_phi, sigma_phi, center_psi, sigma_psi, offset)
            print("Starting gaussian fit: p0:   center_x = {0:5f} ; center_y = {1:5f} ; sigma_x = {2:5f} ; sigma_y = {3:5f} ; offset = {4:5f} ; prefactor = {5:5f}".format(p0[1],p0[3], p0[2], p0[4], p0[5], p0[0]))
            
            #do the fit
            with warnings.catch_warnings(record=True) as w:
                coordinates_phi=np.linspace(self.min_x, self.max_x, num=int(self.spacing_x))
                coordinates_psi=np.linspace(self.min_y, self.max_y, num=int(self.spacing_y))
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
                    self.subplot.axes.contour(x, y, data_fitted.reshape(self.spacing_y, self.spacing_x), 8, colors='b', label="Gaussian Fit")
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
            center_phi=(self.min_phi_rect+self.max_phi_rect)/2
            center_psi=(self.min_psi_rect+self.max_psi_rect)/2
            sigma_phi=np.abs(self.min_phi_rect-self.max_phi_rect)/2
            sigma_psi=np.abs(self.min_psi_rect-self.max_psi_rect)/2
            offset=0
            prefactor=np.max(self.rates)
            p0=(prefactor, center_phi, sigma_phi, center_psi, sigma_psi, offset)
            print("Starting gaussian fit: p0:   center_z = {0:5f} ; center_x = {1:5f} ; sigma_z = {2:5f} ; sigma_x = {3:5f} ; offset = {4:5f} ; prefactor = {5:5f}".format(p0[1],p0[3], p0[2], p0[4], p0[5], p0[0]))
            
            #do the fit
            with warnings.catch_warnings(record=True) as w:
                coordinates_phi=np.linspace(self.min_y, self.max_y, num=int(self.spacing_x))
                coordinates_psi=np.linspace(self.min_z, self.max_z, num=int(self.spacing_z))
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
                    self.subplot.axes.contour(x, y, data_fitted.reshape(self.spacing_y, self.spacing_x), 8, colors='b', label="Gaussian Fit")
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
        if self.rates == None:
            raise RuntimeError("The area of interest can't be found if there are no rates! Please load or record a rate file")
        rates=self.rates
        if self.mode=="psi-phi":
            coordinates_phi=np.linspace(self.min_phi, self.max_phi, num=int(self.spacing_phi))
            coordinates_psi=np.linspace(self.min_psi, self.max_psi, num=int(self.spacing_psi))
        elif self.mode=="x-y":
            coordinates_phi=np.linspace(self.min_x, self.max_x, num=int(self.spacing_x))
            coordinates_psi=np.linspace(self.min_y, self.max_y, num=int(self.spacing_y))
        elif self.mode=="x-z":
            coordinates_phi=np.linspace(self.min_x, self.max_x, num=int(self.spacing_x))
            coordinates_psi=np.linspace(self.min_z, self.max_z, num=int(self.spacing_y))
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")  
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
        self.min_phi_rect=rect_start_phi
        self.max_phi_rect=rect_start_phi+rect_width_phi
        self.min_psi_rect=rect_start_psi+rect_width_psi
        self.max_psi_rect=rect_start_psi
        
    #######################################
    #  FILE FORMAT FOR THE .ratepp FILES  #
    # [00] Min Phi                        #
    # [01] Max Phi                        #
    # [02] Min Psi                        #
    # [03] Max Psi                        #
    # [04] Spacing Phi                    #
    # [05] Spacing Psi                    #
    # [06] Camera Z                       #
    # [07] Camera X                       #
    # [08] Mirror Z                       #
    # [09] Mirror Height                  #
    # [10] actual Rates                   #
    #######################################
    
    #######################################
    #  FILE FORMAT FOR THE .ratexy FILES  #
    # [00] Min X                          #
    # [01] Max X                          #
    # [02] Min Y                          #
    # [03] Max Y                          #
    # [04] Spacing X                      #
    # [05] Spacing Y                      #
    # [06] PHI                            #
    # [07] PSI                            #
    # [08] offset pathlength              #
    # [09] mirror z                       #
    # [10] actual Rates                   #
    #######################################
    
    #######################################
    #  FILE FORMAT FOR THE .ratexz FILES  #
    # [00] Min X                          #
    # [01] Max X                          #
    # [02] Min Z                          #
    # [03] Max Z                          #
    # [04] Spacing X                      #
    # [05] Spacing Z                      #
    # [06] PHI                            #
    # [07] PSI                            #
    # [08] offset pathlength              #
    # [09] mirror height                  #
    # [10] actual Rates                   #
    #######################################
    
    
    def loadRates(self):
        if self.mode=="psi-phi": 
            file = filedialog.askopenfile(parent=self.window, initialdir = "../../..", title = "Load Rate Distribution", filetypes = (("PSI-PHI rate files","*.ratepp"),("PSI-PHI rate files old","*.rate"),("all files","*.*")))
        elif self.mode=="x-y":
            file = filedialog.askopenfile(parent=self.window, initialdir = "../../..", title = "Load Rate Distribution", filetypes = (("X-Y rate files", ".ratexy"),("X-Y rate files old","*.ratel"),("all files","*.*")))
        elif self.mode=="x-z":
            file = filedialog.askopenfile(parent=self.window, initialdir = "../../..", title = "Load Rate Distribution", filetypes = (("X-Y rate files","*.ratexz"),("all files","*.*")))
        else:
            raise RuntimeError("The measuring mode needs to be definied correctly!")  
        if file!=None:
            string=file.read()
            parts=string.split("~")
            if self.mode=="psi-phi":
                if ".rate" not in file.name and ".ratepp" not in file.name:
                    raise RuntimeError("Cannot open this file! The fileformat is not correct. Maybe the Rate Analyzer needs to be in another mode?")
                self.min_phi=float(parts[0])
                self.max_phi=float(parts[1])
                self.min_psi=float(parts[2])
                self.max_psi=float(parts[3])
                self.spacing_psi=int(parts[4])
                self.spacing_phi=int(parts[5])
                if len(parts)==7:
                    self.camera_z=np.nan
                    self.camera_x=np.nan
                    self.mirror_z=np.nan
                    self.mirror_height=np.nan
                    array_data=parts[6]
                else:
                    self.camera_z=float(parts[6])
                    self.camera_x=float(parts[7])
                    self.mirror_z=float(parts[8])
                    self.mirror_height=float(parts[9])
                    array_data=parts[10]
                lines=array_data.splitlines()
                rates=np.empty((self.spacing_psi, self.spacing_phi))
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
                self.min_x=float(parts[0])
                self.max_x=float(parts[1])
                self.min_y=float(parts[2])
                self.max_y=float(parts[3])
                self.spacing_x=int(parts[4])
                self.spacing_y=int(parts[5])
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
                rates=np.empty((self.spacing_y, self.spacing_x))
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
                self.min_x=float(parts[0])
                self.max_x=float(parts[1])
                self.min_z=float(parts[2])
                self.max_z=float(parts[3])
                self.spacing_x=int(parts[4])
                self.spacing_z=int(parts[5])
                self.psi=float(parts[6])
                self.phi=float(parts[7])
                self.offset_pathlengtht=float(parts[8])
                self.mirror_height=float(parts[9])
                array_data=parts[10]
                lines=array_data.splitlines()
                rates=np.empty((self.spacing_x, self.spacing_z))
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
                file = filedialog.asksaveasfile(parent=self.window, initialdir = "../../..", title = "Save Rate Distribution", filetypes = (("PSI-PHI rate files","*.ratepp"),("all files","*.*")))
            elif self.mode=="x-y":
                file = filedialog.asksaveasfile(parent=self.window, initialdir = "../../..", title = "Save Rate Distribution", filetypes = (("X-Y rate files","*.ratexy"),("all files","*.*")))
            elif self.mode=="x-z":
                file = filedialog.asksaveasfile(parent=self.window, initialdir = "../../..", title = "Save Rate Distribution", filetypes = (("X-Z rate files","*.ratexz"),("all files","*.*")))
            else:
                raise RuntimeError("The measuring mode needs to be definied correctly!") 
        else:
            file = open(path, "w")
        if file!=None:
            #file=open(filename, "w")
            if self.mode=="psi-phi":
                file.write("{0}~{1}~{2}~{3}~{4}~{5}~{6}~{7}~{8}~{9}~{10}".format(self.min_phi, self.max_phi, self.min_psi, self.max_psi, self.spacing_psi, self.spacing_phi, self.camera_z, self.camera_x, self.mirror_z, self.mirror_height, np.array2string(self.rates, threshold=10e9)).replace("\n ", "").replace("]", "]\n").replace("]\n]", "]]"))
            elif self.mode=="x-y":
                file.write("{0}~{1}~{2}~{3}~{4}~{5}~{6}~{7}~{8}~{9}~{10}".format(self.min_x, self.max_x, self.min_y, self.max_y, self.spacing_x, self.spacing_y, self.phi, self.psi, self.offset_pathlength, self.mirror_z, np.array2string(self.rates, threshold=10e9)).replace("\n ", "").replace("]", "]\n").replace("]\n]", "]]"))
            elif self.mode=="x-z":
                file.write("{0}~{1}~{2}~{3}~{4}~{5}~{6}~{7}~{8}~{9}~{10}".format(self.min_x, self.max_x, self.min_z, self.max_z, self.spacing_x, self.spacing_z, self.phi, self.psi, self.offset_pathlength, self.mirror_height, np.array2string(self.rates, threshold=10e9)).replace("\n ", "").replace("]", "]\n").replace("]\n]", "]]"))
            else:
                raise RuntimeError("The measuring mode needs to be definied correctly!")    
            file.close()
            
    def offsetMode(self):
        if self.offset_bool.get() == 1:
            self.label_starting_cam_z.config(text="Offset:")
            self.box_starting_cam_z.config(from_=-10, to=10)
        elif self.offset_bool.get() == 0:
            self.label_starting_cam_z.config(text="Camera Z:")
            self.box_starting_cam_z.config(from_=0, to=139)
        print("Toggled mode")
        
    #THIS SHOULD ACTUALLY GET IT INFORMATION FROM THE GEOMETRY PACKAGE!
    def adoptCurrentGuess(self):
        cam_x, cam_z, phi, psi, mir_z, mir_y = 0,0,0,0,0,0  # geo.get_optimal_parameters_current_guess()
        self.box_starting_cam_x.set(cam_x)
        self.box_starting_cam_z.set(cam_z)
        self.box_starting_phi.set(phi)
        self.box_starting_psi.set(psi)
        self.box_starting_mir_z.set(mir_z)
        self.box_starting_mir_y.set(mir_y)
            
    def adoptProposal(self):
        #set the sliders to the borders of the rectangle
        self.box_min_phi.set(self.min_phi_rect)
        self.box_max_phi.set(self.max_phi_rect)
        self.box_min_psi.set(self.min_psi_rect)
        self.box_max_psi.set(self.max_psi_rect)
        
        #do some more complex approximations for the spacing
        spacing_psi=-1
        spacing_phi=-1
        psi_active=None
        if (self.max_phi_rect-self.min_phi_rect)>(self.max_psi_rect-self.min_psi_rect):
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
            spacing_phi=(self.max_phi_rect-self.min_phi_rect)/(self.max_psi_rect-self.min_psi_rect)*spacing_psi
        else:
            #calculate the correct psi for about square pixels
            spacing_psi=(self.max_psi_rect-self.min_psi_rect)/(self.max_phi_rect-self.min_phi_rect)*spacing_phi
        #set sliders for the spacing
        self.box_spacing_phi.set(spacing_phi)
        self.box_spacing_psi.set(spacing_psi)
        
    def resetRectangle(self):
        min_psi_rect=None
        max_psi_rect=None
        min_phi_rect=None
        max_phi_rect=None
        
    def updateResults(self, results):
        self.resultsCenterPhiLabel['text']='Center PHI: {0:3.2f}'.format(results[1])
        self.resultsCenterPsiLabel['text']='Center PSI: {0:3.2f}'.format(results[3])
        self.resultsSigmaPhiLabel['text']='Sigma PHI:  {0:3.2f}'.format(results[2])
        self.resultsSigmaPsiLabel['text']='Sigma PSI:  {0:3.2f}'.format(results[4])
        self.resultsOffsetLabel['text']='Offset:     {0:3.2f}'.format(results[5])
        self.resultsPrefactorPhiLabel['text']='Prefactor:  {0:3.2f}'.format(results[0])
        
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
        #	     [3] position_mirror_height   // mirror Z                                      #
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
                    self.box_min_x.set(m[4])
                    self.box_max_x.set(m[5])
                    self.box_min_y.set(m[6])
                    self.box_max_y.set(m[7])
                    self.box_spacing_x.set(m[8])
                    self.box_spacing_y.set(m[9])
                    
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
                    self.mirror_height=m[3]
                    self.controller.set_position_camera_z(self.camera_z, verbose=True)
                    self.controller.set_position_camera_x(self.camera_x, verbose=True)
                    self.controller.set_position_mirror_z(self.mirror_z, verbose=True)
                    self.controller.set_position_mirror_height(self.mirror_height, verbose=True)
                    
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
                        self.mirror_height=self.controller.get_position_mirror_height()
                    except TrinamicException:
                        try:
                            self.camera_z=self.controller.get_position_camera_z()
                            self.camera_x=self.controller.get_position_camera_x()
                            self.mirror_z=self.controller.get_position_mirror_z()
                            self.mirror_height=self.controller.get_position_mirror_height()
                        except TrinamicException:
                            print("Tried twice to get the Positions but failed both times (Trinamic Exception)! Instead take the ones that were initally set!")
                            self.camera_z=m[0]
                            self.camera_x=m[1]
                            self.mirror_z=m[2]
                            self.mirror_height=m[3]
                        except:
                            print("Tried twice to get the Positions but failed both times (But notTrinamic Exception)! Instead take the ones that were initally set!")
                            self.camera_z=m[0]
                            self.camera_x=m[1]
                            self.mirror_z=m[2]
                            self.mirror_height=m[3]
                    except:
                        print("Tried to get the Positions but failed both times (No Trinamic Exception)! Instead take the ones that were initally set!")
                        self.camera_z=m[0]
                        self.camera_x=m[1]
                        self.mirror_z=m[2]
                        self.mirror_height=m[3]

            
                    #measure the rate distribution
                    #set the sliders to the borders of the rectangle
                    self.box_min_phi.set(m[4])
                    self.box_max_phi.set(m[5])
                    self.box_min_psi.set(m[6])
                    self.box_max_psi.set(m[7])
                    self.box_spacing_phi.set(m[8])
                    self.box_spacing_psi.set(m[9])
                    
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
