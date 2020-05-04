"""
Subclass implementations of specific sensor devices.
"""
from collections import OrderedDict

import numpy as np
from .iobase import Sensor, be16_to_native, SolenoidBase, IODeviceBase, native16_to_be
from time import sleep


class I2CDevice(IODeviceBase):
    """ A class wrapper for pigpio I2C handles. Defines several methods
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
    """

    def __init__(self, i2c_address, i2c_bus, pig=None):
        """ Initializes pigpio bindings and opens i2c connection.
        """
        super().__init__(pig)
        self._i2c_bus = i2c_bus
        self.open(i2c_bus, i2c_address)

    def open(self, i2c_bus, i2c_address):
        """ Opens i2c connection given i2c bus and address.
        """
        self._handle = self.pig.i2c_open(i2c_bus, i2c_address)

    def close(self):
        """ Extends superclass method. Checks that pigpiod is connected
        and if a handle has been set - if so, closes an i2c connection.
        """
        super().close()
        self.pig.i2c_close(self.handle)

    def read_device(self, num_bytes):
        """ Read a specified number of bytes directly from the the
        device without changing the register. Does NOT perform LE/BE
        conversion.
        """
        return self.pig.i2c_read_device(self.handle, num_bytes)

    def write_device(self, word, signed=False, count=2):
        """ Write bytes to the device without specifying register.
        DOES perform LE/BE conversion. Count should be
        specified for when passing something other than a word.
        """
        self.pig.i2c_write_device(
            self.handle,
            native16_to_be(word, signed=signed, count=count)
        )

    def read_register(self, register, signed=False, count=2):
        """ Read count# bytes from the specified register
        (denoted by a single byte)
        """
        return be16_to_native(
            self.pig.i2c_read_i2c_block_data(
                self.handle,
                register,
                count
            ),
            signed=signed
        )

    def write_register(self, register, word, signed=False, count=2):
        """ Write bytes to the specified register. Count should be
        specified for when passing something other than a word.
        (register denoted by a single byte)
        """
        self.pig.i2c_write_i2c_block_data(
            self.handle,
            register,
            native16_to_be(word, signed=signed, count=count)
        )

    class Register:
        """ Describes a writable configuration register. Has dynamically
        defined attributes corresponding to the fields described by the
        passed arguments. Takes as arguments two tuples of equal length,
        the first of which names each field and the second being a tuple
        of tuples containing the (human readable) possible settings &
        values for each field.

        Note: The intializer reverses the fields & their values because
        a human reads the register, as drawn in the datasheet, from left
        to right - however, the fields furthest to the left are the most
        significant bits of the register.
        """

        def __init__(self, fields, values):
            """ Initializer which loads in (dynamically defined)
            attributes.
            """
            self.fields = fields
            offset = 0
            for fld, val in zip(reversed(fields), reversed(values)):
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
            """ Given the contents of a register in integer form,
            returns a dict of fields and their current settings
            """
            return OrderedDict(zip(
                self.fields,
                (getattr(
                    getattr(self, field),
                    'unpack')(cfg) for field in self.fields)
            ))

        def pack(self, cfg, **kwargs):
            """ Given an initial integer representation of a register and an
            arbitrary number of field=value settings, returns an integer
            representation of the register incorporating the new settings.
            """
            for field, value in kwargs.items():
                if hasattr(self, field) and value is not None:
                    cfg = getattr(getattr(self, field), 'insert')(cfg, value)
            return cfg

        class RegisterField:
            """ Describes a configurable field in a writable register.
            """

            def __init__(self, offset, mask, values):
                self._offset = offset
                self._mask = mask
                self._values = values

            def offset(self):
                """ Returns the position of the field's LSB in the
                register. Example: mask = self._mask << self._offset
                """
                return self._offset

            def info(self):
                """ Returns a list containing stuff """
                return [self._offset, self._mask, self._values]

            def unpack(self, cfg):
                """ Extracts setting from passed 16-bit config & returns
                human readable result.
                """
                return OrderedDict(map(reversed, self._values.items()))[self.extract(cfg)]

            def pack(self, value):
                """ Takes a human-readable setting and returns a
                bit-shifted integer.
                """
                return self._values[value] << self._offset

            def insert(self, cfg, value):
                """ Performs validation and then does a bitwise
                replacement on passed config with the passed value.
                Returns integer representation of the new config.
                """
                if value not in self._values.keys():
                    raise ValueError("RegisterField must be one of: {}".format(self._values.keys()))
                return (cfg & ~(self._mask << self._offset)) | (self._values[value] << self._offset)

            def extract(self, cfg):
                """ Extracts setting from passed 16-bit config & returns
                integer representation.
                """
                return (cfg & (self._mask << self._offset)) >> self._offset


