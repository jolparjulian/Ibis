from shifter import Shifter
import random
import time
random.seed()

class Bug:
    def __init__(self, timestep = 0.1, x = 3, isWrapOn = False):
        self.timestep = timestep
        self.x = x
        self.isWrapOn = isWrapOn

    __schwifty = Shifter(23, 25, 24)

    def start(self):
        while True:
            self.__schwifty.shiftByte(1 << self.x)
            time.sleep(self.timestep)
            if (not self.isWrapOn):
                if (x == 0):
                    x = 1
                elif (x == 7):
                    x = 6
                else:
                    x += random.choice([-1, 1])
            else:
                x += random.choice([-1, 1])
                if (x == -1):
                    x = 7
                elif (x == 8):
                    x = 0     
            
    def stop(self):
        self.__schwifty.shiftByte(0)