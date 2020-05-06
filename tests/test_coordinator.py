# TODO: this is a unit test, need to add integration test
import random
import socket
import threading
import time
from unittest.mock import patch, Mock

import pytest

from vent.common import values
from vent.common.message import ControlSetting, SensorValues, SensorValue
from vent.common.values import ValueName
from vent.controller.control_module import ControlModuleBase
from vent.coordinator import rpc
from vent.coordinator.coordinator import get_coordinator


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0


class ControlModuleMock(ControlModuleBase):
    def __init__(self):
        self.control_setting = {name: ControlSetting(name, -1, -1, -1, -1) for name in (ValueName.PIP,
                                                                                        ValueName.PIP_TIME,
                                                                                        ValueName.PEEP,
                                                                                        ValueName.BREATHS_PER_MINUTE,
                                                                                        ValueName.INSPIRATION_TIME_SEC)}
        self._running = threading.Event()

    def is_running(self):
        return self._running.is_set()

    def start(self):
        self._running.set()

    def get_sensors(self):
        self._running.wait()
        return SensorValues(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:
        self._running.wait()
        return self.control_setting[control_setting_name]

    def set_control(self, control_setting: ControlSetting):
        self._running.wait()
        self.control_setting[control_setting.name] = control_setting


def mock_get_control_module(sim_mode):
    return ControlModuleMock()


@pytest.mark.parametrize("control_setting_name", values.controllable_values)
@patch('vent.controller.control_module.get_control_module', mock_get_control_module, Mock())
def test_local_coordinator(control_setting_name):
    coordinator = get_coordinator(single_process=True, sim_mode=True)
    coordinator.start()
    while not coordinator.is_running():
        pass
    t = time.time()
    v = random.randint(10, 100)
    v_min = v - 5
    v_max = v + 5

    # TODO: add test for stop
    # TODO: add test for test reference

    c = ControlSetting(name=control_setting_name, value=v, min_value=v_min, max_value=v_max, timestamp=t)
    coordinator.set_control(c)

    c_read = coordinator.get_control(control_setting_name)
    assert c_read.name == c.name
    assert c_read.value == c.value
    assert c_read.min_value == c.min_value
    assert c_read.max_value == c.max_value
    assert c_read.timestamp == c.timestamp


@pytest.mark.parametrize("control_setting_name", values.controllable_values)
@patch('vent.controller.control_module.get_control_module', mock_get_control_module, Mock())
def test_remote_coordinator(control_setting_name):
    # wait before
    while not is_port_in_use(rpc.default_port):
        time.sleep(1)
    coordinator = get_coordinator(single_process=False, sim_mode=True)
    #TODO need to wait for rpc client start?
    time.sleep(1)
    coordinator.start()
    while not coordinator.is_running():
        pass
    t = time.time()
    v = random.randint(10, 100)
    v_min = v - 5
    v_max = v + 5

    # TODO: add test for stop
    # TODO: add test for test reference
    # TODO: test racing condition

    c = ControlSetting(name=control_setting_name, value=v, min_value=v_min, max_value=v_max, timestamp=t)
    coordinator.set_control(c)

    c_read = coordinator.get_control(control_setting_name)
    assert c_read.name == c.name
    assert c_read.value == c.value
    assert c_read.min_value == c.min_value
    assert c_read.max_value == c.max_value
    assert c_read.timestamp == c.timestamp

    coordinator.process_manager.stop_process()


def test_process_manager():
    # wait before
    while not is_port_in_use(rpc.default_port):
        time.sleep(1)
    coordinator = get_coordinator(single_process=False, sim_mode=True)
    # TODO need to wait for rpc client start?
    time.sleep(1)
    coordinator.start()
    while not coordinator.is_running():
        pass

    sensor_values = coordinator.get_sensors()
    assert isinstance(sensor_values, dict)
    for k, v in sensor_values.items():
        assert isinstance(k, ValueName)
        assert isinstance(v, SensorValue)

    coordinator.process_manager.stop_process()
    assert coordinator.process_manager.child_pid is None

    coordinator.process_manager.start_process()
    assert coordinator.process_manager.child_pid is not None

    sensor_values = coordinator.get_sensors()
    assert isinstance(sensor_values, dict)
    for k, v in sensor_values.items():
        assert isinstance(k, ValueName)
        assert isinstance(v, SensorValue)

    coordinator.process_manager.restart_process()
    assert coordinator.process_manager.child_pid is not None

    sensor_values = coordinator.get_sensors()
    assert isinstance(sensor_values, dict)
    for k, v in sensor_values.items():
        assert isinstance(k, ValueName)
        assert isinstance(v, SensorValue)
