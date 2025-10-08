from shifter import Shifter
import random
import time
import RPi.GPIO as gpio
random.seed()

class Bug:
    def __init__(self, timestep = 0.1, x = 3, isWrapOn = False):
        self.timestep = timestep
        self.x = x
        self.isWrapOn = isWrapOn

    serialPin = 23
    latchPin = 24
    clockPin = 25

    __schwifty = Shifter(serialPin, clockPin, latchPin)

    def start(self):
        while True:
            self.__schwifty.shiftByte(1 << self.x)
            time.sleep(self.timestep)
            if (not self.isWrapOn):
                if (self.x == 0):
                    self.x = 1
                elif (self.x == 7):
                    self.x = 6
                else:
                    self.x += random.choice([-1, 1])
            else:
                self.x += random.choice([-1, 1])
                if (self.x == -1):
                    self.x = 7
                elif (self.x == 8):
                    self.x = 0    
            
    def stop(self):
        self.__schwifty.shiftByte(0)