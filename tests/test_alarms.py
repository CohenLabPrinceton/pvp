import pytest

import pdb
import time
import copy

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

        # since 0 is out of range for fio2, manually set it
        # FIXME: find values that by definition don't raise any of the default rules
        vals[ValueName.FIO2] = 80

        # update with any in kwargs
        if arg:
            for k, v in arg.items():
                vals[k] = v

        sensors = SensorValues(vals=vals)

        return sensors
    return _fake_sensor

@pytest.fixture
def fake_rule():
    def _fake_rule(alarm_type = AlarmType.HIGH_PRESSURE,
                   latch = False,
                   persistent = False,
                   conditions = None):

        if not conditions:
            conditions = (
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
                    )
                ),
                (
                    AlarmSeverity.HIGH,
                    condition.ValueCondition(
                        value_name=ValueName.PRESSURE,
                        limit=3,
                        mode='max'
                    )
                )
            )
        rule = Alarm_Rule(
            name=alarm_type,
            latch=latch,
            persistent=persistent,
            conditions=conditions
        )

        return rule

    return _fake_rule

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
        if value == test_value:
            other_sensor = fake_sensors({value: 2})
        else:
            other_sensor = fake_sensors({value: 2, test_value: 0})

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
    """
    Test that the alarm manager raises a single alarm

    Args:
        fake_sensors:

    Returns:

    """

    manager = Alarm_Manager()
    manager.reset()
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
    sensor = fake_sensors()

    manager.update(sensor)
    assert len(manager.active_alarms) == 0
    assert alarms_emitted == 0

    sensor.PRESSURE = ALARM_RULES[AlarmType.HIGH_PRESSURE].conditions[0][1].limit + 1
    manager.update(sensor)
    assert AlarmType.HIGH_PRESSURE in manager.active_alarms.keys()
    assert alarms_emitted == 1

def test_alarm_manager_escalation(fake_sensors, fake_rule):
    """
    For unlatched alarms, test that alarms are:

    * emitted when alarm severity is raised
    * decremented when alarm severity is decreased and alarm is not latched
    * deactivated and deleted
    """

    manager = Alarm_Manager()
    manager.reset()

    assert len(manager.active_alarms) == 0

    #
    # create alarm rule for testing
    rule = fake_rule(latch=False, persistent=False)
    manager.load_rule(rule)

    assert manager.rules[rule.name] is rule

    # callback to catch emitted alarms
    global caught_alarm
    caught_alarm = None

    def catch_alarm(alarm):
        global caught_alarm
        caught_alarm = alarm

    manager.add_callback(catch_alarm)

    # raise and see that we get a new alarm
    sensors = fake_sensors()
    sensors.PRESSURE = 1.5

    manager.update(sensors)

    assert isinstance(caught_alarm, Alarm)
    assert caught_alarm.severity == AlarmSeverity.LOW
    assert manager.active_alarms[rule.name] is caught_alarm

    # raise to medium
    sensors.PRESSURE = 2.5
    manager.update(sensors)
    assert caught_alarm.severity == AlarmSeverity.MEDIUM
    assert manager.active_alarms[rule.name] is caught_alarm

    # then high
    sensors.PRESSURE = 3.5
    manager.update(sensors)
    assert caught_alarm.severity == AlarmSeverity.HIGH
    assert manager.active_alarms[rule.name] is caught_alarm

    # now decrement
    sensors.PRESSURE = 2.5
    manager.update(sensors)
    assert caught_alarm.severity == AlarmSeverity.MEDIUM
    assert manager.active_alarms[rule.name] is caught_alarm

    sensors.PRESSURE = 1.5
    manager.update(sensors)
    assert caught_alarm.severity == AlarmSeverity.LOW
    assert manager.active_alarms[rule.name] is caught_alarm

    # when alarm is brought back into safe range, should be deleted from active_alarms
    sensors.PRESSURE = 0.5
    manager.update(sensors)
    assert caught_alarm.severity == AlarmSeverity.OFF
    assert rule.name not in manager.active_alarms.keys()
    assert len(manager.active_alarms) == 0



def test_alarm_manager_latch(fake_sensors, fake_rule):
    """
    * not decremented when alarm severity is decreased and alarm is latched
    * dismissed when latched *only when* alarm condition is OFF AND has been dismissed

    Args:
        fake_sensors:
        fake_rule:

    Returns:

    """

    manager = Alarm_Manager()
    manager.reset()

    assert len(manager.active_alarms) == 0

    # create alarm rule for testing
    rule = fake_rule(latch=True, persistent=False)
    manager.load_rule(rule)
    assert manager.rules[rule.name] is rule

    # callback to catch emitted alarms
    global caught_alarm
    global n_alarms
    n_alarms = 0
    caught_alarm = None

    def catch_alarm(alarm):
        global caught_alarm
        global n_alarms
        caught_alarm = alarm
        n_alarms += 1

    manager.add_callback(catch_alarm)

    # raise and see that we get a new alarm
    sensors = fake_sensors()

    # raise alarm to HIGH
    sensors.PRESSURE = 3.5
    manager.update(sensors)

    assert isinstance(caught_alarm, Alarm)
    assert caught_alarm.severity == AlarmSeverity.HIGH
    assert manager.active_alarms[rule.name] is caught_alarm
    assert n_alarms == 1

    # raise alarm range to OFF, but don't request dismiss
    sensors.PRESSURE = 0.5
    manager.update(sensors)

    # no alarm should have been emitted
    assert caught_alarm.severity == AlarmSeverity.HIGH
    assert manager.active_alarms[rule.name] is caught_alarm
    assert n_alarms == 1

    # raise back to HIGH
    sensors.PRESSURE = 3.5
    manager.update(sensors)

    # dismiss but only drop to MEDIUM, so alarm should not be emitted
    manager.dismiss_alarm(rule.name)

    assert rule.name in manager.pending_clears

    sensors.PRESSURE = 2.5
    manager.update(sensors)

    assert caught_alarm.severity == AlarmSeverity.HIGH
    assert manager.active_alarms[rule.name] is caught_alarm
    assert n_alarms == 1

    # dropping to OFF should finally clear the alarm
    sensors.PRESSURE = 0.5
    manager.update(sensors)

    assert caught_alarm.severity == AlarmSeverity.OFF
    assert rule.name not in manager.active_alarms.keys()
    assert len(manager.active_alarms) == 0
    assert len(manager.pending_clears) == 0
    assert n_alarms == 2


