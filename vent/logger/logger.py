import time
from typing import List
import threading
import numpy as np
import copy
from collections import deque
import pdb
import vent.io as io
import logging
import tables as pytb
from datetime import datetime
import os

from vent.common.message import SensorValues, ControlValues, ControlSetting
from vent.common.values import CONTROL, ValueName


class DataSample(pytb.IsDescription):
    """
    Structure for the hdf5-table for data
    """
    timestamp    = pytb.Float64Col()    # current time of the measurement - has to be 64 bit
    pressure     = pytb.UInt8Col()
    flow_in      = pytb.UInt8Col()
    flow_out     = pytb.UInt8Col()
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
        open_logfile():                       Opens a log-file, creates one if necessary. 
        close_logfile():                      Flushes, and closes the logfile.
        store_waveform_data(SensorValues):    Takes data from SensorValues, but DOES NOT FLUSH 
        store_controls():                     Store controls in the same file? TODO: Discuss 
        flush_logfile():                      Flush the data into the file
        check_size():                         Make sure that the files don't grow too big TODO: Implement

    """

    def __init__(self):

        # If initialized, make a new file
        today = datetime.today()
        date_string = today.strftime("%Y-%m-%d-%H-%M")

        if not os.path.exists('logfiles'):
            os.makedirs('logfiles')
        self.file = "vent/logfiles/" + date_string + "_controller_log.h5"

        self.storage_used = self.check_files()  # Make sure there is space. Sum of all logfiles in bytes

    def open_logfile(self):
        """
        Opens the hdf5 file.
        """

        #Open the file
        self.h5file = pytb.open_file(self.file, mode = "a")

        #If it doesn't contain our structure, create it.
        if "/waveforms" not in self.h5file:
            group = self.h5file.create_group("/", 'waveforms', 'Respiration waveforms')
            self.data_table    = self.h5file.create_table(group, 'readout', DataSample, "Breath Cycles")
        else:
            self.data_table = self.h5file.root.waveforms.readout

        if "/controls" not in self.h5file:
            group = self.h5file.create_group("/", 'controls', 'Control signal history')
            self.control_table = self.h5file.create_table(group, 'readout', ControlCommand, "Control Commands")
        else:
            self.control_table = self.h5file.root.controls.readout
            
    def close_logfile(self):
        """
        Flushes & closes the open hdf file.
        """
        self.h5file.close() # Also flushes the remaining buffers
        
    def __rescale_save(self, raw_value, value, target, scalingconstant):
        """
        Rescales values to fit into the ranges specified in DataSample
        """
        if DataSample.columns[value].dtype == target.dtype:
            return np.int8( raw_value * scalingconstant )    # type cast to unsigned int 8, flow between 0 and 1.28 l/sec
        else:
            raise ValueError('Dynamic range unclear.')

    def store_waveform_data(self, sensor_values: SensorValues, control_values: ControlValues):
        """
        Appends a datapoint to the file.
        NOTE: Not flushed yet.
        """

        #Make sure hdf5 file is open
        if not self.h5file.isopen:
            self.open_logfile()
        
        datapoint                 = self.data_table.row
        datapoint['timestamp']    = sensor_values.timestamp
        datapoint['pressure']     = self.__rescale_save(raw_value = sensor_values.PRESSURE, value = 'pressure', target=pytb.UInt8Col(), scalingconstant=5)
        datapoint['cycle_number'] = sensor_values.breath_count
        datapoint['flow_in']      = self.__rescale_save(raw_value = control_values.flow_in, value = 'flow_in', target=pytb.UInt8Col(), scalingconstant=100)
        datapoint['flow_out']     = self.__rescale_save(raw_value = control_values.flow_out, value = 'flow_out', target=pytb.UInt8Col(), scalingconstant=100)
        datapoint.append()
    
    def store_control_command(self, control_setting: ControlSetting):
        """
        Appends a control signal to the hdf5 file.
        NOTE: Also not flushed yet.
        """
        if not self.h5file.isopen:
            self.open_logfile()

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
        
    def store_controls(self):
        """
        Saves a new controlsetting to the file. TODO: SHOULD WE DO THIS HERE?
        """
        
        self.open_logfile()
        
        datapoint                 = self.data_table.row
        datapoint['name']         = ValueName.PEEP
        datapoint['value']        = 3
        datapoint['min_value']    = 1
        datapoint['max_value']    = 4
        datapoint['timestamp']    = time.time()
        datapoint.append()
    
        self.close_logfile()
                
    def check_files(self):
        """
        make sure that the file's are not getting too large.
        """
        total_size = 0
        logpath = 'vent/logfiles'
        for filenames in os.listdir(logpath):
            fp = os.path.join(logpath, filenames)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
        if total_size>1e10:     #
            raise OSError('Too many logfiles in /vent/logfiles/ (>10GB). Free disk space')
        else:
            return total_size  # size in bytes