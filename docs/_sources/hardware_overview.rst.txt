Hardware Overview
==================

Mechanical Diagram
----------------

.. figure:: /images/mechanical_diagram.png
    :align: center
    :figwidth: 100%
    :width: 100%

    Schematic diagram of main mechanical components <- THIS NEEDS TO BE UPDATED

Flow actuators
-------------------    
- Actuator PCB/overview (link to PCB with BoM, schematic, layout, etc.)    
- Proportional solenoid valve (V1) (link to doc with crit specs, driving circuit, part spec, datasheet, alternatives, etc.)
- Expiratory valve (V2) (link to doc with crit specs, driving circuit, part spec, datasheet, etc.)
    
Sensors
-------------------
- Sensor PCB/overview (link to PCB with BoM, schematic, layout, etc.)
- Oxygen sensor (O2S) (link to doc with crit specs, interface circuit, part spec, datasheet, alternatives, etc.)
- Proximal pressure sensor (PS1)
- Expiratory pressure sensor (PS2)
- Expiratory flow sensor (FS1)

Bill of Materials
-------------------

.. list-table:: 
   :widths: 15 50 50 50
   :header-rows: 1

   * - Ref
     - Name
     - Part
     - Description
   * - V1
     - Inspiratory on/off valve
     - red hat process valve
     - completely cut off flow if required
   * - PRV1
     - High pressure relief valve
     - Sets to 50 psi
     - regulates upstream pressure to 50 psi
   * - CV
     - Inspiratory check valve
     - valve stat here
     - In case of emergency power loss, allows patient to continue taking breaths from air
   * - PRV2
     - Maximum pressure valve
     - ...
     - Sets absolute maximum pressure at patient side to 53 cm H2O
   * - F1/F2
     - Filters
     - HEPA filters?
     - Keeps the system's sensors from becoming contaminated
   * - O2S
     - Oxygen sensor
     - Sensiron ...
     - Checks FiO2 level
   * - PS1/PS2
     - Pressure sensors
     - mini4v
     - Uses gas takeoffs to measure pressure at each desired point
   * - FS1
     - Flow sensor
     - Sensiron flow sensor
     - Measures expiratory flow to calculate tidal volume
   * - M1/M2
     - Manifolds
     - 3D printed parts
     - Hubs to connect multiple components in one place
   * - V3
     - Expiratory on/off valve
     - Festo Electrical Air Directional Control Valve, 3/2 flow, Normally Closed, 8 mm Push-to-Connect
     - Opens to initiation the expiratory cycle
   * - PEEP
     - PEEP backpressure valve
     - PEEP valve
     - Sets PEEP on expiratory cycle!
