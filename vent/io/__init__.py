""" Provides helper functions and base classes for inheritance by subclasses in vent.io.
"""

import time
from abc import ABC, abstractmethod

import numpy as np
import pigpio


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
        self.close()
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

    def close(self):
        """ Closes an I2C/SPI (or potentially Serial) connection
        """
        if not self.pigpiod_ok() or self.handle <= 0:
            return


class Sensor(ABC):
    """ Abstract base Class describing generalized sensors. Defines a
    mechanism for limited internal storage of recent observations and
    methods to pull that data out for external use.
    """
    _DEFAULT_STORED_OBSERVATIONS = 128

    def __init__(self):
        """ Upon creation, calls update() to ensure that if get is
        called there will be something to return
        """
        self._data = np.zeros(
            self._DEFAULT_STORED_OBSERVATIONS,
            dtype=np.float16
        )
        self._i = 0
        self._data_length = self._DEFAULT_STORED_OBSERVATIONS
        self._last_timestamp = -1

    def update(self):
        """ Make a sensor reading, verify that it makes sense and store
        the result internally. Returns True if reading was verified and
        False if something went wrong.
        """
        value = self._read()
        if self._verify(value):
            self.__store_last(value)
            self._last_timestamp = time.time()
        return self._verify(value)

    def get(self):
        """ Return the most recent sensor reading.
        """
        if self._last_timestamp == -1:
            raise RuntimeWarning('get() called before update()')
        return self._data[(self._i - 1) % self._data_length]

    def age(self):
        """ Returns the time since the last sensor update, in seconds.
        """
        if self._last_timestamp == -1:
            raise RuntimeError('age() called before update()')
        return time.time() - self._last_timestamp

    def reset(self):
        """ Resets the sensors internal memory. May be overloaded by
        subclasses to extend functionality specific to a device.
        """
        self._data = np.zeros(self.data_length, dtype=np.float16)
        self._i = 0

    @property
    def data(self):
        """ Generalized, not necessarily performant. Returns an ndarray
        of observations arranged oldest to newest. Result has length
        equal to the lessor of self.n and the number of observations
        made.

        Note: ndarray.astype(bool) returns an equivalent sized array
        with True for each nonzero element and False everywhere else.
        """
        rolled = np.roll(self._data, self.data_length - self._i)
        return rolled[rolled.astype(bool)]

    @property
    def data_length(self):
        """ Returns the number of observations kept in the Sensor's
        internal ndarray. Once the ndarray has been filled, the sensor
        begins overwriting the oldest elements of the ndarray with new
        observations such that the size of the internal storage stays
        constant.
        """
        return self._data_length

    @data_length.setter
    def data_length(self, new_data_length):
        """ Set a new length for stored observations. Clears existing
        observations and resets. """
        self._data_length = new_data_length
        self.reset()

    def _read(self):
        """ Calls _raw_read and scales the result before returning it
        """
        return self._convert(self._raw_read())

    @abstractmethod
    def _verify(self, value):
        """ Validate reading and throw exception/alarm if sensor does not
        appear to be working correctly
        """
        raise NotImplementedError('Subclass must implement _verify()')

    @abstractmethod
    def _convert(self, raw):
        """ Converts a raw reading from a sensor in whatever forma
        the device communicates with into a meaningful result.
        """
        raise NotImplementedError('Subclass must implement _raw_read()')

    @abstractmethod
    def _raw_read(self):
        """ Requests a new observation from the device and returns the
        raw result in whatever format/units the device communicates with
        """
        raise NotImplementedError('Subclass must implement _raw_read()')

    def __store_last(self, value):
        """ Takes a value and stores it in self.data. Increments counter
        """
        self._data[self._i] = value
        self._i = (self._i + 1) % self.data_length