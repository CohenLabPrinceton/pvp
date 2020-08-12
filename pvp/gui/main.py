import time
import sys
import threading
import pdb
import os
import typing
import json

from PySide2 import QtWidgets, QtCore, QtGui

import pvp.gui.widgets.alarm_bar
from pvp import prefs
from pvp.alarm import AlarmSeverity, Alarm
from pvp.common import values
from pvp.common.values import ValueName
from pvp.common.loggers import init_logger
from pvp.common.message import ControlSetting, SensorValues
from pvp.coordinator import coordinator
from pvp import gui
from pvp.gui import widgets, set_gui_instance, get_gui_instance, styles, mono_font
from pvp.alarm import Alarm_Manager




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

    state_changed = QtCore.Signal(bool)
    """
    :class:`PySide2.QtCore.Signal` emitted when the gui is started (True) or stopped (False)
    """


    MONITOR = values.DISPLAY_MONITOR
    """
    see :data:`.gui.defaults.DISPLAY_MONITOR`
    """

    CONTROL = values.DISPLAY_CONTROL
    """
    see :data:`.gui.defaults.CONTROL`
    """

    PLOTS = values.PLOTS
    """
    see :data:`.gui.defaults.PLOTS`
    """

    monitor_width = 3
    plot_width = 4
    control_width = 3
    total_width = monitor_width + plot_width + control_width
    """
    computed from ``monitor_width+plot_width+control_width``
    """

    status_height = 2
    main_height = 5
    total_height = status_height+main_height
    """
    computed from ``status_height+main_height``
    """

    def __init__(self,
                 coordinator: coordinator.CoordinatorBase,
                 set_defaults: bool = False,
                 update_period: float = 0.05):
        """
        The Main GUI window.

        Only one instance can be created at a time. Uses :func:`set_gui_instance` to
        store a reference to itself. after initialization, use `get_gui_instance` to
        retrieve a reference.

        .. todo:

            Jonny add a screenshot here when final version.


        Attributes:
            monitor (dict): Dictionary mapping :data:`.values.SENSOR` keys to :class:`.widgets.Display_Value` objects
            plots (dict): Dictionary mapping :data:`.gui.PLOT` keys to :class:`.widgets.Plot` objects
            controls (dict): Dictionary mapping :data:`.values.CONTROL` keys to :class:`.widgets.Display` objects
            coordinator (:class:`pvp.coordinator.coordinator.CoordinatorBase`): Some coordinator object that we use to communicate with the controller
            control_module (:class:`pvp.controller.control_module.ControlModuleBase`): Reference to the control module, retrieved from coordinator
            start_time (float): Start time as returned by :func:`time.time`
            update_period (float): The global delay between redraws of the GUI (seconds)
            alarm_manager (:class:`~.alarm.alarm_manager.Alarm_Manager`)
            _alarm_state (:class:`~.alarm.AlarmSeverity`): current maximum alarm severity
            alarms (dict): any active alarms that are being displayed


        Arguments:
            coordinator: The :class:`pvp.coordinator.coordinator.CoordinatorBase` object!
            set_defaults (bool): Whether default `Value` s should be set on initialization (default ``False``)
            update_period (float): The global delay between redraws of the GUI (seconds)
            test (bool): Whether the monitored values and plots should be fed sine waves for visual testing.


        """
        self.logger = init_logger(__name__)

        # load mono font before initing widgets
        _ = mono_font()

        if get_gui_instance() is not None and gui.limit_gui():
            self.logger.exception('GUI attempted to be instantiated but instance of gui already running!')
            raise Exception('Instance of gui already running!') # pragma: no cover
        else:
            set_gui_instance(self)

        super(Vent_Gui, self).__init__()

        self.alarm_manager = Alarm_Manager()
        self._alarm_state = AlarmSeverity.OFF
        self.alarms = {}
        # connect alarm manager signals to slots
        self.alarm_manager.add_callback(self.handle_alarm)
        self.alarm_manager.add_dependency_callback(self.limits_updated)
        self.logger.debug('Alarm Manager instantiated')

        self.monitor = {} # type: typing.Dict[ValueName, widgets.Display]
        #self.plots = {} # type: typing.Dict[ValueName, widgets.Plot]
        self.plot_box = None # type: typing.Union[None, widgets.plot.Plot_Container]
        self.controls = {} # type: typing.Dict[ValueName.name, widgets.Display]

        self.coordinator = coordinator

        # start QTimer to update values
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.update_gui)
        # stop QTimer when program closing
        self.gui_closing.connect(self.timer.stop)

        # set update period (after timer is created!!)
        self._update_period = None
        self.update_period = update_period

        self._autocalc_cycle = ValueName.INSPIRATION_TIME_SEC # which of the cycle control to autocalculate

        self.running = False
        self.locked = False

        # keep track of set values!!!
        self._state = {
            'controls': {}
        }



        self.init_ui()
        self.start_time = time.time()

        # initialize controls to starting values
        if set_defaults:
            self.init_controls()

        self.toggle_cycle_widget(values.ValueName.INSPIRATION_TIME_SEC)

        self.show()
        self.update_gui()

        # no idea why but we have to set the stylesheets again after showing in order to
        # get the fonts to work right
        self.controls_box.setStyleSheet(styles.CONTROL_BOX)
        self.monitor_box.setStyleSheet(styles.MONITOR_BOX)

        self.logger.info('GUI Initialized Successfully')

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
            if control_name == self._autocalc_cycle:
                continue
            self.set_value(control_params.default, control_name)

    def set_value(self, new_value, value_name=None):
        """
        Set a control value using a value and its name.

        .. note::

            This method is primarily intended as a means of responding to signals from other widgets,
            Other cases should use :meth:`.set_control`

        Args:
            new_value (float): Som
        """
        # get sender ID
        if value_name is None:
            value_name = self.sender().objectName()

        elif isinstance(value_name, ValueName):
            # TODO: More explicitly check for enum
            value_name = value_name.name


        # if we're not autocalculating the IE ratio, just send the control through
        # otherwise we have to compute something from the IE ratio.
        if value_name in (ValueName.BREATHS_PER_MINUTE.name,
                          ValueName.IE_RATIO.name,
                          ValueName.INSPIRATION_TIME_SEC.name):
            self._set_cycle_control(value_name, new_value)

        else:
            control_object = ControlSetting(name=getattr(ValueName, value_name),
                                            value=new_value,
                                            timestamp = time.time())
            self.set_control(control_object)

    def _set_cycle_control(self, value_name: str, new_value: float):
        """
        Compute the computed breath cycle control.

        We only actually have BPM and INSPt as controls, so if we're using I:E ratio we have to compute one or the other.

        Computes the value and calls :meth:`.set_control` with the appropriate values

        # ie = inspt/expt
        # inspt = ie*expt
        # expt = inspt/ie
        #
        # cycle_time = inspt + expt
        # cycle_time = inspt + inspt/ie
        # cycle_time = inspt*(1+1/ie)
        #inspt = cycle_time/(1+1/ie)
        # cycle_time - expt
        """
        bpm = None
        inspt = None
        ie = None

        if self._autocalc_cycle == ValueName.INSPIRATION_TIME_SEC:
            if value_name == ValueName.IE_RATIO.name:
                ie = new_value
                # try to get BPM:
                try:
                    bpm = self._state['controls'][ValueName.BREATHS_PER_MINUTE.name]
                    cycle_time = 1/(bpm/60)
                    inspt = cycle_time/(1+1/new_value)

                except KeyError: # pragma no cover
                    self.logger.debug('Tried to set breath cycle controls with autocalc INSPt, but dont have BPM yet.') # pragma: no cover
                    # do nothing -- we've alredy stashed IE ratio above, will set both once we have bpm

            elif value_name == ValueName.BREATHS_PER_MINUTE.name:
                bpm = new_value
                # try to get ie
                try:
                    ie = self._state['controls'][ValueName.IE_RATIO.name]
                    cycle_time = 1/(new_value/60)
                    inspt = cycle_time / (1 + 1 / ie)
                except KeyError:
                    self.logger.debug('Tried to set breath cycle controls with autocalc INSPt, but dont have IE ratio yet. Setting BPM alone')

        elif self._autocalc_cycle == ValueName.BREATHS_PER_MINUTE:
            if value_name == ValueName.IE_RATIO.name:
                ie = new_value
                try:
                    inspt = self._state['controls'][ValueName.INSPIRATION_TIME_SEC.name]
                    expt = inspt/new_value
                    cycle_time = inspt + expt # in Hz
                    bpm = (1/cycle_time)*60
                except KeyError:
                    self.logger.debug(
                        'Tried to set breath cycle controls with autocalc BPM, but dont have INSPt yet.')

            elif value_name == ValueName.INSPIRATION_TIME_SEC.name:
                inspt = new_value
                try:
                    ie = self._state['controls'][ValueName.IE_RATIO.name]
                    expt = new_value / ie
                    cycle_time = new_value + expt  # in Hz
                    bpm = (1 / cycle_time) * 60
                except KeyError:
                    self.logger.debug(
                        'Tried to set breath cycle controls with autocalc BPM, but dont have I:E yet. Setting INSPt alone')

        elif self._autocalc_cycle == ValueName.IE_RATIO:
            # don't need ta do anything, just calculate, stash, and set
            try:
                if value_name == ValueName.BREATHS_PER_MINUTE.name:
                    bpm = new_value
                    inspt = self._state['controls'][ValueName.INSPIRATION_TIME_SEC.name]
                elif value_name == ValueName.INSPIRATION_TIME_SEC.name:
                    inspt = new_value
                    bpm = self._state['controls'][ValueName.BREATHS_PER_MINUTE.name]

                cycle_time = 1 / (bpm / 60)
                expt = cycle_time - inspt
                ie = inspt/expt

            except KeyError:
                self.logger.debug(
                    f'Tried to set breath cycle controls with autocalc IE Ratio, but dont have BPM and INSPt. Setting {value_name} without calculating IE')


        #set whatever values we have
        for _value_name, _set_value in zip(
                (ValueName.INSPIRATION_TIME_SEC, ValueName.BREATHS_PER_MINUTE, ValueName.IE_RATIO),
                (inspt, bpm, ie)):
            if _set_value is not None:
                if _value_name.name in self._state['controls'].keys() and _set_value == self._state['controls'][_value_name.name]:
                    continue
                else:
                    self.set_control(ControlSetting(
                        name=_value_name,
                        value=_set_value
                    ))

    def set_control(self, control_object: ControlSetting):
        """
        Set a control in the alarm manager, coordinator, and gui

        Args:
            control_object:

        Returns:

        """
        if isinstance(control_object, list):
            control_object = control_object[0] # pragma: no cover
        # pdb.set_trace()
        self.logger.info(f'Setting control value: {control_object.name.name}, {control_object.value}')

        # FIXME: replace set_value with this kinda thing
        #self.logger.debug(control_object.__dict__)
        self.alarm_manager.update_dependencies(control_object)
        if control_object.name != ValueName.IE_RATIO:
            self.coordinator.set_control(control_object)

        if control_object.name.name in self.controls.keys():
            self.controls[control_object.name.name].update_set_value(control_object.value)

        # if control_object.name in self.pressure_waveform.PARAMETERIZING_VALUES:
        #     self.pressure_waveform.update_target(control_object)

        self.update_state('controls', control_object.name.name, control_object.value)

    def update_gui(self, vals: SensorValues = None):
        """

        Args:
            vals (:class:`.SensorValue`): Default None, but SensorValues can be passed manually -- usually for debugging

        """
        try:
            # if not running yet, don't update anything else.
            if not self.running:
                return

            if not vals:
                vals = self.coordinator.get_sensors()

            # update alarms
            # only after first breath! many values are only defined after first cycle
            if vals.breath_count > 1:
                # don't test this because we don't usually want the GUI just updating during tests
                # and this method is really heavy, so we test each of the pieces separately
                self.alarm_manager.update(vals) # pragma: no cover

            try:
                controller_alarms = self.coordinator.get_alarms()
                if isinstance(controller_alarms, (tuple, list)):
                    for alarm in controller_alarms:
                        # alarm can either be Alarm object of a list of Alarm objects
                        if isinstance(alarm, Alarm):
                            self.handle_alarm(alarm) # pragma: no cover - testing separately
                        elif isinstance(alarm, (tuple, list)):
                            for subalarm in alarm:
                                self.handle_alarm(subalarm)
                        else:
                            self.logger.warning(f'Dont know how to handle {alarm} gotten from controller get_alarms() method')
                elif controller_alarms is not None:
                    self.logger.warning(f'Dont know how to handle {controller_alarms} gotten from controller get_alarms() method')
            except Exception as e: # pragma: no cover
                self.logger.exception(f'Couldnt get alarms from controller, got error {e}')

            try:
                self.plot_box.update_value(vals)
            except Exception as e: # pragma: no cover
                self.logger.exception(f"couldnt update plot box with {vals}, got {e}")

            for monitor_key, monitor_obj in self.monitor.items():
                if hasattr(vals, monitor_key):
                    try:
                        monitor_obj.update_sensor_value(getattr(vals, monitor_key))
                    except Exception as e: # pragma: no cover
                        self.logger.exception(f'Couldnt update monitor object with {monitor_key}, got error {e}')

            for control_key, control in self.controls.items():
                if hasattr(vals, control_key):
                    try:
                        control.update_sensor_value(getattr(vals, control_key))
                    except Exception as e: # pragma: no cover
                        self.logger.exception(f'Couldnt update control object with {control_key}, got error {e}')

            # let our  timer know we got some data
            self.control_panel.heartbeat.beatheart(vals.timestamp)
        #
        finally:
            self.timer.start()

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
        self.layout = QtWidgets.QGridLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        self.main_widget.setLayout(self.layout)

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
        # self.layout.addLayout(self.main_layout, self.main_height)

        # connect signals and slots
        self.init_ui_signals()

        self.showMaximized()
        self.setFixedSize(self.width(), self.height())
        self.layout.setColumnStretch(0, self.monitor_width)
        self.layout.setColumnStretch(1, self.plot_width)
        self.layout.setColumnStretch(2, self.control_width)

    def init_ui_status_bar(self):
        ############
        # Status Bar
        self.control_panel = widgets.Control_Panel()
        self.alarm_bar = widgets.Alarm_Bar()


        self.layout.addWidget(self.control_panel, 0,0, 2,1)
        self.layout.addWidget(self.alarm_bar, 0,1,1,2)

    def init_ui_monitor(self):

        #########
        # display values
        # box that contains both the monitors and the plots
        self.monitor_box = QtWidgets.QGroupBox("Sensor Monitor")
        self.monitor_box.setContentsMargins(0,0,0,0)
        self.monitor_box.setStyleSheet(styles.MONITOR_BOX)

        # box that just displays the monitor widgets
        self.display_layout = QtWidgets.QVBoxLayout()
        self.display_layout.setContentsMargins(0,0,0,0)
        self.monitor_box.setLayout(self.display_layout)

        for display_key, display_params in self.MONITOR.items():
            if display_key in self.CONTROL.keys():
                continue

            self.monitor[display_key.name] = widgets.Display(display_params, enum_name=display_key,
                                                             control_type=display_params.control_type,
                                                             button_orientation='left', style='dark')

            self.display_layout.addWidget(self.monitor[display_key.name], 1)

        self.display_layout.addStretch(10)

        self.layout.addWidget(self.monitor_box, 2,0,2,1)



    def init_ui_plots(self):
        ###########
        # plots
        self.plot_layout = QtWidgets.QVBoxLayout()
        self.plot_layout.setContentsMargins(0, 0, 0, 0)

        # the plot widgets themselves

        self.plot_box = widgets.plot.Plot_Container(self.PLOTS)

        self.layout.addWidget(self.plot_box, 1, 1, 3, 1)

    def init_ui_controls(self):
        # FIXME: Jonny this is shameful comment your work

        # All-controls box

        self.controls_box = QtWidgets.QGroupBox("Controls")
        self.controls_box.setContentsMargins(0, 0, 0, 0)

        self.controls_layout = QtWidgets.QVBoxLayout()
        self.controls_layout.setContentsMargins(0,0,0,0)
        self.controls_box.setLayout(self.controls_layout)

        ####################
        # Controls - Pressure
        for control_name, control in self.CONTROL.items():
            self.controls[control_name.name] = widgets.Display(value=control, button_orientation="right", style="light",
                                                               enum_name=control_name,
                                                               control_type=control.control_type,
                                                               parent=self.controls_box)
            self.controls[control_name.name].setObjectName(control_name.name)
            self.controls_layout.addWidget(self.controls[control_name.name])

        # TODO: Jonny implement groups (maybe?) and move the automatic calculation to the control panel
        self.controls_box.setStyleSheet(styles.CONTROL_BOX)
        self.controls_layout.addStretch(10)

        self.layout.addWidget(self.controls_box, 1,2,3,1)

    def init_ui_signals(self):
        """
        Connect Qt signals and slots
        """

        #self.alarm_bar.message_cleared.connect(self.handle_cleared_alarm)

        # connect controls
        for control in self.controls.values():
            control.value_changed.connect(self.set_value)

        for monitor in self.monitor.values():
            monitor.value_changed.connect(self.set_value)

        # TODO also connect monitor signals

        # connect start button to coordinator start
        self.control_panel.start_button.toggled.connect(self.toggle_start)

        # connect lock button
        self.control_panel.lock_button.toggled.connect(self.toggle_lock)

        self.control_panel.controls_cycle_button_group.buttonClicked.connect(self.toggle_cycle_widget)

        # control panel buttons & settings
        self.control_panel.pressure_units_changed.connect(self.set_pressure_units)
        self.control_panel.breath_detection_button.toggled.connect(self.set_breath_detection)

        # connect heartbeat indicator to set off before controller starts
        self.state_changed.connect(self.control_panel.heartbeat.set_state)

    @QtCore.Slot(QtWidgets.QAbstractButton)
    def toggle_cycle_widget(self, button):

        if isinstance(button, QtWidgets.QAbstractButton):
            # get name of button
            value_name = button.objectName()
            #pdb.set_trace()
            self._autocalc_cycle = ValueName.__members__[value_name]

        elif isinstance(button, values.ValueName):
            value_name = button.name
            self._autocalc_cycle = button

        else:
            self.logger.exception(f"Dont know how to set autocalc cycle with {button}") # pragma: no cover
            return # pragma: no cover

        for value in (ValueName.BREATHS_PER_MINUTE, ValueName.INSPIRATION_TIME_SEC, ValueName.IE_RATIO):
            control = self.controls[value.name]
            if value.name == value_name:
                control.setVisible(False)
            else:
                control.setVisible(True)

    @QtCore.Slot(Alarm)
    def handle_alarm(self, alarm: Alarm):
        """
        Update :class:`~.Status_Bar` and any affected widgets

        Args:
            alarm (:class:`~.Alarm`)


        """
        self.logger.info(str(alarm))

        if alarm.severity > AlarmSeverity.OFF:

            self.alarm_bar.add_alarm(alarm)
        else:
            self.alarm_bar.clear_alarm(alarm)

        try:
            self.monitor[alarm.alarm_name.name].alarm_state = True
        except:
            # FIXME: will be fixed when values are displayed next to controls
            pass
        if alarm.severity > self.alarm_state:
            self.alarm_state = alarm.severity

    @QtCore.Slot(ControlSetting)
    def limits_updated(self, control:ControlSetting):
        if control.name.name in self.controls.keys():
            self.controls[control.name.name].update_limits(control)
        if control.name.name in self.monitor.keys():
            self.monitor[control.name.name].update_limits(control)
        self.plot_box.set_safe_limits(control)

    # @QtCore.Slot(Alarm)
    # def handle_cleared_alarm(self, alarm):
    #     try:
    #         self.monitor[alarm.alarm_name.name].alarm_state = False
    #     except:
    #         # FIXME: will be fixed when values are displayed next to controls
    #         pass

    @property
    def alarm_state(self):
        return self._alarm_state

    @alarm_state.setter
    def alarm_state(self, state):
        # FIXME: set colors on relevant widgets
        self._alarm_state = state # pragma: no cover
        pass
        # if state == AlarmSeverity.HIGH:
        #     pass

    # @QtCore.Slot(AlarmSeverity)
    # def alarm_state_changed(self, state):
    #     self.alarm_state = state

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
            except: # pragma: no cover
                raise Warning('had a thread object, but the thread object couldnt be stopped')

        event.accept()

    def start(self):
        """
        Click the :meth:`~.gui.widgets.control_panel.Status_Bar.start` button

        Returns:

        """
        self.control_panel.start_button.click()

    def toggle_start(self, state: bool):
        """
        set running true or not

        Args:
            state (bool): running or no?

        Returns:

        """
        if state:
            # check if all controls have been set
            if not self.controls_set:
                if 'pytest' not in sys.modules: # pragma: no cover
                    box = widgets.pop_dialog(
                        'Not all controls have been set',
                        'Please ensure all controls have been set before starting ventilation',
                    )
                    box.exec_()
                self.control_panel.start_button.set_state('OFF')
                return

            if 'pytest' not in sys.modules: # pragma: no cover - test controls_set and dialogs separately

                if prefs.get_pref('ENABLE_WARNINGS'):
                    box = widgets.pop_dialog(
                        'Confirm Ventilation Start',
                        modality = QtCore.Qt.WindowModal,
                        buttons = QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                        default_button = QtWidgets.QMessageBox.Cancel
                    )
                    ret = box.exec_()
                    if ret != QtWidgets.QMessageBox.Ok:
                        self.control_panel.start_button.set_state('OFF')
                        return


            self.running = True
            self.control_panel.runtime.start_timer()
            self.plot_box.reset_start_time()
            self.coordinator.start()
            self.control_panel.start_button.set_state('ON')
            # self.control_panel.lock_button.set_state('LOCKED')
            self.toggle_lock(True)
        else:
            # TODO: what happens when u stop lol
            # box = widgets.pop_dialog(
            #     'No such thing as stopping yet!',
            #     'NotImplementedError.exe',
            # )
            # box.exec_()
            if not self.running:
                return

            do_stop = False

            if 'pytest' not in sys.modules and prefs.get_pref('ENABLE_WARNINGS'): # pragma: no cover
                box = widgets.pop_dialog(
                    'Confirm Ventilation Stop',
                    'Stopping Ventilation Prematurely is Dangerous! Are you sure?',
                    modality=QtCore.Qt.WindowModal,
                    buttons=QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                    default_button=QtWidgets.QMessageBox.Cancel
                )
                ret = box.exec_()
                if ret != QtWidgets.QMessageBox.Ok:
                    self.control_panel.start_button.set_state('ON')
                    return
                else:
                    do_stop = True

            else:
                do_stop = True

            if do_stop:
                self.coordinator.stop()
                self.control_panel.start_button.set_state('OFF')
                self.toggle_lock(False)
                self.running = False
                self.control_panel.runtime.stop_timer()
            return

        self.state_changed.emit(state)

    def toggle_lock(self, state):
        if not self.running:
            self.control_panel.lock_button.set_state('DISABLED')
            self.logger.debug('Lock state changed to disabled')
        else:
            if state:
                self.control_panel.lock_button.set_state('LOCKED')
                self.controls_box.setStyleSheet(styles.CONTROL_BOX_LOCKED)

                for control in self.controls.values():
                    control.set_locked(True)

                self.logger.debug('Lock state changed to locked')
            else:
                self.control_panel.lock_button.set_state('UNLOCKED')
                self.controls_box.setStyleSheet(styles.CONTROL_BOX_UNLOCKED)

                for control in self.controls.values():
                    control.set_locked(False)

                # self.pressure_waveform.set_locked(False)
                self.logger.debug('Lock state changed to unlocked')

    def update_state(self, state_type: str, key:str, val: typing.Union[str,float,int]):
        """
        Update the GUI state and save it to disk

        Args:
            state_type (str): What type of state to save, one of ``('controls')``
            key (str): Which of that type is being saved (eg. if 'control', 'PIP')
            val (str, float, int): What is that item being set to?

        Returns:

        """
        if state_type not in self._state.keys():
            self.logger.warning(f'No such state type as {state_type}') # pragma: no cover
            return # pragma: no cover

        self._state[state_type][key] = val
        self.save_state()

    def save_state(self):
        try:
            # update timestamp
            if 'pytest' not in sys.modules: # pragma: no cover
                self._state['timestamp'] = time.time()
                state_fn = os.path.join(prefs.get_pref('VENT_DIR'), prefs.get_pref('GUI_STATE_FN'))
                with open(state_fn, 'w') as state_f:
                    json.dump(self._state, state_f,
                              indent=4, separators=(',', ': '))

        except Exception as e: # pragma: no cover
            self.logger.warning(f'State could not be saved, state:\n    {self._state}\n\nerror message:\n    {e}')

    def load_state(self, state: typing.Union[str, dict]): # pragma: no cover
        """

        Args:
            state (str, dict): either a pathname to a state file or an already-loaded state dictionary

        """

        if isinstance(state, str):
            if not os.path.exists(state):
                self.logger.exception(f'Attempted to load state from file, but none found: {state}')

            with open(state, 'r') as state_f:
                state = json.load(state_f)

        self._state = state

        for control_name, control_value in self._state['controls'].items():
            self.set_value(control_value, control_name)

    @property
    def controls_set(self):
        """
        Check if all controls are set

        .. note::

            Note that even when RR or INSPt are autocalculated, they are still set in their control objects, so
            this check is the same regardless of what is set to autocalculate
        """
        controls2set = [
            ValueName.PIP,
            ValueName.PIP_TIME,
            ValueName.BREATHS_PER_MINUTE,
            ValueName.INSPIRATION_TIME_SEC
        ]

        if all([self.controls[c.name].is_set for c in controls2set]):
            return True
        else:
            return False

    def set_pressure_units(self, units):
        if units not in ('cmH2O', 'hPa'):
            self.logger.exception(f'Couldnt set pressure units {units}')
            return

        self.controls[ValueName.PIP.name].set_units(units)
        self.controls[ValueName.PEEP.name].set_units(units)
        # self.pressure_waveform.set_units(units)
        self.monitor[ValueName.PRESSURE.name].set_units(units)
        self.plots[ValueName.PRESSURE.name].set_units(units)

    def set_breath_detection(self, breath_detection: bool):
        """
        Connected to :attr:`~Control_Panel.breath_detection_button` - toggles autonomous breath detection in the controller

        Args:
            breath_detection (bool): Whether the controller detects autonomous breaths and resets the breath cycle accordingly
        """
        self.coordinator.set_breath_detection(breath_detection)

def launch_gui(coordinator, set_defaults=False): # pragma: no cover - identical thing in tests but we need a lil flavor

    # just for testing, should be run from main
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(styles.DARK_THEME)
    app = styles.set_dark_palette(app)
    gui = Vent_Gui(coordinator, set_defaults)
    gui.show()

    return app, gui