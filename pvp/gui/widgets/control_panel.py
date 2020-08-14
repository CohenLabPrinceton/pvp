import time
import os
from collections import OrderedDict as odict
import subprocess

from PySide2 import QtWidgets, QtCore, QtGui

from pvp.gui import styles, mono_font
from pvp.gui import get_gui_instance
from pvp.gui.widgets.components import QHLine, OnOffButton
from pvp.alarm import Alarm, AlarmType
from pvp.common import prefs, values
import pvp

class Control_Panel(QtWidgets.QGroupBox):
    """
    * Start/stop button
    * Status indicator - a clock that increments with heartbeats,
        or some other visual indicator that things are alright
    * Status bar - most recent alarm or notification w/ means of clearing
    * Override to give 100% oxygen and silence all alarms

    """

    pressure_units_changed = QtCore.Signal(str)
    cycle_autoset_changed = QtCore.Signal()

    def __init__(self):
        super(Control_Panel, self).__init__('Control Panel')

        self._autocalc_cycle = values.ValueName.INSPIRATION_TIME_SEC

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

        # heartbeat indicator
        self.heartbeat = HeartBeat()
        self.heartbeat.start_timer()
        self.status_layout.addWidget(QtWidgets.QLabel('Control System'),
                                     0,0,alignment=QtCore.Qt.AlignLeft)
        self.status_layout.addWidget(self.heartbeat,
                                     0,1,alignment=QtCore.Qt.AlignRight)

        # runtime clock
        self.runtime = StopWatch()
        self.status_layout.addWidget(QtWidgets.QLabel('Runtime (s)'),
                                     1,0,alignment=QtCore.Qt.AlignLeft)

        self.status_layout.addWidget(self.runtime,1,1,
                                     alignment=QtCore.Qt.AlignRight)



        # version indicator
        self.status_layout.addWidget(QtWidgets.QLabel('PVP Version'),
                                     2,0,alignment=QtCore.Qt.AlignLeft)
        version = pvp.__version__
        try:
            # get git version
            git_version = subprocess.check_output(['git', 'describe', '--always'],
                                                  cwd=os.path.dirname(__file__)).strip().decode('utf-8')
            version = " - ".join([version, git_version])
        except Exception:
            # no problem, just use package version
            pass

        self.status_layout.addWidget(QtWidgets.QLabel(version),
                                     2,1,alignment=QtCore.Qt.AlignRight)


        self.layout.addLayout(self.status_layout)
        self.layout.addWidget(QHLine())
        ############
        # controls
        self.control_layout = QtWidgets.QGridLayout()

        # ----------------------
        # pressure units control
        # ----------------------
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

        # ----------------------------
        # autonomous breath detection
        # ----------------------------
        self.control_layout.addWidget(QtWidgets.QLabel('Autonomous Breathing'),
                                      1,0,alignment=QtCore.Qt.AlignLeft)
        self.breath_detection_button = OnOffButton()
        # set initial state depending on prefs
        self.breath_detection_button.setChecked(prefs.get_pref('BREATH_DETECTION'))
        self.control_layout.addWidget(self.breath_detection_button,
                                      1, 1, alignment=QtCore.Qt.AlignRight)

        # -------------------------
        # Breath Cycle Controls
        # --------------------------
        self.control_layout.addWidget(QtWidgets.QLabel('Autoset Cycle Control'),
                                      2,0,alignment=QtCore.Qt.AlignLeft)

        self.cycle_buttons = odict({
            values.ValueName.BREATHS_PER_MINUTE: QtWidgets.QPushButton('RR') ,
            values.ValueName.INSPIRATION_TIME_SEC: QtWidgets.QPushButton('INSPt'),
            values.ValueName.IE_RATIO: QtWidgets.QPushButton('I:E')
        })

        self.controls_cycle_button_group = QtWidgets.QButtonGroup()
        self.controls_cycle_button_group.setExclusive(True)
        self.controls_layout_cycle_buttons = QtWidgets.QHBoxLayout()

        for button_name, button in self.cycle_buttons.items():
            button.setObjectName(button_name.name)
            button.setCheckable(True)
            self.controls_cycle_button_group.addButton(button)
            button.setStyleSheet(styles.TOGGLE_BUTTON)
            self.controls_layout_cycle_buttons.addWidget(button)

        self.cycle_buttons[values.ValueName.INSPIRATION_TIME_SEC].setChecked(True)

        self.controls_cycle_button_group.buttonClicked.connect(self.cycle_autoset_changed)

        self.control_layout.addLayout(self.controls_layout_cycle_buttons,
                                      2, 1, alignment=QtCore.Qt.AlignRight)




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

