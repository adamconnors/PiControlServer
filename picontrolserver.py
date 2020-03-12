#!/usr/bin/python
# To run: python2.7 PiControlServer.py
# Expected URL: http://<ip>:8080/cmd?c=0,0&m=0,0
# c = Camera position -100% to 100%
# m = Motor power -100% to 100%
# a0 / a1 / a2 / a3 = -1 0 1 to control direction

import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from os import path,getcwd,sep
import serial
import threading
import time

try:
	# Real implementation when running on Raspberry Pi -- comment for local testing
	from Adafruit_PWM_Servo_Driver import PWM
	import RPi.GPIO as GPIO
	from rrb3 import *
except:
	# Fake libraries for running on laptop & testing
	print '***WARNING*** COULDNT FIND Adafruit, GPIO, or RRB3 libs, using fake ones only. Nothing is gonna happen now.'
	from dummylibs import GPIO
	from dummylibs import PWM
	from dummylibs import RRB3


# Configure raspirobot board 12V input & 12V motors
# See https://www.monkmakes.com/rrb3/ for APIs.
rr = RRB3(12, 12)

# Configure two GPIO outputs for grabby hand controls
# Top side of motor
GPIO_RELAY1 = 16

# Bottom side of motor
GPIO_RELAY2 = 17

# Overall on/off switch. Connected to NC since default for GPIO is HIGH,
# so always ensure GPIO state is HIGH (off) before changes RELAY1 or RELAY2
GPIO_RELAY3_MASTER = 18

# Configure two GPIO outputs
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(GPIO_RELAY1,GPIO.OUT)
GPIO.setup(GPIO_RELAY2, GPIO.OUT)
GPIO.setup(GPIO_RELAY3_MASTER, GPIO.OUT)

# Configure PWM board connected at IC2 address 0x40 (default).
pwm = PWM(0x40)
pwm.setPWMFreq(60)

# Server port.
PORT_NUMBER = 8081

# Servo channels (based on where the wires are plugged into servo board).
# VERTICAL_SERVO_CHANNEL = 4
# HORIZONTAL_SERVO_CHANNEL = 5

# Arm servo channels -- temporarily using the camera ones
A0_SERVO_CHANNEL = 5
A1_SERVO_CHANNEL = 4
A2_SERVO_CHANNEL = 7
A3_SERVO_CHANNEL = 6

# Calculated based on the PWM freq, see adafruit tutorial.
SERVO_MIN = 160
SERVO_MAX = 600
SERVO_RANGE = SERVO_MAX - SERVO_MIN

# Signal sent from client to indicate whether to power grabby hand or not.
GRABBYHAND_ON = '1'
GRABBYHAND_OFF = '0'


class Arm(threading.Thread):

	def __init__(self):
		print("Created Arm Thread")
		super(Arm, self).__init__()

	run = True

	# The direction each part of the arm is moving -- updated by params in request
	arm0 = 0
	arm1 = 0
	arm2 = 0
	arm3 = 0

	# The current value of the arm -- updated by Arm thread based on arm values
	armVal0 = 0
	armVal1 = 0
	armVal2 = 0
	armVal3 = 0

	def run(self):
		while self.run:
			time.sleep(0.05)

			sendUpdate = False
			if self.arm0 != 0:
				self.armVal0 += self.arm0
				sendUpdate = True

			if self.arm1 != 0:
				self.armVal1 += self.arm1
				sendUpdate = True

			if self.arm2 != 0:
				self.armVal2 += self.arm2
				sendUpdate = True

			if self.arm3 != 0:
				self.armVal3 += self.arm3
				sendUpdate = True

			# Boundaries - TODO: Use an array instead
			if self.armVal0 > 100:
				self.armVal0 = 100
				self.arm0 = 0

			if self.armVal0 < -100:
				self.armVal0 = -100
				self.arm0 = 0

			if self.armVal1 > 100:
				self.armVal1 = 100
				self.arm1 = 0

			if self.armVal1 < -100:
				self.armVal1 = -100
				self.arm1 = 0

			if self.armVal2 > 100:
				self.armVal2 = 100
				self.arm2 = 0

			if self.armVal2 < -100:
				self.armVal2 = -100
				self.arm2 = 0

			if self.armVal3 > 100:
				self.armVal3 = 100
				self.arm3 = 0

			if self.armVal3 < -100:
				self.armVal3 = -100
				self.arm3 = 0


			if sendUpdate:
				print("Sending pwm vals: %d %d %d %d" % \
					  (self.armVal0, self.armVal1, self.armVal2, self.armVal3))

				pwm.setPWM(A0_SERVO_CHANNEL, 0, calculatePWM(int(self.armVal0)))
				pwm.setPWM(A1_SERVO_CHANNEL, 0, calculatePWM(int(self.armVal1)))
				pwm.setPWM(A2_SERVO_CHANNEL, 0, calculatePWM(int(self.armVal2)))
				pwm.setPWM(A3_SERVO_CHANNEL, 0, calculatePWM(int(self.armVal3)))


