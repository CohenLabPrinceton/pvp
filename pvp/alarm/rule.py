"""
Class to declare alarm rules
"""
import typing
from pvp.common.values import ValueName
from pvp.alarm import AlarmType, AlarmSeverity

class Alarm_Rule(object):
    """
    * name of rule
    * conditions: ((alarm_type, (condition_1, condition_2)), ...)
    * latch (bool): if True, alarm severity cannot be decremented until user manually dismisses

    * silencing/overriding rules
    """

    def __init__(self, name: AlarmType, conditions, latch=True, technical=False):
        super(Alarm_Rule, self).__init__()

        self.name = name
        self.conditions = conditions
        self.technical = technical
        self.latch = latch

        self._severity = AlarmSeverity.OFF

    def check(self, sensor_values):
        """
        Check all of our :attr:`.conditions` .

        Args:
            sensor_values:

        Returns:

        """
        active_severity = AlarmSeverity.OFF
        for severity, condition in self.conditions:
            active = condition.check(sensor_values)
            if active:
                if severity > active_severity:
                    active_severity = severity

        self._severity = active_severity
        return active_severity

    @property
    def severity(self):
        """
        Last Alarm Severity from ``.check()``
        Returns:
            :class:`.AlarmSeverity`

        """
        return self._severity


    def reset(self):
        for _, condition in self.conditions:
            condition.reset()

    @property
    def depends(self) -> typing.List[ValueName]:
        """
        Get all ValueNames whose alarm limits depend on this alarm rule
        Returns:
            list[ValueName]
        """
        depends = []
        for condition_pair in self.conditions:
            condition = condition_pair[1]

            if condition.depends is not None:
                if condition.depends.get('value_name', False):
                    depends.append(condition.depends['value_name'])

        return depends

    @property
    def value_names(self) -> typing.List[ValueName]:
        """
        Get all ValueNames specified as value_names in alarm conditions

        Returns:
            list[ValueName]
        """

        return [c[1].value_name for c in self.conditions]