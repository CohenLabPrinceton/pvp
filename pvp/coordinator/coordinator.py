import pickle
import threading
from typing import List, Dict
import typing

import pvp
import pvp.controller.control_module
from pvp.common.message import ControlSetting
from pvp.alarm import Alarm
from pvp.common.message import SensorValues
from pvp.common.values import ValueName
from pvp.common.loggers import init_logger
from pvp.coordinator.process_manager import ProcessManager
from pvp.coordinator.rpc import get_rpc_client



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


    def get_sensors(self) -> SensorValues:                                  # pragma: no cover
        pass

    def get_alarms(self) -> typing.Union[None, typing.Tuple[Alarm]]:        # pragma: no cover
        pass

    def set_control(self, control_setting: ControlSetting):                 # pragma: no cover
        pass

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:  # pragma: no cover
        pass

    def set_breath_detection(self, breath_detection: bool):                 # pragma: no cover
        pass

    def get_breath_detection(self) -> bool:  # pragma: no cover
        pass

    def start(self):                         # pragma: no cover
        pass

    def is_running(self) -> bool:            # pragma: no cover
        pass

    def kill(self):                          # pragma: no cover
        pass

    def stop(self):                          # pragma: no cover
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
        self.control_module = pvp.controller.control_module.get_control_module(sim_mode)


    def get_sensors(self) -> SensorValues:

        # return res
        return self.control_module.get_sensors()

    def get_alarms(self) -> typing.Union[None, typing.Tuple[Alarm]]:
        return self.control_module.get_alarms()

    def set_control(self, control_setting: ControlSetting):
        self.control_module.set_control(control_setting)

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:
        return self.control_module.get_control(control_setting_name)

    def set_breath_detection(self, breath_detection: bool):
        self.control_module.set_breath_detection(breath_detection)

    def get_breath_detection(self) -> bool:
        return self.control_module.get_breath_detection()

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

    def kill(self): # pragma: no cover
        # dont need to do anything since should just go away on its own
        pass



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

    def get_alarms(self) -> typing.Union[None, typing.Tuple[Alarm]]:
        controller_alarms = pickle.loads(self.rpc_client.get_alarms().data)
        return controller_alarms

    def set_control(self, control_setting: ControlSetting):
        pickled_args = pickle.dumps(control_setting)
        self.rpc_client.set_control(pickled_args)

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:
        pickled_args = pickle.dumps(control_setting_name)
        pickled_res = self.rpc_client.get_control(pickled_args).data
        return pickle.loads(pickled_res)

    def set_breath_detection(self, breath_detection: bool):
        pickled_args = pickle.dumps(breath_detection)
        self.rpc_client.set_breath_detection(pickled_args)

    def get_breath_detection(self) -> bool:
        return pickle.loads(self.rpc_client.get_breath_detection().data)

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
        except ConnectionRefusedError:  # pragma: no cover
            pass

    def kill(self):
        """
        Stop the coordinator and end the whole program
        """
        self.stop()
        self.process_manager.try_stop_process()

    def __del__(self):
        self.kill()


def get_coordinator(single_process=False, sim_mode=False) -> CoordinatorBase:
    if single_process:
        return CoordinatorLocal(sim_mode)
    else:
        return CoordinatorRemote(sim_mode)
