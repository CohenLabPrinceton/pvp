from collections import OrderedDict as odict

from vent.gui import styles

MONITOR = odict({
    'oxygen': {
        'name': 'O2 Concentration',
        'units': '%',
        'abs_range': (0, 100),
        'safe_range': (60, 100),
        'decimals' : 1
    },
    'temperature': {
        'name': 'Temperature',
        'units': '\N{DEGREE SIGN}C',
        'abs_range': (0, 50),
        'safe_range': (20, 30),
        'decimals': 1
    },
    'humidity': {
        'name': 'Humidity',
        'units': '%',
        'abs_range': (0, 100),
        'safe_range': (20, 75),
        'decimals': 1
    },
    'vte': {
        'name': 'VTE',
        'units': '%',
        'abs_range': (0, 100),
        'safe_range': (20, 80),
        'decimals': 1
    }
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
    'pip': {
        'name': 'PIP (Peak Inspiratory Pressure)',
        'units': 'cmH2O',
        'abs_range': (0, 100), # FIXME
        'safe_range': (0,100), # FIXME
        'value': 80,           # FIXME
        'decimals': 1          # FIXME
    },
    'peep': {
        'name': 'PEEP (Positive End Expiratory Pressure)',
        'units': 'cmH2O',
        'abs_range': (0, 100),  # FIXME
        'safe_range': (0, 100), # FIXME
        'value': 80,            # FIXME
        'decimals': 1           # FIXME
    },
    'ie': {
        'name': 'I:E',
        'units': 'inspiratory/expiratory time',
        'abs_range': (0, 100),  # FIXME
        'safe_range': (0, 100), # FIXME
        'value': 80,            # FIXME
        'decimals': 1           # FIXME
    },
    'bpm': {
        'name': 'Breath Rate',
        'units': 'breaths/min',
        'abs_range': (0, 100),  # FIXME
        'safe_range': (0, 100), # FIXME
        'value': 80,            # FIXME
        'decimals': 1           # FIXME
    }
})
"""
Values to control but not monitor.

Sent to control module to control operation of ventilator.::

    {
        'name' (str):  Human readable name,
        'units' (str): units string, (like degrees or %),
        'abs_range' (tuple): absolute possible range of values,
        'safe_range' (tuple): range outside of which a warning will be raised,
        'value' (int, float): the default value of the parameter,
        'decimals' (int): The number of decimals of precision this number should be displayed with
    }
"""


PLOTS = {
        'flow': {
            'name': 'Flow (L/s)',
            'abs_range': (0, 100),
            'safe_range': (20, 80),
            'color': styles.SUBWAY_COLORS['yellow'],
        },
        'pressure': {
            'name': 'Pressure (mmHg)',
            'abs_range': (0, 100),
            'safe_range': (20, 80),
            'color': styles.SUBWAY_COLORS['orange'],
        }
    }
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

