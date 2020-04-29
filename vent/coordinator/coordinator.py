import time
import threading
from typing import List

from vent.common.message import SensorValues, ControlSetting, Alarm, ControlSettingName, IPCMessageCommand
from vent.controller.control_module import get_control_module
from vent.coordinator.ipc import IPC
from vent.coordinator.process_manager import ProcessManager


class CoordinatorBase:
    def __init__(self, sim_mode=False):
        # get_ui_control_module handles single_process flag
        self.control_module = get_control_module(sim_mode)
        self.sensor_values = None
        self.alarms = None
        self.control_settings = {}
        self.tentative_control_settings = {}
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

    def set_control(self, control_setting: ControlSetting):
        # takes ControlSetting struct
        pass

    def get_control(self, control_setting_name: ControlSettingName) -> ControlSetting:
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
        """

        Args:
            sim_mode:

        Attributes:
            stopping (:class:`threading.Event`): ``.set()`` when thread should stop

        """
        super().__init__(sim_mode=sim_mode)
        self.stopping = threading.Event()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.start, daemon=True)
        self.thread.start()
        self.thread_id = self.thread.ident

    def __del__(self):
        self.thread.join()

    def set_control(self, control_setting: ControlSetting):
        self.lock.acquire()
        self.tentative_control_settings[control_setting.name] = control_setting
        self.lock.release()

    def get_control(self, control_setting_name: ControlSettingName) -> ControlSetting:
        self.lock.acquire()
        control_setting = self.control_settings[control_setting_name]
        self.lock.release()
        return control_setting

    def get_sensors(self) -> SensorValues:
        self.lock.acquire()
        sensor_values = self.sensor_values
        self.lock.release()
        return sensor_values

    def get_logged_alarms(self) -> List[Alarm]:
        return self.control_module.get_logged_alarms()

    def get_active_alarms(self) -> List[Alarm]:
        return self.control_module.get_active_alarms()

    def clear_logged_alarms(self):
        return self.control_module.clear_logged_alarms()

    def get_msg_timestamp(self):
        self.lock.acquire()
        last_message_timestamp = self.last_message_timestamp
        self.lock.release()
        return last_message_timestamp

    def do_process(self, command):
        super().do_process(command)

    def start(self):

        if not self.control_module.running():
            self.do_process(IPCMessageCommand.START)


        while not self.stopping.is_set():
            sensor_values = self.control_module.get_sensors()
            self.lock.acquire()
            self.sensor_values = sensor_values
            self.last_message_timestamp = sensor_values.timestamp
            self.lock.release()
            for name in ControlSettingName:
                self.lock.acquire()
                if (name not in self.control_settings):
                    self.lock.release()
                    control_setting = self.control_module.get_control(name)
                    self.lock.acquire()
                    self.control_settings[name] = control_setting
                    self.lock.release()
                else:
                    self.lock.release()

                self.lock.acquire()
                if name in self.tentative_control_settings and self.tentative_control_settings[name] != self.control_settings[
                            name]:
                    tentative_control_setting = self.tentative_control_settings[name]
                    self.lock.release()
                    self.control_module.set_control(tentative_control_setting)
                    self.lock.acquire()
                    self.control_settings[name] = self.control_module.get_control(name)
                    self.lock.release()
                else:
                    self.lock.release()
            # sleep 10 ms
            time.sleep(0.01)

    def stop(self):
        self.stopping.set()


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
