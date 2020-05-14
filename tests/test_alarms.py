import pytest

import pdb
import time

import numpy as np

from vent.alarm import condition, ALARM_RULES, AlarmType, AlarmSeverity, Alarm, Alarm_Manager
from vent.alarm.rule import Alarm_Rule

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

#############################
# conditions

@pytest.mark.parametrize("test_value", [k for k in SENSOR.keys()])
def test_value_condition(fake_sensors, test_value):


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
def test_cyclevalue_condition(fake_sensors, test_value):

    for i in range(n_samples):
        n_cycles = np.random.randint(1, 100)

        cond = condition.CycleValueCondition(
            value_name=test_value,
            limit=1,
            mode='max',
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
            mode='max',
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
        mode='max',
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

def test_alarmseverity_condition():
    # FIXME
    pass

def test_cyclealarmseverity_condition():
    # FIXME
    pass

def test_condition_addition():
    # FIXME
    pass

def test_condition_dependency():
    # FIXME
    pass


###############################

# rules
#@pytest.mark.parametrize("alarm_rule", [k for k in ALARM_RULES.values()])
def test_alarm_rule(fake_sensors):
    """
    test the alarm rule class itself

    assume the individual conditions have been tested
    """

    rule = Alarm_Rule(
        name=AlarmType.HIGH_PRESSURE,
        latch=False,
        persistent=False,
        conditions=(
            (
                AlarmSeverity.LOW,
                condition.ValueCondition(
                    value_name=ValueName.PRESSURE,
                    limit=1,
                    mode='max',
                )
            ),
            (
                AlarmSeverity.MEDIUM,
                condition.ValueCondition(
                    value_name=ValueName.PRESSURE,
                    limit=2,
                    mode='max'
                ) + \
                condition.CycleAlarmSeverityCondition(
                    alarm_type = AlarmType.HIGH_PRESSURE,
                    severity   = AlarmSeverity.LOW,
                    n_cycles = 2
                )
            ),
            (
                AlarmSeverity.HIGH,
                condition.ValueCondition(
                    value_name=ValueName.PRESSURE,
                    limit=3,
                    mode='max'
                ) + \
                condition.CycleAlarmSeverityCondition(
                    alarm_type = AlarmType.HIGH_PRESSURE,
                    severity   = AlarmSeverity.MEDIUM,
                    n_cycles = 2
                )
            ),
        )
    )

    sensors = fake_sensors()

    # test that initial check is off
    assert rule.check(sensors) == AlarmSeverity.OFF

    # test low severity alarm
    sensors.PRESSURE = 1.5
    sensors.breath_count += 1

    assert rule.check(sensors) == AlarmSeverity.LOW

    # register alarm manually
    # (alarm should call register_alarm)
    low_alarm = Alarm(
        AlarmType.HIGH_PRESSURE,
        AlarmSeverity.LOW,
        latch=False
    )

    # test that we don't jump to medium
    sensors.PRESSURE = 2.5
    sensors.breath_count += 1

    assert rule.check(sensors) == AlarmSeverity.LOW

    # now check that we go to medium
    sensors.breath_count += 2

    assert rule.check(sensors) == AlarmSeverity.MEDIUM

    med_alarm = Alarm(
        AlarmType.HIGH_PRESSURE,
        AlarmSeverity.MEDIUM,
        latch=False
    )

    # keep at medium
    sensors.PRESSURE = 3.5
    sensors.breath_count += 1

    assert rule.check(sensors) == AlarmSeverity.MEDIUM

    sensors.breath_count += 2

    assert rule.check(sensors) == AlarmSeverity.HIGH

def test_rules_individual():
    # test that each individual rule does what we think it does
    # FIXME
    pass


##############################
#
def test_alarm_manager_raise(fake_sensors):

    manager = Alarm_Manager()
    manager.clear_all_alarms()
    assert len(manager.active_alarms) == 0

    # check that we got all the alarm rules
    for alarm_type, rule in ALARM_RULES.items():
        assert alarm_type in manager.rules.keys()

    # make callback to count emitted alarms
    global alarms_emitted
    alarms_emitted = 0
    def alarm_cb(alarm):
        assert isinstance(alarm, Alarm)
        global alarms_emitted
        alarms_emitted += 1

    manager.add_callback(alarm_cb)

    # take a value out of range and test that an alarm is raised an emitted
    sensor = fake_sensors({ValueName.FIO2: 90})

    manager.update(sensor)
    assert len(manager.active_alarms) == 0
    assert alarms_emitted == 0

    sensor.PRESSURE = ALARM_RULES[AlarmType.HIGH_PRESSURE].conditions[0][1].limit + 1
    manager.update(sensor)
    assert AlarmType.HIGH_PRESSURE in manager.active_alarms.keys()
    assert alarms_emitted == 1



