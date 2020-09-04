# import time
# import numpy as np
# import pytest
# import random

# from pvp.common.message import SensorValues, ControlSetting
# from pvp.alarm import AlarmSeverity, Alarm
# from pvp.common.values import ValueName
# from pvp.coordinator.coordinator import get_coordinator
# from pvp.controller.control_module import get_control_module
# from pvp import prefs
# prefs.init()

# import pytest

# from pvp.common import values
# from pvp.common.message import ControlSetting, SensorValues
# from pvp.alarm import AlarmSeverity, Alarm
# from pvp.common.values import ValueName
# from pvp.controller.control_module import ControlModuleBase
# from pvp.coordinator import rpc
# from pvp.coordinator.coordinator import get_coordinator



# class HALMock(HAL):
#     def __init__(self):
#         super(HAL:, self).__init__()
#         self.control_setting = {name: ControlSetting(name, -1, -1, -1, -1) for name in (ValueName.PIP,
#                                                                                         ValueName.PIP_TIME,
#                                                                                         ValueName.PEEP,
#                                                                                         ValueName.BREATHS_PER_MINUTE,
#                                                                                         ValueName.INSPIRATION_TIME_SEC)}
#         self._running = threading.Event()

#     def is_running(self):
#         return self._running.is_set()


# def mock_get_HAL(sim_mode):
#     return HALMock()

# ######################################################################
# #########################   TEST 1  ##################################
# ######################################################################
# #
# #   Make sure the controller remembers settings, and can be started
# #   and stopped repeatedly a couple of times.
# #

# @pytest.mark.parametrize("control_setting_name", [ValueName.PIP,
#                                                   ValueName.PIP_TIME,
#                                                   ValueName.PEEP,
#                                                   ValueName.BREATHS_PER_MINUTE,
#                                                   ValueName.INSPIRATION_TIME_SEC])

# def test_control_settings(control_setting_name):
#     '''
#     This test set_controls and get_controls
#     Set and read a all five variables, make sure that they are identical.
#     '''
#     Controller = get_control_module(sim_mode=True)
#     Controller.start()
#     Controller.stop()

#     v = random.randint(10, 100)
#     v_min = random.randint(10, 100)
#     v_max = random.randint(10, 100)
#     t = time.time()

#     c_set = ControlSetting(name=control_setting_name, value=v)
#     Controller.set_control(c_set)

#     c_get = Controller.get_control(control_setting_name)

#     assert c_get.name == c_set.name
#     assert c_get.value == c_set.value

# def test_restart_controller():
#     '''
#     This tests whether the controller can be started and stopped 10 times without problems
#     '''
#     Controller = get_control_module(sim_mode=True)

#     for counter in range(10):
#         time.sleep(0.1)
#         Controller.start()
#         vals_start = Controller.get_sensors()
#         time.sleep(0.3)
#         Controller.stop() 
#         vals_stop = Controller.get_sensors()
#         assert vals_stop.loop_counter > vals_start.loop_counter








# ######################################################################
# #########################   TEST 2  ##################################
# ######################################################################
# #
# #   Make sure the controller controlls, and the controll values look 
# #   good. (i.e. close to target within narrow margins).
# #

# def test_control_dynamical():
#     ''' 
#     This tests whether the controller is controlling pressure as intended.
#     Start controller, set control values, measure whether actually there.
#     '''
#     Controller = get_control_module(sim_mode=True, simulator_dt=0.01)
#     Controller._LOOP_UPDATE_TIME = 0.01

#     vals_start = Controller.get_sensors()

#     v_peep = 5
#     command = ControlSetting(name=ValueName.PEEP, value=v_peep)
#     Controller.set_control(command)

#     v_pip = random.randint(15, 30)
#     command = ControlSetting(name=ValueName.PIP, value=v_pip)
#     Controller.set_control(command)

#     v_bpm = random.randint(6, 20)
#     command = ControlSetting(name=ValueName.BREATHS_PER_MINUTE, value=v_bpm)

#     Controller.set_control(command)

#     v_iphase = (0.3 + np.random.random()*0.5) * 60/v_bpm
#     command = ControlSetting(name=ValueName.INSPIRATION_TIME_SEC, value=v_iphase)
#     Controller.set_control(command)


#     Controller.start()
#     time.sleep(0.1)
#     vals_start = Controller.get_sensors()
#     temp_vals = Controller.get_sensors()
#     while temp_vals.breath_count < 5:
#         time.sleep(0.1)
#         temp_vals = Controller.get_sensors()

#     Controller.stop() # consecutive stops should be ignored
#     Controller.stop() 
#     Controller.stop()

