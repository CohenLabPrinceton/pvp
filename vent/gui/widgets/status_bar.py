import logging
import time
import datetime
import typing
import os

import numpy as np
from PySide2 import QtWidgets, QtCore, QtGui

from vent.gui import styles, mono_font
from vent.gui import get_gui_instance
from vent.gui.widgets.components import QHLine
from vent.alarm import AlarmSeverity, Alarm, AlarmType, Alarm_Manager
#
# class Control_Panel(QtWidgets.QWidget):
#     def __init__(self):
#         super(Control_Panel, self).__init__()
#
#         self.init_ui()
#
#     def init_ui(self):



class Control_Panel(QtWidgets.QGroupBox):
    """
    * Start/stop button
    * Status indicator - a clock that increments with heartbeats,
        or some other visual indicator that things are alright
    * Status bar - most recent alarm or notification w/ means of clearing
    * Override to give 100% oxygen and silence all alarms

    """

    pressure_units_changed = QtCore.Signal(str)

    def __init__(self):
        super(Control_Panel, self).__init__('Control Panel')

        self.init_ui()

    def init_ui(self):

        self.setStyleSheet(styles.CONTROL_PANEL)


        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(5,5,5,5)

        # Top buttons - start and lock
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setContentsMargins(0,0,0,0)

        self.start_button = Start_Button()
        self.button_layout.addWidget(self.start_button,3)

        self.lock_button = Lock_Button()
        self.button_layout.addWidget(self.lock_button, 1)

        self.layout.addLayout(self.button_layout)
        ###################
        # Status indicators
        self.status_layout = QtWidgets.QGridLayout()

        self.heartbeat = HeartBeat()
        self.heartbeat.start_timer()
        self.status_layout.addWidget(QtWidgets.QLabel('Control System'),
                                     0,0,alignment=QtCore.Qt.AlignLeft)
        self.status_layout.addWidget(self.heartbeat,
                                     0,1,alignment=QtCore.Qt.AlignRight)

        self.runtime = StopWatch()
        self.status_layout.addWidget(QtWidgets.QLabel('Runtime (s)'),
                                     1,0,alignment=QtCore.Qt.AlignLeft)

        self.status_layout.addWidget(self.runtime,1,1,
                                     alignment=QtCore.Qt.AlignRight)




        self.layout.addLayout(self.status_layout)
        self.layout.addWidget(QHLine())

        ############
        # controls
        self.control_layout = QtWidgets.QGridLayout()


        self.control_layout.addWidget(QtWidgets.QLabel('Pressure Units'),
                                      0,0,alignment=QtCore.Qt.AlignLeft)
        self.pressure_buttons = {
            'cmH2O': QtWidgets.QPushButton('cmH2O'),
            'hPa': QtWidgets.QPushButton('hPa')
        }

        # make button group to enforce exclusivity
        self.pressure_button_group = QtWidgets.QButtonGroup()
        self.pressure_button_group.setExclusive(True)
        # and groupbox for layout
        # self.pressure_button_groupbox = QtWidgets.QGroupBox()
        pressure_button_layout = QtWidgets.QHBoxLayout()


        for button_name, button in self.pressure_buttons.items():
            button.setCheckable(True)
            if button_name == 'cmH2O':
                button.setChecked(True)
            self.pressure_button_group.addButton(button)
            button.setStyleSheet(styles.TOGGLE_BUTTON)

        self.pressure_button_group.buttonClicked.connect(self._pressure_units_changed)

        pressure_button_layout.addWidget(self.pressure_buttons['cmH2O'])
        pressure_button_layout.addWidget(self.pressure_buttons['hPa'])

        self.control_layout.addLayout(pressure_button_layout,
                                      0,1,alignment=QtCore.Qt.AlignRight)

        self.layout.addLayout(self.control_layout)

        # stretch for empty space
        self.layout.addStretch(5)

        self.setLayout(self.layout)

        style = self.style()
        size = style.pixelMetric(QtWidgets.QStyle.PM_MessageBoxIconSize, None, self)

        # self.setMaximumHeight(size*1.5)
        #self.setMaximumWidth(styles.LEFT_COLUMN_MAX_WIDTH)
        self.setContentsMargins(0,0,0,0)
        #
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                    QtWidgets.QSizePolicy.Expanding)

    def add_alarm(self, alarm: Alarm):
        """
        Wraps  :meth:`.Alarm_Bar.add_alarm`

        Args:
            alarm (:class:`.Alarm`): passed to :class:`Alarm_Bar`
        """
        self.alarm_bar.add_alarm(alarm)

    def clear_alarm(self, alarm: Alarm = None, alarm_type: AlarmType = None):
        """
        Wraps :meth:`.Alarm_Bar.clear_alarm`
        """
        self.alarm_bar.clear_alarm(alarm, alarm_type)

    def _pressure_units_changed(self, button):
        self.pressure_units_changed.emit(button.text())


