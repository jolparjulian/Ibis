import RPi.GPIO as gpio
import time

class Shifter:
    def __init__(self, serialPin, clockPin, latchPin):
        self.serialPin = serialPin
        self.clockPin = clockPin
        self.latchPin = latchPin
    
    gpio.setmode(gpio.BCM)

    def __ping(self, pin):
        gpio.output(pin, 1)
        time.sleep(0)
        gpio.output(pin, 0)
        
    def shiftByte(self, b):
        for i in range(8):
            gpio.output(self.serialPin, b & (1 << i))
            self.__ping(self.clockPin)
        self.__ping(self.latchPin)