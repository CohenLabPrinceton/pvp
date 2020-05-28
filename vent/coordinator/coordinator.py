import pickle
import threading
from typing import List, Dict

import vent
import vent.controller.control_module
from vent.common.message import ControlSetting
from vent.alarm import Alarm
from vent.common.message import SensorValues
from vent.common.values import ValueName
from vent.common.logging import init_logger
from vent.coordinator.process_manager import ProcessManager
from vent.coordinator.rpc import get_rpc_client



class CoordinatorBase:
    def __init__(self, sim_mode=False):
        # get_ui_control_module handles single_process flag
        # self.lock = threading.Lock()
        self.logger = init_logger(__name__)
        self.logger.info('coordinator init')

    # TODO: do we still need this
    # def get_msg_timestamp(self):
    #     # return timestamp of last message
    #     with self.lock:
    #         last_message_timestamp = self.last_message_timestamp
    #     return last_message_timestamp


    def get_sensors(self) -> SensorValues:
        pass

    # def get_active_alarms(self) -> Dict[str, Alarm]:
    #     pass
    #
    # def get_logged_alarms(self) -> List[Alarm]:
    #     pass
    #
    # def clear_logged_alarms(self):
    #     pass

    def set_control(self, control_setting: ControlSetting):
        pass

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:
        pass

    def start(self):
        pass

    def is_running(self) -> bool:
        pass

    def stop(self):
        pass

class CoordinatorLocal(CoordinatorBase):
    def __init__(self, sim_mode=False):
        """

        Args:
            sim_mode:

        Attributes:
            _is_running (:class:`threading.Event`): ``.set()`` when thread should stop

        """
        super().__init__(sim_mode=sim_mode)
        self.control_module = vent.controller.control_module.get_control_module(sim_mode)


    def get_sensors(self) -> SensorValues:

        # return res
        return self.control_module.get_sensors()

    # def get_active_alarms(self) -> Dict[str, Alarm]:
    #     return self.control_module.get_active_alarms()

    # def get_logged_alarms(self) -> List[Alarm]:
    #     return self.control_module.get_logged_alarms()

    # def clear_logged_alarms(self):
    #     # TODO: implement this
    #     raise NotImplementedError

    def set_control(self, control_setting: ControlSetting):
        self.control_module.set_control(control_setting)

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:
        return self.control_module.get_control(control_setting_name)

    def start(self):
        """
        Start the coordinator.
        This does a soft start (not allocating a process).
        """
        self.control_module.start()

    def is_running(self) -> bool:
        """
        Test whether the whole system is running
        """
        return self.control_module._running

    def stop(self):
        """
        Stop the coordinator.
        This does a soft stop (not kill a process)
        """
        self.control_module.stop()


class CoordinatorRemote(CoordinatorBase):
    def __init__(self, sim_mode=False):
        super().__init__(sim_mode=sim_mode)
        # TODO: according to documentation, pass max_heartbeat_interval?
        self.process_manager = ProcessManager(sim_mode)
        self.rpc_client = get_rpc_client()
        # TODO: make sure the ipc connection is setup. There should be a clever method

    def get_sensors(self) -> SensorValues:
        sensor_values = pickle.loads(self.rpc_client.get_sensors().data)
        return sensor_values

    # def get_active_alarms(self) -> Dict[str, Alarm]:
    #     pickled_res = self.rpc_client.get_active_alarms().data
    #     return pickle.loads(pickled_res)
    #
    # def get_logged_alarms(self) -> List[Alarm]:
    #     pickled_res = self.rpc_client.get_logged_alarms().data
    #     return pickle.loads(pickled_res)
    #
    # def clear_logged_alarms(self):
    #     # TODO: implement this
    #     raise NotImplementedError

    def set_control(self, control_setting: ControlSetting):
        pickled_args = pickle.dumps(control_setting)
        self.rpc_client.set_control(pickled_args)

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:
        pickled_args = pickle.dumps(control_setting_name)
        pickled_res = self.rpc_client.get_control(pickled_args).data
        return pickle.loads(pickled_res)

    def start(self):
        """
        Start the coordinator.
        This does a soft start (not allocating a process).
        """
        self.rpc_client.start()

    def is_running(self) -> bool:
        """
        Test whether the whole system is running
        """
        return self.rpc_client.is_running()

    def stop(self):
        """
        Stop the coordinator.
        This does a soft stop (not kill a process)
        """
        try:
            self.rpc_client.stop()
        except ConnectionRefusedError:
            pass
        self.process_manager.try_stop_process()

    def __del__(self):
        self.stop()


def get_coordinator(single_process=False, sim_mode=False) -> CoordinatorBase:
    if single_process:
        return CoordinatorLocal(sim_mode)
    else:
        return CoordinatorRemote(sim_mode)
