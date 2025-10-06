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

in1 = 14
gpio.setup(in1, gpio.IN, pull_up_down=gpio.PUD_DOWN)

def call(pin):
    phi *= -1

gpio.add_event_detect(in1, gpio.RISING, callback = call, bouncetime = 100)


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

for each in pwm:
    each.stop()
gpio.cleanup()