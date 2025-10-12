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

ant = Bug()
ant.start()

s1 = False
s2 = False
s3 = False
def switch1(pin):
    global s1
    s1 = not s1
    print('a')

def switch2(pin):
    global s2
    s2 = not s2
    print('b')

def switch3(pin):
    global s3
    s3 = not s3
    print('c')

gpio.add_event_detect(s1Pin, gpio.BOTH, callback = switch1, bouncetime = 100)
gpio.add_event_detect(s2Pin, gpio.RISING, callback = switch2, bouncetime = 100)
gpio.add_event_detect(s3Pin, gpio.BOTH, callback = switch3, bouncetime = 100)

try:
    while True:
        print('d')
        if (s3):
            ant.timestep /= 3
        else:
            ant.timestep *= 3

        if (s2):
            ant.isWrapOn = True
        else:
            ant.isWrapOn = False

        if (s1):
            ant.start()
        else:
            ant.stop()
        
except:
    gpio.cleanup()
