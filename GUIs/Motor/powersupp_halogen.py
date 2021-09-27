import serial
from tkinter import *
import time

class powerSupply:
    # Device
    dev = None
    # The two important variables: on is the state of the psupp (on/off), step the voltage step
    on = 0
    step = 0
    volt = 0
    
    def __init__(self):
        pass

    def connect(self):
        self.dev = serial.Serial('/dev/ttyACM2', timeout=0.2)
        self.get_state()
        
    def get_state(self):
        self.dev.write(bytearray([91]))
        state = str(self.dev.read(8)).split("x")[1][:-1]
        state = int(state,16)
        if state > 127:
            self.on = 1#; onoffButton.config(text="On")
            self.step = state - 128
        else:
            #onoffButton.config(text="Off")
            self.step = state
        self.voltage()

    def turn_on(self):
        self.on = 1
        self.dev.write(bytearray([92,128*self.on+self.step]))
        #onoffButton.config(text="On")        
    def turn_off(self):
        self.on = 0
        self.dev.write(bytearray([92,128*self.on+self.step]))
        #onoffButton.config(text="Off")        
    def onoff(self):
        if self.on == 1:
            self.turn_off()
        elif self.on == 0:
            self.turn_on()

    def voltage(self):
        #print ("Voltage set is " + str((800 + 50*step)/1000))
        self.volt = (800 + 50*self.step)/1000
    def voltage_to_step(self, voltage):
        return int((1000*voltage-800)/50)    

    def set_voltage(self, voltage_to_set):
        self.step = self.voltage_to_step(voltage_to_set)
        self.dev.write(bytearray([92,128*self.on+self.step]))
        self.voltage()
    #def set_step_from_scale(val):
    #    step_to_set = voltage_to_step(float(voltageScale.get()))
    #    #print(step_to_set)
    #    set_step(step_to_set)