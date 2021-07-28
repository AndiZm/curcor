import threading
import socket
import os
import mouse as m

address = "131.188.167.97"
port = 2610

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((address,port))

listening = True
def listen():
	global listening
	while listening:
		data = str(clientSocket.recv(1024).decode())
		print (data)
		if data == "exit":
			print ("\tClosing Client and exit ...")
			clientSocket.send(b"OK, I will exit. Bye!")
			clientSocket.shutdown(socket.SHUT_RDWR)
			clientSocket.close()
			listening = False
		if data == "ping":
			clientSocket.send(b"Still online!")
		if data == "single":
			m.single()
		if data == "loop":
			m.loop()
		if data == "stop":
			m.stop()
	os._exit(1)

listen_thread = threading.Thread(target=listen, args=[])
listen_thread.start()