# Vent control pseudocode
Describes the procedure to operate low-cost ventilator under pressure control

## Pressure control parameters
**Set in GUI**
- PIP: peak inhalation pressure (~20 cm H2O)
- T_insp: inspiratory time to PEEP (~0.5 sec)
- I/E: inspiratory to expiratory time ratio
- bpm: breaths per minute (15 bpm -> 1/15 sec cycle time)
- PIP_time: Target time for PIP. While lungs expand, dP/dt should be PIP/PIP_time
- flow_insp: nominal flow rate during inspiration

**Set by hardware**
- FiO2: fraction of inspired oxygen, set by blender
- max_flow: manual valve at output of blender
- PEEP: positive end-expiratory pressure, set by manual valve

**Derived parameters**
- cycle_time: 1/bpm
- t_insp: inspiratory time, controlled by cycle_time and I/E
- t_exp: expiratory time, controlled by cycle_time and I/E

**Monitored variables**
- Tidal volume: the volume of air entering the lung, derived from flow through t_exp
- PIP: peak inspiratory pressure, set by user in software
- Mean plateau pressure: derived from pressure sensor during inspiration cycle hold (no flow)
- PEEP: positive end-expiratory pressure, set by manual valve

**Alarms**
- Oxygen out of range
- High pressure (tube/airway occlusion)
- Low-pressure (disconnect)
- Temperature out of range 
- Low voltage alarm (if using battery power)
- Tidal volume (expiratory) out of range

## Hardware
**Sensors**
- O2 fraction, in inspiratory path
- Pressure, just before wye to endotrachial tube
- Flow, on expiratory path
- Temperature
- Humidity?

**Actuators**
- Inspiratory valve
    - Proportional or on/off
    - Must maintain low flow during expiratory cycle to maintain PEEP
- Expiratory valve
    - On/off in conjunction with PEEP valve probably OK

## Pressure control loop
1. Begin inhalation
    - v1 Triggered by program every 1/bpm sec
    - v2 triggered by momentary drop in pressure when patient initiates inhalation (technically pressure-assisted control, PAC)
    1. ExpValve.close()
    2. InspValve.set(flow_insp)
2. While PSensor.read() < PIP
    1. Monitor d(PSensor.read())/dt
    2. Adjust flow rate for desired slope with controller
4. Cut flow and hold for t_insp
    1. InspValve.close()
    2. Monitor PSensor.read() and average across this time interval to report mean plateau pressure
5. Begin exhalation and hold for t_exp
    1. InspValve.set(PEEP_flow_rate) (alt: switch to parallel tube with continuous flow)
    2. ExpValve.open()
    3. integrate(FSensor.read()) for t_exhalation to determine V_tidal
6. Repeat from step 1.
