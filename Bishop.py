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
seq = [0b00010001,0b00100010,0b01000100,0b10001000]

try:
    while True:
        for s in seq:
            sch.shiftByte(s)
            time.sleep(0.01)
        
except:
    gpio.cleanup()
