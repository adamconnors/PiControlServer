#!/usr/bin/python

class GPIO:
    BCM = 1
    OUT = 1
    HIGH = 1
    LOW = 0

    @staticmethod
    def setmode(mode):
        return
    @staticmethod
    def setwarnings(bool):
        return
    @staticmethod
    def setup(port, mode):
        print 'setup ' + str(port) + ' as ' + str(mode)
        return
    @staticmethod
    def output(port, mode):
        print 'GPIO port=' + str(port) + ' mode=' + str(mode)
        return

class PWM:
    def __init__(self, address):
        print 'pwm address ' + str(address)
    def setPWMFreq(self, freq):
        print 'pwm freq ' + str(freq)
        return
    def setPWM(self, channel, upedge, downedge):
        print 'set pwm ' + str(channel) + ' up/down: ' + str(upedge) + '/' + str(downedge)
        return

class RRB3:
    def __init__(self, val1, val2):
        print 'Configured robotboard: ' + str(val1) + ", " + str(val2)
        return

    def set_motors(self, leftSpeed, leftDirection, rightSpeed, rightDirection):
        print 'setmotors ' + str(leftSpeed) + ' ' + str(leftDirection) + ' ' + str(rightSpeed) + ' ' + str(rightDirection)
        return

    def set_oc1(self, state):
        print 'oc1=' + str(state)
        return
    def set_led1(self, state):
        print 'led1' + str(state)
        return
    def set_led2(self, state):
        print 'led2' + str(state)
        return


