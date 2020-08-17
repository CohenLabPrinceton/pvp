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

Alarm Rule Example
~~~~~~~~~~~~~~~~~~~

One :class:`.Alarm_Rule` is defined for each :class:`~.alarm.AlarmType` in :data:`.ALARM_RULES`.

An alarm rule defines:

* The conditions for raising different severities of an alarm
* The dependencies between set values and alarm thresholds
* The behavior of the alarm, specifically whether it is :attr:`~.Alarm_Rule.latch` ed.

As an example, we'll define a ``LOW_PRESSURE`` alarm with escalating severity. First we define the name and
behavior of the alarm::

    Alarm_Rule(
        name = AlarmType.LOW_PRESSURE,
        latch = False,

In this case, ``latch == False`` means that the alarm will disappear (or be downgraded in severity)
whenever the conditions for that alarm are no longer met. If ``latch == True``, an alarm requires manual dismissal before
it is downgraded or disappears.

Next we'll define a tuple of :class:`.Condition` objects for ``LOW`` and ``MEDIUM`` severity objects.

Starting with the ``LOW`` severity alarm::

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
                })
            ),
            # ... continued in next block

Each condition is a tuple of an ``(:class:`.AlarmSeverity`, :class:`.Condition`)``. In this case,
we use a :class:`.ValueCondition` which tests whether a value is above or below a set ``'max'`` or ``'min'``, respectively.
For the low severity ``LOW_PRESSURE`` alarm, we test if ``ValueName.PIP`` is below (``mode='min'``) some ``limit``, which
is initialized as the low-end of ``PIP``'s safe range.

We also define a condition for updating the ``'limit'`` of the condition (``'condition_attr' : 'limit'``), from the
:attr:`.ControlSetting.value`` field whenever ``PIP`` is updated. Specifically, we set the ``limit`` to be 10% less than the
set ``PIP`` value by 10% with a lambda function (``lambda x : x-(x*0.10)``).

Next, we define the ``MEDIUM`` severity alarm condition::


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
            ))


Main Alarm Module
-------------------

.. automodule:: pvp.alarm
    :members:
    :undoc-members:
    :autosummary:






