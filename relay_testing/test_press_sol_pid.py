import RPi.GPIO as GPIO   # Import the GPIO library.
import time               # Import time library

GPIO.setmode(GPIO.BCM) 
GPIO.setup(17, GPIO.OUT)  # This is the inspiratory guy.
GPIO.setup(27, GPIO.OUT)  # This is the expiratory guy.
pwm = GPIO.PWM(27, 10)   # Initialize PWM on pwmPin 100Hz frequency

RAMPTIME = (0.5 / 20)
LOTIME = 1
HITIME = 1
MAXPRESS = 40.0

KP = 0.02
KD = 0.01
KI = 0.005

# main loop of program
print("\nPress Ctl C to quit \n")  # Print blank line before and after message.
dc=0                               # set dc variable to 0 for 0%
pwm.start(dc)

def clamp(value):
    return max(min(100, value),0)

try:
  GPIO.output(27, GPIO.HIGH)
  while True:                      # Loop until Ctl C is pressed to stop.
      
    pr = get_pressure_reading()    # Returns current pressure reading in cmH2O
    if(pr > 40):
        pwm.ChangeDutyCycle(100)
        print(dc)
        time.sleep(HITIME)
        for dc in range(95, 0, -5):    # Loop 95 to 5 stepping dc down by 5 each loop
            
          # Set pressure setpoint:
          press_setpoint = MAXPRESS * dc * 0.01
          # Do PID control:
          dc_pid = dc
          e_preverror = 0
          e_sumerror = 0 
          for i in range(5):
              pr_pid = get_pressure_reading()
              e_error = press_setpoint - pr_pid
              
              dc_pid += (e_error * KP) + (e_preverror * KD) + (e_sumerror * KI)
              dc_pid = clamp(dc_pid)
              
              dc = PID()
              pwm.ChangeDutyCycle(dc)
              print(dc)
              time.sleep(RAMPTIME / 5)
              e_preverror = e_error
              e_sumerror += e_error            
          

        time.sleep(LOTIME)
        
except KeyboardInterrupt:
  print("Ctl C pressed - ending program")

pwm.stop()                         # stop PWM
GPIO.cleanup()                     # resets GPIO ports used back to input mode

