import time
import RPi.GPIO as gpio
from shifter import Shifter

serialPin = 23
latchPin = 24
clockPin = 25

gpio.setmode(gpio.BCM)
gpio.setup(serialPin, gpio.OUT)
gpio.setup(latchPin, gpio.OUT, initial = 0)
gpio.setup(clockPin, gpio.OUT, initial = 0)

schwifty = Shifter(serialPin, clockPin, latchPin)

try:
    while True:
        for i in range(2 ** 8):
            schwifty.shiftByte(i)
            time.sleep(0.5)
except:
    gpio.cleanup()