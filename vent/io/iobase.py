from pigpio import pi as PigPi
from abc import ABC, abstractmethod
from numpy import zeros,float16,roll
from collections import OrderedDict
from struct import pack,unpack


class IODeviceBase(ABC):
    ''' Abstract base Class for pigpio handles (or whatever other GPIO library
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
        self._pig.close(self.handle)


class i2cDevice(IODeviceBase):
    ''' A class wrapper for pigpio I2C handles. Defines several methods used for 
    reading from and writing to device registers. Defines helper classes Register
    and RegisterField for handling the manipulation of arbitrary registers.
    
    Note: The Raspberry Pi uses LE byte-ordering, while the outside
    world tends to use BE (at least, the sensors in use so far all do). 
    Thus, bytes need to be swapped from native (LE) ordering to BE 
    prior to being written to an i2c device, and bytes recieved need to 
    be swapped from BE into native (LE). All methods except read_device 
    and write_device perform this automatically. The methods read_device
    and write_device do NOT byteswap and return bytearrays rather than 
    the unsigned 16-bit int used by the other read/write methods.
    '''
    def __init__(self, i2c_address, i2c_bus, pig=None):
        super().__init__(pig)
        self._i2c_bus = i2c_bus
        self.open_i2c(i2c_bus,i2c_address)


    def read_device(self,num_bytes):
        ''' Read a specified number of bytes directly from the the device 
        without changing the register. Does NOT perform LE/BE conversion
        '''
        return self._pig.i2c_read_device(self.handle,num_bytes)[1]

    def write_device(self,data):
        ''' Write bytes to the device without specifying register.
        Does NOT perform LE/BE conversion
        '''
        self._pig.i2c_write_device(self.handle,data)

    def read_word(self):
        ''' Read two bytes directly from the the device without changing the register.'''
        return self.__be16bytes_to_native(self._pig.i2c_read_device(self.handle)[1])

    def write_word(self,wordbytes):
        ''' Write two bytes to the device without specifying register.'''
        self._pig.i2c_write_device(self.handle,self.__native16_to_be_bytes(wordbytes))

    def read_register(self,register,signed=False):
        ''' Read 2 bytes from the specified register(denoted by a single byte)'''
        return self.__be16_to_native(self._pig.i2c_read_word_data(self.handle,register),signed=signed)

    def write_register(self,register,word,signed=False):
        ''' Write 2 bytes to the specified register (denoted by a single byte)'''
        self._pig.i2c_write_word_data(self.handle,register,self.__native16_to_be(word,signed=signed))

    def __be16_to_native(self,word,signed):
        ''' BigEndian to Native-endian conversion for signed 2 Byte
        integers (2 complement).
        '''
        if signed:  return unpack('@h',pack('>h',word))[0]
        else:       return unpack('@H',pack('>H',word))[0]

    def __native16_to_be(self,word,signed = False):
        ''' Little Endian to BigEndian conversion for unsigned 2Byte
        integers (2 complement).
        '''
        if signed: return unpack('@h',pack('>h',word))[0]
        else: return unpack('@H',pack('>H',word))[0]

    def __be16bytes_to_native(self,data):
        ''' Unpacks a bytearray of length 2 respecting big-endianness of
        the outside world and returns int
        '''
        return unpack('>H',data)[0]
        
    def __native16_to_be_bytes(self,word):
        ''' Packs an int into a bytearray while swapping big-endianness of
        the pi and returns bytearray
        '''
        return pack('>H',word)

    class Register:
        ''' Describes a writable configuration register. Has Dynamically-defined
        attributes corresponding to the fields described by the passed arguments.
        Takes as arguments two tuples of equal length, the first of which
        names each field and the second being a tuple of tuples containing
        the (human readable) possible settings/values for each field.
        
        Note: The intializer reverses the fields & their values because 
        a human reads the register, as drawn in the datasheet, from left
        to right - however, the fields furthest to the left  
        '''
        def __init__(self,fields,values):
            self._fields = fields
            offset = 0
            for f,v in zip(reversed(fields),reversed(values)):
                setattr( self, f, self.RegisterField(offset, len(v)-1, OrderedDict(zip( v, range(len(v)) )) ) )
                offset += (len(v)-1).bit_length()
                
        def unpack(self,cfg):
            ''' Given the contents of a register in integer form, 
            returns a dict of fields and their current settings
            '''
            return OrderedDict(zip(self._fields, ( getattr(getattr(self,field), 'unpack' )(cfg) for field in self._fields )))
        
        def pack(self,cfg,**kwargs):
            ''' Given an initial integer representation of a register and an
            arbitrary number of field=value settings, returns an integer
            representation of the register incorporating the new settings.
            '''
            for field,value in kwargs.items():
                if hasattr(self,field) and value is not None:
                    cfg = getattr( getattr(self,field), 'insert' )(cfg,value)
            return cfg


        class RegisterField:
            ''' Describes a configurable field in a writable register.
            '''
            def __init__(self,offset,mask,values):
                self._offset    = offset
                self._mask      = mask
                self._values    = values
                
            def offset(self):
                return self._offset

            def info(self):
                ''' Returns a list containing stuff '''
                return [ self._offset, self._mask, self._values ]
            
            def unpack(self,cfg):
                ''' Extracts setting from passed 16-bit config & returns human readable result '''
                return OrderedDict(map(reversed,self._values.items()))[ self.extract(cfg) ]
            
            def pack(self,value):
                '''Takes a human-readable setting and returns a bit-shifted integer'''
                return self._values[value] << self._offset
                
            def insert(self,cfg,value):
                ''' 
                Performs validation and then does a bitwise replacement on passed config with
                the passed value. Returns integer representation of the new config.
                '''
                if value not in self._values.keys():
                    raise ValueError("RegisterField must be one of: {}".format(self._values.keys()))
                return ( cfg & ~(self._mask<<self._offset) )|( self._values[value] << self._offset )
                
            def extract(self,cfg):
                '''Extracts setting from passed 16-bit config & returns integer representation'''
                return ( cfg & (self._mask<<self._offset) )>>self._offset


class spiDevice(IODeviceBase):
    '''
    A class wrapper for pigpio SPI handles. Not implemented.
    '''
    def __init(self,pig,channel,baudrate):
        super().__init__(pig)
        self.open_spi(channel,baudrate)


class Sensor(ABC):
    '''
    Abstract base Class describing generalized sensors. Defines a mechanism
    for limited internal storage of recent observations and methods to
    pull that data out for external use. 
    '''
    _DEFAULT_STORED_OBSERVATIONS = 128
    
    def __init__(self):
        self._data  = zeros(self._DEFAULT_STORED_OBSERVATIONS,dtype=float16)
        self._i     = 0
        self._n     = self._DEFAULT_STORED_OBSERVATIONS
        
    @property
    def data(self):
        '''
        Generalized, not performant. Returns an np.ndarray of observations
        arranged oldest to newest. Result has length equal to the lessor
        of self.n and the number of observations made.
        '''
        rolled = roll(self._data,self.n-self._i)
        return rolled[rolled.nonzero()]
        
    @property
    def n(self):
        '''
        Returns the number of observations temporarily kept in the Sensor's
        internal np.ndarray. Once the ndarray has been filled, the sensor 
        begins overwriting the oldest elements of the ndarray with new
        observations such that the size of the internal storage stays 
        constant.
        '''
        return self._n
    
    @n.setter
    def n(self,new_n):
        ''' Set a new length for stored observations. Clears existing 
        observations and resets. '''
        self._n = new_n
        self.reset()
        
    @abstractmethod
    def read(self):
        self._i = (self._i + 1)%self.n
    
    def reset(self):
        self._data  = zeros(self.n)
        self._i     = 0


class AnalogSensor(Sensor):
    ''' Generalized class describing an analog sensor attached to an ADC.
    If instantiated without a subclass, represents a voltmeter with range 0-1.0.
    '''
# Change CONFIG fields to match convention 
    def __init__(   self, adc, channel,
                    calibration=(0,5,),
                    gain=None, data_rate=None, mode=None ):
        if type(calibration) != tuple:
                raise TypeError('arg calibration must be a tuple of the form (low,high)')
        super().__init__()
        self.channel    = channel
        self.gain       = adc._config.PGA.unpack(adc.cfg) if gain is None else gain
        self.data_rate  = adc._config.DR.unpack(adc.cfg) if data_rate is None else data_rate
        self.mode       = adc._config.MODE.unpack(adc.cfg) if mode is None else mode
        self.adc        = adc
        self.calibrate(calibration)
        
    def read(self):
        ''' Returns a value in the range of 0 - 1 corresponding to a fraction
        of the full input range of the sensor
        '''
        return self._convert(self._raw_read())
        
    def calibrate(self,calibration=None):
        if calibration is not None and type(calibration) != tuple:
            raise TypeError('arg calibration must be a tuple of the form (low,high)')
            
            # FIX THIS
        elif calibration is None: 
            self.calibration = calibration
        else:
            for i in range(50):
                self.read()
                print('Analog Sensor Calibration @ %6.4f V'%(self._DATA[self._N]),end='\r')
                time.sleep(.1)
            self.calibration[0] = np.mean(self.data(50))
            print('Calibrated low-end of Analog sensor  @ %6.4f V'%(self.calibration[0]))

    def _raw_read(self):
        ''' Returns raw voltage
        '''
        return self.adc.read(self.channel,self.gain,self.mode,self.data_rate)

    def _convert(self,raw):
        ''' Scales raw voltage into the range 0 - 1 
        '''
        return raw - self.calibration[0]/(self.calibration[1]-self.calibration[0])


class Pin(IODeviceBase):
    '''
    Base Class wrapping pigpio methods for interacting with GPIO pins on
    the raspberry pi. Subclasses include InputPin, OutputPin; along with
    any specialized pins or specific devices defined in vent.io.actuators
    & vent.io.sensors (note: actuators and sensors do not need to be tied 
    to a GPIO pin and may instead be interfaced through an ADC or I2C).
    
    When this class is initialized without a subclass, it represents a 
    fully-functional binary digital GPIO pin. The subclasses InputPin and
    OutputPin overload some functionaly of Pin in order to ensure the user
    is warned when they call methods that are not consistent with the 
    declared use (i.e. calling .set() on an InputPin).
    '''
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
    '''
    Subclass of Pin that should be used when calls to the pin should be  
    read-only during normal operation.
    That is, if a call is made to set the value on an InputPin, it will
    throw a runtime warning.
    '''
    def __init__(self,pin,pig=None):
        super().__init__(pin,pig)
        self.mode = 'INPUT'
        
    def set(self,value):
        raise RuntimeWarning('set() was called on an InputPin')
        super().set(value)


class OutputPin(Pin):
    '''
    Subclass of Pin that should be used when calls to the pin should be  
    write-only during normal operation.
    That is, if a call is made to get the value of an OutputPin, it will
    throw a runtime warning.
    '''
    def __init__(self,pin,pig=None):
        super().__init__(pin,pig)
        self.mode = 'OUTPUT'

    def on(self):
        self.set(1)
    
    def off(self):
        self.set(0)
        
    def toggle(self):
        self.set(not self._pig.read(self.pin))
        
    def get(self):
        raise RuntimeWarning('get() was called on an OutputPin')
        super().get()


class PWMOutput(OutputPin):
    '''
    I am a Special Pin!
    '''
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