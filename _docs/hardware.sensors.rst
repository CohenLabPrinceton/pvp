Sensors | Hardware
=========

Overview
-------------------
The TigerVent has four main sensors:
1. oxygen sensor (O2S)
2. proximal pressure sensor (PS1)
3. expiratory pressure sensor (PS2)
4. expiratory flow sensor (FS1)

These materials interface with a modular sensor PCB that can be reconfigured for part substitution.
The nominal design assumes both pressure sensors and the oxygen sensor have analog voltage outputs, and interface with the controller via I2C link with a 16-bit, 4 channel ADC (ADS1115).
The expiratory flow sensor (SFM3300 or equivalent) uses a direct I2C interface, but can be replaced by a commercial spirometer and an additional differential pressure sensor.

Sensor PCB
-------------------

Schematic
*******************
.. figure:: /images/sensor_pcb_schematic.png
    :align: center
    :figwidth: 100%
    :width: 100%

    Electrical schematic for sensor board

Bill of Materials
*******************

.. list-table:: Bill of materials
    :widths: 25 50 50 50
    :header-rows: 1
* - Ref
  - Part
  - Description
  - Datasheet
* - U1
  - Amphenol 1 PSI-D1-4V-MINI
  - Analog output differential pressure sensor
  - /DS-0103-Rev-A-1499253.pdf <- not sure best way to do this
* - U3
  - Amphenol 1 PSI-D1-4V-MINI differential pressure sensor
  - Analog output differential pressure sensor
  - above 
* - U2
  - Adafruit 4-channel ADS1115 ADC breakout
  - Supply ADC to RPi to read analog sensors
  - /adafruit-4-channel-adc-breakouts.pdf
* - U4
  - INA126 instrumentation amplifier, DIP-8
  - Instrumentation amplifier to boost oxygen sensor output
  - /ina126.pdf
* - J1
  - 01x02 2.54 mm pin header
  - Breakout for alert pin from ADS1115 ADC
  - none
* - J2
  - 02x04 2.54 mm pin header
  - Jumpers to select I2C address for ADC 
  - none
* - J3
  - 40 pin RPi hat connector
  - Extends RPi GPIO pins to the board
  - (to be inserted)
* - J4
  - 01x02 2.54 mm 90 degree pin header
  - For direct connection to oxygen sensor output
  - none
* - J5
  - 01x04 2.54 mm 90 degree pin header pin header
  - For I2C connection to SFM3300 flow meter
  - none
* - J6
  - 01x03 2.54 mm 90 degree pin header pin header
  - Connector to use an additional analog output (ADS1115 input A3).
  - none
* - R1
  - 1-2.7 k resistor
  - Optional I2C pullup resistor (RPi already has 1.8k pullups)
  - none
* - R2
  - 1-2.7 k resistor
  - Connector to use an additional analog output (RPi already has 1.8k pullups).
  - none 
* - R3
  - 0.1-100k resistor
  - R_G that sets gain for the INA126 instrumentation amplifier (U4). G = 5 + 80k/R_G
  - none 
  
Flow sensor
-------------------
Document D-lite alternative 
 
Pressure sensors
-------------------
Just use any other analog voltage output (0-4 V) sensor

Oxygen sensor
-------------------
Explanation of interface circuit and some alts

- Expiratory flow sensor (FS1)
