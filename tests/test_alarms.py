import pytest

import pdb

import numpy as np

from vent.alarm import condition

from vent.common.values import ValueName, SENSOR
from vent.common.message import SensorValues

##########
# conditions

n_samples = 100


@pytest.fixture
def fake_sensors():
    def _fake_sensor(arg=None):
        # make an empty SensorValues
        vals = {k:0 for k in ValueName}
        vals.update({k:0 for k in SensorValues.additional_values})

        # update with any in kwargs
        if arg:
            for k, v in arg.items():
                vals[k] = v

        sensors = SensorValues(vals=vals)

        return sensors
    return _fake_sensor


@pytest.mark.parametrize("test_value", [k for k in SENSOR.keys()])
def test_valuecondition(fake_sensors, test_value):


    for i in range(n_samples):
        # test min
        test_val = (np.random.rand()-0.5)*100
        min_cond = condition.ValueCondition(test_value, test_val, 'min')

        min_no_alarms = fake_sensors({test_value: test_val+1})
        min_yes_alarms = fake_sensors({test_value: test_val - 1})

        assert min_cond.check(min_no_alarms) == False
        assert min_cond.check(min_yes_alarms) == True

        # test max
        max_cond = condition.ValueCondition(test_value, test_val, 'max')

        max_no_alarms = fake_sensors({test_value: test_val - 1})
        max_yes_alarms = fake_sensors({test_value: test_val + 1})

        assert max_cond.check(max_no_alarms) == False
        assert max_cond.check(max_yes_alarms) == True

        # test that the @mode.setter works for already created objects
        min_cond.mode = 'max'
        max_cond.mode = 'min'

        assert min_cond.check(max_no_alarms) == False
        assert min_cond.check(max_yes_alarms) == True
        assert max_cond.check(min_no_alarms) == False
        assert max_cond.check(min_yes_alarms) == True

    # test that other values don't do anything
    other_cond = condition.ValueCondition(test_value, 1, 'max')

    for value in ValueName:
        other_sensor = fake_sensors({value: 2})
        assert other_sensor[value] == 2

        if value == test_value:
            assert other_cond.check(other_sensor) == True
        else:
            assert other_cond.check(other_sensor) == False

@pytest.mark.parametrize("test_value", [k for k in SENSOR.keys()])
def test_cyclevaluecondition(fake_sensors, test_value):

    for i in range(n_samples):
        n_cycles = np.random.randint(1, 100)

        cond = condition.CycleValueCondition(
            value_name=test_value,
            limit=1,
            minmax='max',
            n_cycles=n_cycles
        )

        sensors = fake_sensors()

        # test that just checking alone without incrementing cycle doesn't trigger
        sensors[test_value] = 2

        for j in range(n_cycles * 2):
            assert cond.check(sensors) == False

        # test the straightforward case, goes out of range and stays out of range
        for j in range(n_cycles * 2):
            sensors.breath_count = j
            if j < n_cycles:
                assert cond.check(sensors) == False
            else:
                assert cond.check(sensors) == True

        # test that going under the limit resets the cycle count check
        sensors[test_value] = 0
        sensors.breath_count += 1
        assert cond.check(sensors) == False
        sensors[test_value] = 2
        sensors.breath_count += 1
        assert cond.check(sensors) == False

    # test discontinuous breath cycles
    # test that discontinuous checks without conflicting info still trigger
    cond = condition.CycleValueCondition(
            value_name=test_value,
            limit=1,
            minmax='max',
            n_cycles=10
        )
    sensors = fake_sensors()
    sensors[test_value] = 2

    assert cond.check(sensors) == False
    sensors.breath_count = 11
    assert cond.check(sensors) == True

    # but that discontinuous checks with conflicting info dont trigger
    cond = condition.CycleValueCondition(
        value_name=test_value,
        limit=1,
        minmax='max',
        n_cycles=10
    )
    sensors = fake_sensors()
    sensors[test_value] = 2

    assert cond.check(sensors) == False
    sensors.breath_count = 5
    sensors[test_value] = 0
    assert cond.check(sensors) == False
    sensors.breath_count = 11
    sensors[test_value] = 2
    assert cond.check(sensors) == False

