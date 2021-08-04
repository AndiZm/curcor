import threading
import socket
import time as t
import globals as gl

address = ""
port = 2610
connections = 5

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#serverSocket.bind((socket.gethostname(), port))
serverSocket.bind(("131.188.167.97", port))
serverSocket.listen(connections)

listening = True
clientsockets = []; addresses = []

def send(text):
	global clientsockets
	text=text.encode('utf8')
	for i in clientsockets:
		try:
			sent = i.send(text)
			if sent == 0:
				print("The socket connection on one of the sockets is broken. Socket will be eliminated")
				#i.shutdown(soc.SHUT_RDWR)
				i.close()
				clientsockets.remove(i)
		except ConnectionAbortedError:
			print("The socket connection on one of the sockets is broken. Socket will be eliminated")
			#i.shutdown(soc.SHUT_RDWR)
			i.close()
			clientsockets.remove(i)
		except ConnectionResetError:
			print("The socket connection on one of the sockets is broken. Socket will be eliminated")
			#i.shutdown(soc.SHUT_RDWR)
			i.close()
			clientsockets.remove(i)

def ping():
	send("ping")

def listen():
	global listening, listening_msg, clientsockets, responses
	print ("Server started, is listening to new connections")
	while listening:
		# accept connections from outside. The OSError exception ist thrown, when the server is shutdown, because the accept routine can't handle well that the socket is closed by another thread.
		try:
			#get new clientsocket from the listening server socket
			(clientsocket, address) = serverSocket.accept()
			
			# create a new thread for each client and put it in the list of clientsockets
			ct = clientsocket; add = address
			ct.send("You have been accepted!".encode('utf8'))
			clientsockets.append(ct); addresses.append(address)
			print("New client connected to the server! ({})".format(address))
			newthread = threading.Thread(target=listen_msg_from, args=[len(clientsockets)-1])
			newthread.start()
			gl.connectionLabelText += "\n" + str(address)
			gl.connectionLabel.config(text=gl.connectionLabelText)
			gl.ndevices += 1

		except OSError:
			if listening :
				print("There was an error in the accept() statement of the server while listening for incoming connections. How could that be?")
			else:
				print("Successfully ended the server-listening thread!")
def listenThread():
	listen_thread = threading.Thread(target=listen, args=[])
	listen_thread.start()

listening_msg = True
gl.responses = 0 # Will increase if clients send measurement
def listen_msg_from(client):
	global listening_msg, clientsockets
	print ("Server listens now to messages from {}".format(addresses[client]))
	while listening_msg:
			data = str(clientsockets[client].recv(1024).decode())
			print ("Received message from {}: {}".format(addresses[client], data))
			if "New measurement" in data:
				gl.responses += 1; gl.response_times.append(t.time())
				gl.responsesLabel.config(text=str(gl.responses))
	print ("Server stops listening to messages from {}".format(addresses[client]))

def finish():
	global listening, clientsockets, listening_msg
	listening = False; listening_msg = False
	t.sleep(1)
	send("exit")
	t.sleep(1)
	for i in clientsockets:
		i.shutdown(socket.SHUT_RDWR)
		i.close()
		clientsockets.remove(i)
	serverSocket.close()
	exit()

# Do a continuous measurement and wait each time for response
measure_thread = False
def measureT():
	global measure_thread, clientsockets
	measure_thread = True
	while measure_thread == True:
		gl.responses = 0; gl.response_times = []
		gl.responsesLabel.config(text=str(gl.responses))
		send("start")
		while gl.responses < len(clientsockets):
			pass
		t_diff = gl.response_times[-1] - gl.response_times[0]
		#print ("Time between responses:\t{:.2f} s".format(t_diff))
		gl.responsetimesLabel.config(text="{:.2f} s".format(t_diff))
		t.sleep(0.2)

def measure():
	m_thread = threading.Thread(target=measureT, args=[])
	m_thread.start()

def stop():
	global measure_thread
	measure_thread = False
