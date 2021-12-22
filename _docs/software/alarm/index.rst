Alarm
==========


Alarm System Overview
----------------------

* Alarms are represented as :class:`~.alarm.Alarm` objects, which are created and managed by the :class:`.Alarm_Manager`.
* A collection of :class:`.Alarm_Rule` s define the :class:`.Condition` s for raising :class:`~.alarm.Alarm` s of different :class:`~.alarm.AlarmSeverity` .
* The alarm manager is continuously fed :class:`~.message.SensorValues` objects during :meth:`.PVP_Gui.update_gui`, which it uses to :meth:`~.Alarm_Rule.check` each alarm rule.
* The alarm manager emits :class:`~.alarm.Alarm` objects to the :meth:`.PVP_Gui.handle_alarm` method.
* The alarm manager also updates alarm thresholds set as :attr:`.Condition.depends` to :meth:`.PVP_Gui.limits_updated` when control parameters are set (eg. updates the ``HIGH_PRESSURE`` alarm to be triggered 15% above some set ``PIP`` ).

Alarm Modules
---------------

.. toctree::
    :hidden:

    Alarm Manager <alarm_manager>
    Alarm <alarm>
    Alarm Rule <alarm_rule>
    Alarm Condition <condition>

.. raw:: html

    <div class="software-summary">
        <a href="alarm.alarm_manager.html"><h2>Alarm Manager</h2></a> <p>Computes alarm logic and emits alarms to the GUI</p>
        <a href="alarm.alarm.html"><h2>Alarm</h2></a> <p>Objects used to represent alarms</p>
        <a href="alarm.alarm_rule.html"><h2>Alarm Rule</h2></a> <p>Define conditions for triggering alarms and their behavior</p>
        <a href="alarm.condition.html"><h2>Condition</h2></a> <p>Objects to check for alarm state</p>
    </div>


Main Alarm Module
-------------------

.. automodule:: pvp.alarm
    :members:
    :undoc-members:
    :autosummary:






