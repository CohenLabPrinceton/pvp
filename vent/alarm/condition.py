import operator
import types

from vent.alarm.alarm_manager import get_alarm_manager
from vent.common.message import SensorValues
from vent.common.values import ValueName


class Condition(object):
    """
    Base class for specifying alarm test conditions

    Need to be able to condition alarms based on
    * value ranges
    * value ranges & durations
    * levels of other alarms


    Attributes:
        manager (:class:`vent.alarm.alarm_manager.Alarm_Manager`): alarm manager, used to get status of alarms
        _child (:class:`Condition`): if another condition is added to this one, store a reference to it
        """

    def __init__(self, *args, **kwargs):

        self.manager = get_alarm_manager()
        self._child = None
        self._check = None

    def check(self, sensor_values):
        raise NotImplementedError("Every condition needs to override check!!")

    def __add__(self, other):
        """
        Add another :class:`Condition` object to check in series.

        Conditions are evaluated left-to-right, and return if any along the sequence is False

        Args:
            other (:class:`Condition`)
        """
        # can't just add any ole apples n oranges
        assert(issubclass(type(other), Condition))

        if self._child is None:
            # if something hasn't been added to us yet...
            # claim our child
            self._child = other

            # override our check method so we check recursively
            # make a quick backup first tho yno
            self._check = self.check

            def new_check(self, sensor_values):
                if self._check(sensor_values) == False:
                    # if our stashed condition check is false,
                    # return immediately
                    return False
                else:
                    # otherwise call check (potentially recursively)
                    return self._child.check(sensor_values)

            # use python types to programmatically reassign method
            self.check = types.MethodType(new_check, self)

        else:
            # if we have already had something added to us,
            # add it to our child instead, (also potentially recursively)
            self._child = self._child + other

        return self


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

        # self.arguments = [value_name]
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
            self.operator = operator.gt
        elif minmax == 'max':
            self.operator = operator.lt
        self._minmax = minmax

    def check(self, sensor_values):
        assert(isinstance(sensor_values, SensorValues))
        return self.operator(sensor_values[self.value_name], self.limit)


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

    def check(self, sensor_values):
        # first check if we are outside of the range
        if super(CycleValueCondition, self).check(sensor_values):

            breath_cycle = sensor_values.breath_count
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