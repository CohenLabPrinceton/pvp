import time
from vent.common.message import ControlSetting, ControlSettingName
from vent.coordinator.coordinator import get_coordinator
from vent.controller.control_module import get_control_module
import numpy as np
import pytest
import random


def test_controller():

    Controller = get_control_module(sim_mode=True)

    Controller.start()
    vals_start = Controller.get_sensors()

    time.sleep(1)

    vals_stop = Controller.get_sensors()
    Controller.stop()

    assert vals_start.loop_counter < vals_stop.loop_counter


# get sensors
# get alarms
# get active alarms
# get logged alarms
# set controls
# get control
# test _PID update?
# repeated stars and stops of the mainloop, make sure heartbeat increases
# For settings, try good and bad values. Make sure that it works