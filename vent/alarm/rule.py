"""
Class to declare alarm rules
"""

from vent.alarm import AlarmType, AlarmSeverity

class Alarm_Rule(object):
    """
    * name of rule
    * conditions: ((alarm_type, (condition_1, condition_2)), ...)
    * persistent (bool): if True, alarm will not be visually dismissed until alarm conditions are no longer true
    * latch (bool): if True, alarm severity cannot be decremented until user manually dismisses

    * silencing/overriding rules
    """

    def __init__(self, name: AlarmType, conditions, latch=True, persistent=True, technical=False):
        super(Alarm_Rule, self).__init__()

        self.name = name
        self.conditions = conditions
        self.technical = technical
        self.latch = latch
        self.persistent = persistent

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
                if severity.value > active_severity.value:
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
