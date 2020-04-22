from typing import List

from vent.controller.control_module import get_control_module
from vent.coordinator.ipc import IPC
from vent.common.message import SensorValues, ControlSettings, Alarm, ControlSettingName, IPCMessageCommand
from vent.coordinator.process_manager import ProcessManager


class CoordinatorBase:
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

    def get_controls(self, control_setting_name: ControlSettingName) -> ControlSettings:
        pass

    def get_msg_timestamp(self):
        # return timestamp of last message
        pass

    def do_process(self, command: IPCMessageCommand):
        # TODO: we need to test these
        # start / stop / reset process
        if command == IPCMessageCommand.START:
            self.control_module.start()
        elif command == IPCMessageCommand.STOP:
            self.control_module.stop()
        else:
            raise KeyError("Error: undefined action" + str(command))


class CoordinatorLocal(CoordinatorBase):
    def __init__(self, sim_mode=False):
        super().__init__(sim_mode=sim_mode)
        self.thread_id = None  # TODO: do I need a thread

    def set_controls(self, control_settings: ControlSettings):
        self.control_module.set_controls(control_settings)
        self.last_message_timestamp = control_settings.timestamp

    def get_controls(self, control_setting_name: ControlSettingName) -> ControlSettings:
        return self.control_module.get_controls(control_setting_name)

    def get_sensors(self) -> SensorValues:
        sensor_values = self.control_module.get_sensors()
        self.last_message_timestamp = sensor_values.timestamp
        return sensor_values

    def get_logged_alarms(self) -> List[Alarm]:
        return self.control_module.get_logged_alarms()

    def get_active_alarms(self) -> List[Alarm]:
        return self.control_module.get_active_alarms()

    def clear_logged_alarms(self):
        return self.control_module.clear_logged_alarms()

    def get_msg_timestamp(self):
        return self.last_message_timestamp

    def do_process(self, command):
        super().do_process(command)


class CoordinatorRemote(CoordinatorBase):
    def __init__(self, sim_mode=False):
        super().__init__(sim_mode=sim_mode)
        # TODO: pass max_heartbeat_interval
        self.process_manager = ProcessManager()
        self.rpc = IPC()
        raise NotImplementedError


def get_coordinator(single_process=False, sim_mode=False):
    if single_process == True:
        return CoordinatorLocal(sim_mode)
    else:
        return CoordinatorRemote(sim_mode)
