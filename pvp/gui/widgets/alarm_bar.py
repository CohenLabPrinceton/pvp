import datetime
import typing

import numpy as np
from PySide2 import QtWidgets, QtCore

from pvp.alarm import AlarmSeverity, Alarm, AlarmType, Alarm_Manager
from pvp.gui import styles, mono_font


class Alarm_Bar(QtWidgets.QFrame):
    """
    Holds and manages a collection of :class:`Alarm_Card` s
    """

    #message_cleared = QtCore.Signal()
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

    # def clear_message(self):
    #     if not self.current_alarm:
    #         return
    #
    #     self.message_cleared.emit(self.current_alarm)
    #     del self.alarms[self.current_alarm.id]
    #
    #
    #     # check if we have another message to display
    #     if len(self.alarms)>0:
    #         # get message priorities
    #         paired_priorities = [(alarm.id, alarm.severity) for alarm in self.alarmss()]
    #         priorities = np.array([msg[1] for msg in paired_priorities])
    #         # find the max priority
    #         max_ind = np.argmax(priorities)
    #         self.current_alarm = None
    #         new_alarm = self.alarms[paired_priorities[max_ind][0]]
    #         self.update_message(new_alarm)
    #         self.alarm_level = new_alarm.severity
    #     else:
    #         self.update_message(None)
    #         self.alarm_level = AlarmSeverity.OFF

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