import os

_CONFIG = {}

_DIRECTORIES = {}
"""
Directories to ensure are created and added to prefs.

    * ``VENT_DIR``: ~/vent - base directory for user storage
    * ``LOG_DIR``: ~/vent/logs - for storage of event and alarm logs
    * ``DATA_DIR``: ~/vent/data - for storage of waveform data
"""
_DIRECTORIES['VENT_DIR'] = os.path.join(os.path.expanduser('~'), 'vent')
_DIRECTORIES['LOG_DIR'] = os.path.join(_DIRECTORIES['VENT_DIR'], 'logs')
_DIRECTORIES['DATA_DIR'] = os.path.join(_DIRECTORIES['VENT_DIR'], 'logs')

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


def make_dirs():
    """
    ensures _DIRECTORIES are created and added to prefs.
    """
    global _DIRECTORIES
    # create directories if they don't exist already
    for dir_name, make_dir in _DIRECTORIES.items():
        if not os.path.exists(make_dir):
            os.mkdir(make_dir)

        set_pref(dir_name, make_dir)

def init():
    """
    Initialize prefs. Called in ``vent.__init__.py`` to ensure prefs are initialized before anything else.
    """

    # add more functions as needed, but probably bad to hardcode default prefs here.
    # pull them up top like _DIRECTORIES

    make_dirs()