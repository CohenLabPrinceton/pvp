import time
import threading
from typing import List, Dict

import vent
from vent.common.message import SensorValues, ControlSetting, Alarm
from vent.common.values import ValueName
from vent.common import values
from vent.common.message import SensorValueNew
# from vent.controller.control_module import get_control_module
from vent.coordinator.ipc import IPC, IPCMessage, IPCCommand
from vent.coordinator.process_manager import ProcessManager


class CoordinatorBase:
    def __init__(self, sim_mode=False):
        # get_ui_control_module handles single_process flag
        # TODO: SHARED_ is a better prefix than COPY_, as not all fields are copy
        self.COPY_sensor_values = None
        self.COPY_alarms = None
        self.COPY_active_alarms = {}
        self.COPY_logged_alarms = []
        self.COPY_control_settings = {}
        self.COPY_tentative_control_settings = {}
        self.COPY_last_message_timestamp = None
        self.lock = threading.Lock()
        self._is_running = threading.Event()

    def get_sensors(self) -> Dict[ValueName, SensorValueNew]:
        with self.lock:
            sensor_values = self.COPY_sensor_values
        res = {
            ValueName.PIP: SensorValueNew(ValueName.PIP, sensor_values.pip, sensor_values.timestamp,
                                          sensor_values.loop_counter),
            ValueName.PEEP: SensorValueNew(ValueName.PEEP, sensor_values.peep, sensor_values.timestamp,
                                           sensor_values.loop_counter),
            ValueName.FIO2: SensorValueNew(ValueName.FIO2, sensor_values.fio2, sensor_values.timestamp,
                                           sensor_values.loop_counter),
            ValueName.TEMP: SensorValueNew(ValueName.TEMP, sensor_values.temp, sensor_values.timestamp,
                                           sensor_values.loop_counter),
            ValueName.HUMIDITY: SensorValueNew(ValueName.HUMIDITY, sensor_values.humidity, sensor_values.timestamp,
                                               sensor_values.loop_counter),
            ValueName.PRESSURE: SensorValueNew(ValueName.PRESSURE, sensor_values.pressure, sensor_values.timestamp,
                                               sensor_values.loop_counter),
            ValueName.VTE: SensorValueNew(ValueName.VTE, sensor_values.vte, sensor_values.timestamp,
                                          sensor_values.loop_counter),
            ValueName.BREATHS_PER_MINUTE: SensorValueNew(ValueName.BREATHS_PER_MINUTE, sensor_values.breaths_per_minute,
                                                         sensor_values.timestamp, sensor_values.loop_counter),
            ValueName.INSPIRATION_TIME_SEC: SensorValueNew(ValueName.INSPIRATION_TIME_SEC,
                                                           sensor_values.inspiration_time_sec, sensor_values.timestamp,
                                                           sensor_values.loop_counter),
        }
        return res

    def get_active_alarms(self) -> Dict[str, Alarm]:
        # TODO: the dict key should be better as class instead of str
        with self.lock:
            active_alarms = self.COPY_active_alarms.copy()  # Make sure to return a copy
        return active_alarms

    def get_logged_alarms(self) -> List[Alarm]:
        with self.lock:
            logged_alarms = self.COPY_logged_alarms.copy()  # Make sure to return a copy
        return logged_alarms

    def clear_logged_alarms(pself):
        pass

    def set_control(self, control_setting: ControlSetting):
        """
        takes ControlSetting struct
        """
        with self.lock:
            self.COPY_tentative_control_settings[control_setting.name] = control_setting

    def get_control(self, control_setting_name: ValueName) -> ControlSetting:
        with self.lock:
            control_setting = self.COPY_control_settings[control_setting_name]
        return control_setting

    def get_msg_timestamp(self):
        # return timestamp of last message
        with self.lock:
            last_message_timestamp = self.last_message_timestamp
        return last_message_timestamp

    def start(self):
        """
        Start the coordinator.
        This does a soft start (not allocating a process).
        This function will return immediately
        """
        self._is_running.set()

    def is_running(self) -> bool:
        """
        Test whether the whole system is running
        TODO: current implementation is not good. As we need also make sure the controller is running.
        """
        return self._is_running.is_set()

    def stop(self):
        """
        Stop the coordinator.
        This does a soft stop (not kill a process)
        This function will return immediately
        :return:
        """
        self._is_running.clear()

    # def do_process(self, command: IPCCommand):
    #     # TODO: we need to test these
    #     # start / stop / reset process
    #     if command == IPCCommand.START:
    #         self.control_module.start()
    #     elif command == IPCCommand.STOP:
    #         self.control_module.stop()
    #     else:
    #         raise KeyError("Error: undefined action" + str(command))


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
        self.thread = threading.Thread(target=self.__main_loop, daemon=True)
        self.thread.start()
        self.thread_id = self.thread.ident

    def __del__(self):
        self.thread.join()

    def __main_loop(self):
        # TODO: why add this? Local model doesn't need IPC
        # if not self.control_module.running():
        #     self.do_process(IPCCommand.START)
        while self._is_running.wait():
            sensor_values = self.control_module.get_sensors()
            with self.lock:
                self.COPY_sensor_values = sensor_values
                self.last_message_timestamp = sensor_values.timestamp
            for name in values.controllable_values:
                with self.lock:
                    not_in_control_settings = name not in self.COPY_control_settings
                if not_in_control_settings:
                    control_setting = self.control_module.get_control(name)
                    with self.lock:
                        self.COPY_control_settings[name] = control_setting
                with self.lock:
                    disagreed_tentative = name in self.COPY_tentative_control_settings and \
                                      self.COPY_tentative_control_settings[name] != self.COPY_control_settings[
                                          name]
                if disagreed_tentative:
                    with self.lock:
                        tentative_control_setting = self.COPY_tentative_control_settings[name]
                    self.control_module.set_control(tentative_control_setting)
                    with self.lock:
                        self.COPY_control_settings[name] = self.control_module.get_control(name)
            # sleep 10 ms
            time.sleep(0.01)


