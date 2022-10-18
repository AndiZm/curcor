import matplotlib.pyplot as plt
import matplotlib.animation as ani
import os
import moviepy.editor as mp
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from mpl_toolkits.axes_grid.inset_locator import (inset_axes, InsetPosition, mark_inset)


def hours2rad(h,m,s):
    degs = ( h*15 + m*(15/60) + s*(15/3600) ) - 180
    return degs * np.pi/180
def deg2rad(deg, amin, asec):
    degs = ( deg + np.sign(deg)*amin/60 + np.sign(deg)*asec/3600 )
    return  degs * np.pi/180

x = np.arange(0,len(np.loadtxt("g2cross_20220421_HESS_Shaula_use_17_35_8.6--37_7_9.9.txt")[:,1]),1)

def gauss(x, a, x0, sigma, d):
    return a*np.exp(-(x-x0)**2/(2*sigma**2)) + d

def fit(data, s, e, m):
    xfit = x[(x>s) & (x<e)]
    yfit = data[(x>s) & (x<e)]
    xplot = np.arange(s, e, 0.01)
    popt, cov = curve_fit(gauss, xfit, yfit, p0=[1e-6,m,3,1])
    perr = np.sqrt(np.diag(cov))
    return xplot, popt, perr

def integral(fitpar, fitpar_err):
    a = fitpar[0]; d_a = fitpar_err[0]
    s = np.abs(fitpar[2]*1e-9); d_s = fitpar_err[2]*1e-9
    Int = a*s*np.sqrt(2*np.pi)
    dInt = np.sqrt(2*np.pi)*np.sqrt((a*d_s)**2 + (s*d_a)**2)
    return Int, dInt

# Scan into one direction
fig = plt.figure(figsize=(12,6))

#plt.rcParams["figure.figsize"] = [12, 6]
#plt.rcParams["figure.autolayout"] = True

ax_g2 = fig.add_subplot(111)

ax_sky = plt.axes([0,0,1,1], projection="aitoff")
ip = InsetPosition(ax_g2, [0.05,0.55,0.4,0.4])
ax_sky.set_axes_locator(ip)
ax_sky.grid()


ax_g2.axvline(x=5000, color="grey", linestyle="--")
ax_g2.set_xlim(4700,5300); ax_g2.set_ylim(0.9999995, 1.0000014)
ax_g2.set_xlabel("Time bin"); ax_g2.set_ylabel("$g^{(2)}$")
ax_g2.ticklabel_format(useOffset=False)
#plt.tight_layout()

shaula_ra  = hours2rad(17, 35, 8.6)
shaula_dec = deg2rad(-37, 7, 9.9)

ax_sky.plot(shaula_ra, shaula_dec, 'o', markersize=7)

js = np.arange(10, 47, 1)

data = np.loadtxt("g2cross_20220421_HESS_Shaula_use_17_35_8.6-{}_7_9.9.txt".format(-1*js[0]))[:,1]
correlation, = ax_g2.plot(data, color="red")

use_dec = deg2rad(-10, 7, 9.9)
use_position, = ax_sky.plot(shaula_ra, use_dec, "o", markersize=4, color="red")


#plt.show()

def build_g2(frame):
    j = js[frame]

    dec = -1*j
    use_dec = deg2rad(dec, 7, 9.9)

    data = np.loadtxt("g2cross_20220421_HESS_Shaula_use_17_35_8.6-{}_7_9.9.txt".format(dec))[:,1]

    correlation.set_ydata(data)
    use_position.set_ydata(use_dec)


frames=len(js)

name = r"\Shaula.gif"
path = str(os.getcwd())

anim = ani.FuncAnimation(fig, build_g2, frames = frames, interval=150)
anim.save(path+name)

clip = mp.VideoFileClip(path+name)