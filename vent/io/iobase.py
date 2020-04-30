''' Provides the abstract classes and classes for basic objects like
pins, to be used for higher-level operations by the "device" objects.
'''
from abc import ABC, abstractmethod
from collections import OrderedDict
import struct
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
        if self.handle >= 0: self.close()
        if self.pigpiod_ok: self.pig.stop()

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
        ''' Close an i2c/spi connection, if implemented in subclass
        '''
        return


def be16_to_native(word, signed):
    ''' BigEndian to Native-endian conversion for signed 2 Byte
    integers (2 complement).
    '''
    if signed:
        result = struct.unpack('@h', struct.pack('>h', word))[0]
    else:
        result = struct.unpack('@H', struct.pack('>H', word))[0]
    return result


def native16_to_be(word, signed = False):
    ''' Little Endian to BigEndian conversion for unsigned 2Byte
    integers (2 complement).
    '''
    if signed:
        result = struct.unpack('@h', struct.pack('>h', word))[0]
    else:
        result = struct.unpack('@H', struct.pack('>H', word))[0]
    return result


def be16bytes_to_native(data):
    ''' Unpacks a bytearray of length 2 respecting big-endianness of
    the outside world and returns int
    '''
    return struct.unpack('>H', data)[0]


def native16_to_be_bytes(word):
    ''' Packs an int into a bytearray while swapping big-endianness
    of the pi and returns bytearray
    '''
    return struct.pack('>H', word)


