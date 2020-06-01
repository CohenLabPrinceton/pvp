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

## Do things
command = ControlSetting(name=ValueName.PEEP, value=30)
Controller.set_control(command)
command = ControlSetting(name=ValueName.PIP, value=48)
Controller.set_control(command)
command = ControlSetting(name=ValueName.BREATHS_PER_MINUTE, value=15)
Controller.set_control(command)
command = ControlSetting(name=ValueName.INSPIRATION_TIME_SEC, value = 0.8)
Controller.set_control(command)
##

for t in np.arange(0, 60,0.05):
    if t%5==0:  # ask for a heartbeat from thread every 5 seconds
        print(t)

    vals = Controller.get_sensors()
    print(vals.PRESSURE)
    time.sleep(0.05)

Controller.stop()
