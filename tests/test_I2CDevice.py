from vent.io.devices import I2CDevice
from .pigpio_mocks import *


def test_i2c_device_pigpiod_ok(mock_pigpio_i2c_base):
    """__________________________________________________________________________________________________________TEST #1
    Tests the testing environment; more specifically, tests to make sure the pigpiod interface is mocked correctly.
        - creates an I2CDevice (which will try to connect to the pigpio daemon)
        - asserts that the I2CDevice believes it is connected to pigpiod

    Mocks:
        - function: socket.create_connection()  -> mock_create_connection
            -class:     socket.Socket               -> MockSocket
        - class:    pigpio._socklock            -> MockSockLock
        - class:    pigpio._callback_thread     -> MockThread
        - function: pigpio._pigpio_command      -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open          -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close         -> mock_pigpio_i2c_close
    """
    i2c_dev = I2CDevice(i2c_address=0x69, i2c_bus=1)
    assert i2c_dev.pigpiod_ok
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("idx", [0, 1])
def test_read_device(mock_pigpio_i2c_base, idx, monkeypatch):
    """__________________________________________________________________________________________________________TEST #2
    Tests vent.io.devices.I2CDevice.read_device(), which does NOT perform BE/LE conversion
        - creates an I2CDevice (which will try to connect to the pigpio daemon)
        - calls read_device() and verifies results match expected

    Mocks:
        - function: socket.create_connection()  -> mock_create_connection
            -class:     socket.Socket               -> MockSocket
        - class:    pigpio._socklock            -> MockSockLock
        - class:    pigpio._callback_thread     -> MockThread
        - function: pigpio._pigpio_command      -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open          -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close         -> mock_pigpio_i2c_close
        + method:   pigpio.pi.i2c_read_device   -> mock_i2c_read_device
    """
    swp = 'SWAPPED'
    i2c_dev = I2CDevice(i2c_address=0x69, i2c_bus=1)
    monkeypatch.setattr(i2c_dev._pig, "i2c_read_device", mock_i2c_read_device('SFM', swap_dict[swp], idx))
    result = i2c_dev.read_device(count=2)
    expected = mock_register('SFM', swp, idx).to_bytes(2, 'big')
    print('\n i2c_read_device returned: {}, expected: {} '.format(result[1], expected))
    assert result == (len(expected), expected)
    assert result[1] == expected
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("idx", [0, 1])
def test_write_device(mock_pigpio_i2c_base, idx, monkeypatch):
    """__________________________________________________________________________________________________________TEST #3
    Tests vent.io.devices.I2CDevice.write_device(), which DOES perform BE/LE conversion
        - creates an I2CDevice (which will try to connect to the pigpio daemon)
        - Picks a byte-swapped word from the mock_register and calls write_device(word)
        - Intercepts pigpio.pi.i2c_write_device and asserts word has been correctly converted & byteswapped

    Mocks:
        - function: socket.create_connection()  -> mock_create_connection
            -class:     socket.Socket               -> MockSocket
        - class:    pigpio._socklock            -> MockSockLock
        - class:    pigpio._callback_thread     -> MockThread
        - function: pigpio._pigpio_command      -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open          -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close         -> mock_pigpio_i2c_close
        + method:   pigpio.pi.i2c_write_device  -> mock_i2c_write_device
    """
    reg = 'SFM'
    swp = 'NORMAL'
    word = mock_register(reg, swp, idx)
    i2c_dev = I2CDevice(i2c_address=0x69, i2c_bus=1)
    monkeypatch.setattr(i2c_dev._pig, "i2c_write_device", mock_i2c_write_device(reg, swp, idx))
    i2c_dev.write_device(word)
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("idx", [0, 1])
@pytest.mark.parametrize("reg", ['CONFIG', 'CONVERSION'])
def test_read_register(mock_pigpio_i2c_base, reg, idx, monkeypatch):
    """__________________________________________________________________________________________________________TEST #4
    Tests vent.io.devices.I2CDevice.read_register(), which DOES perform BE/LE conversion
        - creates an I2CDevice (which will try to connect to the pigpio daemon)
        - calls read_register() and verifies results match expected

    Mocks:
        - function: socket.create_connection()          -> mock_create_connection
            -class:     socket.Socket                       -> MockSocket
        - class:    pigpio._socklock                    -> MockSockLock
        - class:    pigpio._callback_thread             -> MockThread
        - function: pigpio._pigpio_command              -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open                  -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close                 -> mock_pigpio_i2c_close
        + method:   pigpio.pi.i2c_read_i2c_block_data   -> mock_i2c_read_i2c_block_data
    """
    swp = 'SWAPPED'
    i2c_dev = I2CDevice(i2c_address=0x69, i2c_bus=1)
    monkeypatch.setattr(
        i2c_dev._pig,
        "i2c_read_i2c_block_data",
        mock_i2c_read_i2c_block_data(swp, idx)
    )
    result = i2c_dev.read_register(reg_nums[reg])
    expected = mock_register(reg, swap_dict[swp], idx)
    print('\n i2c_read_register returned: {}, expected: {} '.format(hex(result), hex(expected)))
    assert result == expected
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("idx", [0, 1])
@pytest.mark.parametrize("reg", ['CONFIG', 'CONVERSION'])
def test_write_register(mock_pigpio_i2c_base, reg, idx, monkeypatch):
    """__________________________________________________________________________________________________________TEST #5
    Tests vent.io.devices.I2CDevice.write_register(), which DOES perform BE/LE conversion
        - creates an I2CDevice (which will try to connect to the pigpio daemon)
        - Picks a byte-swapped word from the mock_register and calls write_register(word)
        - Intercepts pigpio.pi.i2c_write_i2c_block_data and asserts word has been correctly converted & byteswapped

    Mocks:
        - function: socket.create_connection()          -> mock_create_connection
            -class:     socket.Socket                       -> MockSocket
        - class:    pigpio._socklock                    -> MockSockLock
        - class:    pigpio._callback_thread             -> MockThread
        - function: pigpio._pigpio_command              -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open                  -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close                 -> mock_pigpio_i2c_close
        + method:   pigpio.pi.i2c_write_i2c_block_data  -> mock_i2c_write_device
    """
    swp = 'NORMAL'
    i2c_dev = I2CDevice(i2c_address=0x69, i2c_bus=1)
    monkeypatch.setattr(
        i2c_dev._pig,
        "i2c_write_i2c_block_data",
        mock_i2c_write_i2c_block_data(swp, idx)
    )
    word = mock_register(reg, swp, idx)
    i2c_dev.write_register(reg_nums[reg], word)
    """__________________________________________________________________________________________________________
    """