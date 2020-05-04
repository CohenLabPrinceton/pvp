""" Provides helper functions and base classes for inheritance by subclasses in vent.io.
"""

from abc import ABC

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