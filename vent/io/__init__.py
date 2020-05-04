import pigpio
import configparser
from importlib import import_module
from .devices.sensors import AnalogSensor, SFM3200
from .devices.valves import SolenoidValve, PWMControlValve

class Ventilator:
    """ Hardware Abstraction Layer for vent.io.devices.

    """
    def __init__(self, config_file=None):
        """

        Args:
            config_file (str): Path to the configuration file containing the definitions of specific components on the
            ventilator machine.
        """
        self._pig = pigpio.pi()
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self._adc = getattr(import_module('devices'), self.config['ADC']['type'])(pig=self._pig)
        self._inlet_valve = getattr(
            import_module('devices'),
            self.config['InletValve']['type']
        )(self.config['InletValve']['pin'], self.config['InletValve']['form'])
        self._control_valve = getattr(
            import_module('devices'),
            self.config['ControlValve']['type']
        )(self.config['ControlValve']['pin'], self.config['ControlValve']['form'])
        self._expiratory_valve = getattr(
            import_module('devices'),
            self.config['ExpiratoryValve']['type']
        )(self.config['ExpiratoryValve']['pin'], self.config['ExpiratoryValve']['form'])
        