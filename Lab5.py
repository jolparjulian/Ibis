import time
import math
import RPi.GPIO as gpio

pin = 4
gpio.setmode(gpio.BCM) 
gpio.setup(pin, gpio.OUT)

t = time.time()
f = 0.2 #Hz
pwmF = 500 #Hz
pwm = gpio.PWM(pin, pwmF)

try:
    while True:
        t = time.time()
        brightness = (math.sin(math.pi * 2 * f * t)) ** 2
        pwm.start(brightness * 100)
except KeyboardInterrupt:
    print("out")

pwm.stop()
gpio.cleanup()