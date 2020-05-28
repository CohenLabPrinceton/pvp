import trio
from trio.abc import AsyncResource
from fcntl import ioctl

# Commands from uapi/linux/i2c-dev.h
I2C_SLAVE = 0x0703  # Use this slave address


class AsyncSMBus(AsyncResource):

    def __init__(self, bus=1, force=False):
        """
        Initialize and (optionally) open an i2c bus connection.

        :param bus: i2c bus number (e.g. 0 or 1)
            or an absolute file path (e.g. `/dev/i2c-42`).
            If not given, a subsequent  call to ``open()`` is required.
        :type bus: int or str
        :param force: force using the slave address even when driver is
            already using it.
        :type force: boolean
        """
        self.lock = trio.Lock()
        self._file = None
        self.bus = bus
        self.address = None
        self.register = None
        if isinstance(bus, int):
            self.path = "/dev/i2c-{}".format(bus)
        elif isinstance(bus, str):
            self.path = bus
        else:
            raise TypeError("Unexpected type(bus)={}".format(type(bus)))

    async def __aenter__(self):
        await self.aopen()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    async def aclose(self):
        """ Close the i2c connection."""
        self.register = None
        self.address = None
        if self._file:
            self._file.close()
            self._file = None
        self.lock.release()

    async def aopen(self):
        """ Opens an I2C connection; aquires smbus lock"""
        await self.lock.acquire()
        self._file = open(self.path, mode='r+b', buffering=0)

    async def set_address(self, address):
        """ Set I2C slave address to use for this or subsequent calls.

        Args:
            address: I2C Address to set
        """
        if self.address != address:
            ioctl(self._file.fileno(), I2C_SLAVE, address)
            self.address = address

    async def _set_register_for_read(self, register):
        """
        Set register for subsequent read call.

        Args:
            register (int): The register to access
        """
        if self.register != register:
            self._file.write(register.to_bytes(1, 'big'))
            self.register = register

    def _sync_set_register_for_write(self, register, data):
        """ Adds a byte to the beginning of data to set the pointer register to the desired place

        Args:
            register (int): The register to read from
            data (bytes): The data to write

        Returns:
            bytes: returns the data to be written with the register byte prepended
        """
        if not isinstance(data, bytes):
            raise TypeError('_set_register_for_write expected bytes but got {}'.format(type(data)))
        data = register.to_bytes(1, 'big') + data
        self.register = register
        return data

    async def __read(self, i2c_addr, num_bytes, register=None):
        """ Underlying function to read data from a device

        Args:
            i2c_addr (int): I2C Address of the device to read from
            num_bytes (int): The number of bytes to read
            register: The register to read from, or None if a device transaction

        Returns:
            bytes: the data returned from the device
        """
        await self.set_address(i2c_addr)
        if register is not None:
            await self._set_register_for_read(register)
        return self._file.read(num_bytes)

    async def _read_device(self, i2c_addr, num_bytes):
        """ Perform a device-level read transaction (for devices with no pointer register)

        Args:
            i2c_addr (int): I2C Address of the device to read from
            num_bytes (int): The number of bytes to read

        Returns:
            bytes: the data returned from the device
        """
        return await self.__read(i2c_addr=i2c_addr, num_bytes=num_bytes)

    async def _read_register(self, i2c_addr, num_bytes, register):
        """ Read the contents of a specific register from a device

        Args:
            i2c_addr (int): I2C Address of the device to read from
            num_bytes (int): The number of bytes to read
            register: The register to read from, or None if a device transaction

        Returns:
            bytes: the data returned from the device
        """
        return await self.__read(i2c_addr=i2c_addr, num_bytes=num_bytes, register=register)

    async def __write(self, i2c_addr, data, register=None, num_bytes=None):
        """ Underlying function to write data to a device

        Args:
            i2c_addr (int): I2C Address of the device to write to
            data (int or bytes): The data to write
            register (int or None): The register to write to
            num_bytes (int or None): The number of bytes to write. Required only if data has type int
        """
        await self.set_address(i2c_addr)
        if isinstance(data, int):
            if num_bytes is None:
                raise ValueError('Must specify num_bytes when calling _write_data with integer data')
            data = data.to_bytes(num_bytes, 'big')
        else:
            if num_bytes != len(data):
                raise RuntimeWarning('num_bytes was provided but does not match length of data (it was ignored)')
        data = self._sync_set_register_for_write(register, data)
        self._file.write(data)

    async def _write_device(self, i2c_addr, data, num_bytes=None):
        """ Perform a device-level write transaction (for devices with no pointer register)

        Args:
            i2c_addr (int): I2C Address of the device to write to
            data (int or bytes): The data to write
            num_bytes (int or None): The number of bytes to write. Required only if data has type int
        """
        await self.__write(i2c_addr, data, register=None, num_bytes=num_bytes)

    async def _write_register(self, i2c_addr, data, register, num_bytes=None):
        """ Underlying function to write data to a specific register of a device

        Args:
            i2c_addr (int): I2C Address of the device to write to
            data (int or bytes): The data to write
            register (int): The register to write to
            num_bytes (int or None): The number of bytes to write. Required only if data has type int
        """
        await self.__write(i2c_addr, data, register=register, num_bytes=num_bytes)

    async def read_byte_data(self, i2c_addr, register):
        """ Read a single byte from a designated register.

        Args:
            i2c_addr: I2C Address of the device to write to
            register: The register to read from
        """
        return await self._read_register(i2c_addr, num_bytes=1, register=register)

    async def write_byte_data(self, i2c_addr, register, data):
        """ Write a single byte to a register

        Args:
            i2c_addr (int): I2C Address of the device to write to
            register (int): The register to write to
            data (int or bytes): The data to write
        """
        await self._write_register(i2c_addr=i2c_addr, data=data, register=register, num_bytes=1)

    async def read_word_data(self, i2c_addr, register):
        """ Read two bytes from a designated register.

        Args:
            i2c_addr: I2C Address of the device to read from
            register: The register to read from
        """
        return await self._read_register(i2c_addr=i2c_addr, num_bytes=2, register=register)

    async def write_word_data(self, i2c_addr, register, data):
        """ Write two bytes to a register

        Args:
            i2c_addr (int): I2C Address of the device to write to
            register (int): The register to write to
            data (int or bytes): The data to write
        """
        await self._write_register(i2c_addr=i2c_addr, data=data, register=register, num_bytes=2)

    async def read_byte(self, i2c_addr):
        """ Read a single byte from a device.

        Args:
            i2c_addr: I2C Address of the device to read from
        """
        return await self._read_device(i2c_addr=i2c_addr, num_bytes=1)

    async def write_byte(self, i2c_addr, data):
        """ Write a single byte to a device.

        Args:
            i2c_addr (int): I2C Address of the device to write to
            data (int or bytes): The data to write

        """
        await self._write_device(i2c_addr=i2c_addr, data=data, num_bytes=1)

    async def read_device(self, i2c_addr, num_bytes):
        """ Read num_bytes from a device.

        Args:
            i2c_addr: I2C Address of the device to read from
            num_bytes (int): The number of bytes to read
        """
        return await self._read_device(i2c_addr=i2c_addr, num_bytes=num_bytes)

    async def write_device(self, i2c_addr, data, num_bytes=None):
        """ Write bytes to a device.

        Args:
            i2c_addr (int): I2C Address of the device to write to
            data (int or bytes): The data to write
            num_bytes (int or None): The number of bytes to write. Required only if data has type int

        """
        await self._write_device(i2c_addr=i2c_addr, data=data, num_bytes=num_bytes)

    async def read_i2c_block_data(self, i2c_addr, register, num_bytes):
        return await self._read_register(i2c_addr=i2c_addr, num_bytes=num_bytes, register=register)

    async def write_i2c_block_data(self, i2c_addr, register, data):
        if not (isinstance(data, bytes) or isinstance(data, bytearray)):
            raise TypeError("write_i2c_block_data expects bytelike but got {}".format(type(data)))
        await self._write_register(i2c_addr=i2c_addr, data=data, register=register, num_bytes=len(data))
