from .pigpio_mocks import patch_pigpio_base, patch_pigpio_i2c, patch_pigpio_gpio, mock_i2c_hardware
from vent.io.devices import ADS1015, ADS1115, PigpioConnection
from vent.io.devices.sensors import Sensor, AnalogSensor, SFM3200, SimSensor
from secrets import token_bytes

import numpy as np
import pytest
import random


def test_sensor():
    """__________________________________________________________________________________________________________TEST #1
    Tests errors are thrown when you try to do stuff with the abstract base class
    """
    with pytest.raises(TypeError):
        s = Sensor()


def test_sim_sensor(patch_pigpio_i2c, mock_i2c_hardware):
    """__________________________________________________________________________________________________________TEST #2
    Tests the proper functioning of a simulated sensor. Not much to this one, really. Also checks that age sends back -1
        when update() has not been called
    """
    sim_sensor = SimSensor()
    assert sim_sensor.age() == -1
    n_iter = random.randint(100, 1000)
    for i in range(n_iter):
        result = sim_sensor.get()
        assert sim_sensor.low <= result <= sim_sensor.high
    sim_sensor.update()
    assert sim_sensor.age() > 0
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("ads1x15", [ADS1115, ADS1015])
@pytest.mark.parametrize("seed", [token_bytes(8) for _ in range(8)])
@pytest.mark.parametrize("pga", random.sample(ADS1115._CONFIG_VALUES[2], 4))
@pytest.mark.parametrize("mode", ['SINGLE', 'CONTINUOUS'])
def test_analog_sensor_single_read(patch_pigpio_i2c, mock_i2c_hardware, ads1x15, seed, pga, mode):
    """__________________________________________________________________________________________________________TEST #3
    Tests the proper functioning of an AnalogSensor with random, but plausible, calibration.

    - Performs a sequence of observations and verifies that each matches expectations and that the age of each reading
        properly reflects called updates
    """
    random.seed(seed)
    kwargs = {
        "MUX": random.choice(ads1x15._CONFIG_VALUES[1]),
        "PGA": pga,
        "MODE": mode,
        "DR": random.choice(ads1x15._CONFIG_VALUES[4]),
        'offset_voltage': round(random.uniform(-0.35, 0.35) * pga, 2),
        'output_span': round(random.uniform(.75, 1.0) * pga, 2),
        'conversion_factor': round(random.choice([-1, 1]) * random.uniform(1, 10), 2)
    }
    mock = mock_i2c_hardware(
        i2c_bus=1,
        i2c_address=ads1x15._DEFAULT_ADDRESS,
        n_registers=4,
        reg_values=[
            b'\x00\x00',
            b'\x85\x83'
        ]
    )
    pig = PigpioConnection()
    pig.add_mock_hardware(mock['device'], mock['i2c_address'], mock['i2c_bus'])
    ads = ads1x15(pig=pig)
    a_sensor = AnalogSensor(ads, **kwargs)
    n_iter = 250
    conversion_bytes = [token_bytes(2) for _ in range(n_iter)]
    raw_voltage = [int.from_bytes(cb, 'big', signed=True) * kwargs['PGA'] / 32767 for cb in conversion_bytes]
    expected = [
        kwargs['conversion_factor'] * (rv - kwargs['offset_voltage']) / kwargs['output_span'] for rv in raw_voltage
    ]
    for i in range(n_iter):
        pig.mock_i2c[1][mock['i2c_address']].write_mock_hardware_register(0, conversion_bytes[i])
        result = a_sensor.get()
        assert round(result, 9) == round(expected[i], 9)
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("ads1x15", [ADS1115, ADS1015])
@pytest.mark.parametrize("seed", [token_bytes(8) for _ in range(8)])
def test_analog_sensor_single_read_drop_kwargs(patch_pigpio_i2c, mock_i2c_hardware, ads1x15, seed):
    """__________________________________________________________________________________________________________TEST #4
    Same as the above test, except it will randomly drop kwargs to check that the default attributes are
        properly filled in and that the read functions normally.
        - Note: calibration values are stored seperately s.t. the later verification of the result can be calculated
         even without the store the default calibration for later conversion.
    """
    random.seed(seed)
    kwargs = {
        "MUX": random.choice(ads1x15._CONFIG_VALUES[1]),
        "PGA": random.choice(ads1x15._CONFIG_VALUES[2]),
        "MODE": random.choice(ads1x15._CONFIG_VALUES[3]),
        "DR": random.choice(ads1x15._CONFIG_VALUES[4]),
        'offset_voltage': 0,
        'output_span': 5,
        'conversion_factor': 10
    }
    kw_copy = kwargs.copy()
    for field in kw_copy:
        if random.getrandbits(1) and field is not "MUX":
            del kwargs[field]
            kw_copy[field] = dict(**ads1x15._DEFAULT_VALUES, **AnalogSensor._DEFAULT_CALIBRATION)[field]

    mock = mock_i2c_hardware(
        i2c_bus=1,
        i2c_address=ads1x15._DEFAULT_ADDRESS,
        n_registers=4,
        reg_values=[
            b'\x00\x00',
            b'\x85\x83'
        ]
    )
    pig = PigpioConnection()
    pig.add_mock_hardware(mock['device'], mock['i2c_address'], mock['i2c_bus'])
    ads = ads1x15(pig=pig)
    a_sensor = AnalogSensor(ads, **kwargs)
    n_iter = 250
    conversion_bytes = [token_bytes(2) for _ in range(n_iter)]
    raw_voltage = [int.from_bytes(cb, 'big', signed=True) * kw_copy['PGA'] / 32767 for cb in conversion_bytes]
    expected = [
        kw_copy['conversion_factor'] * (rv - kw_copy['offset_voltage']) / kw_copy['output_span'] for rv in raw_voltage
    ]
    for i in range(n_iter):
        pig.mock_i2c[1][mock['i2c_address']].write_mock_hardware_register(0, conversion_bytes[i])
        result = a_sensor.get()
        assert round(result, 9) == round(expected[i], 9)
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("ads1x15", [ADS1115, ADS1015])
@pytest.mark.parametrize("seed", [token_bytes(8) for _ in range(8)])
@pytest.mark.parametrize("pga", random.sample(ADS1115._CONFIG_VALUES[2], 4))
@pytest.mark.parametrize("mode", ['SINGLE', 'CONTINUOUS'])
def test_analog_sensor_kwarg_exceptions(patch_pigpio_i2c, mock_i2c_hardware, ads1x15, seed, pga, mode):
    """__________________________________________________________________________________________________________TEST #5
    Tests that an exception is properly raised when either:
        - a kwarg is passed that it unrecognized
        - MUX is not passed in kwargs
    """
    random.seed(seed)
    kwargs = {
        "MUX": random.choice(ads1x15._CONFIG_VALUES[1]),
        "PGA": pga,
        "MODE": mode,
        "DR": random.choice(ads1x15._CONFIG_VALUES[4]),
        'offset_voltage': round(random.uniform(-0.35, 0.35) * pga, 2),
        'output_span': round(random.uniform(.75, 1.0) * pga, 2),
        'conversion_factor': round(random.choice([-1, 1]) * random.uniform(1, 10), 2)
    }
    mock = mock_i2c_hardware(
        i2c_bus=1,
        i2c_address=ads1x15._DEFAULT_ADDRESS,
        n_registers=4,
        reg_values=[
            b'\x00\x00',
            b'\x85\x83'
        ]
    )
    pig = PigpioConnection()
    pig.add_mock_hardware(mock['device'], mock['i2c_address'], mock['i2c_bus'])
    ads = ads1x15(pig=pig)
    with pytest.raises(TypeError):
        bad_kwargs = kwargs.copy()
        bad_kwargs['bad_key'] = 'bad_value'
        AnalogSensor(ads, **bad_kwargs)
    with pytest.raises(TypeError):
        bad_kwargs = kwargs.copy()
        del bad_kwargs['MUX']
        AnalogSensor(ads, **bad_kwargs)
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("ads1x15", [ADS1115, ADS1015])
@pytest.mark.parametrize("seed", [token_bytes(8) for _ in range(32)])
def test_analog_sensor_average_read(patch_pigpio_i2c, mock_i2c_hardware, ads1x15, seed):
    """__________________________________________________________________________________________________________TEST #6
    Performs a several updates before averaging AnalogSensor.data to determine if the result matches expectations
        - Data loaded into the conversion register is gaussian normal about the expected value
    """
    random.seed(seed)
    pga = random.choice(ads1x15._CONFIG_VALUES[2])

    kwargs = {
        "MUX": random.choice(ads1x15._CONFIG_VALUES[1]),
        "PGA": pga,
        "MODE": random.choice(ads1x15._CONFIG_VALUES[3]),
        "DR": random.choice(ads1x15._CONFIG_VALUES[4]),
        'offset_voltage': round(random.uniform(-0.35, 0.35) * pga, 2),
        'output_span': round(random.uniform(.75, 1.0) * pga, 2),
        'conversion_factor': round(random.choice([-1, 1]) * random.uniform(1, 10), 2)
    }

    mock = mock_i2c_hardware(
        i2c_bus=1,
        i2c_address=ads1x15._DEFAULT_ADDRESS,
        n_registers=4,
        reg_values=[b'\x00\x00', b'\x85\x83']
    )

    def voltage(bytes_value):
        val = int.from_bytes(bytes_value, 'big', signed=True)
        result = val*kwargs['PGA'] / 32767
        return result

    def gaussian_bytes(mu):
        def _gauss():
            val = random.gauss(mu, mu/1000)
            result = int(round(val)).to_bytes(2, 'big')
            return result
        return _gauss

    n_iter = 1000
    target = random.randint(1000, 20000)

    pig = PigpioConnection()
    pig.add_mock_hardware(mock['device'], mock['i2c_address'], mock['i2c_bus'])
    ads = ads1x15(pig=pig)
    a_sensor = AnalogSensor(ads, **kwargs)
    a_sensor.maxlen_data = n_iter
    gauss_cannon = gaussian_bytes(target)
    bytes_data = [gauss_cannon() for _ in range(n_iter)]
    avg_voltage = np.mean([voltage(byt) for byt in bytes_data])
    expected_value = kwargs['conversion_factor'] * (avg_voltage - kwargs['offset_voltage']) / kwargs['output_span']

    for i in range(n_iter):
        pig.mock_i2c[1][mock['i2c_address']].write_mock_hardware_register(0, bytes_data[i])
        a_sensor.update()
    data = a_sensor.data
    result_0 = a_sensor.get(average=True)
    result_1 = data[:, 1].mean()
    assert len(data) == n_iter
    assert result_0 - result_1 < 0.1
    assert result_0 - expected_value < 0.1
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("seed", [token_bytes(8) for _ in range(4)])
def test_sfm_single_read(patch_pigpio_i2c, mock_i2c_hardware, seed):
    """__________________________________________________________________________________________________________TEST #7
    Tests the proper functioning of an SFM sensor. similar to single read of analog sensor, except starts with 4 bytes
        in the register and discards two (just like in real life)
    """
    random.seed(seed)
    mock = mock_i2c_hardware(
        i2c_bus=1,
        i2c_address=SFM3200._DEFAULT_ADDRESS,
        reg_values=[b'\x00\x00']
    )
    pig = PigpioConnection()
    pig.add_mock_hardware(mock['device'], mock['i2c_address'], mock['i2c_bus'])
    sfm = SFM3200(address=mock['i2c_address'], i2c_bus=mock['i2c_bus'], pig=pig)

    n_iter = random.randint(100, 1000)
    conversion_bytes = [token_bytes(4) for _ in range(n_iter)]
    raw_int = [int.from_bytes(cb[:2], 'big') for cb in conversion_bytes]
    expected = [(rv - sfm._FLOW_OFFSET) / sfm._FLOW_SCALE_FACTOR for rv in raw_int]
    for i in range(n_iter):
        pig.mock_i2c[1][mock['i2c_address']].write_mock_hardware_register(0, conversion_bytes[i])
        result = sfm.get()
        assert round(result, 10) == round(expected[i], 10)
    """__________________________________________________________________________________________________________
    """