class i2cDevice(IODeviceBase):
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
        ''' Closes i2c connection.
        '''
        self.pig.i2c_close(self.handle)

    def read_device(self, num_bytes):
        ''' Read a specified number of bytes directly from the the
        device without changing the register. Does NOT perform LE/BE
        conversion.
        '''
        return self.pig.i2c_read_device(self.handle, num_bytes)[1]

    def write_device(self, data):
        ''' Write bytes to the device without specifying register.
        Does NOT perform LE/BE conversion
        '''
        self.pig.i2c_write_device(self.handle, data)

    def read_word(self):
        ''' Read two bytes directly from the the device without changing the register.'''
        return be16bytes_to_native(self.pig.i2c_read_device(self.handle)[1])

    def write_word(self, wordbytes):
        ''' Write two bytes to the device without specifying register.
        '''
        self.pig.i2c_write_device(
            self.handle,
            native16_to_be_bytes(wordbytes)
        )

    def read_register(self, register, signed=False):
        ''' Read 2 bytes from the specified register
        (denoted by a single byte)
        '''
        return be16_to_native(
            self.pig.i2c_read_word_data(self.handle, register),
            signed=signed
        )

    def write_register(self, register, word, signed=False):
        ''' Write 2 bytes to the specified register
        (denoted by a single byte)
        '''
        self.pig.i2c_write_word_data(
            self.handle,
            register,
            native16_to_be(word, signed=signed)
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
            self._fields = fields
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
                    self._fields,
                    (getattr(
                        getattr(self,field),
                        'unpack' )(cfg) for field in self._fields)
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
                return self._offset

            def info(self):
                ''' Returns a list containing stuff '''
                return [self._offset, self._mask, self._values]

            def unpack(self, cfg):
                ''' Extracts setting from passed 16-bit config & returns human readable result '''
                return OrderedDict(map(reversed, self._values.items()))[self.extract(cfg)]

            def pack(self, value):
                '''Takes a human-readable setting and returns a bit-shifted integer'''
                return self._values[value] << self._offset

            def insert(self, cfg, value):
                '''
                Performs validation and then does a bitwise replacement on passed config with
                the passed value. Returns integer representation of the new config.
                '''
                if value not in self._values.keys():
                    raise ValueError("RegisterField must be one of: {}".format(self._values.keys()))
                return ( cfg & ~(self._mask<<self._offset) )|( self._values[value] << self._offset )

            def extract(self, cfg):
                '''Extracts setting from passed 16-bit config & returns integer representation'''
                return ( cfg & (self._mask<<self._offset) )>>self._offset


class spiDevice(IODeviceBase):
    '''
    A class wrapper for pigpio SPI handles. Not implemented.
    '''
    def __init(self, channel, baudrate, pig=None):
        super().__init__(pig)
        self.open(channel, baudrate)

    def open(self, channel, baudrate):
        self._handle = self.pig.spi_open(channel, baudrate)

    def close(self):
        self.pig.spi_close(self.handle)

class Sensor(ABC):
    ''' Abstract base Class describing generalized sensors. Defines a mechanism
    for limited internal storage of recent observations and methods to
    pull that data out for external use.
    '''
    _DEFAULT_STORED_OBSERVATIONS = 128

    def __init__(self):
        self._data  = np.zeros(
            self._DEFAULT_STORED_OBSERVATIONS,
            dtype=np.float16
        )
        self._i     = 0
        self._n     = self._DEFAULT_STORED_OBSERVATIONS

    def update(self):
        ''' Make a sensor reading, verify that it makes sense and store
        the result internally. Returns True if reading was verified and
        False if something went wrong.
        '''
        value = self._read()
        if self._verify(value):
            self.__store_last(value)
        return self._verify(value)

    def get(self):
        ''' Return the most recent sensor reading.
        '''
        return self.data[(self._i - 1)%self.n]

    def reset(self):
        ''' Resets the sensors internal memory. May be overloaded by
        subclasses to extend functionality specific to a device.
        '''
        self._data  = np.zeros(self.n)
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
        rolled = np.roll(self._data, self.n - self._i)
        return rolled[rolled.astype(bool)]

    @property
    def n(self):
        ''' Returns the number of observations kept in the Sensor's
        internal ndarray. Once the ndarray has been filled, the sensor
        begins overwriting the oldest elements of the ndarray with new
        observations such that the size of the internal storage stays
        constant.
        '''
        return self._n

    @n.setter
    def n(self, new_n):
        ''' Set a new length for stored observations. Clears existing
        observations and resets. '''
        self._n = new_n
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
        self.data[self._i] = value
        self._i = (self._i + 1)%self.n


class AnalogSensor(Sensor):
    ''' Generalized class describing an analog sensor attached to the
    ADS1115 analog to digital converter. Inherits from the sensor base
    class and extends with functionality specific to analog sensors
    attached to the ads1115.

    If instantiated without a subclass, conceptually represents a
    voltmeter with a normalized output.
    '''
    _DEFAULT_OFFSET_VOLTAGE = 0
    _DEFAULT_OUTPUT_SPAN    = 5
    _CONVERSION_FACTOR      = 1

    def __init__(   self,
                    adc,
                    channel,
                    offset_voltage  = _DEFAULT_OFFSET_VOLTAGE,
                    output_span     = _DEFAULT_OUTPUT_SPAN,
                    gain            = None,
                    mode            = None,
                    data_rate       = None
                    ):
        ''' Links analog sensor on the ADC with configutation options
        specified. If no options are specified, it assumes the settings
        currently on the ADC.
        '''
        super().__init__()
        self.MUX        = channel
        self.PGA        = adc.config.PGA.unpack(adc.cfg) if gain is None else gain
        self.MODE       = adc.config.MODE.unpack(adc.cfg) if mode is None else mode
        self.DR         = adc.config.DR.unpack(adc.cfg) if data_rate is None else data_rate
        self.adc        = adc
        offset_voltage  = self._DEFAULT_OFFSET_VOLTAGE if offset_voltage is None else offset_voltage
        output_span     = self._DEFAULT_OUTPUT_SPAN if output_span is None else output_span 
        calibration = (
            offset_voltage,
            offset_voltage + output_span
            )
        self.calibrate(calibration)

    def calibrate(self, calibration=None):
        ''' Sets the calibration of the sensor, either to the values
        contained in the passed tuple or by some routine; the current
        routine is pretty rudimentary and only calibrates offset voltage
        '''
        if calibration is not None:
            if not isinstance(calibration,tuple):
                raise TypeError('calibration must be a tuple of the form (low, high)')
            else:
                self.calibration = calibration
        else:
            for _ in range(50):
                self.update()
                # debug
                print('Analog Sensor Calibration @ %6.4f V'%(self.data[self.data.shape[0]]), end='\r')
                time.sleep(.1)
            self.calibration[0] = np.mean(self.data[-50:])
            RuntimeWarning('This calibration routine is not meant for production')

            # debug
            print('Calibrated low-end of Analog sensor  @ %6.4f V'%(self.calibration[0]))

    def _read(self):
        ''' Returns a value in the range of 0 - 1 corresponding to a fraction
        of the full input range of the sensor
        '''
        return self._convert(self._raw_read())

    def _verify(self, value):
        ''' Checks to make sure sensor reading was indeed in [0, 1]
        '''
        return bool(0<= value <= 1)

    def _convert(self, raw):
        ''' Scales raw voltage into the range 0 - 1
        '''
        return (raw - self.calibration[0])/(self.calibration[1]-self.calibration[0])


    def _raw_read(self):
        ''' Returns raw voltage
        '''
        return self.adc.read_conversion(self.MUX, self.PGA, self.MODE, self.DR)


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

    def get(self):
        ''' Returns the value of the pin: usually 0 or 1 but can be
        overridden e.g. by PWM which returns duty cycle.
        '''
        self.pig.read(self.pin)

    def set(self, value):
        ''' Sets the value of the Pin. Usually 0 or 1 but behavior
        differs for some subclasses.
        '''
        if value not in (0, 1):
            raise ValueError('Cannot set a value other than 0 or 1 to a Pin')
        self.pig.write(self.pin, value)


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

    def set(self, value):
        super().set(value)
        RuntimeWarning('set() was called on an InputPin')


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
        self.set(1)

    def off(self):
        self.set(0)

    def toggle(self):
        self.set(not self.pig.read(self.pin))

    def get(self):
        super().get()
        RuntimeWarning('get() was called on an OutputPin')


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
            RuntimeWarning('PWMOutput called on pin {} but that is not a PWM channel. Available frequencies will be limited.'.format(self.pin))
        else:
            self.hardware_enabled = True
            default_frequency = self._DEFAULT_FREQUENCY
        self.__pwm(frequency if frequency is not None else default_frequency, initial_duty)

    @property
    def frequency(self):
        return self.pig.get_PWM_frequency(self.pin)

    @frequency.setter
    def frequency(self, new_frequency):
        ''' Description:
        Note: pigpio.pi.hardware_PWM() returns 0 if OK and an error code otherwise.
        - Tries to set hardware PWM if hardware_enabled
        - If that fails, or if not hardware_enabled, tries to set software PWM instead.'''
        self.__pwm(new_frequency, self.duty)

    @property
    def duty(self):
        ''' Description:
        Returns the PWM duty cycle (pulled straight from pigpiod) mapped to the range [0-1] '''
        return self.pig.get_PWM_dutycycle(self.pin)/self.pig.get_PWM_range(self.pin)

    @duty.setter
    def duty(self, duty_cycle):
        ''' Description:
        Validation of requested duty cycle is performed here.
        Sets the PWM duty cycle to a value proportional to the input between (0, 1) '''
        if not 0<duty_cycle<1: raise ValueError('Duty cycle must be between 0 and 1')
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
        result = self.pig.hardware_PWM(self.pin, frequency, duty)
        if result != 0:
            self.hardware_enabled = False
            RuntimeWarning('Failed to start hardware PWM with frequency {} on pin {}. Error: {}'.format(frequency, self.pin, self.pig.error_text(result)))
        else:
            self.hardware_enabled = True

    def __software_pwm(self, frequency, duty):
        ''' Used for pins where hardware PWM is not available. '''
        self.pig.set_PWM_dutycycle(self.pin, duty)
        realized_frequency = self.pig.set_PWM_frequency(self.pin, frequency)
        if frequency != realized_frequency:
            RuntimeWarning('A PWM frequency of {} was requested but the best that could be done was {}'.format(frequency, realized_frequency))
        self.hardware_enabled = False
