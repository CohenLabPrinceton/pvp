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
    * Save/load parameters. Autosave, and autorestore if saved <5m ago, otherwise init from defaults.
    * Possible plots

        * Pressure vs. flow
        * flow vs volume
        * volume vs time


* Spec a display for Julienne!!!!

GUI Object Documentation
-------------------------

Main GUI Module
~~~~~~~~~~~~~~~~~

.. automodule:: vent.gui
    :members:
    :undoc-members:
    :autosummary:

GUI Widgets
~~~~~~~~~~~~~

.. automodule:: vent.gui.widgets
    :members:
    :undoc-members:
    :autosummary:

GUI Defaults
~~~~~~~~~~~~~~~

.. automodule:: vent.gui.defaults
    :members:
    :undoc-members:
    :autosummary:

GUI Stylesheets
~~~~~~~~~~~~~~~~~~

.. automodule:: vent.gui.styles
    :members:
    :undoc-members:
    :autosummary:
