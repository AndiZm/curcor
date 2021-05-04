from tkinter import *
from tkinter import messagebox
from numpy import random
from time import sleep
import stepper_drive as sd
import motor_switch as ms
import _thread
from threading import Thread
from PIL import Image
import os

# Get motors
a=sd.init()

microsteps_nano = 32

microsteps_standa = 32
offset_standa = 512000

LEDColors = []
LEDColors.append("#737373") #Resting
LEDColors.append("#ff6600") #Moving
LEDColors.append("#ff0000") #Warning

WarningStatus=[]
for i in range (0,6):
    WarningStatus.append(0)

lastpositions=[]
readpos = open("stepper_items/current_positions.txt","r")
for line in readpos:
    lastpositions.append(float(line))

def degree_to_mm(degree):
    return (8./9.)*degree #8mm/9°
    
def mm_to_degree(mm):
    return (9./8.)*mm #9°/8mm

def steps_to_degree(steps):
    return mm_to_degree(steps/(800.*microsteps_standa))-4.5  #1mm /800step*microsteps_standa

def degree_to_steps(degree): #800step*microsteps_standa / 1mm
    return int(degree_to_mm(degree+4.5)*800*microsteps_standa)

def steps_to_mm(steps):
    return steps/(200.*microsteps_nano) #1mm / 200steps*microsteps_nano

def mm_to_steps(mm):
    return int(mm*200*microsteps_nano) #200steps*microsteps_nano / 1mm

#Für Höhenmotor
def steps_to_hmm(steps):
    return steps/(200.*microsteps_nano) #CHANGE

def hmm_to_steps(mm):
    return int(mm*200*microsteps_nano) #CHANGE



root = Tk()
root.wm_title("II Motor Control")
root.config(background = "#003366")


mirror_z_pos = DoubleVar()
mirror_height_pos = DoubleVar()
mirror_phi_pos = DoubleVar()
mirror_psi_pos = DoubleVar()
camera_x_pos = DoubleVar()
camera_z_pos = DoubleVar()



def callback2(moveto):
    print(moveto)
    
def stop_all():
    for motor in a:
        motor.stop()
    for i in range (0,6):
        if sd.ismoving(a[i]) == 1:
            WarningStatus[i] = 1
    print("Stop all motors!")

    
def exitGUI():
    savepos = open("stepper_items/current_positions.txt","w")
    for i in range (0,3):
        savepos.write(str(steps_to_mm(sd.position(a[i])))+"\n")
    savepos.write(str(steps_to_hmm(sd.position(a[3])))+"\n")
    for i in range (4,6):
        savepos.write(str(steps_to_degree(sd.position(a[i])))+"\n")        
    savepos.close()
    root.destroy()

def save_this_position():
    thispos = open("stepper_items/saved_position.txt","w")
    for i in range (0,3):
        thispos.write(str(steps_to_mm(sd.position(a[i])))+"\n")
    thispos.write(str(steps_to_hmm(sd.position(a[3])))+"\n")
    for i in range (4,6):
        thispos.write(str(steps_to_degree(sd.position(a[i])))+"\n")

def goto_saved_position():
    thispositions = []
    readpos = open("stepper_items/saved_position.txt","r")
    for line in readpos:
        thispositions.append(float(line))
    CameraZ.set(thispositions[0])
    CameraX.set(thispositions[1])
    MirrorZ.set(thispositions[2])
    MirrorHeight.set(thispositions[3])
    MirrorPsi.set(thispositions[4])
    MirrorPhi.set(thispositions[5])
    moveto_camera_z(None)
    moveto_camera_x(None)
    moveto_mirror_z(None)
    moveto_mirror_height(None)
    moveto_mirror_psi(None)
    moveto_mirror_phi(None)

    
def refsearch_mirror_height():
    if(verify_command(refsearch_mirror_height.__name__)):
        return 0
    print("Searching for mirror height position 0mm")
    WarningStatus[3]=0
    a[3].reference_search(0)
    mirror_height_pos.set(0)
    
def refsearch_mirror_z():
    if(verify_command(refsearch_mirror_z.__name__)):
        return 0
    print("Searching for mirror z position 0mm")
    WarningStatus[2]=0
    a[2].reference_search(0)
    mirror_z_pos.set(0)

def refsearch_mirror_phi():
    if(verify_command(refsearch_mirror_phi.__name__)):
        return 0
    print("Searching for mirror phi position -4.5°")
    WarningStatus[5]=0
    a[5].reference_search(0)
    mirror_phi_pos.set(-4.5)    
    
def refsearch_mirror_psi():
    if(verify_command(refsearch_mirror_psi.__name__)):
        return 0
    print("Searching for mirror psi -90°")
    WarningStatus[4]=0
    a[4].reference_search(0)
    mirror_psi_pos.set(-4.5)
    
def refsearch_camera_x():
    if(verify_command(refsearch_camera_x.__name__)):
        return 0
    print("Searching for camera x-position 0mm")
    WarningStatus[1]=0
    a[1].reference_search(0)
    camera_x_pos.set(0)
    
def refsearch_camera_z():
    if(verify_command(refsearch_camera_z.__name__)):
        return 0
    print("Searching for camera z-position 0mm")
    WarningStatus[0]=0
    a[0].reference_search(0)
    camera_z_pos.set(0)
    
def refsearch_all():
    refsearch_mirror_height()
    refsearch_mirror_z()
    refsearch_mirror_phi()
    refsearch_mirror_psi()
    refsearch_camera_x()
    refsearch_camera_z()

#-----------------#
#---- Movetos ----#
#-----------------#
def moveto_mirror_height(val):
    print("Move mirror height to",mirror_height_pos.get(),"in steps",mm_to_steps(mirror_height_pos.get()))
    WarningStatus[3]=0
    a[3].move_absolute(hmm_to_steps(mirror_height_pos.get()))
   
def moveto_mirror_z(val):
    print("Move mirror z to",mirror_z_pos.get(),"in steps",mm_to_steps(mirror_z_pos.get()))
    WarningStatus[2]=0
    a[2].move_absolute(mm_to_steps(mirror_z_pos.get()))
    
def moveto_mirror_phi(val):
    print("Move mirror phi to",mirror_phi_pos.get(),"in steps",degree_to_steps(mirror_phi_pos.get()))
    WarningStatus[5]=0
    a[5].move_absolute(degree_to_steps(mirror_phi_pos.get()))
    
def moveto_mirror_psi(val):
    print("Move mirror psi to",mirror_psi_pos.get(),"in steps",degree_to_steps(mirror_psi_pos.get()))
    WarningStatus[4]=0
    a[4].move_absolute(degree_to_steps(mirror_psi_pos.get()))
    
def moveto_camera_x(val):    
    print("Move camera x to",camera_x_pos.get(), "von" , CameraX.get(),"in steps",mm_to_steps(camera_x_pos.get()))
    WarningStatus[1]=0
    a[1].move_absolute(mm_to_steps(camera_x_pos.get()))
    
def moveto_camera_z(val):
    print("Move camera z to",camera_z_pos.get(),"in steps",mm_to_steps(camera_z_pos.get()))
    WarningStatus[0]=0
    a[0].move_absolute(mm_to_steps(camera_z_pos.get()))

    
def center_camera():
    CameraX.set(150)
    moveto_camera_x(150)
    CameraZ.set(150)
    moveto_camera_z(150)
    
def center_mirror_pos():
    MirrorHeight.set(20)
    MirrorZ.set(150)
    
def center_mirror_phi():
    MirrorPhi.set(0)
    moveto_mirror_phi(0)
def center_mirror_psi():
    MirrorPsi.set(0)
    moveto_mirror_psi(0)
def center_mirror_angle():
    center_mirror_phi()
    center_mirror_psi()
    

def verify_command(command):
    if messagebox.askyesno('Verify', 'Execute command {}?'.format(command)):
        print('I will execute command {} '.format(command))
        return 0
    else:
        print('Command {} has been cancelled'.format(command))
    return 1



#----------------#
#---- Frames ----#
#----------------#
mainFrame = Frame(root, width=200, height = 400)
mainFrame.grid(row=0, column=0, padx=10,pady=3)
mainFrame.config(background = "#003366")

switchFrame = Frame(mainFrame, width=200, height=20)
switchFrame.grid(row=0,column=1, padx=10, pady=3)

MirrorTFrame = Frame(mainFrame, width=200, height=400)
MirrorTFrame.grid(row=1, column=0, padx=10, pady=3)

MirrorRFrame = Frame(mainFrame, width=200, height=400)
MirrorRFrame.grid(row=1, column=1, padx=10, pady=3)

CameraFrame = Frame(mainFrame, width=200, height=400)
CameraFrame.grid(row=1, column=2, padx=10, pady=3)

#SwitchFrame Content
ms.init(); ms.motor_on(); motoron = True
switchLabel = Label(switchFrame, text="Motor is ")
switchLabel.grid(row=0, column=0)


onoffButton = Button(switchFrame, text="ON", bg="#91CC66")
def switchMotor():
    global motoron
    if motoron == True:
        ms.motor_off(); motoron = False
        onoffButton.config(text="OFF", bg="#a3a3a3")
    else:
        ms.motor_on(); motoron = True
        onoffButton.config(text="ON", bg="#91CC66")

onoffButton.config(command=switchMotor)
onoffButton.grid(row=0, column=1)


    

#MirrorT-Content
MirrorTHeadFrame = Frame(MirrorTFrame, width=200, height=20)
MirrorTHeadFrame.grid(row=0, column=0, padx=10, pady=3)
leftLabel1 = Label(MirrorTHeadFrame, text="Mirror Height")
leftLabel1.grid(row=0, column=0, padx=10, pady=3)
MirrorHeightDisplay = Canvas(MirrorTHeadFrame, width=20,height=20)
MirrorHeightDisplay.grid(row=0, column=1, padx=3, pady=3)
MirrorHeightPositionLabel = Label(MirrorTHeadFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_degree(sd.position(a[3])),2)))
MirrorHeightPositionLabel.grid(row=0, column=2, padx=10, pady=3)

MirrorTUpperFrame = Frame(MirrorTFrame, width=200, height=300)
MirrorTUpperFrame.grid(row=1, column=0)
MirrorHeight_OSTOP = Canvas(MirrorTUpperFrame, bg=LEDColors[a[3].axis.get(10)], width=20, height=10)
MirrorHeight_OSTOP.grid(row=0, column=0)
MirrorHeight = Scale(MirrorTUpperFrame, variable=mirror_height_pos,from_=40, to=0, resolution=0.1, orient=VERTICAL, length=300)
MirrorHeight.grid(row=1, column=0, padx=10, pady=3)
MirrorHeight.bind("<ButtonRelease-1>", moveto_mirror_height)
MirrorHeight.set(lastpositions[3])
MirrorHeight_USTOP = Canvas(MirrorTUpperFrame, bg=LEDColors[a[3].axis.get(10)], width=20, height=10)
MirrorHeight_USTOP.grid(row=2, column=0)
MirrorTButtonFrame = Frame(MirrorTUpperFrame, width=100, height=150)
MirrorTButtonFrame.grid(row=1, column=1)
B1 = Button(MirrorTButtonFrame, text="Refsearch Mirror Height", bg="#D3D3D3", width=16, command=refsearch_mirror_height)
B1.grid(row=0, column=0, padx=10, pady=3) 
B2 = Button(MirrorTButtonFrame, text="Refsearch Mirror Z", bg="#D3D3D3", width=16, command=refsearch_mirror_z)
B2.grid(row=2, column=0, padx=10, pady=3)
B3 = Button(MirrorTButtonFrame, text="Center Mirror Pos", bg="#C0C0C0", width=16, command=center_mirror_pos)
B3.grid(row=1, column=0, padx=10, pady=3)

MirrorTLowerFrame = Frame(MirrorTFrame, width=200, height=20)
MirrorTLowerFrame.grid(row=2, column=0)
leftLabel2 = Label(MirrorTLowerFrame, text="Mirror Z")
leftLabel2.grid(row=0, column=0, padx=10, pady=3)
MirrorZDisplay = Canvas(MirrorTLowerFrame, width=20,height=20)
MirrorZDisplay.grid(row=0, column=1, padx=3, pady=3)
MirrorZPositionLabel = Label(MirrorTLowerFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_mm(sd.position(a[2])),2)))
MirrorZPositionLabel.grid(row=0, column=2, padx=10, pady=3)

MirrorTBottomFrame = Frame(MirrorTFrame, width=200, height=60)
MirrorTBottomFrame.grid(row=3, column=0)
MirrorZ_LSTOP = Canvas(MirrorTBottomFrame, bg=LEDColors[a[2].axis.get(10)], width=10, height=20)
MirrorZ_LSTOP.grid(row=0, column=0)
MirrorZ = Scale(MirrorTBottomFrame, variable=mirror_z_pos, from_=0, to=150, resolution=0.1, orient=HORIZONTAL, length=250)
MirrorZ.bind("<ButtonRelease-1>", moveto_mirror_z)
MirrorZ.set(lastpositions[2])
MirrorZ.grid(row=0, column=1, padx=10, pady=3)
MirrorZ_RSTOP = Canvas(MirrorTBottomFrame, bg=LEDColors[a[2].axis.get(11)], width=10, height=20)
MirrorZ_RSTOP.grid(row=0, column=2)


#MirrorR-Content
MirrorRHeadFrame = Frame(MirrorRFrame, width=200, height=20)
MirrorRHeadFrame.grid(row=0, column=0)
midLabel1 = Label(MirrorRHeadFrame, text="Mirror Psi")
midLabel1.grid(row=0, column=0, padx=10, pady=3)
MirrorPsiDisplay = Canvas(MirrorRHeadFrame, width=20,height=20)
MirrorPsiDisplay.grid(row=0, column=1, padx=3, pady=3)
MirrorPsiPositionLabel = Label(MirrorRHeadFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_degree(sd.position(a[4])),2)))
MirrorPsiPositionLabel.grid(row=0, column=2, padx=10, pady=3)

MirrorRUpperFrame = Frame(MirrorRFrame, width=200, height=300)
MirrorRUpperFrame.grid(row=1, column=0)
MirrorPsi_OSTOP = Canvas(MirrorRUpperFrame, bg=LEDColors[a[4].axis.get(10)], width=20, height=10)
MirrorPsi_OSTOP.grid(row=0, column=0)
MirrorPsi = Scale(MirrorRUpperFrame, variable=mirror_psi_pos,from_=4.5, to=-4.5, resolution=0.01, orient=VERTICAL, length=300)
MirrorPsi.bind("<ButtonRelease-1>", moveto_mirror_psi)
MirrorPsi.grid(row=1, column=0, padx=10, pady=3)
MirrorPsi.set(lastpositions[4])
MirrorPsi_USTOP = Canvas(MirrorRUpperFrame, bg=LEDColors[a[4].axis.get(10)], width=20, height=10)
MirrorPsi_USTOP.grid(row=2, column=0)
MirrorRButtonFrame = Frame(MirrorRUpperFrame, width=100, height=150)
MirrorRButtonFrame.grid(row=1, column=1)
B4 = Button(MirrorRButtonFrame, text="Refsearch Mirror Psi", bg="#D3D3D3", width=16, command=refsearch_mirror_psi)
B4.grid(row=0, column=0, padx=10, pady=3) 
B5 = Button(MirrorRButtonFrame, text="Refsearch Mirror Phi", bg="#D3D3D3", width=16, command=refsearch_mirror_phi)
B5.grid(row=2, column=0, padx=10, pady=3)
B6 = Button(MirrorRButtonFrame, text="Center Mirror Angle", bg="#C0C0C0", width=16, command=center_mirror_angle)
B6.grid(row=1, column=0, padx=10, pady=3)

MirrorRLowerFrame = Frame(MirrorRFrame, width=200, height=20)
MirrorRLowerFrame.grid(row=2, column=0)
midLabel2 = Label(MirrorRLowerFrame, text="Mirror Phi")
midLabel2.grid(row=0, column=0, padx=10, pady=3)
MirrorPhiDisplay = Canvas(MirrorRLowerFrame, width=20,height=20)
MirrorPhiDisplay.grid(row=0, column=1, padx=3, pady=3)
MirrorPhiPositionLabel = Label(MirrorRLowerFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_degree(sd.position(a[5])),2)))
MirrorPhiPositionLabel.grid(row=0, column=2, padx=10, pady=3)

MirrorRBottomFrame = Frame(MirrorRFrame, width=200, height=60)
MirrorRBottomFrame.grid(row=3, column=0)
MirrorPhi_LSTOP = Canvas(MirrorRBottomFrame, bg=LEDColors[a[5].axis.get(10)], width=10, height=20)
MirrorPhi_LSTOP.grid(row=0, column=0)
MirrorPhi = Scale(MirrorRBottomFrame, variable=mirror_phi_pos,from_=-4.5, to=4.5, resolution=0.01, orient=HORIZONTAL, length=300)
MirrorPhi.bind("<ButtonRelease-1>", moveto_mirror_phi)
MirrorPhi.grid(row=0, column=1, padx=10, pady=3)
MirrorPhi.set(lastpositions[5])
MirrorPhi_RSTOP = Canvas(MirrorRBottomFrame, bg=LEDColors[a[5].axis.get(10)], width=10, height=20)
MirrorPhi_RSTOP.grid(row=0, column=2)



#Camera-Content
CameraHeadFrame = Frame(CameraFrame, width=200, height=20)
CameraHeadFrame.grid(row=0, column=0)
rightLabel1 = Label(CameraHeadFrame, text="Camera X")
rightLabel1.grid(row=0, column=0, padx=10, pady=3)
CameraXDisplay = Canvas(CameraHeadFrame, width=20,height=20)
CameraXDisplay.grid(row=0, column=1, padx=3, pady=3)
CameraXPositionLabel = Label(CameraHeadFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_mm(sd.position(a[3])),1)))
CameraXPositionLabel.grid(row=0, column=2, padx=10, pady=3)

CameraUpperFrame = Frame(CameraFrame, width=200, height=300)
CameraUpperFrame.grid(row=1, column=0)
CameraX_OSTOP = Canvas(CameraUpperFrame, bg=LEDColors[a[1].axis.get(10)], width=20, height=10)
CameraX_OSTOP.grid(row=0, column=0)
CameraX = Scale(CameraUpperFrame, variable=camera_x_pos,from_=300, to=0, resolution=0.1, orient=VERTICAL, length=300)
CameraX.bind("<ButtonRelease-1>", moveto_camera_x)
CameraX.grid(row=1, column=0, padx=10, pady=3)
CameraX.set(lastpositions[1])
CameraButtonFrame = Frame(CameraUpperFrame, width=100, height=150)
CameraButtonFrame.grid(row=1, column=1)
CameraX_USTOP = Canvas(CameraUpperFrame, bg=LEDColors[a[1].axis.get(11)], width=20, height=10)
CameraX_USTOP.grid(row=2, column=0)
B7 = Button(CameraButtonFrame, text="Refsearch Camera X", bg="#D3D3D3", width=16, command=refsearch_camera_x)
B7.grid(row=0, column=0, padx=10, pady=3) 
B8 = Button(CameraButtonFrame, text="Refsearch Camera Z", bg="#D3D3D3", width=16, command=refsearch_camera_z)
B8.grid(row=2, column=0, padx=10, pady=3)
B9 = Button(CameraButtonFrame, text="Center Camera", bg="#C0C0C0", width=16, command=center_camera)
B9.grid(row=1, column=0, padx=10, pady=3)

CameraLowerFrame = Frame(CameraFrame, width=200, height=20)
CameraLowerFrame.grid(row=2, column=0)
rightLabel2 = Label(CameraLowerFrame, text="Camera Z")
rightLabel2.grid(row=0, column=0, padx=10, pady=3)
CameraZDisplay = Canvas(CameraLowerFrame, width=20,height=20)
CameraZDisplay.grid(row=0, column=1, padx=3, pady=3)
CameraZPositionLabel = Label(CameraLowerFrame, fg=LEDColors[1], bg="black", font=("Helvetica 15 bold"), text=str(round(steps_to_mm(sd.position(a[0])),2)))
CameraZPositionLabel.grid(row=0, column=2, padx=10, pady=3)

