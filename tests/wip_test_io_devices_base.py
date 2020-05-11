from unittest.mock import patch
from unittest import TestCase, main

import random
import vent.io.devices


""" A sampling of possible things you could find in the config register of the ADS1115 (these are all valid)"""
MOCK_CONFIG_REGISTER = (0xC3E3, 0x8583)
MOCK_CONVERSION_REGISTER = (-3000, 3000)
MOCK_SWAPPED_CONFIG_REGISTER = (0xE3C3, 0x8385)
MOCK_SWAPPED_CONVERSION_REGISTER = (18676, -18421)
""" A collection of samplings"""
MOCK_REGISTER_CONTENTS = (MOCK_CONFIG_REGISTER, MOCK_CONVERSION_REGISTER)
MOCK_SWAPPED_REGISTER_CONTENTS = (MOCK_SWAPPED_CONFIG_REGISTER, MOCK_SWAPPED_CONVERSION_REGISTER)


def mock_i2c_read_i2c_block_data(self, handle, register, count):
    """ Mock designed specifically for testing the ADS1115 - returns data consistent with what might be found on those
    registers.

    Args:
        handle: Ignored
        register: Number in the range [0,1,2,3]; {0: Conversion, 1: Config, 2: Lo_thresh, 3: High_thresh}
        count: The number of bytes to read (should always be 2 for the ADS1115)

    Returns:

    """
    if handle <= 0:
        raise ValueError('handle should be > 0')
    elif count != 2:
        raise ValueError('count should be 2')
    if register == 0:
        return count, MOCK_SWAPPED_CONVERSION_REGISTER[
            random.randrange(0, len(MOCK_SWAPPED_CONVERSION_REGISTER), 1)
        ].to_bytes(count, 'little')
    elif register == 1:
        return count, MOCK_SWAPPED_CONFIG_REGISTER[
            random.randrange(0, len(MOCK_SWAPPED_CONFIG_REGISTER), 1)
        ].to_bytes(count, 'little')
    else:
        raise ValueError


def mock_i2c_read_device(self, handle, num_bytes):
    if handle <= 0:
        raise RuntimeError
    return num_bytes, abs(random.getrandbits(8 * num_bytes)).to_bytes(num_bytes, 'little')


class I2CDeviceTests(TestCase):

    @patch('vent.io.devices.PigpioConnection.i2c_open', return_value=1)
    @patch('vent.io.devices.IODeviceBase.pigpiod_ok', return_value=1)
    def setUp(self, *args):
        """ Instantiate an I2CDevice, and then delete it. Assert i2c_open() and i2c_close() were called"""
        self.i2c_device = vent.io.devices.I2CDevice(i2c_address=0x48, i2c_bus=1)
        self.n_registers = len(MOCK_REGISTER_CONTENTS)
        self.idx = []
        self.test_word = []
        self.expected_results = []
        for i in range(self.n_registers):
            self.idx.append(random.randrange(0, len(MOCK_REGISTER_CONTENTS[i]), 1))
            self.test_word.append(MOCK_REGISTER_CONTENTS[i][self.idx[i]])
            self.expected_results.append(MOCK_SWAPPED_REGISTER_CONTENTS[i][self.idx[i]])

    @patch('vent.io.devices.PigpioConnection.i2c_read_device', mock_i2c_read_device)
    def test_read_device(self):


    @patch('vent.io.devices.PigpioConnection.i2c_write_device')
    def test_write_device(self, *args):
        """ This test writes a test word to a mock device, and we check to make sure the mock pigpio i2c write was
        passed the correctly byteswapped expected value.
        """
        for i in range(self.n_registers):
            signed = False if i == 0 else True
            self.i2c_device.write_device(self.test_word[self.idx[i]], signed=signed)

        # Check results
        for i in range(self.n_registers):
            self.i2c_device.pig.i2c_write_device.assert_called_with(1, self.expected_results[i])

    @patch('vent.io.devices.PigpioConnection.i2c_read_i2c_block_data', mock_i2c_read_i2c_block_data)
    def test_read_register(self):
        """ This test reads a mock'd register, and checks to make sure the result is one of the possible byteswapped
         values.
         """
        result = []
        for i in range(self.n_registers):
            signed = False if i == 0 else True
            result.append(self.i2c_device.read_register(register=i, signed=signed))

        # Check results
        for res, possible in zip(result, MOCK_REGISTER_CONTENTS):
            assert res in possible

    @patch('vent.io.devices.PigpioConnection.i2c_write_i2c_block_data')
    def test_write_register(self, *args):
        for i in range(self.n_registers):
            signed = False if self.test_word[self.idx[i]] >= 0 else True
            self.i2c_device.write_register(register=i, word=self.test_word[self.idx[i]], signed=signed)

            # Check results
        for register, expected in zip(self.idx, self.expected_results):
            self.i2c_device.pig.i2c_write_i2c_block_data.assert_called_with(1, register, expected.to_bytes(2, 'little',signed=signed))
