import time
import numpy as np
import pytest
import random

from vent.common.message import SensorValues, ControlSetting
from vent.alarm import AlarmSeverity, Alarm
from vent.common.values import ValueName
from vent.coordinator.coordinator import get_coordinator
from vent.controller.control_module import get_control_module
from vent import prefs
prefs.init()

######################################################################
#########################   TEST 1  ##################################
######################################################################
#
#   Make sure the controller remembers settings, and can be started
#   and stopped repeatedly a couple of times.
#

@pytest.mark.parametrize("control_setting_name", [ValueName.PIP,
                                                  ValueName.PIP_TIME,
                                                  ValueName.PEEP,
                                                  ValueName.BREATHS_PER_MINUTE,
                                                  ValueName.INSPIRATION_TIME_SEC])

def test_control_settings(control_setting_name):
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

    c_set = ControlSetting(name=control_setting_name, value=v)
    Controller.set_control(c_set)

    c_get = Controller.get_control(control_setting_name)

    assert c_get.name == c_set.name
    assert c_get.value == c_set.value

    wv = Controller.get_target_waveform()
    assert len(wv) == 5

def test_restart_controller():
    '''
    This tests whether the controller can be started and stopped 10 times without problems
    '''
    Controller = get_control_module(sim_mode=True)

    for counter in range(10):
        time.sleep(0.1)
        Controller.start()
        vals_start = Controller.get_sensors()
        time.sleep(0.3)
        Controller.stop() 
        vals_stop = Controller.get_sensors()
        assert vals_stop.loop_counter > vals_start.loop_counter








######################################################################
#########################   TEST 2  ##################################
######################################################################
#
#   Make sure the controller controlls, and the controll values look 
#   good. (i.e. close to target within narrow margins).
#

@pytest.mark.parametrize("control_type", ["PID", "STATE"])

def test_control_dynamical(control_type):
    ''' 
    This tests whether the controller is controlling pressure as intended.
    Start controller, set control values, measure whether actually there.
    '''
    Controller = get_control_module(sim_mode=True, simulator_dt=0.01)
    Controller._LOOP_UPDATE_TIME = 0.01


    if control_type == "PID":
        Controller.do_pid_control()
        Controller.do_pid_control()
        Inspiration_CI = 0.2
    else:
        Controller.do_state_control()
        Controller.do_state_control()
        Inspiration_CI = 0.4    # State control is not that precise, slightly wider confidence regions.

    vals_start = Controller.get_sensors()

    v_peep = 5
    command = ControlSetting(name=ValueName.PEEP, value=v_peep)
    Controller.set_control(command)

    v_pip = random.randint(15, 30)
    command = ControlSetting(name=ValueName.PIP, value=v_pip)
    Controller.set_control(command)

    v_bpm = random.randint(6, 20)
    command = ControlSetting(name=ValueName.BREATHS_PER_MINUTE, value=v_bpm)

    Controller.set_control(command)

    v_iphase = (0.3 + np.random.random()*0.5) * 60/v_bpm
    command = ControlSetting(name=ValueName.INSPIRATION_TIME_SEC, value=v_iphase)
    Controller.set_control(command)


    Controller.start()
    time.sleep(0.1)
    vals_start = Controller.get_sensors()
    temp_vals = Controller.get_sensors()
    while temp_vals.breath_count < 5:
        time.sleep(0.1)
        temp_vals = Controller.get_sensors()

    Controller.stop() # consecutive stops should be ignored
    Controller.stop() 
    Controller.stop()

    vals_stop = Controller.get_sensors()

    # Test whether get_sensors() return the right values
    COPY_peep     = Controller.COPY_sensor_values.PEEP
    COPY_pip      = Controller.COPY_sensor_values.PIP
    COPY_fio2     = Controller.COPY_sensor_values.FIO2
    COPY_pressure = Controller.COPY_sensor_values.PRESSURE
    COPY_vte      = Controller.COPY_sensor_values.VTE
    COPY_bpm      = Controller.COPY_sensor_values.BREATHS_PER_MINUTE
    COPY_Iinsp    = Controller.COPY_sensor_values.INSPIRATION_TIME_SEC
    COPY_tt       = Controller.COPY_sensor_values.timestamp
    COPY_lc       = Controller.COPY_sensor_values.loop_counter

    assert COPY_peep     == vals_stop.PEEP
    assert COPY_pip      == vals_stop.PIP
    assert COPY_fio2     == vals_stop.FIO2
    assert COPY_pressure == vals_stop.PRESSURE
    assert COPY_vte      == vals_stop.VTE
    assert COPY_bpm      == vals_stop.BREATHS_PER_MINUTE
    assert COPY_Iinsp    == vals_stop.INSPIRATION_TIME_SEC
    assert COPY_tt       == vals_stop.timestamp
    assert COPY_lc       == vals_stop.loop_counter

    print(v_peep)
    print(v_pip)
    print(v_bpm)
    print(v_iphase)
    print(Inspiration_CI)
    print(control_type)

    assert (vals_stop.loop_counter - vals_start.loop_counter)  > 100 # In 20s, this program should go through a good couple of loops
    assert np.abs(vals_stop.PEEP - v_peep)                     < 5   # PEEP error correct within 5 cmH2O
    assert np.abs(vals_stop.PIP - v_pip)                       < 5   # PIP  error correct within 5 cmH2O
    assert np.abs(vals_stop.BREATHS_PER_MINUTE - v_bpm)        < 5   # Breaths per minute correct within 5 bpm
    assert np.abs(vals_stop.INSPIRATION_TIME_SEC - v_iphase)   < 0.2*vals_stop.INSPIRATION_TIME_SEC # Inspiration time, correct within 20%

    hb1 = Controller.get_heartbeat()
    assert hb1 > 0                                 # Test the heartbeat
    assert np.abs(hb1 - COPY_lc) < Controller._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE + 2  # true heart-beat should be close to the sensor loop counter







######################################################################
#########################   TEST 3  ##################################
######################################################################



######################################################################
#########################   TEST 4  ##################################
######################################################################
#
#   More involved test, randomized waittimes and make sure the system works
#
def test_erratic_dt():
    '''
        This is a function to test whether the controller works with random update times
    '''
    Controller = get_control_module(sim_mode=True)

    Controller.start()
    ls = []
    for t in np.arange(0, 30,0.05):
        Controller._LOOP_UPDATE_TIME = np.random.randint(100)/1000  # updates anywhere between 0ms and 100ms
        time.sleep(0.05)
        vals = Controller.get_sensors()
        ls.append(vals)
    Controller.stop()

    cc = Controller.get_control(control_setting_name = ValueName.PEEP)
    target_peep = cc.value
    cc = Controller.get_control(control_setting_name = ValueName.PIP)
    target_pip = cc.value

    peeps = np.unique([np.abs(s.PEEP - target_peep)  for s in ls if s.PEEP is not None])
    pips = np.unique([np.abs(s.PIP - target_pip)  for s in ls if s.PIP is not None])

    assert np.mean(peeps) < 5
    assert np.mean(pips) < 5