class ADS1115(I2CDevice):
    """ Description:
    Class for the ADS1115 16 bit, 4 Channel ADC.
    Datasheet:
     http://www.ti.com/lit/ds/symlink/ads1114.pdf?ts=1587872241912

    Default Values:
     Default configuration for vent:     0xC3E3
     Default configuration on power-up:  0x8583
    """
    _DEFAULT_ADDRESS = 0x48
    _DEFAULT_VALUES = {'MUX': 0, 'PGA': 4.096, 'MODE': 'SINGLE', 'DR': 860}

    """ Address Pointer Register (write-only) """
    _POINTER_FIELDS = ('P',)
    _POINTER_VALUES = (
        (
            'CONVERSION',
            'CONFIG',
            'LO_THRESH',
            'HIGH_THRESH'
        ),
    )

    """ Config Register (R/W) """
    _CONFIG_FIELDS = (
        'OS',
        'MUX',
        'PGA',
        'MODE',
        'DR',
        'COMP_MODE',
        'COMP_POL',
        'COMP_LAT',
        'COMP_QUE'
    )
    _CONFIG_VALUES = (
        ('NO_EFFECT', 'START_CONVERSION'),
        ((0, 1), (0, 3), (1, 3), (2, 3), 0, 1, 2, 3),
        (6.144, 4.096, 2.048, 1.024, 0.512, 0.256, 0.256, 0.256),
        ('CONTINUOUS', 'SINGLE'),
        (8, 16, 32, 64, 128, 250, 475, 860),
        ('TRADIONAL', 'WINDOW'),
        ('ACTIVE_LOW', 'ACTIVE_HIGH'),
        ('NONLATCHING', 'LATCHING'),
        (1, 2, 3, 'DISABLE')
    )
    USER_CONFIGURABLE_FIELDS = ('MUX', 'PGA', 'MODE', 'DR')
    """ Note:
    The Conversion Register is read-only and contains a 16bit
    representation of the requested value (provided the conversion is
    ready).

    The Lo-thresh & Hi-thresh Registers are not Utilized here. However,
    their function and usage are described in the datasheet. Should you
    want to extend the functionality implemented here.
    """

    def __init__(self, address=_DEFAULT_ADDRESS, i2c_bus=1, pig=None):
        """ Initializes registers: Pointer register is write only,
        config is R/W. Sets initial value of _last_cfg to what is
        actually on the ADS.Packs default settings into _cfg, but does
        not actually write to ADC - that occurs when read_conversion()
        is called.
        """
        super().__init__(address, i2c_bus, pig)
        self.pointer = self.Register(self._POINTER_FIELDS, self._POINTER_VALUES)
        self._config = self.Register(self._CONFIG_FIELDS, self._CONFIG_VALUES)
        self._last_cfg = self._read_last_cfg()
        self._cfg = self._config.pack(cfg=self._last_cfg, **self._DEFAULT_VALUES)

    def read_conversion(self, **kwargs):
        """ Returns a voltage (expressed as a float) corresponding to a
        channel on the ADC. The channel to read from, along with the
        gain, mode, and sample rate of the conversion may be may be
        specified as optional parameters. If read_conversion() is called
        with no parameters, the resulting voltage corresponds to the
        channel last read from and the same conversion settings.
        """
        return (
                self._read_conversion(**kwargs)
                * self._config.PGA.unpack(self.cfg) / 32767
        )

    def print_config(self):
        """ Returns the human-readable configuration for the next read.
        """
        return self._config.unpack(self.cfg)

    @property
    def config(self):
        """ Returns the Register object of the config register.
        """
        return self._config

    @property
    def cfg(self):
        """ Returns the contents (as a 16-bit unsigned integer) of the
        configuration that will be written to the config register when
        read_conversion() is next called.
        """
        return self._cfg

    def _read_conversion(self, **kwargs):
        """ Backend for read_conversion(). Returns the contents of the
        16-bit conversion register as an unsigned integer.

        If no parameters are passed, one of two things can happen:

            1)  If the ADC is in single-shot (mode='SINGLE') conversion
                mode, _last_cfg is written to the config register; once
                the ADC indicates it is ready, the contents of the
                conversion register are read and the result is returned.
            2)  If the ADC is in CONTINUOUS mode, the contents of the
                conversion register are read immediately and returned.

        If any of channel, gain, mode, or data_rate are specified as
        parameters, a new _cfg is packed and written to the config
        register; once the ADC indicates it is ready, the contents of
        the conversion register are read and the result is returned.

        Note: In continuous mode, data can be read from the conversion
        register of the ADS1115 at any time and always reflects the
        most recently completed conversion. So says the datasheet.
        """
        self._cfg = self._config.pack(cfg=self.cfg, **kwargs)
        mode = self.print_config()['MODE']
        if self._cfg != self._last_cfg or mode == 'SINGLE':
            self.write_register(self.pointer.P.pack('CONFIG'), self.cfg)
            self._last_cfg = self.cfg
            data_rate = self._config.DR.unpack(self.cfg)
            while not (self._ready() or mode == 'CONTINUOUS'):
                tick = self.pig.get_current_tick()
                while (self.pig.get_current_tick() - tick) < 1000000 / data_rate:
                    pass
        return self.read_register(self.pointer.P.pack('CONVERSION'), signed=True)

    def _read_last_cfg(self):
        """ Reads the config register and returns the contents as a
        16-bit unsigned integer; updates internal record _last_cfg.
        """
        self._last_cfg = self.read_register(self.pointer.P.pack('CONFIG'))
        return self._last_cfg

    def _ready(self):
        """ Return status of ADC conversion.
        OS = 0: Device is currently performing a conversion
        OS = 1: Device is not currently performing a conversion
        """
        return self.read_register(self.pointer.P.pack('CONFIG')) >> 15


