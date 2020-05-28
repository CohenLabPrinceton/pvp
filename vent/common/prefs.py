VENT_DIR = None
LOG_DIR = None
DATA_DIR = None

_CONFIG = {}

def set_pref(key: str, val):
    globals()['_CONFIG'][key] = val

def get_pref(key: str = None):
    """
    Get global configuration value

    Args:
        key (str, None): get configuration value with specific ``key`` .
            if ``None`` , return all config values.
    """
    if key is None:
        return globals()['_CONFIG']
    else:
        try:
            return globals()['_CONFIG'][key]
        except KeyError:
            return None