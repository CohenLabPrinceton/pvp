Alarm Condition
===================

Condition objects define conditions that can raise alarms. They are used by :class:`.Alarm_Rule` s.

Each has to define a :meth:`.Condition.check` method that accepts :class:`.SensorValues` .
The method should return ``True`` if the alarm condition is met, and ``False`` otherwise.

Conditions can be added (``+``) together to make compound conditions, and a single call to ``check`` will only return true
if both conditions return true. If any condition in the chain returns false, evaluation is stopped and
the alarm is not raised.

Conditions can

.. inheritance-diagram:: pvp.alarm.condition

.. automodule:: pvp.alarm.condition
    :members:
    :undoc-members:
    :autosummary:
    :show-inheritance:
