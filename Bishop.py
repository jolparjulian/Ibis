import time
import RPi.GPIO as gpio
from shifter import Shifter
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

try:
    x = random.randint(0, 7)
    while True:
        schwifty.shiftByte(1 << x)
        time.sleep(0.05)
        if (x == 0):
            x = 1
        elif (x == 7):
            x = 6
        else:
            x += random.choice([-1, 1])
        
except:
    gpio.cleanup()