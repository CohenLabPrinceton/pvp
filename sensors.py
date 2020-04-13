# library imports:
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_bus_device.i2c_device import I2CDevice
from time import sleep

# This is the library for reading sensor values.
# Much is taken from https://circuitpython.readthedocs.io/projects/ads1x15/en/latest/examples.html

class JuliePlease:
    def __init__(self):
        self.i2c            = busio.I2C(board.SCL,board.SDA)
        try:
            self.adc            = ADS.ADS1115(self.i2c)
            sleep(0.1) # short pause after ads1115 class creation recommended
            self.pressure1      = AnalogIn(self.adc,ADS.P0)
            self.pressure2      = AnalogIn(self.adc,ADS.P1)
            self.o2             = AnalogIn(self.adc,ADS.P2,ADS.P3)
        except: print('No ADC found.\n')
        self.flow           = I2CDevice(self.i2c,0x40) 
        with self.flow:
            self.flow.write(b"\x10\x00")
            sleep(0.5)
        
    def get_pressure1_reading(self):
        pres_val = self.__convert_raw_to_pressure(self.pressure1.voltage)
        return pres_val
        
    def get_pressure2_reading(self):
        pres_val = self.__convert_raw_to_pressure(self.pressure2.voltage)
        return pres_val
        
    def get_o2_reading(self):
        o2_raw = self.o2.value
        return o2_raw

    def get_flow_reading(self):
        flowbytes = flowbytes = bytearray(4)
        self.flow.readinto(flowbytes)
        flow_val = self.__convert_raw_to_flow(flowbytes)
        return flow_val

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
    def __convert_raw_to_flow(self,flowbytes):
        # Convert raw i2c response (4 bytes) to a flow reading represaented by a floating-point
        # number with units slm.
        # Source: https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/5_Mass_Flow_Meters/Application_Notes/Sensirion_Mass_Flo_Meters_SFM3xxx_I2C_Functional_Description.pdf
        flow_offset         = 32768
        flow_scale_factor   = 120
        flow = float(int.from_bytes(flowbytes[:2],'big',signed=False)-flow_offset)/flow_scale_factor
        return flow


def update_single_sensor(track, val, track_len):
    # Adds newest sensor reading to end of track.
    # Only store most recent [track_len] values.
    
    # Check if list is already at max track length:
    if(len(track) >= track_len):
        # Remove first element
        track.pop(0)
    # Add current sensor reading to track:
    track.append(val)  
    return track    
   
    
class SensorTracking:
    # A class for keeping track of prior sensor values.
    # These are used by controllers and to sound alarms.
    def __init__(self, jp):
        self.jp = jp
        self._track_len = 50    # Type int: How long to retain sensor data. Could vary this later per sensor. 
        self.pres1_track = []
        self.pres2_track = []
        self.o2_track = []
        self.flow_track = []
        self.temp_track = []
        self.humid_track = []
        
    def update_all_sensors(self):
        # Takes in current sensor readings object; updates tracking log for all sensors.
        self.pres1_track = update_single_sensor(self.pres1_track, self.jp.get_pressure1_reading(), self._track_len)
        self.pres2_track = update_single_sensor(self.pres2_track, self.jp.get_pressure2_reading(), self._track_len)
        self.o2_track = update_single_sensor(self.o2_track, self.jp.get_o2_reading(), self._track_len)
        self.flow_track = update_single_sensor(self.flow_track, self.jp.get_flow_reading(), self._track_len)
        self.temp_track = update_single_sensor(self.temp_track, self.jp.get_temp_reading(), self._track_len)
        self.humid_track = update_single_sensor(self.humid_track, self.jp.get_humid_reading(), self._track_len)
        
    def reset(self):
        self.pres1_track = []
        self.pres2_track = []
        self.o2_track = []
        self.flow_track = []
        self.temp_track = []
        self.humid_track = []

    
    
    
