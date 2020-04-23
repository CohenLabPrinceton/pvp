import pigpio
import struct
from time import sleep

class hardware:
	# defines the GPIO interface (pigpio.io())
	# prepares SensorValues message
	self.pig = pigpio.pi()
	
	# Initializes sensors
	# does calibration
	

	
class Sensor():
	# Abstract class defining general sensor API
	
class FlowSensor(Sensor):
	
class PressureSensor(Sensor):
	
class OxygenSensor(Sensor):
	
class HumiditySensor(Sensor):
	
class TemperatureSensor(Sensor):

class Valve():
	
class SolenoidValve(Valve):
	
class ProportionalValve(Valve):
	
class ADS1x15:
    """Base functionality for ADS1x15 analog to digital converters."""
    
    _ADS1X15_DEFAULT_ADDRESS = 0x48
    _ADS1X15_POINTER_CONVERSION = 0x00
    _ADS1X15_POINTER_CONFIG = 0x01
    _ADS1X15_CONFIG_OS_SINGLE = 0x8000
    _ADS1X15_CONFIG_MUX_OFFSET = 12
    _ADS1X15_CONFIG_COMP_QUE_DISABLE = 0x0003
    _ADS1X15_CONFIG_MODE = {
        'CONTINUOUS' : 0x0000,
        'SINGLE' : 0x0100
        }
    _ADS1X15_CONFIG_GAIN = {
        2 / 3: 0x0000,
        1: 0x0200,
        2: 0x0400,
        4: 0x0600,
        8: 0x0800,
        16: 0x0A00,
        }
    # Channels
    _ADS1X15_CHANNELS = { 
        (0, 1): 0,
        (0, 3): 1,
        (1, 3): 2,
        (2, 3): 3,
        0 : 4,
        1 : 5,
        2 : 6,
        3 : 7
        }

    _ADS1X15_PGA_RANGE = {2 / 3: 6.144, 1: 4.096, 2: 2.048, 4: 1.024, 8: 0.512, 16: 0.256}
    
    def __init__(
        self, pig, channel=0, gain=1, data_rate=None,
        mode='SINGLE',
        address=_ADS1X15_DEFAULT_ADDRESS ):
        
        self._last_channel  = None
        self.word           = 0
        self.pig            = pig
        self.i2c_device     = self.pig.i2c_open(1, address)
        data_rate           = self._data_rate_default() if data_rate is None else data_rate        
        self.set_config(channel,gain,data_rate,mode)
        
    def get_voltage(self,channel,gain=None,data_rate=None,mode=None):
        return self.get_raw(channel,gain,data_rate,mode)*self._ADS1X15_PGA_RANGE[self.gain] / 32767
    
    def get_raw(self, channel, gain=None,data_rate=None,mode=None):
        if (channel != self._last_channel or any(c is not None for c in (gain,data_rate,mode))):
            self._last_channel = channel
            self.set_config(channel,gain,data_rate,mode)
            sleep(1/self.data_rate)
            while not self._conversion_complete():
                pass
        elif self.mode == 'SINGLE':
            self._write_register(self._ADS1X15_POINTER_CONFIG, self.config)
            sleep(1/self.data_rate)
            while not self._conversion_complete():
                pass
        return self._conversion_value(self.get_last_result()) << (16 - self._bits)
        
    @property
    def channel(self):
        return self._channel
    
    @channel.setter
    def channel(self,channel):
        possible_channels = self.get_channels()
        if channel not in possible_channels:
            raise ValueError("Channel must be one of: {}".format(list(possible_channels)))
        self._channel = self._ADS1X15_CHANNELS[channel]
            
    @property
    def gain(self):
        """The ADC gain."""
        return self._gain
        
    @gain.setter
    def gain(self, gain):
        possible_gains = self.get_gains()
        if gain not in possible_gains:
            raise ValueError("Gain is {} but must be one of: {}".format(gain,possible_gains))
        self._gain = gain
        
    @property
    def data_rate(self):
        """The data rate for ADC conversion in samples per second."""
        return self._data_rate

    @data_rate.setter
    def data_rate(self, rate):
        possible_rates = self.get_rates()
        if rate not in possible_rates:
            raise ValueError("Data rate must be one of: {}".format(possible_rates))
        self._data_rate = rate

    @property
    def mode(self):
        """The ADC conversion mode."""
        return self._mode

    @mode.setter
    def mode(self, mode):
        possible_modes = self.get_modes()
        if mode not in possible_modes:
            raise ValueError("Mode must be one of: {}".format(possible_modes))
        self._mode = mode
        
    @property
    def config(self):
        """The word to be written to the config register"""
        return self._config
    
    @config.setter
    def config(self):
        raise NotImplementedError("Must use set_config(gain,mode) to set config.")
    
    def set_config(self,channel,gain=None,data_rate=None,mode=None):
        self.channel = channel
        if gain is not None: self.gain = gain
        if mode is not None: self.mode = mode
        if data_rate is not None: self.data_rate = data_rate
        self._config = self._ADS1X15_CONFIG_OS_SINGLE
        self._config |= (self.channel & 0x07) << self._ADS1X15_CONFIG_MUX_OFFSET
        self._config |= self._ADS1X15_CONFIG_GAIN[self.gain]
        self._config |= self._ADS1X15_CONFIG_MODE[self.mode]
        self._config |= self._CONFIG_DR[self.data_rate]
        self._config |= self._ADS1X15_CONFIG_COMP_QUE_DISABLE
        self._write_register(self._ADS1X15_POINTER_CONFIG, self.config)
        
    def get_channels(self):
        c = list(self._ADS1X15_CHANNELS.keys())
        return c
        
    def get_gains(self):
        """Possible gain settings."""
        g = list(self._ADS1X15_CONFIG_GAIN.keys())
        g.sort()
        return g

    def get_rates(self):
        """Possible data rate settings."""
        raise NotImplementedError("Subclass must implement rates property.")

    def get_modes(self):
        """Possible modes."""
        m = list(self._ADS1X15_CONFIG_MODE.keys())
        m.sort()
        return m

    @property
    def _CONFIG_DR(self):
        """Rate configuration masks."""
        raise NotImplementedError("Subclass must implement CONFIG_DR property.")

    def _data_rate_default(self):
        """Retrieve the default data rate for this ADC (in samples per second).
        Should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _data_rate_default!")

    def _conversion_value(self, raw_adc):
        """Subclasses should override this function that takes the 16 raw ADC
        values of a conversion result and returns a signed integer value.
        """
        raise NotImplementedError("Subclass must implement _conversion_value function!")
    
    def _bits(self):
        raise NotImplementedError("Subclass must implement _bits() function!")
        
    def _conversion_complete(self):
        """Return status of ADC conversion."""
        # OS is bit 15
        # OS = 0: Device is currently performing a conversion
        # OS = 1: Device is not currently performing a conversion
        return self._read_register(self._ADS1X15_POINTER_CONFIG) & 0x8000

    def get_last_result(self):
        return self._read_register(self._ADS1X15_POINTER_CONVERSION)

    def _write_register(self, reg, word):
        """Write 16 bit value to register."""
        self.word = self.b2l(word)
        self.pig.i2c_write_word_data(self.i2c_device,reg,self.word)

    def _read_register(self, reg):
        """Read 16 bit register value. If fast is True, the pointer register
        is not updated.
        """
        self.word = self.pig.i2c_read_word_data(self.i2c_device,reg)
        return self.b2l(self.word)
    
    def byteSwap(self,word):
        '''Revert Byte order for Words (2 Bytes, 16 Bit).'''
        word = (word>>8 |word<<8)&0xFFFF
        return word

    def b2l(self,word):
        '''BigEndian to LittleEndian conversion for signed 2 Byte integers (2 complement).'''
        if(word < 0):
            word = 2**16 + word
        return self.byteSwap(word)

class ads1015(ADS1x15):
    """Class for the ADS1015 12 bit ADC."""
        
    @property
    def _bits(self):
        """The ADC bit resolution."""
        return 12
    
    @property
    def _CONFIG_DR(self):
        """Data sample rates"""
        return {
            128: 0x0000,
            250: 0x0020,
            490: 0x0040,
            920: 0x0060,
            1600: 0x0080,
            2400: 0x00A0,
            3300: 0x00C0 }


    def get_rates(self):
        """Possible data rate settings."""
        r = list(self._CONFIG_DR.keys())
        r.sort()
        return r

    def _data_rate_default(self):
        return 1600

    def _conversion_value(self, raw_adc):
        raw_adc = raw_adc.to_bytes(2, "big")
        value = struct.unpack(">h", raw_adc)[0]
        return value >> 4

class ads1115(ADS1x15):
    """Class for the ADS1115 16 bit ADC."""
    


    @property
    def _bits(self):
        """The ADC bit resolution."""
        return 16
        
    @property
    def _CONFIG_DR(self):
        """Data sample rates"""
        return {
            8: 0x0000,
            16: 0x0020,
            32: 0x0040,
            64: 0x0060,
            128: 0x0080,
            250: 0x00A0,
            475: 0x00C0,
            860: 0x00E0,
    }

    def get_rates(self):
        """Possible data rate settings."""
        r = list(self._CONFIG_DR.keys())
        r.sort()
        return r

    def _data_rate_default(self):
        return 860

    def _conversion_value(self, raw_adc):
        raw_adc = raw_adc.to_bytes(2, "big")
        value = struct.unpack(">h", raw_adc)[0]
        return value
