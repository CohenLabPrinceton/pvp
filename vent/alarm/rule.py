"""
Class to declare alarm rules
"""


class Alarm_Rule(object):
    """
    * name of rule
    * value to condition on
    * conditions: ((alarm_type, (condition_1, condition_2)), ...)

    * silencing/overriding rules
    """

    def __init__(self):
        super(Alarm_Rule, self).__init__()