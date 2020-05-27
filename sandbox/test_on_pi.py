import sys
import time
import numpy as np
import pylab as pl
import tables as pytb
import os
sys.path.append('../')

from vent.controller.control_module import get_control_module, Balloon_Simulator
from vent.common.message import SensorValues, ControlSetting
from vent.common.values import ValueName, CONTROL

Controller = get_control_module(sim_mode=False)
Controller.start()
ls = []
tt = []
t0 = time.time()

for t in np.arange(0, 10,0.05):
    if t%5==0:  # ask for a heartbeat from thread every 5 seconds
        print(t)

    ## Do things
    command = ControlSetting(name=ValueName.PEEP, value=3, min_value=1, max_value=4, timestamp=time.time())
    Controller.set_control(command)
    command = ControlSetting(name=ValueName.PIP, value=40, min_value=38, max_value=42, timestamp=time.time())
    Controller.set_control(command)
    command = ControlSetting(name=ValueName.BREATHS_PER_MINUTE, value=20, min_value=19, max_value=21, timestamp=time.time())
    Controller.set_control(command)
    v_iphase = 0.4 * 60/20  #0.3 and 0.8
    command = ControlSetting(name=ValueName.INSPIRATION_TIME_SEC, value=v_iphase, min_value=v_iphase - 1, max_value=v_iphase + 1, timestamp=time.time())
    Controller.set_control(command)
    ##

    vals = Controller.get_sensors()
    ls.append(vals)
    tt.append(time.time()  - t0)
    time.sleep(0.05)

Controller.stop()