class Start_Button(QtWidgets.QToolButton):
    states = ['OFF', 'ON', 'ALARM']
    def __init__(self, *args, **kwargs):
        super(Start_Button, self).__init__(*args, **kwargs)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.setCheckable(True)

        self.pixmaps = {}
        self.load_pixmaps()


        self.setIconSize(QtCore.QSize(styles.START_BUTTON_HEIGHT,
                                      styles.START_BUTTON_HEIGHT))
        self.setFixedHeight(styles.BUTTON_MAX_HEIGHT)

        self.set_state('OFF')

    def load_pixmaps(self):
        gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        power_dir = os.path.join(gui_dir, 'images', 'power')

        self.pixmaps['OFF'] = QtGui.QPixmap(os.path.join(power_dir, 'start_button_off.png'))
        self.pixmaps['ON'] =  QtGui.QPixmap(os.path.join(power_dir, 'start_button_on.png'))
        self.pixmaps['ALARM'] =  QtGui.QPixmap(os.path.join(power_dir, 'start_button_alarm.png'))


    def set_state(self, state):
        """
        Should only be called by other objects (as there are checks to whether it's ok to start/stop that we shouldn't be aware of)

        Args:
            state (str): ``('OFF', 'ON', 'ALARM')``
        """
        self.blockSignals(True)
        if state == "OFF":
            self.setIcon(self.pixmaps['OFF'])
            self.setText('START')
            self.setStyleSheet(styles.START_BUTTON_OFF)
            self.setChecked(False)
        elif state == 'ON':
            self.setIcon(self.pixmaps['ON'])
            self.setText('STOP')
            self.setStyleSheet(styles.START_BUTTON_ON)
            self.setChecked(True)
        elif state == 'ALARM':
            self.setIcon(self.pixmaps['ALARM'])
            self.setStyleSheet(styles.START_BUTTON_ALARM)
        self.blockSignals(False)

class Lock_Button(QtWidgets.QToolButton):

    states = ['DISABLED', 'UNLOCKED', 'LOCKED']
    def __init__(self, *args, **kwargs):
        super(Lock_Button, self).__init__(*args, **kwargs)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        self.setCheckable(True)
        self.setChecked(True)

        self.pixmaps = {}
        self.load_pixmaps()


        self.setIconSize(QtCore.QSize(styles.START_BUTTON_HEIGHT,
                                      styles.START_BUTTON_HEIGHT))
        self.setFixedHeight(styles.BUTTON_MAX_HEIGHT)
        self.set_state('DISABLED')

    def load_pixmaps(self):
        gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        lock_dir = os.path.join(gui_dir, 'images', 'lock')

        self.pixmaps['DISABLED'] = QtGui.QPixmap(os.path.join(lock_dir, 'disabled.png'))
        self.pixmaps['UNLOCKED'] = QtGui.QPixmap(os.path.join(lock_dir, 'unlocked.png'))
        self.pixmaps['LOCKED'] = QtGui.QPixmap(os.path.join(lock_dir, 'locked.png'))

    def set_state(self, state):
        """
        Should only be called by other objects (as there are checks to whether it's ok to start/stop that we shouldn't be aware of)

        Args:
            state (str): ``('OFF', 'ON', 'ALARM')``
        """
        self.blockSignals(True)
        if state == "DISABLED":
            self.setIcon(self.pixmaps['DISABLED'])
            #self.setStyleSheet(styles.START_BUTTON_OFF)
            self.setChecked(True)
        elif state == 'UNLOCKED':
            self.setIcon(self.pixmaps['UNLOCKED'])
            #self.setStyleSheet(styles.START_BUTTON_ON)
            self.setChecked(False)
        elif state == 'LOCKED':
            self.setIcon(self.pixmaps['LOCKED'])
            #self.setStyleSheet(styles.START_BUTTON_ALARM)
            self.setChecked(True)
        self.blockSignals(False)


class Alarm_Bar(QtWidgets.QFrame):
    """
    Holds and manages a collection of :class:`Alarm_Card` s
    """

    message_cleared = QtCore.Signal()
    level_changed = QtCore.Signal()
    alarm_dismissed = QtCore.Signal()
    """
    Wraps :attr:`.Alarm_Card.alarm_dismissed`
    """

    def __init__(self):
        super(Alarm_Bar, self).__init__()

        self.icons = {}
        self.alarms = [] # type: typing.List[Alarm]
        self.alarm_cards = [] # type: typing.List[Alarm_Card]
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
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.addStretch(10)
        self.layout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)

        self.alarm_layout = QtWidgets.QHBoxLayout()

        self.icon = QtWidgets.QLabel()
        #self.icon.setEnabled(False)

        style = self.style()
        size = style.pixelMetric(QtWidgets.QStyle.PM_MessageBoxIconSize, None, self)

        #self.icon.setPixmap()
        self.icon.setFixedHeight(size)
        self.icon.setFixedWidth(size)

        #self.layout.addWidget(self.message, 6)
        self.layout.addLayout(self.alarm_layout, 6)
        self.layout.addWidget(self.icon, 1)
        # self.layout.addWidget(self.clear_button,1)
        self.setLayout(self.layout)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)
        self.setFixedHeight(styles.ALARM_BAR_HEIGHT)

    def add_alarm(self, alarm:Alarm):
        """
        Add an alarm created by the :class:`.Alarm_Manager` to the bar.

        Args:
            alarm:

        """
        for existing_alarm in self.alarms:
            if existing_alarm.alarm_type == alarm.alarm_type:
                self.clear_alarm(existing_alarm)

        # make new alarm widget
        alarm_card = Alarm_Card(alarm)
        alarm_card.alarm_dismissed.connect(self.alarm_dismissed)

        # alarm priority should go low on left, high on right
        # newer alarms should be on the right of older alarms of same severity
        for i, existing_alarm in enumerate(self.alarms):
            if alarm.severity < existing_alarm.severity:
                self.alarms.insert(i, alarm)
                self.alarm_cards.insert(i, alarm_card)
                self.alarm_layout.insertWidget(i, alarm_card)
                break

        else:
            # no alarm was greater than us, we should go at the end
            self.alarms.append(alarm)
            self.alarm_cards.append(alarm_card)
            self.alarm_layout.addWidget(alarm_card)

        # update our icon
        self.update_icon()

    def clear_alarm(self, alarm:Alarm=None, alarm_type:AlarmType=None):
        if (alarm is None) and (alarm_id is None):
            raise ValueError('Need to provide either alarm object or alarm id to clear')


        if alarm:
            alarm_type = alarm.alarm_type


        for existing_alarm, alarm_card in zip(self.alarms, self.alarm_cards):
            if alarm_type == existing_alarm.alarm_type:
                self.alarms.remove(existing_alarm)
                self.alarm_layout.removeWidget(alarm_card)
                self.alarm_cards.remove(alarm_card)
                alarm_card.deleteLater()

        self.update_icon()

    def update_icon(self):
        """
        Call :meth:`.set_icon` with highest severity in :attr:`Alarm_Bar.alarms`
        """
        severity = AlarmSeverity.OFF
        for alarm in self.alarms:
            if alarm.severity > severity:
                severity = alarm.severity

        self.set_icon(severity)


    def set_icon(self, state: AlarmSeverity=None):
        """
        Change the icon to reflect the alarm severity

        Args:
            state:

        Returns:

        """

        if state == AlarmSeverity.LOW:
            self.setStyleSheet(styles.STATUS_NORMAL)
            self.icon.setPixmap(self.icons[AlarmSeverity.LOW])
            #self.clear_button.setVisible(True)
        elif state == AlarmSeverity.MEDIUM:
            self.setStyleSheet(styles.STATUS_WARN)
            self.icon.setPixmap(self.icons[AlarmSeverity.MEDIUM])
            #self.clear_button.setVisible(True)
        elif state == AlarmSeverity.HIGH:
            self.setStyleSheet(styles.STATUS_ALARM)
            self.icon.setPixmap(self.icons[AlarmSeverity.HIGH])
            #self.clear_button.setVisible(True)
        else:
            self.setStyleSheet(styles.STATUS_NORMAL)
            #self.clear_button.setVisible(False)
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
            self.set_icon()
            self.message.setText("")
            return

        self.alarms[alarm.id] = alarm

        if self.current_alarm:
            # see if we are outranked by current message
            if alarm.severity >= self.current_alarm.severity:
                self.set_icon(alarm.severity)
                self.message.setText(alarm.message)
                self.current_alarm = alarm
                self.alarm_level = alarm.severity
            else:
                return

        else:
            self.set_icon(alarm.severity)
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
            paired_priorities = [(alarm.id, alarm.severity) for alarm in self.alarmss()]
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

class Alarm_Card(QtWidgets.QFrame):
    """
    Representation of an alarm raised by :class:`.Alarm_Manager` in GUI.

    If allowed by alarm, allows user to dismiss/silence alarm
    """
    alarm_dismissed = QtCore.Signal()

    def __init__(self, alarm: Alarm):
        super(Alarm_Card, self).__init__()

        assert isinstance(alarm, Alarm)
        self.alarm = alarm
        self.severity = self.alarm.severity


        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(styles.ALARM_CARD_STYLES[self.severity])
        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                           QtWidgets.QSizePolicy.Expanding)

        self.layout = QtWidgets.QGridLayout()
        self.name_label = QtWidgets.QLabel(self.alarm.alarm_type.human_name)
        self.name_label.setStyleSheet(styles.ALARM_CARD_TITLE)

        timestamp = datetime.datetime.fromtimestamp(self.alarm.start_time)
        theday = timestamp.strftime('%Y-%m-%d')
        thetime = timestamp.strftime('%H:%M:%S')

        self.timestamp_label = QtWidgets.QLabel(
            '\n'.join([theday, thetime])
        )
        self.timestamp_label.setStyleSheet(styles.ALARM_CARD_TIMESTAMP)
        self.timestamp_label.setFont(mono_font())

        # close button
        # style = self.style()
        # size = style.pixelMetric(QtWidgets.QStyle.PM_MessageBoxIconSize, None, self)
        # close_icon = style.standardIcon(QtWidgets.QStyle.SP_TitleBarCloseButton, None, self)
        # close_icon = close_icon.pixmap(size, size)
        #
        self.close_button = QtWidgets.QPushButton('X')
        self.close_button.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum,
            QtWidgets.QSizePolicy.Expanding)
        self.close_button.setStyleSheet(styles.ALARM_CARD_BUTTON)
        self.close_button.clicked.connect(self._dismiss)

        self.layout.addWidget(self.name_label,0, 0)
        self.layout.addWidget(self.timestamp_label, 1,0)
        self.layout.addWidget(self.close_button, 0, 1, 2, 1)

        self.setLayout(self.layout)

    def _dismiss(self):

        Alarm_Manager().dismiss_alarm(self.alarm.alarm_type)
        self.close_button.setStyleSheet(styles.ALARM_CARD_BUTTON_INACTIVE)
        self.close_button.setText('...')













class HeartBeat(QtWidgets.QFrame):

    timeout = QtCore.Signal(bool)
    heartbeat = QtCore.Signal(float)

    def __init__(self, update_interval = 100, timeout_dur = 5000):
        """
        Attributes:
            _state (bool): whether the system is running or not

        Args:
            update_interval (int): How often to do the heartbeat, in ms
            timeout (int): how long to wait before hearing from control process
        """

        super(HeartBeat, self).__init__()

        self.update_interval = update_interval
        self.start_time = None
        self.timeout_dur = timeout_dur
        self._state = False # whether we have started or stopped
        self._indicator = None
        self._last_heartbeat = 0
        self.init_ui()
        self.set_indicator('OFF')

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._heartbeat)

        get_gui_instance().gui_closing.connect(self.timer.stop)

    def init_ui(self):

        self.layout = QtWidgets.QHBoxLayout()

        self.status_label = QtWidgets.QLabel()
        self.status_label.setFont(mono_font())

        self.indicator = QtWidgets.QRadioButton()

        self.set_indicator('OFF')

        # self.layout.addWidget(QtWidgets.QLabel("Uptime"), 0, 0, alignment=QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)

        # self.layout.addWidget(QtWidgets.QLabel("Status"), 0, 1)
        self.layout.addWidget(self.indicator)
        self.layout.addWidget(self.status_label)

        # self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)


        self.setLayout(self.layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                           QtWidgets.QSizePolicy.Maximum)

    @QtCore.Slot(bool)
    def set_state(self, state):
        # if current state is false and turning on, reset _last_heartbeat so we don't
        # jump immediately into timeout
        if not self._state and state:
            self._last_heartbeat = time.time()
        self._state = state

    def set_indicator(self, state=None):
        if self._indicator == state:
            return

        self._indicator = state

        if state == 'ALARM':
            self.setStyleSheet(styles.HEARTBEAT_ALARM)
            self.status_label.setText('LOST CONNECTION')
        elif state == 'OFF':
            # eg. before controller starts
            self.setStyleSheet(styles.HEARTBEAT_OFF)
            self.status_label.setText('OFF')
        elif state == 'NORMAL':
            self.setStyleSheet(styles.HEARTBEAT_NORMAL)
            self.status_label.setText('CONNECTED')

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
        Called every (update_interval) milliseconds to set the check the status of the heartbeat.
        """
        current_time = time.time()

        if not self._state:
            self.set_indicator("OFF")

        else:
            # we've been started
            dt = current_time - self._last_heartbeat
            if dt < self.update_interval/1000:
                # if we've gotten some notice in the updating interval, great!
                self.set_indicator("NORMAL")
            elif dt < self.timeout_dur/1000:
                # emit a heartbeat notice, requesting our _last_heartbeat be updated
                self.heartbeat.emit(current_time)
            else:
                # we're over the limit for a timeout, emit the timeout signal and set style
                self.set_indicator("ALARM")
                self.heartbeat.emit(current_time)
                self.timeout.emit(True)




class StopWatch(QtWidgets.QLabel):
    def __init__(self, update_interval: float = 100, *args, **kwargs):
        """

        Args:
            update_interval (float): update clock every n seconds
            *args:
            **kwargs:
        """
        super(StopWatch, self).__init__(*args, **kwargs)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update_time)
        # stop if the program closes
        get_gui_instance().gui_closing.connect(self.timer.stop)

        self.init_ui()
        self.start_time = time.time()
        self.update_interval = update_interval

    def init_ui(self):
        self.setFont(mono_font())


    def start_timer(self, update_interval=None):
        """
        Args:
            update_interval (float): How often (in ms) the timer should be updated.
        """
        self.start_time = time.time()

        if update_interval:
            self.update_interval = update_interval

        self.timer.start(self.update_interval)

    def stop_timer(self):
        """
        you can read the sign ya punk
        """
        self.timer.stop()
        self.setText("")


    def _update_time(self):

        secs_elapsed = time.time()-self.start_time
        self.setText("{:02d}:{:02d}:{:.2f}".format(int(secs_elapsed / 3600), int((secs_elapsed / 60)) % 60, secs_elapsed % 60))





class Power_Button(QtWidgets.QPushButton):

    def __init__(self):

        super(Power_Button, self).__init__()
        self.init_ui()

    def init_ui(self):
        pass

