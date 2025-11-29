import RPi.GPIO as gpio
import time

serialPin = 16
latchPin = 20
clockPin = 21

seq = [0b00010001,0b00100010,0b01000100,0b10001000]

def ping(pin, tim):
    gpio.output(pin, 1)
    time.sleep(tim)
    gpio.output(pin, 0)

def shiftByte(b):
    for i in range(8):
        gpio.output(serialPin, b & (1 << i))
        ping(clockPin, 0)
    ping(latchPin, 0)
    
gpio.setmode(gpio.BCM)

gpio.setup(serialPin, gpio.OUT)
gpio.setup(latchPin, gpio.OUT, initial = 0)
gpio.setup(clockPin, gpio.OUT, initial = 0)

shiftByte(0b00000000)
time.sleep(5)
print("yep")
shiftByte(0b10100011)
time.sleep(90)
shiftByte(0b00000000)

'''
ping(clockPin, 3)
time.sleep(2)
ping(latchPin, 3)
time.sleep(2)
shiftByte(0b00000000)
time.sleep(2)
shiftByte(0b11111111)
time.sleep(2)
shiftByte(0b00000000)
'''
