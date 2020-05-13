# TODO: this is a unit test, need to add integration test
import random
import socket
import threading
import time
from unittest.mock import patch, Mock

import pytest

from vent.common import values
from vent.common.message import ControlSetting, SensorValues
from vent.alarm import AlarmSeverity, Alarm
from vent.common.values import ValueName
from vent.controller.control_module import ControlModuleBase
from vent.coordinator import rpc
from vent.coordinator.coordinator import get_coordinator


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0


class ControlModuleMock(ControlModuleBase):
    def __init__(self):
        super(ControlModuleMock, self).__init__()
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

    def get_active_alarms(self):
        return {ValueName.PIP: Alarm(ValueName.PIP, True, AlarmSeverity.HIGH, time.time(), None)}

    def get_logged_alarms(self):
        return [Alarm(ValueName.PIP, False, AlarmSeverity.HIGH, time.time(), None)]


def mock_get_control_module(sim_mode):
    return ControlModuleMock()


@pytest.mark.parametrize("control_setting_name", values.controllable_values)
@patch('vent.controller.control_module.get_control_module', mock_get_control_module, Mock())
def test_local_coordinator(control_setting_name):
    coordinator = get_coordinator(single_process=True, sim_mode=True)
    coordinator.start()
    #while not coordinator.is_running():
    #    pass
    t = time.time()
    v = random.randint(10, 100)
    v_min = v - 5
    v_max = v + 5

    # TODO: add test for test reference

    c = ControlSetting(name=control_setting_name, value=v, min_value=v_min, max_value=v_max, timestamp=t)
    coordinator.set_control(c)

    c_read = coordinator.get_control(control_setting_name)
    assert c_read.name == c.name
    assert c_read.value == c.value
    assert c_read.min_value == c.min_value
    assert c_read.max_value == c.max_value
    assert c_read.timestamp == c.timestamp

@pytest.mark.timeout(10)
@pytest.mark.parametrize("control_setting_name", values.controllable_values)
@patch('vent.controller.control_module.get_control_module', mock_get_control_module, Mock())
def test_remote_coordinator(control_setting_name):
    # wait before
    #while not is_port_in_use(rpc.default_port):
    #    time.sleep(1)
    coordinator = get_coordinator(single_process=False, sim_mode=True)
    #TODO need to wait for rpc client start?
    #time.sleep(1)
    coordinator.start()
    #while not coordinator.is_running():
    #    pass
    t = time.time()
    v = random.randint(10, 100)
    v_min = v - 5
    v_max = v + 5

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


@pytest.mark.timeout(10)
def test_process_manager():
    # wait before
    #while not is_port_in_use(rpc.default_port):
    #    time.sleep(1)
    coordinator = get_coordinator(single_process=False, sim_mode=True)
    # TODO need to wait for rpc client start?
    #time.sleep(1)
    coordinator.start()
    #while not coordinator.is_running():
    #    pass

    assert coordinator.is_running() == True
    coordinator.process_manager.try_stop_process()
    assert coordinator.process_manager.child_pid is None

    try:
        coordinator.is_running()
        assert False
    except ConnectionRefusedError:
        pass
    except Exception:
        assert False

    coordinator.process_manager.start_process()

    #time.sleep(1)
    assert coordinator.process_manager.child_pid is not None
    assert coordinator.is_running() == False

    coordinator.process_manager.restart_process()

    #time.sleep(1)
    assert coordinator.process_manager.child_pid is not None
    assert coordinator.is_running() == False


def test_local_sensors():
    coordinator = get_coordinator(single_process=True, sim_mode=True)
    coordinator.start()
    #while not coordinator.is_running():
    #    pass

    sensor_values = coordinator.get_sensors()
    assert isinstance(sensor_values, SensorValues)

    values_dict = sensor_values.to_dict()
    # if all of the values are none, then this is just a blank object
    # FIXME: No longer relevant as blank SensorValues cannot be created anymore -- should ensure no values are None
    assert(not all([v is None for v in values_dict.values()]))
    for k, v in values_dict.items():
        assert isinstance(k, ValueName) or (k in sensor_values.additional_values)
        assert isinstance(v, int) or isinstance(v, float) or v is None

@pytest.mark.timeout(10)
def test_remote_sensors():
    # wait before
    #while not is_port_in_use(rpc.default_port):
    #    time.sleep(1)
    coordinator = get_coordinator(single_process=False, sim_mode=True)
    # TODO need to wait for rpc client start?
    #time.sleep(1)
    coordinator.start()
    #while not coordinator.is_running():
    #    pass

    sensor_values = coordinator.get_sensors()
    assert isinstance(sensor_values, SensorValues)
    values_dict = sensor_values.to_dict()
    # if all of the values are none, then this is just a blank object
    assert(not all([v is None for v in values_dict.values()]))

    for k, v in sensor_values.to_dict().items():
        assert isinstance(k, ValueName) or (k in sensor_values.additional_values)
        assert isinstance(v, int) or isinstance(v, float) or v is None


# def test_local_alarms():
#     coordinator = get_coordinator(single_process=True, sim_mode=True)
#     coordinator.start()
#     #while not coordinator.is_running():
#     #    pass
#
#     alarms = coordinator.get_active_alarms()
#     assert isinstance(alarms, dict)
#     for k, v in alarms.items():
#         assert isinstance(v, Alarm)
#
#     alarms = coordinator.get_logged_alarms()
#     assert isinstance(alarms, list)
#     for a in alarms:
#         assert isinstance(a, Alarm)

# @pytest.mark.timeout(10)
# def test_remote_alarms():
#     # wait before
#     #while not is_port_in_use(rpc.default_port):
#     #    time.sleep(1)
#     coordinator = get_coordinator(single_process=False, sim_mode=True)
#     # TODO need to wait for rpc client start?
#     #time.sleep(1)
#     coordinator.start()
#     #while not coordinator.is_running():
#     #    pass
#
#     alarms = coordinator.get_active_alarms()
#     assert isinstance(alarms, dict)
#     for k, v in alarms.items():
#         assert isinstance(v, Alarm)
#
#     alarms = coordinator.get_logged_alarms()
#     assert isinstance(alarms, list)
#     for a in alarms:
#         assert isinstance(a, Alarm)
