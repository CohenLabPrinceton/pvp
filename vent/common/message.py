from enum import Enum, auto
from vent.common import values



class SensorValueNew:
    def __init__(self, name, value, timestamp, loop_counter):
        self.name = name
        self.value = value
        self.timestamp = timestamp
        self.loop_counter = loop_counter


class SensorValues:
    def __init__(self, timestamp=None, loop_counter=None, **kwargs):
        """

        Args:
            **kwargs: sensor readings, must be in :data:`vent.values.SENSOR.keys`
        """

        # init
        self.timestamp = timestamp
        self.loop_counter = loop_counter

        # init all sensor values to none
        # use __members__ as the keys are strings rather than enums
        for key in values.ValueName.__members__.keys():
            setattr(self, key, None)

        # assign kwargs as attributes,
        # check that all the kwargs are in values.SENSOR
        for key, value in kwargs.items():
            if (key in values.ValueName.__members__.keys()):
                setattr(self, key, value)
            else:
                raise KeyError(f'value {key} not declared in vent.values!!!')



class ControlSetting:
    def __init__(self, name, value, min_value, max_value, timestamp):
        """
        TODO: if enum is hard to use, we may just use a predefined set, e.g. {'PIP', 'PEEP', ...}
        :param name: enum belong to ValueName
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
