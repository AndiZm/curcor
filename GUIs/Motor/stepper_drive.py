import serial 
import pyTMCL

def init():
    serial_port = serial.Serial("/dev/ttyACM0")  #an welchen usb haengt motor
    bus=pyTMCL.connect(serial_port)   #erlaubt motorsteuerung 
    module = bus.get_module(0)

    a=[]
    for i in range (6):
        a.append(module.get_motor(i))  # 6 motoren eingefuegt
        a[i].set_axis_parameter(5,20)  # acceleration einstellen
        
    a[3].set_pullups(3) #disable pullups for Mirror 
    
    for i in range (4):
        a[i].set_axis_parameter(140,5) #32 Microsteps
        a[i].axis.left_limit_switch_disabled=False  #enable limit switches
        a[i].axis.right_limit_switch_disabled=False

    for i in range (4,6):
        a[i].set_axis_parameter(140,5) #32 Microsteps
        a[i].axis.left_limit_switch_disabled=False  #enable limit switches
        a[i].axis.right_limit_switch_disabled=False
    
    #reduce max current
    a[0].set_axis_parameter(6,100)
    a[1].set_axis_parameter(6,185)
    a[2].set_axis_parameter(6,150)
    a[3].set_axis_parameter(6,200)
    a[4].set_axis_parameter(6,100)
    a[5].set_axis_parameter(6,100)
    
    # Reference search direction settings
    a[0].set_axis_parameter(193,65) #Right Ref Search
    a[1].set_axis_parameter(193,1) #Left Ref Search
    a[1].set_axis_parameter(160,65) #Interpolate steps
    a[2].set_axis_parameter(193,65)
    a[3].set_axis_parameter(193,1)
    
    #max speed
    a[0].axis.max_positioning_speed=300
    a[0].set_axis_parameter(194, 300)

    a[1].axis.max_positioning_speed=300
    a[1].set_axis_parameter(194, 500)
    
    a[2].axis.max_positioning_speed=200
    
    a[3].axis.max_positioning_speed=100 #Should be limited to 200
    a[3].set_axis_parameter(194, 100) #Refsearch Speed of Mirror Height
    
    a[4].axis.max_positioning_speed=300
    a[5].axis.max_positioning_speed=300
    
    return a   #a wird an stepper_gui weitergegeben, liste aller motoren
    

def ismoving(themotor): #ob motor faehrt
    return 1-themotor.get_position_reached()
def position(themotor): #motor position abrufen
    return themotor.axis.get(1)
