import random
import time
random.seed()

class Bug:
    def __init__(self, __shift, timestep = 0.1, x = 3, isWrapOn = False):
        self.timestep = timestep
        self.x = x
        self.isWrapOn = isWrapOn
        self.__shift = __shift

    def start(self):
        self.__shift.shiftByte(1 << self.x)
        if (not self.isWrapOn):
            if (self.x == 0):
                self.x = 1
            elif (self.x == 7):
                self.x = 6
            else:
                self.x += random.choice([-1, 1])
        else:
            self.x += random.choice([-1, 1])
            if (self.x == -1):
                self.x = 7
            elif (self.x == 8):
                self.x = 0    
        time.sleep(self.timestep)
            
    def stop(self):
        self.__shift.shiftByte(0b00000000)