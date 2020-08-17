import time
import typing

from pvp.common import values
from copy import copy
from collections import OrderedDict as odict
from pvp.common.loggers import init_logger

class SensorValues:

    additional_values = ('timestamp', 'loop_counter', 'breath_count')
    """
    Additional attributes that are not :class:`.ValueName` s that are expected in each SensorValues message
    """

    def __init__(self, timestamp=None, loop_counter=None, breath_count=None, vals=typing.Union[None, typing.Dict['ValueName', float]], **kwargs):
        """
        Structured class for communicating sensor readings throughout PVP.

        Should be instantiated with each of the :attr:`.SensorValues.additional_values`, and values for all
        :class:`.ValueName` s in :data:`.values.SENSOR` by passing them in the ``vals`` kwarg.
        An ``AssertionError`` if an incomplete set of values is given.

        Values can be accessed either via attribute name (``SensorValues.PIP``) or like a dictionary (``SensorValues['PIP']``)

        Args:
            timestamp (float): from time.time(). must be passed explicitly or as an entry in ``vals``
            loop_counter (int): number of control_module loops. must be passed explicitly or as an entry in ``vals``
            breath_count (int): number of breaths taken. must be passed explicitly or as an entry in ``vals``
            vals (None, dict): Dict of ``{ValueName: float}`` that contains current sensor readings. Can also be equivalently given as ``kwargs`` .
                if None, assumed values are being passed as kwargs, but an exception will be raised if they aren't.
            **kwargs: sensor readings, must be in :data:`pvp.values.SENSOR.keys`
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
                try:
                    setattr(self, val, kwargs[val])
                except KeyError as e:
                    if val == "timestamp":
                        # if it's a timestamp we can make one, we cant make up the rest.
                        # otherwise just make one
                        self.timestamp = time.time()
                    else:
                        raise e


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
                raise KeyError(f'value {key} not declared in pvp.values!!!')

    def to_dict(self) -> dict:
        """
        Return a dictionary of all sensor values and additional values

        Returns:
            dict
        """
        ret_dict = {
            valname: getattr(self, valname.name) for valname in values.SENSOR.keys()
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
    def __init__(self,
                 name: values.ValueName,
                 value: float = None,
                 min_value: float =None,
                 max_value: float=None,
                 timestamp: float =None,
                 range_severity: 'AlarmSeverity' = None):
        """
        Message containing ventilation control parameters.

        At least **one of** ``value``, ``min_value``, or ``max_value`` must be given (unlike :class:`.SensorValues` which requires
        all fields to be present) -- eg. in the case where one is setting alarm thresholds without changing the actual set value

        When a parameter has multiple alarm limits for different alarm severities, the severity should be passed to ``range_severity``

        Args:
            name ( :class:`.ValueName` ): Name of value being set
            value (float): Value to set control
            min_value (float): Value to set control minimum (typically used for alarm thresholds)
            max_value (float): Value to set control maximum (typically used for alarm thresholds)
            timestamp (float): ``time.time()`` control message was generated
            range_severity (:class:`.AlarmSeverity`): Some control settings have multiple limits for different alarm severities,
                this attr, when present, specifies which is being set.
        """
        if isinstance(name, str):
            try:
                name = values.CONTROL.__members__[name]
            except KeyError as e:
                logger = init_logger(__name__)
                logger.exception(f'Couldnt create ControlSetting with name {name}, not in values.CONTROL')
                raise e
        elif isinstance(name, values.ValueName):
            assert name in values.CONTROL.keys() or name in (values.ValueName.VTE, values.ValueName.FIO2)

        self.name = name # type: values.ValueName

        if (value is None) and (min_value is None) and (max_value is None):
            logger = init_logger(__name__)
            ex_string = 'at least one of value, min_value, or max_value must be set in a ControlSetting'
            logger.exception(ex_string)
            raise ValueError(ex_string)

        self.value = value
        self.min_value = min_value
        self.max_value = max_value

        if timestamp is None:
            timestamp = time.time()

        self.timestamp = timestamp
        self.range_severity = range_severity

class ControlValues:
    """
    Class to save control values, analogous to SensorValues.

    Used by the controller to save waveform data in :meth:`.DataLogger.store_waveform_data` and :meth:`.ControlModuleBase.__save_values``

    Key difference: SensorValues come exclusively from the sensors, ControlValues contains controller variables, i.e. control signals and controlled signals (the flows).
    :param control_signal_in:
    :param control_signal_out:
    """
    def __init__(self, control_signal_in, control_signal_out):
        self.control_signal_in = control_signal_in
        self.control_signal_out = control_signal_out

class DerivedValues:
    """
    Class to save derived values, analogous to SensorValues.

    Used by controller to store derived values (like PIP from Pressure) in :meth:`.DataLogger.store_derived_data` and
    in :meth:`.ControlModuleBase.__analyze_last_waveform``

    Key difference: SensorValues come exclusively from the sensors, DerivedValues contain estimates of I_PHASE_DURATION, PIP_TIME, PEEP_time, PIP, PIP_PLATEAU, PEEP, and VTE.
    :param timestamp:
    :param breath_count:
    :param I_phase_duration:
    :param pip_time:
    :param peep_time:
    :param pip:
    :param pip_plateau:
    :param peep:
    :param vte:
    """
    def __init__(self, timestamp, breath_count, I_phase_duration, pip_time, peep_time, pip, pip_plateau, peep, vte):
        self.timestamp        = timestamp
        self.breath_count     = breath_count
        self.I_phase_duration = I_phase_duration
        self.pip_time         = pip_time
        self.peep_time        = peep_time
        self.pip              = pip
        self.pip_plateau      = pip_plateau
        self.peep             = peep
        self.vte              = vte

