import socket as soc
import time
import threading
import configparser
import globals as gl
import time as t

class controller_client:

	#info about the server to connect to
	port = 2611
	address = "131.188.167.132"
	
	#client socket that is used to connect to the rate server
	socket = None
	
	#status of the client's listening functionality
	listening = False
	#thread which executes the listening function
	listen_thread = None
	# PC ID
	pc_ID = None
	# Await response
	awaitR = False
	# Response time stamp
	timeR = None
	
	def __init__(self, connection_string):
		#check if config file exists and load it, otherwise standard parameters are kept
		config = configparser.ConfigParser()
		config.read('rate_transmission.conf')
		if connection_string in config:
			self.port=int(config[connection_string]["port_controller"])
			self.address=config[connection_string]["address"]
		if "pc1" in connection_string:
			self.pc_ID = 1
		elif "pc2" in connection_string:
			self.pc_ID = 2
		print("controller-client init completed. Configuation: addr {0} port {1}".format(self.address, self.port))

		
	#connects the rate client to the rate server
	#NEED TO ADD ERROR HANDLING!
	def connect(self):
		#create a client socket to connect to the rate server
		if self.socket is None:
			self.socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
			self.socket.settimeout(1)
			print("Connecting to {0} on port {1}".format(self.port, self.address))
			self.socket.connect((self.address, self.port))
			self.socket.settimeout(None)
			print("Client started!")	
			
			#routine to start a client thread as soon as a connection is requested (in own thread)
			self.listen_thread = threading.Thread(target=listen, args=[self])
			self.listening=True
			self.listen_thread.start()
			if self.listen_thread != None:
				print("Client connected to {1} on Port {0} and is listening!".format(self.port, self.address))	
			if self.pc_ID == 1:
				gl.pc1Button.config(text="Stop Client PC 1", bg="#bfff91")
				gl.quickRates1Button.config(state="normal", command=self.quickrates)
				gl.fileRates1Button.config(state="normal", command=self.filerates)
			if self.pc_ID == 2:
				gl.pc2Button.config(text="Stop Client PC 2", bg="#bfff91")
				gl.quickRates2Button.config(state="normal", command=self.quickrates)
				gl.fileRates2Button.config(state="normal", command=self.filerates)	
		else:
			print("Error in the connect method of the rate client! There shouldn't be a socket but in fact there is! Did you connect once too often?")

	#stops the client and closes all connections
	def stop(self):
		self.listening = False
		self.socket.shutdown(soc.SHUT_RDWR)
		self.socket.close()
		print("Shutdown the client and closed the socket!")
		self.socket = None
		if self.pc_ID == 1:
			gl.quickRates1Button.config(state="disabled")
			gl.fileRates1Button.config(state="disabled")
		if self.pc_ID == 2:
			gl.quickRates2Button.config(state="disabled")
			gl.fileRates2Button.config(state="disabled")
	def stop_self(self):
		sendText(self, "clientstop")
	# Commands to the server
	def quickrates(self):
		sendText(self, "command # quickrates #")
	def filerates(self):
		sendText(self, "command # filerates #")
	def meas_single(self, name):
		sendText(self, "command # meas_single # {} #".format(name))
		self.awaitR = True
	def init_meas(self, name):
		sendText(self, "command # init_meas # {} #".format(name))

	
#makes the client listen to incoming messages
def listen(self):
	while self.listening:
		data = str(self.socket.recv(1024).decode())
		#print (data)
		if data == "serverstop":
			print ("\tClosing Client and exit ...")
			#self.socket.send(b"OK, I will exit. Bye!")
			self.stop()
			if self.pc_ID == 1:
				gl.client_PC1 = None
				gl.pc1Button.config(text="Start Client PC 1", bg="#cdcfd1")
			if self.pc_ID == 2:
				gl.client_PC2 = None
				gl.pc2Button.config(text="Start Client PC 2", bg="#cdcfd1")
		# Rate
		if "rates" in data.split("#")[0]:
			self.awaitR = False; self.timeR = t.time()
			update_rates(self, data)			
		if "rate " in data.split("#")[0]:
			self.awaitR = False; self.timeR = t.time()
			update_rate(self, data)
		# Max rate
		if "maxrs" in data.split("#")[0]:
			update_max_rates(self, data)
		if "maxr " in data.split("#")[0]:
			update_max_rate(self, data)
		# Information update
		if "actions" in data.split("#")[0]:
			update_information(self, data)

# Rate
def update_rates(self,data):
	data = data.split("#")
	r_a = float(data[1])
	r_b = float(data[2])
	if self.pc_ID == 1:
		gl.lastA1.append(r_a); gl.lastB1.append(r_b)
		gl.rateA1Label.config(text="{:.1f}".format(r_a))
		gl.rateB1Label.config(text="{:.1f}".format(r_b))
		gl.placeRateLineA1(r_a)
		gl.placeRateLineB1(r_b)
		gl.wait1Canvas.itemconfig(gl.wait1LED, fill="green")
	if self.pc_ID == 2:
		gl.lastA2.append(r_a); gl.lastB2.append(r_b)
		gl.rateA2Label.config(text="{:.1f}".format(r_a))
		gl.rateB2Label.config(text="{:.1f}".format(r_b))
		gl.placeRateLineA2(r_a)
		gl.placeRateLineB2(r_b)
		gl.wait2Canvas.itemconfig(gl.wait2LED, fill="green")
def update_rate(self,data):
	data = data.split("#")
	r_a = float(data[1])
	if self.pc_ID == 1:
		gl.lastA1.append(r_a)
		gl.rateA1Label.config(text="{:.1f}".format(r_a))
		gl.rateB1Label.config(text="-.-")
		gl.placeRateLineA1(r_a)
	if self.pc_ID == 2:
		gl.lastA2.append(r_a)
		gl.rateA2Label.config(text="{:.1f}".format(r_a))
		gl.rateB2Label.config(text="-.-")
		gl.placeRateLineA2(r_a)
# Max rate
def update_max_rates(self, data):
	data = data.split("#")
	if self.pc_ID == 1:
		gl.rmaxA1 = float(data[1])
		gl.rmaxB1 = float(data[2])
		gl.rateA1Canvas.itemconfig(gl.rmaxA1Text, text="{:.0f}".format(gl.rmaxA1))
		gl.rateB1Canvas.itemconfig(gl.rmaxB1Text, text="{:.0f}".format(gl.rmaxB1))
	if self.pc_ID == 2:
		gl.rmaxA2 = float(data[1])
		gl.rmaxB2 = float(data[2])
		gl.rateA2Canvas.itemconfig(gl.rmaxA2Text, text="{:.0f}".format(gl.rmaxA2))
		gl.rateB2Canvas.itemconfig(gl.rmaxB2Text, text="{:.0f}".format(gl.rmaxB2))
def update_max_rate(self, data):
	data = data.split("#")
	if self.pc_ID == 1:
		gl.rmaxA1 = float(data[1])
		gl.rateA1Canvas.itemconfig(gl.rmaxA1Text, text="{:.0f}".format(gl.rmaxA1))
	if self.pc_ID == 2:
		gl.rmaxA2 = float(data[1])
		gl.rateA2Canvas.itemconfig(gl.rmaxA2Text, text="{:.0f}".format(gl.rmaxA2))
def update_information(self, data):
	# quick Rates active
	if "True" in data.split("#")[1]:
		if self.pc_ID == 1:
			gl.quickRates1_on()
		if self.pc_ID == 2:
			gl.quickRates2_on()
	if "False" in data.split("#")[1]:
		if self.pc_ID == 1:
			gl.quickRates1_off()
		if self.pc_ID == 2:
			gl.quickRates2_off()
	# file Rates active
	if "True" in data.split("#")[2]:
		if self.pc_ID == 1:
			gl.fileRates1_on()
		if self.pc_ID == 2:
			gl.fileRates2_on()
	if "False" in data.split("#")[2]:
		if self.pc_ID == 1:
			gl.fileRates1_off()
		if self.pc_ID == 2:
			gl.fileRates2_off()



def sendText(self, text):
	text = text.encode("utf8")
	self.socket.send(text)
