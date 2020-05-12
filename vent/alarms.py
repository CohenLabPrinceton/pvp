from enum import Enum, auto
from itertools import count
import operator

from vent.common.values import ValueName

ALARM_MANAGER_INSTANCE = None

def get_alarm_manager():
    if globals()['ALARM_MANAGER_INSTANCE'] is None:
        alarm_manager = Alarm_Manager()
        # instantiating alarm manager will assign it to the global variable
    else:
        alarm_manager = globals()['ALARM_MANAGER_INSTANCE']

    return alarm_manager


class AlarmType(Enum):
    LOW_PRESSURE  = auto()  # low airway pressure alarm
    HIGH_PRESSURE = auto()  # high airway pressure alarm
    LOW_VTE       = auto()  # low VTE
    HIGH_VTE      = auto()
    LOW_PEEP      = auto()
    HIGH_PEEP     = auto()
    LOW_O2        = auto()
    HIGH_O2       = auto()
    OBSTRUCTION   = auto()
    LEAK          = auto()


class AlarmSeverity(Enum):
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    TECHNICAL = 1
    OFF = 0

class AlarmArgs(Enum):
    """
    Arguments that an alarm may request as parameterization that are not in
    another enum.

    .. warning::

        for each entry, the :class:`Alarm_Manager` needs to have a method to
    """
    # the required arguments for SensorValues
    TIMESTAMP = auto()
    LOOP_COUNTER = auto()
    BREATH_COUNT = auto()

###################################


class Condition(object):
    """
    Base class for specifying alarm test conditions

    Need to be able to condition alarms based on
    * value ranges
    * value ranges & durations
    * levels of other alarms
    *

    * arguments: values needed to evaluate the condition.
        Caller of :meth:`Condition.check` should give {arguments[0]:value, ...} as argument
    """

    def __init__(self, *args, **kwargs):
        self._arguments = []
        self.arguments = kwargs.get('arguments', [])



    @property
    def arguments(self):
        return self._arguments

    @arguments.setter
    def arguments(self, arguments):
        if not isinstance(arguments, list):
            arguments = [arguments]

        if len(arguments)>0:
            for arg in arguments:
                assert((arg in ValueName) or (arg in AlarmType))

        self._arguments = arguments

    def add_argument(self, argument):
        self.arguments = self._arguments.append(argument)

    def check(self, **kwargs):
        raise NotImplementedError("Every condition needs to override check!!")

class ValueCondition(Condition):
    """
    value is greater or lesser than some max/min
    """

    def __init__(self,
                 value_name: ValueName,
                 limit: (int, float),
                 minmax: str,
                 *args, **kwargs):
        """

        Args:
            value_name (ValueName): Which value to check
            limit (int, float): value to check against
            minmax ('min', 'max'): whether the limit is a minimum or maximum
            *args:
            **kwargs:
        """
        super(ValueCondition, self).__init__(*args, **kwargs)

        self.arguments = [value_name]
        self.value_name = value_name
        self.limit = limit

        self._minmax = None
        self.operator = None
        self.minmax = minmax

    @property
    def minmax(self):
        return self._minmax

    @minmax.setter
    def minmax(self, minmax):
        assert(minmax in ('min', 'max'))
        if minmax == 'min':
            self.operator = operator.lt
        elif minmax == 'max':
            self.operator = operator.gt
        self._minmax = minmax

    def check(self, **kwargs):
        assert(self.value_name in kwargs.keys())
        return self.operator(kwargs.get(self.value_name), self.limit)





class CycleValueCondition(ValueCondition):
    """
    value goes out of range for a specific number of breath cycles

    Attributes:
        _start_cycle (int): The breath cycle where the
        _mid_check (bool): whether a value has left the acceptable range and we are counting consecutive breath cycles
    """

    def __init__(self, n_cycles, *args, **kwargs):
        super(CycleValueCondition, self).__init__(*args, **kwargs)
        self._n_cycles = None
        self.n_cycles = n_cycles
        self.add_argument(AlarmArgs.BREATH_COUNT)

        self._start_cycle = 0
        self._mid_check = False

    @property
    def n_cycles(self):
        return self._n_cycles

    @n_cycles.setter
    def n_cycles(self, n_cycles):
        if not isinstance(n_cycles, int):
            n_cycles = int(round(n_cycles))
        assert(n_cycles>0)
        self._n_cycles = n_cycles

    def check(self, **kwargs):
        assert(AlarmArgs.BREATH_COUNT in kwargs.keys())
        # first check if we are outside of the range
        if super(CycleValueCondition, self).check(**kwargs):

            breath_cycle = kwargs.get(AlarmArgs.BREATH_COUNT)
            # if we're currently in a consecutive set of out-of-range alarms..
            # note: doing it this way because we *dont* want to alarm if there are
            # in-range values seen in the waiting period, but we *do* want to
            # alarm if we miss a value from a breath cycle but haven't seen any
            # in-range values.
            if self._mid_check:
                # if we have progressed the required number of cycles...
                if breath_cycle >= self._start_cycle + self.n_cycles:
                    return True
            else:
                # otherwise, this is the first time we've gone out of bounds
                self._mid_check = True
                self._start_cycle = breath_cycle
                # don't check yet, n_cycles must > 0
                return False

        else:
            # if we're not outside the range, false.
            # reset the flag that says we're inside a check
            self._mid_check = False
            return False

class TimeValueCondition(ValueCondition):
    """
    value goes out of range for specific amount of time
    """

    def __init__(self, time, *args, **kwargs):
        """

        Args:
            time (float): number of seconds value must be out of range
            *args:
            **kwargs:
        """
        super(TimeValueCondition, self).__init__(*args, **kwargs)


        self.time = time


class Alarm_Rule(object):
    """
    * name of rule
    * value to condition on
    * conditions: ((alarm_type, (condition_1, condition_2)), ...)

    * silencing/overriding rules
    """

    def __init__(self):
        super(Alarm_Rule, self).__init__()




class Alarm:
    """
    Class used by the program to control and coordinate alarms.

    Parameterized by a :class:`Alarm_Rule` and managed by :class:`Alarm_Manager`
    """


    id_counter = count()
    """
    :class:`itertools.count`: used to generate unique IDs for each alarm
    """

    def __init__(self, alarm_name, is_active, severity, alarm_start_time, alarm_end_time,value=None, message=None):
        """

        Args:
            alarm_name :
            is_active:
            severity:
            alarm_start_time:
            alarm_end_time:
            value (int, float): optional - numerical value that generated the alarm
            message (str): optional - override default text generated by :class:`~vent.gui.alarm_manager.AlarmManager`
        """
        self.id = next(Alarm.id_counter)
        self.alarm_name = alarm_name
        self.is_active = is_active
        self.severity = severity
        self.alarm_start_time = alarm_start_time
        self.alarm_end_time = alarm_end_time
        self.value = value
        self.message = message

class Alarm_Manager(object):
    def __init__(self):
        if globals()['ALARM_MANAGER_INSTANCE'] is None:
            globals()['ALARM_MANAGER_INSTANCE'] = self
        else:
            raise RuntimeError('Only one alarm manager at a time ya rascal!')
