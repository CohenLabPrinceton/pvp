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
    Set and read a few variables, make sure that they are identical.
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
    Start controller, set control values, measure whether actually there
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

    v_iphase = 1.2*random.random() + 0.8  #between 0.8 and 2
    command = ControlSetting(name=ControlSettingName.INSPIRATION_TIME_SEC, value=v_iphase, min_value=v_iphase-1, max_value=v_iphase+1, timestamp=time.time()) 
    Controller.set_control(command)


    vals_start = Controller.get_sensors()
    Controller.start()
    time.sleep(15)                                                   # Let this run for 15 sec
    Controller.stop() 
    
    vals_stop = Controller.get_sensors()
    
    assert (vals_stop.loop_counter - vals_start.loop_counter) > 1000 # In 15sec, this program should go through at least 1000 loops
    assert np.abs(vals_stop.peep - v_peep)                     < 0.5 # PIP error correct within 0.5 cmH2O
    assert np.abs(vals_stop.pip - v_pip)                       < 0.5 # PIP error correct within 0.5 cmH2O
    assert np.abs(vals_stop.breaths_per_minute - v_bpm)        < 1   # Breaths per minute correct within 1 bpm
    assert np.abs(vals_stop.inspiration_time_sec - v_iphase)   < 0.2 # Inspiration time   correct within 0.2 sec


# Still to check:
# get sensors
# get alarms
# get active alarms
# get logged alarms
# set controls
# get control
# test _PID update?
# repeated stars and stops of the mainloop, make sure heartbeat increases
# For settings, try good and bad values. Make sure that it works


