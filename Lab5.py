import time
import math
import RPi.GPIO as gpio

pin = [4, 17, 27, 22, 10, 9, 11, 5, 6, 13]
gpio.setmode(gpio.BCM) 
t = time.time()
f = 0.2 #Hz
pwmF = 500 #Hz
phi = math.pi / 11
pwm = [None] * 10

for i in range(10):
    gpio.setup(pin[i], gpio.OUT)
    pwm[i] = gpio.PWM(pin[i], pwmF)

try:
    while True:
        t = time.time()
        for i in range(10):
            brightness = (math.sin(math.pi * 2 * f * t - i * phi)) ** 2
            pwm[i].start(brightness * 100)
except KeyboardInterrupt:
    print("out")

pwm.stop()
gpio.cleanup()