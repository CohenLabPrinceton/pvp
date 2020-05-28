import trio
from collections import OrderedDict
from vent.io.devices import I2CDevice, be16_to_native
from vent.io.devices import AsyncSMBus


class AsyncI2CDevice:
    Register = I2CDevice.Register

    def __init__(self, i2c_address, smbus: AsyncSMBus):
        self._i2c_address = i2c_address
        self._smbus = smbus

    async def read_register(self, register, signed=False):
        """ Read 2 bytes from the specified register and convert to int

        Args:
            register (int): The index of the register to read.
            signed (bool): Whether or not the data to read is expected to be signed.

        Returns:
            int: integer representation of 16 bit register contents.
        """
        # print(type(self._smbus))
        async with self._smbus as bus:
            await bus.set_address(self._i2c_address)
            data = await bus.read_word_data(self._i2c_address, register)
            # print('Read {} from register {}'.format(data, register))
        return int.from_bytes(data, 'big', signed=signed)

    async def write_register(self, register, word, signed=False):
        """ Write 2 bytes to the specified register, converting from int

        Args:
            register (int): The index of the register to write to
            word (int): The unsigned 16 bit integer to write to the register (must be consistent with 'signed')
            signed (bool): Whether or not 'word' is signed
        """
        async with self._smbus as bus:
            await bus.set_address(self._i2c_address)
            # print('trying to write {} to register {}'.format(word.to_bytes(2, 'little', signed=signed), register))
            await bus.write_word_data(
                self._i2c_address,
                register,
                word.to_bytes(2, 'big', signed=signed)
            )

    async def read_device(self, count=2) -> tuple:
        """ Read a specified number of bytes directly from the the device without specifying or changing the register.
        Does NOT perform LE/BE conversion.

        Args:
            count (int): The number of bytes to read from the device.

        Returns:
            tuple: a tuple of the number of bytes read and a bytearray containing the bytes. If there was an error the
            number of bytes read will be less than zero (and will contain the error code).
        """
        data = await self._smbus.read_device(i2c_addr=self._i2c_address, num_bytes=count)
        return len(data), data

    async def write_device(self, word, signed=False):
        """ Write 2 bytes to the device without specifying register, converting from int

        Args:
            word (int): The integer representation of the data to write.
            signed (bool): Whether or not `word` is signed.
        """
        await self._smbus.write_device(
            self._i2c_address,
            word.to_bytes(2, 'big', signed=signed)
        )


