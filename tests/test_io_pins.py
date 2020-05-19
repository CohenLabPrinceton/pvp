from .pigpio_mocks import *
from vent.io.devices.pins import PWMOutput


@pytest.mark.parametrize("seed", [secrets.token_bytes(8) for _ in range(16)])
@pytest.mark.parametrize("gpio", random.sample(range(53), 4))
def test_mode(patch_pigpio_gpio, seed, gpio):
    """______________________________________________________________________________________________________Pin_TEST #1
     Tests the mode setting & getting methods of Pin
         - Initializes a Pin
         - Reads mode off pin (should be random)
         - Writes a mode to Pin
         - Reads the mode back from the Pin
         - Asserts that the first (random) mode read is a valid mode
         - Asserts that the second mode is the mode we set
    """
    random.seed(seed)
    if random.getrandbits(3) == 7:
        mode = 'Fake Mode'
    else:
        mode = random.choice([key for key in Pin._PIGPIO_MODES.keys()])

    results = []
    pin = Pin(gpio)
    results.append(pin.mode)
    if mode == 'Fake Mode':
        with pytest.raises(ValueError):
            pin.mode = mode
    else:
        pin.mode = mode
        results.append(pin.mode)
        assert results[1] == mode
    assert results[0] in Pin._PIGPIO_MODES

    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("gpio", random.sample(range(31), 10))
@pytest.mark.parametrize("level", [0, 1])
def test_read_write_toggle(patch_pigpio_gpio, gpio, level):
    """______________________________________________________________________________________________________Pin_TEST #2
     Tests the toggle feature of a Pin
         - Initializes a random Pin (in User_GPIO)
         - Sets mode to 'OUTPUT'
         - Writes a random level to Pin
         - Reads the pin and stores in results
         - Writes the level to Pin again
         - Toggles the Pin
         - Reads the Pin and stores in results
         - Asserts that the result is [level, not level]
         - Checks that an exception is thrown if you try to write a bad value
    """
    results = []
    pin = Pin(gpio)
    pin.mode = 'OUTPUT'
    pin.write(level)
    results.append(pin.read())
    pin.write(level)
    pin.toggle()
    results.append(pin.read())
    assert sum(results) == 1
    assert results[0] is not results[1]
    with pytest.raises(ValueError):
        pin.write(-1)
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("seed", [secrets.token_bytes(8) for _ in range(16)])
def test_frequency(patch_pigpio_gpio, seed):
    """________________________________________________________________________________________________PWMOutput_TEST #1
     Tests the frequency setter & getter properties, and checks that duty is not changed or something weird like that
         - Initializes a PWMOutput
         - Sets frequency
         - reads frequency and appends to results
         - reads duty and appends to results
         - set up a condition that should never happen and check that the driver recovers (lie: hardware_enabled = True)
    """
    random.seed(seed)
    gpio = random.choice(range(31))
    offspec = False
    if gpio not in PWMOutput._HARDWARE_PWM_PINS:
        if random.getrandbits(3) == 7:
            frequency = random.choice(soft_frequencies)
        else:
            frequency = random.randint(1, 10000)
            offspec = True
    else:
        frequency = random.randint(1, 20000000)
    results = []
    pin = PWMOutput(gpio)
    if offspec:
        with pytest.raises(RuntimeWarning):
            pin.frequency = frequency
    else:
        pin.frequency = frequency
        results.append(pin.frequency)
        results.append(pin.read())
        assert results[0] == frequency
        assert results[1] == 0
    if not pin.hardware_enabled:
        with pytest.raises(Exception):
            pin._hardware_enabled = True
            pin.frequency = 20000
    """__________________________________________________________________________________________________________
    """


@pytest.mark.parametrize("gpio", [1, 12, 14, 19])
@pytest.mark.parametrize("duty", [x/10 for x in range(11)])
def test_duty(patch_pigpio_gpio, gpio, duty):
    """________________________________________________________________________________________________PWMOutput_TEST #2
     Tests the duty setter & getter properties (and synonym write())
         - Initializes a PWMOutput
         - Reads frequency and appends to results
         - Writes duty
         - Reads duty and appends to results
         - Reads freqency and appends to results
         - Asserts frequency was not changed
         - Asserts duty read from pin matches input
    """
    results = []
    pin = PWMOutput(gpio)
    results.append(pin.frequency)
    pin.write(duty)
    results.append(pin.duty)
    results.append(pin.frequency)
    assert results[0] == results[2]
    assert round(results[1], 2) == duty
    with pytest.raises(ValueError):
        pin.duty = -1
    """__________________________________________________________________________________________________________
    """


