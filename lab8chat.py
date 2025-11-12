import time
import multiprocessing
from shifter import Shifter   # your custom shift register class

class Stepper:
    """
    Multiprocessing Stepper class with per-rotation processes.
    Supports concurrent motion of multiple motors while maintaining
    sequential order of rotations per motor.
    """

    # Class attributes
    num_steppers = 0
    shifter_outputs = multiprocessing.Value('i', 0)
    seq = [0b0001,0b0011,0b0010,0b0110,0b0100,0b1100,0b1000,0b1001]
    delay = 2500  # [us]
    steps_per_degree = 4096/360
    lock = multiprocessing.Lock()
    s = Shifter(data=16, latch=20, clock=21)

    def __init__(self):
        self.angle = multiprocessing.Value('d', 0.0)
        self.step_state = 0
        self.shifter_bit_start = 4 * Stepper.num_steppers
        Stepper.num_steppers += 1

        # Queue of active processes for sequential rotations per motor
        self._process_queue = []

    # Signum function
    def __sgn(self, x):
        if x == 0: return 0
        return int(abs(x)/x)

    # Step motor by +1 or -1
    def __step(self, dir):
        self.step_state = (self.step_state + dir) % 8
        with Stepper.lock:
            Stepper.shifter_outputs.value &= ~(0b1111 << self.shifter_bit_start)
            Stepper.shifter_outputs.value |= Stepper.seq[self.step_state] << self.shifter_bit_start
            Stepper.s.shiftByte(Stepper.shifter_outputs.value)

        with self.angle.get_lock():
            self.angle.value = (self.angle.value + dir / Stepper.steps_per_degree) % 360

    # Rotate relative angle (called in a separate process)
    def __rotate(self, delta):
        num_steps = int(abs(delta) * Stepper.steps_per_degree)
        dir = self.__sgn(delta)
        for _ in range(num_steps):
            self.__step(dir)
            time.sleep(max(Stepper.delay / 1e6, 0.01))  # Pi Zero timing safe

    # Public rotate method: spawns a new process for this rotation
    def rotate(self, delta):
        if delta == 0:
            return

        p = multiprocessing.Process(target=self.__rotate, args=(delta,))
        p.start()
        self._process_queue.append(p)

        # Clean up completed processes at the front of the queue
        while self._process_queue and not self._process_queue[0].is_alive():
            self._process_queue[0].join()
            self._process_queue.pop(0)

    # Move to absolute angle using shortest path
    def goToAngle(self, angle):
        with self.angle.get_lock():
            current = self.angle.value

        delta = (angle - current) % 360
        if delta > 180:
            delta -= 360
        elif delta < -180:
            delta += 360

        if delta != 0:
            self.rotate(delta)

    # Pause (also spawns process if required)
    def pause(self, pause_time):
        def _pause(t):
            time.sleep(t)

        p = multiprocessing.Process(target=_pause, args=(pause_time,))
        p.start()
        self._process_queue.append(p)

        # Clean up finished processes
        while self._process_queue and not self._process_queue[0].is_alive():
            self._process_queue[0].join()
            self._process_queue.pop(0)

    # Zero motor
    def zero(self):
        with self.angle.get_lock():
            self.angle.value = 0.0

# Example usage
if __name__ == '__main__':
    m1 = Stepper()
    m2 = Stepper()

    m1.zero()
    m2.zero()

    # Concurrent rotations
    m1.goToAngle(90)
    m1.goToAngle(-45)

    m2.goToAngle(-90)
    m2.goToAngle(45)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nend")
