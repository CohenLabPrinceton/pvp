from pigpio import pi as PigPi
from abc import ABC, abstractmethod
import numpy as np
from collections import OrderedDict
from struct import pack,unpack

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
        self._pig.stop()

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
        self._i2c_bus = i2c_bus
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

    def read_word(self,signed=True):
        '''
        Read two bytes directly from the the device 
        without changing the register. 
        '''
        return self.__be16bytes_to_native(self._pig.i2c_read_device(self.handle),signed=signed)

    def write_word(self,word):
        '''
        Write two bytes to the device without specifying register.
        '''
        self._pig.i2c_write_data(self.handle,self.__native16_to_be(word))

    def read_register(self,register,signed=True):
        '''
        Read 2 bytes from the specified register(denoted by a single byte)
        '''
        return self.__be16_to_native(self._pig.i2c_read_word_data(self.handle,register),signed=signed)

    def write_register(self,register,word):
        '''
        Write 2 bytes to the specified register (denoted by a single byte)
        '''
        self._pig.i2c_write_word_data(self.handle,register,self.__native16_to_be(word))

    def __be16_to_native(self,word,signed):
        '''BigEndian to Native-endian conversion for signed 2 Byte integers (2 complement).'''
        if signed:  return unpack('@h',pack('>h',word))[0]
        else:       return unpack('@H',pack('>H',word))[0]

    def __native16_to_be(self,word):
        '''Little Endian to BigEndian conversion for unsigned 2Byte integers (2 complement).'''
        return unpack('@H',pack('>H',word))[0]

    def __be16bytes_to_native(self,data):
        '''UNpacks a bytearray of length 2 respecting big-endianness of the outside world and returns int '''
        if len(data) != 2:
            raise TypeError('Tried to call __byteswap on something that is most definitely not a two-complement')
        return unpack('>H',data)[0]

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

class Sensor(ABC):
    '''
    Abstract base Class describing generalized sensors
    '''
    def __init__(self):
        self._DATA  = np.zeros(128,dtype=np.float16)
        self._I     = 0
        self._N      = 128
        
    @property
    def data(self):
        '''
        Generalized, not performant. Returns an np.ndarray of observations
        arranged oldest to newest. Result has length equal to the lessor
        of self.n and the number of observations made.
        '''
        rolled = self._DATA.roll(self.n-self._I)
        return rolled[rolled.nonzero()]
        
    @property
    def n(self):
        return self._N
    
    @n.setter
    def n(self,new_n):
        ''' Set a new length for stored observations. Clears existing 
        observations and resets. '''
        self._N = new_n
        self.reset()
        
    @abstractmethod
    def read(self):
        self._I = (self._I + 1)%self.n
    
    def reset(self):
        self._DATA  = np.zeros(self.n)
        self._I     = 0

class Pin(IODeviceBase):
    
    _PIGPIO_MODES = {   'INPUT'     : 0,
                        'OUTPUT'    : 1,
                        'ALT5'      : 2,
                        'ALT4'      : 3,
                        'ALT0'      : 4,
                        'ALT1'      : 5,
                        'ALT2'      : 6,
                        'ALT3'      : 7 }
    
    def __init__(self,pin,pig=None):
        super().__init__(pig)
        self.pin=pin
        
    @property
    def mode(self):
        return map(reversed,self._PIGPIO_MODES.items())[ self._pig.get_mode(self.pin) ]
    
    @mode.setter
    def mode(self,mode):
        '''
        Performs validation on requested mode, then sets the mode. 
        Raises runtime error if something goes wrong.
        '''
        if mode not in self._PIGPIO_MODES.keys():
                raise ValueError("Pin mode must be one of: {}".format(self._PIGPIO_MODES.keys()))
        result = self._pig.set_mode(self.pin,self._PIGPIO_MODES[mode])
        
        # Pull error and print it
        if result != 0: raise RuntimeError('Failed to set mode % on pin %'%(mode,self.pin))
        
    def get(self):
        self._pig.read(self.pin)
        
    def set(self,value):
        if value not in (0,1): raise ValueError('Cannot set a value other than 0 or 1 to a Pin')
        self._pig.write(self.pin,value)

class InputPin(Pin):
    def __init__(self,pin,pig=None):
        super().__init__(pin,pig)
        self.mode = 'INPUT'
        
    def set(self,value):
        raise RuntimeWarning('set() was called on an InputPin')
        super().set(value)

