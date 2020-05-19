from .pigpio_mocks import *
import vent.io.devices as iodev


def test_mock_pigpio_base(patch_pigpio_base):
    """__________________________________________________________________________________________________________TEST #1
        Tests that the base fixture of pigpio mocks is indeed enough to instantiate pigpio.pi()
    """
    pig = iodev.PigpioConnection()
    assert isinstance(pig, pigpio.pi)
    assert pig.connected
    pig.stop()
    assert not pig.connected
    """__________________________________________________________________________________________________________
    """


def test_pigpio_connection_exception(patch_pigpio_base, monkeypatch):
    """__________________________________________________________________________________________________________TEST #2
        Tests to make sure an exception is thrown if, upon init, a PigpioConnection finds it is not connected."""
    def mock_create_bad_connection(host, timeout):
        """ mock of socket.create_connection(). Returns a bare-bones mock socket"""
        raise socket.error
    monkeypatch.setattr("socket.create_connection", mock_create_bad_connection)
    with pytest.raises(RuntimeError):
        iodev.PigpioConnection()
    with pytest.raises(RuntimeError):
        iodev.IODeviceBase()


def test_io_device_base_no_handles_to_close(patch_pigpio_base, monkeypatch):
    """__________________________________________________________________________________________________________TEST #3
        Tests that IODeviceBase._close() returns cleanly when it has no handles"""
    device = iodev.IODeviceBase()
    device._close()


@pytest.mark.parametrize("seed", [secrets.token_bytes(8) for _ in range(10)])
def test_mock_pigpio_i2c(patch_pigpio_i2c, mock_i2c_hardware, seed):
    """__________________________________________________________________________________________________________TEST #4
    Tests the functionality of the mock pigpio i2c device interface. More specifically, tests that:
    - mock hardware devices are initialized correctly
    - mock handles, i2c_open(), and i2c_close() can be used to add, interact with, and remove mock hardware devices
        - correct functioning of i2c_open is implied by the read/write tests
        - the correct functioning of i2c_close() is ascertained from the assertion that pig.mock_i2c[i2c_bus] is empty
    - mock i2c read and write functions work as intended
        - result['init'] is the inital value read from the register
        - result['write'] is the actual value found on the register after write
        - result['read'] is what was read back from the register
    - if there is only one register on the device, test read_device() and write_device() instead of read_register()
        and write_register()
    """
    random.seed(seed)
    n_devices = random.randint(1, 20)
    address_pool = random.sample(range(128), k=n_devices)
    pig = iodev.PigpioConnection()
    mocks = []
    for i in range(n_devices):
        mock = mock_i2c_hardware(i2c_address=address_pool.pop())
        pig.add_mock_hardware(mock['device'], mock['i2c_address'], mock['i2c_bus'])
        mock['handle'] = pig.i2c_open(mock['i2c_bus'], mock['i2c_address'])
        mocks.append(mock)
    for mock in mocks:
        handle = mock['handle']
        expected = {'init': [], 'write': [], 'read': []}
        result = {'init': [], 'write': [], 'read': []}
        for reg in range(len(mock['values'])):
            expected['init'] = mock['values'][reg]
            expected['write'] = expected['init']
            expected['read'] = mock['values'][reg]
            if len(mock['values']) == 1:
                result['init'] = pig.i2c_read_device(handle, 2)[1]
                pig.i2c_write_device(handle, mock['values'][0])
                result['write'] = pig.mock_i2c[mock['i2c_bus']][mock['i2c_address']].registers[0][-1]
                result['read'] = pig.i2c_read_device(handle, 2)[1]
            else:
                result['init'] = pig.i2c_read_i2c_block_data(handle, reg, count=2)[1]
                pig.i2c_write_i2c_block_data(handle, reg, mock['values'][reg])
                result['write'] = pig.mock_i2c[mock['i2c_bus']][mock['i2c_address']].registers[reg][-1]
                result['read'] = pig.i2c_read_i2c_block_data(handle, reg, count=2)[1]
            assert result == expected
        pig.i2c_close(handle)
    assert not pig.mock_i2c[0]
    assert not pig.mock_i2c[1]
    assert not pig.mock_i2c['spi']
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("seed", [secrets.token_bytes(8) for _ in range(100)])
def test_i2c_device(patch_pigpio_i2c, mock_i2c_hardware, seed):
    """__________________________________________________________________________________________________________TEST #5
    Tests the various basic I2CDevice methods, open, close, read,  write, etc.
        - Note: i2c_device.read_device() does not byteswap. write_device, read_register, and write_register all DO
            perform byteswaps. Therefore, `expected` does not get byteswapped like it normally would when num_registers
            is called (queuing up a read_device() call rather than a read_register() call)
    """
    results = []
    random.seed(seed)
    mock = mock_i2c_hardware()
    n_registers = len(mock['values'])
    data = [int.from_bytes(val, 'little') for val in mock['values']]
    if n_registers == 1:
        # We expect to get back raw bytes from read_device(), which have not been byteswapped
        expected = [bytes(reversed(mock['values'][0]))]
    else:
        # We expect to get back what we put in, if byteswapping is happening correctly on both read and write.
        expected = data
    pig = iodev.PigpioConnection()
    pig.add_mock_hardware(mock['device'], mock['i2c_address'], mock['i2c_bus'])
    i2c_device = iodev.I2CDevice(mock['i2c_address'], mock['i2c_bus'], pig=pig)
    assert i2c_device.pigpiod_ok
    if n_registers == 1:
        i2c_device.write_device(data[0])
        results.append(i2c_device.read_device()[1])
    else:
        for register in range(n_registers):
            i2c_device.write_register(register, data[register])
            results.append(i2c_device.read_register(register))
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
        iodev.I2CDevice.Register(fields=('one', 'two', 'three'), values=((0, 1, 3), (4, 5)))


