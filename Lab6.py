import time
import RPi.GPIO as gpio
from shifter import Shifter
from bug import Bug
import random
random.seed()

serialPin = 23
latchPin = 24
clockPin = 25

gpio.setmode(gpio.BCM)
gpio.setup(serialPin, gpio.OUT)
gpio.setup(latchPin, gpio.OUT, initial = 0)
gpio.setup(clockPin, gpio.OUT, initial = 0)

s1Pin = 16
s2Pin = 20
s3Pin = 21

gpio.setup(s1Pin, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.setup(s2Pin, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.setup(s3Pin, gpio.IN, pull_up_down=gpio.PUD_DOWN)

try:
    ant = Bug()
        
except:
    gpio.cleanup()

def switch1(pin):
    global ant
    ant.start()
def switch2(pin):
    global ant
    ant.isWrapOn = not ant.isWrapOn
def switch3(pin):
    ant.timestep = ant.timestep / 3

gpio.add_event_detect(s1Pin, gpio.RISING, callback = switch1, bouncetime = 100)
gpio.add_event_detect(s2Pin, gpio.RISING, callback = switch2, bouncetime = 100)
gpio.add_event_detect(s3Pin, gpio.RISING, callback = switch3, bouncetime = 100)