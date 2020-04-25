from enum import Enum, auto
from vent import values


class SensorValues:
    def __init__(self, pip=None, peep=None, fio2=None, temp=None, humidity=None, pressure=None, vte=None, breaths_per_minute=None,
                 inspiration_time_sec=None, timestamp=None, loop_counter = None):
        self.pip = pip
        self.peep = peep
        self.fio2 = fio2
        self.temp = temp
        self.humidity = humidity
        self.pressure = pressure
        self.vte = vte
        self.breaths_per_minute = breaths_per_minute
        self.inspiration_time_sec = inspiration_time_sec
        self.timestamp = timestamp
        self.loop_counter = loop_counter

#
# class ControlSettingName(Enum):
#     #Setting that are likely important for future adjustements
#     PIP = auto()       # PIP pressure
#     PIP_TIME = auto()  # time to reach PIP
#     PEEP = auto()      # PEEP pressure
#     BREATHS_PER_MINUTE = auto()
#     INSPIRATION_TIME_SEC = auto()
#     #Settings that are read out, but can not be controlled by software
#     FIO2 = auto()
#     TEMP = auto()
#     HUMIDITY = auto()
#     VTE = auto()

ControlSettingName = Enum('ControlSettingName', list(values.CONTROL.keys()))

class ControlSetting:
    def __init__(self, name, value, min_value, max_value, timestamp):
        """
        TODO: if enum is hard to use, we may just use a predefined set, e.g. {'PIP', 'PEEP', ...}
        :param name: enum belong to ControlSettingName
        :param value:
        :param min_value:
        :param max_value:
        :param timestamp:
        """
        self.name = name
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.timestamp = timestamp


class AlarmSeverity(Enum):
    RED = auto()
    ORANGE = auto()
    YELLOW = auto()


class Alarm:
    def __init__(self, alarm_name, is_active, severity, alarm_start_time, alarm_end_time):
        """
        :param alarm_name:
        :param is_active:
        :param severity: ENUM in AlarmSeverity
        :param alarm_start_time:
        :param alarm_end_time:
        """
        self.alarm_name = alarm_name
        self.is_active = is_active
        self.severity = severity
        self.alarm_start_time = alarm_start_time
        self.alarm_end_time = alarm_end_time


class Error:
    def __init__(self, errnum, err_str, timestamp):
        self.errnum = errnum
        self.err_str = err_str
        self.timestamp = timestamp


class IPCMessageCommand(Enum):
    START = auto()
    STOP = auto()
    RESET = auto()
    GETSENSORS = auto()
    GETALARMS = auto()
    SETCONTROLS = auto()


class IPCMessage:
    def __init__(self, command):
        """
        :param command: ENUM in IPCMessageCommand
        """
        self.command = command
