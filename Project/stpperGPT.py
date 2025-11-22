# stepper_manager.py
import time
import multiprocessing
from shifter import Shifter

class StepperMotor:
    """Data container for a motor attached to the shared shifter"""
    def __init__(self, bit_start):
        self.angle = 0.0           # Current absolute angle
        self.step_state = 0         # Sequence position
        self.bit_start = bit_start  # Start bit in the shift register
        self.target_angle = None    # Desired angle
        self.busy = False           # Motor busy flag

class StepperManager:
    # Shared hardware
    seq = [0b0001,0b0011,0b0010,0b0110,0b0100,0b1100,0b1000,0b1001]
    steps_per_degree = 4096/360
    delay = 2500  # microseconds

    shifter = Shifter(16, 20, 21)          # Shared shift register
    shifter_outputs = multiprocessing.Value('i', 0)  # 8-bit output word
    lock = multiprocessing.Lock()

    def __init__(self):
        self.motors = []
        self.queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(target=self._worker)
    
    def add_motor(self):
        bit_start = len(self.motors) * 4
        motor = StepperMotor(bit_start)
        self.motors.append(motor)
        return motor

    def start(self):
        self.process.start()

    def stop(self):
        self.queue.put(("exit", None))
        self.process.join()

    def rotate_motor(self, motor, delta):
        """Queue a rotation command"""
        self.queue.put(("rotate", motor, delta))

    def go_to_angle(self, motor, angle):
        """Queue an absolute rotation"""
        self.queue.put(("goto", motor, angle % 360))

    def zero_motor(self, motor):
        motor.angle = 0.0

    # --- Private worker ---
    def _worker(self):
        while True:
            # Process any new commands
            while not self.queue.empty():
                cmd, motor, value = self.queue.get()
                if cmd == "exit":
                    return
                elif cmd == "rotate":
                    motor.target_angle = (motor.angle + value) % 360
                    motor.busy = True
                elif cmd == "goto":
                    motor.target_angle = value
                    motor.busy = True

            # Step motors toward their targets
            any_busy = False
            for m in self.motors:
                if m.target_angle is None or abs(m.target_angle - m.angle) < 0.01:
                    m.busy = False
                    m.target_angle = None
                    continue

                any_busy = True
                # Compute shortest path
                delta = (m.target_angle - m.angle) % 360
                if delta > 180:
                    delta -= 360
                dir = 1 if delta > 0 else -1
                # Step
                m.step_state = (m.step_state + dir) % 8
                with StepperManager.lock:
                    StepperManager.shifter_outputs.value &= ~(0b1111 << m.bit_start)
                    StepperManager.shifter_outputs.value |= StepperManager.seq[m.step_state] << m.bit_start
                    StepperManager.shifter.shiftByte(StepperManager.shifter_outputs.value)
                # Update angle
                m.angle = (m.angle + dir / StepperManager.steps_per_degree) % 360

            # Sleep between steps
            if any_busy:
                time.sleep(StepperManager.delay / 1e6)
            else:
                time.sleep(0.001)  # Idle wait

if __name__ == "__main__":
    manager = StepperManager()

    # Add motors
    m1 = manager.add_motor()
    m2 = manager.add_motor()

    manager.start()

    # Queue some moves
    manager.go_to_angle(m1, 90)
    manager.go_to_angle(m2, -90)

    time.sleep(1)

    manager.go_to_angle(m1, 0)
    manager.go_to_angle(m2, 45)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        manager.stop()
