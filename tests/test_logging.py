import numpy as np
import pylab as pl
import sys
import pytest
import time
import os
sys.path.append("../")

from pvp.common.loggers import DataLogger
from pvp.common.message import SensorValues, ControlValues, DerivedValues, ControlSetting
from pvp.common.values import ValueName
from pvp.common import values


@pytest.mark.parametrize("control_setting_name", values.CONTROL.keys())
def test_control_storage(control_setting_name):

    # Store stuff
    dl = DataLogger()  
    control_setting = ControlSetting(name=control_setting_name, value=np.random.random(), min_value = np.random.random(), max_value = np.random.random())
    dl.store_control_command(control_setting)

    dl.flush_logfile
    dl.close_logfile()
    dl.log2mat()
    dl.log2csv()
    filepath = dl.file

    # Load stuff
    dl2 = DataLogger()  
    tt = dl2.load_file(filepath)
    dl2.log2mat(filepath)
    dl2.log2csv(filepath)

    st = tt['control_data']['name'][0]
    assert str(control_setting.name) == st.decode('utf-8') 
    assert control_setting.value     == tt['control_data']['value'][0]
    assert control_setting.min_value == tt['control_data']['min_value'][0]
    assert control_setting.max_value == tt['control_data']['max_value'][0]
    assert control_setting.timestamp == tt['control_data']['timestamp'][0]

def test_sensor_storage():

    # Store stuff
    dl = DataLogger()  
    sensor_values =  SensorValues(vals={
            ValueName.PIP.name                  : np.random.random(),
            ValueName.PEEP.name                 : np.random.random(),
            ValueName.FIO2.name                 : np.random.random(),
            ValueName.PRESSURE.name             : np.random.random(),
            ValueName.VTE.name                  : np.random.random(),
            ValueName.BREATHS_PER_MINUTE.name   : np.random.random(),
            ValueName.INSPIRATION_TIME_SEC.name : np.random.random(),
            ValueName.FLOWOUT.name              : np.random.random(),
            'timestamp'                         : time.time(),
            'loop_counter'                      : np.random.random(),
            'breath_count'                      : np.random.randint(1000)
            })
    control_values = ControlValues(
                control_signal_in = np.random.random(),
                control_signal_out = np.random.random(),
    )
    dl.store_waveform_data(sensor_values, control_values)
    dl.flush_logfile
    dl.close_logfile()
    filepath = dl.file

    # Load stuff
    dl2 = DataLogger()  
    tt = dl2.load_file(filepath)

    assert control_values.control_signal_in  == tt['waveform_data']['control_in'][0]
    assert control_values.control_signal_out == tt['waveform_data']['control_out'][0]
    assert sensor_values.breath_count == tt['waveform_data']['cycle_number'][0]
    assert sensor_values.FLOWOUT == tt['waveform_data']['flow_out'][0]
    assert sensor_values.FIO2 == tt['waveform_data']['oxygen'][0]
    assert sensor_values.PRESSURE == tt['waveform_data']['pressure'][0]
    assert sensor_values.timestamp == tt['waveform_data']['timestamp'][0]

def test_derived_storage():

    # Store stuff
    dl = DataLogger()  
    derived_values = DerivedValues(
        timestamp        = time.time(),
        breath_count     = np.random.randint(1000),
        I_phase_duration = np.random.random(),
        pip_time         = np.random.random(),
        peep_time        = np.random.random(),
        pip              = np.random.random(),
        pip_plateau      = np.random.random(),
        peep             = np.random.random(), 
        vte              = np.random.random()
    )
    dl.store_derived_data(derived_values)
    dl.flush_logfile
    dl.close_logfile()
    filepath = dl.file

    # Load stuff
    dl2 = DataLogger()  
    tt = dl2.load_file(filepath)

    assert derived_values.I_phase_duration  == tt['derived_data']['I_phase_duration'][0]
    assert derived_values.breath_count  == tt['derived_data']['cycle_number'][0]
    assert derived_values.peep  == tt['derived_data']['peep'][0]
    assert derived_values.peep_time  == tt['derived_data']['peep_time'][0]
    assert derived_values.pip  == tt['derived_data']['pip'][0]
    assert derived_values.pip_plateau  == tt['derived_data']['pip_plateau'][0]
    assert derived_values.pip_time  == tt['derived_data']['pip_time'][0]
    assert derived_values.timestamp  == tt['derived_data']['timestamp'][0]
    assert derived_values.vte  == tt['derived_data']['vte'][0]


def test_checks():

    #Make sure the rotation system works
    dl = DataLogger()
    sensor_values =  SensorValues(vals={
            ValueName.PIP.name                  : np.random.random(),
            ValueName.PEEP.name                 : np.random.random(),
            ValueName.FIO2.name                 : np.random.random(),
            ValueName.PRESSURE.name             : np.random.random(),
            ValueName.VTE.name                  : np.random.random(),
            ValueName.BREATHS_PER_MINUTE.name   : np.random.random(),
            ValueName.INSPIRATION_TIME_SEC.name : np.random.random(),
            ValueName.FLOWOUT.name              : np.random.random(),
            'timestamp'                         : time.time(),
            'loop_counter'                      : np.random.random(),
            'breath_count'                      : np.random.randint(1000)
            })
    control_values = ControlValues(
                control_signal_in = np.random.random(),
                control_signal_out = np.random.random(),
    )
    dl.store_waveform_data(sensor_values, control_values)
    dl.flush_logfile
    dl.close_logfile()

    file1 = dl.file
    parts = file1.split(".0.")
    dl._MAX_FILE_SIZE = -1

    new_filename = parts[0] + '.1.' + parts[1]
    assert not os.path.exists(new_filename)

    for i in range(10):
        dl.rotation_newfile()
        new_filename = parts[0] + '.' + str(i) + '.' + parts[1]
        assert os.path.exists(new_filename)

    # Check file sizes 
    dl.check_files()

