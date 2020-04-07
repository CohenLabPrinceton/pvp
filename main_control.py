#!/usr/bin/env python

import time
import automationhat
import sensors
import alarms
import controller
import helper

def take_step(curr, tracker, alarm_bounds):
    # Read the sensors. 
    curr.read_all_sensors()
    print(curr.pres1)
    
    # Read inputs from user.
    # TODO: UI. Will modify alarm bounds.
    # set alarm_bounds
       
    # Control loop. Update controller according to tracked sensor values. 
    controller.update_controller(tracker)
        
    # Update sensor tracking:
    tracker.update_all_sensors(curr)
    
    #Throw any alarms that need throwing.
    alarms.throw_raw_alarms(tracker, alarm_bounds)
    

