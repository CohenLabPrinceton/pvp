from .pigpio_mocks import patch_pigpio_base, patch_pigpio_i2c, patch_pigpio_gpio, mock_i2c_hardware, patch_bad_socket
from .pigpio_mocks import MockHardwareDevice
from vent.io.devices import ADS1115, ADS1015, SPIDevice, PigpioConnection, IODeviceBase, I2CDevice

from secrets import token_bytes

import pigpio
import pytest
import random


def test_mock_pigpio_base(patch_pigpio_base):
    """__________________________________________________________________________________________________________TEST #1
    Tests that the base fixture of pigpio mocks is indeed enough to instantiate pigpio.pi()
    """
    pig = PigpioConnection()
    assert isinstance(pig, pigpio.pi)
    assert pig.connected
    pig.stop()
    assert not pig.connected
    """__________________________________________________________________________________________________________
    """


def test_pigpio_connection_exception(patch_pigpio_base, patch_bad_socket):
    """__________________________________________________________________________________________________________TEST #2
    Tests to make sure an exception is thrown if, upon init, a PigpioConnection finds it is not connected.
    """
    with pytest.raises(RuntimeError):
        PigpioConnection()
    with pytest.raises(RuntimeError):
        IODeviceBase()


def test_io_device_base_no_handles_to_close(patch_pigpio_base, monkeypatch):
    """__________________________________________________________________________________________________________TEST #3
    Tests that IODeviceBase._close() returns cleanly when it has no handles
    """
    device = IODeviceBase()
    device._close()


@pytest.mark.parametrize("seed", [token_bytes(8) for _ in range(128)])
def test_mock_pigpio_i2c(patch_pigpio_i2c, mock_i2c_hardware, seed):
    """__________________________________________________________________________________________________________TEST #4
    Tests the functionality of the mock pigpio i2c device interface. More specifically, tests that:
    - mock hardware devices are initialized correctly
    - mock handles, i2c_open(), and i2c_close() can be used to add, interact with, and remove mock hardware devices
        - correct functioning of i2c_open is implied by the read/write tests
        - the correct functioning of i2c_close() is ascertained from the assertion that pig.mock_i2c[i2c_bus] is empty
    - mock i2c read and write functions work as intended:
        - This is three tests in one. For each register of each mock hardware device:
            1) Read the register with i2c_read and store the result in results['init']. We expect it to be the value
            from the correct register of the matching mock_device (expected['init'])
            2) Write two random bytes to the register with i2c_write. Look at the actual contents of the target register
                and put them in results['write']. We expect them to be the same as the two random bytes we generated.
            3) Read the register with i2c_read again and put the results in expected['read']. These should also match
                the two random bytes from the 'write' test.
            -> Assert that the results match what we expect
    - if there is only one register on the device, test read_device() and write_device() instead of read_register()
        and write_register() -> this matches how such a device would be interacted with in practice.
    """
    random.seed(seed)
    n_devices = random.randint(1, 20)
    address_pool = random.sample(range(128), k=n_devices)
    pig = PigpioConnection()
    mocks = []
    for i in range(n_devices):
        mock = mock_i2c_hardware(i2c_address=address_pool.pop())
        pig.add_mock_hardware(mock['device'], mock['i2c_address'], mock['i2c_bus'])
        mock['handle'] = pig.i2c_open(mock['i2c_bus'], mock['i2c_address'])
        mocks.append(mock)
    for mock_device in mocks:
        handle = mock_device['handle']
        bus = mock_device['i2c_bus']
        address = mock_device['i2c_address']
        results = {'init': [], 'write': [], 'read': []}
        expected = {'init': [], 'write': [], 'read': []}
        for reg in range(len(mock_device['values'])):
            expected['init'] = mock_device['values'][reg]
            expected['write'] = token_bytes(2)
            expected['read'] = expected['write']
            if len(mock_device['values']) == 1:
                results['init'] = pig.i2c_read_device(handle, 2)[1]
                pig.i2c_write_device(handle, expected['write'])
                results['write'] = pig.mock_i2c[bus][address].registers[0][-1]
                results['read'] = pig.i2c_read_device(handle, 2)[1]
            else:
                results['init'] = pig.i2c_read_i2c_block_data(handle, reg, count=2)[1]
                pig.i2c_write_i2c_block_data(handle, reg, expected['write'])
                results['write'] = pig.mock_i2c[bus][address].registers[reg][-1]
                results['read'] = pig.i2c_read_i2c_block_data(handle, reg, count=2)[1]
            assert results == expected
        pig.i2c_close(handle)
    assert not pig.mock_i2c[0]
    assert not pig.mock_i2c[1]
    assert not pig.mock_i2c['spi']
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("seed", [token_bytes(8) for _ in range(128)])
def test_i2c_device(patch_pigpio_i2c, mock_i2c_hardware, seed):
    """__________________________________________________________________________________________________________TEST #5
    Tests the various basic I2CDevice methods, open, close, read,  write, etc.
        - Note: i2c_device.read_device() returns raw bytes (assumed to have big-endian ordering.) read_register, on the
        other hand, returns the integer representation of those bytes. write_device and write_register take an integer
        argument which is the written to the device register as a big-endian two's complement.
        - The RPi is native little endian, so to simulate/test the byte-swapping that occurs over I2C we generate a
        random 16-bit integer (`data`), write it to the register, and read it back.
        - If the int->byte-> int conversions in i2c_device are working correctly, we should expect one of two possible
         values to be returned (depending on whether read_device() or read_register() is called)
            - read_device() should return the big-endian two's complement of `data`
            - read_register() should just return `data`
    """
    results = []
    random.seed(seed)
    mock = mock_i2c_hardware()
    n_registers = len(mock['values'])
    data = [random.getrandbits(15) for _ in range(n_registers)]
    signed = random.getrandbits(1)
    expected = [data[0].to_bytes(2, 'big', signed=signed)] if n_registers == 1 else data
    pig = PigpioConnection()
    pig.add_mock_hardware(mock['device'], mock['i2c_address'], mock['i2c_bus'])
    i2c_device = I2CDevice(mock['i2c_address'], mock['i2c_bus'], pig=pig)
    assert i2c_device.pigpiod_ok
    if n_registers == 1:
        i2c_device.write_device(data[0], signed=signed)
        results.append(i2c_device.read_device()[1])
    else:
        for register in range(n_registers):
            i2c_device.write_register(register, data[register], signed=signed)
            results.append(i2c_device.read_register(register, signed=signed))
    i2c_device._close()
    assert not i2c_device._pig.mock_i2c[mock['i2c_bus']]
    assert results == expected
    """__________________________________________________________________________________________________________
    """


