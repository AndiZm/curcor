import RPi.GPIO as GPIO

def init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.OUT)
    
def motor_on():
    GPIO.output(23, GPIO.HIGH)
def motor_off():
    GPIO.output(23, GPIO.LOW)
        
