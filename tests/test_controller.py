import time
import numpy as np
import pytest
import random

from vent.common.message import SensorValues, ControlSetting, Alarm, AlarmSeverity, ControlSettingName
from vent.coordinator.coordinator import get_coordinator
from vent.controller.control_module import get_control_module

######################################################################
#########################   TEST 1  ##################################
######################################################################
#
#   Make sure the controller remembers settings, and can be started
#   and stopped repeatedly a couple of times.
#
@pytest.mark.parametrize("control_setting_name", [ControlSettingName.PIP,
                                                  ControlSettingName.PIP_TIME,
                                                  ControlSettingName.PEEP,
                                                  ControlSettingName.BREATHS_PER_MINUTE,
                                                  ControlSettingName.INSPIRATION_TIME_SEC])

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

    c_set = ControlSetting(name=control_setting_name, value=v, min_value=v_min, max_value=v_max, timestamp=t)
    Controller.set_control(c_set)

    c_get = Controller.get_control(control_setting_name)

    assert c_get.name == c_set.name
    assert c_get.value == c_set.value
    assert c_get.min_value == c_set.min_value
    assert c_get.max_value == c_set.max_value
    assert c_get.timestamp == c_set.timestamp

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








######################################################################
#########################   TEST 2  ##################################
######################################################################
#
#   Make sure the controller controlls, and the controll values look 
#   good. (i.e. close to target within narrow margins).
#
def test_control_dynamical():
    ''' 
    This tests whether the controller is controlling pressure as intended.
    Start controller, set control values, measure whether actually there.
    '''
    Controller = get_control_module(sim_mode=True)

    vals_start = Controller.get_sensors()

    v_peep = random.randint(5, 10)
    command = ControlSetting(name=ControlSettingName.PEEP, value=v_peep, min_value=v_peep-2, max_value=v_peep+2, timestamp=time.time())
    Controller.set_control(command)

    v_pip = random.randint(15, 30)
    command = ControlSetting(name=ControlSettingName.PIP, value=v_pip, min_value=v_pip-2, max_value=v_pip+2, timestamp=time.time())
    Controller.set_control(command)

    v_bpm = random.randint(6, 20)
    command = ControlSetting(name=ControlSettingName.BREATHS_PER_MINUTE, value=v_bpm, min_value=v_bpm-1, max_value=v_bpm+1, timestamp=time.time()) 
    Controller.set_control(command)

    v_iphase = (0.3 + np.random.random()*0.5) * 60/v_bpm
    command = ControlSetting(name=ControlSettingName.INSPIRATION_TIME_SEC, value=v_iphase, min_value=v_iphase-1, max_value=v_iphase+1, timestamp=time.time()) 
    Controller.set_control(command)


    Controller.start()
    time.sleep(0.1)
    vals_start = Controller.get_sensors()
    time.sleep(30)                                                   # Let this run for half a minute

    Controller.stop() # consecutive stops should be ignored
    Controller.stop() 
    Controller.stop()

    vals_stop = Controller.get_sensors()
    
    assert (vals_stop.loop_counter - vals_start.loop_counter)  > 100 # In 20s, this program should go through a good couple of loops
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

    hb1 = Controller.heartbeat()
    assert hb1 > 0                                 # Test the heartbeat
    assert np.abs(hb1 - COPY_lc) <= Controller._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE  # true heart-beat should be close to the sensor loop counter







