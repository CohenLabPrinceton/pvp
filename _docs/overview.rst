System Overview
=================

The **People's Ventilator Project (PVP)** is an open-source, low-cost pressure-control ventilator designed for minimal reliance on specialized medical parts to better adapt to supply chain shortages.

.. raw:: html

    <video width="100%" autoplay loop>
      <source src="images/ventilator_rotate.mp4" type="video/mp4">
    Video of a rotating ventilator
    </video>

.. toctree::
   :maxdepth: 4
   :caption: Hardware:

   Hardware <overview.hardware>
   Software <overview.software>

Hardware
=========

.. raw:: html
    :file: /images/schematic_v2.svg

The device components were selected to enable a **minimalistic and relatively low-cost ventilator design, 
to avoid supply chain limitations, and to facilitate rapid and easy assembly**. 
Most parts in the PVP are not medical-specific devices, and those that are specialized components 
are readily available and standardized across ventilator platforms, such as standard respiratory 
circuits and HEPA filters. We provide complete assembly of the PVP, 
including 3D-printable components, as well as justifications for selecting all actuators and sensors,
as guidance to those who cannot source an exact match to components used in the Bill of Materials.

PVP Hardware
--------------

.. raw:: html

    <div class="software-summary">
	    <a href="components.html"><h2>Components</h2></a> <p>Justifcation behind the components actuators and sensors selected for the PVP.</p>
		<a href="assembly.html"><h2>Assembly</h2></a> <p>Solidworks model of the system assembly, description of enclosure, and models for 3D printed components.</p>
        <a href="electronics.html"><h2>Electronics</h2></a> <p>Modular PCBs that interface the PVP actuators and sensors with the Raspberry Pi.</p>
		<a href="bom.html"><h2>Bill of Materials</h2></a> <p>Itemized PVP parts list.</p>
	</div>


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
