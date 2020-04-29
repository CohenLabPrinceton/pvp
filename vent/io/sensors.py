from .iobase import Sensor, i2cDevice, spiDevice
from time import sleep

'''
Subclass implementations of specific sensor devices.
'''

         
class P4vMini(AnalogSensor):
    ''' Analog gauge pressure sensor with range of 0 - 20" h20. The
    calibration outlined in the datasheet has low =  0.25V and 
    high = 4.0V (give or take a bit). The conversion factor is derived 
    from the sensor's maximum output of 20 in(h20), and we want sensor 
    readings in cm h20: (2.54 cm/in * 20" h20) * read() = observed cmh20
    '''
    _DEFAULT_OFFSET_VOLTAGE = 0.25
    _DEFAULT_OUTPUT_SPAN    = 4
    '''  '''
    _CONVERSION_FACTOR      = 2.54*20 

    def __init__(self,adc,channel,calibration = (_DEFAULT_OFFSET_VOLTAGE,
				 _DEFAULT_OUTPUT_SPAN ),gain=1,data_rate=860,mode=None):
        super().__init__(	adc,
							channel,
							calibration,
							gain,
							data_rate,
							mode )
		# A check here to make sure calibrated offset voltage is 
		#  reasonablyclose to what is currently coming from the sensor
		#	would be prudent. A warning is probably sufficient.   
		
    def read(self):
		''' Overloaded to convert the superclass normalized output into 
		the desired units: cm(h20)'''
        return self._CONVERSION_FACTOR*super()._read()


class OxygenSensor(AnalogSensor):
	''' Not yet implemented.
	'''
	def __init__(self):
		pass


class SFM3200(Sensor,i2cDevice):
    ''' Datasheet:
		 https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/ ...
			... 5_Mass_Flow_Meters/Datasheets/Sensirion_Mass_Flow_Meters_SFM3200_Datasheet.pdf
    '''
    _DEFAULT_ADDRESS     = 0x40 
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
        ''' Performs a read on the sensor, converts recieved bytearray, 
        discards the last two bytes (crc values - could implement in future),
        and returns a signed int converted from the big endian two 
        complement that remains.
        '''
        return unpack('>H',self.read_device(4)[2:])[0]

    def reset(self):
		''' Asks the sensor to perform a soft reset. Also resets internal
		data. 80 ms soft reset time 
		'''
        super.reset()
        self.write_word(0x2000)
        sleep(.08)                     

    def _start(self):
		''' Sends the 'start measurement' command to the sensor. Start-up
		time once command has been recieved is 'less than 100ms'
        '''
        self.write_word(0x1000) 
        sleep(.1)

    def _convert(self,value):
        ''' Convert raw int to a flow reading having type float with
        units slm. Source: 
        
        https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/ ...
			... 5_Mass_Flow_Meters/Application_Notes/Sensirion_Mass_Flo_Meters_SFM3xxx_I2C_Functional_Description.pdf
        '''
        return (value-self._FLOW_OFFSET)/self._FLOW_SCALE_FACTOR


class HumiditySensor(Sensor):
	''' Not yet implemented.
	'''
	def __init__(self):
		pass


class TemperatureSensor(spiDevice):
	''' Not yet implemented
	'''
	def __init__(self):
		pass
