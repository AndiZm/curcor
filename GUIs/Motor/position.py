import ephem
from datetime import datetime

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
		"Mimosa,
		"Test"
		])
