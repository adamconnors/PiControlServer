#!/usr/bin/python
# To run: python2.7 PiControlServer.py
# Expected URL: http://<ip>:8080/cmd?c=0,0&m=0,0
# c = Camera position -100% to 100%
# m = Motor power -100% to 100%

import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from os import path,getcwd,sep

# Real implementation when running on Raspberry Pi -- comment for local testing
# from Adafruit_PWM_Servo_Driver import PWM
#import RPi.GPIO as GPIO
#from rrb3 import *

# Uncomment this line for local testing
from dummylibs import GPIO
from dummylibs import PWM
from dummylibs import RRB3


# Configure raspirobot board 12V input & 12V motors
# See https://www.monkmakes.com/rrb3/ for APIs.
rr = RRB3(12, 12)

# Configure two GPIO outputs for grabby hand controls
GPIO_OUTPUT1 = 17
GPIO_OUTPUT2 = 18

# Configure two GPIO outputs
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(GPIO_OUTPUT1,GPIO.OUT)
GPIO.setup(GPIO_OUTPUT2, GPIO.OUT)

# Configure PWM board connected at IC2 address 0x40 (default).
pwm = PWM(0x40)
pwm.setPWMFreq(60)

# Server port.
PORT_NUMBER = 8081

# Servo channels (based on where the wires are plugged into servo board).
VERTICAL_SERVO_CHANNEL = 4
HORIZONTAL_SERVO_CHANNEL = 5

# Calculated based on the PWM freq, see adafruit tutorial.
SERVO_MIN = 160
SERVO_MAX = 600

# Signal sent from client to indicate whether to power grabby hand or not.
GRABBYHAND_ON = '1'
GRABBYHAND_OFF = '0'

#This class will handle any incoming request from
#the browser
class PiControlServer(BaseHTTPRequestHandler):

	#Handler for the GET requests
	def do_GET(self):

		# Decode the incoming request
		parsed_path = urlparse.urlparse(self.path)
		params = urlparse.parse_qs(parsed_path.query)

		# Camera controller parameters
		if params.has_key('c'):
			vals = params['c'][0].split(',')

			servoRange = SERVO_MAX - SERVO_MIN

			# Invert hpos since it was moving the wrong way.
			hPercent = int(vals[0]) * -1
			vPercent = int(vals[1])
			hPos = (float(hPercent + 100) / float(200) * float(servoRange)) + float(SERVO_MIN)
			vPos = (float(vPercent + 100) / float(200) * float(servoRange)) + float(SERVO_MIN)

			pwm.setPWM(HORIZONTAL_SERVO_CHANNEL, 0, int(hPos))
			pwm.setPWM(VERTICAL_SERVO_CHANNEL, 0, int(vPos))

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

		# Grabby hand controller parameters
		# On, Direction
		if params.has_key('h'):
			vals = params['h'][0].split(",")
			on = vals[0]
			dir = vals[1]
			print('Grabbyhand, on=' + on + " dir=" + dir)
			failsafe = False

			# Direction controlled by relay state
			if dir == '1':
				print('open')
				GPIO.output(GPIO_OUTPUT1, GPIO.HIGH)
				GPIO.output(GPIO_OUTPUT2, GPIO.LOW)
				failsafe = True
			else:
				print('close')
				GPIO.output(GPIO_OUTPUT1, GPIO.LOW)
				GPIO.output(GPIO_OUTPUT2, GPIO.HIGH)
				failsafe = True

			# Whether switch on the open collector which is set up as the
			# overall on/off switch for the hand.
			if on == GRABBYHAND_ON:
				if (failsafe):
					# Set open collector
					rr.set_oc1(1)
				else:
					print('WARNING: Attempted to switch on grabby hand without setting direction!')
			else:
				rr.set_oc1(0)


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

# //
try:
	#Create a web server and define the handler to manage the
	#incoming request
	server = HTTPServer(('', PORT_NUMBER), PiControlServer)
	print 'Started httpserver on port ' , PORT_NUMBER

	#Wait forever for incoming htto requests
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	server.socket.close()
	