
import scipy.optimize as opt
from numpy import random

import numpy as np #only needed for simulations
from PIL import Image


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