class AnalogSensor(Sensor):
    """ Generalized class describing an analog sensor attached to the
    ADS1115 analog to digital converter. Inherits from the sensor base
    class and extends with functionality specific to analog sensors
    attached to the ads1115.

    If instantiated without a subclass, conceptually represents a
    voltmeter with a normalized output.
    """
    _DEFAULT_offset_voltage = 0
    _DEFAULT_output_span = 5
    _CONVERSION_FACTOR = 1
    _DEFAULT_CALIBRATION = {
        'offset_voltage': _DEFAULT_offset_voltage,
        'output_span': _DEFAULT_output_span
    }

    def __init__(self, adc, **kwargs):
        """ Links analog sensor on the ADC with configuration options
        specified. If no options are specified, it assumes the settings
        currently on the ADC.
        """
        super().__init__()
        self.adc = adc
        if 'MUX' not in (kwargs.keys()):
            raise TypeError(
                'User must specify MUX for AnalogSensor creation'
            )
        self._check_and_set_attr(**kwargs)

    def calibrate(self, **kwargs):
        """ Sets the calibration of the sensor, either to the values
        contained in the passed tuple or by some routine; the current
        routine is pretty rudimentary and only calibrates offset voltage
        """
        if kwargs:
            for fld, val in kwargs.items():
                if fld in self._DEFAULT_CALIBRATION.keys():
                    setattr(self, fld, val)
        else:
            for _ in range(50):
                self.update()
                # PRINT FOR DEBUG / HARDWARE TESTING
                print(
                    "Analog Sensor Calibration @ {:6.4f}".format(self.data[self.data.shape[0] - 1]),
                    end='\r'
                )
                sleep(.1)
            self.offset_voltage = np.mean(self.data[-50:])
            # PRINT FOR DEBUG / HARDWARE TESTING
            print("Calibrated low-end of AnalogSensor @",
                  ' %6.4f V' % self.offset_voltage)

    def _read(self):
        """ Returns a value in the range of 0 - 1 corresponding to a
        fraction of the full input range of the sensor
        """
        return self._convert(self._raw_read())

    def _verify(self, value):
        """ Checks to make sure sensor reading was indeed in [0, 1]
        """
        report = bool(0 <= value <= 1)
        if not report:
            print(value)
        return report

    def _convert(self, raw):
        """ Scales raw voltage into the range 0 - 1
        """
        return (
                (raw - getattr(self, 'offset_voltage'))
                / (getattr(self, 'output_span') + getattr(self, 'offset_voltage'))
        )

    def _raw_read(self):
        """ Builds kwargs from configured fields to pass along to adc,
        then calls adc.read_conversion(), which returns a raw voltage.
        """
        fields = self.adc.USER_CONFIGURABLE_FIELDS
        kwargs = dict(zip(
            fields,
            (getattr(self, field) for field in fields)
        ))
        return self.adc.read_conversion(**kwargs)

    def _fill_attr(self):
        """ Examines self to see if there are any fields identified as
        user configurable or calibration that have not been write (i.e.
        were not passed to __init__ as **kwargs). If a field is missing,
        grabs the default value either from the ADC or from
        _DEFAULT_CALIBRATION and sets it as an attribute.
        """
        for cfld in self.adc.USER_CONFIGURABLE_FIELDS:
            if not hasattr(self, cfld):
                setattr(
                    self,
                    cfld,
                    getattr(self.adc.config, cfld).unpack(self.adc.cfg)
                )
        for dcal, value in self._DEFAULT_CALIBRATION.items():
            if not hasattr(self, dcal):
                setattr(self, dcal, value)

    def _check_and_set_attr(self, **kwargs):
        """ Checks to see if arguments passed to __init__ are recognized
        as user configurable or calibration fields. If so, write the value
        as an attribute like: self.KEY = VALUE. Keeps track of how many
        attributes are write in this way; if at the end there unknown
        arguments leftover, raises a TypeError; otherwise, calls
        _fill_attr() to fill in fields that were not passed
        """
        allowed = (
            *self.adc.USER_CONFIGURABLE_FIELDS,
            *self._DEFAULT_CALIBRATION.keys(),
        )
        result = 0
        for fld, val in kwargs.items():
            if fld in allowed:
                setattr(self, fld, val)
                result += 1
        if result != len(kwargs):
            raise TypeError('AnalogSensor was passed unknown field(s)')
        self._fill_attr()


