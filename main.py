#!/usr/bin/env python

# This is the main script. The UI people can create this for us.
# It calls to main_control which reads in sensor data and controls the system.
import time
import sensors
import alarms
import controller
import main_control
import helper

SAMPLETIME = 0.01

# Initialize sensor reading/tracking and UI structures:
jp               = sensors.JuliePlease()                # Provides a higher-level sensor interface.
tracker          = sensors.SensorTracking(jp)             # Initialize class for logging sensor readings.
alarm_bounds     = alarms.AlarmBounds()                 # Intiialize object for storing alarm trigger bounds.
control          = controller.Controller()

try:
    while True:
    
        # UI logic should go into this script. Callbacks needed. 
    
        main_control.take_step(jp, tracker, alarm_bounds, control)
        
        # Pause until next datapoint capture
        #time.sleep(SAMPLETIME)
except KeyboardInterrupt:
  print("Ctl C pressed - ending program")
  del control
  
  
    
