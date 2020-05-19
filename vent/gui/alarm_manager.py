from PySide2 import QtCore
from vent.alarm import AlarmSeverity, Alarm
import datetime
import time
from vent.common import values, message
import numpy as np

_ALARM_MANAGER_INSTANCE = None

def get_alarm_manager():

    if isinstance(globals()['_ALARM_MANAGER_INSTANCE'], AlarmManager):
        return globals()['_ALARM_MANAGER_INSTANCE']
    else:
        return AlarmManager()

class AlarmManager(QtCore.QObject):

    new_alarm = QtCore.Signal(Alarm)

    def __init__(self):
        super(AlarmManager, self).__init__()

        self.active_alarms = {}

    @QtCore.Slot(dict)
    def update_alarms(self, alarms):
        # FIXME: for now just forwarding
        self.active_alarms = alarms

        for alarm in alarms.values():
            alarm = self.parse_message(alarm)
            self.new_alarm.emit(alarm)

    @QtCore.Slot(tuple)
    def monitor_alarm(self, alarm):
        """
        Parse a tentative alarm from a monitor --
        we should have already gotten an alarm from the controller, so this
        largely serves as a double check.

        Doesn't use the :class:`~.message.Alarm` class because creating a new alarm increments
        the counter.

        Args:
            alarm (tuple): (monitor_name, monitor_value, timestamp)

        """
        # if alarm[0] in self.active_alarms.keys():
        #     return
        # else:
        #     # TODO: count these and raise an alarm that says the controller is out of sync
        #     new_alarm = Alarm(
        #         alarm_name=alarm[0],
        #         active = True,
        #         severity = AlarmSeverity.HIGH,
        #         start_time= alarm[2],
        #         alarm_end_time = None,
        #         value = alarm[1],
        #     )
        #     new_alarm = self.parse_message(new_alarm)
        #     self.new_alarm.emit(new_alarm)
        #     self.active_alarms[alarm[0]] = new_alarm
        pass



    def parse_message(self, alarm):
        """
        If an alarm doesn't have a ``message`` attr, make one for it.
        """
        if alarm.message is None:
            # make human readable time
            start_time = time.strftime(
                '%m/%d, %H:%M:%S',
                time.localtime(alarm.alarm_start_time)
            )

            if isinstance(alarm.alarm_name, values.ValueName):
                alarm_str = alarm.alarm_name.name
            else:
                alarm_str = str(alarm.alarm_name)


            if alarm.value is not None:
                # round to `digits` specified in value def
                round_digits = 1
                if alarm.alarm_name in values.CONTROL.keys():
                    round_digits = values.CONTROL[alarm.alarm_name]['decimals']
                elif alarm.alarm_name in values.SENSOR.keys():
                    round_digits = values.SENSOR[alarm.alarm_name]['decimals']

                value = np.round(alarm.value, decimals=round_digits)



                alarm.message = f"{alarm_str} went out of range at {start_time}, value was {value}"
            else:
                alarm.message = f"{alarm_str} went out of range at {start_time}"
        return alarm




