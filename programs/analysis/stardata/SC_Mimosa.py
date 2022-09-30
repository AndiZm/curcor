#!/usr/bin/env python3

import os

import inspect
import math
import numpy
import ephem
import matplotlib.pyplot as plt
import scipy.special as scp
from operator import itemgetter
import scipy.interpolate

from geopy.distance import geodesic
import geopy.distance
import numpy as np
import subprocess
import os

#source, rad, dis, mag = np.genfromtxt('star_list.txt', delimiter=';', unpack=True)
source = "Mimosa"
anfang = 20
ende = 21

command = 'python baselines/ -source %s -t1 2022/04/%s 17:00:00 -t2 2022/04/%s 05:00:00 -verbose -save_data -save_plot' %(source,anfang, ende)
os.system(command)

print('picture')

angles, atm_trans = np.loadtxt('baselines/output/atm txt/Mimosa_atm_trans.txt', unpack=True)
func = scipy.interpolate.interp1d(angles, atm_trans)
#realtime, sourcealt, baseline_3_4, baseline_1_3, baseline_1_4, baseline_2_4, baseline_1_2, baseline_2_3 = np.loadtxt('baselines/output/baseline txt/%s.txt' %(source), unpack=True)
realtime, sourcealt, baseline_3_4, baseline_1_4, separation = np.loadtxt('baselines/output/baseline txt/%s.txt' %(source), unpack=True)
#bl_1_2 = np.nan_to_num(baseline_1_2, nan=0)
#bl_1_3 = np.nan_to_num(baseline_1_3, nan=0)
bl_1_4 = np.nan_to_num(baseline_1_4)
#bl_2_4 = np.nan_to_num(baseline_2_4, nan=0)
bl_3_4 = np.nan_to_num(baseline_3_4)
separation = np.nan_to_num(separation)


y = []
m = []
d = []
h = []
mi = []
s = []
for i in range(len(realtime)):
	realt = (ephem.Date(realtime[i]))
	year, month, day, hour, minute, sec = realt.tuple()
	y.append(year)
	m.append(month)
	d.append(day)
	h.append(hour)
	mi.append(minute)
	s.append(sec)

year = np.array(y)
month = np.array(m)
day = np.array(d)
hour = np.array(h)
minute = np.array(mi)

#### change  ###
rad = 8.4                   # radius of star in m
dis = 85  					# distance of star in m 
mag = 1.25  				# magnitude of star
#### #####

atm = 0.7 					# atmospheric transmission 
tau_e = 5e-9				# electronics time resolution of HESS
T = 20*60 					# Messzeit in sec
lam = 465e-9				# in m Filterwellenlaenge
dlam = 2e-9					# in m Filterbreite
c = 299792458				# Lichtgeschw m/s
area = 100					# in m^2
opt = 0.6					# optical loss factor
eff = 0.361 				# PMT efficiency
bs = 2						# beamsplitter factor
bg = 0.1					# background photon rate


# calculate angular size in rad
ang = (2*7e8*rad)/(3.1e16*dis)		# 7e8 Sun radius in m, 3.1e16 pc in m
print("angular size =" + str(ang) + "rad")
#convert ang size from rad in mas
angu = (ang*206264806.71915)
print("angular size =" + str(angu) + 'mas')

# fuer mag2flux
lambda_0 = 465 * 1e-9 	# [m] Central wavelength
h = 6.626e-34 			# [J s] Planck constant
F_nu = 4.26e-23 		# [W/m^2/Hz] Absolute flux density for mag = 0.0 at 440 nm (Bessel 1979)

# Calculate Photon rate from star magnitude (in the B-band)
def mag2flux(m_v):	
	return 1e-9 * F_nu * 100**(-m_v/5)  / h / lambda_0 # Flux in Hz / m^2 / nm

fl =  mag2flux(mag)
print("Flux =" + str(fl/1000000) + ' ' + 'MHz')

R = (2*fl*area*opt*eff*atm)/bs  		# 2 wegen 2nm filterbreite
print("Rate:" + str(R/1000000) + ' ' + 'MHz')					# Rate in MHz 
x = np.linspace(0,200)				# Baseline 
sc = (2*scp.j1(np.pi*x*ang/lam)/(np.pi*x*ang/lam))**2  #j1 Bessel fct mit x als baseline
 
tau_c = 0.5*0.664* ((lam)**2/ (c* dlam))
#print("tau_c:" + str(tau_c))

dS = ((1/R )* np.sqrt(tau_e/T))/ tau_c 
dS2 = (np.sqrt(tau_e/T)*(1+bg))/ (R*tau_c) 
#print("Fehler:" + str(dS))
#print("Fehler:" + str(dS2))

bl12 = []
bl13 = []
bl14 =[]
bl24 = []
bl34 = []
S_bl12 = []
S_bl13 = []
S_bl14 = []
S_bl24 = []
S_bl34 = []
Rate12 = []
Rate13 = []
Rate14 = []
Rate24 = []
Rate34 = []
deltaS12 = []
deltaS13 = []
deltaS14 = []
deltaS24 = []
deltaS34 = []
t_ob = []
salt = []
R34 = []

