from .pigpio_mocks import *
from os import getrandom
from collections import OrderedDict
import vent.io.devices as iodev


def test_mock_pigpio_base(mock_pigpio_base):
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


@pytest.mark.parametrize("i2c_bus", [0, 1])
@pytest.mark.parametrize("seed", [getrandom(8) for x in range(1000)])
def test_mock_pigpio_i2c(mock_pigpio_i2c, seed, i2c_bus):
    """__________________________________________________________________________________________________________TEST #2
    Tests the functionality of the mock pigpio i2c device interface. More specifically, tests that:
    - mock hardware devices are initialized correctly using both ints and bytes as register values
    - mock handles, i2c_open(), and i2c_close() can be used to add, interact with, and remove mock hardware devices
        - correct functioning of i2c_open is implied by the read/write tests
        - the correct functioning of i2c_close() is ascertained from the assertion that pig.mock_i2c[i2c_bus] is empty
    - mock i2c read functions work as intended
        - asserts that bytes read from register match what they were initialized with exactly
    - mock i2c write functions work as intended
        - asserts that bytes written to and then read back from the register were byteswapped (during write)

    Setup:
    - Runs 10 times per i2c_bus
    """
    num_registers = []
    expected = {'init': [], 'write': []}
    results = {'init': [], 'write': []}
    handles = []
    random.seed(seed)
    num_devices = random.randint(1, 5)
    i2c_addresses = random.sample(range(128), num_devices)
    pig = pigpio.pi()
    for i in range(num_devices):
        num_registers.append(random.randint(1, 5))
        for key in expected.keys():
            expected[key].append([random.getrandbits(16).to_bytes(2, 'little') for x in range(num_registers[i])])
        init_data = [byte if random.getrandbits(1) else int.from_bytes(byte, 'little') for byte in expected['init'][i]]
        pig.add_mock_i2c_hardware(MockI2CHardwareDevice(*init_data), i2c_addresses[i], i2c_bus)
        handles.append(pig.i2c_open(i2c_bus, i2c_addresses[i]))
        if len(init_data) == 1:
            (cnt, data) = pig.i2c_read_device(handles[i], 2)
            results['init'].append([data])
            pig.i2c_write_device(handles[i], expected['write'][i][0])
            (cnt, data) = pig.i2c_read_device(handles[i], 2)
            results['write'].append([data])
        else:
            result = {'init': [], 'write': []}
            for reg in range(num_registers[i]):
                (cnt, data) = pig.i2c_read_i2c_block_data(handles[i], reg, count=2)
                result['init'].append(data)
                pig.i2c_write_i2c_block_data(handles[i], reg, expected['write'][i][reg])
                (cnt, data) = pig.i2c_read_i2c_block_data(handles[i], reg, count=2)
                result['write'].append(data)
            for key in results.keys():
                results[key].append(result[key])
        pig.i2c_close(handles[i])
    for device in range(num_devices):
        for reg in range(num_registers[device]):
            assert expected['init'][device][reg] == results['init'][device][reg]
            assert bytes(reversed(expected['write'][device][reg])) == results['write'][device][reg]
    assert not pig.mock_i2c[i2c_bus]
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("seed", [getrandom(8) for y in range(1000)])
def test_i2c_device(mock_pigpio_i2c, seed):
    """__________________________________________________________________________________________________________TEST #1
    Tests the various basic I2CDevice methods, open, close, read,  write, etc.
        - Note: i2c_device.read_device() does not byteswap. write_device, read_register, and write_register all DO
            perform byteswaps. Therefore, `expected` does not get byteswapped like it normally would when num_registers
            is called (queuing up a read_device() call rather than a read_register() call)
    """
    random.seed(seed)
    i2c_address = random.randint(1, 127)
    i2c_bus = random.getrandbits(1)
    num_registers = random.randint(1, 127)
    register_data = [random.getrandbits(16) for x in range(num_registers)]
    if num_registers == 1:
        expected = [data.to_bytes(2, 'little') for data in register_data]
    else:
        expected = [int.from_bytes(data.to_bytes(2, 'little'), 'big') for data in register_data]
    mock_ads = MockI2CHardwareDevice(*register_data)
    pig = iodev.PigpioConnection()
    pig.add_mock_i2c_hardware(mock_ads, i2c_address, i2c_bus)
    i2c_device = iodev.I2CDevice(i2c_address, i2c_bus, pig=pig)
    assert i2c_device.pigpiod_ok
    results = []
    if num_registers == 1:
        i2c_device.write_device(register_data[0])
        (count, result) = i2c_device.read_device()
        results.append(result)
    else:
        for register in range(num_registers):
            i2c_device.write_register(register, register_data[register])
            results.append(i2c_device.read_register(register))
    i2c_device._close()
    assert not i2c_device._pig.mock_i2c[i2c_bus]
    assert results == expected
    """__________________________________________________________________________________________________________
    """

