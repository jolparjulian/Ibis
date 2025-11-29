import RPi.GPIO as gpio
import time
from shifter import Shifter

serialPin = 16
latchPin = 20
clockPin = 21

seq = [0b00010001,0b00100010,0b01000100,0b10001000]

sch = Shifter(16, 20, 21)

try:
    while True:
        for s in seq:
            sch.shiftByte(s)
            time.sleep(0.01)
        
except:
    gpio.cleanup()
