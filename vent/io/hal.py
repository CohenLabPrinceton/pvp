""" Module for interacting with physical and/or simulated devices installed on the ventilator.

"""
import configparser
from importlib import import_module

import pigpio

from .devices.sensors import Sensor


class Hal:
    """ Hardware Abstraction Layer for ventilator hardware.
    Defines a common API for interacting with the sensors & actuators on the ventilator. The types of devices installed
    on the ventilator (real or simulated) are specified in a configuration file.
    """

    def __init__(self, config_file=None):
        """ Initializes HAL from config_file.
            For each section in config_file, imports the class <type> from module <module>, and sets attribute
            self.<section> = <type>(**opts), where opts is a dict containing all of the options in <section> that are not
            <type> or <section>. For example, upon encountering the following entry in config_file.ini:

                [adc]
                type   = ADS1115
                module = devices
                i2c_address = 0x48
                i2c_bus = 1

            The Hal will:
                1) Import vent.io.devices.ADS1115 as a local variable:
                        class_ = getattr(import_module('.devices', 'vent.io'), 'ADS1115')

                2) Instantiate an ADS1115 object with the arguments defined in config_file and set it as an attribute:
                        self._adc = class_(pig=self.-pig,i2c_address=0x48,i2c_bus=1)

            Note: RawConfigParser.optionxform() is overloaded here s.t. options are case sensitive (they are by default
            case insensitive). This is necessary due to the kwarg MUX which is so named for consistency with the config
            registry documentation in the ADS1115 datasheet. For example, A P4vMini pressure_sensor on pin A0 (MUX=0)
            of the ADC is passed arguments like:

            analog_sensor = AnalogSensor(
                pig=self._pig,
                adc=self._adc,
                MUX=0,
                offset_voltage=0.25,
                output_span = 4.0,
                conversion_factor=2.54*20
            )

        Args:
            config_file (str): Path to the configuration file containing the definitions of specific components on the
                ventilator machine. (e.g., config_file = "vent/io/config/devices.ini")
        """
        self._setpoint = 0.0
        self._adc = object
        self._inlet_valve = object
        self._control_valve = object
        self._expiratory_valve = object
        self._pressure_sensor = object
        self._secondary_pressure_sensor = object
        self._flow_sensor = object
        self._pig = pigpio.pi()
        self.config = configparser.RawConfigParser()
        self.config.optionxform = lambda option: option
        self.config.read(config_file)
        for section in self.config.sections():
            sdict = dict(self.config[section])
            class_ = getattr(import_module('.'+sdict['module'], 'vent.io'), sdict['type'])
            opts = {key: sdict[key] for key in sdict.keys() - ('module', 'type')}
            setattr(self, '_'+section, class_(pig=self._pig, **opts))

    # TODO: Need exception handling whenever inlet valve is opened

    @property
    def pressure(self) -> float:
        """ Returns the pressure from the primary pressure sensor.
        """
        self._pressure_sensor.update()
        return self._pressure_sensor.get()

    @property
    def secondary_pressure(self) -> float:
        """ Returns the pressure from the secondary pressure sensor, if so equipped.
        If a secondary pressure sensor is not defined, raises a RuntimeWarning
        """
        if isinstance(self._secondary_pressure_sensor, Sensor):
            self._secondary_pressure_sensor.update()
            return self._secondary_pressure_sensor.get()
        else:
            raise RuntimeWarning('Secondary pressure sensor not instantiated. Check your "devices.ini" file.')

    @property
    def flow(self) -> float:
        """ The measured flow rate.
        """
        self._flow_sensor.update()
        return self._flow_sensor.get()

    @property
    def setpoint(self) -> float:
        """ The currently requested flow

        Returns:
            float: 0<=setpoint<=1; The current set-point for flow control as a proportion of the maximum.
        """
        return self._setpoint

    @setpoint.setter
    def setpoint(self, value: float):
        """

        Args:
            value: Requested flow, as a proportion of maximum. Must be in [0, 1].
        """
        if 0 <= value <= 1:
            raise ValueError('setpoint must be a number between 0 and 1')
        if value > 0 and not self._inlet_valve.isopen():
            self._inlet_valve.open()
        elif value == 0 and self._inlet_valve.isopen():
            self._inlet_valve.close()
        self._control_valve.setpoint = value