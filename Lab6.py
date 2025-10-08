import time
import RPi.GPIO as gpio
from shifter import Shifter
from bug import Bug
import random
random.seed()

try:
    ant = Bug()
    ant.start()
        
except:
    gpio.cleanup()