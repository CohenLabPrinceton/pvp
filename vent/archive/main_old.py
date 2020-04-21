#!/usr/bin/env python

# This is the main script. The UI people can create this for us.
# It calls to main_control which reads in sensor data and controls the system.
import time
from vent.archive import sensors, alarms, main_control

SAMPLETIME = 0.01

# Initialize sensor reading/tracking and UI structures:
julieplease     = sensors.JuliePlease()
curr            = sensors.SensorReadings(julieplease)
tracker         = sensors.SensorTracking()
alarm_bounds    = alarms.AlarmBounds()

while True:
    
    # UI logic should go into this script. Callbacks needed. 
    
    main_control.take_step(curr, tracker, alarm_bounds)
    # Pause until next datapoint capture
    time.sleep(SAMPLETIME)
    
    
