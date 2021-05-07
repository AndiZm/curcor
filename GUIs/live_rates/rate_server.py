import socket as soc
import threading
import time

class server:
	
	#declare global variables. Note that these might be changed at initialization of the server object
	
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
		return
	
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
				print("Server listens on Port {0} !".format(self.port))	
		else:
			print("Server already started")
			return
    
    #stops the server by closing the listening and all client sockets and destroying them
	def stop(self):
		#stop the thread that listens
		server_cache=self.serversocket
		self.serversocket=None
		self.still_listening=False
		#soc.socket(soc.AF_INET, soc.SOCK_STREAM).connect( (soc.hostname, server_cache.port))
#		time.sleep(0.3)
		server_cache.shutdown(soc.SHUT_RDWR)
		server_cache.close()
		for i in self.clientsockets:
			i.shutdown(soc.SHUT_RDWR)
			i.close()
			self.clientsockets.remove(i)
		print("Shutdown the server and closed all sockets!")
				
	def sendRate(self, rate):
		for i in self.clientsockets:
			sent = i.send(rate)
			if sent == 0:
				print("The Socket connection on one of the sockets is broken. Socket will be eliminated")
				i.shutdown(soc.SHUT_RDWR)
				i.close()
				self.clientsockets.remove(i)
				
def listen(self):
	while self.still_listening:
		# accept connections from outside. The OSError exception ist thrown, when the server is shutdown, becaus the accept routine can't handle well that the socket is closed by another thread.
		try:
			#get new clientsocket from the listening server socket
			(clientsocket, address) = self.serversocket.accept()
			
			# create a new thread for each client and put it in the list of clientsockets
			ct = client_thread(clientsocket)
			ct.run()
			self.clientsockets.append(ct)
		except OSError:
			if self.still_listening :
				print("There was an error in the accept() statement of the server while listening for incoming connections. How could that be?")
			else:
				print("Successfully ended the server-listening thread!")
				
		