#     vals_stop = Controller.get_sensors()

#     # Test whether get_sensors() return the right values
#     COPY_peep     = Controller.COPY_sensor_values.PEEP
#     COPY_pip      = Controller.COPY_sensor_values.PIP
#     COPY_fio2     = Controller.COPY_sensor_values.FIO2
#     COPY_pressure = Controller.COPY_sensor_values.PRESSURE
#     COPY_vte      = Controller.COPY_sensor_values.VTE
#     COPY_bpm      = Controller.COPY_sensor_values.BREATHS_PER_MINUTE
#     COPY_Iinsp    = Controller.COPY_sensor_values.INSPIRATION_TIME_SEC
#     COPY_tt       = Controller.COPY_sensor_values.timestamp
#     COPY_lc       = Controller.COPY_sensor_values.loop_counter

#     assert COPY_peep     == vals_stop.PEEP
#     assert COPY_pip      == vals_stop.PIP
#     assert COPY_fio2     == vals_stop.FIO2
#     assert COPY_pressure == vals_stop.PRESSURE
#     assert COPY_vte      == vals_stop.VTE
#     assert COPY_bpm      == vals_stop.BREATHS_PER_MINUTE
#     assert COPY_Iinsp    == vals_stop.INSPIRATION_TIME_SEC
#     assert COPY_tt       == vals_stop.timestamp
#     assert COPY_lc       == vals_stop.loop_counter

#     print(v_peep)
#     print(v_pip)
#     print(v_bpm)
#     print(v_iphase)

#     assert (vals_stop.loop_counter - vals_start.loop_counter)  > 100 # In 20s, this program should go through a good couple of loops
#     assert np.abs(vals_stop.PEEP - v_peep)                     < 2   # PEEP error correct within 5 cmH2O
#     assert np.abs(vals_stop.PIP - v_pip)                       < 5   # PIP  error correct within 5 cmH2O
#     assert np.abs(vals_stop.BREATHS_PER_MINUTE - v_bpm)        < 1   # Breaths per minute correct within 5 bpm
#     assert np.abs(vals_stop.INSPIRATION_TIME_SEC - v_iphase)   < 0.2 # Inspiration time, correct within 20%

#     hb1 = Controller.get_heartbeat()
#     assert hb1 > 0                                 # Test the heartbeat
#     assert np.abs(hb1 - COPY_lc) < Controller._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE + 2  # true heart-beat should be close to the sensor loop counter







# ######################################################################
# #########################   TEST 3  ##################################
# ######################################################################
# #
# # tests the logging abilits
# # #
# #
# # Test BPM to 0; shouldn't crash code shouldn't be a problem

# # Test savelogs: self._save_logs = True

# # Test bad HAL values, e.g. set pressure to inf, shouldn't break the code

# # test get_alarms() method


# # remove peep_time

# # test breath detection

# # test _control_reset()

# # make data_implausible by feeding const values, raise alarm
# # make missed_heartbeat by no querying anything for a critical time

# # test (or remove) get past waveforms

# # test interrupt
# # test is_running

# # remove/test _reset for balloon


# # test control_module device 


# ######################################################################
# #########################   TEST 4  ##################################
# ######################################################################
# #
# #   More involved test, randomized waittimes and make sure the system works
# #
# def test_erratic_dt():
#     '''
#         This is a function to test whether the controller works with random update times
#     '''
#     Controller = get_control_module(sim_mode=True)

#     # set _LOOP_UPDATE_TIME to zero and use simulator_dt so that the test actually runs good
#     Controller._LOOP_UPDATE_TIME = 0

#     Controller.start()
#     ls = []
#     test_cycles = 10
#     last_cycle = 0
#     for t in range(test_cycles):
#         Controller.simulator_dt = np.random.randint(100)/1000  # updates anywhere between 0ms and 100ms
#         vals = Controller.get_sensors()
#         while vals.breath_count <= last_cycle:
#             time.sleep(0.05)
#             vals = Controller.get_sensors()
#         last_cycle = vals.breath_count
#         ls.append(vals)
#     Controller.stop()

#     cc = Controller.get_control(control_setting_name = ValueName.PEEP)
#     target_peep = cc.value
#     cc = Controller.get_control(control_setting_name = ValueName.PIP)
#     target_pip = cc.value

#     peeps = np.unique([np.abs(s.PEEP - target_peep)  for s in ls if s.PEEP is not None])
#     pips = np.unique([np.abs(s.PIP - target_pip)  for s in ls if s.PIP is not None])

#     assert np.mean(peeps) < 8
#     assert np.mean(pips) < 8

