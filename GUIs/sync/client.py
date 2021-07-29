import threading
import socket
import os
import mouse as m
import live_wait_for_file as wff
import globals as gl
import time as t

address = "131.188.167.132"
port = 2610
basicpath = "E:/Test/data/"
samples = 2*1024**3

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
			gl.stop_wait_for_file_thread = True
			gl.cont_measurement_thread = False
		if data == "start": # Start synchronized continuous measurements
			# Start file check thread
			cm_thread = threading.Thread(target=cont_measurement, args=[])
			cm_thread.start()
	os._exit(1)

def cont_measurement():
	m.single()
	gl.stop_wait_for_file_thread = False
	file = wff.execute_single(basicpath, samples)
	print (file)
	text = "New measurement: {}".format(file)
	clientSocket.send(text.encode('utf8'))
	t.sleep(1)


listen_thread = threading.Thread(target=listen, args=[])
listen_thread.start()