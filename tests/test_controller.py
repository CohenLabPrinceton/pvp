import time
import numpy as np
import pytest
import random

from vent.common.message import SensorValues, ControlSetting, Alarm, AlarmSeverity, ControlSettingName
from vent.coordinator.coordinator import get_coordinator
from vent.controller.control_module import get_control_module


def test_control_dynamical():
    ''' 
    Start controller, set control values, measure whether actually there
    '''
    Controller = get_control_module(sim_mode=True)

    Controller._NUMBER_CONTROLL_LOOPS_UNTIL_UPDATE = 2

    vals_start = Controller.get_sensors()

    v_peep = random.randint(0, 15)
    command = ControlSetting(name=ControlSettingName.PEEP, value=v_peep, min_value=v_peep-1, max_value=v_peep+1, timestamp=time.time())
    Controller.set_control(command)

    v_pip = random.randint(15, 30)
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


# self.COPY_sensor_values = SensorValues(pip=self._DATA_PIP,
#                                   peep=self._DATA_PEEP,
#                                   fio2=self.Balloon.fio2,
#                                   temp=self.Balloon.temperature,
#                                   humidity= self.Balloon.humidity,
#                                   pressure=self.Balloon.current_pressure,
#                                   vte=self._DATA_VTE,
#                                   breaths_per_minute=self._DATA_BPM,
#                                   inspiration_time_sec=self._DATA_I_PHASE,
#                                   timestamp=time.time(),
#                                   loop_counter = self._loop_counter)
# self.__SET_I_PHASE = 1.3    # Target duration of inspiratory phase)
# get sensors
# get alarms
# get active alarms
# get logged alarms
# set controls
# get control
# test _PID update?
# repeated stars and stops of the mainloop, make sure heartbeat increases
# For settings, try good and bad values. Make sure that it works


