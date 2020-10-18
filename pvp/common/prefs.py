import os
import time
import json
import multiprocessing as mp
from ctypes import c_bool

import logging

_PREF_MANAGER = mp.Manager()
"""
The :class:`multiprocessing.Manager` that stores prefs during system operation
"""

_PREFS = _PREF_MANAGER.dict()
"""
The dict created by :data:`.prefs._PREF_MANAGER` to store prefs.
"""

_LOGGER = None # type: logging.Logger
"""
A :class:`logging.Logger` to log pref init and setting events
"""

_LOCK = mp.Lock()
"""
:class:`mp.Lock` : Locks access to `prefs_fn`
"""

_DIRECTORIES = {}
"""
Directories to ensure are created and added to prefs.

    * ``VENT_DIR``: ~/pvp - base directory for user storage
    * ``LOG_DIR``: ~/pvp/logs - for storage of event and alarm logs
    * ``DATA_DIR``: ~/pvp/data - for storage of waveform data
"""
_DIRECTORIES['VENT_DIR'] = os.path.join(os.path.expanduser('~'), 'pvp')
_DIRECTORIES['LOG_DIR'] = os.path.join(_DIRECTORIES['VENT_DIR'], 'logs')
_DIRECTORIES['DATA_DIR'] = os.path.join(_DIRECTORIES['VENT_DIR'], 'logs')

LOADED = mp.Value(c_bool, False)
"""
bool: flag to indicate whether prefs have been loaded (and thus :func:`set_pref` should write to disk).

uses a :class:`multiprocessing.Value` to be thread and process safe.
"""

_DEFAULTS = {
    'PREFS_FN': None,
    'TIME_FIRST_START' : None,
    'LOGGING_MAX_BYTES': 2 * 2 ** 30, # total
    'LOGGING_MAX_FILES': 5,
    'LOGLEVEL': 'WARNING',
    'TIMEOUT': 0.05, # timeout used for timeout decorator
    'HEARTBEAT_TIMEOUT': 0.02, # timeout used in heartbeat between gui and contorller,
    'GUI_STATE_FN': 'gui_state.json',
    'GUI_UPDATE_TIME': 0.05,
    'ENABLE_DIALOGS': True, # enable _all_ dialogs -- for testing on virtual frame buffer
    'ENABLE_WARNINGS': True, # enable user warnings and confirmations
    'CONTROLLER_MAX_FLOW': 10,
    'CONTROLLER_MAX_PRESSURE': 100,
    'CONTROLLER_MAX_STUCK_SENSOR': 5,  # Choose such that O2 doesn't constantly trigger a stuck sensor; oxygen read every ~2 seconds; see 'OXYGEN_READ_FREQUENCY' below
    'CONTROLLER_LOOP_UPDATE_TIME': 0.0,
    'CONTROLLER_LOOP_UPDATE_TIME_SIMULATOR': 0.005,
    'CONTROLLER_LOOPS_UNTIL_UPDATE': 1,  # update copied values like get_sensor every n loops,
    'CONTROLLER_RINGBUFFER_SIZE': 100,
    'COUGH_DURATION': 0.1,
    'BREATH_PRESSURE_DROP': 4,
    'BREATH_DETECTION': True,
    'OXYGEN_READ_FREQUENCY': 2

}
"""
Declare all available parameters and set default values. If no default, set as None. 

* ``PREFS_FN`` - absolute path to the prefs file
* ``TIME_FIRST_START`` - time when the program has been started for the first time
* ``VENT_DIR``: ~/pvp - base directory for user storage
* ``LOG_DIR``: ~/pvp/logs - for storage of event and alarm logs
* ``DATA_DIR``: ~/pvp/data - for storage of waveform data
* ``LOGGING_MAX_BYTES`` : the **total** storage space for all loggers -- each logger gets ``LOGGING_MAX_BYTES/len(loggers)`` space (2GB by default)
* ``LOGGING_MAX_FILES`` : number of files to split each logger's logs across (default: 5)
* ``LOGLEVEL``: One of ``('DEBUG', 'INFO', 'WARNING', 'EXCEPTION')`` that sets the minimum log level that is printed and written to disk
* ``TIMEOUT``: timeout used for timeout decorators on time-sensitive operations (in seconds, default 0.05)
* ``HEARTBEAT_TIMEOUT``: Time between heartbeats between GUI and controller after which contact is assumed to be lost (in seconds, default 0.02)
* ``GUI_STATE_FN``: Filename of gui control state file, relative to ``VENT_DIR`` (default: gui_state.json)
* ``GUI_UPDATE_TIME``: Time between calls of :meth:`.PVP_Gui.update_gui` (in seconds, default: 0.05)
* ``ENABLE_DIALOGS``: Enable all GUI dialogs -- set as False when testing on virtual frame buffer that doesn't support them (default: True and should stay that way)
* ``ENABLE_WARNINGS``: Enable user warnings and value change confirmations (default: True)
* ``CONTROLLER_MAX_FLOW``: Maximum flow, above which the controller considers a sensor error (default: 10)
* ``CONTROLLER_MAX_PRESSURE``: Maximum pressure, above which the controller considers a sensor error (default: 100)
* ``CONTROLLER_MAX_STUCK_SENSOR``: Max amount of time (in s) before considering a sensor stuck (default: 0.2)
* ``CONTROLLER_LOOP_UPDATE_TIME``: Amount of time to sleep in between controller update times when using :class:`.ControlModuleDevice` (default: 0.0)
* ``CONTROLLER_LOOP_UPDATE_TIME_SIMULATOR``: Amount of time to sleep in between controller updates when using :class:`.ControlModuleSimulator` (default: 0.005)
* ``CONTROLLER_LOOPS_UNTIL_UPDATE``: Number of controller loops in between updating its externally-available ``COPY`` attributes retrieved by :meth:`.ControlModuleBase.get_sensor` et al
* ``CONTROLLER_RINGBUFFER_SIZE``: Maximum number of breath cycle records to be kept in memory (default: 100)
* ``COUGH_DURATION``: Amount of time the high-pressure alarm limit can be exceeded and considered a cough (in seconds, default: 0.1)
* ``BREATH_PRESSURE_DROP``: Amount pressure can drop below set PEEP before being considered an autonomous breath when in breath detection mode
* ``BREATH_DETECTION``: Whether the controller should detect autonomous breaths in order to reset ventilation cycles (default: True)
"""

