import ephem
from datetime import datetime
from tkinter import simpledialog

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
		self.obj=ephem.star(star)
		print("succesfully set star to {0}".format(self.obj.name))
	
	#returns the position of the observed object in Ra, Dec coordinates
	def get_ra_dec(self):
		return (self.obj.ra, self.obj.dec)
	
	def get_as_alt(self):
		self.HESS_site.date = ephem.Date(datetime.now())
		self.obj.compute(self.HESS_site)
		return self.obj.az, self.obj.alt
		
	def get_star_list(self):
		return np.array([
		"Acrux",
		"Alnair",
		"Mimosa",
		"Test"
		])

	def get_name(self):
		return self.obj.name

class selection_dialog(simpledialog.Dialog):
    ## this thing inherits stuff from the SimpleDialog class
    def body(self, master, position):  ## wird ueberschrieben
        self.title('Star Selector')
        #get list of all stars that are available in the position class
        stars=position.get_star_list()
        
        self.mode=IntVar()
        self.label=Label(master, text="Measurement mode", justify = LEFT, padx = 20).pack()
        self.linear=Radiobutton(master, text="linear", padx = 20, variable=self.mode, value=1).pack(anchor=W)
        self.angeled=Radiobutton(master, text="angled", padx = 20, variable=self.mode, value=2).pack(anchor=W)
        return self.linear #set focus on the linear option

    def apply(self): # override
        self.result = self.mode
