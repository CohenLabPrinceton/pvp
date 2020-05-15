from collections import OrderedDict as odict
from enum import Enum, auto

# TODO: Zhenyu's job is to make sure the print value is an intepretable string
class ValueName(Enum):
    #Setting that are likely important for future adjustements
    PIP = auto()       # PIP pressure
    PIP_TIME = auto()  # time to reach PIP
    PEEP = auto()      # PEEP pressure
    PEEP_TIME = auto() # time to reach PEEP
    BREATHS_PER_MINUTE = auto()
    INSPIRATION_TIME_SEC = auto()
    IE_RATIO = auto()
    #Settings that are read out, but can not be controlled by software
    FIO2 = auto()
    TEMP = auto()
    HUMIDITY = auto()
    VTE = auto()
    PRESSURE = auto()

controllable_values = {
    ValueName.PIP,
    ValueName.PIP_TIME,
    ValueName.PEEP,
    ValueName.BREATHS_PER_MINUTE,
    ValueName.INSPIRATION_TIME_SEC,
    ValueName.IE_RATIO
}

non_controllable_values = {
    # TODO: is PEEP_TIME controllable? control_module doesn't allow set_control on it
    ValueName.PEEP_TIME,
    ValueName.FIO2,
    ValueName.TEMP,
    ValueName.HUMIDITY,
    ValueName.VTE,
    ValueName.PRESSURE,
}


class Value(object):

    def __init__(self,
                 name: str,
                 units: str,
                 abs_range: tuple,
                 safe_range: tuple,
                 decimals: int,
                 control: bool,
                 sensor: bool,
                 default: (int, float) = None):
        """
        Definition of a value.

        Used by the GUI and control module to set defaults.

        Args:
            name (str): Human-readable name of the value
            units (str): Human-readable description of units
            abs_range (tuple): tuple of ints or floats setting the logical limit of the value,
                eg. a percent between 0 and 100, (0, 100)
            safe_range (tuple): tuple of ints or floats setting the safe ranges of the value,

                note::

                    this is not the same thing as the user-set alarm values,
                    though the user-set alarm values are initialized as ``safe_range``.

            decimals (int): the number of decimals of precision used when displaying the value
        """

        self._name = None
        self._units = None
        self._abs_range = None
        self._safe_range = None
        self._decimals = None
        self._default = None
        self._control = None
        self._sensor = None

        self.name = name
        self.units = units
        self.abs_range = abs_range
        self.safe_range = safe_range
        self.decimals = decimals
        self.control = control
        self.sensor = sensor

        if default is not None:
            self.default = default

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name):
        assert(isinstance(name, str))
        self._name = name

    @property
    def abs_range(self) -> tuple:
        return self._abs_range

    @abs_range.setter
    def abs_range(self, abs_range):
        assert(isinstance(abs_range, tuple) or isinstance(abs_range, list))
        assert(all([isinstance(x, int) or isinstance(x, float) for x in abs_range]))
        self._abs_range = abs_range

    @property
    def safe_range(self) -> tuple:
        return self._safe_range

    @safe_range.setter
    def safe_range(self, safe_range):
        assert(isinstance(safe_range, tuple) or isinstance(safe_range, list))
        assert(all([isinstance(x, int) or isinstance(x, float) for x in safe_range]))
        self._safe_range = safe_range

    @property
    def decimals(self) -> int:
        return self._decimals

    @decimals.setter
    def decimals(self, decimals):
        assert(isinstance(decimals, int))
        self._decimals = decimals

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, default):
        assert(isinstance(default, int) or isinstance(default, float))
        self._default = default

    @property
    def control(self):
        return self._control

    @control.setter
    def control(self, control):
        assert(isinstance(control, bool))
        self._control = control

    @property
    def sensor(self):
        return self._sensor

    @sensor.setter
    def sensor(self, sensor):
        assert(isinstance(sensor, bool))
        self._sensor = sensor

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __getitem__(self, key):
        return self.__getattribute__(key)

    def to_dict(self):
        return {
            'name': self.name,
            'units': self.units,
            'abs_range': self.abs_range,
            'safe_range': self.safe_range,
            'decimals': self.decimals,
            'default': self.default,
            'control': self.control,
            'sensor': self.sensor
                }




