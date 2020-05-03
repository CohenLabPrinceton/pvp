# TODO: this is a unit test, need to add integration test
import random
import time
from unittest.mock import patch, Mock

import pytest

from vent.common.message import ControlSetting, SensorValues
from vent.common.values import ValueName
from vent.common import values
from vent.controller.control_module import ControlModuleBase
from vent.coordinator.coordinator import get_coordinator


class ControlModuleMock(ControlModuleBase):
    def __init__(self):
        self.control_setting = {name: ControlSetting(name, -1, -1, -1, -1) for name in (ValueName.PIP,
                                                                                        ValueName.PIP_TIME,
                                                                                        ValueName.PEEP,
                                                                                        ValueName.BREATHS_PER_MINUTE,
                                                                                        ValueName.INSPIRATION_TIME_SEC)}

    def get_sensors(self):
        return SensorValues(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:
        return self.control_setting[control_setting_name]

    def set_control(self, control_setting: ControlSetting):
        self.control_setting[control_setting.name] = control_setting


def mock_get_control_module(sim_mode):
    return ControlModuleMock()


@pytest.mark.parametrize("single_process,control_setting_name", ((single_process, name) for single_process in (True, False) for name in values.controllable_values))
@patch('vent.controller.control_module.get_control_module', mock_get_control_module, Mock())
def test_coordinator(single_process, control_setting_name):
    coordinator = get_coordinator(single_process=single_process, sim_mode=True)
    coordinator.start()
    # TODO: why need this sleep time?
    time.sleep(1)
    # while not coordinator.is_running():
    #     pass
    t = time.time()
    v = random.randint(10, 100)
    v_min = v - 5
    v_max = v + 5

    # TODO: add test for start/stop
    # TODO: add test for test reference

    c = ControlSetting(name=control_setting_name, value=v, min_value=v_min, max_value=v_max, timestamp=t)
    coordinator.set_control(c)

    # TODO: this should be tight
    time.sleep(1)

    c_read = coordinator.get_control(control_setting_name)
    assert c_read.name == c.name
    assert c_read.value == c.value
    assert c_read.min_value == c.min_value
    assert c_read.max_value == c.max_value
    assert c_read.timestamp == c.timestamp

# TODO: test racing condition