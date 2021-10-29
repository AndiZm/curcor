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


import numpy as np #only needed for simulations
from PIL import Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.patches as patches

#updating=False


class RATE_ANALYZER():
    
    client=None
    controller=None
    change_mirror_psi=False
    change_mirror_phi=False
    
    #currently loaded distribution
    rates=None
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
    file_frame=None
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
    checkbutton_live=None
    adoptButton=None 
    box_min_phi=None
    box_max_phi=None
    box_min_psi=None
    box_max_psi=None
    box_spacing_phi=None
    box_spacing_psi=None
    checked=None
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
        
        #get positions of the controller
        self.controller.setBussy(True)
        sleep(0.1)
        self.camera_z=controller.get_position_camera_z()
        self.camera_x=controller.get_position_camera_x()
        self.mirror_z=controller.get_position_mirror_z()
        self.mirror_height=controller.get_position_mirror_height()
        self.controller.setBussy(False)
        
        #create new window and frames
        self.window = Toplevel(master)
        self.main_frame = Frame(self.window, width=840, height = 700)
        self.main_frame.grid(row=0, column=0)
        self.main_frame.config(background = "#003366")
        self.plot_frame = Frame(self.main_frame, width=600, height=600)
        self.plot_frame.grid(row=0, column=0, padx=10,pady=10)
        self.plot_frame.config(background = "#003366")
        self.positions_frame = Frame(self.main_frame, width=600, height=100)
        self.positions_frame.grid(row=1, column=0, padx=10,pady=2)
        self.positions_frame.config(background = "#DBDBDB")
        self.control_frame = Frame(self.main_frame, width=320, height=600)
        self.control_frame.grid(row=0, column=1)
        self.control_frame.config(background = "#003366")
        self.file_frame = Frame(self.control_frame, width=300, height=100)
        self.file_frame.grid(row=0, column=0, padx=10,pady=10)
        self.file_frame.config(background = "#003366")
        self.record_frame = Frame(self.control_frame, width=300, height=200)
        self.record_frame.grid(row=1, column=0, padx=10, pady=10)
        self.record_frame.config(background = "#DBDBDB")
        self.fit_frame = Frame(self.control_frame, width=300, height=200)
        self.fit_frame.grid(row=3, column=0, padx=10, pady=10)
        self.fit_frame.config(background = "#003366")
        self.results_frame = Frame(self.fit_frame, width=290, height=120)
        self.results_frame.grid(row=3, column=0, padx=10, pady=10)
        self.results_frame.config(background = "#DBDBDB")
        
        self.checked=IntVar()
        
        ##############
        # PLOT FRAME #
        ##############
        
        #create the plot
        self.figure=plt.Figure(figsize=(6,6))
        self.subplot = self.figure.add_subplot(111)
        self.subplot.set_title("Heatmap of the mirror Positions")
        self.subplot.set_xlabel("$\phi$ [°]")
        self.subplot.set_ylabel("$\psi$ [°]")
        self.subplot.set_xlim((self.min_phi, self.max_phi))
        self.subplot.set_ylim((self.min_psi, self.max_psi))
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.canvas.draw()
        
        
        ###################
        # POSITIONS FRAME #
        ###################
        
        #create labels
        self.camZLabel = Label(self.positions_frame, pady=10, text='Camera Z: {0:4.1f}'.format(self.camera_z), width="15")
        self.camXLabel = Label(self.positions_frame, pady=10, text='Camera X: {0:4.1f}'.format(self.camera_x), width="15")
        self.mirZLabel = Label(self.positions_frame, pady=10, text='Mirror Z: {0:4.1f}'.format(self.mirror_z), width="15")
        self.mirHLabel = Label(self.positions_frame, pady=10, text='Mirror Height: {0:4.1f}'.format(self.mirror_height), width="20")
        
        #place labels
        self.camZLabel.grid(row=0, column=0)
        self.camXLabel.grid(row=0, column=1)
        self.mirZLabel.grid(row=0, column=2)
        self.mirHLabel.grid(row=0, column=3)
        
        ##############
        # FILE FRAME #
        ##############
        
        #add GUI elements
        self.loadButton = Button(self.file_frame, text="Load Rate Distribution", width=31, pady=3, padx=3, command=self.loadRates)
        self.loadButton.grid(row=0,column=0)
        self.saveButton = Button(self.file_frame, text="Save Rate Distribution", width=31, pady=3, padx=3, command=self.saveRates)
        self.saveButton.grid(row=1,column=0)


        ################
        # RECORD FRAME #
        ################

        #add record elements
        min_phi=-4.4
        max_phi=4.4
        min_psi=-4.4
        max_psi=4.4
        spacing_phi=10
        spacing_psi=11
        
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

        #create and place checkbutton
        self.checkbutton_live = Checkbutton(self.record_frame, text="draw live", onvalue = 1, offvalue = 0, variable=self.checked)
        self.checkbutton_live.select()
        self.checkbutton_live.grid(row=6, column=0, padx=10, pady=3)

        #create and place button for recomended parameter adoption
        self.adoptButton = Button(self.record_frame, text="adopt proposal", command=self.adoptProposal)
        self.adoptButton.grid(row=6, column=1, padx=10, pady=3)
        
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
        
        #create labels
        self.resultsHeadLabel = Label(self.results_frame, text='RESULTS:', width="15")
        self.resultsCenterPhiLabel  = Label(self.results_frame, text='Center PHI:  ', width="15")
        self.resultsCenterPsiLabel = Label(self.results_frame, text='Center PSI:  ', width="15")
        self.resultsSigmaPhiLabel = Label(self.results_frame, text='Sigma PHI:  ', width="15")
        self.resultsSigmaPsiLabel = Label(self.results_frame, text='Sigma PSI:  ', width="15")
        self.resultsOffsetLabel = Label(self.results_frame, text='Offset:  ', width="15")
        self.resultsPrefactorPhiLabel = Label(self.results_frame, text='Prefactor:  ', width="15")
        
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
        self.crazyBatchButton.grid(row=5)
        self.crazyBatchButton["command"]= self.crazyBatch
  
    def replotRates(self):
        #update the other parameters
        
        self.camZLabel["text"]='Camera Z: {0:4.1f}'.format(self.camera_z)
        self.camXLabel["text"] ='Camera X: {0:4.1f}'.format(self.camera_x)
        self.mirZLabel["text"] ='Mirror Z: {0:4.1f}'.format(self.mirror_z)
        self.mirHLabel["text"] ='Mirror Height: {0:4.1f}'.format(self.mirror_height)
        #make a nice plot
        if self.figure==None:
            self.figure=plt.Figure(figsize=(6,6))
        else:
            self.figure.clf()
        self.subplot = self.figure.add_subplot(111)
        self.subplot.set_title("Heatmap of the mirror positions")
        self.subplot.imshow(self.rates, cmap='cool', extent=( self.min_phi-(self.max_phi-self.min_phi)/(self.spacing_phi)/2, self.max_phi+(self.max_phi-self.min_phi)/(self.spacing_phi)/2, self.min_psi-(self.max_psi-self.min_psi)/(self.spacing_psi)/2, self.max_psi+(self.max_psi-self.min_psi)/(self.spacing_psi)/2))
        self.subplot.set_xlabel("$\phi$ [°]")
        self.subplot.set_ylabel("$\psi$ [°]")
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
            t1 = threading.Thread(target= lambda arg_min_phi=self.box_min_phi.get(), arg_max_phi=self.box_max_phi.get(), arg_min_psi=self.box_min_psi.get(), arg_max_psi=self.box_max_psi.get(), arg_spacing_phi=self.box_spacing_phi.get(), arg_spacing_psi=self.box_spacing_psi.get() : self.recordRateDistribution(spacing_phi=arg_spacing_phi, spacing_psi=arg_spacing_psi, min_phi=arg_min_phi, max_phi=arg_max_phi, min_psi=arg_min_psi, max_psi=arg_max_psi))
            t1.start()
            self.replotRatesUpdate()
        else:
            print("Result will be plotted after everything is measured!")
            self.recordRateDistribution(self.box_spacing_phi.get(), self.box_spacing_psi.get(), self.box_min_phi.get(), self.box_max_phi.get(), self.box_min_psi.get(), self.box_max_psi.get())
            self.replotRates()
            
         
    def recordRateDistribution(self, spacing_phi=25, spacing_psi=26, min_phi=-2., max_phi=2, min_psi=-3.80, max_psi=-0.5):
        print("Starting to measure the rate distribution. MinPhi={0:4.2f} ; MaxPhi={1:4.2f} ; MinPsi={2:4.2f} ; MaxPsi={3:4.2f} ; SpacingPhi={4} ; SpacingPsi={5}".format(min_phi, max_phi, min_psi, max_psi, spacing_phi, spacing_psi))
        self.resetRectangle()
        if self.client==None:
            print("No client connected! Cannot plot Mirrors")
            self.still_recording=False
            return
        self.controller.setBussy(True)
        sleep(0.02)
        coordinates_phi=np.linspace(min_phi, max_phi, num=spacing_phi)
        coordinates_psi=np.linspace(min_psi, max_psi, num=spacing_psi)
        x, y=np.meshgrid(coordinates_phi, coordinates_psi)
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
        while moving_both:
            sleep(0.05)
            try:
		    	moving_both=self.controller.get_mirror_phi_moving() or self.controller.get_mirror_psi_moving() 
		    except TrinamicException:
	    		print("Trinamic Exception while waiting for PHI and PSI to stop moving")
        #walk through the whole space of different positions
        for i in range(0, spacing_phi, 1):
            pos_phi=min_phi+(max_phi-min_phi)/(spacing_phi-1)*i
            self.controller.set_position_mirror_phi(pos_phi)
            moving_phi=True
            try:
            	moving_phi=self.controller.get_mirror_phi_moving()
        	except TrinamicException:
        		print("Trinamic Exception while waiting for PHI to stop moving")
            while moving_phi:
                sleep(0.05)
                try:
		        	moving_phi=self.controller.get_mirror_phi_moving()
		    	except TrinamicException:
		    		print("Trinamic Exception while waiting for PHI to stop moving")
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
                while moving_psi:
                    sleep(0.05)
            		try:
             		   	moving_psi=self.controller.get_mirror_psi_moving()
        			except TrinamicException:
            			print("Trinamic Exception while waiting for PSI to stop moving")
                if i%2==0:
                    rates[i][spacing_psi-1-j]=self.client.getRateA()+self.client.getRateB()
                else:
                    rates[i][j]=self.client.getRateA()+self.client.getRateB()
                self.rates=np.transpose(rates)
                self.new_record=True
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
                
    def findRectangle(self, contrast_factor=1.5):
        rates=self.rates
        coordinates_phi=np.linspace(self.min_phi, self.max_phi, num=int(self.spacing_phi))
        coordinates_psi=np.linspace(self.min_psi, self.max_psi, num=int(self.spacing_psi))
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
        print("rect_start_phi={0} ; rect_start_psi={1} ; rect_width_phi={2} ; rect_width_psi={3}".format(rect_start_phi, rect_start_psi, rect_width_phi, rect_width_psi ))
        self.min_phi_rect=rect_start_phi
        self.max_phi_rect=rect_start_phi+rect_width_phi
        self.min_psi_rect=rect_start_psi+rect_width_psi
        self.max_psi_rect=rect_start_psi
        
    #####################################
    #  FILE FORMAT FOR THE .rate FILES  #
    # [00] Min Phi                      #
    # [01] Max Phi                      #
    # [02] Min Psi                      #
    # [03] Max Psi                      #
    # [04] Spacing Phi                  #
    # [05] Spacing Psi                  #
    # [06] Camera Z                     #
    # [07] Camera X                     #
    # [08] Mirror Z                     #
    # [09] Mirror Height                #
    # [10] actual Rates                 #
    #####################################
    
    
    def loadRates(self):
        file = filedialog.askopenfile(parent=self.window, initialdir = "../../..", title = "Load Rate Distribution", filetypes = (("rate files","*.rate"),("all files","*.*")))
        if file!=None:
            string=file.read()
            parts=string.split("~")
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
        self.resetRectangle()
        self.replotRates()

    def saveRates(self, path=None):
        if path==None:
            file = filedialog.asksaveasfile(parent=self.window, initialdir = "../../..", title = "Save Rate Distribution", filetypes = (("rate files","*.rate"),("all files","*.*")))
        else:
            file = open(path, "w")
        if file!=None:
            #file=open(filename, "w")
            file.write("{0}~{1}~{2}~{3}~{4}~{5}~{6}~{7}~{8}~{9}~{10}".format(self.min_phi, self.max_phi, self.min_psi, self.max_psi, self.spacing_psi, self.spacing_phi, self.camera_z, self.camera_x, self.mirror_z, self.mirror_height, self.rates).replace("\n ", "").replace("]", "]\n").replace("]\n]", "]]"))
            file.close()
            
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
        print("Start to do a crazy batch!")
        self.controller.setBatch(True)
        
        ########################################################################################
        #  this method will perform all measurements that are listed in the measurement array  #
        #  the measurements are to be stored as follows:                                       #
        #     [0] position_camera_z                                                            #
        #     [1] position_camera_x                                                            #
        #     [2] position_mirror_z                                                            #
        #     [3] position_mirror_height                                                       #
        #     [4] phi_min                                                                      #
        #     [5] phi_max                                                                      #
        #     [6] psi_min                                                                      #
        #     [7] psi_max                                                                      #
        #     [8] spacing_phi                                                                  #
        #     [9] spacing_psi                                                                  #
        #  the reuslts are stored in the same way, but additionally contain:                   #
        #     [10] id / number of measurement                                                  #
        #     [11] center_phi                                                                  #
        #     [12] center_psi                                                                  #
        #     [13] sigma_phi                                                                   #
        #     [14] sigma_psi                                                                   #
        #     [15] prefactor                                                                   #
        #     [16] offset                                                                      #
        #     [17] timestamp                                                                   #
        ########################################################################################
        
        path="../../../crazy_batch"
        try:
            #print(path)
            os.mkdir(path, mode=0o777)
            #print("{0}/rates".format(path))
            os.mkdir("{0}/rates".format(path), mode=0o777)
        except:
            print("Cannot create new directory! Does the directory already exist? Please check and retry!")
            return
        measurements=np.zeros(shape=(211,10))
        #first measurement is the "equilibrium position"
        measurements[0]=[70, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        #now check "depth" by slowly moving the camera away from the mirror (center pos)
        measurements[1]=[95, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[2]=[90, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[3]=[85, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[4]=[80, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[5]=[75, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[6]=[70, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[7]=[65, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[8]=[60, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[9]=[55, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[10]=[50, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[11]=[45, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[12]=[40, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[13]=[35, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[14]=[30, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[15]=[25, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[16]=[20, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[17]=[15, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[18]=[10, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[19]=[5, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[20]=[0, 125. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        #now check "depth" by slowly moving the camera away from the mirror (left pos)
        measurements[21]=[95, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 5, 5]
        measurements[22]=[90, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 5, 5]
        measurements[23]=[85, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[24]=[80, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[25]=[75, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[26]=[70, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[27]=[65, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[28]=[60, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[29]=[55, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[30]=[50, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[31]=[45, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[32]=[40, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[33]=[35, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[34]=[30, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[35]=[25, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[36]=[20, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[37]=[15, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[38]=[10, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[39]=[5, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[40]=[0, 100. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        #now check "depth" by slowly moving the camera away from the mirror (right pos)
        measurements[41]=[95, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 5, 5]
        measurements[42]=[90, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 5, 5]
        measurements[43]=[85, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[44]=[80, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[45]=[75, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[46]=[70, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[47]=[65, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[48]=[60, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[49]=[55, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[50]=[50, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[51]=[45, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[52]=[40, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[53]=[35, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[54]=[30, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[55]=[25, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[56]=[20, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[57]=[15, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[58]=[10, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[59]=[5, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[60]=[0, 150. , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        #now check "depth" by slowly moving the camera away from the mirror (upper pos)
        measurements[61]=[95, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 5, 5]
        measurements[62]=[90, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 5, 5]
        measurements[63]=[85, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[64]=[80, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[65]=[75, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[66]=[70, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[67]=[65, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[68]=[60, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[69]=[55, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[70]=[50, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[71]=[45, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[72]=[40, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[73]=[35, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[74]=[30, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[75]=[25, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[76]=[20, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[77]=[15, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[78]=[10, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[79]=[5, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[80]=[0, 125. , 94.5, 1, -4.4, 4.4, -4.4, 4.4, 25, 25]
        #now check "depth" by slowly moving the camera away from the mirror (lower pos)
        measurements[81]=[95, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 5, 5]
        measurements[82]=[90, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 5, 5]
        measurements[83]=[85, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[84]=[80, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[85]=[75, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[86]=[70, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[87]=[65, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[88]=[60, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[89]=[55, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[90]=[50, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[91]=[45, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[92]=[40, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[93]=[35, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[94]=[30, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[95]=[25, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[96]=[20, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[97]=[15, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[98]=[10, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[99]=[5, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[100]=[0, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        #now try to measure the influence of the mirror height
        measurements[101]=[70, 125. , 94.5, 0, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[102]=[70, 125. , 94.5, 5, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[103]=[70, 125. , 94.5, 10, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[104]=[70, 125. , 94.5, 15, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[105]=[70, 125. , 94.5, 20, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[106]=[70, 125. , 94.5, 25, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[107]=[70, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[108]=[70, 125. , 94.5, 35, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[109]=[70, 125. , 94.5, 40, -4.4, 4.4, -4.4, 4.4, 25, 25]
        #now try to measure the influence of the mirror position
        measurements[110]=[70, 125. , 94.5, 0, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[111]=[70, 125. , 90, 0, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[112]=[70, 125. , 85, 0, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[113]=[70, 125. , 80, 0, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[114]=[70, 125. , 70, 0, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[115]=[70, 125. , 60, 0, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[116]=[70, 125. , 50, 0, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[117]=[70, 125. , 40, 0, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[118]=[70, 125. , 94.5, 5, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[119]=[70, 125. , 90, 5, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[120]=[70, 125. , 85, 5, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[121]=[70, 125. , 80, 5, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[122]=[70, 125. , 70, 5, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[123]=[70, 125. , 60, 5, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[124]=[70, 125. , 50, 5, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[125]=[70, 125. , 40, 5, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[126]=[70, 125. , 94.5, 10, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[127]=[70, 125. , 90, 10, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[128]=[70, 125. , 85, 10, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[129]=[70, 125. , 80, 10, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[130]=[70, 125. , 70, 10, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[131]=[70, 125. , 60, 10, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[132]=[70, 125. , 50, 10, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[133]=[70, 125. , 40, 10, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[134]=[70, 125. , 94.5, 15, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[135]=[70, 125. , 90, 15, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[136]=[70, 125. , 85, 15, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[137]=[70, 125. , 80, 15, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[138]=[70, 125. , 70, 15, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[139]=[70, 125. , 60, 15, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[140]=[70, 125. , 50, 15, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[141]=[70, 125. , 40, 15, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[142]=[70, 125. , 94.5, 20, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[143]=[70, 125. , 90, 20, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[144]=[70, 125. , 85, 20, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[145]=[70, 125. , 80, 20, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[146]=[70, 125. , 70, 20, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[147]=[70, 125. , 60, 20, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[148]=[70, 125. , 50, 20, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[149]=[70, 125. , 40, 20, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[150]=[70, 125. , 94.5, 25, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[151]=[70, 125. , 90, 25, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[152]=[70, 125. , 85, 25, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[153]=[70, 125. , 80, 25, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[154]=[70, 125. , 70, 25, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[155]=[70, 125. , 60, 25, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[156]=[70, 125. , 50, 25, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[157]=[70, 125. , 40, 25, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[158]=[70, 125. , 94.5, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[159]=[70, 125. , 90, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[160]=[70, 125. , 85, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[161]=[70, 125. , 80, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[162]=[70, 125. , 70, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[163]=[70, 125. , 60, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[164]=[70, 125. , 50, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[165]=[70, 125. , 40, 30, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[166]=[70, 125. , 94.5, 35, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[167]=[70, 125. , 90, 35, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[168]=[70, 125. , 85, 35, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[169]=[70, 125. , 80, 35, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[170]=[70, 125. , 70, 35, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[171]=[70, 125. , 60, 35, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[172]=[70, 125. , 50, 35, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[173]=[70, 125. , 40, 35, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[174]=[70, 125. , 94.5, 40, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[175]=[70, 125. , 90, 40, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[176]=[70, 125. , 85, 40, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[177]=[70, 125. , 80, 40, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[178]=[70, 125. , 70, 40, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[179]=[70, 125. , 60, 40, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[180]=[70, 125. , 50, 40, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[181]=[70, 125. , 40, 40, -4.4, 4.4, -4.4, 4.4, 25, 25]
        #try to measure the horizontal shift of the camera
        measurements[182]=[70, 50 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[183]=[70, 60 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[184]=[70, 65 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[185]=[70, 70 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[186]=[70, 75 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[187]=[70, 80 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[188]=[70, 85 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[189]=[70, 90 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[190]=[70, 95 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[191]=[70, 100 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[192]=[70, 105 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[193]=[70, 110 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[194]=[70, 115 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[195]=[70, 120 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[196]=[70, 125 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[197]=[70, 130 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[198]=[70, 135 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[199]=[70, 140 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[200]=[70, 145 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[201]=[70, 150 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[202]=[70, 155 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[203]=[70, 160 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[204]=[70, 165 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[205]=[70, 170 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[206]=[70, 175 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[207]=[70, 180 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[208]=[70, 185 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[209]=[70, 190 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        measurements[210]=[70, 200 , 94.5, 13.2, -4.4, 4.4, -4.4, 4.4, 25, 25]
        #measurements=measurements[42:]
        results=np.zeros(shape=(len(measurements), 18))
        no=0
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
            while moving_all:
                sleep(0.05)
	            try:
		        	moving_all=self.controller.get_camera_z_moving() or self.controller.get_camera_x_moving() or self.controller.get_mirror_z_moving() or self.controller.get_mirror_height_moving()
		    	except TrinamicException:
		    		print("Trinamic Exception while waiting for 4 Dimensions to stop moving")
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
					print("Tried twice to get the Positions but failed both times! Instead take the ones that were initally set!")
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
            gaussian=self.fitGaussian()
            
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
        self.controller.setBussy(False)
        self.controller.setBatch(False)
        print("The batch is done!")
def gauss2d(datapoints, prefactor=1, x_0=0, x_sigma=1, y_0=0, y_sigma=1, offset=0):
    return offset+prefactor*np.exp(-(np.power(datapoints[0]-x_0, 2)/(2*np.power(x_sigma,2)))-(np.power(datapoints[1]-y_0,2)/(2*np.power(y_sigma,2)))).ravel()
