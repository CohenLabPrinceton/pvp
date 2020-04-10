#  Pulse Width Modulation (PWM) to cycle relay at pin 17

import RPi.GPIO as GPIO   # Import the GPIO library.
import time               # Import time library

GPIO.setmode(GPIO.BCM) 
GPIO.setup(17, GPIO.OUT)  # This is the inspiratory guy.
GPIO.setup(27, GPIO.OUT)  # This is the expiratory guy.
pwm = GPIO.PWM(27, 10)   # Initialize PWM on pwmPin 100Hz frequency

RAMPTIME = (0.5 / 20)
LOTIME = 1
HITIME = 1

# main loop of program
print("\nPress Ctl C to quit \n")  # Print blank line before and after message.
dc=0                               # set dc variable to 0 for 0%
pwm.start(dc)

try:
  GPIO.output(27, GPIO.HIGH)
  while True:                      # Loop until Ctl C is pressed to stop.
      
    pr = get_pressure_reading()    # Returns current pressure reading in cmH2O
    if(pr > 40):
        pwm.ChangeDutyCycle(100)
        print(dc)
        time.sleep(HITIME)
        for dc in range(95, 0, -5):    # Loop 95 to 5 stepping dc down by 5 each loop
          pwm.ChangeDutyCycle(dc)
          #if dc > 50:
          #pwm.ChangeDutyCycle(50)
          #else:
           # pwm.ChangeDutyCycle(0)
          time.sleep(RAMPTIME)             # wait 
          print(dc)
        time.sleep(LOTIME)
except KeyboardInterrupt:
  print("Ctl C pressed - ending program")

pwm.stop()                         # stop PWM
GPIO.cleanup()                     # resets GPIO ports used back to input mode