class AsyncADS1115(AsyncI2CDevice):
    # FIXME ought to inherit from ADS1115
    """ ADS1115 16 bit, 4 Channel Analog to Digital Converter.
    Datasheet:
     http://www.ti.com/lit/ds/symlink/ads1114.pdf?ts=1587872241912

    Default Values:
     Default configuration for vent:     0xC3E3
     Default configuration on power-up:  0x8583
    """
    _DEFAULT_ADDRESS = 0x48
    _DEFAULT_VALUES = {'MUX': 0, 'PGA': 4.096, 'MODE': 'SINGLE', 'DR': 860}
    _TIMEOUT = 1
    """ Address Pointer Register (write-only) """
    _POINTER_FIELDS = ('P',)
    _POINTER_VALUES = (
        (
            'CONVERSION',
            'CONFIG',
            'LO_THRESH',
            'HIGH_THRESH'
        ),)
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
        'COMP_QUE')
    _CONFIG_VALUES = (
        ('NO_EFFECT', 'START_CONVERSION'),
        ((0, 1), (0, 3), (1, 3), (2, 3), 0, 1, 2, 3),
        (6.144, 4.096, 2.048, 1.024, 0.512, 0.256, 0.256, 0.256),
        ('CONTINUOUS', 'SINGLE'),
        (8, 16, 32, 64, 128, 250, 475, 860),
        ('TRADIONAL', 'WINDOW'),
        ('ACTIVE_LOW', 'ACTIVE_HIGH'),
        ('NONLATCHING', 'LATCHING'),
        (1, 2, 3, 'DISABLE'))
    USER_CONFIGURABLE_FIELDS = ('MUX', 'PGA', 'MODE', 'DR')
    """ Note:
    The Conversion Register is read-only and contains a 16bit
    representation of the requested value (provided the conversion is
    ready).

    The Lo-thresh & Hi-thresh Registers are not Utilized here. However,
    their function and usage are described in the datasheet. Should you
    want to extend the functionality implemented here.
    """

    def __init__(self, address=_DEFAULT_ADDRESS, smbus=None):
        """ Initializes registers: Pointer register is write only,
        config is R/W. Sets initial value of _last_cfg to what is
        actually on the ADS.Packs default settings into _cfg, but does
        not actually write to ADC - that occurs when read_conversion()
        is called.

        Args:
            address (int): I2C address of the device. (e.g., `i2c_address=0x48`)
            i2c_bus (int): The I2C bus to use. Should probably be set to 1 on Raspberry Pi.
            pig (PigpioConnection): pigpiod connection to use; if not specified, a new one is established
        """
        smbus = AsyncSMBus() if smbus is None else smbus
        super().__init__(address, smbus)
        self.pointer = self.Register(self._POINTER_FIELDS, self._POINTER_VALUES)
        self._config = self.Register(self._CONFIG_FIELDS, self._CONFIG_VALUES)
        self._last_cfg = None
        self._cfg = None
        self._conversion_lock = trio.Lock()
        self.isopen = False

    async def aopen(self):
        self._last_cfg = self._read_last_cfg()
        self._cfg = self._config.pack(cfg=await self._last_cfg, **self._DEFAULT_VALUES)
        self.isopen = True

    async def read_conversion(self, **kwargs):
        """ Returns a voltage (expressed as a float) corresponding to a channel on the ADC.
        The channel to read from, along with the gain, mode, and sample rate of the conversion may be may be  specified
        as optional parameters. If read_conversion() is called with no parameters, the resulting voltage corresponds to
        the channel last read from and the same conversion settings.

        Args:
            MUX: The pin to read from in single channel mode: e.g., `0, 1, 2, 3`
                or, a tuple of pins over which to make a differential reading.
                e.g., `(0, 1), (0, 3), (1, 3), (2, 3)`
            PGA: The full scale voltage (FSV) corresponding to a programmable gain setting.
                e.g., `(6.144, 4.096, 2.048, 1.024, 0.512, 0.256, 0.256, 0.256)`
            MODE: Whether to set the ADC to continuous conversion mode, or operate in single-shot mode.
                e.g., `'CONTINUOUS', 'SINGLE'`
            DR: The data rate to make the conversion at; units: samples per second.
                e.g., `8, 16, 32, 64, 128, 250, 475, 860`
        """
        return (
                await self._read_conversion(**kwargs)
                * self.config.PGA.unpack(self.cfg) / 32767
        )

    def print_config(self) -> OrderedDict:
        """ Returns the human-readable configuration for the next read.

        Returns:
            OrderedDict: an ordered dictionary of the form {field: value}, ordered from MSB -> LSB
        """
        return self.config.unpack(self.cfg)

    @property
    def config(self):
        """ Returns the Register object of the config register.

        Returns:
            vent.io.devices.I2CDevice.Register: The Register object initialized for the ADS1115.
        """
        return self._config

    @property
    def cfg(self) -> int:
        """ Returns the contents (as a 16-bit unsigned integer) of the configuration that will be written to the config
        register when read_conversion() is next called.
        """
        return self._cfg

    async def _read_conversion(self, **kwargs) -> int:
        """ Backend for read_conversion. Returns the contents of the 16-bit conversion register as an unsigned integer.

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

        Args:
            **kwargs: see documentation of vent.io.devices.ADS1115.read_conversion
        """
        self._cfg = self._config.pack(cfg=self.cfg, **kwargs)
        mode = self.config.MODE.unpack(self.cfg)
        if self.cfg != self._last_cfg or mode == 'SINGLE':
            async with self._conversion_lock:
                await self.write_register(self.pointer.P.pack('CONFIG'), self.cfg)
                self._last_cfg = self.cfg
                result = await self._get_conversion()
        return result

    async def _get_conversion(self):
        data_rate = self.config.DR.unpack(self.cfg)
        await trio.sleep(1/data_rate)
        result = await self.read_register(self.pointer.P.pack('CONVERSION'), signed=True)
        return result

    async def _read_last_cfg(self) -> int:
        """ Reads the config register and returns the contents as a 16-bit unsigned integer;
        updates internal record _last_cfg.
        """
        self._last_cfg = await self.read_register(self.pointer.P.pack('CONFIG'))
        return self._last_cfg

    async def _ready(self) -> bool:
        """ Return status of ADC conversion; True indicates the conversion is complete and the results ready to be read.
        """
        return bool(await self.read_register(self.pointer.P.pack('CONFIG')) >> 15)


class AsyncADS1015(AsyncADS1115):
    """ ADS1015 16 bit, 4 Channel Analog to Digital Converter.
    Datasheet:
      http://www.ti.com/lit/ds/symlink/ads1015.pdf?&ts=1589228228921

    Basically the same device as the ADS1115, except has 12 bit resolution instead of 16, and has different (faster)
    data rates. The difference in data rates is handled by overloading _CONFIG_VALUES. The difference in resolution is
    irrelevant for implementation.
    """

    _DEFAULT_ADDRESS = 0x48
    _DEFAULT_VALUES = {'MUX': 0, 'PGA': 4.096, 'MODE': 'SINGLE', 'DR': 3300}

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
        (128, 250, 490, 920, 1600, 2400, 3300, 3300),  # This one is different
        ('TRADIONAL', 'WINDOW'),
        ('ACTIVE_LOW', 'ACTIVE_HIGH'),
        ('NONLATCHING', 'LATCHING'),
        (1, 2, 3, 'DISABLE')
    )
    USER_CONFIGURABLE_FIELDS = ('MUX', 'PGA', 'MODE', 'DR')

    def __init__(self, address=_DEFAULT_ADDRESS, smbus=None):
        """ See: vent.io.devices.ADS1115.__init__
        """
        super().__init__(address, smbus)
