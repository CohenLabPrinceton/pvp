#!/usr/bin/env python

# This is the main script. The UI people can create this for us.
# It calls to main_control which reads in sensor data and controls the system.
import time
from vent import sensors
from vent import alarms
from vent import controls
from vent import helper

# Initialize sensor reading/tracking and UI structures:
jp               = sensors.JuliePlease()                # Provides a higher-level sensor interface.
alarm_bounds     = alarms.AlarmBounds()                 # Intiialize object for storing alarm trigger bounds.
logger           = controls.DataLogger(jp)           # Initialize class for logging sensor readings.
controller          = controls.Controller(jp,logger)

def take_step(control,alarm_bounds):
  # Read all the sensors.
  # Read inputs from user.
  # TODO: UI. Will modify alarm bounds.
  # set alarm_bounds

  # Update sensor tracking:
  logger.update()

  # Control loop. Update controller according to tracked sensor values.
  controller.update()

  #Throw any alarms that need throwing.
  alarms.throw_raw_alarms(logger, alarm_bounds)

try:
  while True:
    # UI logic should go into this script. Callbacks needed. 
    take_step(controller, alarm_bounds)

    # Pause until next datapoint capture
    time.sleep(controller.settings.SAMPLETIME)

except KeyboardInterrupt:
  print("Ctl C pressed - ending program")
  del controller
