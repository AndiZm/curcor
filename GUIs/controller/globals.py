pc1Button = []
pc2Button = []


client_PC1 = None
client_PC2 = None

rateA1Canvas = []; rateA1Line = []; rmaxA1Text = []; rateA1Label = []
rateB1Canvas = []; rateB1Line = []; rmaxB1Text = []; rateB1Label = []

rateA2Canvas = []; rateA2Line = []; rmaxA2Text = []; rateA2Label = []
rateB2Canvas = []; rateB2Line = []; rmaxB2Text = []; rateB2Label = []

# Quick Rates
quickRates1Button = []
def quickRates1_on():
	quickRates1Button.config(text="Stop quick", bg="#fa857a")
def quickRates1_off():
	quickRates1Button.config(text="Start quick", bg="#e8fcae")
quickRates2Button = []
def quickRates2_on():
	quickRates2Button.config(text="Stop quick", bg="#fa857a")
def quickRates2_off():
	quickRates2Button.config(text="Start quick", bg="#e8fcae")
# File Rates
fileRates1Button = []
def fileRates1_on():
	fileRates1Button.config(text="Stop File", bg="#fa857a")
def fileRates2_off():
	fileRates2Button.config(text="Start File", bg="#e8fcae")
fileRates2Button = []
def fileRates2_on():
	fileRates2Button.config(text="Stop File", bg="#fa857a")
def fileRates2_off():
	fileRates2Button.config(text="Start File", bg="#e8fcae")


rmaxA1 = 1
rmaxB1 = 1
rmaxA2 = 1
rmaxB2 = 1

# For rate bar
r_width  = 20
r_height = 500
## Calculate positions of rate lines and place them there
def placeRateLineA1(rate):
	lineposition = r_height - (rate/rmaxA1 * 0.8 * r_height)
	rateA1Canvas.coords(rateA1Line, 0, lineposition, r_width, lineposition)
def placeRateLineB1(rate):
	lineposition = r_height - (rate/rmaxB1 * 0.8 * r_height)
	rateB1Canvas.coords(rateB1Line, 0, lineposition, r_width, lineposition)
def placeRateLineA2(rate):
	lineposition = r_height - (rate/rmaxA2 * 0.8 * r_height)
	rateA2Canvas.coords(rateA2Line, 0, lineposition, r_width, lineposition)
def placeRateLineB2(rate):
	lineposition = r_height - (rate/rmaxB2 * 0.8 * r_height)
	rateB2Canvas.coords(rateB2Line, 0, lineposition, r_width, lineposition)


responsesLabel = []
responsetimesLabel = []
ndevices = 0