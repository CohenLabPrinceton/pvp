"""
Logging functionality

There are two types of loggers: a standard :class:`logging.Logger` -based logging system for debugging and recording system events,
and a :mod:`tables` - based :class:`.DataLogger` class to store continuously measured sensor values.

"""
import typing
import shutil
import traceback
import os
import logging
import sys
from datetime import datetime
from logging import handlers
import scipy.io as sio


import numpy as np
import tables as pytb

if typing.TYPE_CHECKING:
    # from vent.common.message import SensorValues, ControlValues, ControlSetting
    from vent.common.message import SensorValues, ControlValues, DerivedValues, ControlSetting


# some global stack param
MAX_STACK_DEPTH = 20

from vent.common import prefs

_LOGGERS = []
"""
list of strings, which loggers have been created already.
"""


def init_logger(module_name: str,
                log_level: int = None,
                file_handler: bool = True) -> logging.Logger:
    """
    Initialize a logger for logging events.

    If a logger has already been initialized, return that.

    Args:
        module_name (str): module name used to generate filename and name logger
        log_level (int): one of :var:`logging.DEBUG`, :var:`logging.INFO`, :var:`logging.WARNING`, or :var:`logging.ERROR`
        file_handler (bool, str): if ``True``, (default), log in ``<logdir>/module_name.log`` .
            if ``False``, don't log to disk.

    Returns:
        :class:`logging.Logger` : Logger 4 u 2 use
    """

    logger = logging.getLogger(module_name)

    # if the logger has already been created, return the same instance
    if module_name in globals()['_LOGGERS']:
        return logger

    # set log level
    if not log_level:
        log_level = prefs.get_pref('LOGLEVEL')
        log_level = getattr(logging, log_level)


    assert log_level in (logging.DEBUG,
                         logging.INFO,
                         logging.WARNING,
                         logging.ERROR)
    logger.setLevel(log_level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # I assume this is to stop printing to stderr? why does it get a formatter then? -jls 2020-05-25
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # handler to log to disk
    # max = 8 file x 16 MB = 128 MB
    if file_handler and 'pytest' not in sys.modules:
        log_filename = os.path.join(prefs.get_pref('LOG_DIR'),
                                    module_name + '.log')
        fh = logging.handlers.RotatingFileHandler(
            log_filename,
            mode = 'a',
            maxBytes=round(prefs.get_pref('LOGGING_MAX_BYTES')/(len(globals()['_LOGGERS'])+1)/prefs.get_pref('LOGGING_MAX_FILES')),
            backupCount=prefs.get_pref('LOGGING_MAX_FILES')
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    globals()['_LOGGERS'].append(module_name)

    # update the maxBytes of each logger so the same total maxBytes is kept
    update_logger_sizes()

    return logger

def update_logger_sizes():
    """
    Adjust each logger's ``maxBytes`` attribute so that the total across all loggers is ``prefs.LOGGING_MAX_BYTES``
    """
    new_max_bytes = round(prefs.get_pref('LOGGING_MAX_BYTES')/len(globals()['_LOGGERS'])/prefs.get_pref('LOGGING_MAX_FILES'))

    for logger_name in globals()['_LOGGERS']:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.maxBytes = new_max_bytes




def log_exception(e, tb):
    """  # TODO: Stub exception logger. Prints exception type & traceback

    Args:
        e: Exception to log
        tb: TraceBack associated with Exception e

    """
    print("Caught the following exception:", e, " but I don't know what to do with it.")
    # print(traceback.print_tb(tb, limit=MAX_STACK_DEPTH))
    raise


class ContinuousData(pytb.IsDescription):
    """
    Structure for the hdf5-table for continuous waveform data; measured once per controller loop.
    """
    timestamp    = pytb.Float64Col()    # current time of the measurement - has to be 64 bit
    pressure     = pytb.Float64Col()
    flow_out     = pytb.Float64Col()
    control_in   = pytb.Float64Col()
    control_out  = pytb.Float64Col()
    oxygen       = pytb.Float64Col()
    cycle_number = pytb.UInt32Col()     # Max is 2147483647 Breath Cycles (~78 years)


class ControlCommand(pytb.IsDescription):
    """
    Structure for the hdf5-table to store control commands. Appended whenever a control command is received.
    """
    name      = pytb.StringCol(16)   # Control setting name
    value     = pytb.Float64Col()    # double (double-precision)
    min_value = pytb.Float64Col()    # double (double-precision)
    max_value = pytb.Float64Col()    # double (double-precision)
    timestamp = pytb.Float64Col()    # double (double-precision)

class CycleData(pytb.IsDescription):
    """
    Structure for the hdf5-table to store derived quantities from waveform measurements. Measured once per breath-cycle.
    """
    timestamp        =  pytb.Float64Col()    # Start time of this breath cycle
    cycle_number     =  pytb.UInt32Col()     # Index of this breath cycle, Max is 2147483647 Breath Cycles (~78 years)
    I_phase_duration =  pytb.Float64Col()    # estimated duration of inspiratory phase
    pip_time         =  pytb.Float64Col()    # estimated time when peak inspiratory pressure [PIP] was reached
    peep_time        =  pytb.Float64Col()    # estimated time when positive end-expiratory pressure [PEEP] was reached
    pip              =  pytb.Float64Col()    # estimated peak inspiration pressure [PIP]
    pip_plateau      =  pytb.Float64Col()    # estimated plateau pressure around PIP
    peep             =  pytb.Float64Col()    # estimated peep pressure
    vte              =  pytb.Float64Col()    # estimated End-Tidal Volume

class DataLogger:
    """
    Class for logging numerical respiration data and control settings.
    Creates a hdf5 file with this general structure:
        / root
        |--- waveforms (group)
        |    |--- time | pressure_data | flow_out | control_signal_in | control_signal_out | FiO2 | Cycle No.
        |
        |--- controls (group)
        |    |--- (time, controllsignal)
        |
        |--- derived_quantities (group)
        |    |--- (time, Cycle No, I_PHASE_DURATION, PIP_TIME, PEEP_time, PIP, PIP_PLATEAU, PEEP, VTE )
        |
        |

    Public Methods:
        close_logfile():                      Flushes, and closes the logfile.
        store_waveform_data(SensorValues):    Takes data from SensorValues, but DOES NOT FLUSH
        store_controls():                     Store controls in the same file? TODO: Discuss
        flush_logfile():                      Flush the data into the file

    """

    def __init__(self, compression_level : int = 9):

        # Logging the start of the DataLogger
        self.logger = init_logger(__name__)
        self.logger.info('DataLogger init')

        # general parameters for logging
        self._MAX_FILE_SIZE = 1e8          # Maximum allowed file size for circular logging
        self._MAX_NUM_LOGFILES = 10        # Maximum allowed file number for circular logging
        self._data_save_allowed = True     # Data is allowed to be saved. If exceeds limits above, the flag is set to False, and logging stops.

        # If initialized, make a new file
        today = datetime.today()
        date_string = today.strftime("%Y-%m-%d-%H-%M")

        # Make the log folder
        self.log_dir = prefs.get_pref('DATA_DIR')
        self.file = os.path.join(self.log_dir, date_string + "_controller_log.0.h5")

        # Make sure that the file doesn't exist yet, if it does, append another number
        # In rarely happens, but for Travis-tests, this is needed.
        c=0
        while os.path.exists(self.file):
            self.file = os.path.join(self.log_dir, date_string + '-' + str(c) + "_controller_log.0.h5")
            c = c + 1

        self.storage_used = self.check_files()  # Make sure there is space. Sum of all logfiles in bytes

        ## For data storage ##
        self.h5file = pytb.open_file(self.file, mode = "a")      # Open logfile
        self.compression_level = compression_level # From 1 to 9, see tables documentation

    def __del__(self):
        self.close_logfile()

    def _open_logfile(self):
        """
        Opens the hdf5 file.
        """
        if not self.h5file.isopen:
            self.logger.info('Reopening ' + self.file )
            self.h5file = pytb.open_file(self.file, mode = "a")

        if "/waveforms" not in self.h5file:
            self.logger.info('Generating /waveform table in: ' + self.file )
            group = self.h5file.create_group("/", 'waveforms', 'Respiration waveforms')
            self.data_table = self.h5file.create_table(group, 'readout', ContinuousData, "Breath Cycles",
                                                       filters = pytb.Filters(
                                                           complevel=self.compression_level,
                                                           complib='zlib'),
                                                       expectedrows=1000000)
        else:
            self.data_table = self.h5file.root.waveforms.readout

        if "/controls" not in self.h5file:
            self.logger.info('Generating /controls table in: ' + self.file )
            group = self.h5file.create_group("/", 'controls', 'Control signal history')
            self.control_table = self.h5file.create_table(group, 'readout', ControlCommand, "Control Commands",
                                                          filters = pytb.Filters(
                                                              complevel=self.compression_level,
                                                              complib='zlib')
                                                          )
        else:
            self.control_table = self.h5file.root.controls.readout

        if "/derived_quantities" not in self.h5file:
            self.logger.info('Generating /derived_quantities table in: ' + self.file )
            group = self.h5file.create_group("/", 'derived_quantities', 'Quantities derived from waveform, one per cycle')
            self.derived_table = self.h5file.create_table(group, 'readout', CycleData, "Derived Values",
                                                          filters = pytb.Filters(
                                                              complevel=self.compression_level,
                                                              complib='zlib')
                                                          )
        else:
            self.derived_table = self.h5file.root.derived_quantities.readout

    def close_logfile(self):
        """
        Flushes & closes the open hdf file.
        """
        print("Saving in..." + self.file)
        self.h5file.close() # Also flushes the remaining buffers

    def store_waveform_data(self, sensor_values: 'SensorValues', control_values: 'ControlValues'):
        """
        Appends a datapoint to the file.
        NOTE: Not flushed yet.
        """
        if self._data_save_allowed:
            self._open_logfile()
            datapoint                 = self.data_table.row
            datapoint['timestamp']    = sensor_values.timestamp
            datapoint['pressure']     = sensor_values.PRESSURE
            datapoint['flow_out']     = sensor_values.FLOWOUT
            datapoint['control_in']   = control_values.control_signal_in
            datapoint['control_out']  = control_values.control_signal_out
            datapoint['oxygen']       = sensor_values.FIO2
            datapoint['cycle_number'] = sensor_values.breath_count
            datapoint.append()

    def store_control_command(self, control_setting: 'ControlSetting'):
        """
        Appends a control signal to the hdf5 file.
        NOTE: Also not flushed yet.
        """
        if self._data_save_allowed:
            self._open_logfile()
            datapoint               = self.control_table.row
            datapoint['name']       = control_setting.name
            datapoint['value']      = control_setting.value
            datapoint['min_value']  = control_setting.min_value
            datapoint['max_value']  = control_setting.max_value
            datapoint['timestamp']  = control_setting.timestamp
            datapoint.append()

    def store_derived_data(self, derived_values: 'DerivedValues'):
        """
        Appends derived data to the hdf5 file.
        NOTE: Also not flushed yet.
        """
        if self._data_save_allowed:
            self._open_logfile()
            datapoint                      = self.derived_table.row
            datapoint['timestamp']         = derived_values.timestamp
            datapoint['cycle_number']      = derived_values.breath_count
            datapoint['I_phase_duration']  = derived_values.I_phase_duration
            datapoint['pip_time']          = derived_values.pip_time
            datapoint['peep_time']         = derived_values.peep_time
            datapoint['pip']               = derived_values.pip
            datapoint['pip_plateau']       = derived_values.pip_plateau
            datapoint['peep']              = derived_values.peep
            datapoint['vte']               = derived_values.vte
            datapoint.append()

    def flush_logfile(self):
        """
        This flushes the datapoints to the file.
        To be executed every other second, e.g. at the end of breath cycle.
        """
        if self._data_save_allowed:
            self.data_table.flush()
            self.control_table.flush()

    def check_files(self):
        """
        make sure that the file's are not getting too large.
        """
        total_size = 0
        for filenames in os.listdir(self.log_dir):
            fp = os.path.join(self.log_dir, filenames)
            # skip if it is symbolic link
            if (not os.path.islink(fp)) and fp.endswith('.h5'):
                total_size += os.path.getsize(fp)

        #Check file system
        total_space_hd, used, free = shutil.disk_usage('/')
        max_size = np.min([total_space_hd*0.2, 1e10])      # Limit to whatever is smaller, 20% of the file system or 10 GB

        if len(os.listdir(self.log_dir)) > 1000:
            message = f'Too many logfiles in {self.log_dir} (>1000 files). There are ' + str(len(os.listdir(self.log_dir))) + ' files. Delete some.'
            print(message)
            # self.logger.exception(message)  # Log a warning
            self._data_save_allowed = False # Stop data saving
        elif total_size>max_size:
            message = f'Logfiles in {self.log_dir} are too large. Max allowed is ' + '{0:.2f}'.format(max_size*1e-9) + 'GB, used is ' + '{0:.2f}'.format(total_size*1e-9) +  'GB. Free disk space.'
            print(message)
            self.logger.exception(message)  # Log a warning
            self._data_save_allowed = False # Stop data saving
        else:
            self._data_save_allowed = True  # Allow data saving
            return total_size  # size in bytes

    def rotation_newfile(self):
        logfile_size = os.path.getsize(self.file)                       # Measure active logfile "..._log.0.h5"

        if logfile_size > self._MAX_FILE_SIZE:                          # If too big:
            self.close_logfile()                                        # Close current logfile

            parts = self.file.split(".0.")                              # Go through all logfiles, and increase idx;  "..._log.0.h5" -> "..._log.1.h5" etc
            for file_idx in range(self._MAX_NUM_LOGFILES-1, -1, -1):    # Have to start at index of last allowed file
                old_filename = parts[0] + '.' + str(file_idx    ) + '.' + parts[1]
                new_filename = parts[0] + '.' + str(file_idx + 1) + '.' + parts[1]
                if os.path.exists(old_filename):                        # On only if logfile already exists
                    os.rename(old_filename, new_filename)

            self.h5file.close()                                         # Generate new file with right file structure
            self.h5file = pytb.open_file(self.file, mode = "w")
            self._open_logfile()
            self.logger.info('DataLogger: rotated to new file.')

    def load_file(self, filename = None):
        """
        This loads a hdf5 file, and returns data to the user as a dictionary with two keys: waveform_data and control_data
        """
        self.close_logfile()

        if filename == None:
            filename = self.file

        print("Reading... " + filename)

        with pytb.open_file(filename, mode = "r") as file:

            table = file.root.waveforms.readout
            waveform_data = table.read()

            table = file.root.controls.readout
            control_data = table.read()

            table = file.root.derived_quantities.readout
            derived_data = table.read()

        data_dict = {"waveform_data": waveform_data, "control_data": control_data, "derived_data": derived_data}
        return data_dict

    def log2mat(self, filename = None):
        """
        Translates the compressed hdf5 into a matlab file containing a matlab struct. This struct has the same structure as the hdf5 file, but is not compressed.
        Use for any file:
            dl = DataLogger()
            dl.log2mat(filename)
        """
        if filename == None:
            filename = self.file

        new_file = filename.split('h5')
        new_filename = new_file[0] + '.mat'
        # try:
        dff = self.load_file(filename)
        ls_wv = dff['waveform_data']
        ls_dv = dff['derived_data']
        ls_ct = dff['control_data']
        matlab_data = {'waveforms': ls_wv, 'derived_quantities': ls_dv, 'control_commands': ls_ct}
        sio.savemat(new_filename, matlab_data)
        # except:
            # print(filename + " not found.")


    def log2csv(self, filename = None):
        """
        Translates the compressed hdf5 into three csv files containing:
            - waveform_data (measurement once per cycle)
            - derived_quantities (PEEP, PIP etc.)
            - control_commands (control commands sent to the controller)

        This is the best proxy for the structure contained in the hdf5 file.

        Use for any file:
            dl = DataLogger()
            dl.log2csv(filename)
        """
        
        if filename == None:
            filename = self.file
        new_file = filename.split('h5')

        try:
            dff = self.load_file(filename)
            ls_wv = dff['waveform_data']
            ls_dv = dff['derived_data']
            ls_ct = dff['control_data']

            # Waveform_data
            new_filename = new_file[0] + "waveforms"+'.csv'
            title = str(ls_wv.dtype.names)[1:-1]
            title.replace("'",'')
            np.savetxt(new_filename, ls_wv, delimiter=',', header=title, comments="")

            # Derived quantities
            new_filename = new_file[0] + "derived_quantities"+'.csv'
            title = str(ls_dv.dtype.names)[1:-1]
            title.replace("'",'')
            np.savetxt(new_filename, ls_dv, delimiter=',', header=title, comments="")

            # Control Commands
            new_filename = new_file[0] + "control_commands"+'.csv'
            title = str(ls_ct.dtype.names)[1:-1]
            title.replace("'",'')
            np.savetxt(new_filename, ls_ct, delimiter=',', header=title, fmt = ('%.18e,%.18e,%s,%.18e,%.18e'))
        except:
            print(filename + " not found.")
