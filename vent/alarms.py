# library imports:
import automationhat

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
    # Throws alarm for pressure sensor at WYE port.
    do_throw = 0    
    return do_throw

def throw_flow_alarm(tracker, bounds):
    # Throws alarm for pressure sensor at WYE port.
    do_throw = 0    
    return do_throw

def throw_temp_alarm(tracker, bounds):
    # Throws alarm for pressure sensor at WYE port.
    do_throw = 0    
    return do_throw

def throw_humid_alarm(tracker, bounds):
    # Throws alarm for pressure sensor at WYE port.
    do_throw = 0    
    return do_throw

def throw_raw_alarms(tracker, alarm_bounds):
    # Throw alarms for raw values which leave acceptable bounds.      
    # Check all sensor tracks:
    do_throw = 0
    do_throw = do_throw or throw_pres1_alarm(tracker, alarm_bounds.pres1_bounds)
    do_throw = do_throw or throw_pres2_alarm(tracker, alarm_bounds.pres2_bounds)
    # ...

    # Raise alarms: 
    if (automationhat.is_automation_hat() and do_throw==1):
        automationhat.light.power.write(1)  # Just turning on a light for now. 
    return

class AlarmBounds:
    # A class for obtaining sensor readings at a single timepoint. 
    def __init__(self):
        self._pres1_bounds = [-10000, 4.0]
        self._pres2_bounds = [-10000, 10000]
        self._o2_bounds = [-10000, 10000]
        self._flow_bounds = [-10000, 10000]
        self._temp_bounds = [-10000, 10000]
        self._humid_bounds = [-10000, 10000]
        
    def set_pres1_bounds(self, pres_val):
        self._pres1_bounds = pres_val
    def set_pres2_bounds(self, pres_val):
        self._pres2_bounds = pres_val
    def set_o2_bounds(self, o2_val):
        self._o2_bounds = o2_val
    def set_flow_bounds(self, flow_val):
        self._flow_bounds = flow_val
    def set_temp_bounds(self, temp_val):
        self._temp_bounds = temp_val
    def set_humid_bounds(self, humid_val):
        self._humid_bounds = humid_val
        
    def reset(self):
        self._pres1_bounds = [-10000, 10000]
        self._pres2_bounds = [-10000, 10000]
        self._o2_bounds = [-10000, 10000]
        self._flow_bounds = [-10000, 10000]
        self._temp_bounds = [-10000, 10000]
        self._humid_bounds = [-10000, 10000]
    
    @property
    def pres1_bounds(self):
        return self._pres1_bounds
    @property
    def pres2_bounds(self):
        return self._pres2_bounds
    @property
    def o2_bounds(self):
        return self._o2_bounds
    @property
    def flow_bounds(self):
        return self._flow_bounds
    @property
    def temp_bounds(self):
        return self._temp_bounds
    @property
    def humid_bounds(self):
        return self._humid_bounds

