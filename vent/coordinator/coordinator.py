import time
import threading
from typing import List, Dict

import vent
from vent.common.message import SensorValues, ControlSetting, Alarm
from vent.common.values import ValueName
from vent.common import values
from vent.common.message import SensorValueNew
import vent.controller.control_module
from vent.coordinator.ipc import IPC, IPCMessage, IPCCommand
from vent.coordinator.process_manager import ProcessManager


class CoordinatorBase:
    def __init__(self, sim_mode=False):
        # get_ui_control_module handles single_process flag
        # self.lock = threading.Lock()
        pass

    # TODO: do we still need this
    # def get_msg_timestamp(self):
    #     # return timestamp of last message
    #     with self.lock:
    #         last_message_timestamp = self.last_message_timestamp
    #     return last_message_timestamp


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

    def get_sensors(self) -> Dict[ValueName, SensorValueNew]:
        sensor_values = self.control_module.get_sensors()
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
        return self.control_module.get_active_alarms()

    def get_logged_alarms(self) -> List[Alarm]:
        return self.control_module.get_logged_alarms()

    def clear_logged_alarms(pself):
        # TODO: implement this
        raise NotImplementedError

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
        # TODO: according to documentation, pass max_heartbeat_interval
        self.ipc = IPC(listen=True)
        self.process_manager = ProcessManager(sim_mode, self.ipc.addr, self.ipc.port)
        # TODO: make sure the ipc connection is setup. There should be a clever method
        time.sleep(1)
        self.receive_thread = threading.Thread(target=self.__receive_loop, daemon=True)
        self.receive_thread.start()
        self.receive_thread_id = self.receive_thread.ident
        self.send_thread = threading.Thread(target=self.__send_loop, daemon=True)
        self.send_thread.start()
        self.send_thread_id = self.send_thread.ident
        self.start()

    def start(self):
        # send start msg
        self.ipc.send_msg(IPCMessage(IPCCommand.START))
        super().start()

    def stop(self):
        # send stop msg
        super().stop()
        self.ipc.send_msg(IPCMessage(IPCCommand.STOP))

    def __receive_loop(self):
        """
        The key to prevent deadlock is this thread never blocking
        """
        while self._is_running.wait():
            # TODO: we need have better logging!
            # print('parent in receiving loop')
            msg = self.ipc.recv_msg()
            # print(f'parent process received: {msg.command}')
            if msg.command == IPCCommand.GET_SENSORS:
                sensor_values = msg.args
                # print(f'parent process read sensor: {sensor_values}')
                with self.lock:
                    self.COPY_sensor_values = sensor_values
                # TODO: set timestamp
            elif msg.command == IPCCommand.GET_CONTROL:
                if msg.args is not None:
                    control_setting = msg.args
                    name = control_setting.name
                    with self.lock:
                        self.COPY_control_settings[name] = control_setting
                else:
                    # assume wait some time will sync the control setting
                    pass
            # TODO: if msg is alarm
            else:
                raise NotImplementedError(f'Error: {msg.command} not implemented')

    def __send_loop(self):
        while self._is_running.wait():
            # don't send GET_SENSOR command because assuming it will send periodically
            # print('parent in sending loop')
            for name in values.controllable_values:
                with self.lock:
                    not_in_control_settings = name not in self.COPY_control_settings
                if not_in_control_settings:
                    self.ipc.send_msg(IPCMessage(IPCCommand.GET_CONTROL, name))
                # print('testing disagree')
                with self.lock:
                    disagreed_tentative = name in self.COPY_tentative_control_settings and \
                                          self.COPY_tentative_control_settings[name] != self.COPY_control_settings[
                                              name]
                if disagreed_tentative:
                    with self.lock:
                        tentative_control_setting = self.COPY_tentative_control_settings[name]
                    # print('parent setting control')
                    self.ipc.send_msg(IPCMessage(IPCCommand.SET_CONTROL, tentative_control_setting))
                    self.ipc.send_msg(IPCMessage(IPCCommand.GET_CONTROL, name))
            # sleep 10 ms
            time.sleep(0.01)


def get_coordinator(single_process=False, sim_mode=False):
    if single_process:
        return CoordinatorLocal(sim_mode)
    else:
        return CoordinatorRemote(sim_mode)
