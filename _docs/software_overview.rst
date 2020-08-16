.. _software_overview:

Software Overview
==================

.. raw:: html
    :file: assets/images/pvp_software_overview_clickable.svg

PVP runs as three independent processes:

* The :ref:`GUI <gui_overview>` and :ref:`Coordinator <coordinator_overview>` run in the first process, receive user input, display system status, and relay :class:`~.message.ControlSetting` s to the :ref:`Controller <controller_overview>` .
* At launch, the :ref:`Coordinator <coordinator_overview>` spawns a :ref:`Controller <controller_overview>` that runs the logic of the ventilator based on control values from the GUI.
* The :ref:`Controller <controller_overview>` communicates with a third `pigpiod <http://abyz.me.uk/rpi/pigpio/>`_ process which communicates with the ventilation hardware

PVP is configured by

* The :ref:`Values <values_overview>` module parameterizes the different sensor and control values displayed by the GUI and used by the controller
* The :ref:`Prefs <prefs_overview>` module creates a ``prefs.json`` file in ``~/pvp`` that defines user-specific preferences.

PVP is launched like::

    python3 -m pvp.main

And launch options can be displayed with the ``--help`` flag.

PVP Modules
------------

.. raw:: html

    <div class="software-summary">
        <a href="gui.html"><h2>GUI</h2></a> <p>A modular GUI with intuitive controls and a clear alarm system that can be configured to control any parameter or display values from any sensor.</p>
        <a href="controller.html"><h2>Controller</h2></a> <p>... Manuel write this</p>
        <a href="io.html"><h2>IO</h2></a> <p>A hardware abstraction layer powered by <a href="http://abyz.me.uk/rpi/pigpio/">pigpio</a> that can read/write at [x Hz]</p>
        <a href="alarm.html"><h2>Alarm</h2></a> <p>Define complex and responsive alarm triggering criteria with human-readable Alarm Rules</p>
        <a href="common.html"><h2>Common</h2><a> <p>Modules that provide the API between the GUI and controller, user preferences, and other utilities</p>
    </div>