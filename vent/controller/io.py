import pigpio
import struct
import abc
import numpy as np
from time import sleep

class Ventilator:
    '''
    Class representation of the physical ventilator device
    '''
    def __init__(self):
        self.pig = pigpio.pi()
	
    def __del__(self):
        self.pig.stop()

    def test(self,sensor):
        return result

    def calibrate(self):
        return


class Device(abc.ABC):
    '''
    Abstract class for pigpio handles
    '''
    def __init__(self,pig):
        self._pig = pig

    def __del__(self):
        self.close()

    @property
    def handle(self):
        return self._handle

    def close(self):
        self._handle.close()

class i2cDevice(Device):
    '''
    A class wrapper for pigpio I2C handles 
    '''
    def __init__(self,pig,i2c_address,i2c_bus=1):
        super().__init__(pig)
        self._handle    = self._pig.i2c_open(i2c_bus,i2c_address)

    def read_device(self,num_bytes):
        '''
        Read a specified number of bytes directly from the the device 
        without changing the register. Does NOT perform LE/BE conversion
        '''
        return self._pig.i2c_read_device(self._handle,num_bytes)

    def write_device(self,data):
        '''
        Write bytes to the device without specifying register.
        Does NOT perform LE/BE conversion
        '''
        self._pig.i2c_write_device(self._handle,data)

    def read_word(self):
        '''
        Read two words directly from the the device 
        without changing the register. 
        '''
        return self._be16_to_le(self._pig.i2c_read_word(self._handle))

    def write_word(self,word):
        '''
        Write two bytes to the device without specifying register.
        '''
        self._pig.i2c_write_word(self._handle,self._le16_to_be(word))

    def read_register(self,register):
        '''
        Read 2 bytes from the specified register(denoted by a single byte)
        '''
        return self._be16_to_le(self._pig.i2c_read_word_data(self._handle,register))

    def write_register(self,register,word):
        '''
        Write 2 bytes to the specified register (denoted by a single byte)
        '''
        self._pig.i2c_write_word_data(self._handle,register,self._le16_to_be(word))

    def _be16_to_le(self,word):
        '''BigEndian to LittleEndian conversion for signed 2 Byte integers (2 complement).'''
        if(word < 0):
            word = 2**16 + word
        return self._byteswap(word)

    def _le16_to_be(self,word):
        '''Little Endian to BigEndian conversion for signed 2Byte integers (2 complement).'''
        word = self._byteswap(word)
        if(word >= 2**15):
            word = word-2**16
        return word

    def _byteswap(self,word):
        '''Revert Byte order for Words (2 Bytes, 16 Bit).'''
        word = (word>>8 |word<<8)&0xFFFF
        return word

class spiDevice(Device):
    '''
    A class wrapper for pigpio SPI handles. Not implemented.
    '''
    def __init(self,pig,spi_channel,baudrate):
        super().__init__(pig)
        self._handle = self._pig.spi_open(spi_channel,baudrate)
        	
class ads1115(i2cDevice):  # This should inherit from i2cInterface - change i2c_device to match convention & whatever else needs to happen
    '''
    Class for the ADS1115 16 bit, 4 Channel Analog to Digital Converter
    '''
    ''' Default config values & other hardware descriptors'''
    _POINTER_CONVERSION     = 0x00
    _POINTER_CONFIG         = 0x01
    _DEFAULT_ADDRESS        = 0x48
    _DEFAULT_CHANNEL        = 0
    _DEFAULT_GAIN           = 1
    _DEFAULT_DATA_RATE      = 860
    _DEFAULT_MODE           = 'SINGLE'
    _CONFIG_OS_SINGLE       = 0x8000
    _CONFIG_MUX_OFFSET      = 12
    _CONFIG_COMP_QUE_DISABLE = 0x0003
    '''Maps pins & differential combinations of pins to channels'''
    _CONFIG_CHANNELS = {
        (0, 1): 0,
        (0, 3): 1,
        (1, 3): 2,
        (2, 3): 3,
        0 : 4,
        1 : 5,
        2 : 6,
        3 : 7 }
    '''Possible gain settings'''
    _CONFIG_GAIN = {   
        2 / 3: 0x0000,
        1: 0x0200,
        2: 0x0400,
        4: 0x0600,
        8: 0x0800,
        16: 0x0A00 }
    _CONFIG_MODE = { 'CONTINUOUS' : 0x0000, 'SINGLE' : 0x0100 }
    """Data sample rates"""
    _CONFIG_DATA_RATE = {
            8: 0x0000,
            16: 0x0020,
            32: 0x0040,
            64: 0x0060,
            128: 0x0080,
            250: 0x00A0,
            475: 0x00C0,
            860: 0x00E0 }
    '''human readable gains'''
    _PGA_RANGE = {
        2 / 3: 6.144,
        1: 4.096,
        2: 2.048,
        4: 1.024,
        8: 0.512,
        16: 0.256}
    
    def __init__(self, pig, address=_DEFAULT_ADDRESS):
        super().__init__(pig,address)
        self.channel    = self._DEFAULT_CHANNEL
        self.gain       = self._DEFAULT_GAIN
        self.data_rate  = self._DEFAULT_DATA_RATE
        self.mode       = self._DEFAULT_MODE
        self.config     = (self.channel,self.gain,self.data_rate,self.mode)

    @property
    def channel(self):
        '''Returns the human-readable definition of the channel spcified by the current register''' 
        return dict(map(reversed,self._CONFIG_CHANNELS.items()))[self._CHANNEL >> self._CONFIG_MUX_OFFSET]

    @property
    def gain(self):
        """The ADC gain."""
        return dict(map(reversed,self._CONFIG_GAIN.items()))[self._GAIN]

    @property
    def data_rate(self):
        """The data rate for ADC conversion in samples per second."""
        return dict(map(reversed,self._CONFIG_DATA_RATE.items()))[self._DATA_RATE]

    @property
    def mode(self):
        """The ADC conversion mode."""
        return dict(map(reversed,self._CONFIG_MODE.items()))[self._MODE]

    @property
    def config(self):
        """The word to be written to the config register"""
        return {'channel'   : self.channel,
                'gain'      : self.gain,
                'data_rate' : self.data_rate,
                'mode'      : self.mode }
    '''Overloaded property.setters'''

    @channel.setter
    def channel(self,channel):
        possible_channels = self.get_channels()
        if channel not in possible_channels:
            raise ValueError("Channel must be one of: {}".format(list(possible_channels)))
        self._CHANNEL = self._CONFIG_CHANNELS[channel] << self._CONFIG_MUX_OFFSET
            
    @gain.setter
    def gain(self, gain):
        possible_gains = self.get_gains()
        if gain not in possible_gains:
            raise ValueError("Gain is {} but must be one of: {}".format(gain,possible_gains))
        self._GAIN = self._CONFIG_GAIN[gain]

    @data_rate.setter
    def data_rate(self, rate):
        possible_rates = self.get_rates()
        if rate not in possible_rates:
            raise ValueError("Data rate must be one of: {}".format(possible_rates))
        self._DATA_RATE = self._CONFIG_DATA_RATE[rate]

    @mode.setter
    def mode(self, mode):
        possible_modes = self.get_modes()
        if mode not in possible_modes:
            raise ValueError("Mode must be one of: {}".format(possible_modes))
        self._MODE = self._CONFIG_MODE[mode]
    
    @config.setter
    def config(self,channel=None,gain=None,data_rate=None,mode=None):
        new_and_old = zip( (channel,gain,data_rate,mode), (self.channel,self.gain,self.data_rate,self.mode) )
        if not any(new is not None and new !=old for new,old in new_and_old):
            pass
        else:
            self._CONFIG = self._CONFIG_OS_SINGLE
            for config,new_config in new_and_old:
                if new_config != config: config = new_config 
                self._CONFIG |= config
            self.write_register(self._POINTER_CONFIG, self._CONFIG)

    def read(self,channel,gain=None,data_rate=None,mode=None):
        return self.raw_read(channel,gain,data_rate,mode)*self._PGA_RANGE[self.gain] / 32767
    
    def raw_read(self, channel, gain=None,data_rate=None,mode=None):
        '''
        Checks to see whether new config values  were passed, and if
        they were, whether they are different from the current config.
        If there are new values that are different, set the new config.
        If ADC is in single-shot mode, or if a new config was set, wait
        until the conversion is ready. Finally, read the value in the
        conversion register.
        '''
        if self.mode == 'SINGLE':
            self.write_register(self._POINTER_CONFIG, self._CONFIG)
            sleep(1/self.data_rate)
            while not self.ready():
                sleep(1/self.data_rate/10)
        return self.read_register(self._POINTER_CONVERSION)
    
    def ready(self):
        """Return status of ADC conversion."""
        # OS is bit 15
        # OS = 0: Device is currently performing a conversion
        # OS = 1: Device is not currently performing a conversion
        return self.read_register(self._POINTER_CONFIG) & 0x8000

    def get_channels(self):
        c = list(self._CONFIG_CHANNELS.keys())
        return c
        
    def get_gains(self):
        """Possible gain settings."""
        g = list(self._CONFIG_GAIN.keys())
        g.sort()
        return g

    def get_rates(self):
        """Possible data rate settings."""
        r = list(self._CONFIG_DATA_RATE.keys())
        r.sort()
        return r

    def get_modes(self):
        """Possible modes."""
        m = list(self._CONFIG_MODE.keys())
        m.sort()
        return m

class Sensor(abc.ABC):
    '''
    Class describing generalized sensors
    '''
    def __init__(self):
        _DATA   = np.zeros(128)
        _N      = 0
    @property
    def data(self,n=None):
        if n is None: return _DATA
        else: return _DATA[n]
        
    @property 
    def n(self):
        return self._N
        
    @abc.abstractmethod
    def read(self):
        self._N +=1
    
    def reset(self):
        self._DATA  = np.zeros(128)
        self._N     = 0

    
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
        time.sleep(.08)                     # 80 ms soft reset time 

    def _start(self):
        self.write_word(0x1000)  # start measurement
        time.sleep(.1)                     # start-up time is 100 ms.

    def _convert(self,value):
        # Convert raw int to a flow reading represaented by a floating-point
        # number with units slm.
        # Source: https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/5_Mass_Flow_Meters/Application_Notes/Sensirion_Mass_Flo_Meters_SFM3xxx_I2C_Functional_Description.pdf
        return (value-self._FLOW_OFFSET)/self._FLOW_SCALE_FACTOR
	
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
            
class P4vMini(Sensor):
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

# ~ class OxygenSensor(Sensor):
	
# ~ class HumiditySensor(Sensor):
	
# ~ class TemperatureSensor(Sensor):

# ~ class Valve():
	
# ~ class SolenoidValve(Valve):
	
# ~ class ProportionalValve(Valve):
