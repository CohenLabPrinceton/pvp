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


CONTROL = {
        'oxygen': {
            'name': 'O2 Concentration',
            'units': '%',
            'abs_range': (0, 100),
            'value': 80,
            'decimals': 1
        },
        'temperature': {
            'name': 'Temperature',
            'units': '\N{DEGREE SIGN}C',
            'abs_range': (0, 50),
            'value': 23,
            'decimals': 1
        },
    }

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