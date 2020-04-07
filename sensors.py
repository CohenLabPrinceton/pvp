# library imports:
import automationhat

# This is the library for reading sensor values.

def convert_raw_to_pressure(raw_val):
    # Convert raw analog signal to pressure value in cm H20. Hysteresis not accounted for.
    # Source 20 INCH-G-P4V-MINI: http://www.allsensors.com/datasheets/DS-0102_Rev_A.pdf
    # Two-Point Calibration: 
    raw_low = 0.28
    raw_hi = 4.0 # needs calibration
    raw_range = raw_hi - raw_low
    ref_low = 0.25
    ref_hi = 4.0
    ref_range = ref_hi - ref_low
    #corrected_val = (((raw_val - raw_low)*ref_range)/raw_range) + ref_low 
    conv_val_inchh20 = (((raw_val - raw_low)*20.0)/raw_range) + 0.0    
    conv_val_cmh20 = (2.54)*conv_val_inchh20    
    return conv_val_cmh20

def get_pressure1_reading():
    retrieve1 = automationhat.analog.one.read() # current pressure raw analog value
    pres_val = convert_raw_to_pressure(retrieve1)
    return pres_val

def get_pressure2_reading():
    #retrieve2 = automationhat.analog.two.read() # current pressure raw analog value
    #res_val = convert_raw_to_pressure(retrieve2)
    pres_val = -1.0
    return pres_val

def get_o2_reading():
    return -1.0

def get_flow_reading():
    return -1.0

def get_temp_reading():
    return -1.0

def get_humid_reading():
    return -1.0

def update_single_sensor(track, curr_val, track_len):
    # Adds newest sensor reading to end of track.
    # Only store most recent [track_len] values.
    
    # Check if list is already at max track length:
    if(len(track) >= track_len):
        # Remove first element
        track.pop(0)
    # Add current sensor reading to track:
    track.append(curr_val)  
    return track    
   
class SensorReadings:
    # A class for obtaining sensor readings at a single timepoint. 
    def __init__(self):
        self._pres1 = -1.0
        self._pres2 = -1.0
        self._o2 = -1.0
        self._flow = -1.0
        self._temp = -1.0
        self._humid = -1.0
        
    def read_all_sensors(self):
        print('Reading sensors: ')
        self._pres1 = get_pressure1_reading()
        self._pres2 = get_pressure2_reading()
        self._o2 = get_o2_reading()
        self._flow = get_flow_reading()
        self._temp = get_temp_reading()
        self._humid = get_humid_reading()
        
    def reset(self):
        self._pres1 = -1.0
        self._pres2 = -1.0
        self._o2 = -1.0
        self._flow = -1.0
        self._temp = -1.0
        self._humid = -1.0
    
    @property
    def pres1(self):
        return self._pres1
    @property
    def pres2(self):
        return self._pres2
    @property
    def o2(self):
        return self._o2
    @property
    def flow(self):
        return self._flow
    @property
    def temp(self):
        return self._temp
    @property
    def humid(self):
        return self._humid
    
class SensorTracking:
    # A class for keeping track of prior sensor values.
    # These are used by controllers and to sound alarms.
    def __init__(self):
        self._track_len = 50    # Type int: How long to retain sensor data. Could vary this later per sensor. 
        self._pres1_track = []
        self._pres2_track = []
        self._o2_track = []
        self._flow_track = []
        self._temp_track = []
        self._humid_track = []
        
    def update_all_sensors(self, curr):
        # Takes in current sensor readings object; updates tracking log for all sensors.
        print('Updating sensor tracks: ')
        self._pres1_track = update_single_sensor(self._pres1_track, curr._pres1, self._track_len)
        self._pres2_track = update_single_sensor(self._pres2_track, curr._pres2, self._track_len)
        self._o2_track = update_single_sensor(self._o2_track, curr._o2, self._track_len)
        self._flow_track = update_single_sensor(self._flow_track, curr._flow, self._track_len)
        self._temp_track = update_single_sensor(self._temp_track, curr._temp, self._track_len)
        self._humid_track = update_single_sensor(self._humid_track, curr._humid, self._track_len)
        
    def reset(self):
        self._pres1_track = []
        self._pres2_track = []
        self._o2_track = []
        self._flow_track = []
        self._temp_track = []
        self._humid_track = []
    
    @property
    def pres1_track(self):
        return self._pres1_track
    @property
    def pres2_track(self):
        return self._pres2_track
    @property
    def o2_track(self):
        return self._o2_track
    @property
    def flow_track(self):
        return self._flow_track
    @property
    def temp_track(self):
        return self._temp_track
    @property
    def humid_track(self):
        return self._humid_track   
    
    
    