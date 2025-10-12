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

schwifty = Shifter(serialPin, clockPin, latchPin)
ant = Bug(schwifty)

try:
    while True:
        ant.start()
        
except:
    gpio.cleanup()