class P4vMini(AnalogSensor):
    """ Analog gauge pressure sensor with range of 0 - 20" h20. The
    calibration outlined in the datasheet has low =  0.25V and
    high = 4.0V (give or take a bit). The conversion factor is derived
    from the sensor's maximum output of 20 in(h20), and we want sensor
    readings in cm h20: (2.54 cm/in * 20" h20) * read() = observed cmh20

    The only difference between this device and a generic AnalogSensor
    is its calibration, and the additional unit conversion in _convert()
    """
    _CALIBRATION = {
        'offset_voltage': 0.25,
        'output_span': 4.0
    }
    _CONVERSION_FACTOR = 2.54 * 20

    def __init__(self, adc, mux, **calibration_kwargs):
        super().__init__(adc, MUX=mux, **calibration_kwargs)

        # A check here to make sure calibrated offset voltage is
        #  reasonably close to what is currently coming from the sensor
        #   would be prudent. A warning is probably sufficient.

    def _verify(self, value):
        """ Extends superclass value to function with a conversion
        factor
        """
        return super()._verify(value / self._CONVERSION_FACTOR)

    def _convert(self, raw):
        """ Overloaded to map AnalogSensor's normalized output into the
        desired units of cm(h20)"""
        return self._CONVERSION_FACTOR * super()._convert(raw)


class SFM3200(Sensor, I2CDevice):
    """ Datasheet:
         https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/ ...
            ... 5_Mass_Flow_Meters/Datasheets/Sensirion_Mass_Flow_Meters_SFM3200_Datasheet.pdf
    """
    _DEFAULT_ADDRESS = 0x40
    _FLOW_OFFSET = 32768
    _FLOW_SCALE_FACTOR = 120

    def __init__(self, address=_DEFAULT_ADDRESS, i2c_bus=1, pig=None):
        I2CDevice.__init__(self, address, i2c_bus, pig)
        Sensor.__init__(self)
        self.reset()
        self._start()

    def reset(self):
        """ Extended to add device specific behavior: Asks the sensor
        to perform a soft reset. 80 ms soft reset time.
        """
        super().reset()
        self.write_device(0x2000)
        sleep(.08)

    def _start(self):
        """ Device specific:Sends the 'start measurement' command to the
        sensor. Start-up time once command has been recieved is
        'less than 100ms'
        """
        self.write_device(0x1000)
        sleep(.1)

    def _verify(self, value):
        """ No further verification needed for this sensor. Onboard
        chip handles all that. Could throw in a CRC8 checker instead of
        discarding them in _convert().
        """
        return True

    def _convert(self, raw):
        """ Overloaded to replace with device-specific protocol.
        Convert raw int to a flow reading having type float with
        units slm. Implementation differs from parent for clarity and
        consistency with source material.

        Source:
          https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/ ...
            ... 5_Mass_Flow_Meters/Application_Notes/Sensirion_Mass_Flo_Meters_SFM3xxx_I2C_Functional_Description.pdf
        """
        return (raw - self._FLOW_OFFSET) / self._FLOW_SCALE_FACTOR

    def _raw_read(self):
        """ Performs an read on the sensor, converts recieved bytearray,
        discards the last two bytes (crc values - could implement in future),
        and returns a signed int converted from the big endian two
        complement that remains.
        """
        return be16_to_native(self.read_device(4))


class Pin(IODeviceBase):
    """
    Base Class wrapping pigpio methods for interacting with GPIO pins on
    the raspberry pi. Subclasses include InputPin, OutputPin; along with
    any specialized pins or specific devices defined in vent.io.actuators
    & vent.io.sensors (note: actuators and sensors do not need to be tied
    to a GPIO pin and may instead be interfaced through an ADC or I2C).

    This is an abstract base class. The subclasses InputPin and
    OutputPin extend Pin into a usable form.
    """
    _PIGPIO_MODES = {'INPUT': 0,
                     'OUTPUT': 1,
                     'ALT5': 2,
                     'ALT4': 3,
                     'ALT0': 4,
                     'ALT1': 5,
                     'ALT2': 6,
                     'ALT3': 7}

    def __init__(self, pin, pig=None):
        """ Inherits attributes and methods from IODeviceBase.
        """
        super().__init__(pig)
        self.pin = pin

    @property
    def mode(self):
        """ The currently active pigpio mode of the pin.
        """
        return dict(map(reversed, self._PIGPIO_MODES.items()))[self.pig.get_mode(self.pin)]

    @mode.setter
    def mode(self, mode):
        """
        Performs validation on requested mode, then sets the mode.
        Raises runtime error if something goes wrong.
        """
        if mode not in self._PIGPIO_MODES.keys():
            raise ValueError("Pin mode must be one of: {}".format(self._PIGPIO_MODES.keys()))
        result = self.pig.set_mode(self.pin, self._PIGPIO_MODES[mode])

        # Pull error and print it
        if result != 0:
            raise RuntimeError('Failed to write mode {} on pin {}'.format(mode, self.pin))

    def toggle(self):
        """ If pin is on, turn it off. If it's off, turn it on. Do not
        raise a warning when pin is read in this way.
        """
        self.write(not self.read())

    def read(self):
        """ Returns the value of the pin: usually 0 or 1 but can be
        overridden e.g. by PWM which returns duty cycle.
        """
        self.pig.read(self.pin)

    def write(self, value):
        """ Sets the value of the Pin. Usually 0 or 1 but behavior
        differs for some subclasses.
        """
        if value not in (0, 1):
            raise ValueError('Cannot write a value other than 0 or 1 to a Pin')
        self.pig.write(self.pin, value)