def test_register_arg_exception():
    """__________________________________________________________________________________________________________TEST #6
        Tests that I2CDevice.Register throws an exception if it tries to init with a mismatched number of arguments
    """
    with pytest.raises(ValueError):
        I2CDevice.Register(fields=('one', 'two', 'three'), values=((0, 1, 3), (4, 5)))


def test_value_field_pack_unknown_value_exception():
    """__________________________________________________________________________________________________________TEST #7
        Tests that I2CDevice.Register throws an exception if it tries to init with a mismatched number of arguments
    """
    reg = I2CDevice.Register(fields=('one', 'two', 'three'), values=((0, 1, 3), (4, 5), ('hi', 'mark')))
    with pytest.raises(ValueError):
        reg.three.pack('oh')


def test_value_field_insert_unknown_value_exception():
    """__________________________________________________________________________________________________________TEST #8
        Tests that I2CDevice.Register throws an exception if it tries to init with a mismatched number of arguments
    """
    reg = I2CDevice.Register(fields=('one', 'two', 'three'), values=((0, 1, 3), (4, 5), ('hi', 'mark')))
    with pytest.raises(ValueError):
        reg.three.insert(0x0, 'oh')


def test_spi_device(patch_pigpio_i2c):
    """__________________________________________________________________________________________________________TEST #9
        Tests that an SPI device can be created without issue. That's about all you can do with one of these anyway.
    """
    channel = random.randint(1, 20)
    device = SPIDevice(channel=channel, baudrate=100)
    mock_device = MockHardwareDevice(token_bytes(2))
    device.pig.add_mock_hardware(mock_device, i2c_address=channel, i2c_bus='spi')
    assert device._handle >= 0
    device._close()


@pytest.mark.parametrize("ads1x15", [ADS1115, ADS1015])
@pytest.mark.parametrize("seed", [token_bytes(8) for _ in range(128)])
def test_read_conversion(patch_pigpio_i2c, mock_i2c_hardware, ads1x15, seed):
    """_________________________________________________________________________________________________________TEST #10
    Tests that the proper cfg is generated and written to the config register given kwargs, and tests that the
        conversion register is properly read & converted to signed int
    """
    random.seed(seed)
    kwargs = {
        "MUX": random.choice(ads1x15._CONFIG_VALUES[1]),
        "PGA": random.choice(ads1x15._CONFIG_VALUES[2]),
        "MODE": random.choice(ads1x15._CONFIG_VALUES[3]),
        "DR": random.choice(ads1x15._CONFIG_VALUES[4])}
    conversion_bytes = token_bytes(2)
    expected_val = int.from_bytes(conversion_bytes, 'big', signed=True) * kwargs['PGA'] / 32767
    mock = mock_i2c_hardware(
        i2c_bus=1,
        i2c_address=ads1x15._DEFAULT_ADDRESS,
        n_registers=4,
        reg_values=[
            conversion_bytes,
            b'\x85\x83'
        ]
    )
    pig = PigpioConnection()
    pig.add_mock_hardware(mock['device'], mock['i2c_address'], mock['i2c_bus'])
    ads = ads1x15(pig=pig)

    expected_default_config = ads.config.unpack(0xC3E3)
    expected_config = ads.config.unpack(ads.config.pack(0xC3E3, **kwargs))
    assert ads.print_config() == expected_default_config
    result = ads.read_conversion(**kwargs)
    assert ads.print_config() == expected_config
    assert result == expected_val
    """__________________________________________________________________________________________________________
    """
