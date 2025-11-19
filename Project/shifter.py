from RPi import GPIO
from time import sleep
GPIO.setmode(GPIO.BCM)

class Shifter():
    def __init__(self, serialPin, latchPin, clockPin):
        self.serialPin = serialPin
        self.latchPin = latchPin
        self.clockPin = clockPin
        
        GPIO.setup(self.serialPin, GPIO.OUT)
        GPIO.setup(self.latchPin, GPIO.OUT)
        GPIO.setup(self.clockPin, GPIO.OUT)
    
    def ping(self, p):
        GPIO.output(p,1)
        sleep(0)
        GPIO.output(p,0)

    def shiftWord(self, dataword, num_bits):
        for i in range((num_bits+1) % 8):
            GPIO.output(self.serialPin, 0)
            self.ping(self.clockPin)
        for i in range(num_bits):
            GPIO.output(self.serialPin, dataword & (1<<i))
            self.ping(self.clockPin)
            self.ping(self.latchPin)
   
    def shiftByte(self, databyte):
        self.shiftWord(databyte, 8)