class SolenoidValve(SolenoidBase, Pin):
    """ An extension of vent.io.iobase.Pin which uses valve terminology for its methods.
    Also allows configuring both normally open and normally closed valves (called the "form" of the valve).
    """
    _FORMS = {'Normally Closed': 0,
              'Normally Open': 1}

    def __init__(self, pin, form='Normally Closed', pig=None):
        self.form = form
        Pin.__init__(self, pin, pig)
        SolenoidBase.__init__(self, form=form)


class PWMOutput(Pin):
    """
    I am a Special Pin!
    """
    _DEFAULT_FREQUENCY = 20000
    _DEFAULT_SOFT_FREQ = 2000
    _HARDWARE_PWM_PINS = (12, 13, 18, 19)

    def __init__(self, pin, initial_duty=0, frequency=None, pig=None):
        super().__init__(pin, pig)
        if pin not in self._HARDWARE_PWM_PINS:
            self.hardware_enabled = False
            frequency = self._DEFAULT_SOFT_FREQ if frequency is None else frequency
            raise RuntimeWarning(
                'PWMOutput called on pin {} but that is not a PWM channel. Available frequencies will be limited.'.format(
                    self.pin))
        else:
            self.hardware_enabled = True
            frequency = self._DEFAULT_FREQUENCY if frequency is None else frequency
        self.__pwm(frequency, initial_duty)

    @property
    def frequency(self):
        """ Return the current PWM frequency active on the pin.
        """
        return self.pig.get_PWM_frequency(self.pin)

    @frequency.setter
    def frequency(self, new_frequency):
        """ Description:
        Note: pigpio.pi.hardware_PWM() returns 0 if OK and an error code otherwise.
        - Tries to write hardware PWM if hardware_enabled
        - If that fails, or if not hardware_enabled, tries to write software PWM instead."""
        self.__pwm(new_frequency, self._duty())

    @property
    def duty(self):
        """ Description:
        Returns the PWM duty cycle (pulled straight from pigpiod) mapped to the range [0-1] """
        return self.pig.get_PWM_dutycycle(self.pin) / self.pig.get_PWM_range(self.pin)

    def _duty(self):
        """ Returns the pigpio int representation of the duty cycle
        """
        return self.pig.get_PWM_dutycycle(self.pin)

    @duty.setter
    def duty(self, duty_cycle):
        """ Description:
        Validation of requested duty cycle is performed here.
        Sets the PWM duty cycle to a value proportional to the input between (0, 1) """
        if not 0 <= duty_cycle <= 1:
            raise ValueError('Duty cycle must be between 0 and 1')
        self.__pwm(self.frequency, int(duty_cycle * self.pig.get_PWM_range(self.pin)))

    def read(self):
        """Overloaded to return duty cycle instead of reading the value on the pin """
        return self.duty

    def write(self, value):
        """Overloaded to write duty cycle"""
        self.duty = value

    def on(self):
        """ Same functionality as parent, but done with PWM intact"""
        self.duty = 1

    def off(self):
        """ Same functionality as parent, but done with PWM intact"""
        self.duty = 0

    def __pwm(self, frequency, duty):
        """ Description:
        -If hardware_enabled is True, start a hardware pwm with the requested duty.
        -Otherwise (or if setting a hardware pwm fails and hardware_enabled is write to False),
         write a software pwm in the same manner."""
        if self.hardware_enabled:
            self.__hardware_pwm(frequency, duty)
        if not self.hardware_enabled:
            self.__software_pwm(frequency, duty)

    def __hardware_pwm(self, frequency, duty):
        """ Description:
        -Tries to write a hardware pwm. result == 0 if it suceeds.
        -Sets hardware_enabled flag to indicate success or failure"""
        # print('pin: %3.0d freq: %5.0d duty: %4.2f'%(self.pin,frequency,duty))
        result = self.pig.hardware_PWM(self.pin, frequency, duty)
        if result != 0:
            self.hardware_enabled = False
            raise RuntimeWarning(
                'Failed to start hardware PWM with frequency {} on pin {}. Error: {}'.format(frequency, self.pin,
                                                                                             self.pig.error_text(
                                                                                                 result)))
        else:
            self.hardware_enabled = True

    def __software_pwm(self, frequency, duty):
        """ Used for pins where hardware PWM is not available. """
        self.pig.set_PWM_dutycycle(self.pin, duty)
        realized_frequency = self.pig.set_PWM_frequency(self.pin, frequency)
        if frequency != realized_frequency:
            raise RuntimeWarning(
                'A PWM frequency of {} was requested but the best that could be done was {}'.format(frequency,
                                                                                                    realized_frequency))
        self.hardware_enabled = False


