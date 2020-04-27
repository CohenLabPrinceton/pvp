from pigpio import pi as PigPi
from abc import ABC, abstractmethod
import numpy as np
from collections import OrderedDict


class Ventilator:
    '''
    Class representation of the physical ventilator device
    '''
    def __init__(self):
        #self.pig = PigPi()
        pass
        
    def __del__(self):
        #self.pig.stop()
        pass
        
    def test(self,sensor):
        pass

    def calibrate(self):
        pass

class IODeviceBase(ABC):
    '''
    Abstract base Class for pigpio handles (or whatever other GPIO library
    we end up using)
    '''
    def __init__(self,pig):
        self._pig = pig if pig is not None else PigPi()

    def __del__(self):
        self.close()

    @property
    def handle(self):
        return self._handle
        
    def open_i2c(self,i2c_bus,i2c_address):
        self._handle = self._pig.i2c_open(i2c_bus,i2c_address)
        
    def open_spi(self,channel,baudrate):
        self._handle = self._pig.spi_open(channel,baudrate)

    def close(self):
        self._pig.close(self._handle)

class i2cDevice(IODeviceBase):
    '''
    A class wrapper for pigpio I2C handles 
    '''
    def __init__(self, i2c_address, i2c_bus, pig=None):
        super().__init__(pig)
        self.open_i2c(i2c_bus,i2c_address)

    def read_device(self,num_bytes):
        '''
        Read a specified number of bytes directly from the the device 
        without changing the register. Does NOT perform LE/BE conversion
        '''
        return self._pig.i2c_read_device(self.handle,num_bytes)

    def write_device(self,data):
        '''
        Write bytes to the device without specifying register.
        Does NOT perform LE/BE conversion
        '''
        self._pig.i2c_write_device(self.handle,data)

    def read_word(self):
        '''
        Read two words directly from the the device 
        without changing the register. 
        '''
        return self._be16_to_le(self._pig.i2c_read_word(self.handle))

    def write_word(self,word):
        '''
        Write two bytes to the device without specifying register.
        '''
        self._pig.i2c_write_word(self.handle,self._le16_to_be(word))

    def read_register(self,register):
        '''
        Read 2 bytes from the specified register(denoted by a single byte)
        '''
        return self._be16_to_le(self._pig.i2c_read_word_data(self.handle,register))

    def write_register(self,register,word):
        '''
        Write 2 bytes to the specified register (denoted by a single byte)
        '''
        self._pig.i2c_write_word_data(self.handle,register,self._le16_to_be(word))

    def _be16_to_le(self,word):
        '''BigEndian to LittleEndian conversion for signed 2 Byte integers (2 complement).'''
        if(word < 0):
            word = 2**16 + word
        return self._byteswap(word)

    def _le16_to_be(self,word):
        '''Little Endian to BigEndian conversion for unsigned 2Byte integers (2 complement).'''
        word = self._byteswap(word)
        #if(word >= 2**15):
        #    word = word-2**16
        return word

    def _byteswap(self,word):
        '''Revert Byte order for Words (2 Bytes, 16 Bit).'''
        word = (word>>8 |word<<8)&0xFFFF
        return word

    class Register:
        '''
        Describes a writable configuration register. Has Dynamically-defined
        attributes corresponding to the fields described by the passed arguments.
        Takes as arguments two tuples of equal length, the first of which
        names each field and the second being a tuple of tuples containing
        the (human readable) possible settings/values for each field.  
        '''
        def __init__(self,fields,values):
            self._fields = fields
            
            ''' Dynamically initialize attributes'''
            offset = 0
            for f,v in zip(reversed(fields),reversed(values)):
                setattr( self, f, self.ConfigField(offset, len(v)-1, OrderedDict(zip( v, range(len(v)) )) ) )
                offset += (len(v)-1).bit_length()
                
        def unpack(self,cfg):
            '''
            Given the contents of a register in integer form, returns a dict of fields and their current settings
            '''
            return OrderedDict(zip(self._fields, ( getattr(getattr(self,field), 'unpack' )(cfg) for field in self._fields )))
        
        def pack(self,cfg,**kwargs):
            '''
            Given an initial integer representation of a register and an
            arbitrary number of field=value settings, returns an integer
            representation of the register incorporating the new settings
            '''
            for field,value in kwargs.items():
                if hasattr(self,field) and value is not None:
                    cfg = getattr( getattr(self,field), 'insert' )(cfg,value)
            return cfg

        class ConfigField:
            '''
            Describes a configurable field in a writable register.
            '''
            def __init__(self,offset,mask,values):
                self._OFFSET    = offset
                self._MASK      = mask
                self._VALUES    = values
                
            def offset(self):
                return self._OFFSET

            def info(self):
                ''' Returns a list containing stuff '''
                return [ self._OFFSET, self._MASK, self._VALUES ]
            
            def unpack(self,cfg):
                ''' Extracts setting from passed 16-bit config & returns human readable result '''
                return OrderedDict(map(reversed,self._VALUES.items()))[ self.extract(cfg) ]
            
            def pack(self,value):
                '''Takes a human-readable setting and returns a bit-shifted integer'''
                return self._VALUES[value] << self._OFFSET
                
            def insert(self,cfg,value):
                ''' 
                Performs validation and then does a bitwise replacement on passed config with
                the passed value. Returns integer representation of the new config.
                '''
                if value not in self._VALUES.keys():
                    raise ValueError("ConfigField must be one of: {}".format(self._VALUES.keys()))
                return ( cfg & ~(self._MASK<<self._OFFSET) )|( self._VALUES[value] << self._OFFSET )
                
            def extract(self,cfg):
                '''Extracts setting from passed 16-bit config & returns integer representation'''
                return ( cfg & (self._MASK<<self._OFFSET) )>>self._OFFSET

class spiDevice(IODeviceBase):
    '''
    A class wrapper for pigpio SPI handles. Not implemented.
    '''
    def __init(self,pig,channel,baudrate):
        super().__init__(pig)
        self.open_spi(hannel,baudrate)

class Sensor(abc.ABC):
    '''
    Abstract base Class describing generalized sensors
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
        
    @abstractmethod
    def read(self):
        self._N +=1
    
    def reset(self):
        self._DATA  = np.zeros(128)
        self._N     = 0
        
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


#TODO
class Pin(IODeviceBase)
	def __init__(self):
		pass

class InputPin(Pin)
	def __init__(self):
		pass

class OutputPin(Pin)
	def __init__(self):
		pass

class PWMOutput(OutputPin)
	def __init__(self):
		pass
