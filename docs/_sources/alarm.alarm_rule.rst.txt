Alarm Rule
============

One :class:`.Alarm_Rule` is defined for each :class:`~.alarm.AlarmType` in :data:`.ALARM_RULES`.

An alarm rule defines:

* The conditions for raising different severities of an alarm
* The dependencies between set values and alarm thresholds
* The behavior of the alarm, specifically whether it is :attr:`~.Alarm_Rule.latch` ed.

Example
----------

As an example, we'll define a ``LOW_PRESSURE`` alarm with escalating severity. A ``LOW`` severity alarm
will be raised when measured ``PIP`` falls 10% below set ``PIP``, which will escalate to a
``MEDIUM`` severity alarm if measured ``PIP`` falls 15% below set ``PIP`` **and** the ``LOW`` severity
alarm has been active for at least two breath cycles.

First we define the name and behavior of the alarm::

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

Each condition is a tuple of an (:class:`.AlarmSeverity`, :class:`.Condition`). In this case,
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
        limit=VALUES[ValueName.PIP]['safe_range'][0],
        mode='min'
        depends={
            'value_name': ValueName.PIP,
            'value_attr': 'value',
            'condition_attr': 'limit',
            'transform': lambda x: x - (x * 0.15)
        },
    ) + \
    condition.CycleAlarmSeverityCondition(
        alarm_type = AlarmType.LOW_PRESSURE,
        severity   = AlarmSeverity.LOW,
        n_cycles = 2
    ))

The first ``ValueCondition`` is the same as in the ``LOW`` alarm severity condition, except that it is
set 15% below ``PIP``.

A second :class:`.CycleAlarmSeverityCondition` has been added (with ``+``) to the :class:`.ValueCondition`
When conditions are added together, they will only return ``True`` (ie. trigger an alarm) if all of the conditions are met.
This condition checks that the ``LOW_PRESSURE`` alarm has been active at a ``LOW`` severity for at least two cycles.

Full source for this example and all alarm rules can be found `here <_modules/pvp/alarm.html>`_


Module Documentation
--------------------

.. automodule:: pvp.alarm.rule
    :members:
    :undoc-members:
    :autosummary: