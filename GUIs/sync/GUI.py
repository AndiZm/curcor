from tkinter import *
import server
import globals as gl

root = Tk(); root.wm_title("Measurement Synchronization")

rootMainFrame = Frame(root); rootMainFrame.grid(row=0,column=0)
###########
# Buttons #
###########
ButtonFrame = Frame(rootMainFrame); ButtonFrame.grid(row=0,column=0)

startSeverButton = Button(ButtonFrame, text="Start Server", command=server.listenThread)
startSeverButton.grid(row=0,column=0)
startStopMeasButton = Button(ButtonFrame, text="Start Measurement", bg="#92f0eb")
startStopMeasButton.grid(row=1,column=0)
measurement = False
def toggle_measure():
	global measurement
	if measurement == False: # Start measurement
		measurement = True
		server.measure()
		startStopMeasButton.config(text="Stop Measurement", bg="#f2b4a0")
		mssLabel.config(text="Waiting for {} responses".format(gl.ndevices))
	elif measurement == True: # Stop measurement
		measurement = False
		server.stop()
		startStopMeasButton.config(text="Start Measurement", bg="#92f0eb")
		mssLabel.config(text="Measurement stopped")
startStopMeasButton.config(command=toggle_measure)

stopSeverButton = Button(ButtonFrame, text="Finish", command=server.finish)
stopSeverButton.grid(row=2,column=0)

###############
# Connections #
###############
connectionFrame = Frame(rootMainFrame); connectionFrame.grid(row=0, column=1)

connectedLabel = Label(connectionFrame, text="Connected Devices:"); connectedLabel.grid(row=0,column=0)
gl.connectionLabel = Label(connectionFrame, text=gl.connectionLabelText, width=30, height=5, bg="#f4f7b7"); gl.connectionLabel.grid(row=1,column=0)

measStatusLabel = Label(connectionFrame, text="Measurement Status"); measStatusLabel.grid(row=2,column=0)
measStatusFrame = Frame(connectionFrame); measStatusFrame.grid(row=3,column=0)
mssLabel = Label(measStatusFrame, text="Measurement stopped", bg="#f4f7b7"); mssLabel.grid(row=0,column=0)
gl.responsesLabel = Label(measStatusFrame, text="", bg="#d6c5f0", width=2); gl.responsesLabel.grid(row=0,column=1)


############
# Messages #
############
root.mainloop()