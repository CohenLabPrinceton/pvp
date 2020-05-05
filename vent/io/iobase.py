''' Provides the abstract classes and classes for basic objects like
pins, to be used for higher-level operations by the "device" objects.
'''
from abc import ABC, abstractmethod
from collections import OrderedDict
import time
import numpy as np
import pigpio


class IODeviceBase(ABC):
    ''' Abstract base Class for pigpio handles (or whatever other GPIO library
    we end up using)

    Note: pigpio commands return -144 if an error is encountered while
    attempting to communicate with the demon. TODO would be to recognize
    when that occurs and handle it gracefully, i.e. kill the daemon,
    restart it, and reopen the python interface(s)
    '''

    def __init__(self, pig):
        ''' Initializes the pigpio python bindings oject if necessary,
        and checks that it is actually running.
        '''
        self._pig = pig if pig is not None else pigpio.pi()
        self._handle = -1
        if not self.pigpiod_ok():
            raise RuntimeError

    def __del__(self):
        ''' Closes the i2c/spi connection, and stops the python bindings
        for the pigpio daemon.
        '''
        self.close()
        if self.pigpiod_ok:
            self.pig.stop()

    @property
    def pig(self):
        ''' The pigpio python bindings object
        '''
        return self._pig

    @property
    def handle(self):
        ''' Pigpiod handle associated with device (only for i2c/spi)
        '''
        return self._handle

    def pigpiod_ok(self):
        ''' Returns True if pigpiod is running and False if not
        '''
        return self.pig.connected

    def close(self):
        ''' Closes an I2C/SPI (or potentially Serial) connection
        '''
        if not self.pigpiod_ok() or self.handle <= 0:
            return


def be16_to_native(data, signed=False, count=2):
    ''' Unpacks a bytearray respecting big-endianness of outside world
    and returns an int according to signed.
    '''
    return int.from_bytes(data[1][:count],'big',signed=signed)


def native16_to_be(word, signed=False, count=2):
    ''' Packs an int into a bytearray while swapping big-endianness
    of the pi and returns bytearray
    '''
    return word.to_bytes(count,'big',signed=signed)


