Alarm
==========

.. toctree::
    :hidden:

    Alarm Manager <alarm.alarm_manager>
    Alarm <alarm.alarm>
    Alarm Rule <alarm.alarm_rule>
    Alarm Condition <alarm.condition>

Alarm System Overview
----------------------

Alarms are represented as :class:`~.alarm.Alarm` objects, which are created and managed by the
:class:`.Alarm_Manager`. A collection of :class:`.Alarm_Rule` s define the :class:`.Condition` s
for raising :class:`~.alarm.Alarm` s of different :class:`~.alarm.AlarmSeverity` . The alarm manager is
continuously fed :class:`~.message.SensorValues` objects during :meth:`.PVP_Gui.update_gui`, which it uses to
:meth:`~.Alarm_Rule.check` each alarm rule. The alarm manager emits :class:`~.alarm.Alarm` objects to the
:meth:`.PVP_Gui.handle_alarm` method. The alarm manager also updates alarm thresholds set as :attr:`.Condition.depends`
when control parameters are set (eg. updates the ``HIGH_PRESSURE`` alarm to be triggered 15% above some set ``PIP`` ).



Main Alarm Module
-------------------

.. automodule:: pvp.alarm
    :members:
    :undoc-members:
    :autosummary:






