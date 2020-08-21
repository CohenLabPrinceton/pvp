.. title:: The People's Ventilator Project

.. raw:: html

   <div class="header-img" >
      <img alt="People's Ventilator Project logo" src="images/pvp_logo_fulltext.png">
      <div>
         <h1>A fully-open</h1>
         <h1>Supply-chain resilient</h1>
         <h1>pressure-control ventilator</h1>
         <h1 style="color: #fd2701;">for the people</h1>
      </div>
   </div>

The global COVID-19 pandemic has highlighted the need for a low-cost, rapidly-deployable ventilator, for the current as well as future respiratory virus outbreaks.
While safe and robust ventilation technology exists in the commercial sector, the small number of capable suppliers cannot meet the severe demands for ventilators during a pandemic. 

**<Statement of cost>** Moreover, the specialized and proprietary equipment developed by medical device manufacturers is expensive and inaccessible in low-resource areas.
Compounding the issue during an emergency, manufacturing time...

The **People's Ventilator Project (PVP)** is an open-source, low-cost pressure-control ventilator designed with minimal reliance on specialized medical parts to better adapt to supply chain shortages.
The **PVP** largely follows established design conventions, most importantly active and computer-controlled inhalation, together with passive exhalation.
It supports pressure-controlled ventilation, combined with standard-features like autonomous breath detection, and the suite of FDA required alarms.

**<Statement of purpose>**

.. raw:: html

    <video width="100%" autoplay loop>
      <source src="images/ventilator_rotate.mp4" type="video/mp4">
    Video of a rotating ventilator
    </video>


Hardware
=========

PVP is a pressure-controlled ventilator that uses a minimal set of inexpensive, off-the-self hardware components.
An inexpensive proportional valve controls inspiratory flow, and a relay valve controls expiratory flow.
A gauge pressure sensor monitors airway pressure, and an inexpensive D-lite spirometer used in conjunction with a differential pressure sensor monitors expiratory flow.

.. raw:: html
    <object type="image/svg+xml" data="assets/images/Schematic_v2.svg">
    Hardware schematic for People's Ventilator Project
    </object>

PVP's components are coordinated by a Raspberry Pi 4 board, which runs the graphical user interface, administers the alarm system, monitors sensor values, and sends actuation commands to the valves.
The core electrical system consists of two modular board 'hats', a sensor board and an actuator board, that stack onto the Raspberry Pi via 40-pin stackable headers.
The modularity of this system enables individual boards to be revised or modified to substitute components in the case of part scarcity.

.. raw:: html

    <img src="assets/images/electronics_diagram.png" alt="Electronics diagram for People's Ventilator Project">
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
        <a href="common.html"><h2>Common</h2></a> <p>Modules that provide the API between the GUI and controller, user preferences, and other utilities</p>
    </div>




.. toctree::
   :hidden:
   :maxdepth: 4
   :caption: Overview

   System Overview <overview>

.. toctree::
   :hidden:
   :maxdepth: 4
   :caption: Hardware:

   Hardware Overview <hardware_overview>
   Sensors <hardware_sensors>
   Actuators <hardware_actuators>
   Electronics <hardware_electronics>
   Safety <hardware_safety>
   Enclosure <hardware_enclosure>

.. toctree::
   :hidden:
   :maxdepth: 4
   :caption: Software:

   Software Overview <software_overview>
   Main <main>
   GUI <gui>
   Controller <controller>
   Common <common>
   I/O <io>
   Alarm <alarm>
   Coordinator <coordinator>

.. toctree::
   :hidden:
   :maxdepth: 4
   :caption: Resources:

   Ventilator Requirements <requirements>
   Datasheets & Manuals <datasheets>
   Specifications <specs>


.. toctree::
   :hidden:
   :maxdepth: 4
   :caption: Meta:

   Changelog <changelog/index>
   Contributing <contributing>
   Building the Docs <buildthedocs>
   Markdown Example <example_markdown>
   Index <meta_index>