def set_pref(key: str, val):
    """
    Sets a pref in the manager and, if :data:`.prefs.LOADED` is True, calls :func:`.prefs.save_prefs`

    Args:
        key (str): Name of pref key
        val: Value to set
    """
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
    if key is None: # pragma: no cover
        return globals()['_PREFS']._getvalue()
    else:
        try:
            return globals()['_PREFS'][key]
        except KeyError: # pragma: no cover
            return None

def load_prefs(prefs_fn: str):
    """
    Load prefs from a .json prefs file, combining (and overwriting) any existing prefs, and then saves.

    Called on pvp import by :func:`.prefs.init`

    Also initializes :data:`.prefs._LOGGER`

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
        except json.JSONDecodeError as e: # pragma: no cover
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
        from pvp.common.loggers import init_logger
        globals()['_LOGGER'] = init_logger(__name__)

    globals()['_LOGGER'].info(f'Loaded prefs from {prefs_fn}')

    # save file
    save_prefs()

    # Make sure startime is set if the program is run for the first time
    if get_pref('TIME_FIRST_START') is None:
        set_pref('TIME_FIRST_START', time.time()) 
        globals()['_LOGGER'].info(f'Starttime set: ' + str(time.time()))


def save_prefs(prefs_fn: str = None):
    """
    Dumps loaded prefs to ``PREFS_FN``.

    Args:
        prefs_fn (str): Location to dump prefs. if None, use existing ``PREFS_FN``

    """
    if prefs_fn is None:
        try:
            prefs_fn = globals()['_PREFS']['PREFS_FN']
        except KeyError: # pragma: no cover
            raise RuntimeError('Asked to save_prefs without prefs_fn, but no PREFS_FN in prefs')

    with globals()['_LOCK']:
        with open(prefs_fn, 'w') as prefs_f:
            json.dump(globals()['_PREFS']._getvalue(), prefs_f,
                      indent=4, separators=(',', ': '))

    if globals()['_LOGGER'] is not None:
        globals()['_LOGGER'].info(f'Saved prefs to {prefs_fn}')




def make_dirs(): # pragma: no cover - travis doesnt like making directories like this
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
    Initialize prefs. Called in ``pvp.__init__.py`` to ensure prefs are initialized before anything else.
    """

    # add more functions as needed, but probably bad to hardcode default prefs here.
    # pull them up top like _DIRECTORIES

    make_dirs()
    load_prefs(os.path.join(get_pref('VENT_DIR'), 'prefs.json'))



