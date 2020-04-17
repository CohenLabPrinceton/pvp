class SensorValues:
    def __init__(self):
        self.pip = None
        self.peep = None
        self.fio2 = None
        self.temp = None
        self.humidity = None
        self.vte = None
        self.breaths_per_minute = None
        self.inspiration_time_sec = None
        self.timestamp = None


class ControlSettings:
    def __init__(self):
        self.pip = None
        self.peep = None
        self.breaths_per_minute = None
        self.inspiration_time_sec = None
        self.timestamp = None


class Alarm:
    def __init__(self):
        self.alarm_name = None
        self.is_active = None
        self.severity = None
        # {red, orange, yellow}
        self.alarm_start_time = None
        self.alarm_end_time = None


class Error:
    def __init__(self):
        self.errnum = None
        self.err_str = None
        self.timestamp = None


class IPCMessage:
    def __init__(self):
        self.command = None
        # enum{start, stop, reset, getSensors, getAlarms, setControls}
