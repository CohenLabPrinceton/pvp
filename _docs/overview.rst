System Overview
=================

Hardware
=========

PVP is a pressure-controlled ventilator that uses a minimal set of inexpensive, off-the-self hardware components.
An inexpensive proportional valve controls inspiratory flow, and a relay valve controls expiratory flow.
A gauge pressure sensor monitors airway pressure, and an inexpensive D-lite spirometer used in conjunction with a differential pressure sensor monitors expiratory flow.

.. raw:: html
    <object type="image/svg+xml" data="images/Schematic_v2.svg">
    Hardware schematic for People's Ventilator Project
    </object>

PVP's components are coordinated by a Raspberry Pi 4 board, which runs the graphical user interface, administers the alarm system, monitors sensor values, and sends actuation commands to the valves.
The core electrical system consists of two modular board 'hats', a sensor board and an actuator board, that stack onto the Raspberry Pi via 40-pin stackable headers.
The modularity of this system enables individual boards to be revised or modified to substitute components in the case of part scarcity.

.. raw:: html

    <img src="images/electronics_diagram.png" alt="Electronics diagram for People's Ventilator Project">
    </img>

Links to system:
... Mechanical overview
... Electronics overview

Software
========

.. image:: /images/gui_overview_v1_1920px.png
   :width: 100%
   :alt: Gui Overview - modular design, alarm cards, multiple modalities of input, alarm limits represented consistently across ui


PVP's software was developed to bring the philosophy of free and open-source software to medical devices. PVP is not only
open from top to bottom, but we have developed it as a framework for **an adaptable, general-purpose, communally-developed ventilator.**

PVP's ventilation control system is fast, robust, and **written entirely in high-level Python** (3.7) -- without the development
and inspection bottlenecks of split computer/microprocessor systems that require users to read and write low-level hardware firmware.

All of PVP's components are **modularly designed**, allowing them to be reconfigured and expanded for new ventilation modes and
hardware configurations.

We provide complete **API-level documentation** and an **automated testing suite**
to give everyone the freedom to inspect, understand, and expand PVP's software framework.



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
