from vent.common import values
from copy import copy
from collections import OrderedDict as odict

class SensorValues:

    additional_values = ('timestamp', 'loop_counter', 'breath_count')
    def __init__(self, timestamp=None, loop_counter=None, breath_count=None, vals=None, **kwargs):
        """


        Args:
            timestamp (float): from time.time(). must be passed explicitly or as an entry in ``vals``
            loop_counter (int): number of control_module loops. must be passed explicitly or as an entry in ``vals``
            breath_count (int): number of breaths taken. must be passed explicitly or as an entry in ``vals``
            **kwargs: sensor readings, must be in :data:`vent.values.SENSOR.keys`
        """

        # if we were passed vals, we were given a dict of {ValueName: value}
        # allow this because python doesn't allow ** unpacking when the keys are not strings
        if vals is not None:
            for key, val in vals.items():
                if isinstance(key, values.ValueName):
                    kwargs[key.name] = val
                elif key in values.ValueName.__members__.keys():
                    kwargs[key] = val
                elif key in self.additional_values:
                    kwargs[key] = val

        # if we were called with a dictionary, make sure it came with
        # timestamp
        # loop_counter
        # breath_count
        self.timestamp = timestamp
        self.loop_counter = loop_counter
        self.breath_count = breath_count

        # if we were given None, try to get from kwargs.
        for val in self.additional_values:
            if getattr(self, val) is None:
                setattr(self, val, kwargs[val])

        # insist that we have all the rest of the vals
        assert(all([value.name in kwargs.keys() for value in values.SENSOR.keys()]))


        # assign kwargs as attributes,
        # don't allow any non-ValueName keys
        for key, value in kwargs.items():
            if (key in values.ValueName.__members__.keys()):
                setattr(self, key, copy(value))
            elif key in self.additional_values:
                continue
            else:
                raise KeyError(f'value {key} not declared in vent.values!!!')

    def to_dict(self):
        ret_dict = {
            valname: getattr(self,valname.name) for valname in values.SENSOR.keys()
        }

        ret_dict.update({
            k:getattr(self, k) for k in self.additional_values
        })

        return ret_dict

    def __getitem__(self, item):
        if item in values.ValueName:
            return getattr(self, item.name)
        elif item in values.ValueName.__members__.keys():
            return getattr(self, item)
        elif item.lower() in self.additional_values:
            return getattr(self, item.lower())
        else:
            raise KeyError(f'No such value as {item}')

    def __setitem__(self, key, value):
        if key in values.ValueName:
            return setattr(self, key.name, value)
        elif key in values.ValueName.__members__.keys():
            return setattr(self, key, value)
        elif key.lower() in self.additional_values:
            return setattr(self, key.lower(), value)
        else:
            raise KeyError(f'No such value as {key}')




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