class PWMControlValve(PWMOutput, SolenoidBase):
    """ An extension of PWMOutput which incorporates linear
    compensation of the valve's response.
    """

    def __init__(self, pin, form='Normally Closed', initial_duty=0, frequency=None, pig=None):
        PWMOutput.__init__(self, pin=pin, initial_duty=initial_duty, frequency=frequency, pig=pig)
        SolenoidBase.__init__(self, form=form)

    @property
    def setpoint(self):
        """ The linearized setpoint corresponding to the current duty cycle according to the valve's response curve

        Args:
            self:

        Returns:

        """
        return self.inverse_response(self.duty)

    @setpoint.setter
    def setpoint(self, setpoint):
        """Overridden to determine & write the duty cycle corresponting
        to the requested linearized setpoint according to the valve's
        response curve"""
        self.duty = self.response(setpoint)

    def response(self, setpoint):
        """Setpoint takes a value in the range (0,100) so as not to
        confuse with duty cycle, which takes a value in the range (0,1).
        Response curves are specific to individual valves and are to
        be implemented by subclasses. If not implemented in subclass,
        defaults to a perfectly linear response"""
        return setpoint / 100

    def inverse_response(self, duty_cycle):
        """Inverse of response. Given a duty cycle in the range (0,1),
        returns the corresponding linear setpoint in the range (0,100).
        """
        return duty_cycle * 100


class SPIDevice(IODeviceBase):
    """
    A class wrapper for pigpio SPI handles. Not really implemented.
    """

    def __init(self, channel, baudrate, pig=None):
        super().__init__(pig)
        self.open(channel, baudrate)

    def open(self, channel, baudrate):
        """ Opens an SPI connection and returns the pigpiod handle.
        """
        self._handle = self.pig.spi_open(channel, baudrate)

    def close(self):
        """ Extends superclass method. Checks that pigpiod is connected
        and if a handle has been set - if so, closes an SPI connection.
        """
        super().close()
        self.pig.spi_close(self.handle)

# class HumiditySensor(Sensor):
#    """ Not yet implemented.
#    """
#    def __init__(self):
#        raise NotImplementedError

# class TemperatureSensor(Sensor, SPIDevice):
#    """ Not yet implemented
#    """
#    def __init__(self):
#        raise NotImplementedError

# class OxygenSensor(AnalogSensor):
#    """ Not yet implemented. Would need to define calibration and
#    overload _convert() to add unit conversion.
#    """
#    def __init__(self):
#        raise NotImplementedError