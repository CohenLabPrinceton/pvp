from .pigpio_mocks import patch_pigpio_base, patch_pigpio_gpio, soft_frequencies
from vent.io.devices.valves import OnOffValve, PWMControlValve, SimOnOffValve, SimControlValve
from secrets import token_bytes

import pytest
import random


@pytest.mark.parametrize("gpio", random.sample(range(31), 16))
@pytest.mark.parametrize("form", ['Normally Closed', 'Normally Open'])
def test_form(patch_pigpio_gpio, gpio, form):
    """__________________________________________________________________________________________________________TEST #1
     Tests the set/get interface of SolenoidBase/children
         - Initializes an OnOffValve
         - Sets a form
         - asserts form is set to expected form
    """
    valve = OnOffValve(gpio)
    valve.form = form
    assert valve.form == form
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("gpio", random.sample(range(31), 16))
@pytest.mark.parametrize("form", ['Normally Closed', 'Normally Open'])
def test_on_off_valve(patch_pigpio_gpio, gpio, form):
    """__________________________________________________________________________________________________________TEST #2
     Tests the open/close interface of an OnOffValve
         - Initializes an OnOffValve
         - records is_open
         - Opens the valve, records is_open
         - Closes the valve, records is_open
         - Asserts that the valve follows the pattern of a cycled valve with the set form
    """
    NC = 'Normally Closed'
    with pytest.raises(ValueError):
        OnOffValve(gpio, form='Not A Real Form')
    valve = OnOffValve(gpio, form)
    assert not valve.is_open if form == NC else valve.is_open
    valve.open()
    assert valve.is_open
    valve.close()
    assert not valve.is_open
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("seed", [token_bytes(8) for _ in range(31)])
def test_pwm_control_valve(patch_pigpio_gpio, seed):
    """__________________________________________________________________________________________________________TEST #3
     Tests the open/close interface of an PWMControlValve. This should mimic the behavior of an OnOffValve, but uses a
        different backend.
         - Tests that an exception is raised if an attempt is made to initialize w/o a response curve
         - Initializes a PWMControlValve
         - Checks proper functioning of open()/close() commands
         - Checks that valve.setpoint = 100 -> sets the highest duty of the 'rising' == True column of the response file
            - And that valve.is_open works
         - Checks that valve.setpoint = 1 -> sets the lowest duty from the 'rising' == False column of the response file
            - And that valve.is_open still reports that the valve is open
        - Checks that valve.setpoint = 0 -> valve.duty = 0 & valve.is_open reports false
    """
    random.seed(seed)
    gpio = random.choice(PWMControlValve._HARDWARE_PWM_PINS)
    form = 'Normally Closed'
    '''with pytest.raises(NotImplementedError):
        PWMControlValve(gpio, form)'''
    with pytest.raises(NotImplementedError):
        PWMControlValve(gpio, 'Normally Open')
    if random.getrandbits(1):
        valve = PWMControlValve(gpio, form)
    else:
        valve = PWMControlValve(gpio, form, response="vent/io/config/calibration/SMC_PVQ31_5G_23_01N_response")
    # Using standard On/Off commands:
    assert not valve.is_open
    valve.open()
    assert valve.is_open
    valve.close()
    assert not valve.is_open
    # Using setpoint:
    valve.setpoint = 100
    assert valve.is_open
    assert round(valve.duty, 4) == valve._response_array[:, 1].max()
    valve.setpoint = 1
    assert valve.is_open
    assert round(valve.duty, 4) == valve._response_array[valve._response_array[:, 2].nonzero(), 2].min()
    valve.setpoint = 0
    assert not valve.is_open
    assert valve.duty == 0
    with pytest.raises(ValueError):
        valve.setpoint = 101
    with pytest.raises(ValueError):
        valve.setpoint = -1
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("gpio", random.sample(range(31), 16))
@pytest.mark.parametrize("form", ['Normally Closed', 'Normally Open'])
def test_sim_on_off_valve(patch_pigpio_gpio, gpio, form):
    """__________________________________________________________________________________________________________TEST #4
     Tests the open/close interface of an SimOnOffValve
         - Initializes an OnOffValve
         - records is_open
         - Opens the valve, records is_open
         - Closes the valve, records is_open
         - Asserts that the valve follows the pattern of a cycled valve with the set form
    """
    NC = 'Normally Closed'
    valve = SimOnOffValve(gpio, form)
    assert not valve.is_open if form == NC else valve.is_open
    valve.open()
    assert valve.is_open
    valve.close()
    assert not valve.is_open
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("gpio", random.sample(range(31), 16))
def test_sim_control_valve(patch_pigpio_gpio, gpio):
    """__________________________________________________________________________________________________________TEST #5
     Tests SimControlValve in much the same way as PWMControlValve.
    """
    form = 'Normally Closed'
    with pytest.raises(NotImplementedError):
        SimControlValve(gpio, form, response="fake/path/to/file")
    with pytest.raises(NotImplementedError):
        SimControlValve(gpio, 'Normally Open')
    valve = SimControlValve(gpio, form)
    # Using standard On/Off commands:
    assert not valve.is_open
    valve.open()
    assert valve.is_open
    valve.close()
    assert not valve.is_open
    # Using setpoint:
    valve.setpoint = 100
    assert valve.is_open
    valve.setpoint = 1
    assert valve.is_open
    valve.setpoint = 0
    assert not valve.is_open
    with pytest.raises(ValueError):
        valve.setpoint = 101
    with pytest.raises(ValueError):
        valve.setpoint = -1
    """__________________________________________________________________________________________________________
    """