"""
System preferences are stored in ~/vent/prefs.json
"""

import os
import json
import multiprocessing as mp
from ctypes import c_bool

import logging

_PREF_MANAGER = mp.Manager()

_PREFS = _PREF_MANAGER.dict()

_LOGGER = None # type: logging.Logger

_LOCK = mp.Lock()
"""
:class:`mp.Lock` : Locks access to `prefs_fn`
"""

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

LOADED = mp.Value(c_bool, False)
"""
bool: flag to indicate whether prefs have been loaded (and thus :func:`set_pref` should write to disk.
"""

_DEFAULTS = {
    'PREFS_FN': None,
    'LOGGING_MAX_BYTES': 2 * 2 ** 30, # total
    'LOGGING_MAX_FILES': 5,
    'TIMEOUT': 0.05, # timeout used for timeout decorator
    'HEARTBEAT_TIMEOUT': 0.02, # timeout used in heartbeat between gui and contorller,
    'CONTROLLER_LOOP_UPDATE_TIME': 0,
    'CONTROLLER_LOOPS_UNTIL_UPDATE': 5, # update copied values like get_sensor every n loops,
    'CONTROLLER_RINGBUFFER_SIZE': 100,
    'COUGH_DURATION': 0.1
}
"""
Declare all available parameters and set default values. If no default, set as None. 

* ``PREFS_FN`` - absolute path to the prefs file
* ``VENT_DIR``: ~/vent - base directory for user storage
* ``LOG_DIR``: ~/vent/logs - for storage of event and alarm logs
* ``DATA_DIR``: ~/vent/data - for storage of waveform data
* ``LOGGING_MAX_BYTES`` : the **total** storage space for all loggers -- each logger gets ``LOGGING_MAX_BYTES/len(loggers)`` space
* ``LOGGING_MAX_FILES`` : number of files to split each logger's logs across
"""

def set_pref(key: str, val):
    globals()['_PREFS'][key] = val
    if globals()['LOADED'].value == True:
        save_prefs()

def get_pref(key: str = None):
    """
    Get global configuration value

    Args:
        key (str, None): get configuration value with specific ``key`` .
            if ``None`` , return all config values.
    """
    if key is None:
        return globals()['_PREFS']._getvalue()
    else:
        try:
            return globals()['_PREFS'][key]
        except KeyError:
            return None

def load_prefs(prefs_fn: str):
    """
    Load prefs from a .json prefs file, combining (and overwriting) any existing prefs, and then saves.

    .. note::

        once this function is called, :func:`set_pref` will update the prefs file on disk.
        So if :func:`load_prefs` is called again at any point it should not change prefs.

    Args:
        prefs_fn (str): path of prefs.json
    """
    # create empty dict for new prefs
    new_prefs = {}

    # add any defaults
    new_prefs.update(globals()['_DEFAULTS'])

    # overwrite with any prefs that might exist already
    new_prefs.update(globals()['_PREFS'])

    # finally update from the prefs file
    if os.path.exists(prefs_fn):
        try:
            with globals()['_LOCK']:
                with open(prefs_fn, 'r') as prefs_f:
                    prefs = json.load(prefs_f)

            new_prefs.update(prefs)
        except json.JSONDecodeError as e:
            Warning(f'JSON decoding error in loading prefs, restoring from defaults.\n{e}')

    else:
        RuntimeWarning(f'No prefs file was found at {prefs_fn}, creating new file.')

    # set this filename as the prefs_fn
    new_prefs['PREFS_FN'] = os.path.abspath(prefs_fn)

    # update prefs
    globals()['_PREFS'].update(new_prefs)
    globals()['LOADED'].value = True

    # log
    if globals()['_LOGGER'] is None:
        # if program is just starting, logger shouldn't be created in case LOG_DIR is different than default
        # so it's ok to start it here.
        from vent.common.loggers import init_logger
        globals()['_LOGGER'] = init_logger(__name__)

    globals()['_LOGGER'].info(f'Loaded prefs from {prefs_fn}')

    # save file
    save_prefs()

def save_prefs(prefs_fn: str = None):
    if prefs_fn is None:
        try:
            prefs_fn = globals()['_PREFS']['PREFS_FN']
        except KeyError:
            raise RuntimeError('Asked to save_prefs without prefs_fn, but no PREFS_FN in prefs')

    with globals()['_LOCK']:
        with open(prefs_fn, 'w') as prefs_f:
            json.dump(globals()['_PREFS']._getvalue(), prefs_f)

    globals()['_LOGGER'].info(f'Saved prefs to {prefs_fn}')




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
    # make_dirs should have
    load_prefs(os.path.join(get_pref('VENT_DIR'), 'prefs.json'))



