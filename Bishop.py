import time
import RPi.GPIO as gpio
from shifterJules import ShifterJules

serialPin = 16
latchPin = 20
clockPin = 21

gpio.setup(serialPin, gpio.OUT)
gpio.setup(latchPin, gpio.OUT, initial = 0)
gpio.setup(clockPin, gpio.OUT, initial = 0)

sch = ShifterJules(serialPin, clockPin, latchPin)
seq = [0b00010000,0b00100000,0b01000000,0b10000000]

try:
    while True:
        for s in seq:
            sch.shiftByte(s)
            time.sleep(0.01)
        
except:
    gpio.cleanup()
