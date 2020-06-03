"""
Logging functionality

There are two types of loggers: a standard :class:`logging.Logger` -based logging system for debugging and recording system events,
and a :mod:`tables` - based :class:`.DataLogger` class to store continuously measured sensor values.

"""
import shutil
import traceback
import os
import logging
from datetime import datetime
from logging import handlers


import numpy as np
import tables as pytb

from vent.common.message import SensorValues, ControlValues, ControlSetting

# some global stack param
MAX_STACK_DEPTH = 20

from vent.common import prefs

_LOGGERS = []
"""
list of strings, which loggers have been created already.
"""


def init_logger(module_name: str,
                log_level: int = logging.DEBUG,
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
    if file_handler:
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


class DataSample(pytb.IsDescription):
    """
    Structure for the hdf5-table for data
    """
    timestamp    = pytb.Float64Col()    # current time of the measurement - has to be 64 bit
    pressure     = pytb.Float64Col()
    flow_in      = pytb.Float64Col()
    flow_out     = pytb.Float64Col()
    cycle_number = pytb.UInt32Col()     # Max is 2147483647 Breath Cycles (~78 years)


class ControlCommand(pytb.IsDescription):
    """
    Structure for the hdf5-table to store control commands
    """
    name      = pytb.StringCol(16)   # Control setting name
    value     = pytb.Float64Col()    # double (double-precision)
    min_value = pytb.Float64Col()    # double (double-precision)
    max_value = pytb.Float64Col()    # double (double-precision)
    timestamp = pytb.Float64Col()    # double (double-precision)


class DataLogger:
    """
    Class for logging numerical respiration data and control settings.
    Creates a hdf5 file with this general structure:
        / root
        |--- waveforms (group)
        |    |--- time | pressure_data | volume | Cycle No.    --- TODO: WHAT TO SAVE?
        |
        |--- controls (group)                                  --- TODO: WHAT TO SAVE? DO THIS HERE?
        |    |--- (time, controllsignal)
        |

    Public Methods:
        close_logfile():                      Flushes, and closes the logfile.
        store_waveform_data(SensorValues):    Takes data from SensorValues, but DOES NOT FLUSH
        store_controls():                     Store controls in the same file? TODO: Discuss
        flush_logfile():                      Flush the data into the file
        check_size():                         Make sure that the files don't grow too big TODO: Implement

    """

    def __init__(self, compression_level : int = 9):

        # general parameters for logging
        self._MAX_FILE_SIZE = 1e8          # Maximum allowed file size for circular logging
        self._MAX_NUM_LOGFILES = 10        # Maximum allowed file number for circular logging

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
            self.h5file = pytb.open_file(self.file, mode = "a")

        if "/waveforms" not in self.h5file:
            group = self.h5file.create_group("/", 'waveforms', 'Respiration waveforms')
            self.data_table = self.h5file.create_table(group, 'readout', DataSample, "Breath Cycles",
                                                       filters = pytb.Filters(
                                                           complevel=self.compression_level,
                                                           complib='zlib'),
                                                       expectedrows=1000000)
        else:
            self.data_table = self.h5file.root.waveforms.readout

        if "/controls" not in self.h5file:
            group = self.h5file.create_group("/", 'controls', 'Control signal history')
            self.control_table = self.h5file.create_table(group, 'readout', ControlCommand, "Control Commands",
                                                          filters = pytb.Filters(
                                                              complevel=self.compression_level,
                                                              complib='zlib')
                                                          )
        else:
            self.control_table = self.h5file.root.controls.readout

    def close_logfile(self):
        """
        Flushes & closes the open hdf file.
        """
        self.h5file.close() # Also flushes the remaining buffers

    def store_waveform_data(self, sensor_values: SensorValues, control_values: ControlValues):
        """
        Appends a datapoint to the file.
        NOTE: Not flushed yet.
        """
        self._open_logfile()
        datapoint                 = self.data_table.row
        datapoint['timestamp']    = sensor_values.timestamp
        datapoint['pressure'] = sensor_values.PRESSURE
        datapoint['cycle_number'] = sensor_values.breath_count
        datapoint['flow_in'] = control_values.flow_in
        datapoint['flow_out'] = control_values.flow_out
        datapoint.append()

    def store_control_command(self, control_setting: ControlSetting):
        """
        Appends a control signal to the hdf5 file.
        NOTE: Also not flushed yet.
        """
        self._open_logfile()
        datapoint               = self.control_table.row
        datapoint['name']       = control_setting.name
        datapoint['value']      = control_setting.value
        datapoint['min_value']  = control_setting.min_value
        datapoint['max_value']  = control_setting.max_value
        datapoint['timestamp']  = control_setting.timestamp
        datapoint.append()

    def flush_logfile(self):
        """
        This flushes the datapoints to the file.
        To be executed every other second, e.g. at the end of breath cycle.
        """
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
            raise OSError(f'Too many logfiles in {self.log_dir} (>1000 files). There are ' + str(len(os.listdir(self.log_dir))) + ' files. Delete some.')
            # TODO: log a warning
            # TODO: Turn off save data flag
        elif total_size>max_size:     #
            raise OSError(f'Logfiles in {self.log_dir} are too large. Max allowed is ' + '{0:.2f}'.format(max_size*1e-9) + 'GB, used is ' + '{0:.2f}'.format(total_size*1e-9) +  'GB. Free disk space.')
        else:
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

        data_dict = {"waveform_data": waveform_data, "control_data": control_data}
        return data_dict