CameraBottomFrame = Frame(CameraFrame, width=200, height=60)
CameraBottomFrame.grid(row=3, column=0)
CameraZ_LSTOP = Canvas(CameraBottomFrame, bg=LEDColors[a[0].axis.get(10)], width=10, height=20)
CameraZ_LSTOP.grid(row=0, column=0)
CameraZ = Scale(CameraBottomFrame,variable=camera_z_pos, from_= 150, to=0, resolution=0.1, orient=HORIZONTAL, length=250)
CameraZ.bind("<ButtonRelease-1>", moveto_camera_z)
CameraZ.grid(row=0, column=1, padx=10, pady=3)
CameraZ.set(lastpositions[0])
CameraZ_RSTOP = Canvas(CameraBottomFrame, bg=LEDColors[a[0].axis.get(11)], width=10, height=20)
CameraZ_RSTOP.grid(row=0, column=2)

# Displays with LEDs
MirrorHeightLED = MirrorHeightDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)
MirrorZLED = MirrorZDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)
    
MirrorPhiLED = MirrorPhiDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)
MirrorPsiLED = MirrorPsiDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)

CameraXLED = CameraXDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)
CameraZLED = CameraZDisplay.create_oval(1,1,19,19, fill=LEDColors[0], width=0)

#Permanently update screen
stop_thread = False
def update_motor_status():
    global stop_thread
    stop_thread = False
    while True:
        MirrorHeightDisplay.itemconfig(MirrorHeightLED, fill=LEDColors[sd.ismoving(a[3])+WarningStatus[3]])
        MirrorHeightPositionLabel.config(text=str(round(steps_to_hmm(sd.position(a[3])),1)))
        MirrorHeight_OSTOP.config(bg=LEDColors[a[3].axis.get(10)])
        MirrorHeight_USTOP.config(bg=LEDColors[a[3].axis.get(11)])   
        
        MirrorZDisplay.itemconfig(MirrorZLED, fill=LEDColors[sd.ismoving(a[2])+WarningStatus[2]])
        MirrorZPositionLabel.config(text=str(round(steps_to_mm(sd.position(a[2])),1)))
        MirrorZ_LSTOP.config(bg=LEDColors[a[2].axis.get(11)])
        MirrorZ_RSTOP.config(bg=LEDColors[a[2].axis.get(10)])
        
        MirrorPsiPositionLabel.config(text=str(round(steps_to_degree(sd.position(a[4])),2)))
        MirrorPsiDisplay.itemconfig(MirrorPsiLED, fill=LEDColors[sd.ismoving(a[4])+WarningStatus[4]])
        MirrorPsi_OSTOP.config(bg=LEDColors[a[4].axis.get(10)])
        MirrorPsi_USTOP.config(bg=LEDColors[a[4].axis.get(11)])

        MirrorPhiPositionLabel.config(text=str(round(steps_to_degree(sd.position(a[5])),2)))
        MirrorPhiDisplay.itemconfig(MirrorPhiLED, fill=LEDColors[sd.ismoving(a[5])+WarningStatus[5]])
        MirrorPhi_LSTOP.config(bg=LEDColors[a[5].axis.get(11)])
        MirrorPhi_RSTOP.config(bg=LEDColors[a[5].axis.get(10)])
    
        CameraXPositionLabel.config(text=str(round(steps_to_mm(sd.position(a[1])),1)))
        CameraXDisplay.itemconfig(CameraXLED, fill=LEDColors[sd.ismoving(a[1])+WarningStatus[1]])
        CameraX_OSTOP.config(bg=LEDColors[a[1].axis.get(10)])
        CameraX_USTOP.config(bg=LEDColors[a[1].axis.get(11)])        
        
        CameraZPositionLabel.config(text=str(round(steps_to_mm(sd.position(a[0])),1)))
        CameraZDisplay.itemconfig(CameraZLED, fill=LEDColors[sd.ismoving(a[0])+WarningStatus[1]])
        CameraZ_LSTOP.config(bg=LEDColors[a[0].axis.get(10)])
        CameraZ_RSTOP.config(bg=LEDColors[a[0].axis.get(11)])
        
        #print (WarningStatus)
        #for i in range (0,6):
        #    print (a[i].axis.get(10), " ", a[i].axis.get(11))
        #print (" ")
    
        root.update_idletasks()
        if stop_thread:
            break

