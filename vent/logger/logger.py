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

from vent.common.message import SensorValues, ControlSetting
from vent.common.values import CONTROL, ValueName


class DataSample(pytb.IsDescription):
    """
    Structure for the hdf5-table for data
    """
    timestamp    = pytb.Float64Col()    # current time of the measurement
    pressure     = pytb.Float32Col()    # float  (single-precision)  -- because we'll have a whole bunch of these
    cycle_number = pytb.Int32Col()      # Breath Cycle No.

class ControlCommand(pytb.IsDescription):
    """
    Structure for the hdf5-table to store control commands
    """
    name      = pytb.StringCol(16)   # Control setting name
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

    def __init__(self, filename):
        self.file = filename    # Filename
        
    def open_logfile(self):
        """
        Opens the hdf5 file.
        """

        #If it isn't already open, open it.
        try:
            if not self.h5file.isopen:
                self.h5file = pytb.open_file(self.file, mode = "a")
            else:
                print("This should't happen. hdf5 file was open.")
        except:
            self.h5file = pytb.open_file(self.file, mode = "w")
    
        #If it doesn't contain our structure, create it.
        try:
            group = self.h5file.create_group("/", 'waveforms', 'Respiration waveforms')
            self.data_table    = self.h5file.create_table(group, 'readout', DataSample, "Breath Cycles")
            
            group = self.h5file.create_group("/", 'controls', 'Control signal history')
            self.control_table = self.h5file.create_table(group, 'readout', ControlCommand, "Control Commands")
        except:
            self.data_table = self.h5file.root.waveforms.readout
            self.control_table = self.h5file.root.controls.readout
            
    def close_logfile(self):
        """
        Flushes & closes the open hdf file.
        """
        self.data_table.flush()
        self.h5file.close()
        
    def store_waveform_data(self, sensor_values: SensorValues):
        """
        Appends a datapoint to the file.
        NOTE: Not flushed yet.
        """

        #Make sure hdf5 file is open
        if not self.h5file.isopen:
            self.open_logfile()
        
        datapoint                 = self.data_table.row

        datapoint['timestamp'] = sensor_values.timestamp
        datapoint['pressure'] = sensor_values.PRESSURE
        datapoint['cycle_number'] = sensor_values.breath_count

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
                
    def check_size(self):
        """
        make sure that the file's are not getting too large.
        """
        pass