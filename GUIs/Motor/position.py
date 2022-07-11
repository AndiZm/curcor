import ephem
from datetime import datetime
from tkinter import *
import numpy as np

#this class provides you with the position of the observed object
class position:

	#position of the HESS Site
	HESS_site = ephem.Observer()
	HESS_site.lat  = ephem.degrees("-23.271536")
	HESS_site.long = ephem.degrees("16.500974")

	#object we observe
	obj = ephem.star("Acrux")
	
	#sets the observed object to an new star
	def set_star(self, star):
		print("try to set star to {0}".format(star))
		try:
			self.obj=ephem.star(star)
		except KeyError:
			print("Apparently this is not a valid name of a star and can therefore not be set!")
			return
		print("succesfully set star to {0}".format(self.obj.name))
	
	#returns the position of the observed object in Ra, Dec coordinates
	def get_ra_dec(self):
		return (self.obj.ra, self.obj.dec)
	
	def get_az_alt(self):
		self.HESS_site.date = ephem.Date(datetime.utcnow())
		self.obj.compute(self.HESS_site)
		#print("Time: {0} , Alt: {1} , Az: {2}".format(datetime.utcnow(), self.obj.az/np.pi*180, self.obj.alt/np.pi*180))
		return self.obj.az/np.pi*180, self.obj.alt/np.pi*180
		
	def get_star_list(self):
		return [
		"Acrux",
		"Peacock",
		"Alnair",
		"Mimosa",
		"Test"
		]

	def get_name(self):
		return self.obj.name

class selection_dialog(simpledialog.Dialog):
	## this thing inherits stuff from the SimpleDialog class
	position=None
	menu=None
	selected_star=None
	def __init__(self, master, position):
		self.position=position
		simpledialog.Dialog.__init__(self, master)
	def body(self, master):  ## wird ueberschrieben
		self.title('Star Selector')
		#get list of all stars that are available in the position class
		stars=self.position.get_star_list()

		self.selected_star=StringVar()
		self.selected_star.set(stars[0])
		#self.label=Label(master, text="Select object:", justify = LEFT, padx = 20).pack(side="top")
		self.menu=OptionMenu(self, self.selected_star, *stars)
		self.menu.pack()
		self.menu.config(width="25")
		
	def apply(self): # override
		self.result = self.selected_star.get()
