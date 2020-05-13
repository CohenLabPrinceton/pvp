import copy
import pdb




from vent.alarm import AlarmSeverity, AlarmType
from vent.alarm.condition import Condition
from vent.common.message import SensorValues, ControlSetting
from vent.alarm.alarm import Alarm

import typing

ALARM_MANAGER_INSTANCE = None

class Alarm_Manager(object):
    """
    Attributes:
        active_alarms (dict): {:class:`.AlarmType`: :class:`.Alarm`}
    """

    def __new__(cls):
        """
        If an Alarm_Manager already exists, when initing just return that one
        """
        if isinstance(globals()['ALARM_MANAGER_INSTANCE'], Alarm_Manager):
            return globals()['ALARM_MANAGER_INSTANCE']
        else:
            # create alarm manager
            manager_instance = super(Alarm_Manager, cls).__new__(cls)
            globals()['ALARM_MANAGER_INSTANCE'] = manager_instance
            return manager_instance



    def __init__(self):
        self.active_alarms: typing.Dict[AlarmType, Alarm] = {}
        self.logged_alarms: typing.List[Alarm] = []

        # get our alarm rules
        self.dependencies = {}
        self.load_rules()


    def load_rules(self):
        from vent.alarm import ALARM_RULES
        self.rules = copy.deepcopy(ALARM_RULES)

        # register dependencies
        for alarm_name, alarm_rule in self.rules.items():
            try:
                for severity, condition in alarm_rule.conditions:


                    if isinstance(condition.depends, dict):
                        self.register_dependency(condition,  condition.depends)
                    elif isinstance(condition.depends, list) or isinstance(condition.depends, tuple):
                        for depend in condition.depends:
                            self.register_dependency(condition, depend)
            except:
                pdb.set_trace()

    def update(self, sensor_values: SensorValues):
        for alarm_name, rule in self.rules.items():
            current_severity = rule.check(sensor_values)

            if alarm_name in self.active_alarms.keys():
                # if we've got an active alarm of this type
                # check if the severity has changed
                if current_severity.value < self.active_alarms[alarm_name].severity.value:
                    # if we have a lower severity
                    # TODO
                    # check if latched
                    pass

    def get_alarm_severity(self, alarm_type: AlarmType):
        if alarm_type in self.active_alarms.keys():
            return self.active_alarms[alarm_type].severity
        else:
            return AlarmSeverity.OFF


    def register_alarm(self, alarm: Alarm):
        """
        Add alarm to registry

        Args:
            alarm (:class:`.Alarm`)
        """

        if alarm.alarm_type in self.active_alarms.keys():
            if alarm is self.active_alarms[alarm.alarm_type]:
                return
            # if another alarm is already active,
            # check if this is a higher severity
            if alarm.severity.value > self.active_alarms[alarm.alarm_type].severity.value:
                self.deactivate_alarm(alarm.alarm_type)
                self.active_alarms[alarm.alarm_type] = alarm
            else:
                return
                # TODO: currently just bouncing redundant alarms, is that what we want?
        else:
            self.active_alarms[alarm.alarm_type] = alarm

        # TODO: Emit evidence of this new alarm

    def register_dependency(self, condition: Condition,
                            dependency: dict):
        """
        Add dependency in a Condition object to be updated when values are changed

        Args:
            condition:
            dependency (dict): either a (ValueName, attribute_name) or optionally also + transformation callable
        """

        # invert the structure of the dependency so it's keyed by the ValueName being updated
        dependency['condition'] = condition,
        value_name = dependency.pop('value_name')
        if value_name not in self.dependencies.keys():
            self.dependencies[value_name] = [dependency]
        else:
            self.dependencies[value_name].append(dependency)


    def update_dependencies(self, control_setting: ControlSetting):
        if control_setting.name in self.dependencies.keys():
            # dependencies have
            # ('value_name', 'value_attribute', 'condition_attr', 'transform')
            for depend in self.dependencies[control_setting.name]:

                # get the value from the control setting we want to update from
                new_value = getattr(control_setting, depend['value_attribute'])

                # if the attribute we're looking to update from is None, then
                # this control isn't being set right now
                if new_value is None:
                    return

                if 'transform' in depend.keys():
                    # apply transformation if it has one
                    new_value = depend['transform'](new_value)

                setattr(depend['condition'], depend['condition_attr'], new_value)







    def deactivate_alarm(self, alarm: (AlarmType, Alarm)):

        if isinstance(alarm, Alarm):
            alarm_type = alarm.alarm_type

        elif isinstance(alarm, AlarmType):
            alarm_type = alarm

        else:
            raise ValueError(f'alarm must be AlarmType or Alarm, got {alarm}')

        if alarm_type in self.active_alarms.keys():

            got_alarm = self.active_alarms.pop(alarm_type)
            alarm.deactivate()
            self.logged_alarms.append(alarm)
        else:
            return