for i in range(len(sourcealt)):
	y = sourcealt[i]
	zenith = 90 - sourcealt[i]
	#a = bl_1_2[i]
	#b = bl_1_3[i]
	#c = bl_1_4[i]
	#d = bl_2_4[i]
	e = bl_3_4[i]
	#if y > 10 and a != 0:
	#	bl12.append(bl_1_2[i])
	#	S_bl12.append( (2*scp.j1(np.pi*baseline_1_2[i]*ang/lam)/(np.pi*baseline_1_2[i]*ang/lam))**2 )
	#	Rate12.append( (2*fl*area*opt*eff*func(zenith))/bs ) 
	#	deltaS12.append( (1/Rate12[-1] )* np.sqrt(tau_e/T)/ tau_c )
	#if y > 10 and b!= 0:
	#	bl13.append(bl_1_3[i])
	#	S_bl13.append( (2*scp.j1(np.pi*baseline_1_3[i]*ang/lam)/(np.pi*baseline_1_3[i]*ang/lam))**2 )
	#	Rate13.append( (2*fl*area*opt*eff*func(zenith))/bs ) 
	#	deltaS13.append( (1/Rate13[-1] )* np.sqrt(tau_e/T)/ tau_c )
	if y > 20 and c!= 0:
		bl14.append(bl_1_4[i])
		S_bl14.append( (2*scp.j1(np.pi*baseline_1_4[i]*ang/lam)/(np.pi*baseline_1_4[i]*ang/lam))**2 )
		Rate14.append( (2*fl*area*opt*eff*func(zenith))/bs ) 
		deltaS14.append( (1/Rate14[-1] )* np.sqrt(tau_e/T)/ tau_c )
	#if y > 10 and d!= 0:
	#	bl24.append(bl_2_4[i])
	#	S_bl24.append( (2*scp.j1(np.pi*baseline_2_4[i]*ang/lam)/(np.pi*baseline_2_4[i]*ang/lam))**2 )	
	#	Rate24.append( (2*fl*area*opt*eff*func(zenith))/bs ) 
	#	deltaS24.append( (1/Rate24[-1] )* np.sqrt(tau_e/T)/ tau_c )		
	if y > 10 and e!= 0:
		bl34.append(bl_3_4[i])
		S_bl34.append( (2*scp.j1(np.pi*baseline_3_4[i]*ang/lam)/(np.pi*baseline_3_4[i]*ang/lam))**2 )	
		Rate34.append( (2*fl*area*opt*eff*func(zenith))/bs ) 
		R34.append(Rate34[-1]/1000000)
		deltaS34.append( (1/Rate34[-1] )* np.sqrt(tau_e/T)/ tau_c )
		t_ob.append(realtime[i])
		salt.append(sourcealt[i])
		#print(ephem.Date(realtime[i]), sourcealt[i], bl_3_4[i], separation[i])
th = []
tmin = []
for i in range(len(t_ob)):
	t = (ephem.Date(t_ob[i]))
	year2, month2, day2, hour2, minute2, sec2 = t.tuple()
	th.append(hour2)
	tmin.append(minute2)

thour = np.array(th)
tminute = np.array(tmin)
print(len(thour), len(tminute), len(salt), len(Rate34))
#print(Rate34)
print(ephem.Date(realtime[0]), sourcealt[0], ephem.Date(realtime[-1]), sourcealt[-1], ephem.Date(t_ob[0]), ephem.Date(t_ob[-1]))
#S = (2*scp.j1(np.pi*110*ang/lam)/(np.pi*110*)ang/lam))**2   # fuer bestimmte baseline 110m 
#S2 = (2*scp.j1(np.pi*100*ang/lam)/(np.pi*100*ang/lam))**2 

plt.plot(x,sc)
#plt.errorbar(bl12, S_bl12, yerr=deltaS12, marker='o', label='baseline 1-2')
plt.errorbar(bl14, S_bl14, yerr=deltaS14, marker='o', label='baseline 1-4')
plt.errorbar(bl34, S_bl34, yerr=deltaS34, marker='o', label='baseline 3-4')
#plt.errorbar(bl13, S_bl13, yerr=deltaS13, marker='o', label='baseline 1-3')
#plt.errorbar(bl24, S_bl24, yerr=deltaS24, marker='o', label='baseline 2-4')
#plt.errorbar(110, S, yerr=dS, marker='o', color='red')
#plt.errorbar(100, S2, yerr=dS2, marker='o', color='red')
plt.legend()
plt.title('g2 for %s' %(source))
plt.xlabel('baseline')
plt.savefig('%s/%s_%s_%s_sc.pdf' %(source, source, anfang, ende))
#np.savetxt("Namibia_April2022/, np.c_[realtime, sourcealt, baseline_3_4, baseline_1_4, separation])
np.savetxt("%s/%s_%s_%s.txt" %(source, source, anfang, ende), np.c_[year, month ,day ,hour, minute, sourcealt, bl_3_4, separation], fmt=' '.join(['%02d']*5 + ['%1.2f']*3), header = "year, month, day, hour, min, alt, baseline, separation moon")
np.savetxt("%s/%s_%s_%s_data.txt" %(source, source, anfang, ende), np.c_[thour, tminute, salt, bl34, R34, S_bl34], fmt=' '.join(['%02d']*2 + ['%1.2f']*4), header = "hour, min, alt, baseline, rate, SC")

#plt.show()





