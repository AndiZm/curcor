import threading
import scipy.optimize as opt
from numpy import random
from tkinter import *
from tkinter import simpledialog
from time import sleep

import numpy as np #only needed for simulations
from PIL import Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


class RATE_ANALYZER():
    
    client=None
    controller=None
    change_mirror_psi=False
    change_mirror_phi=False
    
    #currently loaded distribution
    rates=None
    min_phi=-4.5
    max_phi=4.5
    min_psi=-4.5
    max_psi=4.5
    spacing_psi=10
    spacing_phi=10
    
    #Stuff for the GUI
    window=None
    main_frame=None
    plot_frame=None
    button_frame=None
    nextIterationButton=None
    recordButton=None
    label_min_psi=None
    label_max_psi=None
    label_min_phi=None
    label_max_phi=None
    label_spacing_phi=None
    label_spacing_psi=None
    checkbutton_live=None
    box_min_phi=None
    box_max_phi=None
    box_min_psi=None
    box_max_psi=None
    box_spacing_phi=None
    box_spacing_psi=None
    checked=False
    
    #values for (live) recording
    still_recording=False
    new_record=False

    plot=None
    
    def __init__(self, master, controller=None, client=None):
        #copy stuff
        self.controller=controller
        self.client=client
                
        #create new window and frames
        self.window = Toplevel(master)
        self.main_frame = Frame(self.window, width=840, height = 620)
        self.main_frame.grid(row=0, column=0)
        self.main_frame.config(background = "#003366")
        self.plot_frame = Frame(self.main_frame, width=600, height=600)
        self.plot_frame.grid(row=0, column=0, padx=10,pady=10)
        self.button_frame = Frame(self.main_frame, width=200, height=600)
        self.button_frame.grid(row=0, column=1, padx=10,pady=10)
        self.button_frame.config(background = "#003366")
        self.record_frame = Frame(self.button_frame, width=180, height=200)
        self.record_frame.grid(row=1, column=0, padx=10, pady=10)
        
        
        #create the plot
        self.plot=plt.Figure(figsize=(6,6))
        sub_plot = self.plot.add_subplot(111)
        sub_plot.set_title("Heatmap of the mirror Positions")
        sub_plot.set_xlabel("$\phi$ [°]")
        sub_plot.set_ylabel("$\psi$ [°]")
        sub_plot.set_xlim((self.min_phi, self.max_phi))
        sub_plot.set_ylim((self.min_psi, self.max_psi))
        
        self.canvas = FigureCanvasTkAgg(self.plot, master=self.plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.canvas.draw()
        
        #add GUI elements
        self.nextIterationButton = Button(self.button_frame, text="next Iteration in marked area", width=40, pady=3, padx=3)
        self.nextIterationButton.grid(row=0,column=0)
        
        
        #add record elements
        min_phi=-4.5
        max_phi=4.5
        min_psi=-4.5
        max_psi=4.5
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
        self.checked=True
        self.checkbutton_live = Checkbutton(self.record_frame, text="draw live", onvalue = True, offvalue = False, variable=self.checked)
        self.checkbutton_live.select()
        self.checkbutton_live.grid(row=6, column=0, padx=10, pady=3)

        #create sliders
        self.box_min_phi = Scale(self.record_frame, from_=-4.5, to=4.5, orient=HORIZONTAL, length=150, resolution=0.1)
        self.box_max_phi = Scale(self.record_frame, from_=-4.5, to=4.5, orient=HORIZONTAL, length=150, resolution=0.1)
        self.box_min_psi = Scale(self.record_frame, from_=-4.5, to=4.5, orient=HORIZONTAL, length=150, resolution=0.1)
        self.box_max_psi = Scale(self.record_frame, from_=-4.5, to=4.5, orient=HORIZONTAL, length=150, resolution=0.1)
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
        
        #record button
        self.recordButton = Button(self.button_frame, text="record rate Distribution", width=40, pady=3, padx=3)
        self.recordButton.grid(row=2)
        self.recordButton["command"]= self.recordRateDistributionRead
        
  
    def replotRates(self):
        #make a nice plot
        print("1")
        self.plot=plt.Figure(figsize=(6,6))
        sub_plot = self.plot.add_subplot(111)
        sub_plot.set_title("Heatmap of the mirror Positions")
        print("2")
        sub_plot.imshow(self.rates, cmap='cool', extent=( self.min_phi-(self.max_phi-self.min_phi)/(self.spacing_phi)/2, self.max_phi+(self.max_phi-self.min_phi)/(self.spacing_phi)/2, self.min_psi-(self.max_psi-self.min_psi)/(self.spacing_psi)/2, self.max_psi+(self.max_psi-self.min_psi)/(self.spacing_psi)/2))
        print("3")
        sub_plot.set_xlabel("$\phi$ [°]")
        sub_plot.set_ylabel("$\psi$ [°]")
        plt.draw()
        print("4")
        self.canvas = FigureCanvasTkAgg(self.plot, master=self.plot_frame)
        print("5")
        self.canvas.get_tk_widget().grid(row=0, column=0)
        print("6")
        self.canvas.draw()
        print("replotted the canvas")
    
#    def replotRatesUpdate(self):
#        print("started updating")
#        while self.still_recording:
#            sleep(0.05)
#            print("still looking for updates")
#            if self.new_record:
#                self.replotRates()
#                new_record=False
#                print("T2 replotted")
#        print("stopped updating")
    
    def recordRateDistributionRead(self):
        #self.still_recording=True
        #new_record=False
        print(self.checked)
        print("check 1")
        self.recordRateDistribution(self.box_spacing_phi.get(), self.box_spacing_psi.get(), self.box_min_phi.get(), self.box_max_phi.get(), self.box_min_psi.get(), self.box_max_psi.get(), False)#self.checked)
        #self.still_recording=False
        #self.replotRatesUpdate()
        print("By now the distribution should be plotted!")
        #t1 = threading.Thread(target= lambda arg_min_phi=self.box_min_phi.get(), arg_max_phi=self.box_max_phi.get(), arg_min_psi=self.box_min_psi.get(), arg_max_psi=self.box_max_psi.get(), arg_spacing_phi=self.box_spacing_phi.get(), arg_spacing_psi=self.box_spacing_psi.get(), arg_live=self.checked : self.recordRateDistribution(spacing_phi=arg_spacing_phi, spacing_psi=arg_spacing_psi, min_phi=arg_min_phi, max_phi=arg_max_phi, min_psi=arg_min_psi, max_psi=arg_max_psi, live=arg_live))
        #print("check 2")
        #t1.start()
        #t1.join()
        #print("check 3")
        #print("Checkpoint T1 started")
        
            
         
    def recordRateDistribution(self, spacing_phi=25, spacing_psi=26, min_phi=-2., max_phi=2, min_psi=-3.80, max_psi=-0.5, live=False):
        #print("You entered the DUMMY-state")
        print("Starting to measure the rate distribution. MinPhi={0:4.2f} ; MaxPhi={1:4.2f} ; MinPsi={2:4.2f} ; MaxPsi={3:4.2f} ; SpacingPhi={4} ; SpacingPsi={5}; Live={6}".format(min_phi, max_phi, min_psi, max_psi, spacing_phi, spacing_psi, live))
        
        if self.client==None:
            print("No client connected! Cannot plot Mirrors")
            return
        coordinates_phi=np.linspace(min_phi, max_phi, num=spacing_phi)
        coordinates_psi=np.linspace(min_psi, max_psi, num=spacing_psi)
        x, y=np.meshgrid(coordinates_phi, coordinates_psi)
        rates=np.empty(shape=(spacing_phi, spacing_psi))
        self.rates=np.transpose(rates)
        self.spacing_psi=spacing_psi
        self.spacing_phi=spacing_phi
        self.min_psi=min_psi
        self.max_psi=max_psi
        self.min_phi=min_phi
        self.max_phi=max_phi
        for i in range(0, spacing_phi, 1):
            pos_phi=min_phi+(max_phi-min_phi)/(spacing_phi-1)*i
            self.controller.set_position_mirror_phi(pos_phi)
            while self.controller.get_mirror_phi_moving():
                sleep(0.05)
                #print("wait_5_phi")
            for j in range(0, spacing_psi, 1):
                if i%2==0:
                    pos_psi=min_psi+(max_psi-min_psi)/(spacing_psi-1)*j
                else:
                    pos_psi=max_psi-(max_psi-min_psi)/(spacing_psi-1)*j
                #print("PSI: {0} PHI: {1}".format(pos_psi, pos_phi))
                self.controller.set_position_mirror_psi(pos_psi)
                while self.controller.get_mirror_psi_moving():
                    sleep(0.05)
                    #print("wait_4_psi")
                if i%2==0:
                    rates[i][spacing_psi-1-j]=self.client.getRateA()+self.client.getRateB()
                else:
                    rates[i][j]=self.client.getRateA()+self.client.getRateB()
                if live:
                    #self.new_record=True
                    self.rates=np.transpose(rates)
                    t = threading.Thread(target=self.replotRates)
                    t.start()
                    #t2.join()
                    print("Started replot thread")
        if live==False:
            self.rates=np.transpose(rates)
            print("before replot")
            self.replotRates()
            print("after replot")
            print(rates)
        # coordinates_phi=np.linspace(min_phi, max_phi, num=spacing_phi)
        #coordinates_psi=np.linspace(min_psi, max_psi, num=spacing_psi)
        #x, y=np.meshgrid(coordinates_phi, coordinates_psi)
        print("Recording of the rate distribution done!")
    def findActiveArea():
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
        
        #remove padding if it is lager than the range of the mirrors
        if min_phi>4.5: min_phi=4.5
        if min_phi<-4.5: min_phi=4.5
        if max_phi>4.5: max_phi=4.5
        if max_phi<-4.5: max_phi=4.5
        if min_psi>4.5: min_psi=4.5
        if min_psi<-4.5: min_psi=4.5
        if max_psi>4.5: max_psi=4.5
        if max_psi<-4.5: max_psi=4.5
        
        #add button for next closer fit
        min_phi=rect_start_phi
        max_phi=rect_start_phi+rect_width_phi
        min_psi=rect_start_psi+rect_width_psi
        max_psi=rect_start_psi
        
        contrast_factor=contrast_factor/1.5
        spacing_phi=spacing_phi+2
        spacing_psi=spacing_psi+2
        nextIterationButton["command"]= lambda argSpacingPhi=spacing_phi, argSpacingPsi=spacing_psi, argMinPhi=min_phi, argMaxPhi=max_phi, argMinPsi=min_psi, argMaxPsi=max_psi, argContrastFactor=contrast_factor : showRateDistribution(spacing_phi = argSpacingPhi, spacing_psi = argSpacingPsi, min_phi = argMinPhi, max_phi = argMaxPhi, min_psi = argMinPsi, max_psi= argMaxPsi, contrast_factor= argContrastFactor)
        
    def findRectangle(self, rates, sub_plot , spacing_phi, spacing_psi, min_phi, max_phi, min_psi, max_psi, contrast_factor):
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
