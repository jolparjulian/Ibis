import RPi.GPIO as gpio
import time

gpio.setmode(gpio.BCM)

class Shifter:
    def __init__(self, serialPin, clockPin, latchPin):
        self.serialPin = serialPin
        self.clockPin = clockPin
        self.latchPin = latchPin
        gpio.setup(self.serialPin, gpio.OUT)
        gpio.setup(self.latchPin, gpio.OUT)
        gpio.setup(self.clockPin, gpio.OUT)
    
    def __ping(self, pin):
        gpio.output(pin, 1)
        time.sleep(0)
        gpio.output(pin, 0)
        
    def shiftByte(self, b):
        for i in range(8):
            gpio.output(self.serialPin, b & (1 << i))
            self.__ping(self.clockPin)
        self.__ping(self.latchPin)

    def shiftWord(self, dataword, num_bits):
        for i in range((num_bits+1) % 8):
            gpio.output(self.serialPin, 0)
            self.__ping(self.clockPin)
        for i in range(num_bits): 
            gpio.output(self.serialPin, dataword & (1<<i))
            self.__ping(self.clockPin)
            self.__ping(self.latchPin)

    def shiftByte(self, databyte):
        self.shiftWord(databyte, 8)