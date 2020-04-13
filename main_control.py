#!/usr/bin/env python

import time
import sensors
import alarms
import controller
import helper


def take_step(jp, tracker, alarm_bounds, control):
    # Read all the sensors. 

    # Read inputs from user.
    # TODO: UI. Will modify alarm bounds.
    # set alarm_bounds
       
    # Control loop. Update controller according to tracked sensor values. 
    control.update_controller(jp, tracker)
        
    # Update sensor tracking:
    tracker.update_all_sensors()
    
    #Throw any alarms that need throwing.
    alarms.throw_raw_alarms(tracker, alarm_bounds)
    

