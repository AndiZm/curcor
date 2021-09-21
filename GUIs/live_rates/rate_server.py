import socket as soc
import threading
import time
import configparser
import globals as gl


class server:

	#length of each rate information. In the used protocol the length of the message is the no of valid numbers of the MHz measurement +1 times 2 (two channels A and B) + 1 character for the seperator.
	msg_length = 13
	
	#listening port and address for the server
	port = 2610 
	address = ""
	connections = 1
	
	#socket used for the serversocket
	serversocket = None
	listen_thread = None
	still_listening = True;
	
	#list of client sockets to send to
	clientsockets = []
	

	def __init__(self):
		#check if config file exists and load it, otherwise standard parameters are kept
		config = configparser.ConfigParser()
		config.read('rate_transmission.conf')
		if "connection" in config:
			self.port=int(config["connection"]["port_motor"])
			self.address=config["connection"]["address"]
			self.msg_length=int(config["connection"]["msg_length"])
	
	#starts the server by opening a listening socket			
	def start(self):
		#Check if server is already running
		if self.serversocket is None:
			self.serversocket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
			# create an INET, STREAMing socket
        
			# bind the socket to a host and port
			if self.address=="":
				self.serversocket.bind((soc.gethostname(), self.port))
			else:
				self.serversocket.bind((self.address, self.port))
				
			# make it a server socket that allows for a certain number of connections
			self.serversocket.listen(self.connections)
			
			print("Server started!")	
			
			#routine to start a client thread as soon as a connection is requested (in own thread)
			self.listen_thread = threading.Thread(target=listen, args=[self])
			self.still_listening=True
			self.listen_thread.start()
			if self.listen_thread != None:
				print("Server listens on Port {0} for Motor!".format(self.port))	
		else:
			print("Server already started")
			return
    
    #stops the server by closing the listening and all client sockets and destroying them
	def stop(self):
		#stop the thread that listens
		server_cache=self.serversocket
		self.serversocket=None
		self.still_listening=False
	#	server_cache.shutdown(soc.SHUT_RDWR)
		server_cache.close()
		for i in self.clientsockets:
			i.shutdown(soc.SHUT_RDWR)
			i.close()
			self.clientsockets.remove(i)
		print("Shutdown the server and closed all sockets!")

	def sendRate(self, rate_a, rate_b):
		rate = "{0:6.1f};{1:6.1f}".format(rate_a, rate_b)
		if len(rate) != self.msg_length :
			print("The rate (which was supposed to be sent) had the wrong length! The configured msg_length is {0} but the one given as a parameter '{1}' had length {2}".format(self.msg_length, rate, len(rate)))
			return
		rate=rate.encode('utf8');
		for i in self.clientsockets:
			try:
				sent = i.send(rate)
				if sent == 0:
					print("The socket connection on one of the sockets is broken. Socket will be eliminated")
#					i.shutdown(soc.SHUT_RDWR)
					i.close()
					self.clientsockets.remove(i)
			except ConnectionAbortedError:
				print("The socket connection on one of the sockets is broken. Socket will be eliminated")
#				i.shutdown(soc.SHUT_RDWR)
				i.close()
				self.clientsockets.remove(i)
			except ConnectionResetError:
				print("The socket connection on one of the sockets is broken. Socket will be eliminated")
#				i.shutdown(soc.SHUT_RDWR)
				i.close()
				self.clientsockets.remove(i)

