from typing import List

from vent.coordinator.control_module import get_control_module
from vent.coordinator.ipc import IPC
from vent.coordinator.message import SensorValues, ControlSettings, Alarm
from vent.coordinator.process_manager import ProcessManager


class UIControlModuleBase:
    def __init__(self, sim_mode=False):
        # get_ui_control_module handles single_process flag
        self.control_module = get_control_module(sim_mode)
        self.sensor_values = None
        self.alarms = None
        self.control_settings = None
        self.last_message_timestamp = None

    def get_sensors(self) -> SensorValues:
        # returns SensorValues struct
        pass

    # def get_alarms(self) -> List[Alarm]:
    #     # returns list of Alarm structs
    #     pass

    def get_active_alarms(self) -> List[Alarm]:
        pass

    def get_logged_alarms(self) -> List[Alarm]:
        pass

    def clear_logged_alarms(self):
        pass

    def set_controls(self, control_settings: ControlSettings):
        # takes ControlSettings struct
        pass

    def get_msg_timestamp(self):
        # return timestamp of last message
        pass

    def do_process(self, command):
        # start / stop / reset process
        pass


class UIControlModuleLocal(UIControlModuleBase):
    def __init__(self, sim_mode=False):
        super().__init__(sim_mode=sim_mode)
        self.thread_id = None  # TODO: do I have a thread
        raise NotImplementedError


class UIControlModuleRemote(UIControlModuleBase):
    def __init__(self, sim_mode=False):
        super().__init__(sim_mode=sim_mode)
        # TODO: pass max_heartbeat_interval
        self.process_manager = ProcessManager()
        self.rpc = IPC()
        raise NotImplementedError


def get_ui_control_module(single_process=False, sim_mode=False):
    if single_process == True:
        return UIControlModuleLocal(sim_mode)
    else:
        return UIControlModuleRemote(sim_mode)
