#! /usr/env/python

#Python script to plot ellipses for uv plane interferometry HESS

import numpy as np
import matplotlib.pyplot as plt
import os, sys

if __name__ == '__main__':


    hesslatitude = 23.272/57.3
    hesslongitude = 16.5/57.3

    ra = 266.42/57.3
    dec = -29.01/57.3

    baseNS = -169.7
    baseEW = 169.7

    baselines = np.matrix([baseNS,baseEW,0.])
    baselinesHI = np.matrix([-120.,120.,0.])
    baselines5 = np.matrix([baseNS/2,baseEW/2,0.])

    NumPoints = 50

    uvw = np.matrix([[0.0]*3]*NumPoints)
    uvwHI = np.matrix([[0.0]*3]*NumPoints)
    uvw5 = np.matrix([[0.0]*3]*NumPoints)


#    print 'sanity check: sin(30) = ', np.sin(30/57.3) 

#    print baselines, baselines5

    for i in xrange(0, NumPoints, 1):

        #one hour fraction 1/24 = 0.04167
      #  print float(i)/50, (float(i)/50) +0.5
        GST = (18.697374558 + 24.06570982441908*((float(i)/50)+0.5))/57.3

        hourangle = GST - hesslongitude - ra

        fcoords = np.matrix([[-np.sin(hesslatitude)*np.sin(hourangle),np.cos(hourangle),np.cos(hesslatitude)*np.sin(hourangle)],[np.sin(hesslatitude)*np.cos(hourangle)*np.sin(dec)+np.cos(hesslatitude)*np.cos(dec),np.sin(hourangle)*np.sin(dec),-np.cos(hesslatitude)*np.cos(hourangle)*np.sin(dec)+np.sin(hesslatitude)*np.cos(dec)],[-np.sin(hesslatitude)*np.cos(hourangle)*np.cos(dec)+np.cos(hesslatitude)*np.sin(dec),-np.sin(hourangle)*np.cos(dec),np.cos(hesslatitude)*np.cos(hourangle)*np.cos(dec)+np.sin(hesslatitude)*np.sin(dec)]])


#        print fcoords , baselines.T

        multi = fcoords*baselines.T
        multiHI = fcoords*baselinesHI.T
        multi5 = fcoords*baselines5.T

        uvw[i,0] = multi[0]
        uvw[i,1] = multi[1]
        uvw[i,2] = multi[2]
#        uvwrefl[i] = -fcoords*baselines
        uvwHI[i,0] = multiHI[0]
        uvwHI[i,1] = multiHI[1]
        uvwHI[i,2] = multiHI[2]
        uvw5[i,0] = multi5[0]
        uvw5[i,1] = multi5[1]
        uvw5[i,2] = multi5[2]

#    for nump in xrange(0,NumPoints,1):
    plt.grid(True)

    uvellipse = plt.plot(uvw[:,0],uvw[:,1], 'r')
    uvellipseb = plt.plot(uvw[:,0],-uvw[:,1], 'r')
    uvellipsec = plt.plot(-uvw[:,0],uvw[:,1], 'r')
    uvellipsed = plt.plot(-uvw[:,0],-uvw[:,1], 'r')
    uvellipseHI = plt.plot(uvwHI[:,0],uvwHI[:,1], 'g')
    uvellipseHIb = plt.plot(uvwHI[:,0],-uvwHI[:,1], 'g')
    uvellipseHIc = plt.plot(-uvwHI[:,0],uvwHI[:,1], 'g')
    uvellipseHId = plt.plot(-uvwHI[:,0],-uvwHI[:,1], 'g')
    uvellipse5 = plt.plot(uvw5[:,0],uvw5[:,1], 'b')                     
    uvellipse5b = plt.plot(uvw5[:,0],-uvw5[:,1], 'b')
    uvellipse5c = plt.plot(-uvw5[:,0],uvw5[:,1], 'b')
    uvellipse5d = plt.plot(-uvw5[:,0],-uvw5[:,1], 'b')

    plt.xlabel('u.lambda (m)')
    plt.ylabel('v.lambda (m)')

    plt.show()
