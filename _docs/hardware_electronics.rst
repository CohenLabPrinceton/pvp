Electronics
=============

Electrical Block Diagram
----------------

.. figure:: /images/electronics_diagram.png
    :align: center
    :figwidth: 100%
    :width: 100%

	PVP block diagram for main electrical components

Overview
----------------

The PVP is coordinated by a Raspberry Pi 4 board, which runs the graphical user interface, administers the alarm system, monitors sensor values, and sends actuation commands to the valves.
The core electrical system consists of two modular PCB 'hats', a sensor PCB and an actuator PCB, that stack onto the Raspberry Pi via 40-pin stackable headers (Figure \ref{fig:BOARDSTACK}).
The modularity of this system enables individual boards to be revised or modified to adapt to component substitutions if required.

.. toctree::
   :caption: Electronics:
   Power and I/O <hardware.powerio>
   Sensor PCB <hardware.actuators>
   Actuator PCB <hardware.sensors>

Power and I/O
----------------
The main power to the systems is supplied by a DIN rail-mounted 150W 24V supply, which drives the inspiratory valve (4W) and expiratory valves (13W). This voltage is converted to 5V by a switched mode PCB-mounted regulated to power the Raspberry Pi and sensors.
This power is transmitted across the PCBs through the stacked headers when required.

<ADD COMPONENT TABLE>

Sensor PCB
----------------
The sensor board interfaces four analog output sensors with the Raspberry Pi via I2C commands to a 12-bit 4-channel ADC (Adafruit ADS1015).
1. an airway pressure sensor (Amphenol 1 PSI-D-4V-MINI)
2. a differential pressure sensor (Amphenol 5 INCH-D2-P4V-MINI) to report the expiratory flow rate through a D-Lite spirometer
3. an oxygen sensor (Sensiron SS-12A) whose 13 mV differential output signal is amplified 250-fold by an instrumentation amplifier (Texas Instruments INA126)
4. a fourth auxiliary slot for an additional analog output sensor (unused)

A set of additional header pins allows for digital output sensors (such as the Sensiron SFM3300 flow sensor) to be interfaced with the Pi directly via I2C if desired. 

<ADD SCHEMATIC AND COMPONENT TABLE AND PCB FILES>

Actuator PCB
----------------
The purpose of the actuator board is twofold:
1. regulate the 24V power supply to 5V (CUI Inc PDQE15-Q24-S5-D DC-DC converter)
2. interface the Raspberry Pi with the inspiratory and expiratory valves through an array of solenoid drivers (ULN2003A Darlington transistor array)

<ADD SCHEMATIC AND COMPONENT TABLE AND PCB FILES>