VALUES = odict({
    ValueName.FIO2: Value(**{ 'name': 'FiO2',
        'units': '%',
        'abs_range': (0, 100),
        'safe_range': (20, 100),
        'decimals' : 1,
        'control': False,
        'sensor': True
    }),
    ValueName.TEMP: Value(**{
        'name': 'Temp',
        'units': '\N{DEGREE SIGN}C',
        'abs_range': (35, 40),
        'safe_range': (36, 39),
        'decimals': 1,
        'control': False,
        'sensor': True
    }),
    ValueName.HUMIDITY: Value(**{
        'name': 'Humidity',
        'units': '%',
        'abs_range': (0, 100),
        'safe_range': (70, 100),
        'decimals': 1,
        'control': False,
        'sensor': True
    }),
    ValueName.VTE: Value(**{
        'name': 'VTE',
        'units': 'l',  # Unit is liters :-)
        'abs_range': (0, 100),
        'safe_range': (0, 100),
        'decimals': 2,
        'control': False,
        'sensor': True
    }),
    ValueName.PRESSURE: Value(**{
        'name': 'Pressure',
        'units': 'mmH2O',
        'abs_range': (0,70),
        'safe_range': (0,60),
        'decimals': 1,
        'control': False,
        'sensor': True
    }),
    ValueName.IE_RATIO: Value(**{
        'name': 'I:E Ratio',
        'units': '',
        'abs_range': (0, 2),
        'safe_range': (0.33, 1),
        'decimals': 2,
        'control': False,
        'sensor': False
    }),
    ValueName.PIP: Value(**{
        'name': 'PIP', # (Peak Inspiratory Pressure)
        'units': 'cm H2O',
        'abs_range': (0, 70), # FIXME
        'safe_range': (0, 50), # From DrDan https://tigervents.slack.com/archives/C011MRVJS7L/p1588190130492300
        'default': 22,           # FIXME
        'decimals': 1,
        'control': True,
        'sensor': True
    }),
    ValueName.PIP_TIME: Value(**{
        'name': 'PIPt',
        'units': 'seconds',
        'abs_range': (0, 5),  # FIXME
        'safe_range': (0.2, 0.5),  # FIXME
        'default': 0.3,  # FIXME
        'decimals': 1,
        'control': True,
        'sensor': False
    }),
    ValueName.INSPIRATION_TIME_SEC: Value(**{
        'name': 'INSPt',
        'units': 'seconds',
        'abs_range': (0, 5),  # FIXME
        'safe_range': (1, 3.0),  # FIXME
        'default': 2.0,  # FIXME
        'decimals': 1,
        'control': True,
        'sensor': True
    }),
    ValueName.PEEP: Value(**{
        'name': 'PEEP', #  (Positive End Expiratory Pressure)
        'units': 'cm H2O',
        'abs_range': (0, 20),  # FIXME
        'safe_range': (0, 16), # From DrDan https://tigervents.slack.com/archives/C011MRVJS7L/p1588190130492300
        'default': 5,            # FIXME
        'decimals': 1,
        'control': True,
        'sensor': True
    }),
    ValueName.PEEP_TIME: Value(**{
        'name': 'PEEPt',
        'units': 'seconds',
        'abs_range': (0, 2),  # FIXME
        'safe_range': (0, 1.0),  # FIXME
        'default': 0.5,  # FIXME
        'decimals': 1,
        'control': True,
        'sensor': False
    }),
    ValueName.BREATHS_PER_MINUTE: Value(**{
        'name': 'RR', # Daniel re: FDA labels
        'units': 'BPM', # Daniel re: FDA labels
        'abs_range': (0, 50), # FIXME
        'safe_range': (10, 30), # Stanford's socs https://www.vent4us.org/technical
        'default': 17,            # FIXME
        'decimals': 1,
        'control': True,
        'sensor': True
    }),
})

SENSOR = odict({
    k:v for k, v in VALUES.items() if v.sensor == True
})
"""
Values to monitor but not control. 

Used to set alarms for out-of-bounds sensor values. These should be sent from the control module and not computed.::

    {
        'name' (str):  Human readable name,
        'units' (str): units string, (like degrees or %),
        'abs_range' (tuple): absolute possible range of values,
        'safe_range' (tuple): range outside of which a warning will be raised,
        'decimals' (int): The number of decimals of precision this number should be displayed with
    }
"""


CONTROL = odict({
    k: v for k, v in VALUES.items() if v.control == True
})
"""
Values to control but not monitor.

Sent to control module to control operation of ventilator.::

    {
        'name' (str):  Human readable name,
        'units' (str): units string, (like degrees or %),
        'abs_range' (tuple): absolute possible range of values,
        'safe_range' (tuple): range outside of which a warning will be raised,
        'default' (int, float): the default value of the parameter,
        'decimals' (int): The number of decimals of precision this number should be displayed with
    }
"""

LIMITS = {

}
"""
Values that are dependent on other values::

    {
        "dependent_value": (
            ['value_1', 'value_2'],
            callable_returning_boolean
        }
    }
    
Where the first argument in the tuple is a list of the values that will be 
given as argument to the ``callable_returning_boolean`` which will return
whether (``True``) or not (``False``) a value is allowed.
"""