class I2CDevice(IODeviceBase):
    ''' A class wrapper for pigpio I2C handles. Defines several methods
    used for reading from and writing to device registers. Defines
    helper classes Register and RegisterField for handling the
    manipulation of arbitrary registers.

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
        ''' Initializes pigpio bindings and opens i2c connection.
        '''
        super().__init__(pig)
        self._i2c_bus = i2c_bus
        self.open(i2c_bus, i2c_address)

    def open(self, i2c_bus, i2c_address):
        ''' Opens i2c connection given i2c bus and address.
        '''
        self._handle = self.pig.i2c_open(i2c_bus, i2c_address)

    def close(self):
        ''' Extends superclass method. Checks that pigpiod is connected
        and if a handle has been set - if so, closes an i2c connection.
        '''
        super().close()
        self.pig.i2c_close(self.handle)

    def read_device(self, num_bytes):
        ''' Read a specified number of bytes directly from the the
        device without changing the register. Does NOT perform LE/BE
        conversion.
        '''
        return self.pig.i2c_read_device(self.handle, num_bytes)

    def write_device(self, word, signed=False, count=2):
        ''' Write bytes to the device without specifying register.
        DOES perform LE/BE conversion. Count should be
        specified for when passing something other than a word.
        '''
        self.pig.i2c_write_device(
            self.handle,
            native16_to_be(word,signed=signed,count=count)
        )

    def read_register(self, register, signed=False, count=2):
        ''' Read count# bytes from the specified register
        (denoted by a single byte)
        '''
        return be16_to_native(
            self.pig.i2c_read_i2c_block_data(
                self.handle,
                register,
                count
            ),
            signed=signed
        )

    def write_register(self, register, word,signed=False,count=2):
        ''' Write bytes to the specified register. Count should be
        specified for when passing something other than a word.
        (register denoted by a single byte)
        '''
        self.pig.i2c_write_i2c_block_data(
            self.handle,
            register,
            native16_to_be(word, signed=signed, count=count)
        )

    class Register:
        ''' Describes a writable configuration register. Has dynamically
        defined attributes corresponding to the fields described by the
        passed arguments. Takes as arguments two tuples of equal length,
        the first of which names each field and the second being a tuple
        of tuples containing the (human readable) possible settings &
        values for each field.

        Note: The intializer reverses the fields & their values because
        a human reads the register, as drawn in the datasheet, from left
        to right - however, the fields furthest to the left are the most
        significant bits of the register.
        '''
        def __init__(self, fields, values):
            ''' Initializer which loads in (dynamically defined)
            attributes.
            '''
            self.fields = fields
            offset = 0
            for fld,val in zip(reversed(fields), reversed(values)):
                setattr(
                    self,
                    fld,
                    self.RegisterField(
                        offset,
                        len(val) - 1,
                        OrderedDict(zip(val, range(len(val))))
                    )
                )
                offset += (len(val) - 1).bit_length()

        def unpack(self, cfg):
            ''' Given the contents of a register in integer form,
            returns a dict of fields and their current settings
            '''
            return OrderedDict(zip(
                    self.fields,
                    (getattr(
                        getattr(self,field),
                        'unpack' )(cfg) for field in self.fields)
                ))

        def pack(self, cfg, **kwargs):
            ''' Given an initial integer representation of a register and an
            arbitrary number of field=value settings, returns an integer
            representation of the register incorporating the new settings.
            '''
            for field, value in kwargs.items():
                if hasattr(self, field) and value is not None:
                    cfg = getattr( getattr(self, field), 'insert' )(cfg, value)
            return cfg


        class RegisterField:
            ''' Describes a configurable field in a writable register.
            '''
            def __init__(self, offset, mask, values):
                self._offset    = offset
                self._mask      = mask
                self._values    = values

            def offset(self):
                ''' Returns the position of the field's LSB in the
                register. Example: mask = self._mask << self._offset
                '''
                return self._offset

            def info(self):
                ''' Returns a list containing stuff '''
                return [self._offset, self._mask, self._values]

            def unpack(self, cfg):
                ''' Extracts setting from passed 16-bit config & returns
                human readable result.
                '''
                return OrderedDict(map(reversed, self._values.items()))[self.extract(cfg)]

            def pack(self, value):
                ''' Takes a human-readable setting and returns a
                bit-shifted integer.
                '''
                return self._values[value] << self._offset

            def insert(self, cfg, value):
                ''' Performs validation and then does a bitwise
                replacement on passed config with the passed value.
                Returns integer representation of the new config.
                '''
                if value not in self._values.keys():
                    raise ValueError("RegisterField must be one of: {}".format(self._values.keys()))
                return ( cfg & ~(self._mask<<self._offset) )|( self._values[value] << self._offset )

            def extract(self, cfg):
                ''' Extracts setting from passed 16-bit config & returns
                integer representation.
                '''
                return ( cfg & (self._mask<<self._offset) )>>self._offset


class SPIDevice(IODeviceBase):
    '''
    A class wrapper for pigpio SPI handles. Not really implemented.
    '''
    def __init(self, channel, baudrate, pig=None):
        super().__init__(pig)
        self.open(channel, baudrate)

    def open(self, channel, baudrate):
        ''' Opens an SPI connection and returns the pigpiod handle.
        '''
        self._handle = self.pig.spi_open(channel, baudrate)

    def close(self):
        ''' Extends superclass method. Checks that pigpiod is connected
        and if a handle has been set - if so, closes an SPI connection.
        '''
        super().close()
        self.pig.spi_close(self.handle)

class Sensor(ABC):
    ''' Abstract base Class describing generalized sensors. Defines a
    mechanism for limited internal storage of recent observations and
    methods to pull that data out for external use.
    '''
    _DEFAULT_STORED_OBSERVATIONS = 128

    def __init__(self):
        ''' Upon creation, calls update() to ensure that if get is
        called there will be something to return
        '''
        self._data  = np.zeros(
            self._DEFAULT_STORED_OBSERVATIONS,
            dtype=np.float16
        )
        self._i     = 0
        self._data_length = self._DEFAULT_STORED_OBSERVATIONS
        self._last_timestamp = -1

    def update(self):
        ''' Make a sensor reading, verify that it makes sense and store
        the result internally. Returns True if reading was verified and
        False if something went wrong.
        '''
        value = self._read()
        if self._verify(value):
            self.__store_last(value)
            self._last_timestamp = time.time()
        return self._verify(value)

    def get(self):
        ''' Return the most recent sensor reading.
        '''
        if self._last_timestamp == -1:
            raise RuntimeWarning('get() called before update()')
        return self._data[(self._i - 1)%self._data_length]

    def age(self):
        ''' Returns the time since the last sensor update, in seconds.
        '''
        if self._last_timestamp == -1:
            raise RuntimeError('age() called before update()')
        return time.time()-self._last_timestamp

    def reset(self):
        ''' Resets the sensors internal memory. May be overloaded by
        subclasses to extend functionality specific to a device.
        '''
        self._data  = np.zeros(self.data_length,dtype=np.float16)
        self._i     = 0

    @property
    def data(self):
        ''' Generalized, not necessarily performant. Returns an ndarray
        of observations arranged oldest to newest. Result has length
        equal to the lessor of self.n and the number of observations
        made.

        Note: ndarray.astype(bool) returns an equivalent sized array
        with True for each nonzero element and False everywhere else.
        '''
        rolled = np.roll(self._data, self.data_length - self._i)
        return rolled[rolled.astype(bool)]

    @property
    def data_length(self):
        ''' Returns the number of observations kept in the Sensor's
        internal ndarray. Once the ndarray has been filled, the sensor
        begins overwriting the oldest elements of the ndarray with new
        observations such that the size of the internal storage stays
        constant.
        '''
        return self._data_length

    @data_length.setter
    def data_length(self, new_data_length):
        ''' Set a new length for stored observations. Clears existing
        observations and resets. '''
        self._data_length = new_data_length
        self.reset()

    def _read(self):
        ''' Calls _raw_read and scales the result before returning it
        '''
        return self._convert(self._raw_read())

    @abstractmethod
    def _verify(self, value):
        ''' Validate reading and throw exception/alarm if sensor does not
        appear to be working correctly
        '''
        raise NotImplementedError('Subclass must implement _verify()')

    @abstractmethod
    def _convert(self, raw):
        ''' Converts a raw reading from a sensor in whatever forma
        the device communicates with into a meaningful result.
        '''
        raise NotImplementedError('Subclass must implement _raw_read()')

    @abstractmethod
    def _raw_read(self):
        ''' Requests a new observation from the device and returns the
        raw result in whatever format/units the device communicates with
        '''
        raise NotImplementedError('Subclass must implement _raw_read()')

    def __store_last(self, value):
        ''' Takes a value and stores it in self.data. Increments counter
        '''
        self._data[self._i] = value
        self._i = (self._i + 1)%self.data_length


class AnalogSensor(Sensor):
    ''' Generalized class describing an analog sensor attached to the
    ADS1115 analog to digital converter. Inherits from the sensor base
    class and extends with functionality specific to analog sensors
    attached to the ads1115.

    If instantiated without a subclass, conceptually represents a
    voltmeter with a normalized output.
    '''
    _DEFAULT_OFFSET_VOLTAGE     = 0
    _DEFAULT_OUTPUT_SPAN        = 5
    _CONVERSION_FACTOR          = 1
    _DEFAULT_CALIBRATION        = {
            'OFFSET_VOLTAGE' : _DEFAULT_OFFSET_VOLTAGE,
            'OUTPUT_SPAN'    : _DEFAULT_OUTPUT_SPAN
    }

    def __init__(self, adc, **kwargs):
        ''' Links analog sensor on the ADC with configutation options
        specified. If no options are specified, it assumes the settings
        currently on the ADC.
        '''
        super().__init__()
        self.adc = adc
        if 'MUX' not in(kwargs.keys()):
            raise TypeError(
                    'User must specify MUX for AnalogSensor creation'
            )
        self._check_and_set_attr(**kwargs)

    def calibrate(self, **kwargs):
        ''' Sets the calibration of the sensor, either to the values
        contained in the passed tuple or by some routine; the current
        routine is pretty rudimentary and only calibrates offset voltage
        '''
        if kwargs:
                for fld, val in kwargs.items():
                    if fld in self._DEFAULT_CALIBRATION.keys():
                        setattr(self, fld, val)
        else:
            for _ in range(50):
                self.update()
                # PRINT FOR DEBUG / HARDWARE TESTING
                print(
                        'Analog Sensor Calibration @ %6.4f'%(
                                self.data[self.data.shape[0]-1]
                                )
                        ,
                        end='\r'
                )
                time.sleep(.1)
            setattr(self, 'OFFSET_VOLTAGE', np.mean(self.data[-50:]))
            # PRINT FOR DEBUG / HARDWARE TESTING
            print('Calibrated low-end of AnalogSensor @',
            ' %6.4f V'%(getattr(self,'OFFSET_VOLTAGE')))

    def _read(self):
        ''' Returns a value in the range of 0 - 1 corresponding to a
        fraction of the full input range of the sensor
        '''
        return self._convert(self._raw_read())

    def _verify(self, value):
        ''' Checks to make sure sensor reading was indeed in [0, 1]
        '''
        report = bool(0<= value <= 1)
        if not report:
            print(value)
        return report

    def _convert(self, raw):
        ''' Scales raw voltage into the range 0 - 1
        '''
        return (
                (raw - getattr(self,'OFFSET_VOLTAGE'))
                / (getattr(self,'OUTPUT_SPAN') + getattr(self,'OFFSET_VOLTAGE'))
        )

    def _raw_read(self):
        ''' Builds kwargs from configured fields to pass along to adc,
        then calls adc.read_conversion(), which returns a raw voltage.
        '''
        fields = self.adc.USER_CONFIGURABLE_FIELDS
        kwargs = dict(zip(
            fields,
            (getattr(self,field) for field in fields)
        ))
        return self.adc.read_conversion(**kwargs)

    def _fill_attr(self):
        ''' Examines self to see if there are any fields identified as
        user configurable or calibration that have not been set (i.e.
        were not passed to __init__ as **kwargs). If a field is missing,
        grabs the default value either from the ADC or from
        _DEFAULT_CALIBRATION and sets it as an attribute.
        '''
        for cfld in self.adc.USER_CONFIGURABLE_FIELDS:
            if not hasattr(self,cfld):
                setattr(
                        self,
                        cfld,
                        getattr(self.adc.config,cfld).unpack(self.adc.cfg)
                )
        for dcal,value in self._DEFAULT_CALIBRATION.items():
            if not hasattr(self,dcal): setattr(self,dcal,value)

    def _check_and_set_attr(self,**kwargs):
        ''' Checks to see if arguments passed to __init__ are recognized
        as user configurable or calibration fields. If so, set the value
        as an attribute like: self.KEY = VALUE. Keeps track of how many
        attributes are set in this way; if at the end there unknown
        arguments leftover, raises a TypeError; otherwise, calls
        _fill_attr() to fill in fields that were not passed
        '''
        allowed = (
            *self.adc.USER_CONFIGURABLE_FIELDS,
            *self._DEFAULT_CALIBRATION.keys(),
        )
        result = 0
        for fld,val in kwargs.items():
            if fld in allowed:
                setattr(self,fld,val)
                result += 1
        if result != len(kwargs):
            raise TypeError('AnalogSensor was passed unknown field(s)')
        self._fill_attr()


class Pin(IODeviceBase):
    '''
    Base Class wrapping pigpio methods for interacting with GPIO pins on
    the raspberry pi. Subclasses include InputPin, OutputPin; along with
    any specialized pins or specific devices defined in vent.io.actuators
    & vent.io.sensors (note: actuators and sensors do not need to be tied
    to a GPIO pin and may instead be interfaced through an ADC or I2C).

    This is an abstract base class. The subclasses InputPin and 
    OutputPin extend Pin into a usable form.
    '''
    _PIGPIO_MODES = {   'INPUT'     : 0,
                        'OUTPUT'    : 1,
                        'ALT5'      : 2,
                        'ALT4'      : 3,
                        'ALT0'      : 4,
                        'ALT1'      : 5,
                        'ALT2'      : 6,
                        'ALT3'      : 7 }

    def __init__(self, pin, pig=None):
        ''' Inherits attributes and methods from IODeviceBase.
        '''
        super().__init__(pig)
        self.pin=pin

    @property
    def mode(self):
        ''' The currently active pigpio mode of the pin.
        '''
        return dict(map(reversed, self._PIGPIO_MODES.items()))[self.pig.get_mode(self.pin)]

    @mode.setter
    def mode(self, mode):
        '''
        Performs validation on requested mode, then sets the mode.
        Raises runtime error if something goes wrong.
        '''
        if mode not in self._PIGPIO_MODES.keys():
            raise ValueError("Pin mode must be one of: {}".format(self._PIGPIO_MODES.keys()))
        result = self.pig.set_mode(self.pin, self._PIGPIO_MODES[mode])

        # Pull error and print it
        if result != 0:
            raise RuntimeError('Failed to set mode {} on pin {}'.format(mode, self.pin))


class InputPin(Pin):
    '''
    Subclass of Pin that should be used when calls to the pin should be
    read-only during normal operation.
    That is, if a call is made to set the value on an InputPin, it will
    throw a runtime warning.
    '''
    def __init__(self, pin, pig=None):
        super().__init__(pin, pig)
        self.mode = 'INPUT'

    def get(self):
        ''' Returns the value of the pin: usually 0 or 1 but can be
        overridden e.g. by PWM which returns duty cycle.
        '''
        self.pig.read(self.pin)


class OutputPin(Pin):
    '''
    Subclass of Pin that should be used when calls to the pin should be
    write-only during normal operation.
    That is, if a call is made to get the value of an OutputPin, it will
    throw a runtime warning.
    '''
    def __init__(self, pin, pig=None):
        super().__init__(pin, pig)
        self.mode = 'OUTPUT'

    def on(self):
        ''' Turn on a pin.
        '''
        self.set(1)

    def off(self):
        ''' Turn off a pin.
        '''
        self.set(0)

    def toggle(self):
        ''' If pin is on, turn it off. If it's off, turn it on. Do not
        raise a warning when pin is read in this way.
        '''
        self.set(not super().get())

    def set(self, value):
        ''' Sets the value of the Pin. Usually 0 or 1 but behavior
        differs for some subclasses.
        '''
        if value not in (0, 1):
            raise ValueError('Cannot set a value other than 0 or 1 to a Pin')
        self.pig.write(self.pin, value)


class PWMOutput(OutputPin):
    '''
    I am a Special Pin!
    '''
    _DEFAULT_FREQUENCY      = 20000
    _DEFAULT_SOFT_FREQ      = 2000
    _HARDWARE_PWM_PINS      = (12, 13, 18, 19)

    def __init__(self, pin, initial_duty=0, frequency=None, pig=None):
        super().__init__(pin, pig)
        if pin not in self._HARDWARE_PWM_PINS:
            self.hardware_enabled   = False
            default_frequency = self._DEFAULT_SOFT_FREQ
            raise RuntimeWarning('PWMOutput called on pin {} but that is not a PWM channel. Available frequencies will be limited.'.format(self.pin))
        else:
            self.hardware_enabled = True
            default_frequency = self._DEFAULT_FREQUENCY
        self.__pwm(frequency if frequency is not None else default_frequency, initial_duty)

    @property
    def frequency(self):
        ''' Return the current PWM frequency active on the pin.
        '''
        return self.pig.get_PWM_frequency(self.pin)

    @frequency.setter
    def frequency(self, new_frequency):
        ''' Description:
        Note: pigpio.pi.hardware_PWM() returns 0 if OK and an error code otherwise.
        - Tries to set hardware PWM if hardware_enabled
        - If that fails, or if not hardware_enabled, tries to set software PWM instead.'''
        self.__pwm(new_frequency, self._duty())

    @property
    def duty(self):
        ''' Description:
        Returns the PWM duty cycle (pulled straight from pigpiod) mapped to the range [0-1] '''
        return self.pig.get_PWM_dutycycle(self.pin)/self.pig.get_PWM_range(self.pin)

    def _duty(self):
        ''' Returns the pigpio int representation of the duty cycle
        '''
        return self.pig.get_PWM_dutycycle(self.pin)

    @duty.setter
    def duty(self, duty_cycle):
        ''' Description:
        Validation of requested duty cycle is performed here.
        Sets the PWM duty cycle to a value proportional to the input between (0, 1) '''
        if not 0 <= duty_cycle <= 1:
            raise ValueError('Duty cycle must be between 0 and 1')
        self.__pwm(self.frequency, int(duty_cycle*self.pig.get_PWM_range(self.pin)))

    def get(self):
        '''Overloaded to return duty cycle instead of reading the value on the pin '''
        return self.duty

    def set(self, value):
        '''Overloaded to set duty cycle'''
        self.duty = value

    def on(self):
        ''' Same functionality as parent, but done with PWM intact'''
        self.duty = 1

    def off(self):
        ''' Same functionality as parent, but done with PWM intact'''
        self.duty = 0

    def __pwm(self, frequency, duty):
        ''' Description:
        -If hardware_enabled is True, start a hardware pwm with the requested duty.
        -Otherwise (or if setting a hardware pwm fails and hardware_enabled is set to False),
         set a software pwm in the same manner.'''
        if self.hardware_enabled:
            self.__hardware_pwm(frequency, duty)
        if not self.hardware_enabled:
            self.__software_pwm(frequency, duty)

    def __hardware_pwm(self, frequency, duty):
        ''' Description:
        -Tries to set a hardware pwm. result == 0 if it suceeds.
        -Sets hardware_enabled flag to indicate success or failure'''
        #print('pin: %3.0d freq: %5.0d duty: %4.2f'%(self.pin,frequency,duty))
        result = self.pig.hardware_PWM(self.pin, frequency, duty)
        if result != 0:
            self.hardware_enabled = False
            raise RuntimeWarning('Failed to start hardware PWM with frequency {} on pin {}. Error: {}'.format(frequency, self.pin, self.pig.error_text(result)))
        else:
            self.hardware_enabled = True

    def __software_pwm(self, frequency, duty):
        ''' Used for pins where hardware PWM is not available. '''
        self.pig.set_PWM_dutycycle(self.pin, duty)
        realized_frequency = self.pig.set_PWM_frequency(self.pin, frequency)
        if frequency != realized_frequency:
            raise RuntimeWarning('A PWM frequency of {} was requested but the best that could be done was {}'.format(frequency, realized_frequency))
        self.hardware_enabled = False
