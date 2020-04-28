from .iobase import Sensor, i2cDevice, spiDevice
from struct import pack, unpack
from time import sleep

'''
Class Definitions for specific sensor devices.
'''

class AnalogSensor(Sensor):
    '''
    General class describing an anlog sensor attached to an ADC.
    If instantiated without a subclass, represents a voltmeter with range 0-1.0.
    '''
    def __init__(   self, adc, channel,
                    calibration=(0,5,),
                    gain=None, data_rate=None, mode=None ):
        if type(calibration) != tuple:
                raise TypeError('arg calibration must be a tuple of the form (low,high)')
        super().__init__()
        self.channel    = channel
        self.gain       = adc.gain if gain is None else gain
        self.data_rate  = adc.data_rate if data_rate is None else data_rate
        self.mode       = adc.mode if mode is None else mode
        
    def read(self):
        '''
        Returns a value in the range of 0 - 1 corresponding to a fraction
        of the full input range of the sensor
        '''
        return self._convert(self._raw_read())
        
    def calibrate(self,calibration=None):
        if calibration is not None:
            if type(calibration) != tuple:
                raise TypeError('arg calibration must be a tuple of the form (low,high)')
            elif calibration is not None: 
                self.calibration = calibration
            else:
                for i in range(50):
                    self.read()
                    print('Analog Sensor Calibration @ %6.4f V'%(self._DATA[self._N]),end='\r')
                    time.sleep(.1)
                self.calibration[0] = np.mean(self.data(50))
                print('Calibrated low-end of Analog sensor  @ %6.4f V'%(self.calibration[0]))

    def _raw_read(self):
        '''
        Returns raw voltage
        '''
        return self.adc.get_voltage(self.channel,self.gain,self.data_rate,self.mode)

    def _convert(self,raw):
        '''
        Scales raw voltage into the range 0 - 1 
        '''
        return raw - calibration[0]/(calibration[1]-calibration[0])
            
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
        super().__init__(adc, channel, calibration, gain, data_rate, mode)

    def _convert(self,raw):
        return self._conversion_factor*self.read()

class OxygenSensor(AnalogSensor):
	def __init__(self):
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
        return unpack('>H',self.read_device(4)[2:])[0]

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
	def __init__(self):
		pass
	
class TemperatureSensor(spiDevice):
	def __init__(self):
		pass
