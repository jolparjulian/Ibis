import time
from stepper import Stepper

motors = [Stepper() Stepper()]
for m in enumerate(motors):
	m.zero()
	m.start_process()

motors[0].goToAngle(90)
motors[1].goToAngle(90)
motors[0].goToAngle(-90)
motors[1].goToAngle(-90)