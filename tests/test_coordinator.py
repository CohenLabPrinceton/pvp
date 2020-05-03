# TODO: this is a unit test, need to add integration test
import time
from unittest.mock import patch, Mock
from vent.common.message import ControlSetting, SensorValues
from vent.common.values import ValueName
from vent.coordinator.coordinator import get_coordinator
from vent.controller.control_module import get_control_module, ControlModuleBase
import numpy as np
import pytest
import random


class ControlModuleMock(ControlModuleBase):
    def __init__(self):
        self.control_setting = {name: ControlSetting(name, -1, -1, -1, -1) for name in (ValueName.PIP,
                                                                                        ValueName.PIP_TIME,
                                                                                        ValueName.PEEP,
                                                                                        ValueName.BREATHS_PER_MINUTE,
                                                                                        ValueName.INSPIRATION_TIME_SEC)}

    def get_sensors(self):
        return SensorValues()

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:
        return self.control_setting[control_setting_name]

    def set_control(self, control_setting: ControlSetting):
        self.control_setting[control_setting.name] = control_setting


def mock_get_control_module(sim_mode):
    return ControlModuleMock()


@pytest.mark.parametrize("control_setting_name", [ValueName.PIP,
                                                  ValueName.PIP_TIME,
                                                  ValueName.PEEP,
                                                  ValueName.BREATHS_PER_MINUTE,
                                                  ValueName.INSPIRATION_TIME_SEC])
                                                  
@patch('vent.controller.control_module.get_control_module', mock_get_control_module, Mock())

def test_coordinator(control_setting_name):

    coordinator = get_coordinator(single_process=True, sim_mode=True)
    t = time.time()
    v = random.randint(10, 100)
    v_min = v - 5
    v_max = v + 5

    # TODO: add test for start/stop
    # TODO: add test for test reference

    c = ControlSetting(name=control_setting_name, value=v, min_value=v_min, max_value=v_max, timestamp=t)
    coordinator.set_control(c)

    # TODO: this should be tight
    time.sleep(0.1)

    c_read = coordinator.get_control(control_setting_name)
    assert c_read.name == c.name
    assert c_read.value == c.value
    assert c_read.min_value == c.min_value
    assert c_read.max_value == c.max_value
    assert c_read.timestamp == c.timestamp