class server_controller:
	
	#listening port and address for the server
	port = 26101
	address = ""
	connections = 1
	
	#socket used for the serversocket
	serversocket = None
	listen_thread = None
	listening_accept = False
	listening_msg = False
	
	#client socket to send to. We only will have one (the controller)
	clientsocket = None
	

	def __init__(self):
		#check if config file exists and load it, otherwise standard parameters are kept
		config = configparser.ConfigParser()
		config.read('rate_transmission.conf')
		if "connection" in config:
			self.port=int(config["connection"]["port_controller"])
			self.address=config["connection"]["address"]
	
	#starts the server by opening a listening socket			
	def start(self):
		#Check if server is already running
		if self.serversocket is None:
			self.serversocket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
			# create an INET, STREAMing socket
        
			# bind the socket to a host and port
			if self.address=="":
				self.serversocket.bind((soc.gethostname(), self.port))
			else:
				self.serversocket.bind((self.address, self.port))
				
			# make it a server socket that allows for a certain number of connections
			self.serversocket.listen(self.connections)
			
			print("Server started!")	
			
			#routine to start a client thread as soon as a connection is requested (in own thread)
			self.listen_thread = threading.Thread(target=listen_accept, args=[self,gl.controllerServerButton])
			self.listening_accept = True
			self.listen_thread.start()
			if self.listen_thread != None:
				print("Server listens on Port {0} for Controller!".format(self.port))

		else:
			print("Server already started")
			return

	def sendText(self, text):
		text=text.encode('utf8')
		if self.clientsocket != None:
			sent = self.clientsocket.send(text)
	def sendRate(self, rate_a):
		text = "rate # {}".format(rate_a)
		self.sendText(text)
	def sendRates(self, rate_a, rate_b):
		text = "rates # {} # {} #".format(rate_a, rate_b)
		self.sendText(text)
	def sendMaxRate(self,rate_a):
		text="maxr # {} #".format(rate_a)
		self.sendText(text)
	def sendMaxRates(self,rate_a, rate_b):
		text="maxrs # {} # {} #".format(rate_a, rate_b)
		self.sendText(text)
	def sendActionInformation(self):
		text="actions # {} # {} #".format(gl.act_start_quick, gl.act_start_file)
		self.sendText(text)

    
    #stops the server by closing the listening and all client sockets and destroying them
	def stop(self):
		self.listening_accept = False
		self.listening_msg = False
		self.sendText("serverstop")
		time.sleep(0.5)
		#stop the thread that listens
		server_cache = self.serversocket
		self.serversocket = None
		server_cache.close()
		if self.clientsocket != None:
			self.clientsocket.shutdown(soc.SHUT_RDWR)
			self.clientsocket.close()
			self.clientsocket = None
		print("Shutdown the server and closed the socket!")

# Wait for incoming client requests and accept
def listen_accept(self,button):
	while self.listening_accept:
		# accept connections from outside. The OSError exception ist thrown, when the server is shutdown, becaus the accept routine can't handle well that the socket is closed by another thread.
		try:
			#get new clientsocket from the listening server socket
			(clientsocket, address) = self.serversocket.accept()
			
			# create a new thread for each client and put it in the list of clientsockets
			ct = clientsocket
			self.clientsocket = ct
			print("Created new client socket for new client which connected to the rate server!")
			button.config(bg="#bfff91")

			# Send rate limit info to controller
			send_start_information(self)

			#listen to messages from this client
			self.listen_msg_thread = threading.Thread(target=listen_msg, args=[self, button])
			self.listening_msg = True
			self.listen_msg_thread.start()

		except OSError:
			if self.listening_accept :
				print("There was an error in the accept() statement of the server while listening for incoming connections. How could that be?")
			else:
				print("Successfully ended the server-listening thread!")
def send_start_information(self):
	if gl.rmax_a != None:
		if gl.o_nchn == 1:
			self.sendMaxRate(gl.rmax_a)
		if gl.o_nchn == 2:
			self.sendMaxRates(gl.rmax_a, gl.rmax_b)
	time.sleep(0.1)
	self.sendActionInformation()

def listen_msg(self, button):
	while self.listening_msg:
		data = str(self.clientsocket.recv(1024).decode())
		print (data)
		# If client requests stop, then do so
		if data == "clientstop":
			self.sendText("serverstop")
			if self.clientsocket != None:
				self.clientsocket.shutdown(soc.SHUT_RDWR)
				self.clientsocket.close()
				self.clientsocket = None
			self.listening_msg = False
			button.config(bg="#ffc47d")
		if "command" in data.split("#")[0]:
			if "quickrates" in data.split("#")[1]:
				gl.quickRatesButton.invoke()
			if "filerates" in data.split("#")[1]:
				gl.startstopButton.invoke()
			if "meas_single" in data.split("#")[1]:
				#m.single()
				print ("Not supported yet")
		
def listen(self):
	while self.still_listening:
		# accept connections from outside. The OSError exception ist thrown, when the server is shutdown, becaus the accept routine can't handle well that the socket is closed by another thread.
		try:
			#get new clientsocket from the listening server socket
			(clientsocket, address) = self.serversocket.accept()
			
			# create a new thread for each client and put it in the list of clientsockets
			ct = clientsocket
			self.clientsockets.append(ct)
			print("Created new client socket for new client which connected to the rate server!")
		except OSError:
			if self.still_listening :
				print("There was an error in the accept() statement of the server while listening for incoming connections. How could that be?")
			else:
				print("Successfully ended the server-listening thread!")