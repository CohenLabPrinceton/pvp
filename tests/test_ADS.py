import vent.io.devices as iodev
from .pigpio_mocks import *


@pytest.mark.parametrize("idx", [0, 1])
@pytest.mark.parametrize("mux", [(0, 1), (0, 3), (1, 3), (2, 3), 0, 1, 2, 3])
@pytest.mark.parametrize("pga", [6.144, 4.096, 2.048, 1.024, 0.512, 0.256, 0.256, 0.256])
@pytest.mark.parametrize("mode", ['CONTINUOUS', 'SINGLE'])
@pytest.mark.parametrize("dr_idx", [0, 1, 2, 3, 4, 5, 6, 7])
@pytest.mark.parametrize("ads1x15", [iodev.ADS1115, iodev.ADS1015])
def test_read_conversion(mock_pigpio_i2c_base, idx, mux, pga, mode, dr_idx, ads1x15, monkeypatch):
    """__________________________________________________________________________________________________________TEST #1
    Tests all of the possible (valid) parameter combinations on both the ADS1115 & ADS1x115

        - Patches pigpio.pi with the read method used by ads.__init__
        - Initializes an ADS1x15
        - Patches ads._pig with write method used by read_conversion & Co
        - Calls read_conversion(kwargs), where kwargs is parameterized
            - Builds the expected bytes to be written to the config registry and intercepts them in when
                pigpio.pi.i2c_write_i2c_block_data is called
        - Asserts that the result matches what is expected

    Mocks:
        - function: socket.create_connection()  -> mock_create_connection
            -class:     socket.Socket               -> MockSocket
        - class:    pigpio._socklock            -> MockSockLock
        - class:    pigpio._callback_thread     -> MockThread
        - function: pigpio._pigpio_command      -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open          -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close         -> mock_pigpio_i2c_close
        + method:   pigpio.pi.i2c_write_i2c_block_data  -> mock_i2c_write_device
        + method:   pigpio.pi.i2c_read_i2c_block_data   -> mock_i2c_read_i2c_block_data
    """
    # TODO [code]

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
    print('\n read_conversion returned: {}, expected: {} '.format(result, expected))
    """__________________________________________________________________________________________________________
    """


#def test_print_config():
    """__________________________________________________________________________________________________________TEST #2
    Tests #TODO[stuff]
        - #TODO[creates what]
        - #TODO[does what]
        - #TODO[asserts what]

    Mocks:
        - function: socket.create_connection()  -> mock_create_connection
            -class:     socket.Socket               -> MockSocket
        - class:    pigpio._socklock            -> MockSockLock
        - class:    pigpio._callback_thread     -> MockThread
        - function: pigpio._pigpio_command      -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open          -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close         -> mock_pigpio_i2c_close
        + #TODO[anything else?]
    """
    # TODO [code]
    """__________________________________________________________________________________________________________
    """


#def test_config():
    """__________________________________________________________________________________________________________TEST #3
    Tests #TODO[stuff]
        - #TODO[creates what]
        - #TODO[does what]
        - #TODO[asserts what]

    Mocks:
        - function: socket.create_connection()  -> mock_create_connection
            -class:     socket.Socket               -> MockSocket
        - class:    pigpio._socklock            -> MockSockLock
        - class:    pigpio._callback_thread     -> MockThread
        - function: pigpio._pigpio_command      -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open          -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close         -> mock_pigpio_i2c_close
        + #TODO[anything else?]
    """
    # TODO [code]
    """__________________________________________________________________________________________________________
    """


#def test_cfg():
    """__________________________________________________________________________________________________________TEST #4
    Tests #TODO[stuff]
        - #TODO[creates what]
        - #TODO[does what]
        - #TODO[asserts what]

    Mocks:
        - function: socket.create_connection()  -> mock_create_connection
            -class:     socket.Socket               -> MockSocket
        - class:    pigpio._socklock            -> MockSockLock
        - class:    pigpio._callback_thread     -> MockThread
        - function: pigpio._pigpio_command      -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open          -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close         -> mock_pigpio_i2c_close
        + #TODO[anything else?]
    """
    # TODO [code]
    """__________________________________________________________________________________________________________
    """


#def test__read_conversion():
    """__________________________________________________________________________________________________________TEST #5
    Tests #TODO[stuff]
        - #TODO[creates what]
        - #TODO[does what]
        - #TODO[asserts what]

    Mocks:
        - function: socket.create_connection()  -> mock_create_connection
            -class:     socket.Socket               -> MockSocket
        - class:    pigpio._socklock            -> MockSockLock
        - class:    pigpio._callback_thread     -> MockThread
        - function: pigpio._pigpio_command      -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open          -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close         -> mock_pigpio_i2c_close
        + #TODO[anything else?]
    """
    # TODO [code]
    """__________________________________________________________________________________________________________
    """


#def test__read_last_cfg():
    """__________________________________________________________________________________________________________TEST #6
    Tests #TODO[stuff]
        - #TODO[creates what]
        - #TODO[does what]
        - #TODO[asserts what]

    Mocks:
        - function: socket.create_connection()  -> mock_create_connection
            -class:     socket.Socket               -> MockSocket
        - class:    pigpio._socklock            -> MockSockLock
        - class:    pigpio._callback_thread     -> MockThread
        - function: pigpio._pigpio_command      -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open          -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close         -> mock_pigpio_i2c_close
        + #TODO[anything else?]
    """
    # TODO [code]
    """__________________________________________________________________________________________________________
    """


#def test__ready():
    """__________________________________________________________________________________________________________TEST #7
    Tests #TODO[stuff]
        - #TODO[creates what]
        - #TODO[does what]
        - #TODO[asserts what]

    Mocks:
        - function: socket.create_connection()  -> mock_create_connection
            -class:     socket.Socket               -> MockSocket
        - class:    pigpio._socklock            -> MockSockLock
        - class:    pigpio._callback_thread     -> MockThread
        - function: pigpio._pigpio_command      -> mock_pigpio_command
        - method:   pigpio.pi.i2c_open          -> mock_pigpio_i2c_open
        - method:   pigpio.pi.i2c_close         -> mock_pigpio_i2c_close
        + #TODO[anything else?]
    """
    # TODO [code]
    """__________________________________________________________________________________________________________
    """
