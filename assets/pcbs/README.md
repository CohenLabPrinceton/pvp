# Content of pcbs
This folder contains PCB design files for the PVP1. There are two boards: one for the Actuators and one for the Sensors. They connect to the the Raspberry Pi 4 via 40-pin stackable headers. Uploaded as KiCad project files except where noted.

# Actuator Board (actuators-rev2)
	- Interfaces the Raspberry Pi to the inspiratory and expiratory valves through an array of solenoid drivers (ULN2003A Darlington transistor array)
	- Revision history:
		- rev2 (6/14/2020): Present version. Removed one screw terminal and the adjustable headers. Four of the darlington pairs are tied together to drive the expiratory valve, and three are tied together to drive the proportional valve. These connections are now permanent traces on the PCB.
		- rev1 (5/13/2020): Initial version. Three screw terminals intended to connect to valves. Included extra jumpers J4, J8, J9, and J10 designed to tie together Darlington pairs for felxibility if more current was needed to drive a particular valve.
		
# Sensor Board (pressure-rev2)
	- Interfaces four analog output sensors with the Raspberry Pi via I^2C commands to a 12-bit 4-channel ADC (Adafruit ADS1015)
	- Revision history:
		- rev2 (6/14/2020): Present version. Added a third auxiliary pressure sensor, and revised analog front-end for oxygen sensor. Added a TL7660 charge pump to provide a dual-sided supply to the INA126 instrumentation amplifier. Connections for I2C resistors removed.
		- rev1 (4/27/2020): Initial version. Shared as Gerber production files. Connections included for two pressure sensors, oxygen sensor, and flow sensor.