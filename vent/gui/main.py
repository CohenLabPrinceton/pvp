import time
import sys
import threading
import pdb
import os

from PySide2 import QtWidgets, QtCore, QtGui


from vent.alarm import AlarmSeverity, Alarm
from vent.common import values
from vent.common.values import ValueName
from vent.common.message import ControlSetting
from vent.common.logging import init_logger
from vent import gui
from vent.gui import widgets, set_gui_instance, get_gui_instance, styles, PLOTS
from vent.gui.alarm_manager import AlarmManager




class Vent_Gui(QtWidgets.QMainWindow):

    gui_closing = QtCore.Signal()
    """
    :class:`PySide2.QtCore.Signal` emitted when the GUI is closing.
    """

    alarms_updated = QtCore.Signal(dict)
    """
    :class:`PySide2.QtCore.Signal` emitted whenever alarms are updated.
    
    Returns the result of ``self.coordinator.get_active_alarms``, so will emit an
    empty dict if there are no active alarms.
    """

    MONITOR = values.SENSOR
    """
    see :data:`.gui.defaults.SENSOR`
    """

    CONTROL = values.CONTROL
    """
    see :data:`.gui.defaults.CONTROL`
    """

    PLOTS = PLOTS
    """
    see :data:`.gui.defaults.PLOTS`
    """

    monitor_width = 2
    plot_width = 4
    control_width = 2
    total_width = monitor_width + plot_width + control_width
    """
    computed from ``monitor_width+plot_width+control_width``
    """

    status_height = 1
    main_height = 5
    total_height = status_height+main_height
    """
    computed from ``status_height+main_height``
    """

    def __init__(self, coordinator, update_period = 0.1):
        """
        The Main GUI window.

        Only one instance can be created at a time. Uses :func:`set_gui_instance` to
        store a reference to itself. after initialization, use `get_gui_instance` to
        retrieve a reference.

        .. todo:

            Jonny add a screenshot here when final version.


        Attributes:
            monitor (dict): Dictionary mapping :data:`.values.SENSOR` keys to :class:`.widgets.Monitor_Value` objects
            plots (dict): Dictionary mapping :data:`.gui.PLOT` keys to :class:`.widgets.Plot` objects
            controls (dict): Dictionary mapping :data:`.values.CONTROL` keys to :class:`.widgets.Control` objects
            coordinator (:class:`vent.coordinator.coordinator.CoordinatorBase`): Some coordinator object that we use to communicate with the controller
            control_module (:class:`vent.controller.control_module.ControlModuleBase`): Reference to the control module, retrieved from coordinator
            start_time (float): Start time as returned by :func:`time.time`
            update_period (float): The global delay between redraws of the GUI (seconds)
            alarm_manager (:class:`~.AlarmManager`)


        Arguments:
            update_period (float): The global delay between redraws of the GUI (seconds)
            test (bool): Whether the monitored values and plots should be fed sine waves for visual testing.


        """
        self.logger = init_logger(__name__)
        self.logger.info('gui init')

        if get_gui_instance() is not None and gui.limit_gui():
            raise Exception('Instance of gui already running!') # pragma: no cover
        else:
            set_gui_instance(self)

        super(Vent_Gui, self).__init__()

        self.alarm_manager = AlarmManager()
        self._alarm_state = AlarmSeverity.OFF

        self.monitor = {}
        self.plots = {}
        self.controls = {}

        self.coordinator = coordinator
        try:
            self.control_module = self.coordinator.control_module
        except AttributeError:
            self.control_module = None

        # start QTimer to update values
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.update_gui)
        # stop QTimer when program closing
        self.gui_closing.connect(self.timer.stop)

        # set update period (after timer is created!!)
        self._update_period = None
        self.update_period = update_period

        # initialize controls to starting values
        self.init_controls()

        self.init_ui()
        self.start_time = time.time()

        self.update_gui()

    @property
    def update_period(self):
        return self._update_period

    @update_period.setter
    def update_period(self, update_period):
        assert(isinstance(update_period, float) or isinstance(update_period, int))

        if update_period != self._update_period:
            # if the timer is active, stop it and restart with new period
            # if self.timer.isActive():
            self.timer.setInterval(update_period*1000)

            # store new value
            self._update_period = update_period

    def init_controls(self):
        """
        on startup, set controls in coordinator to ensure init state is synchronized
        """

        for control_name, control_params in self.CONTROL.items():
            self.set_value(control_params.default, control_name)

    def set_value(self, new_value, value_name=None):
        """
        Set a control value with the ``coordinator``

        Args:
            new_value (float): Som
        """
        # get sender ID
        if value_name is None:
            value_name = self.sender().objectName()

        elif not isinstance(value_name, str):
            # TODO: More explicitly check for enum
            value_name = value_name.name


        control_object = ControlSetting(name=getattr(ValueName, value_name),
                                        value=new_value,
                                        min_value = self.CONTROL[getattr(ValueName, value_name)]['safe_range'][0],
                                        max_value = self.CONTROL[getattr(ValueName, value_name)]['safe_range'][1],
                                        timestamp = time.time())
        self.coordinator.set_control(control_object)


    def update_gui(self):
        try:
            # get alarms
            #active_alarms = self.coordinator.get_active_alarms()
            #self.alarms_updated.emit(active_alarms)


            vals = self.coordinator.get_sensors()

            for plot_key, plot_obj in self.plots.items():
                if hasattr(vals, plot_key):
                    plot_obj.update_value((time.time(), getattr(vals, plot_key)))

            for monitor_key, monitor_obj in self.monitor.items():
                if hasattr(vals, monitor_key):
                    monitor_obj.update_value(getattr(vals, monitor_key))

        #
        finally:
            self.timer.start()




    def update_value(self, value_name, new_value):
        """
        Arguments:
            value_name (str): Name of key in :attr:`.Vent_Gui.monitor` and :attr:`.Vent_Gui.plots` to update
            new_value (int, float): New value to display/plot
        """
        if value_name in self.monitor.keys():
            self.monitor[value_name].update_value(new_value)
        elif value_name in self.plots.keys():
            self.plots[value_name].update_value(new_value)

    def init_ui(self):
        """
        Create the UI components for the ventilator screen
        """

        # basic initialization


        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setContentsMargins(0,0,0,0)
        #
        self.setCentralWidget(self.main_widget)

        # layout
        #   - two rows (status, main)
        #   - three columns
        #       left:   monitor values
        #       center: plotted values
        #       right:  controls
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.main_widget.setLayout(self.layout)

        # layout that includes the display and controls
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)


        # call sub-create functions to make ui sections
        # top status bar
        self.init_ui_status_bar()
        # left monitored values
        self.init_ui_monitor()
        # plots
        self.init_ui_plots()
        # controls
        self.init_ui_controls()

        # add main ui area to layout
        self.layout.addLayout(self.main_layout, self.main_height)

        # connect signals and slots
        self.init_ui_signals()

        self.show()

    def init_ui_status_bar(self):
        ############
        # Status Bar
        status_box = QtWidgets.QGroupBox('System Status')
        status_box.setStyleSheet(styles.STATUS_BOX)
        status_layout = QtWidgets.QHBoxLayout()
        self.status_bar = widgets.Status_Bar()
        status_layout.addWidget(self.status_bar)
        status_layout.setContentsMargins(0,0,0,0)
        status_box.setLayout(status_layout)

        self.layout.addWidget(status_box, self.status_height)

    def init_ui_monitor(self):

        #########
        # display values
        # box that contains both the monitors and the plots
        self.monitor_box = QtWidgets.QGroupBox("Sensor Monitor")
        self.monitor_layout = QtWidgets.QHBoxLayout()
        self.monitor_layout.setContentsMargins(0, 0, 0, 0)
        self.monitor_box.setLayout(self.monitor_layout)

        # box that just displays the monitor widgets
        self.display_layout = QtWidgets.QVBoxLayout()
        self.display_layout.setContentsMargins(0,0,0,0)

        for display_key, display_params in self.MONITOR.items():
            self.monitor[display_key.name] = widgets.Monitor(display_params, enum_name=display_key)
            self.display_layout.addWidget(self.monitor[display_key.name])
            self.display_layout.addWidget(widgets.components.QHLine())

        self.display_layout.addStretch(10)

        self.monitor_layout.addLayout(self.display_layout, self.monitor_width)

        self.main_layout.addWidget(self.monitor_box, self.plot_width + self.monitor_width)


    def init_ui_plots(self):
        ###########
        # plots
        self.plot_layout = QtWidgets.QVBoxLayout()
        self.plot_layout.setContentsMargins(0, 0, 0, 0)

        # button to set plot history
        button_box = QtWidgets.QGroupBox("Plot History")
        # button_group = QtWidgets.QButtonGroup()
        # button_group.exclusive()
        times = (("5s", 5),
                 ("10s", 10),
                 ("30s", 30),
                 ("1m", 60),
                 ("5m", 60 * 5),
                 ("15m", 60 * 15),
                 ("60m", 60 * 60))

        self.time_buttons = {}
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        for a_time in times:
            self.time_buttons[a_time[0]] = QtWidgets.QRadioButton(a_time[0])
            self.time_buttons[a_time[0]].setObjectName(str(a_time[1]))
            self.time_buttons[a_time[0]].clicked.connect(self.set_plot_duration)
            button_layout.addWidget(self.time_buttons[a_time[0]])

        button_box.setLayout(button_layout)
        self.plot_layout.addWidget(button_box)

        # the plot widgets themselves
        for plot_key, plot_params in self.PLOTS.items():
            self.plots[plot_key.name] = widgets.Plot(**plot_params)
            self.plot_layout.addWidget(self.plots[plot_key.name])

        # self.main_layout.addLayout(self.plot_layout,5)
        self.monitor_layout.addLayout(self.plot_layout, self.plot_width)

        ######################
        # set the default view as 30s
        self.time_buttons[times[2][0]].click()

    def init_ui_controls(self):
        ####################
        # Controls
        self.controls_box = QtWidgets.QGroupBox("Ventilator Controls")
        # set name so it catches the stylesheet
        self.controls_box.setObjectName('CONTROLBOX')
        # controls_box.setStyleSheet(styles.CONTROL_BOX)

        self.controls_box.setContentsMargins(0, 0, 0, 0)

        self.controls_layout = QtWidgets.QVBoxLayout()
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        for control_name, control_params in self.CONTROL.items():
            self.controls[control_name.name] = widgets.Control(control_params)
            self.controls[control_name.name].setObjectName(control_name.name)
            self.controls[control_name.name].value_changed.connect(self.set_value)
            self.controls_layout.addWidget(self.controls[control_name.name])
            self.controls_layout.addWidget(widgets.components.QHLine(color=styles.DIVIDER_COLOR_DARK))

        self.controls_layout.addStretch(10)
        self.controls_box.setLayout(self.controls_layout)

        self.main_layout.addWidget(self.controls_box, self.control_width)

    def init_ui_signals(self):
        """
        Connect Qt signals and slots
        """

        # hook up monitors and plots
        for value in ValueName:
            if value.name in self.plots.keys():
                self.monitor[value.name].limits_changed.connect(
                    self.plots[value.name].set_safe_limits)
                self.plots[value.name].limits_changed.connect(
                    self.monitor[value.name].update_limits)

        # connect monitors to alarm_manager
        for monitor in self.monitor.values():
            monitor.alarm.connect(self.alarm_manager.monitor_alarm)

        # connect alarms to alarm manager, and then back to us
        self.alarms_updated.connect(self.alarm_manager.update_alarms)
        self.alarm_manager.new_alarm.connect(self.handle_alarm)
        # FIXME: THis should be handled by alarm manager, that's what it's there for!
        #self.status_bar.status_message.level_changed.connect(self.alarm_state_changed)
        self.status_bar.status_message.message_cleared.connect(self.handle_cleared_alarm)

        # connect start button to coordinator start
        self.status_bar.start_button.clicked.connect(self.coordinator.start)

    @QtCore.Slot(Alarm)
    def handle_alarm(self, alarm):
        self.status_bar.status_message.update_message(alarm)
        try:
            self.monitor[alarm.alarm_name.name].alarm_state = True
        except:
            # FIXME: will be fixed when values are displayed next to controls
            pass
        if alarm.severity.value > self.alarm_state.value:
            self.alarm_state = alarm.severity

    @QtCore.Slot(Alarm)
    def handle_cleared_alarm(self, alarm):
        try:
            self.monitor[alarm.alarm_name.name].alarm_state = False
        except:
            # FIXME: will be fixed when values are displayed next to controls
            pass


    @property
    def alarm_state(self):
        return self._alarm_state

    @alarm_state.setter
    def alarm_state(self, state):
        if state == AlarmSeverity.HIGH:
            pass

    @QtCore.Slot(AlarmSeverity)
    def alarm_state_changed(self, state):
        self.alarm_state = state

    def set_plot_duration(self, dur):
        dur = int(self.sender().objectName())

        for plot in self.plots.values():
            plot.set_duration(dur)

    def closeEvent(self, event):
        """
        Emit :attr:`.gui_closing` and close!
        """
        #globals()['_GUI_INSTANCE'] = None
        set_gui_instance(None)
        self.gui_closing.emit()

        if self.coordinator:
            try:
                self.coordinator.stop()
            except:
                raise Warning('had a thread object, but the thread object couldnt be stopped')

        event.accept()

    def start(self):
        """
        Click the :meth:`~.gui.widgets.status_bar.Status_Bar.start` button

        Returns:

        """
        self.status_bar.start_button.click()


def launch_gui(coordinator):

    # just for testing, should be run from main
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(styles.DARK_THEME)
    app = styles.set_dark_palette(app)
    gui = Vent_Gui(coordinator)

    return app, gui