# library imports:
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from time import sleep

# This is the library for reading sensor values.
# Much is taken from https://circuitpython.readthedocs.io/projects/ads1x15/en/latest/examples.html

class JuliePlease:
    def __init__(self):
        self.i2c            = busio.I2C(board.SCL,board.SDA)
        self.adc            = ADS.ADS1115(self.i2c)
        sleep(0.1) # short pause after ads1115 class creation recommended
        self.pressure1      = AnalogIn(self.adc,ADS.P0)
        #self.pressure2     = AnalogIn(self.adc,ADS.P1)
        self.o2             = AnalogIn(self.adc,ADS.P2,ADS.P3)
        
    def get_pressure1_reading(self):
        pres_val = self.__convert_raw_to_pressure(self.pressure1.voltage)
        return pres_val
        
    def get_pressure2_reading(self):
        #pres_val = self.__convert_raw_to_pressure(self.pressure2.voltage)
        pres_val = -1
        return pres_val
        
    def get_o2_reading(self):
        o2_raw = self.o2.value
        return o2_raw

    def get_flow_reading(self):
        return -1.0

    def get_temp_reading(self):
        return -1.0

    def get_humid_reading(self):
        return -1.0

    def __convert_raw_to_pressure(self,raw_val):
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
    def __init__(self,julieplease):
        self._julieplease = julieplease
        self._pres1 = -1.0
        self._pres2 = -1.0
        self._o2 = -1.0
        self._flow = -1.0
        self._temp = -1.0
        self._humid = -1.0
        
    def read_all_sensors(self):
        print('Reading sensors: ')
        self._pres1 = self._julieplease.get_pressure1_reading()
        self._pres2 = self._julieplease.get_pressure2_reading()
        self._o2 = self._julieplease.get_o2_reading()
        self._flow = self._julieplease.get_flow_reading()
        self._temp = self._julieplease.get_temp_reading()
        self._humid = self._julieplease.get_humid_reading()
        
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
    
    
    
