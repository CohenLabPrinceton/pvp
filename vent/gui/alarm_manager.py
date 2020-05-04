

_ALARM_MANAGER_INSTANCE = None

def get_alarm_manager():

    if isinstance(globals()['_ALARM_MANAGER_INSTANCE'], AlarmManager):
        return globals()['_ALARM_MANAGER_INSTANCE']
    else:
        return AlarmManager()

class AlarmManager(object):

    def __init__(self):
        pass


