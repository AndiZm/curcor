import socket as soc
from time import sleep
import threading

class rate_client:

	#length of each rate information. In the used protocol the length of the message is the no of valid numbers of the MHz measurement +1 times 2 (two channels A and B) + 1 character for the seperator.
	msg_length = 13

	#info about the server to connect to
	port = 2610 
	address = "127.0.1.1"#"192.168.0.103"
	
	#client socket that is used to connect to the rate server
	socket = None
	
	#status of the client's listening functionality
	still_listening = False
	#thread which executes the listening function
	listen_thread = None
	
	#value of the last transmitted rates
	rateA = None
	rateB = None
	
	def __init__(self):
		#check if config file exists and load it, otherwise standard parameters are kept
		return
		
	#connects the rate client to the rate server
#NEED TO ADD ERROR HANDLING!
	def connect(self):
		#create a client socket to connect to the rate server
		if self.socket is None:
			self.socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
			self.socket.connect((self.address, self.port))
			print("Client started!")	
			
			#routine to start a client thread as soon as a connection is requested (in own thread)
			self.listen_thread = threading.Thread(target=listen, args=[self])
			self.still_listening=True
			self.listen_thread.start()
			if self.listen_thread != None:
				print("Client connected to {1} on Port {0} and is listening!".format(self.port, self.address))	
		else:
			print("Error in the connect method of the rate client! There shouldn't be a socket but in fact there is! Did you connect once too often?")
		

	#returns the value of the last rate in channel A transmitted
	def getRateA(self):
		if self.rateA != None:
			return self.rateA
		else:
			print("No rate has yet been received")
			return -1
			

	#returns the value of the last rate in channel B transmitted
	def getRateB(self):
		if self.rateB != None:
			return self.rateB
		else:
			print("No rate has yet been received")
			return -1
	
	
#makes the client listen to incoming rates
def listen(self):
	while True:
		chunks = []
		bytes_recd = 0
		while bytes_recd < self.msg_length:
			chunk = self.socket.recv(min(self.msg_length - bytes_recd, 2048))
			if chunk == b'':
				raise RuntimeError("socket connection broken")
			chunks.append(chunk)
			bytes_recd = bytes_recd + len(chunk)
		org=str(b''.join(chunks))
		print(org)
		parts=org.split(";")
		self.rateA=float(parts[0].split("'")[1])
		self.rateB=float(parts[1].split("'")[0])
