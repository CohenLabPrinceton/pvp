""" Base classes & functions used throughout vent.io.devices
"""
from abc import ABC
from collections import OrderedDict

import pigpio


class IODeviceBase(ABC):
    """ Abstract base Class for pigpio handles (or whatever other GPIO library
    we end up using)

    Note: pigpio commands return -144 if an error is encountered while
    attempting to communicate with the demon. TODO would be to recognize
    when that occurs and handle it gracefully, i.e. kill the daemon,
    restart it, and reopen the python interface(s)
    """

    def __init__(self, pig):
        """ Initializes the pigpio python bindings oject if necessary,
        and checks that it is actually running.
        """
        self._pig = pig if pig is not None else pigpio.pi()
        self._handle = -1
        if not self.pigpiod_ok():
            raise RuntimeError

    def __del__(self):
        """ Closes the i2c/spi connection, and stops the python bindings
        for the pigpio daemon.
        """
        self._close()
        if self.pigpiod_ok:
            self.pig.stop()

    @property
    def pig(self):
        """ The pigpio python bindings object
        """
        return self._pig

    @property
    def handle(self):
        """ Pigpiod handle associated with device (only for i2c/spi)
        """
        return self._handle

    def pigpiod_ok(self):
        """ Returns True if pigpiod is running and False if not
        """
        return self.pig.connected

    def _close(self):
        """ Closes an I2C/SPI (or potentially Serial) connection
        """
        if not self.pigpiod_ok() or self.handle <= 0:
            return


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
        self._open(i2c_bus, i2c_address)

    def _open(self, i2c_bus, i2c_address):
        """ Opens i2c connection given i2c bus and address.
        """
        self._handle = self.pig.i2c_open(i2c_bus, i2c_address)

    def _close(self):
        """ Extends superclass method. Checks that pigpiod is connected
        and if a handle has been set - if so, closes an i2c connection.
        """
        super()._close()
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
                # noinspection PyTypeChecker
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


class SPIDevice(IODeviceBase):
    """
    A class wrapper for pigpio SPI handles. Not really implemented.
    """

    def __init(self, channel, baudrate, pig=None):
        super().__init__(pig)
        self._open(channel, baudrate)

    def _open(self, channel, baudrate):
        """ Opens an SPI connection and returns the pigpiod handle.
        """
        self._handle = self.pig.spi_open(channel, baudrate)

    def _close(self):
        """ Extends superclass method. Checks that pigpiod is connected
        and if a handle has been set - if so, closes an SPI connection.
        """
        super()._close()
        self.pig.spi_close(self.handle)


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


def be16_to_native(data, signed=False, count=2):
    """ Unpacks a bytearray respecting big-endianness of outside world
    and returns an int according to signed.
    """
    return int.from_bytes(data[1][:count], 'big', signed=signed)


def native16_to_be(word, signed=False, count=2):
    """ Packs an int into a bytearray while swapping big-endianness
    of the pi and returns bytearray
    """
    return word.to_bytes(count, 'big', signed=signed)
