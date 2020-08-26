.. _prefs_overview:

Prefs
=========

Prefs set configurable parameters used throughout PVP.

See :data:`.prefs._DEFAULTS` for description of all available parameters

Prefs are stored in a .json file, by default located at ``~/pvp/prefs.json`` . Prefs can be manually
changed by editing this file (when the system is not running, when the system is running use :func:`.prefs.set_pref` ).

When any module in pvp is first imported, the :func:`.prefs.init` function is called
that

* Makes any directories listed in :data:`.prefs._DIRECTORIES`
* Declares all prefs as their default values from :data:`.prefs._DEFAULTS` to ensure they are always defined
* Loads the existing ``prefs.json`` file and updates values from their defaults

Prefs can be gotten and set from anywhere in the system with :func:`.prefs.get_pref` and :func:`.prefs.set_pref` .
Prefs are stored in a :class:`multiprocessing.Manager` dictionary which makes these methods both thread- and process-safe.
Whenever a pref is set, the ``prefs.json`` file is updated to reflect the new value, so preferences
are durable between runtimes.

Additional ``prefs`` should be added by adding an entry in the :data:`.prefs._DEFAULTS` dict rather than hardcoding them elsewhere in the program.


.. automodule:: pvp.common.prefs
   :members:
   :undoc-members:
   :show-inheritance: