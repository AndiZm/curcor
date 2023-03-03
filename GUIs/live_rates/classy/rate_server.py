import socket as soc
import threading
import time
import configparser
from threading import Thread

#import live_header as header
import globals as gl
#import transfer_files as tf


class server:

	#length of each rate information. In the used protocol the length of the message is the no of valid numbers of the MHz measurement +1 times 2 (two channels A and B) + 1 character for the seperator.
	msg_length = 13
	
	#listening port and address for the server
	port = 0000 
	address = ""
	connections = 1
	
	#socket used for the serversocket
	serversocket = None
	listen_thread = None
	still_listening = True;
	
	#list of client sockets to send to
	clientsockets = []
	
	def __init__(self, port, tel_number):

		self.port = port
		self.tel_number = int(tel_number)
		#check if config file exists and load it, otherwise standard parameters are kept
		global_config = configparser.ConfigParser()
		global_config.read('../../global.conf')
		# get the rate transmission length
		if "rate_transmission" in global_config:
			self.msg_length=int(global_config["rate_transmission"]["msg_length"])
		else:
			print("Error in the 'global.config'-file. The file does not contain the section 'rate_transmission'. Please correct!")
			exit()
		# get the controller's IP address
		if "controller" in global_config:
			self.address=str(global_config["controller"]["address"])
		else:
			print("Error in the 'global.config'-file. The file does not contain the section 'controller'. Please correct!")
			exit()
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
			#self.listen_thread = threading.Thread(target=listen, args=[self])
			self.listen_thread = threading.Thread(target=self.listen, args=[self.tel_number])
			self.still_listening=True
			self.listen_thread.start()
			if self.listen_thread != None:
				print("Server listens on Port {0} IP {1} for Motor!".format(self.port, self.address))	
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
			#print (i)
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

	def listen(self, tel_number):
		while self.still_listening:
			# accept connections from outside. The OSError exception ist thrown, when the server is shutdown, becaus the accept routine can't handle well that the socket is closed by another thread.
			try:
				#get new clientsocket from the listening server socket
				(clientsocket, address) = self.serversocket.accept()
				
				# create a new thread for each client and put it in the list of clientsockets
				ct = clientsocket
				self.clientsockets=[]
				self.clientsockets.append(ct)
				print (self)
				print (self.clientsockets)
				print("Created new client socket for new client which connected to the rate server!")
				gl.motorServerButton[tel_number].config(bg="#bfff91")
			except OSError:
				if self.still_listening :
					print("There was an error in the accept() statement of the server while listening for incoming connections. How could that be?")
				else:
					print("Successfully ended the server-listening thread!")


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
				gl.remoteMeasName  = data.split("#")[2]
				gl.remoteMeasIndex = int(data.split("#")[3])
				gl.remoteMeasButton.invoke()
			if "init_meas" in data.split("#")[1]:
				gl.syncedMeasButton.invoke()
				header.write_header(name=data.split("#")[2])
			if "start_loop" in data.split("#")[1]:
				gl.statusLabel.config(text="Remote Measurement", bg="#ff867d")
				gl.remoteMeasButton.config(state="normal")
			if "stop_loop" in data.split("#")[1]:
				gl.statusLabel.config(text="Idle", bg="#ffffff")
				gl.remoteMeasButton.config(state="disabled")
				gl.copythread = Thread(target=tf.transfer_files, args=(gl.remoteFiles,"Z:\\"+gl.projectName))
				gl.copythread.start()
				gl.remoteFiles = []