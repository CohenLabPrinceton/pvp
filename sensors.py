# library imports:
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_bus_device.i2c_device import I2CDevice
from digitalio import DigitalInOut     # For reading temperature sensor
from adafruit_max31865 import MAX31865 # Temperature sensor amplifier board
from time import sleep

# This is the library for reading sensor values.
# Much is taken from https://circuitpython.readthedocs.io/projects/ads1x15/en/latest/examples.html

class JuliePlease:
    def __init__(self):
        self._i2c = busio.I2C(board.SCL,board.SDA)
        self._spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        try:
            cs = DigitalInOut(board.D5) # Chip select of the MAX31865 board.
            self.tsensor = MAX31865(self._spi, cs, rtd_nominal=1000.0, ref_resistor=4300.0)
        except: print('No temperature sensor found.\n')
        try:
            self._adc                   = ADS.ADS1115(self._i2c)
            sleep(0.1) # short pause after ads1115 class creation recommended
            self._pressure_sensor_0     = AnalogIn(self._adc,ADS.P0)
            self._pressure_sensor_1     = AnalogIn(self._adc,ADS.P1)
            self._o2_sensor             = AnalogIn(self._adc,ADS.P2,ADS.P3)
        except: print('No ADC found.\n')
        try:
            self._flow_sensor           = I2CDevice(self._i2c,0x40) 
            with self._flow_sensor:
                self._flow_sensor.write(b"\x10\x00")
                sleep(0.1)
        except: print('No flow sensor found.\n')
        
    def get_pressure(self,sensor_ID):
        if sensor_ID == 0:
            return self.__convert_raw_to_pressure(self._pressure_sensor_0.voltage)
        elif sensor_ID == 1: 
            return self.__convert_raw_to_pressure(self._pressure_sensor_1.voltage)
        else: 
            # This really should call an alarm! Someone make alarms smarter plz
            print('Sir; your pressure sensor appears to be malfunctioning.')
            return 100 # return a large fake pressure to make the system stop pressurizing 
        
    def get_o2(self):
        return self._o2_sensor.value

    def get_flow(self):
        flowbytes = flowbytes = bytearray(4)
        self._flow_sensor.readinto(flowbytes)
        return self.__convert_raw_to_flow(flowbytes)

    def get_temperature(self,units='F'):
        # Returns temperature in degrees C
        # Can calculate resistance as: tsensor.resistance in Ohms
        if units == 'F':
                temp = (self.tsensor.temperature*1.8) + 32.0
        elif units =='C':
                temp = self.tsensor.temperature
        else:
                print('Incorrect units specified for temperature. Use \"C\" or \"F\" or leave blank for default \n')
                temp = -100
        return temp

    def get_humidity(self):
        return -100

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
