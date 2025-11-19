from stepper import Stepper

m1 = Stepper()
m2 = Stepper()

m1.zero()
m2.zero()

m1.start_process()
m2.start_process()

m1.goToAngle(90)
m2.goToAngle(90)
m1.goToAngle(-90)
m2.goToAngle(-90)

