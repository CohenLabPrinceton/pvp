"""
Constraints to set values

"""

from vent.common.message import ControlSetting
from vent.common.values import ValueName, CONTROL, VALUES

class Constraints(object):
    """
    Class to calculate constraints on set values
    """
    constrained_values =  CONTROL.keys()

    depends_on = {
        ValueName.PIP: (ValueName.PEEP,),
        ValueName.PEEP: (ValueName.PIP,),
        ValueName.BREATHS_PER_MINUTE:
            (ValueName.IE_RATIO,
             ValueName.INSPIRATION_TIME_SEC,
             ValueName.PIP_TIME,
             ValueName.PEEP_TIME),
        ValueName.IE_RATIO:
            (ValueName.INSPIRATION_TIME_SEC,
             ValueName.BREATHS_PER_MINUTE,
             ValueName.PIP_TIME,
             ValueName.PEEP_TIME),
        ValueName.INSPIRATION_TIME_SEC:
            (ValueName.IE_RATIO,
             ValueName.BREATHS_PER_MINUTE,
             ValueName.PIP_TIME,
             ValueName.PEEP_TIME),
        ValueName.PIP_TIME:
            (ValueName.IE_RATIO,
             ValueName.INSPIRATION_TIME_SEC,
             ValueName.BREATHS_PER_MINUTE,
             ValueName.PEEP_TIME),
        ValueName.PEEP_TIME:
            (ValueName.IE_RATIO,
             ValueName.INSPIRATION_TIME_SEC,
             ValueName.BREATHS_PER_MINUTE,
             ValueName.PIP_TIME)
    }

    # calculate inverse dict to determine which
    # constraints need to be updated when
    constrained_by = {}
    for val in constrained_values:
        constrained_by[val] = [k for k, v in depends_on.items() if val in v ]



    def __init__(self):

        self.values = {v_name: None for v_name in ValueName} # store set control values to calculate whether constraints are met or not

    def check_valid(self, new_value: ControlSetting):
        valid = False

        if not new_value.value:
            # if no value given, no value will be set, so let it pass
            valid = True

        elif new_value.value < 0:
            pass

        elif not self._check_defined(new_value.name):
            # if not all of the values the constraint depend on are not set, the value is valid by default
            valid = True

        elif new_value.name == ValueName.PIP:
            # can't be lower than PEEP
            if self.values[ValueName.PEEP] < new_value.value:
                valid = True

        elif new_value.name == ValueName.PEEP:
            # can't be higher than PIP
            if self.values[ValueName.PIP] > new_value.value:
                valid = True

        elif new_value.name == ValueName.BREATHS_PER_MINUTE:
            pass

        elif new_value.name == ValueName.IE_RATIO:
            pass
        elif new_value.name == ValueName.INSPIRATION_TIME_SEC:
            pass
        elif new_value.name == ValueName.PIP_TIME:
            pass
        elif new_value.name == ValueName.PEEP_TIME:
            pass

        return valid

    def calc_constraint(self, new_value: ControlSetting):

        min_valid = None
        max_valid = None


        if not self._check_defined(new_value.name):
            # if not all of the values the constraint depend on are not set, it is unconstrained
            pass

        elif new_value.name == ValueName.PIP:
            # can't be lower than PEEP
            min_valid = self.values[ValueName.PEEP]
            max_valid = VALUES[ValueName.PIP].abs_range[1]

        elif new_value.name == ValueName.PEEP:
            # can't be higher than PIP
            min_valid = VALUES[ValueName.PEEP].abs_range[0]
            max_valid = self.values[ValueName.PIP]

        elif new_value.name == ValueName.BREATHS_PER_MINUTE:
            pass


        elif new_value.name == ValueName.IE_RATIO:
            pass

        elif new_value.name == ValueName.INSPIRATION_TIME_SEC:
            pass

        elif new_value.name == ValueName.PIP_TIME:
            pass

        elif new_value.name == ValueName.PEEP_TIME:
            pass

        return (min_valid, max_valid)


    def _check_defined(self, value: ValueName):
        """
        Check that the values that need to be present to calculate a constraint are set
        """
        all([self.values[depend] is not None for depend in self.depends_on[value]])



    def update_value(self, new_value: ControlSetting):
        """
        Update stored control values -- note that we assume the passed value has already been checked
        so we don't do it again here.


        """
        if new_value.value:
            self.values[new_value.name] = new_value.value