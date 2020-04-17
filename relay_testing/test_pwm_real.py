#  Pulse Width Modulation (PWM) to cycle relay at pin 17

import RPi.GPIO as GPIO   # Import the GPIO library.
import time               # Import time library

GPIO.setmode(GPIO.BCM) 
GPIO.setup(17, GPIO.OUT)  # Set GPIO pin 17 to output mode.
GPIO.setup(27, GPIO.OUT)  # Set GPIO pin 17 to output mode.
pwm = GPIO.PWM(17, 100)   # Initialize PWM on pwmPin 100Hz frequency
pwm2 = GPIO.PWM(27, 10)   # Initialize PWM on pwmPin 100Hz frequency

RAMPTIME = 0.2
LOTIME = 1
HITIME = 1

# main loop of program
print("\nPress Ctl C to quit \n")  # Print blank line before and after message.
dc=0                               # set dc variable to 0 for 0%
pwm.start(dc)                      # Start PWM with 0% duty cycle
pwm2.start(dc)

try:
  #pwm2.ChangeDutyCycle(50)
  while True:                      # Loop until Ctl C is pressed to stop.
    for dc in range(0, 101, 5):    # Loop 0 to 100 stepping dc by 5 each loop
      pwm.ChangeDutyCycle(dc)
      #if dc > 50:
      #pwm.ChangeDutyCycle(50)
      #else:
      #  pwm.ChangeDutyCycle(0)
      time.sleep(RAMPTIME)             # wait .05 seconds at current LED brightness
      print(dc)
    time.sleep(HITIME)
    for dc in range(95, 0, -5):    # Loop 95 to 5 stepping dc down by 5 each loop
      pwm.ChangeDutyCycle(dc)
      #if dc > 50:
      #pwm.ChangeDutyCycle(50)
      #else:
       # pwm.ChangeDutyCycle(0)
      time.sleep(RAMPTIME)             # wait .05 seconds at current LED brightness
      print(dc)
    time.sleep(LOTIME)
except KeyboardInterrupt:
  print("Ctl C pressed - ending program")

pwm.stop()                         # stop PWM
pwm2.stop()                         # stop PWM
GPIO.cleanup()                     # resets GPIO ports used back to input mode
