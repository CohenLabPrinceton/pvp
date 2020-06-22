import copy
import time
from pprint import pformat
import pdb

from vent.alarm import AlarmSeverity, AlarmType
from vent.alarm.condition import Condition
from vent.common.message import SensorValues, ControlSetting
from vent.common.loggers import init_logger
from vent.alarm.alarm import Alarm
from vent.alarm.rule import Alarm_Rule
from vent.alarm import condition

import typing

class Alarm_Manager(object):
    """
    Attributes:
        active_alarms (dict): {:class:`.AlarmType`: :class:`.Alarm`}
        pending_clears (list): [:class:`.AlarmType`] list of alarms that have been requested to be cleared
        callbacks (list): list of callables that accept `Alarm` s when they are raised/altered.
        cleared_alarms (list): of :class:`.AlarmType` s, alarms that have been cleared but have not dropped back into the 'off' range to enable re-raising
        snoozed_alarms (dict): of :class:`.AlarmType` s : times, alarms that should not be raised because they have been silenced for a period of time
    """
    _instance = None

    # use class attributes because __init__ is called every time instantiated

    active_alarms: typing.Dict[AlarmType, Alarm] = {}
    logged_alarms: typing.List[Alarm] = []

    # get our alarm rules
    dependencies = {}
    pending_clears = []
    cleared_alarms = []
    snoozed_alarms = {}
    callbacks = []
    depends_callbacks = []
    """
    When we :meth:`.update_dependencies`, we send back a :class:`.ControlSetting` with the new min/max
    """
    rules = {}

    logger = init_logger(__name__)


    def __new__(cls):
        """
        If an Alarm_Manager already exists, when initing just return that one
        """

        if not cls._instance:
            cls._instance = super(Alarm_Manager, cls).__new__(cls)

        return cls._instance


    def __init__(self):

        if len(self.rules) == 0:
            self.load_rules()

    def load_rules(self):
        from vent.alarm import ALARM_RULES
        rules = copy.deepcopy(ALARM_RULES)

        # register dependencies
        for alarm_name, alarm_rule in rules.items():
            self.load_rule(alarm_rule)


    def load_rule(self, alarm_rule: Alarm_Rule):
        self.rules[alarm_rule.name] = alarm_rule

        for severity, condition in alarm_rule.conditions:

            if isinstance(condition.depends, dict):
                self.register_dependency(condition, condition.depends, severity)
            elif isinstance(condition.depends, list) or isinstance(condition.depends, tuple):
                for depend in condition.depends:
                    self.register_dependency(condition, depend, severity)

        self.logger.info(f'Registered rule:\n{pformat(alarm_rule.__dict__)}')



    def update(self, sensor_values: SensorValues):
        for alarm_name, rule in self.rules.items():
            self.check_rule(rule, sensor_values)
            # don't want to do alarm emission here because any _check_,
            # not any full update should trigger an alarm

    def check_rule(self, rule: Alarm_Rule, sensor_values: SensorValues):
        current_severity = rule.check(sensor_values)

        ##################
        # Checks that prevent raising

        # check that we're not being snoozed
        if rule.name in self.snoozed_alarms.keys():
            if time.time() >= self.snoozed_alarms[rule.name]:
                # remove from dict and continue
                del self.snoozed_alarms[rule.name]
            else:
                return

        # if we've been cleared, check if we've gone below zero,
        # otherwise return (don't re-raise)
        if rule.name in self.cleared_alarms:
            if current_severity == AlarmSeverity.OFF:
                self.cleared_alarms.remove(rule.name)
            else:
                return

        #####################
        # checks that determine type of raise

        if rule.name in self.active_alarms.keys():
            # if we've got an active alarm of this type
            # check if the severity has changed
            if current_severity > self.active_alarms[rule.name].severity:
                # greater severity always raises
                self.emit_alarm(rule.name, current_severity)
            elif current_severity < self.active_alarms[rule.name].severity:
                # if alarm isn't latched, emit lower alarm
                if not rule.latch:
                    self.emit_alarm(rule.name, current_severity)
                else:
                    # if the alarm is latched, but has been previously requested to be cleared...
                    if rule.name in self.pending_clears:
                        # clear if the severity is zero
                        if current_severity == AlarmSeverity.OFF:
                            self.emit_alarm(rule.name, current_severity)
                            self.pending_clears.remove(rule.name)
        else:
            # alarm isn't active
            if current_severity > AlarmSeverity.OFF:
                # emit if not off
                self.emit_alarm(rule.name, current_severity)



    def emit_alarm(self, alarm_type: AlarmType, severity: AlarmSeverity):
        """
        Emit alarm (by calling all callbacks with it).

        .. note::

            This method emits *and* clears alarms -- a cleared alarm is emitted with :attr:`AlarmSeverity.OFF`

        Args:
            alarm_type (:class:`.AlarmType`):
            severity (:class:`.AlarmSeverity`):
        """
        if alarm_type in self.rules.keys():
            # if another alarm is currently active, deactivate it
            if alarm_type in self.active_alarms.keys():
                self.deactivate_alarm(alarm_type)

            # make alarm and emit
            new_alarm = Alarm(
                alarm_type = alarm_type,
                severity   = severity,
                start_time = time.time(),
                latch      = self.rules[alarm_type].latch,
                persistent = self.rules[alarm_type].persistent
            )

            for callback in self.callbacks:
                callback(new_alarm)

            if severity> AlarmSeverity.OFF:
                # don't add OFF alarms to active_alarms...
                self.active_alarms[alarm_type] = new_alarm

            self.logger.info('Alarm Raised:\n    '+str(new_alarm))

        else:
            raise ValueError('No  rule found for alarm type {}'.format(alarm_type))

    def deactivate_alarm(self, alarm: (AlarmType, Alarm)):
        """
        Mark an alarm's internal active flags and remove from :attr:`.active_alarms`

        .. note::

            This does *not* alert listeners that an alarm has been cleared,
            for that emit an alarm with AlarmSeverity.OFF

        Args:
            alarm:

        Returns:

        """

        if isinstance(alarm, Alarm):
            alarm_type = alarm.alarm_type

        elif isinstance(alarm, AlarmType):
            alarm_type = alarm

        else:
            raise ValueError(f'alarm must be AlarmType or Alarm, got {alarm}')

        if alarm_type in self.active_alarms.keys():
            if isinstance(alarm, Alarm):
                if alarm is not self.active_alarms[alarm_type]:
                    # if we were passed an Alarm and
                    # if this alarm isn't the one that's active, don't deactivate
                    return
            got_alarm = self.active_alarms.pop(alarm_type)
            got_alarm.deactivate()
            self.logged_alarms.append(got_alarm)
            self.logger.info('Deactivated Alarm:\n    ' + str(got_alarm))
        else:
            return

    def dismiss_alarm(self,
                      alarm_type: AlarmType,
                      duration: float = None,):
        """
        GUI or other object requests an alarm to be dismissed & deactivated

        GUI will wait until it receives an `emit_alarm` of severity == OFF to remove
        alarm widgets. If the alarm is not latched

        If the alarm is latched, alarm_manager will not decrement alarm severity or emit
        `OFF` until a) the condition returns to `OFF`, and b) the user dismisses the alarm

        Args:
            alarm_type (:class:`.AlarmType`): Alarm to dismiss
            duration (float): seconds - amount of time to wait before alarm can be re-raised
                If a duration is provided, the alarm will not be able to be re-raised
        """

        assert(alarm_type in self.rules.keys())

        rule = self.rules[alarm_type]
        # if the alarm is latched, add it to the list of pending_clears
        if rule.latch:
            # if the alarm is in the pending_clears list,
            # when the `rule` returns to OFF, the alarm will be deactivated
            self.pending_clears.append(alarm_type)
            # the rest of the logic doesn't apply to latched alarms
            return

        # if we were provided a snooze duration, add to the snooze dict and clear alarm
        if duration:
            assert isinstance(duration, (int, float))
            assert duration >= 0
            self.snoozed_alarms[alarm_type] = time.time() + duration
            self.emit_alarm(alarm_type, AlarmSeverity.OFF)

        #otherwise alarm will be deactivated until condition goes OFF and back on
        else:
            self.cleared_alarms.append(alarm_type)
            self.emit_alarm(alarm_type, AlarmSeverity.OFF)

    def get_alarm_severity(self, alarm_type: AlarmType):
        if alarm_type in self.active_alarms.keys():
            return self.active_alarms[alarm_type].severity
        else:
            return AlarmSeverity.OFF


    def register_alarm(self, alarm: Alarm):
        """
        Add alarm to registry.

        Args:
            alarm (:class:`.Alarm`)
        """

        if alarm.alarm_type in self.active_alarms.keys():
            if alarm is self.active_alarms[alarm.alarm_type]:
                return
            # if another alarm is already active,
            # check if this is a higher severity
            if alarm.severity > self.active_alarms[alarm.alarm_type].severity:
                self.deactivate_alarm(alarm.alarm_type)
                self.active_alarms[alarm.alarm_type] = alarm
            else:
                return
                # TODO: currently just bouncing redundant alarms, is that what we want?
        else:
            self.active_alarms[alarm.alarm_type] = alarm

        # TODO: Emit evidence of this new alarm

    def register_dependency(self, condition: Condition,
                            dependency: dict,
                            severity: AlarmSeverity):
        """
        Add dependency in a Condition object to be updated when values are changed

        Args:
            condition:
            dependency (dict): either a (ValueName, attribute_name) or optionally also + transformation callable
            severity (:class:`.AlarmSeverity`): severity of dependency
        """

        # invert the structure of the dependency so it's keyed by the ValueName being updated
        dependency['condition'] = condition
        dependency['severity'] = severity
        value_name = dependency.pop('value_name')
        if value_name not in self.dependencies.keys():
            self.dependencies[value_name] = [dependency]
        else:
            self.dependencies[value_name].append(dependency)


    def update_dependencies(self, control_setting: ControlSetting):
        """
        Update Condition objects that update their value according to some control parameter

        Args:
            control_setting (:class:`.ControlSetting`):

        Returns:

        """
        if control_setting.name in self.dependencies.keys():
            # dependencies have
            # ('value_name', 'value_attribute', 'condition_attr', 'transform')
            for depend in self.dependencies[control_setting.name]:

                # get the value from the control setting we want to update from
                new_value = getattr(control_setting, depend['value_attr'])

                # if the attribute we're looking to update from is None, then
                # this control isn't being set right now
                if new_value is None:
                    return

                if 'transform' in depend.keys():
                    # apply transformation if it has one
                    new_value = depend['transform'](new_value)

                setattr(depend['condition'], depend['condition_attr'], new_value)

                # emit control signal with new info
                if isinstance(depend['condition'], condition.ValueCondition):
                    control_kwargs = {
                        'name': control_setting.name,
                        #'value': control_setting.value
                    }
                    if depend['condition'].mode == 'min':
                        control_kwargs['min_value'] = new_value
                    elif depend['condition'].mode == 'max':
                        control_kwargs['max_value'] = new_value

                    control_kwargs['range_severity'] = depend['severity']

                    control_out = ControlSetting(**control_kwargs)
                    for cb in self.depends_callbacks:
                        cb(control_out)


    def add_callback(self, callback: typing.Callable):
        assert callable(callback)
        self.callbacks.append(callback)

    def add_dependency_callback(self, callback: typing.Callable):
        assert callable(callback)
        self.depends_callbacks.append(callback)

    def clear_all_alarms(self):
        # make separate list because dict will be cleared during iteration
        alarm_keys = list(self.active_alarms.keys())
        for alarm_type in alarm_keys:
            self.deactivate_alarm(alarm_type)

    def reset(self):
        """
        reset all conditions, callbacks, and other stateful attributes and clear alarms
        """

        self.pending_clears = []
        self.cleared_alarms = []
        self.snoozed_alarms = {}
        self.callbacks = []

        for rule in self.rules.values():
            rule.reset()

        self.clear_all_alarms()









