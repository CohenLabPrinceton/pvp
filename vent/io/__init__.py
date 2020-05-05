from typing import Any, Tuple

import pigpio
import configparser
from importlib import import_module
from .devices.sensors import AnalogSensor, SFM3200
from .devices.valves import OnOffValve, PWMControlValve


class Ventilator:
    """ Hardware Abstraction Layer for vent.io.devices.
    """

    def __init__(self, config_file=None):
        """
            Note: RawConfigParser.optionxform() is overloaded here s.t. options are case sensitive. This is necessary
            due to MUX.
        Args:
            config_file (str): Path to the configuration file containing the definitions of specific components on the
            ventilator machine.
        """
        self._setpoint = 0.0
        self._adc = object
        self._inlet_valve = object
        self._control_valve = object
        self._expiratory_valve = object
        self._pressure_sensor = object
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
        """ Returns the pressure from the primary pressure sensor
        """
        self._pressure_sensor.update()
        return self._pressure_sensor.get()

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

