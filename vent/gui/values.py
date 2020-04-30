from collections import OrderedDict as odict
from vent.common.message import ValueName
from vent.gui import styles

class Value(object):

    def __init__(self,
                 name: str,
                 units: str,
                 abs_range: tuple,
                 safe_range: tuple,
                 decimals: int,
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

        self.name = name
        self.units = units
        self.abs_range = abs_range
        self.safe_range = safe_range
        self.decimals = decimals

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

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __getitem__(self, key):
        return self.__getattribute__(key)








MONITOR = odict({
    ValueName.FIO2: Value(**{ 'name': 'FiO2',
        'units': '%',
        'abs_range': (0, 100),
        'safe_range': (60, 100),
        'decimals' : 1
    }),
    ValueName.TEMP: Value(**{
        'name': 'Temp',
        'units': '\N{DEGREE SIGN}C',
        'abs_range': (0, 50),
        'safe_range': (20, 30),
        'decimals': 1
    }),
    ValueName.HUMIDITY: Value(**{
        'name': 'Humidity',
        'units': '%',
        'abs_range': (0, 100),
        'safe_range': (20, 75),
        'decimals': 1
    }),
    ValueName.VTE: Value(**{
        'name': 'VTE',
        'units': '%',
        'abs_range': (0, 100),
        'safe_range': (20, 80),
        'decimals': 1
    })
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
    ValueName.PIP: Value(**{
        'name': 'PIP', # (Peak Inspiratory Pressure)
        'units': 'cmH2O',
        'abs_range': (10, 30), # FIXME
        'safe_range': (20,24), # FIXME
        'default': 22,           # FIXME
        'decimals': 1          # FIXME
    }),
    ValueName.PIP_TIME: Value(**{
        'name': 'PIPt', #  (Peak Inspiratory Pressure)
        'units': 'seconds',
        'abs_range': (0, 1),  # FIXME
        'safe_range': (0.2, 0.5),  # FIXME
        'default': 0.3,  # FIXME
        'decimals': 1  # FIXME
    }),
    ValueName.PEEP: Value(**{
        'name': 'PEEP', #  (Positive End Expiratory Pressure)
        'units': 'cmH2O',
        'abs_range': (0, 10),  # FIXME
        'safe_range': (4,6), # FIXME
        'default': 5,            # FIXME
        'decimals': 1           # FIXME
    }),
    ValueName.BREATHS_PER_MINUTE: Value(**{
        'name': 'Breath Rate',
        'units': 'breaths/min',
        'abs_range': (0, 50), # FIXME
        'safe_range': (16, 19), # FIXME
        'default': 17,            # FIXME
        'decimals': 1           # FIXME
    }),
    ValueName.INSPIRATION_TIME_SEC: Value(**{
        'name': 'Inspiration Time',
        'units': 'seconds',
        'abs_range': (0, 5),  # FIXME
        'safe_range': (1, 3.0),  # FIXME
        'default': 2.0,  # FIXME
        'decimals': 1  # FIXME
    }),
    # 'ie': Value(**{
    #     'name': 'I:E',
    #     'units': '',
    #     'abs_range': (0, 100),  # FIXME
    #     'safe_range': (0, 100),  # FIXME
    #     'default': 80,  # FIXME
    #     'decimals': 1  # FIXME
    # })
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


PLOTS = odict({
        # 'flow': {
        #     'name': 'Flow (L/s)',
        #     'abs_range': (0, 100),
        #     'safe_range': (20, 80),
        #     'color': styles.SUBWAY_COLORS['yellow'],
        # },

        'pressure': {
            'name': 'Pressure (mmHg)',
            'abs_range': (0, 30),
            'safe_range': (5, 20),
            'color': styles.SUBWAY_COLORS['orange'],
        },
        'temp': {
            'name': 'Temperature (C)',
            'abs_range': (20,50),
            'safe_range' :(35,40),
            'color': styles.SUBWAY_COLORS['red']
        },
        'humidity': {
            'name': 'Humidity (% H2O)',
            'abs_range': (70, 100),
            'safe_range': (90, 100),
            'color': styles.SUBWAY_COLORS['blue']
        }
    })
"""
Values to plot.

Should have the same key as some key in :data:`~.defaults.MONITOR`. If it does,
it will be mutually connected to the resulting :class:`.gui.widgets.Monitor_Value`
such that the set limit range is updated when the horizontal bars on the plot are updated.::

    {
        'name' (str): title of plot,
        'abs_range' (tuple): absolute limit of plot range,
        'safe_range' (tuple): safe range, will be discolored outside of this range,
        'color' (str): hex color of line (like "#FF0000")
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

