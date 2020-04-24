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
