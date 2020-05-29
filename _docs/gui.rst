gui
======

Program Diagram
----------------

.. figure:: /images/gui_diagram.png
    :align: center
    :figwidth: 100%
    :width: 100%

    Schematic diagram of major UI components and signals

Design Requirements
-------------------

* Display Values

    * Value name, units, absolute range, recommended range, default range
    * VTE
    * FiO2
    * Humidity
    * Temperature

* Plots
* Controlled Values

    * PIP
    * PEEP
    * Inspiratory Time

* Value Dependencies

UI Notes & Todo
-------------------

* Jonny add notes from helpful RT in discord!!!
* Top status Bar

    * Start/stop button
    * Status indicator - a clock that increments with heartbeats,
      or some other visual indicator that things are alright
    * Status bar - most recent alarm or notification w/ means of clearing
    * Override to give 100% oxygen and silence all alarms

* API

    * Two queues, input and output. Read from socket and put directly into queue.
    * Input, receive (timestamp, key, value) messages where key and value are names of variables and their values
    * Output, send same format

* Menus

    * Trigger some testing/calibration routine
    * Log/alarm viewer
    * Wizard to set values?
    * save/load values

* Alarms

    * Multiple levels
    * Silenced/reset
    * Logging
    * Sounds?


* General

    * Reduce space given to waveforms
    * Clearer grouping & titling for display values & controls
    * Collapsible range setting
    * Ability to declare dependencies between values

        * Limits - one value's range logically depends on another
        * Derived - one value is computed from another/others

    * Monitored values should have defaults, warning range, and absolute range
    * Two classes of monitored values -- ones with limits and ones without. There seem to be
      lots and lots of observed values, but only some need limits. might want to make larger drawer
      of smaller displayed values that don't need controls
    * Save/load parameters. Autosave, and autorestore if saved <5m ago, otherwise init from defaults.
    * Implement timed updates to plots to limit resource usage
    * Make class for setting values
    * Possible plots

        * Pressure vs. flow
        * flow vs volume
        * volume vs time

* Performance

    * Cache drawText() calls in range selector by drawing to pixmap

Jonny Questions
------------------

* Which alarm sounds to use?
* Final final final breakdown on values and ranges plzzz
* RR always has to be present, can only auto calculate InspT, I:E
* make alarm dismissals all latch and snooze.

jonny todo
______________

* use loop_counter to check on controller advancement
* choice between pressure/volume over time and combined P/V plot
* display flow in SLM (liters per minute)
* deque for alarm manager logged alarms
* need confirmation for start button



GUI Object Documentation
-------------------------

Main GUI Module
~~~~~~~~~~~~~~~~~

.. automodule:: vent.gui.main
    :members:
    :undoc-members:
    :autosummary:

GUI Widgets
~~~~~~~~~~~~~

Control
_________

.. automodule:: vent.gui.widgets.control
    :members:
    :undoc-members:
    :autosummary:

Monitor
_________

.. automodule:: vent.gui.widgets.monitor
    :members:
    :undoc-members:
    :autosummary:

Plot
_______

.. automodule:: vent.gui.widgets.plot
    :members:
    :undoc-members:
    :autosummary:

Status Bar
____________

.. automodule:: vent.gui.widgets.status_bar
    :members:
    :undoc-members:
    :autosummary:

Components
____________

.. automodule:: vent.gui.widgets.components
    :members:
    :undoc-members:
    :autosummary:

GUI Stylesheets
~~~~~~~~~~~~~~~~~~

.. automodule:: vent.gui.styles
    :members:
    :undoc-members:
    :autosummary:

GUI Alarm Manager
~~~~~~~~~~~~~~~~~~~

.. automodule:: vent.gui.alarm_manager
    :members:
    :undoc-members:
    :autosummary: