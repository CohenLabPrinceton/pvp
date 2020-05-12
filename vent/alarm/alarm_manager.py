ALARM_MANAGER_INSTANCE = None


def get_alarm_manager():
    if globals()['ALARM_MANAGER_INSTANCE'] is None:
        alarm_manager = Alarm_Manager()
        # instantiating alarm manager will assign it to the global variable
    else:
        alarm_manager = globals()['ALARM_MANAGER_INSTANCE']

    return alarm_manager


class Alarm_Manager(object):
    def __init__(self):
        if globals()['ALARM_MANAGER_INSTANCE'] is None:
            globals()['ALARM_MANAGER_INSTANCE'] = self
        else:
            raise RuntimeError('Only one alarm manager at a time ya rascal!')