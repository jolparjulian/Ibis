from RPi import GPIO
GPIO.setmode(GPIO.BCM)

class Shifter():
    def __init__(self, serialPin, latchPin, clockPin):
        self.serialPin = serialPin
        self.latchPin = latchPin
        self.clockPin = clockPin
        
        GPIO.setup(self.serialPin, GPIO.OUT)
        GPIO.setup(self.latchPin, GPIO.OUT, initial = 0)
        GPIO.setup(self.clockPin, GPIO.OUT, initial = 0)
    
    def __ping(self, p):
        GPIO.output(p,1)
        GPIO.output(p,0)
   
    def shiftByte(self, b):
        for i in range(8):
            GPIO.output(self.serialPin, b & (1 << i))
            self.__ping(self.clockPin)
        self.__ping(self.latchPin)