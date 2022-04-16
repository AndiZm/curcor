import RPi.GPIO as GPIO
import time

enablePIN = 6
servoPIN = 12
GPIO.setmode(GPIO.BCM)
GPIO.setup(servoPIN, GPIO.OUT)
GPIO.setup(enablePIN, GPIO.OUT)


#GPIO.output(enablePIN, 1)
p = GPIO.PWM(servoPIN, 50) # GPIO 12 als PWM mit 50Hz
p.start(7.1) # Initialisierung

offset=2.1
fullswing=10


def shutter(a):
    angle=a
    GPIO.output(enablePIN, 1)
    time.sleep(.25)
    if angle>180:
        print("Max 180 degree!")
    if angle<0:
        print("Min 0 degree!")
    moveto=10./180.*angle+offset
    print("Move to {:.0f} degrees ({:.2f} duty)".format(angle,moveto))
    p.ChangeDutyCycle(moveto)
    time.sleep(2)
    p.ChangeDutyCycle(0)
    GPIO.output(enablePIN, 0)
    #p.stop()
    #GPIO.cleanup()
  

def shutter_clean(a):
    angle=a
    GPIO.output(enablePIN, 1)
    time.sleep(.25)
    if angle>180:
        print("Max 180 degree!")
    if angle<0:
        print("Min 0 degree!")
    moveto=10./180.*angle+offset
    print("Move to {:.0f} degrees ({:.2f} duty)".format(angle,moveto))
    p.ChangeDutyCycle(moveto)
    time.sleep(2)
    p.ChangeDutyCycle(0)
    GPIO.output(enablePIN, 0)
    p.stop()
    GPIO.cleanup()
    
    
#shutter(180)
#time.sleep(2)
#shutter(0)
    
'''
try:
  while True:
    angle=float(input("please input degrees  "))
    GPIO.output(enablePIN, 1)
    time.sleep(.25)
    if angle>180:
        print("Max 180 degree!")
    if angle<0:
        print("Min 0 degree!")
    moveto=10./180.*angle+offset
    print("Move to {:.0f} degrees ({:.2f} duty)".format(angle,moveto))
    p.ChangeDutyCycle(moveto)
    time.sleep(2)
    p.ChangeDutyCycle(0)
    GPIO.output(enablePIN, 0)
except KeyboardInterrupt:
  GPIO.output(enablePIN, 1)
  time.sleep(.25)
  print("\nExiting (move to 90 degree)")
  p.ChangeDutyCycle(offset+5)
  time.sleep(2)
  GPIO.output(enablePIN, 0)
  p.stop()
  GPIO.cleanup()
'''