######################################################################
#########################   TEST 3  ##################################
######################################################################
#
#   More involved test, triggers a series of alarms and makes sure they
#   are raised correctly.
#
def test_alarm():
    '''
        This is a function to test the alarm functions. It triggers a series of alarms, that remain active for a while, and then are deactivated.
    '''
    Controller = get_control_module(sim_mode=True)
    Controller.start()
    time.sleep(1)

    for t in np.arange(0, 30, 0.05):

        ### Make a cascade of changes that will not trigger alarms
        if t == 0:
            command = ControlSetting(name=ControlSettingName.BREATHS_PER_MINUTE, value=17, min_value=0, max_value=30, timestamp=time.time())
            Controller.set_control(command)
            command = ControlSetting(name=ControlSettingName.INSPIRATION_TIME_SEC, value=1.5, min_value=0, max_value=2, timestamp=time.time())
            Controller.set_control(command)
        if t == 3:
            command = ControlSetting(name=ControlSettingName.PIP, value=25, min_value=0, max_value=30, timestamp=time.time())
            Controller.set_control(command)
        if t == 6:
            command = ControlSetting(name=ControlSettingName.PEEP, value=10, min_value=0, max_value=20, timestamp=time.time())
            Controller.set_control(command)

        ### Make a cascade of changes to trigger four alarms
        if t == 8:    # trigger a PIP alarm
            command = ControlSetting(name=ControlSettingName.PIP, value=25, min_value=0, max_value=5, timestamp=time.time())
            Controller.set_control(command)
        if t == 23:    #resolve the PIP alarm
            command = ControlSetting(name=ControlSettingName.PIP, value=25, min_value=0, max_value=30, timestamp=time.time())
            Controller.set_control(command)
        if (t > 8+(60/17)) and (t<23):  #Test whether it is active
            activealarms = Controller.get_active_alarms()
            assert len(activealarms.keys()) >= 1
            assert 'PIP' in activealarms.keys()

        if t == 12:    # trigger a PEEP alarm
            command = ControlSetting(name=ControlSettingName.PEEP, value=10, min_value=0, max_value=5, timestamp=time.time())
            Controller.set_control(command)
        if t == 23:    # resolve it
            command = ControlSetting(name=ControlSettingName.PEEP, value=10, min_value=0, max_value=20, timestamp=time.time())
            Controller.set_control(command)
        if (t > 12+(60/17)) and (t<23):
            activealarms = Controller.get_active_alarms()
            assert len(activealarms.keys()) >= 1
            assert 'PEEP' in activealarms.keys()

        if t == 15:    # trigger a BPM alarm
            command = ControlSetting(name=ControlSettingName.BREATHS_PER_MINUTE, value=17, min_value=0, max_value=5, timestamp=time.time())
            Controller.set_control(command)
        if t == 20:    # resolve it
            command = ControlSetting(name=ControlSettingName.BREATHS_PER_MINUTE, value=17, min_value=0, max_value=20, timestamp=time.time())
            Controller.set_control(command)
        if (t > 15+(60/17)) and (t<20):
            activealarms = Controller.get_active_alarms()
            assert len(activealarms.keys()) >= 1
            assert 'BREATHS_PER_MINUTE' in activealarms.keys()

        if t == 17:    # Trigger a INSPIRATION_TIME_SEC alarm
            command = ControlSetting(name=ControlSettingName.INSPIRATION_TIME_SEC, value=1.5, min_value=0, max_value=1, timestamp=time.time())
            Controller.set_control(command)
        if t == 22:    # resolve it
            command = ControlSetting(name=ControlSettingName.INSPIRATION_TIME_SEC, value=1.5, min_value=0, max_value=3, timestamp=time.time())
            Controller.set_control(command)
        if (t > 17+(60/17)) and (t<22):
            activealarms = Controller.get_active_alarms()
            assert len(activealarms.keys()) >= 1
            assert 'I_PHASE' in activealarms.keys()


        time.sleep(0.05)

    Controller.stop()
    
    
    #Check that the duration of the four alarms was correct
    sv = Controller.get_sensors()
    logged_alarms = Controller.get_logged_alarms()

    for a in logged_alarms:
        print(a.alarm_name)
        assert not a.is_active

        alarm_duration = a.alarm_end_time - a.alarm_start_time
        if a.alarm_name == 'PEEP':
            assert alarm_duration < (1+np.ceil(sv.breaths_per_minute * 11/60)) * 60/sv.breaths_per_minute
        if a.alarm_name == 'BREATHS_PER_MINUTE':
            assert alarm_duration < (1+np.ceil(sv.breaths_per_minute * 5/60)) * 60/sv.breaths_per_minute
        if a.alarm_name == 'I_PHASE':
            assert alarm_duration < (1+np.ceil(sv.breaths_per_minute * 5/60)) * 60/sv.breaths_per_minute
        if a.alarm_name == "PIP":
            assert alarm_duration < (1+np.ceil(sv.breaths_per_minute * 15/60)) * 60/sv.breaths_per_minute

    # And that they have been resolved/logged correctly
    assert len(Controller.get_active_alarms()) == 0
    assert len(Controller.get_logged_alarms()) >= 4
    assert len(Controller.get_alarms()) >= 4

    waveformlist_1 = Controller.get_past_waveforms() #This also should work fine
    waveformlist_2 = Controller.get_past_waveforms()

    assert len([s for s in waveformlist_1 if s is not None]) > len([s for s in waveformlist_2 if s is not None])   #Test: calling the past_waveforms clears ring buffer.

