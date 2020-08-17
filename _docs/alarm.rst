Alarm
==========

Alarm System Overview
----------------------

Alarms are represented as :class:`~.alarm.Alarm` objects, which are created and managed by the
:class:`.Alarm_Manager`. A collection of :class:`.Alarm_Rule` s define the :class:`.Condition` s
for raising :class:`~.alarm.Alarm` s of different :class:`~.alarm.AlarmSeverity` . The alarm manager is
continuously fed :class:`~.message.SensorValues` objects during :meth:`.PVP_Gui.update_gui`, which it uses to
:meth:`~.Alarm_Rule.check` each alarm rule. The alarm manager emits :class:`~.alarm.Alarm` objects to the
:meth:`.PVP_Gui.handle_alarm` method. The alarm manager also updates alarm thresholds set as :attr:`.Condition.depends`
when control parameters are set (eg. updates the ``HIGH_PRESSURE`` alarm to be triggered 15% above some set ``PIP`` ).

Alarm Rule Example
~~~~~~~~~~~~~~~~~~~

One :class:`.Alarm_Rule` is defined for each :class:`~.alarm.AlarmType` in :data:`.ALARM_RULES`.

An alarm rule defines:

* The conditions for raising different severities of an alarm
* The dependencies between set values and alarm thresholds
* The behavior of the alarm, specifically whether it is :attr:`~.Alarm_Rule.latch` ed or :attr:`~.Alarm_Rule.persistent`

::

    Alarm_Rule(
        name = AlarmType.LOW_PRESSURE,
        latch = False,
        persistent = False,
        conditions = (
            (
            AlarmSeverity.LOW,
                condition.ValueCondition(
                    value_name=ValueName.PIP,
                    limit=VALUES[ValueName.PIP]['safe_range'][0],
                    mode='min',
                    depends={
                        'value_name': ValueName.PIP,
                        'value_attr': 'value',
                        'condition_attr': 'limit',
                        'transform': lambda x : x-(x*0.10)
                    }
                )
            ),
            (
            AlarmSeverity.MEDIUM,
                condition.ValueCondition(
                    value_name=ValueName.PIP,
                    limit=VALUES[ValueName.PIP]['safe_range'][0]- \
                          VALUES[ValueName.PIP]['safe_range'][0]*0.15,
                    depends={
                        'value_name': ValueName.PIP,
                        'value_attr': 'value',
                        'condition_attr': 'limit',
                        'transform': lambda x: x - (x * 0.15)
                    },
                    mode='min'
                ) + \
                condition.CycleAlarmSeverityCondition(
                    alarm_type = AlarmType.LOW_PRESSURE,
                    severity   = AlarmSeverity.LOW,
                    n_cycles = 2
                )
            )
        )
    )


Main Alarm Module
-------------------

.. automodule:: pvp.alarm
    :members:
    :undoc-members:
    :autosummary:

.. toctree::
    :hidden:

    Alarm Manager <alarm.alarm_manager>
    Alarm <alarm.alarm>
    Alarm Rule <alarm.alarm_rule>
    Alarm Condition <alarm.condition>




