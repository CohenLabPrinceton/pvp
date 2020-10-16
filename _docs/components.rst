Components
==================

.. raw:: html
    :file: /images/Schematic_v2.svg
	
.. toctree::
   :maxdepth: 4
   :caption: Hardware:

   Hardware Design <components.design>
   Actuator Selection <components.actuators>
   Sensor Selection <components.sensors>

Hardware Design
-------------------

The following is a guided walk through the main hardware components that comprise the respiratory circuit,
roughly following the flow of gas from the system inlet, to the patient, then out through the expiratory valve.

**Hospital gas blender.**
At the inlet to the system, we assume the presence of a commercial-off-the-shelf (COTS) gas blender. These devices mix air from U.S. standard medical air and O2 as supplied at the hospital wall at a pressure of around 50 psig. The device outlet fitting may vary, but we assume a male O2 DISS fitting (NIST standard). In field hospitals, compressed air and O2 cylinders may be utilized in conjunction with a gas blender, or a low-cost Venturi-based gas blender. We additionally assume that the oxygen concentration of gas supplied by the blender can be manually adjusted. Users will be able to monitor the oxygen concentration level in real-time on the device GUI. 

**Fittings and 3D printed adapters.**
Standardized fittings were selected whenever possible to ease part sourcing in the event that engineers replicating the system need to swap out a component, possibly as the result of sourcing constraints within their local geographic area. Many fittings are American national pipe thread (NPT) standard, or conform to the respiratory circuit tubing standards (15mm I.D./22 mm O.D.). To reduce system complexity and sourcing requirements of specialized adapters, a number of connectors, brackets, and manifold are provided as 3D printable parts. All 3D printed components were print-tested on multiple 3D printers, including consumer-level devices produced by MakerBot, FlashForge, and Creality3D. 

**Pressure regulator.**
The fixed pressure regulator near the inlet of the system functions to step down the pressure supplied to the proportional valve to a safe and consistent set level of 50 psi. It is essential to preventing the over-pressurization of the system in the event of a pressure spike, eases the real-time control task, and ensures that downstream valves are operating within the acceptable range of flow conditions.

**Proportional valve.**
The proportional valve is the first of two actuated components in the system. It enables regulation of the gas flow to the patient via the PID control framework, described in a following section. A proportional valve upstream of the respiratory circuit enables the controller to modify the inspiratory time, and does not present wear limitations like pinch-valves and other analogous flow-control devices. The normally closed configuration was selected to prevent over-pressurization of the lungs in the event of system failure. 

**Sensors.**
The system includes an oxygen sensor for monitoring oxygen concentration of the blended gas supplied to the patient, a pressure sensor located proximally to the patient mouth along the respiratory circuit, and a spirometer, consisting of a plastic housing (D-Lite, GE Healthcare) with an attached differential pressure sensor, to measure flow. Individual sensor selection will be described in more detail in a following section. The oxygen sensor read-out is used to adjust the manual gas blender and to trigger alarm states in the event of deviations from a setpoint. The proximal location of the primary pressure sensor was selected due to the choice of a pressure-based control strategy, specifically to ensure the most accurate pressure readings with respect to the patient's lungs. Flow estimates from the single expiratory flow sensor are not directly used in the pressure-based control scheme, but enable the device to trigger appropriate alarm states in order to avoid deviations from the tidal volume of gas leaving the lungs during expiration. The device does not currently monitor gas temperature and humidity due to the use of an HME rather than a heated humidification system.

**Pressure relief.**
A critical safety component is the pressure relief valve (alternatively called the "pressure release valve", or "pressure safety valve"). The proportional valve is controlled to ensure that the pressure of the gas supplied to the patient never rises above a set maximum level. The relief valve acts as a backup safety mechanism and opens if the pressure exceeds a safe level, thereby dumping excess gas to atmosphere. Thus, the relief valve in this system is located between the proportional valve and the patient respiratory circuit. The pressure relief valve we source cracks at 1 psi (approx 70 cm H2O).

**Standard respiratory circuit.**
The breathing circuit which connects the patient to the device is a standard respiratory circuit: the flexible, corrugated plastic tubing used in commercial ICU ventilators. Because this system assumes the use of an HME/F to maintain humidity levels of gas supplied to the patient, specialized heated tubing is not required. 
 
**Anti-suffocation check valve.** 
A standard ventilator check valve (alternatively called a "one-way valve") is used as a secondary safety component in-line between the proportional valve and the patient respiratory circuit. The check valve is oriented such that air can be pulled into the system in the event of system failure, but that air cannot flow outward through the valve. A standard respiratory circuit check valve is used because it is a low-cost, readily sourced device with low cracking pressure and sufficiently high valve flow coefficient (Cv). 
 
**Bacterial filters.**
A medical-grade electrostatic filter is placed on either end of the respiratory circuit. These function as protection against contamination of device internals and surroundings by pathogens and reduces the probability of the patient developing a hospital-acquired infection. The electrostatic filter presents low resistance to flow in the airway.
 
**HME.**
A Heat and Moisture Exchanger (HME) is placed proximal to the patient. This is used to passively humidify and warm air inspired by the patient. HMEs are the standard solution in the absence of a heated humidifier. While we evaluated the use of an HME/F which integrates a bacteriological/viral filter, use of an HME/F increased flow resistance and compromised pressure control. 

**Pressure sampling filter.**
Proximal airway pressure is sampled at a pressure port near the wye adapter, and measured by a pressure sensor on the sensor PCB. To protect the sensor and internals of the ventilator, an additional 0.2 micron bacterial/viral filter is placed in-line between the proximal airway sampling port and the pressure sensor. This is also a standard approach in many commercial ventilators. 

**Expiratory solenoid.**
The expiratory solenoid is the second of two actuated components in the system. When this valve is open, air bypasses the lungs, thereby enabling the lungs to de-pressurize upon expiration. When the valve is closed, the lungs may inflate or hold a fixed pressure, according to the control applied to the proportional valve. The expiratory flow control components must be selected to have a sufficiently high valve flow coefficient (Cv) to prevent obstruction upon expiration. This valve is also selected to be normally open, to enable the patient to expire in the event of system failure. 

**Manual PEEP valve.**
The PEEP valve is a component which maintains the positive end-expiratory pressure (PEEP) of the system above atmospheric pressure to promote gas exchange to the lungs. A typical COTS PEEP valve is a spring-based relief valve which exhausts when pressure within the airway exceeds a fixed limit. This limit is manually adjusted via compression of the spring. Various low-cost alternatives to a COTS mechanical PEEP valve exist, including the use of a simple water column, in the event that PEEP valves become challenging to source. We additionally provide a 3D printable PEEP valve alternative which utilizes a thin membrane, rather than a spring, to maintain PEEP. 

Actuator Selection
---------------------

When planning actuator selection, it was necessary to consider the placement of the valves within the larger system. Initially, we anticipated sourcing a proportional valve to operate at very low pressures (0-50 cm H20) and sufficiently high flow (over 120 LPM) of gas within the airway. However, a low-pressure, high-flow regime proportional valve is far more expensive than a proportional valve which operates within high-pressure (~50 psi), high-flow regimes. Thus, we designed the device such that the proportional valve would admit gas within the high-pressure regime and regulate air flow to the patient from the inspiratory airway limb. 
Conceivably, it is possible to control the air flow to the patient with the proportional valve alone. However, we couple this actuator with a solenoid and PEEP valve to ensure robust control during PIP (peak inspiratory pressure) and PEEP hold, and to minimize the loss of O2-blended gas to the atmosphere, particularly during PIP hold.


**Proportional valve sourcing.**
Despite designing the system such that the proportional valve could be sourced for operation within a normal inlet pressure regime (approximately 50 psi), it was necessary to search for a valve with a high enough valve flow coefficient (Cv) to admit sufficient gas to the patient. We sourced an SMC PVQ31-5G-23-01N valve with stainless steel body in the normally-closed configuration. This valve has a port size of 1/8" (Rc) and has previously been used for respiratory applications. Although the manufacturer does not supply Cv estimates, we empirically determined that this valve is able to flow sufficiently for the application.

**Expiratory valve sourcing.**
When sourcing the expiratory solenoid, it was necessary to choose a device with a sufficiently high valve flow coefficient (Cv) which could still actuate quickly enough to enable robust control of the gas flow. A reduced Cv in this portion of the circuit would restrict the ability of the patient to exhale. Initially, a number of control valves were sourced for their rapid switching speeds and empirically tested, as Cv estimates are often not provided by valve manufacturers. Ultimately, however, we selected a process valve in lieu of a control valve to ensure the device would flow sufficiently well, and the choice of valve did not present problems when implementing the control strategy. The SMC VXZ250HGB solenoid valve in the normally-open configuration was selected. The valve in particular was sourced partially due to its large port size (3/4" NPT). If an analogous solenoid with rapid switching speed and large Cv cannot be sourced, engineers replicating our device may consider the use of pneumatically actuated valves driven from air routed from a take-off downstream of the pressure regulator. 

**Manual PEEP valve sourcing.**
The PEEP valve is one of the few medical-specific COTS components in the device. The system configuration assumes the use of any ventilator-specific PEEP valve (Teleflex, CareFusion, etc.) coupled with an adapter to the standard 22 mm respiratory circuit tubing. In anticipation of potential supply chain limitations, as noted previously, we additionally provide the CAD models of a 3D printable PEEP valve. 

Sensor Selection
---------------------
We selected a minimal set of sensors with analog outputs to keep the system design sufficiently adaptable. If there were a part shortage for a specific pressure sensor, for example, any readily available pressure sensor with an analog output could be substituted into the system following a simple adjustment in calibration in the controller. Our system uses three sensors: an oxygen sensor, an airway pressure sensor, and a flow sensor with availability for a fourth addition, all interfaced with the Raspberry Pi via a 4-channel ADC (Adafruit ADS1115) through an I2C connection.

**Oxygen sensor.**
We selected an electrochemical oxygen sensor (Sensironics SS-12A) designed for the range of FiO2 used for standard ventilation and in other medical devices. The cell is self-powered, generating a small DC voltage (13-16 mV) that is linearly proportional to oxygen concentration. The output signal is amplified by an instrumentation amplifier interfacing the sensor with the Raspberry Pi controller (see electronics). This sensor is a wear part with a lifespan of about 6 years under operation at ambient air; therefore under continuous ventilator operation with oxygen-enriched gas, it will need to be replaced more frequently. This part can be replaced with any other medical O2 sensor provided calibration is performed given that these parts are typically sold as raw sensors, with a 3-pin molex interface. Moreover, the sensor we specify is compatible with a range of medical O2 sensors, including the Analytical Industries PSR-11-917-M or the Puritan Bennett 4-072214-00, so we anticipate abundant sourcing options.

**Airway pressure sensor.**
We selected a pressure sensor with a few key characteristics in mind: 1) the sensor had to be compatible with the 5V supply of the Raspberry Pi, 2) the sensor's input pressure range had conform to the range of pressures possible in our device (up to 70 cm H2O, the pressure relief valve's cutoff), and 3) the sensor's response time had to be sufficiently fast. We selected the amplified middle pressure sensor from Amphenol (1 PSI-D-4V), which was readily available, with a measurement range up to 70 cm H2O and an analog output voltage span of 4 V. Moreover, the decision to utilize an analog sensor is convenient for engineers replicating the design, as new analog sensors can be swapped in without extensive code and electronics modifications, as in the case of I2C devices which require modifications to hardware addresses. Other pressure sensors from this Amphenol line can be used as replacements if necessary.

**Spirometer.**
Because flow measurement is essential for measuring tidal volume during pressure-controlled ventilation, medical flow sensor availability was extremely limited during the early stages of the 2020 COVID-19 pandemic, and supply is still an issue. For that reason, we looked for inexpensive, more easily sourced spirometers to use in our system. We used the GE D-Lite spirometer, which is a mass-produced part and has been used in hospitals for nearly 30 years. The D-Lite sensor is inserted in-line with the flow of gas on the expiratory limb, and two ports are used to measure the differential pressure drop resulting from flow through a narrow physical restriction. The third pressure-measurement port on the D-Lite is blocked by a male Luer cap, but this could be used as a backup pressure measurement port if desired. An Amphenol 5 INCH-D2-P4V-MINI was selected to measure the differential pressure across the two D-Lite takeoffs. As with the primary (absolute) pressure sensor, this sensor was selected to conform to the voltage range of the Raspberry Pi, operate within a small pressure range, and have a sufficiently fast response time (partially as a function of the analog-to-digital converter). Also, this analog sensor can be readily replaced with a similar analog sensor without substantial code/electronics modifications. 

