from iobase import Sensor, AnalogSensor, i2cDevice, spiDevice
from time import sleep

'''
Class Definitions for specific sensor devices.
'''
            
class P4vMini(AnalogSensor):
    '''
        Analog gauge pressure sensor with range of 0 - 20" h20.
        Datasheet calibration low is 0.25V and high is 4.0V
    '''
    _default_offset_voltage = 0.25
    _default_output_span    = 4
    ''' Maximum reading in cm h20: 2.54 cm/in * 20" h20 * 1.0 normalized output '''
    _conversion_factor      = 2.54*20 

    def __init__(   self, adc, channel,
                    calibration=(0.25,4.0),
                    gain=1, data_rate=860, mode=None ):
        super().__init(self, adc, channel, calibration, gain, data_rate, mode)

    def _convert(self,raw):
        return self._conversion_factor*self.read()

class OxygenSensor(AnalogSensor):
	__init__(self):
		pass
		
class SFM3200(Sensor,i2cDevice):
    '''
    Datasheet:
        https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/5_Mass_Flow_Meters/Datasheets/Sensirion_Mass_Flow_Meters_SFM3200_Datasheet.pdf
    '''
    _DEFAULT_ADDRESS     = 0x40 # SFM3x00 Flow sensor address
    _FLOW_OFFSET         = 32768
    _FLOW_SCALE_FACTOR   = 120

    def __init__(self,pig,address=_DEFAULT_ADDRESS):
        i2cDevice.__init__(pig,address)
        Sensor.__init__()
        self.reset()
        self._start()

    def read(self):
        return self._convert(self._raw_read())

    def _raw_read(self,pig):
        '''
        Performs a read on the sensor, converts recieved bytearray, 
        discards the last two bytes (crc values - could implement in future),
        and returns a signed int converted from the big endian two 
        complement that remains.
        '''
        return int.from_bytes(self.read_device(4)[2],'big',signed=True)

    def reset(self):
        super.reset()
        self.write_word(0x2000)  # soft reset
        sleep(.08)                     # 80 ms soft reset time 

    def _start(self):
        self.write_word(0x1000)  # start measurement
        sleep(.1)                     # start-up time is 100 ms.

    def _convert(self,value):
        # Convert raw int to a flow reading represaented by a floating-point
        # number with units slm.
        # Source: https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/5_Mass_Flow_Meters/Application_Notes/Sensirion_Mass_Flo_Meters_SFM3xxx_I2C_Functional_Description.pdf
        return (value-self._FLOW_OFFSET)/self._FLOW_SCALE_FACTOR
	
class HumiditySensor(Sensor):
	__init__(self):
		pass
	
class TemperatureSensor(spiDevice):
	__init__(self):
		pass
