import random
import pytest

swap_dict = {
    "NORMAL": "SWAPPED",
    "SWAPPED": "NORMAL"
}
reg_nums = {'CONVERSION': 0, 'CONFIG': 1, 'SFM': 2}
reg_names = ('CONVERSION', 'CONFIG', 'SFM')


def mock_register(reg, swp, idx):
    """ A collection of fake register values. Values returned are values that might actually be found in the registers
    they claim to be from.

    Args:
        reg: Which fake register the values might have come from. (From the ADS1x15: 'CONFIG', 'CONVERSION'. From the
            SFM3200: 'SFM')
        swp: 'NORMAL' or byteswapped: 'SWAPPED'
        idx: index of value. 0 & 1 are normal values for testing purposes, reg, swp = 'CONFIG', 2 contains a value that
            might be found on the ADS1x15 when a conversion has begun but is not ready yet. (OS bit = 0)

    Returns:
        int: a register value
    """
    registers = {
        'CONVERSION': {
            'NORMAL': (0x682A, 0x223F),
            'SWAPPED': (0x2A68, 0x3F22)
        },
        'CONFIG': {
            'NORMAL': (0xC3E3, 0x8583, 0x43E3),
            'SWAPPED': (0xE3C3, 0x8385, 0xE343)
        },
        'SFM': {
            'NORMAL': (0x8E10, 0x71F0),
            'SWAPPED': (0x108E, 0xF071)
        }
    }
    return registers[reg][swp][idx]


class MockThread:
    def __init__(self, *args, **kwargs):
        pass
    #    print(
    #        "called MockThread.__init__(",
    #        (arg for arg in args),
    #        {key: value for key, value in kwargs.items()},
    #        ")"
    #    )

    def stop(self):
        pass
     #   print("called MockThread.stop()")


class MockSocket:
    def __init__(self, *args, **kwargs):
        pass
    #    print(
    #        "called MockSocket.__init__(",
    #        (arg for arg in args),
    #        {key: value for key, value in kwargs.items()},
    #        ")"
    #    )

    @staticmethod
    def close():
        pass
    #    print("called MockSocket.close()")

    def setsockopt(self, *args, **kwargs):
        pass
    #    print(
    #        "called MockSocket.setsockopt(",
    #        (arg for arg in args),
    #        {key: value for key, value in kwargs.items()},
    #        ")"
    #    )


class MockSockLock:
    def __init__(self, *args, **kwargs):
    #    print(
    #        "called MockSockLock.setsockopt(",
    #        (arg for arg in args),
    #        {key: value for key, value in kwargs.items()},
    #        ")"
    #    )
        self.s = None
        self.l = None


def mock_create_connection(host, timeout):
#    print("called socket.create_connection((host={}, port={}), timeout={})".format(host[0], host[1], timeout))
    return MockSocket


def mock_pigpio_i2c_open(self, i2c_bus, i2c_address):
    handle = random.randint(1, 5)
#    print("{}.i2c_open returned handle {} for I2C Address {} on I2C Bus {} ".format(self, handle, i2c_address, i2c_bus))
    return handle


def mock_pigpio_i2c_close(handle):
    pass
#    print("i2c_close called on handle {}".format(handle))


def mock_pigpio_command(*args, **kwargs):
    pass
#    print(
#        "called _pigpio_command(",
#        (arg for arg in args),
#        {key: value for key, value in kwargs.items()},
#        ")"
#    )


@pytest.fixture(autouse=True)
def mock_pigpio_base(monkeypatch):
    monkeypatch.setattr("socket.create_connection", mock_create_connection)
    monkeypatch.setattr("pigpio._socklock", MockSockLock)
    monkeypatch.setattr("pigpio._callback_thread", MockThread)
    monkeypatch.setattr("pigpio._pigpio_command", mock_pigpio_command)
    monkeypatch.delattr("pigpio._pigpio_command_nolock")
    monkeypatch.delattr("pigpio._pigpio_command_ext")
    monkeypatch.delattr("pigpio._pigpio_command_ext_nolock")
    monkeypatch.setattr("pigpio.pi.connected", 1, raising=False)


@pytest.fixture()
def mock_pigpio_i2c_base(monkeypatch):
    monkeypatch.setattr("pigpio.pi.i2c_open", mock_pigpio_i2c_open)
    monkeypatch.setattr("pigpio.pi.i2c_close", mock_pigpio_i2c_close)


def mock_i2c_read_device(reg, swp, idx):
    def _mock_i2c_read_device(handle, count):
#        print('called i2c_read_device(handle={},count={}'.format)
        return count, mock_register(reg, swp, idx).to_bytes(count, 'little')
    return _mock_i2c_read_device


def mock_i2c_write_device(reg, swp, idx):
    def _mock_i2c_write_device(handle, word):
        print("\n called _i2c_write_device(handle= {}, word={})".format(handle, word))
        assert int.from_bytes(word, 'little') == mock_register(reg, swap_dict[swp], idx)
    return _mock_i2c_write_device


def mock_i2c_read_i2c_block_data(swp, idx):
    def _mock_i2c_read_i2c_block_data(handle, register, count):
#        print("called _i2c_write_device(handle= {}, register={}, count={}".format(handle, reg, count))
        return count, mock_register(reg_names[register], swp, idx).to_bytes(count, 'little')
    return _mock_i2c_read_i2c_block_data


def mock_i2c_write_i2c_block_data(swp, idx, expected_word=None):
    def _mock_i2c_write_i2c_block_data(handle, register, word):
        print(
            "\n called _mock_i2c_write_i2c_block_data(handle= {}, register={}, word={})".format(
                handle,
                register,
                word)
        )
        if expected_word is None:
            assert int.from_bytes(word, 'little') == mock_register(reg_names[register], swap_dict[swp], idx)
        else:
            assert word == expected_word
    return _mock_i2c_write_i2c_block_data