screenthreads = []
screenthreads.append(Thread(target=update_motor_status, args=()))
screenthreads[-1].start()

def update_screen():
    global stop_thread
    stop_thread= True
    screenthreads.append(Thread(target=update_motor_status, args=()))
    screenthreads[-1].start()


#ButtonFrame
buttonFrame = Frame(root, width=30, height = 400, bg="#003366")
buttonFrame.grid(row=0, column=1, padx=10,pady=3)
img=PhotoImage(file="/home/pi/stepper_items/ecap_blue.png")
ecap = Label(buttonFrame, image=img, bg="#003366")
ecap.grid(row=0,column=0)
titlelabel= Label(buttonFrame, text="II Motor Control", font="Helvetica 18 bold", fg="white", bg="#003366")
titlelabel.grid(row=1, column=0)
B10 = Button(buttonFrame, text="STOP", font="Helvetica 10 bold", fg="white", bg="#FF0000", width=17, height=7, command=stop_all)
B10.grid(row=8, column=0, padx=10, pady=3)
B11 = Button(buttonFrame, text ="Update screen", bg="#A9A9A9", width=17, command=update_screen)
B11.grid(row=9, column=0, padx=10, pady=3)
B12 = Button(buttonFrame, text="Global reference search", bg="#A9A9A9", width=17, command=refsearch_all)
B12.grid(row=10, column=0, padx=10, pady=3)
B13 = Button(buttonFrame, text="Save current positions", bg="#A9A9A9", width=17, command=save_this_position)
B13.grid(row=11, column=0, padx=10, pady=3)
B14 = Button(buttonFrame, text="Go to saved position", bg = "#A9A9A9", width=17, command=goto_saved_position)
B14.grid(row=12, column=0, padx=10, pady=3)
exit_button = Button(buttonFrame, text="Save Positions and exit", bg="#A9A9A9", width=17, command=exitGUI)
exit_button.grid(row=13, column=0, padx=10, pady=3)




#Hübsche Farben
MirrorTColor = "#b3daff"
MirrorTFrame.config(background = MirrorTColor)
MirrorTHeadFrame.config(background = MirrorTColor)
leftLabel1.config(background = MirrorTColor)
MirrorHeightDisplay.config(background = MirrorTColor)
MirrorTUpperFrame.config(background = MirrorTColor)
MirrorHeight.config(background = MirrorTColor)
MirrorTButtonFrame.config(background = MirrorTColor)
MirrorTLowerFrame.config(background = MirrorTColor)
leftLabel2.config(background = MirrorTColor)
MirrorZDisplay.config(background = MirrorTColor)
MirrorTBottomFrame.config(background = MirrorTColor)
MirrorZ.config(background = MirrorTColor)

MirrorRColor = "#66b5ff"
MirrorRFrame.config(background = MirrorRColor)
MirrorRHeadFrame.config(background = MirrorRColor)
midLabel1.config(background = MirrorRColor)
MirrorPhiDisplay.config(background = MirrorRColor)
MirrorRUpperFrame.config(background = MirrorRColor)
MirrorPhi.config(background = MirrorRColor)
MirrorRButtonFrame.config(background = MirrorRColor)
MirrorRLowerFrame.config(background = MirrorRColor)
midLabel2.config(background = MirrorRColor)
MirrorPsiDisplay.config(background = MirrorRColor)
MirrorRBottomFrame.config(background = MirrorRColor)
MirrorPsi.config(background = MirrorRColor)

CameraColor = "#ccff99"
CameraFrame.config(background = CameraColor)
CameraHeadFrame.config(background = CameraColor)
rightLabel1.config(background = CameraColor)
CameraXDisplay.config(background = CameraColor)
CameraUpperFrame.config(background = CameraColor)
CameraX.config(background = CameraColor)
CameraButtonFrame.config(background = CameraColor)
CameraLowerFrame.config(background = CameraColor)
rightLabel2.config(background = CameraColor)
CameraZDisplay.config(background = CameraColor)
CameraBottomFrame.config(background = CameraColor)
CameraZ.config(background = CameraColor)

root.mainloop()
os._exit(0)