class CoordinatorRemote(CoordinatorBase):
    def set_control(self, control_setting: ControlSetting):
        super().set_control(control_setting)

    def __init__(self, sim_mode=False):
        super().__init__(sim_mode=sim_mode)
        # TODO: pass max_heartbeat_interval
        self.process_manager = ProcessManager()
        self.ipc = IPC()

    def start(self):
        # TODO: implement
        # send start msg
        self.ipc.send_msg(IPCMessage(IPCCommand.START))

    def stop(self):
        # TODO: implement
        # send stop msg
        self.ipc.send_msg(IPCMessage(IPCCommand.STOP))

    def __main_loop(self):
        while self._is_running.wait():
            # This is a simple implementation, as the sending and receiving share the same thread.
            # There is parallel recv/send on the subprocess side, so won't block. This is equivalent to GUI behavior
            #  Assume 10ms latency is okay
            msg = self.ipc.recv_msg()
            if msg.command == IPCCommand.GET_SENSORS:
                sensor_values = msg.args
                with self.lock:
                    self.COPY_sensor_values = sensor_values
                    self.last_message_timestamp = sensor_values.timestamp
            elif msg.command == IPCCommand.GET_CONTROL:
                control_setting = msg.args
                name = control_setting.name
                with self.lock:
                    self.COPY_control_settings[name] = control_setting
            # TODO: if msg is alarm
            else:
                raise NotImplementedError(f'Error: {msg.command} not implemented')
            self.ipc.send_msg(IPCMessage(IPCCommand.GET_SENSORS))
            for name in values.controllable_values:
                with self.lock:
                    not_in_control_settings = name not in self.COPY_control_settings
                if not_in_control_settings:
                    self.ipc.send_msg(IPCMessage(IPCCommand.GET_CONTROL, name))
                with self.lock:
                    disagreed_tentative = name in self.COPY_tentative_control_settings and \
                                          self.COPY_tentative_control_settings[name] != self.COPY_control_settings[
                                              name]
                if disagreed_tentative:
                    with self.lock:
                        tentative_control_setting = self.COPY_tentative_control_settings[name]
                    self.ipc.send_msg(IPCMessage(IPCCommand.SET_CONTROL, tentative_control_setting))
                    self.ipc.send_msg(IPCMessage(IPCCommand.GET_CONTROL, name))
            # sleep 10 ms
            time.sleep(0.01)


def get_coordinator(single_process=False, sim_mode=False):
    if single_process:
        return CoordinatorLocal(sim_mode)
    else:
        return CoordinatorRemote(sim_mode)
