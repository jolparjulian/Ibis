import time
import RPi.GPIO as gpio
from shifter import Shifter

sch = Shifter(16, 20, 21)
seq = [0b00010000,0b00110000,0b00100000,0b01100000,0b01000000,0b11000000,0b10000000,0b10010000]

while True:
    for s in seq:
        sch.shiftByte(s)
        time.sleep(0.01)
