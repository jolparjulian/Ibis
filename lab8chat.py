# stepper_class_shiftregister_multiprocessing.py
#
# Stepper class
#
# Because only one motor action is allowed at a time, multithreading could be
# used instead of multiprocessing. However, the GIL makes the motor process run 
# too slowly on the Pi Zero, so multiprocessing is needed.

import time
import multiprocessing
from shifter import Shifter   # your custom class

class Stepper:
    """
    Supports operation of an arbitrary number of stepper motors using
    one or more shift registers.
    """

    # Class attributes:
    num_steppers = 0
    seq = [0b0001, 0b0011, 0b0010, 0b0110,
           0b0100, 0b1100, 0b1000, 0b1001]  # CCW sequence
    delay = 2500             # delay between motor steps [us]
    steps_per_degree = 4096 / 360  # 4096 steps/rev * 1/360 rev/deg
    shifter_outputs = None   # will be a multiprocessing.Value('i', 0)
    shared_lock = None       # single lock shared by all steppers

    def __init__(self, shifter, angle):
        self.s = shifter
        self.angle = multiprocessing.Value('d', 0.0)
        self.step_state = 0
        self.shifter_bit_start = 4 * Stepper.num_steppers
        Stepper.num_steppers += 1

    # sign function
    def __sgn(self, x):
        return 0 if x == 0 else int(abs(x) / x)

    # move one +/-1 step
    def __step(self, dir):
        self.step_state = (self.step_state + dir) % 8

        with Stepper.shared_lock:
            current = Stepper.shifter_outputs.value
            mask = ~(0b00001111 << self.shifter_bit_start)
            new = (current & mask) | (Stepper.seq[self.step_state] << self.shifter_bit_start)
            Stepper.shifter_outputs.value = new
            self.s.shiftByte(new)

        with self.angle.get_lock():
            self.angle.value = (self.angle.value + dir / Stepper.steps_per_degree) % 360

    # rotate by a relative delta (blocking)
    def __rotate(self, delta):
        numSteps = int(Stepper.steps_per_degree * abs(delta))
        dir = self.__sgn(delta)
        for _ in range(numSteps):
            self.__step(dir)
            time.sleep(Stepper.delay / 1e6)

    # public rotate (non-blocking, uses process)
    def rotate(self, delta):
        p = multiprocessing.Process(target=self.__rotate, args=(delta,))
        p.start()

    # move to absolute angle via shortest path
    def goToAngle(self, angle):
        with self.angle.get_lock():
            initialAngle = self.angle.value
        angle %= 360
        delta = angle - initialAngle
        if delta > 180:
            delta -= 360
        elif delta < -180:
            delta += 360
        self.rotate(delta)

    def pause(self, pauseTime):
        p = multiprocessing.Process(target=self.__pause, args=(pauseTime,))
        p.start()

    def __pause(self, pauseTime):
        time.sleep(pauseTime)

    def zero(self):
        with self.angle.get_lock():
            self.angle.value = 0.0


# Example usage:
if __name__ == '__main__':
    s = Shifter(data=16, latch=20, clock=21)

    # single shared lock for all motors
    Stepper.shared_lock = multiprocessing.Lock()

    # shared shift register state
    Stepper.shifter_outputs = multiprocessing.Value('i', 0)

    # create two steppers
    m1 = Stepper(s, 0)
    m2 = Stepper(s, 0)

    m1.zero()
    m2.zero()

    # move the motors
    m1.goToAngle(90)
    m1.goToAngle(-45)

    m2.goToAngle(-90)
    m2.goToAngle(45)

    m1.goToAngle(-135)
    m1.goToAngle(135)
    m1.goToAngle(0)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nend")
