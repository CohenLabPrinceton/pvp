from vent.common import values
from copy import copy


class SensorValueNew:
    def __init__(self, name, value, timestamp, loop_counter):
        self.name = name
        self.value = value
        self.timestamp = timestamp
        self.loop_counter = loop_counter


class SensorValues:
    def __init__(self, timestamp, loop_counter, breath_count, **kwargs):
        """

        Args:
            **kwargs: sensor readings, must be in :data:`vent.values.SENSOR.keys`
        """

        # init
        self.timestamp = timestamp
        self.loop_counter = loop_counter
        self.breath_count = breath_count

        # init all sensor values to none
        # use __members__ as the keys are strings rather than enums
        for key in values.ValueName.__members__.keys():
            setattr(self, key, None)

        # assign kwargs as attributes,
        # check that all the kwargs are in values.SENSOR
        for key, value in kwargs.items():
            if (key in values.ValueName.__members__.keys()):
                setattr(self, key, copy(value))
            else:
                raise KeyError(f'value {key} not declared in vent.values!!!')

    def to_dict(self):
        return {
            valname: getattr(self,valname.name) for valname in values.ValueName
        }



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


class Error:
    def __init__(self, errnum, err_str, timestamp):
        self.errnum = errnum
        self.err_str = err_str
        self.timestamp = timestamp


