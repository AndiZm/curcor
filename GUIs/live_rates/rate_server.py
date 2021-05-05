import socket as soc

class server:
	
	#declare global variables. Note that these might be changed at initialization of the server object
	
	#listening port and address for the server
	port = 2610 
	address = ""
	connections = 1
	
	#socket used for the serversocket
	serversocket = None
	
	#list of client sockets to send to
	clientsockets = []
	

	def __init__(self):
		#check if config file exists and load it, otherwise standard parameters are kept
		return
			
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
			
			#routine to start a client thread as soon as a connection is requested
			while True:
				# accept connections from outside
				(clientsocket, address) = self.serversocket.accept()
				
				# create a new thread for each client and put it in the list of clientsockets
				ct = client_thread(clientsocket)
				ct.run()
				self.clientsockets.append(ct)
		else:
			print("Server already started")
			return
        
        
		
	def sendRate(self, rate):
		for i in self.clientsockets:
			sent = i.send(rate)
			if sent == 0:
				print("The Socket connection on one of the sockets is broken. Socket will be eliminated")
				i.shutdown()
				i.close()
				self.clientsockets.remove(i)