#This class will handle any incoming request from
#the browser
class PiControlServer(BaseHTTPRequestHandler):

	#Handler for the GET requests
	def do_GET(self):

		# Decode the incoming request
		parsed_path = urlparse.urlparse(self.path)
		params = urlparse.parse_qs(parsed_path.query)

		print("Command: " + parsed_path.query)

		# Camera controller parameters
		# Temporarily disable camera controls until arm has its own servo points
		if params.has_key('cxxxx'):
			vals = params['c'][0].split(',')

			# Invert hpos since it was moving the wrong way.
			hPercent = int(vals[0]) * -1
			vPercent = int(vals[1])
			hPos = (float(hPercent + 100) / float(200) * float(SERVO_RANGE)) + float(SERVO_MIN)
			vPos = (float(vPercent + 100) / float(200) * float(SERVO_RANGE)) + float(SERVO_MIN)

			# pwm.setPWM(HORIZONTAL_SERVO_CHANNEL, 0, int(hPos))
			# pwm.setPWM(VERTICAL_SERVO_CHANNEL, 0, int(vPos))

		# Arm controller parameters
		# a0 (base-left-right); a1 (base-up-down); a2 (wrist); a3 (hand)
		# Expect -1, 0, 1 for each value.
		if params.has_key('a0'):
			val = params['a0'][0]
			armState.arm0 = int(val)

		if params.has_key('a1'):
			val = params['a1'][0]
			armState.arm1 = int(val) * -1

		if params.has_key('a2'):
			val = params['a2'][0]
			armState.arm2 = int(val)

		if params.has_key('a3'):
			val = params['a3'][0]
			armState.arm3 = int(val)

		# Motor controller parameters
		if params.has_key('m'):
			vals = params['m'][0].split(',')
			leftSpeed = abs(float(vals[0])) / 100
			leftDirection = 0 if int(vals[0]) < 0 else 1
			rightSpeed = abs(float(vals[1])) / 100
			rightDirection = 0 if int(vals[1]) < 0 else 1
			print('set_motors: ' + str(leftSpeed) + "," + str(leftDirection) + "," + str(rightSpeed) + "," + str(rightDirection))

			# args: left spd, left dir, right spd, right dir
			rr.set_motors(leftSpeed, leftDirection, rightSpeed, rightDirection)

		# Relay tests
		if params.has_key('r'):
			vals = params['r'][0].split(",")
			relay = vals[0]
			on = vals[1]
			gpio = 0
			if relay == '1':
				gpio=GPIO_RELAY1
			elif relay == '2':
				gpio=GPIO_RELAY2
			elif relay == '3':
				gpio=GPIO_RELAY3_MASTER

			if on == '1':
				GPIO.output(gpio, GPIO.HIGH)
			else:
				GPIO.output(gpio, GPIO.LOW)

		# Grabby hand controller parameters
		# On, Direction
		if params.has_key('h'):
			vals = params['h'][0].split(",")
			on = vals[0]
			dir = vals[1]
			print('Grabbyhand, on=' + on + " dir=" + dir)

			# Direction controlled by relay state
			if (on == GRABBYHAND_ON):
				if dir == '1':
					print('open')
					GPIO.output(GPIO_RELAY3_MASTER, GPIO.HIGH)
					GPIO.output(GPIO_RELAY1, GPIO.HIGH)
					GPIO.output(GPIO_RELAY2, GPIO.LOW)
					GPIO.output(GPIO_RELAY3_MASTER, GPIO.LOW)
				else:
					print('close')
					GPIO.output(GPIO_RELAY3_MASTER, GPIO.HIGH)
					GPIO.output(GPIO_RELAY1, GPIO.LOW)
					GPIO.output(GPIO_RELAY2, GPIO.HIGH)
					GPIO.output(GPIO_RELAY3_MASTER, GPIO.LOW)
			else:
				print('off')
				GPIO.output(GPIO_RELAY3_MASTER, GPIO.HIGH)

		# LED controller parameters on Servo module
		if (params.has_key('l')):
			vals = params['l'][0].split(',')
			leftLED = vals[0]
			rightLED = vals[1]
			print('set led1=' + leftLED + ' led2=' + rightLED)
			rr.set_led1(int(leftLED))
			rr.set_led2(int(rightLED))

		# Return HTML
		self.send_response(200)
		self.send_header('Content-type',    'text/html')
		self.end_headers()

		if ((params.has_key('debug')) or (parsed_path.query == '')):
			location = path.realpath(path.join(getcwd(), path.dirname(__file__)))
			f = open(path.join(location, 'index.html'))
			self.wfile.write(f.read())
			f.close()
		else:
			self.wfile.write('ok')
		return


# Expects +100 --> -100, return PWM frequency
def calculatePWM(percent):
	return int((float(percent + 100) / float(200) * float(SERVO_RANGE)) + float(SERVO_MIN))


def sendserial(a0, a1, a2, a3):
	vals = bytearray([a0, a1, a2, a3])
	print("Sending: " + vals + " to arm.")
	ser.write(vals)
	print("sent.")


# //
armState = Arm()

try:
	#Create a web server and define the handler to manage the
	#incoming request
	server = HTTPServer(('', PORT_NUMBER), PiControlServer)
	print 'Started httpserver on port ' , PORT_NUMBER

	# Start arm driver
	armState.start()

	#Wait forever for incoming htto requests
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	armState.run = False
	server.socket.close()
	