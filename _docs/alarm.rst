Alarm
==========

Alarms are represented as :class:`~.alarm.Alarm` objects, which are created and managed by the
:class:`~.alarm.Alarm_Manager`. A collection of :class:`~.alarm.Alarm_Rule` s
 define the :class:`~.alarm.Condition` s
for raising :class:`~.alarm.Alarm` s of different :class:`~.alarm.AlarmSeverity` . The alarm manager is
continuously fed :class:`~.message.SensorValues` objects during :meth:`.PVP_Gui.update_gui`, which it uses to
:meth:`~.Alarm_Rule.check` each alarm rule. The alarm manager emits :class:`~.alarm.Alarm` objects to the
:meth:`.PVP_Gui.handle_alarm` method. The alarm manager also updates alarm thresholds set as :attr:`.Condition.depends`
when control parameters are set (eg. updates the ``HIGH_PRESSURE`` alarm to be triggered 15% above some set ``PIP`` ). 

One :class:`~.alarm.Alarm_Rule` is defined for each :class:`~.alarm.AlarmType` in :data:`.alarm.ALARM_RULES`.




Main Alarm Module
-------------------

.. automodule:: pvp.alarm
    :members:
    :undoc-members:
    :autosummary:




