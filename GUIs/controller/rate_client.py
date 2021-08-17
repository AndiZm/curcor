import socket as soc
import time
import threading
import configparser
import globals as gl

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
			if self.pc_ID == 2:
				gl.pc2Button.config(text="Stop Client PC 2", bg="#bfff91")
		else:
			print("Error in the connect method of the rate client! There shouldn't be a socket but in fact there is! Did you connect once too often?")

	#stops the client and closes all connections
	def stop(self):
		self.listening = False
		self.socket.shutdown(soc.SHUT_RDWR)
		self.socket.close()
		print("Shutdown the client and closed the socket!")
		self.socket = None
	def stop_self(self):
		sendText(self, "clientstop")
	
#makes the client listen to incoming messages
def listen(self):
	while self.listening:
		data = str(self.socket.recv(1024).decode())
		print (data)
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

def sendText(self, text):
	text = text.encode("utf8")
	self.socket.send(text)
