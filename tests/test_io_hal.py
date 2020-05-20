from .pigpio_mocks import patch_pigpio_base
from vent.io import Hal
from random import randint, getrandbits


def test_functions(patch_pigpio_base):
    """__________________________________________________________________________________________________________TEST #1
        Using simulated sensors, tests that hal initializes correctly, that sensors can be read, and that all valves
            can be open, closed, and/or controlled using the setpoint properties of Hal.
            - Checks to make sure that valves report as being open if they are not fully closed (i.e. if they have a
                nonzero setpoint)
    """
    hal = Hal(config_file='vent/io/config/sim-devices.ini')
    for _ in range(randint(1000, 10000)):
        assert hal._pressure_sensor.low <= hal.pressure <= hal._pressure_sensor.high
        assert hal._aux_pressure_sensor.low <= hal.aux_pressure <= hal._aux_pressure_sensor.high
        assert hal._flow_sensor_in.low <= hal.flow_in <= hal._flow_sensor_in.high
        assert hal._flow_sensor_ex.low <= hal.flow_ex <= hal._flow_sensor_ex.high
        setpoint_in = randint(0, 100)
        hal.setpoint_in = setpoint_in
        assert hal.setpoint_in == setpoint_in
        if hal.setpoint_in == 0:
            assert not hal._inlet_valve.is_open
        else:
            assert hal._inlet_valve.is_open
        setpoint_ex = getrandbits(1)
        hal.setpoint_ex = setpoint_ex
        assert hal.setpoint_ex == setpoint_ex
        if hal.setpoint_ex == 0:
            assert not hal._expiratory_valve.is_open
        else:
            assert hal._expiratory_valve.is_open
