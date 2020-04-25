import time
import numpy as np
import pytest
import random

from vent.common.message import SensorValues, ControlSetting, Alarm, AlarmSeverity, ControlSettingName
from vent.coordinator.coordinator import get_coordinator
from vent.controller.control_module import get_control_module


@pytest.mark.parametrize("control_setting_name", [ControlSettingName.PIP,
                                                  ControlSettingName.PIP_TIME,
                                                  ControlSettingName.PEEP,
                                                  ControlSettingName.BREATHS_PER_MINUTE,
                                                  ControlSettingName.INSPIRATION_TIME_SEC])

def test_control_settingss(control_setting_name):
    '''
    This test set_controls and get_controls
    Set and read a all five variables, make sure that they are identical.
    '''
    Controller = get_control_module(sim_mode=True)
    Controller.start()
    Controller.stop()

    v = random.randint(10, 100)
    v_min = random.randint(10, 100)
    v_max = random.randint(10, 100)
    t = time.time()

    c_set = ControlSetting(name=control_setting_name, value=v, min_value=v_min, max_value=v_max, timestamp=t)
    Controller.set_control(c_set)

    c_get = Controller.get_control(control_setting_name)

    assert c_get.name == c_set.name
    assert c_get.value == c_set.value
    assert c_get.min_value == c_set.min_value
    assert c_get.max_value == c_set.max_value
    assert c_get.timestamp == c_set.timestamp



def test_control_dynamical():
    ''' 
    This tests whether the controller is controlling pressure as intended.
    Start controller, set control values, measure whether actually there.
    '''
    Controller = get_control_module(sim_mode=True)

    vals_start = Controller.get_sensors()

    v_peep = random.randint(5, 15)
    command = ControlSetting(name=ControlSettingName.PEEP, value=v_peep, min_value=v_peep-1, max_value=v_peep+1, timestamp=time.time())
    Controller.set_control(command)

    v_pip = random.randint(15, 25)
    command = ControlSetting(name=ControlSettingName.PIP, value=v_pip, min_value=v_pip-1, max_value=v_pip+1, timestamp=time.time())
    Controller.set_control(command)

    v_bpm = random.randint(6, 25)
    command = ControlSetting(name=ControlSettingName.BREATHS_PER_MINUTE, value=v_bpm, min_value=v_bpm-1, max_value=v_bpm+1, timestamp=time.time()) 
    Controller.set_control(command)

    v_iphase = (0.3 + np.random.random()*0.5) * 60/v_bpm
    command = ControlSetting(name=ControlSettingName.INSPIRATION_TIME_SEC, value=v_iphase, min_value=v_iphase-1, max_value=v_iphase+1, timestamp=time.time()) 
    Controller.set_control(command)

    Controller.start()
    time.sleep(0.1)
    vals_start = Controller.get_sensors()
    time.sleep(20)                                                   # Let this run for 20 sec
    vals_stop = Controller.get_sensors()
    Controller.stop() 
    
    vals_stop = Controller.get_sensors()
    
    assert (vals_stop.loop_counter - vals_start.loop_counter)  > 1000 # In 20s, this program should go through at least 1000 loops
    assert np.abs(vals_stop.peep - v_peep)                     < 2    # PIP error correct within 2 cmH2O
    assert np.abs(vals_stop.pip - v_pip)                       < 2    # PIP error correct within 2 cmH2O
    assert np.abs(vals_stop.breaths_per_minute - v_bpm)        < 1    # Breaths per minute correct within 1 bpm
    assert np.abs(vals_stop.inspiration_time_sec - v_iphase)   < 0.2  # Inspiration time   correct within 0.2 sec

    # Test whether get_sensors() return the right values
    COPY_peep     = Controller.COPY_sensor_values.peep
    COPY_pip      = Controller.COPY_sensor_values.pip
    COPY_fio2     = Controller.COPY_sensor_values.fio2
    COPY_temp     = Controller.COPY_sensor_values.temp
    COPY_humidity = Controller.COPY_sensor_values.humidity
    COPY_pressure = Controller.COPY_sensor_values.pressure
    COPY_vte      = Controller.COPY_sensor_values.vte
    COPY_bpm      = Controller.COPY_sensor_values.breaths_per_minute
    COPY_Iinsp    = Controller.COPY_sensor_values.inspiration_time_sec
    COPY_tt       = Controller.COPY_sensor_values.timestamp
    COPY_lc       = Controller.COPY_sensor_values.loop_counter

    assert COPY_peep     == vals_stop.peep
    assert COPY_pip      == vals_stop.pip
    assert COPY_fio2     == vals_stop.fio2
    assert COPY_temp     == vals_stop.temp
    assert COPY_humidity == vals_stop.humidity
    assert COPY_pressure == vals_stop.pressure
    assert COPY_vte      == vals_stop.vte
    assert COPY_bpm      == vals_stop.breaths_per_minute
    assert COPY_Iinsp    == vals_stop.inspiration_time_sec
    assert COPY_tt       == vals_stop.timestamp
    assert COPY_lc       == vals_stop.loop_counter




def test_restart_controller():
    '''
    This tests whether the controller can be started and stopped 10 times without problems
    '''
    Controller = get_control_module(sim_mode=True)

    for counter in range(10):
        time.sleep(0.1)
        Controller.start()
        vals_start = Controller.get_sensors()
        time.sleep(0.2)
        Controller.stop() 
        vals_stop = Controller.get_sensors()
        assert vals_stop.loop_counter > vals_start.loop_counter



# Still to check:
# get alarms
# get active alarms
# get logged alarms
# test _PID update?
# For settings, try good and bad values. Make sure that it works


