import time
import sys
import threading
import pdb
import os

from PySide2 import QtWidgets, QtCore, QtGui

from vent.common.message import ControlSetting
from vent.alarm import AlarmSeverity, Alarm
from vent.common.values import ValueName
from vent import gui
from vent.gui import widgets, set_gui_instance, get_gui_instance, styles, PLOTS
from vent.gui.alarm_manager import AlarmManager
from vent.common import values


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

    MONITOR = values.DISPLAY
    """
    see :data:`.gui.defaults.DISPLAY`
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

    def __init__(self, coordinator, update_period = 0.05):
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

        self.running = False

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
            if control_name == ValueName.IE_RATIO:
                continue
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

            if not self.running:
                return
            # get alarms
            #active_alarms = self.coordinator.get_active_alarms()
            #self.alarms_updated.emit(active_alarms)


            vals = self.coordinator.get_sensors()

            # update ideal waveform
            # pdb.set_trace()
            self.pressure_waveform.update_target(self.coordinator.get_target_waveform())
            self.pressure_waveform.update_waveform(vals)

            for plot_key, plot_obj in self.plots.items():
                if hasattr(vals, plot_key):
                    plot_obj.update_value((time.time(), getattr(vals, plot_key)))

            for monitor_key, monitor_obj in self.monitor.items():
                if hasattr(vals, monitor_key):
                    monitor_obj.update_value(getattr(vals, monitor_key))

            for control_key, control in self.controls.items():
                if hasattr(vals, control_key):
                    control.update_sensor(getattr(vals, control_key))

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
            if display_key in self.CONTROL.keys():
                continue
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
            self.plot_layout.addWidget(self.plots[plot_key.name], 1)

        # the idealized waveform display
        self.pressure_waveform = widgets.Pressure_Waveform()
        self.plot_layout.addWidget(self.pressure_waveform, len(self.plots))


        # self.main_layout.addLayout(self.plot_layout,5)
        self.monitor_layout.addLayout(self.plot_layout, self.plot_width)

        ######################
        # set the default view as 30s
        self.time_buttons[times[2][0]].click()

    def init_ui_controls(self):
        # FIXME: Jonny this is shameful comment your work

        ####################
        # Controls - Pressure
        self.controls_layout = QtWidgets.QVBoxLayout()

        self.controls_box_pressure = QtWidgets.QGroupBox("Pressure Controls")
        self.controls_box_pressure.setStyleSheet(styles.CONTROL_BOX)
        self.controls_box_pressure.setContentsMargins(0, 0, 0, 0)

        self.controls_layout_pressure = QtWidgets.QVBoxLayout()
        self.controls_layout_pressure.setContentsMargins(0, 0, 0, 0)
        for control_name in (ValueName.PIP, ValueName.PEEP):
            control_params = self.CONTROL[control_name]
            self.controls[control_name.name] = widgets.Control(control_params)
            self.controls[control_name.name].setObjectName(control_name.name)
            self.controls_layout_pressure.addWidget(self.controls[control_name.name])
            self.controls_layout_pressure.addWidget(widgets.components.QHLine(color=styles.DIVIDER_COLOR_DARK))

        #self.controls_layout_pressure.addStretch(10)
        self.controls_box_pressure.setLayout(self.controls_layout_pressure)

        ####################
        # Controls - Cycle
        self.controls_box_cycle = QtWidgets.QGroupBox("Breath Cycle Controls")
        self.controls_box_cycle.setStyleSheet(styles.CONTROL_BOX)
        #self.controls_box_cycle.setContentsMargins(0, 0, 0, 0)


        self.controls_cycle_layout = QtWidgets.QVBoxLayout()
        # one row of radio buttons to select which is autoset
        # then the control widgets are added below
        self.controls_cycle_group = QtWidgets.QGroupBox('Auto-Calculate')
        self.controls_cycle_button_group = QtWidgets.QButtonGroup()
        self.controls_cycle_group.setStyleSheet(styles.CONTROL_CYCLE_BOX)
        self.controls_cycle_buttons = {}
        self.controls_layout_cycle_buttons = QtWidgets.QHBoxLayout()
        self.controls_layout_cycle_widgets = QtWidgets.QVBoxLayout()
        self.controls_cycle_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout_cycle_widgets.setContentsMargins(0, 0, 0, 0)
        for control_name in (ValueName.BREATHS_PER_MINUTE, ValueName.INSPIRATION_TIME_SEC, ValueName.IE_RATIO):
            control_params = values.VALUES[control_name]
            self.controls[control_name.name] = widgets.Control(control_params)
            self.controls[control_name.name].setObjectName(control_name.name)

            self.controls_cycle_buttons[control_name] = QtWidgets.QRadioButton(control_params.name)
            self.controls_cycle_buttons[control_name].setObjectName(control_name.name)
            self.controls_layout_cycle_buttons.addWidget(self.controls_cycle_buttons[control_name])
            self.controls_cycle_button_group.addButton(self.controls_cycle_buttons[control_name])
            #self.controls_layout_cycle_buttons.addWidget(widgets.components.QHLine(color=styles.DIVIDER_COLOR_DARK))
            if control_name != ValueName.IE_RATIO:
                self.controls_layout_cycle_widgets.addWidget(self.controls[control_name.name])
                self.controls_layout_cycle_widgets.addWidget(widgets.components.QHLine(color=styles.DIVIDER_COLOR_DARK))
            else:
                self.controls[control_name.name].setVisible(False)
                self.controls_cycle_buttons[control_name].setChecked(True)

        self.controls_cycle_button_group.buttonClicked.connect(self.toggle_cycle_widget)

        self.controls_cycle_group.setLayout(self.controls_layout_cycle_buttons)

        self.controls_cycle_layout.addWidget(self.controls_cycle_group)
        self.controls_cycle_layout.addLayout(self.controls_layout_cycle_widgets)

        self.controls_box_cycle.setLayout(self.controls_cycle_layout)

        ########
        # Controls - ramp

        self.controls_box_ramp = QtWidgets.QGroupBox("Ramp Controls")
        self.controls_box_ramp.setStyleSheet(styles.CONTROL_BOX)
        self.controls_box_ramp.setContentsMargins(0, 0, 0, 0)

        self.controls_layout_ramp = QtWidgets.QVBoxLayout()
        self.controls_layout_ramp.setContentsMargins(0, 0, 0, 0)
        for control_name in (ValueName.PIP_TIME, ValueName.PEEP_TIME):
            control_params = self.CONTROL[control_name]
            self.controls[control_name.name] = widgets.Control(control_params)
            self.controls[control_name.name].setObjectName(control_name.name)
            self.controls_layout_ramp.addWidget(self.controls[control_name.name])
            self.controls_layout_ramp.addWidget(widgets.components.QHLine(color=styles.DIVIDER_COLOR_DARK))

        # self.controls_layout_ramp.addStretch(10)
        self.controls_box_ramp.setLayout(self.controls_layout_ramp)


        self.controls_layout.addWidget(self.controls_box_pressure)
        self.controls_layout.addWidget(self.controls_box_cycle)
        self.controls_layout.addWidget(self.controls_box_ramp)

        self.main_layout.addLayout(self.controls_layout, self.control_width)

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

        # connect controls
        for control in self.controls.values():
            control.value_changed.connect(self.set_value)
            control.value_changed.connect(self.set_value)

        # connect start button to coordinator start
        self.status_bar.start_button.toggled.connect(self.setState)

    @QtCore.Slot(QtWidgets.QAbstractButton)
    def toggle_cycle_widget(self, button):
        # get name of button
        value_name = button.objectName()
        #pdb.set_trace()

        # clear everything
        while self.controls_layout_cycle_widgets.count():
            _ = self.controls_layout_cycle_widgets.takeAt(0)

        line_added = False
        for value in (ValueName.BREATHS_PER_MINUTE, ValueName.INSPIRATION_TIME_SEC, ValueName.IE_RATIO):
            control = self.controls[value.name]
            if value.name == value_name:
                control.setVisible(False)
                #self.controls_layout_cycle_widgets.removeWidget(control)
            else:
                #if not control.isVisible():
                control.setVisible(True)
                self.controls_layout_cycle_widgets.addWidget(control)
                control.adjustSize()
                # if not line_added:
                #     self.controls_layout_cycle_widgets.addWidget(
                #         widgets.components.QHLine(color=styles.DIVIDER_COLOR_DARK))
                #     line_added = True

        #self.adjustSize()

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

    @QtCore.Slot()
    def update_target_waveform(self):
        target_waveform = self.coordinator.get

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

    def setState(self, state: bool):
        """
        set running true or not

        Args:
            state (bool): running or no?

        Returns:

        """
        if state:
            self.running = True
            for plot in self.plots.values():
                plot.reset_start_time()
            self.coordinator.start()
        else:
            # TODO: what happens when u stop lol
            pass


def launch_gui(coordinator):

    # just for testing, should be run from main
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(styles.DARK_THEME)
    app = styles.set_dark_palette(app)
    gui = Vent_Gui(coordinator)

    return app, gui