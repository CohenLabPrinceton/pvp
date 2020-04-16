# library imports:

def throw_pres1_alarm(tracker, bounds):
    # Throws alarm for pressure sensor at output of pressure regulator.
    do_throw = 0
        
    # If all values in tracker are above max value, raise alarm 
    if all(i > bounds[1] for i in tracker.pres1_track):
        do_throw = 1
    # If all values in tracker are below min value, raise alarm
    # TODO
    return do_throw

def throw_pres2_alarm(tracker, bounds):
    # Throws alarm for pressure sensor at WYE port.
    do_throw = 0    
    return do_throw

def throw_o2_alarm(tracker, bounds):
    # Throws alarm for O2 sensor.
    do_throw = 0    
    return do_throw

def throw_flow_alarm(tracker, bounds):
    # Throws alarm for flow sensor.
    do_throw = 0    
    return do_throw

def throw_temp_alarm(tracker, bounds):
    # Throws alarm for temperature sensor.
    do_throw = 0    
    return do_throw

def throw_humid_alarm(tracker, bounds):
    # Throws alarm for humidity sensor (optional).
    do_throw = 0    
    return do_throw

def throw_raw_alarms(tracker, alarm_bounds):
    # Throw alarms for raw values which leave acceptable bounds.      
    # Check all sensor tracks:
    do_throw = 0
    do_throw = do_throw or throw_pres1_alarm(tracker, alarm_bounds.pres1_bounds)
    do_throw = do_throw or throw_pres2_alarm(tracker, alarm_bounds.pres2_bounds)
    # ...

    return

class AlarmBounds:
    # A class for obtaining sensor readings at a single timepoint. 
    def __init__(self):
        self.pres1_bounds = [-10000, 4.0]
        self.pres2_bounds = [-10000, 10000]
        self.o2_bounds = [-10000, 10000]
        self.flow_bounds = [-10000, 10000]
        self.temp_bounds = [-10000, 10000]
        self.humid_bounds = [-10000, 10000]
        
    def reset(self):
        self.pres1_bounds = [-10000, 10000]
        self.pres2_bounds = [-10000, 10000]
        self.o2_bounds = [-10000, 10000]
        self.flow_bounds = [-10000, 10000]
        self.temp_bounds = [-10000, 10000]
        self.humid_bounds = [-10000, 10000]
    

