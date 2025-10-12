import RPi.GPIO as gpio
from shifter import Shifter
from bug import Bug

serialPin = 23
latchPin = 24
clockPin = 25

s1Pin = 16
s2Pin = 20
s3Pin = 21

s1 = False
s2 = False
s3 = False

shift = Shifter(serialPin, clockPin, latchPin)
ant = Bug(shift)

gpio.setmode(gpio.BCM)
gpio.setup(serialPin, gpio.OUT)
gpio.setup(latchPin, gpio.OUT, initial = 0)
gpio.setup(clockPin, gpio.OUT, initial = 0)

gpio.setup(s1Pin, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.setup(s2Pin, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.setup(s3Pin, gpio.IN, pull_up_down=gpio.PUD_DOWN)

def switch1(pin):
    global s1
    s1 = not s1

def switch2(pin):
    global s2
    s2 = not s2

def switch3(pin):
    global s3
    s3 = not s3

gpio.add_event_detect(s1Pin, gpio.BOTH, callback = switch1, bouncetime = 100)
gpio.add_event_detect(s2Pin, gpio.RISING, callback = switch2, bouncetime = 100)
gpio.add_event_detect(s3Pin, gpio.BOTH, callback = switch3, bouncetime = 100)

try:
    while True:
        if (s3):
            ant.timestep = .03
        else:
            ant.timestep = .1

        ant.isWrapOn = s2

        if (s1):
            ant.start()
        else:
            ant.stop()
        
except:
    gpio.cleanup()