def test_value_field_pack_unknown_value_exception():
    """__________________________________________________________________________________________________________TEST #7
        Tests that I2CDevice.Register throws an exception if it tries to init with a mismatched number of arguments
    """
    reg = iodev.I2CDevice.Register(fields=('one', 'two', 'three'), values=((0, 1, 3), (4, 5), ('hi', 'mark')))
    with pytest.raises(ValueError):
        reg.three.pack('oh')


def test_value_field_insert_unknown_value_exception():
    """__________________________________________________________________________________________________________TEST #8
        Tests that I2CDevice.Register throws an exception if it tries to init with a mismatched number of arguments
    """
    reg = iodev.I2CDevice.Register(fields=('one', 'two', 'three'), values=((0, 1, 3), (4, 5), ('hi', 'mark')))
    with pytest.raises(ValueError):
        reg.three.insert(0x0, 'oh')


def test_spi_device(patch_pigpio_i2c):
    channel = random.randint(1, 20)
    device = iodev.SPIDevice(channel=channel, baudrate=100)
    mock_device = MockHardwareDevice(secrets.token_bytes(2))
    device.pig.add_mock_hardware(mock_device, i2c_address=channel, i2c_bus='spi')
    assert device._handle >= 0
    device._close()


@pytest.mark.parametrize("ads1x15", [iodev.ADS1115, iodev.ADS1015])
@pytest.mark.parametrize("seed", [secrets.token_bytes(8) for _ in range(100)])
def test_read_conversion(patch_pigpio_i2c, mock_i2c_hardware, ads1x15, seed):
    """__________________________________________________________________________________________________________TEST #9
    Tests that the proper cfg is generated and written to the config register given kwargs, and tests that the
        conversion register is properly read & converted to signed int
    """
    random.seed(seed)
    kwargs = {
        "MUX": random.choice(ads1x15._CONFIG_VALUES[1]),
        "PGA": random.choice(ads1x15._CONFIG_VALUES[2]),
        "MODE": random.choice(ads1x15._CONFIG_VALUES[3]),
        "DR": random.choice(ads1x15._CONFIG_VALUES[4])}
    conversion_bytes = secrets.token_bytes(2)
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
    pig = iodev.PigpioConnection()
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
