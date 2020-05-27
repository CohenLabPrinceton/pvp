import logging
import time
import datetime

import numpy as np
from PySide2 import QtWidgets, QtCore

from vent.gui import styles, mono_font
from vent.gui import get_gui_instance
from vent.alarm import AlarmSeverity, Alarm


class Status_Bar(QtWidgets.QWidget):
    """
    * Start/stop button
    * Status indicator - a clock that increments with heartbeats,
        or some other visual indicator that things are alright
    * Status bar - most recent alarm or notification w/ means of clearing
    * Override to give 100% oxygen and silence all alarms

    """

    def __init__(self):
        super(Status_Bar, self).__init__()

        self.init_ui()

    def init_ui(self):

        self.layout = QtWidgets.QHBoxLayout()


        self.status_message = Message_Display()
        self.layout.addWidget(self.status_message)
        self.layout.setContentsMargins(5,5,5,5)

        self.heartbeat = HeartBeat()
        self.heartbeat.start_timer()
        self.layout.addWidget(self.heartbeat)

        self.start_button = QtWidgets.QPushButton('start!!!')
        self.layout.addWidget(self.start_button)


        self.setLayout(self.layout)

        style = self.style()
        size = style.pixelMetric(QtWidgets.QStyle.PM_MessageBoxIconSize, None, self)

        # self.setMaximumHeight(size*1.5)
        self.setContentsMargins(0,0,0,0)
        #
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                    QtWidgets.QSizePolicy.Expanding)


class Message_Display(QtWidgets.QFrame):

    message_cleared = QtCore.Signal()
    level_changed = QtCore.Signal()

    def __init__(self):
        super(Message_Display, self).__init__()

        self.icons = {}
        self.alarms = {}
        self.current_alarm = None
        self._alarm_level = AlarmSeverity.OFF
        self.setContentsMargins(0,0,0,0)

        self.make_icons()
        self.init_ui()

    def make_icons(self):

        style = self.style()
        size = style.pixelMetric(QtWidgets.QStyle.PM_MessageBoxIconSize, None, self)

        alarm_icon = style.standardIcon(QtWidgets.QStyle.SP_MessageBoxCritical, None, self)
        alarm_icon = alarm_icon.pixmap(size,size)

        warning_icon = style.standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning, None, self)
        warning_icon = warning_icon.pixmap(size,size)

        normal_icon = style.standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation, None, self)
        normal_icon = normal_icon.pixmap(size,size)

        self.icons[AlarmSeverity.LOW] = normal_icon
        self.icons[AlarmSeverity.MEDIUM] = warning_icon
        self.icons[AlarmSeverity.HIGH] = alarm_icon



    def init_ui(self):

        self.layout = QtWidgets.QHBoxLayout()

        self.message = QtWidgets.QLabel('')
        self.message.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.message.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)

        self.icon = QtWidgets.QLabel()
        #self.icon.setEnabled(False)

        style = self.style()
        size = style.pixelMetric(QtWidgets.QStyle.PM_MessageBoxIconSize, None, self)

        #self.icon.setPixmap()
        self.icon.setFixedHeight(size)
        self.icon.setFixedWidth(size)


        self.clear_button = QtWidgets.QPushButton('Clear Message')
        self.clear_button.setVisible(False)
        self.clear_button.clicked.connect(self.clear_message)
        #clear_icon = QtGui.QIcon.fromTheme('window-close')
        #self.clear_button.setIcon(clear_icon)

        self.layout.addWidget(self.message, 5)
        self.layout.addWidget(self.icon, 1)
        self.layout.addWidget(self.clear_button,1)
        self.setLayout(self.layout)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)

    def draw_state(self, state=None):

        if state == AlarmSeverity.LOW:
            self.setStyleSheet(styles.STATUS_NORMAL)
            self.icon.setPixmap(self.icons[AlarmSeverity.LOW])
            self.clear_button.setVisible(True)
        elif state == AlarmSeverity.MEDIUM:
            self.setStyleSheet(styles.STATUS_WARN)
            self.icon.setPixmap(self.icons[AlarmSeverity.MEDIUM])
            self.clear_button.setVisible(True)
        elif state == AlarmSeverity.HIGH:
            self.setStyleSheet(styles.STATUS_ALARM)
            self.icon.setPixmap(self.icons[AlarmSeverity.HIGH])
            self.clear_button.setVisible(True)
        else:
            self.setStyleSheet(styles.STATUS_NORMAL)
            self.clear_button.setVisible(False)
            self.icon.clear()


    @QtCore.Slot(Alarm)
    def update_message(self, alarm):
        """
        Arguments:
            alarm (:class:`~.message.Alarm`)

        """

        if alarm is None:
            # clear
            self.current_alarm = None
            self.draw_state()
            self.message.setText("")
            return

        self.alarms[alarm.id] = alarm

        if self.current_alarm:
            # see if we are outranked by current message
            if alarm.severity.value >= self.current_alarm.severity.value:
                self.draw_state(alarm.severity)
                self.message.setText(alarm.message)
                self.current_alarm = alarm
                self.alarm_level = alarm.severity
            else:
                return

        else:
            self.draw_state(alarm.severity)
            self.message.setText(alarm.message)
            self.current_alarm = alarm
            self.alarm_level = alarm.severity

        # delete old messages from same value
        self.alarms = {a_key: a_val for a_key, a_val in self.alarms.items() if
                       (a_val.alarm_name != alarm.alarm_name) or
                       (a_val.id == alarm.id)}

    def clear_message(self):
        if not self.current_alarm:
            return

        self.message_cleared.emit(self.current_alarm)
        del self.alarms[self.current_alarm.id]


        # check if we have another message to display
        if len(self.alarms)>0:
            # get message priorities
            paired_priorities = [(alarm.id, alarm.severity.value) for alarm in self.alarms.values()]
            priorities = np.array([msg[1] for msg in paired_priorities])
            # find the max priority
            max_ind = np.argmax(priorities)
            self.current_alarm = None
            new_alarm = self.alarms[paired_priorities[max_ind][0]]
            self.update_message(new_alarm)
            self.alarm_level = new_alarm.severity
        else:
            self.update_message(None)
            self.alarm_level = AlarmSeverity.OFF

    @property
    def alarm_level(self):
        return self._alarm_level

    @alarm_level.setter
    def alarm_level(self, alarm_level):
        if alarm_level != self._alarm_level:
            self.level_changed.emit(alarm_level)
            self._alarm_level = alarm_level


class HeartBeat(QtWidgets.QFrame):

    timeout = QtCore.Signal(bool)
    heartbeat = QtCore.Signal(float)

    def __init__(self, update_interval = 100, timeout_dur = 5000):
        """
        Args:
            update_interval (int): How often to do the heartbeat, in ms
            timeout (int): how long to wait before hearing from control process
        """

        super(HeartBeat, self).__init__()

        self.update_interval = update_interval
        self.start_time = None
        self.timeout_dur = timeout_dur
        self._state = False
        self._last_heartbeat = 0
        self.init_ui()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._heartbeat)

        get_gui_instance().gui_closing.connect(self.timer.stop)

    def init_ui(self):

        self.layout = QtWidgets.QGridLayout()

        self.timer_label = QtWidgets.QLabel()
        self.timer_label.setFont(mono_font())

        self.indicator = QtWidgets.QRadioButton()

        self.set_indicator()

        self.layout.addWidget(QtWidgets.QLabel("Uptime"), 0, 0, alignment=QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.layout.addWidget(self.timer_label, 1, 0)
        self.layout.addWidget(QtWidgets.QLabel("Status"), 0, 1)
        self.layout.addWidget(self.indicator, 1, 1)

        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)


        self.setLayout(self.layout)

    def check_timeout(self):
        if (time.time() - self._last_heartbeat) > (self.timeout_dur/1000):
            self._state = True
            self.set_indicator("alarm")
            self.timeout.emit(True)
        else:
            self._state = False
            self.set_indicator("")

    def set_indicator(self, state=None):

        if state == 'alarm':
            self.setStyleSheet(styles.HEARTBEAT_ALARM)

        else:
            self.setStyleSheet(styles.HEARTBEAT_NORMAL)

    def start_timer(self, update_interval=None):
        """
        Args:
            update_interval (float): How often (in ms) the timer should be updated.
        """
        self.start_time = time.time()
        self._last_heartbeat = self.start_time

        if update_interval:
            self.update_interval = update_interval

        self.timer.start(self.update_interval)

    def stop_timer(self):
        """
        you can read the sign ya punk
        """
        self.timer.stop()
        self.setText("")

    @QtCore.Slot(float)
    def beatheart(self, heartbeat_time):
        self._last_heartbeat = heartbeat_time

    def _heartbeat(self):
        """
        Called every (update_interval) milliseconds to set the text of the timer.

        """
        current_time = time.time()
        self.heartbeat.emit(current_time)

        secs_elapsed = current_time-self.start_time
        self.timer_label.setText("{:02d}:{:02d}:{:.2f}".format(int(secs_elapsed/3600), int((secs_elapsed/60))%60, secs_elapsed%60))

        self.check_timeout()

class Power_Button(QtWidgets.QPushButton):

    def __init__(self):

        super(Power_Button, self).__init__()
        self.init_ui()

    def init_ui(self):
        pass