'''
@pytest.mark.parametrize("idx", [0, 1])
@pytest.mark.parametrize("mux", [(0, 1),  (2, 3), 0, 3])
@pytest.mark.parametrize("pga", [6.144, 4.096, 0.256])
@pytest.mark.parametrize("mode", ['CONTINUOUS', 'SINGLE'])
@pytest.mark.parametrize("dr_idx", [0, 3, 5, 7])
@pytest.mark.parametrize("ads1x15", [iodev.ADS1115, iodev.ADS1015])
def test_read_conversion(mock_pigpio_i2c, idx, mux, pga, mode, dr_idx, ads1x15, monkeypatch):
    """__________________________________________________________________________________________________________TEST #1
    Tests a subset of the possible (valid) parameter combinations on both the ADS1115 & ADS1x115

        - Patches pigpio.pi with the read method used by ads.__init__
        - Initializes an ADS1x15
        - Patches ads._pig with write method used by read_conversion & Co
        - Calls read_conversion(kwargs), where kwargs is parameterized
            - Builds the expected bytes to be written to the config registry and intercepts them in when
                pigpio.pi.i2c_write_i2c_block_data is called
        - Asserts that the result matches what is expected
    """
    dr_ads1115 = [8, 16, 32, 64, 128, 250, 475, 860]
    dr_ads1015 = [128, 250, 490, 920, 1600, 2400, 3300, 3300]
    swp = 'SWAPPED'
    expected = mock_register('CONVERSION', swap_dict[swp], idx) * pga / 32767
    pig = iodev.PigpioConnection()
    monkeypatch.setattr(
        pig,
        "i2c_read_i2c_block_data",
        mock_i2c_read_i2c_block_data(swp, idx)
    )
    ads = ads1x15(pig=pig)
    if isinstance(ads, iodev.ADS1015):
        dr = dr_ads1015[dr_idx]
    else:
        dr = dr_ads1115[dr_idx]
    kwargs = {"MUX": mux, "PGA": pga, "MODE": mode, "DR": dr}
    expected_word = iodev.native16_to_be(ads._config.pack(ads.cfg, **kwargs))
    monkeypatch.setattr(
        ads._pig,
        "i2c_write_i2c_block_data",
        mock_i2c_write_i2c_block_data(swap_dict[swp], idx, expected_word)
    )
    result = ads.read_conversion(**kwargs)
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize(
    "ads1x15, kwargs", [
        (iodev.ADS1115, {"MUX": 0, "PGA": 4.096, "MODE": 'SINGLE', "DR": 8}),
        (iodev.ADS1015, {"MUX": 0, "PGA": 4.096, "MODE": 'SINGLE', "DR": 128})
    ]
)
def test_config(mock_pigpio_i2c, kwargs, ads1x15, monkeypatch):
    """__________________________________________________________________________________________________________TEST #2
    Tests the OrderedDict
        - Patches pigpio.pi to mock read 0x8583 from the 'CONFIG' register
        - Initializes an ADS1x15 as ads
        - Asserts that ads.config is a Register instance
        - Asserts that ads.config.MUX.info() returns a tuple matching expected mux offset, mask, and possible values
    """
    expected = [12, 0x07, OrderedDict({
        (0, 1): 0,
        (0, 3): 1,
        (1, 3): 2,
        (2, 3): 3,
        0: 4,
        1: 5,
        2: 6,
        3: 7
    })]
    pig = iodev.PigpioConnection()
    monkeypatch.setattr(
        pig,
        "i2c_read_i2c_block_data",
        mock_i2c_read_i2c_block_data('SWAPPED', 1)
    )
    ads = ads1x15(pig=pig)
    assert isinstance(ads.config, iodev.I2CDevice.Register)
    result = ads.config.MUX.info()
    assert result == expected
    """__________________________________________________________________________________________________________
    """
'''