def test_alarm_manager_dismiss(fake_sensors, fake_rule):
    """
    * dismissed when not latched until alarm conditions return to off then back on
    * dismissed when not latched until duration regardless of alarm condition

    Args:
        fake_sensors:
        fake_rule:

    Returns:

    """
    manager = Alarm_Manager()
    manager.reset()

    assert len(manager.active_alarms) == 0

    # create alarm rule for testing
    rule = fake_rule(latch=False, persistent=False)
    manager.load_rule(rule)
    assert manager.rules[rule.name] is rule

    # callback to catch emitted alarms
    global caught_alarm
    global n_alarms
    n_alarms = 0
    caught_alarm = None

    def catch_alarm(alarm):
        global caught_alarm
        global n_alarms
        caught_alarm = alarm
        n_alarms += 1

    manager.add_callback(catch_alarm)

    # raise and see that we get a new alarm
    sensors = fake_sensors()
    sensors.PRESSURE = 3.5
    manager.update(sensors)

    assert isinstance(caught_alarm, Alarm)
    assert caught_alarm.severity == AlarmSeverity.HIGH
    assert n_alarms == 1

    # dismiss the alarm, make sure it's gone
    manager.dismiss_alarm(rule.name)
    assert rule.name in manager.cleared_alarms
    assert caught_alarm.severity == AlarmSeverity.OFF
    assert n_alarms == 2

    # update with same sensor values, make sure alarm isn't emitted
    manager.update(sensors)
    assert caught_alarm.severity == AlarmSeverity.OFF
    assert n_alarms == 2

    # take down to OFF range and back up, should get alarm
    sensors.PRESSURE = 0.5
    manager.update(sensors)

    assert rule.name not in manager.cleared_alarms
    assert n_alarms == 2

    sensors.PRESSURE = 3.5
    manager.update(sensors)

    assert caught_alarm.severity == AlarmSeverity.HIGH
    assert n_alarms == 3

    #####################
    # test timed dismissal
    dismiss_time = 2
    manager.dismiss_alarm(rule.name, duration = dismiss_time)

    assert rule.name in manager.snoozed_alarms.keys()
    assert caught_alarm.severity == AlarmSeverity.OFF
    assert n_alarms ==4

    # stash snooze time to check we're not going over
    snooze_time = manager.snoozed_alarms[rule.name]
    # make sure it's not some crazy value
    assert snooze_time <= time.time() + dismiss_time

    # give flip off and on again, check that alarm is not emitted
    # as would be typical
    sensors.PRESSURE = 0.5
    manager.update(sensors)
    sensors.PRESSURE = 3.5
    manager.update(sensors)

    assert caught_alarm.severity == AlarmSeverity.OFF
    assert n_alarms == 4
    assert time.time() < snooze_time

    while time.time() < snooze_time:
        manager.update(sensors)
        assert caught_alarm.severity == AlarmSeverity.OFF
        assert n_alarms == 4
        time.sleep(0.1)

    # now that time has passed, should get an alarm
    assert time.time() > snooze_time
    manager.update(sensors)
    assert caught_alarm.severity == AlarmSeverity.HIGH
    assert n_alarms == 5


def test_alarm_manager_logged_alarms(fake_sensors, fake_rule):
    manager = Alarm_Manager()
    manager.reset()

    assert len(manager.active_alarms) == 0

    # create alarm rule for testing
    rule = fake_rule(latch=False, persistent=False)
    manager.load_rule(rule)
    assert manager.rules[rule.name] is rule

    # callback to catch emitted alarms
    global caught_alarm
    global n_alarms
    n_alarms = 0
    caught_alarm = None

    def catch_alarm(alarm):
        global caught_alarm
        global n_alarms
        caught_alarm = alarm
        n_alarms += 1

    manager.add_callback(catch_alarm)

    # raise and see that we get a new alarm
    sensors = fake_sensors()

    # raise alarm, catch it, turn alarm off, check that it's put in logged_alarms
    sensors.PRESSURE = 3.5
    manager.update(sensors)
    assert isinstance(caught_alarm, Alarm)
    assert caught_alarm.severity == AlarmSeverity.HIGH

    high_alarm = caught_alarm

    sensors.PRESSURE = 0.5
    manager.update(sensors)
    assert high_alarm in manager.logged_alarms
    assert high_alarm not in manager.active_alarms.values()



