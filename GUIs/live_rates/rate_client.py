import socket as soc
from time import sleep
import threading
import configparser

class controller_client:

	#info about the server to connect to
	port = 2611
	address = "131.188.167.132"
	
	#client socket that is used to connect to the rate server
	socket = None
	
	#status of the client's listening functionality
	still_listening = False
	#thread which executes the listening function
	listen_thread = None

	
	def __init__(self, connection_string):
		#check if config file exists and load it, otherwise standard parameters are kept
		config = configparser.ConfigParser()
		config.read('rate_transmission.conf')
		if connection_string in config:
			self.port=int(config[connection_string]["port"])
			self.address=config[connection_string]["address"]
		print("rate-client inti completed. Configuation: addr {0} port {1}".format(self.address, self.port))

		
	#connects the rate client to the rate server
#NEED TO ADD ERROR HANDLING!
	def connect(self):
		#create a client socket to connect to the rate server
		if self.socket is None:
			self.socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
			self.socket.settimeout(1)
			print("Connecing to {0} on port {1}".format(self.port, self.address))
			self.socket.connect((self.address, self.port))
			self.socket.settimeout(None)
			print("Client started!")	
			
			#routine to start a client thread as soon as a connection is requested (in own thread)
			#self.listen_thread = threading.Thread(target=listen, args=[self])
			#self.still_listening=True
			#self.listen_thread.start()
			#if self.listen_thread != None:
			#	print("Client connected to {1} on Port {0} and is listening!".format(self.port, self.address))	
		else:
			print("Error in the connect method of the rate client! There shouldn't be a socket but in fact there is! Did you connect once too often?")

	listening = True
	def listen(self):
		while self.listening:
			data = str(self.socket.recv(1024).decode())
			print (data)
			if data == "exit":
				print ("\tClosing Client and exit ...")
				#self.socket.send(b"OK, I will exit. Bye!")
				self.socket.shutdown(socket.SHUT_RDWR)
				self.socket.close()
				self.listening = False
			#if data == "ping":
			#	clientSocket.send(b"Still online!")
			#if data == "single":
			#	m.single()
			#if data == "loop":
			#	m.loop()
			#if data == "stop":
			#	m.stop()
			#	gl.stop_wait_for_file_thread = True
			#	gl.cont_measurement_thread = False
			#if data == "start": # Start synchronized continuous measurements
			#	# Start file check thread
			#	cm_thread = threading.Thread(target=cont_measurement, args=[])
			#	cm_thread.start()
		os._exit(1)
		

#	#returns the value of the last rate in channel A transmitted
#	def getRateA(self):
#		if self.rateA != None:
#			if self.still_listening:
#				return self.rateA
#			else:
##				print("TEST")
#				raise RuntimeError("Connection to server lost!")
#		else:
#			#print("No rate has yet been received")
#			return -1
#			
#
#	#returns the value of the last rate in channel B transmitted
#	def getRateB(self):
#		if self.rateB != None:
#			if self.still_listening:
#				return self.rateB
#			else:
#				raise RuntimeError("Connection to server lost!")
#		else:
#			#print("No rate has yet been received")
#			return -1
#
	#stops the client and closes all connections
	def stop(self):
		self.socket.shutdown(soc.SHUT_RDWR)
		self.socket.close()
		print("Shutdown the client and closed the socket!")
		self.socket = None;
	
#makes the client listen to incoming rates
#def listen(self):
#	while self.still_listening:
#		chunks = []
#		bytes_recd = 0
#		while bytes_recd < self.msg_length:
#			chunk = self.socket.recv(min(self.msg_length - bytes_recd, 2048))
#			if chunk == b'':
#				if self.socket != None:
#					print("Socket connection broken. Destroyed on purpose?")
#					self.still_listening = False
#					break
#			chunks.append(chunk)
#			bytes_recd = bytes_recd + len(chunk)
#		if self.still_listening == False:
#			break
#		org=str(b''.join(chunks))
#		parts=org.split(";")
#		self.rateA=float(parts[0].split("'")[1])
#		self.rateB=float(parts[1].split("'")[0])
