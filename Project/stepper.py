import time
import multiprocessing
from shifter import Shifter

class Stepper:
    num_steppers = 0
    shifter_outputs = multiprocessing.Value('i', 0)
    seq = [0b1001,0b1000,0b1100,0b0100,0b0110,0b0010,0b0011,0b0001]
    delay = 2500  # [us]
    #steps_per_degree = 1024.0/360.0
    lock = multiprocessing.Lock()
    s = Shifter(16, 20, 21)

    def __init__(self, steps_per_degree):
        self.angle = multiprocessing.Value('d', 0.0)
        self.step_state = 0
        self.shifter_bit_start = 4 * Stepper.num_steppers
        Stepper.num_steppers += 1
        self.angleFlag = False
        self.steps_per_degree = steps_per_degree #required bc belt gearing

        self.busy = multiprocessing.Value('b', False)
        self.queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(target=self._process_loop, args=(self.queue,))

    def _process_loop(self, queue):
        while True:
            cmd, value = queue.get()

            if cmd == "goTo":
                with self.busy.get_lock():
                    self.busy.value = True
                self.angleFlag = False
                self.__rotate(value)
                self.angleFlag = True
                with self.busy.get_lock():
                    self.busy.value = False
            elif cmd == "step":
                with self.busy.get_lock():
                    self.busy.value = True
                self.angleFlag = False
                self.__step(value)
                time.sleep(Stepper.delay / 1e6)
                self.angleFlag = True
                with self.busy.get_lock():
                    self.busy.value = False
            elif cmd == "pause":
                with self.busy.get_lock():
                    self.busy.value = True
                time.sleep(value)
                with self.busy.get_lock():
                    self.busy.value = False

            elif cmd == "exit":
                break

    def start_process(self):
        self.process.start()


    # Signum function
    def __sgn(self, x):
        return 1 if x > 0 else -1 if x < 0 else 0

    # Step motor by +1 or -1
    def __step(self, dir):
        self.step_state = (self.step_state + dir) % 8
        with Stepper.lock:
            Stepper.shifter_outputs.value &= ~(0b1111 << self.shifter_bit_start)
            Stepper.shifter_outputs.value |= Stepper.seq[self.step_state] << self.shifter_bit_start
            Stepper.s.shiftByte(Stepper.shifter_outputs.value)

        with self.angle.get_lock():
            self.angle.value = (self.angle.value + dir / Stepper.steps_per_degree) % 360
    
    # Rotate relative angle 
    def __rotate(self, delta):
        num_steps = int(abs(delta) * Stepper.steps_per_degree)
        dir = self.__sgn(delta)
        for _ in range(num_steps):
            self.__step(dir)
            time.sleep(Stepper.delay / 1e6)

    # Move to absolute angle using shortest path
    def goToAngle(self, angle):
        with self.angle.get_lock():
            current = self.angle.value
            '''
        delta = (angle - current) % 360
        if delta > 180:
            delta -= 360
        elif delta < -180:
            delta += 360
            '''
        # normalize and shift the sign change
        angle = angle%360 - 180
        current = current%360 - 180
        delta = angle-current
        # if diff signs (opposite sides) go the other way
        if (angle*current < 0):
            delta += 360 if delta < 0 else -360


        if delta != 0:
            self.queue.put(("goTo", delta))

    # go by step, for jog code
    def goStep(self,direc):
        direc = self.__sgn(direc) # normalizes to ensure one step
        self.queue.put(("step",direc))

    def pause(self, delay):
        if delay != 0:
            self.queue.put(("pause", delay))
    
    def stop(self):
        self.queue.put(("exit", None))
        self.process.join()

    # Zero motor
    def zero(self):
        with self.angle.get_lock():
            self.angle.value = 0.0

if __name__ == '__main__':
    m1 = Stepper()
    m2 = Stepper()

    m1.zero()
    m2.zero()

    m1.start_process()
    m2.start_process()

    # Concurrent rotations
    m1.goToAngle(45)
    m1.goToAngle(-45)

    m2.goToAngle(-90)
    m2.pause(4)
    m2.goToAngle(45)
    m2.stop()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nend")