class OutputPin(Pin):
    def __init__(self,pin,pig=None):
        super().__init__(pin,pig)
        self.mode = 'OUTPUT'

    def on(self):
        self._pig.write(self.pin,level=1)
    
    def off(self):
        self._pig.write(self.pin,level=0)
        
    def toggle(self):
        self._pig.write(self.pin,not self._pig.read(12))
        
    def get(self):
        super().get(value)

class PWMOutput(OutputPin):
    _DEFAULT_FREQUENCY      = 20000
    _DEFAULT_SOFT_FREQ      = 2000
    _HARDWARE_PWM_PINS      = (12, 13, 18, 19)
    def __init__(self,pin,initial_duty=0,frequency=None,pig=None):
        super().__init__(pin,pig)
        if pin not in self._HARDWARE_PWM_PINS:
            raise RuntimeWarning('PWMOutput called on pin % but that is not a PWM channel. Available frequencies will be limited.'%(self.pin))
            self.hardware_enabled   = False
            default_frequency = self._DEFAULT_SOFT_FREQ
        else:
            self.hardware_enabled = True
            default_frequency = self._DEFAULT_FREQUENCY
        self.__pwm(frequency if frequency is not None else default_frequency, initial_duty)
        
    @property
    def frequency(self):
        return self._pig.get_PWM_frequency(self.pin)
        
    @frequency.setter
    def frequency(self,new_frequency):
        ''' Description:
        Note: pigpio.pi.hardware_PWM() returns 0 if OK and an error code otherwise.
        - Tries to set hardware PWM if hardware_enabled
        - If that fails, or if not hardware_enabled, tries to set software PWM instead.'''
        self.__pwm(new_frequency,self.duty)
   
    @property        
    def duty(self):
        ''' Description:
        Returns the PWM duty cycle (pulled straight from pigpiod) mapped to the range [0-1] '''
        return self._pig.get_PWM_dutycycle(self.pin)/self._pig.get_PWM_range(self.pin)
        
    @duty.setter
    def duty(self,duty_cycle):
        ''' Description:
        Validation of requested duty cycle is performed here.
        Sets the PWM duty cycle to a value proportional to the input between (0,1) '''
        if not 0<duty_cycle<1: raise ValueError('Duty cycle must be between 0 and 1')
        self.__pwm(self.frequency,int(duty_cycle*self._pig.get_PWM_range(self.pin)))
        
    def get(self):
        '''Overloaded to return duty cycle instead of reading the value on the pin '''
        return self.duty
        
    def set(self,value):
        '''Overloaded to set duty cycle'''
        self.duty = value
    
    def on(self):
        ''' Same functionality as parent, but done with PWM intact'''
        self.duty = 1
    
    def off(self):
        ''' Same functionality as parent, but done with PWM intact'''
        self.duty = 0
        
    def __pwm(self,f,dc):
        ''' Description:
        -If hardware_enabled is True, start a hardware pwm with the requested duty. 
        -Otherwise (or if setting a hardware pwm fails and hardware_enabled is set to False),
         set a software pwm in the same manner.'''
        result = None
        if self.hardware_enabled:
            self.__hardware_pwm(new_frequency,self.duty)
        if not self.hardware_enabled:
            self.__software_pwm(new_frequency,self.duty)
        
    def __hardware_pwm(self,f,dc):
        ''' Description:
        -Tries to set a hardware pwm. result == 0 if it suceeds.
        -Sets hardware_enabled flag to indicate success or failure'''
        result = self._pig.hardware_PWM(self.pin,f,dc)
        if result != 0: 
            raise RuntimeWarning('Failed to start hardware PWM with frequency % on pin %. Error: %'%(f,self.pin,self._pig.error_text(result)))
            self.hardware_enabled = False
        else: 
            self.hardware_enabled = True
    
    def __software_pwm(self,f,dc):
        ''' Used for pins where hardware PWM is not available. '''
        self._pig.set_PWM_dutycycle(self.pin,dc)
        realized_frequency = self._pig.set_PWM_frequency(self.pin,self.new_frequency)
        if new_frequency != realized_frequency:
            raise RuntimeWarning('A PWM frequency of % was requested but the best that could be done was %'%(new_frequency,actual_frequency))
        self.hardware_enabled = False
