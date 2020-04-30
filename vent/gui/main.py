import time
import sys
import threading
import pdb

from PySide2 import QtWidgets, QtCore, QtGui

from vent import values
from vent.common.message import ControlSetting, ControlSettingName
from vent.gui import widgets, set_gui_instance, get_gui_instance, styles
from vent.controller.control_module import get_control_module


class Vent_Gui(QtWidgets.QMainWindow):
    """

    Controls:
        - PIP: peak inhalation pressure (~20 cm H2O)
        - T_insp: inspiratory time to PEEP (~0.5 sec)
        - I/E: inspiratory to expiratory time ratio
        - bpm: breaths per minute (15 bpm -> 1/15 sec cycle time)
        - PIP_time: Target time for PIP. While lungs expand, dP/dt should be PIP/PIP_time
        - flow_insp: nominal flow rate during inspiration

    **Set by hardware**
        - FiO2: fraction of inspired oxygen, set by blender
        - max_flow: manual valve at output of blender
        - PEEP: positive end-expiratory pressure, set by manual valve

    **Derived parameters**
        - cycle_time: 1/bpm
        - t_insp: inspiratory time, controlled by cycle_time and I/E
        - t_exp: expiratory time, controlled by cycle_time and I/E

    **Monitored variables**
        - O2
        - Temperature
        - Humidity
        - (VTE) End-Tidal volume: the volume of air entering the lung, derived from flow through t_exp
        - PIP: peak inspiratory pressure, set by user in software
        - Mean plateau pressure: derived from pressure sensor during inspiration cycle hold (no flow)
        - PEEP: positive end-expiratory pressure, set by manual valve
        - fTotal (total respiratory frequency) - breaths delivered by vent & patients natural breaths

    **Alarms**
        - Oxygen out of range
        - High pressure (tube/airway occlusion)
        - Low-pressure (disconnect)
        - Temperature out of range
        - Low voltage alarm (if using battery power)
        - Tidal volume (expiratory) out of range

    Graphs:
        - Flow
        - Pressure

    """

    gui_closing = QtCore.Signal()
    """
    :class:`PySide2.QtCore.Signal` emitted when the GUI is closing.
    """

    MONITOR = values.SENSOR
    """
    see :data:`.gui.defaults.SENSOR`
    """

    CONTROL = values.CONTROL
    """
    see :data:`.gui.defaults.CONTROL`
    """

    PLOTS = values.PLOTS
    """
    see :data:`.gui.defaults.PLOTS`
    """

    display_width = 2
    plot_width = 4
    control_width = 2
    total_width = display_width+plot_width+control_width
    """
    computed from ``display_width+plot_width+control_width``
    """

    status_height = 1
    main_height = 5
    total_height = status_height+main_height
    """
    computed from ``status_height+main_height``
    """

    def __init__(self, coordinator, update_period = 0.1, test=False):
        """

        Attributes:
            monitor (dict): Dictionary mapping :data:`.default.SENSOR` keys to :class:`.widgets.Monitor_Value` objects
            plots (dict): Dictionary mapping :data:`.default.PLOT` keys to :class:`.widgets.Plot` objects
            controls (dict): Dictionary mapping :data:`.default.CONTROL` keys to :class:`.widgets.Control` objects
            start_time (float): Start time as returned by :func:`time.time`
            update_period (float): The global delay between redraws of the GUI (seconds)



        Arguments:
            update_period (float): The global delay between redraws of the GUI (seconds)
            test (bool): Whether the monitored values and plots should be fed sine waves for visual testing.


        """
        if get_gui_instance() is not None:
            raise Exception('Instance of gui already running!')
        else:
            set_gui_instance(self)

        super(Vent_Gui, self).__init__()

        self.monitor = {}
        self.plots = {}
        self.controls = {}

        self.control_settings = {}

        self.draw_lock = threading.Lock()

        self.coordinator = coordinator
        self.control_module = self.coordinator.control_module

        # start QTimer to update values
        self.timer = QtCore.QTimer()
        #self.timer.timeout.connect(self.update_gui)
        # stop QTimer when program closing
        self.gui_closing.connect(self.timer.stop)
        # start the timer

        # set update period (after timer is created!!)
        self._update_period = None
        self.update_period = update_period

        # initialize controls to starting values
        self.init_controls()


        self.init_ui()
        self.start_time = time.time()

        self.update_gui()

        #self.timer.start(self.update_period*1000)

    @property
    def update_period(self):
        return self._update_period

    @update_period.setter
    def update_period(self, update_period):
        assert(isinstance(update_period, float) or isinstance(update_period, int))

        if update_period != self._update_period:
            # if the timer is active, stop it and restart with new period
            if self.timer.isActive():
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
        set value in the test thread
        """
        # get sender ID
        if value_name is None:
            value_name = self.sender().objectName()


        control_object = ControlSetting(name=getattr(ControlSettingName, value_name),
                                         value=new_value,
                                         min_value = self.CONTROL[value_name]['safe_range'][0],
                                         max_value = self.CONTROL[value_name]['safe_range'][1],
                                         timestamp = time.time())
        self.coordinator.set_control(control_object)


    def update_gui(self):
        try:
            vals = self.coordinator.get_sensors()

            for plot_key, plot_obj in self.plots.items():
                if hasattr(vals, plot_key):
                    plot_obj.update_value((time.time(), getattr(vals, plot_key)))

            for monitor_key, monitor_obj in self.monitor.items():
                if hasattr(vals, monitor_key):
                    monitor_obj.update_value(getattr(vals, monitor_key))

        except TypeError:
            # FIXME: why?
            pass




        #
        finally:
            QtCore.QTimer.singleShot(self.update_period*1000, self.update_gui)




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

        #########
        # display values
        monitor_box = QtWidgets.QGroupBox("Sensor Monitor")
        monitor_layout = QtWidgets.QHBoxLayout()
        monitor_layout.setContentsMargins(0, 0, 0, 0)
        monitor_box.setLayout(monitor_layout)


        self.display_layout = QtWidgets.QVBoxLayout()
        self.display_layout.setContentsMargins(0,0,0,0)

        for display_key, display_params in self.MONITOR.items():
            self.monitor[display_key] = widgets.Monitor_Value(display_params, update_period = self.update_period)
            self.display_layout.addWidget(self.monitor[display_key])
            self.display_layout.addWidget(widgets.components.QHLine())

        monitor_layout.addLayout(self.display_layout, self.display_width)
        #self.main_layout.addWidget(display_box, self.display_width)
        #self.main_layout.addLayout(self.display_layout, self.display_width)
        #pdb.set_trace()
        ###########
        # plots
        self.plot_layout = QtWidgets.QVBoxLayout()
        self.plot_layout.setContentsMargins(0,0,0,0)

        # button to set plot history
        button_box = QtWidgets.QGroupBox("Plot History")
        #button_group = QtWidgets.QButtonGroup()
        #button_group.exclusive()
        times = (("5s", 5),
                 ("10s", 10),
                 ("30s", 30),
                 ("1m", 60),
                 ("5m", 60*5),
                 ("15m", 60*15),
                 ("60m", 60*60))

        self.time_buttons = {}
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        for a_time in times:
            self.time_buttons[a_time[0]] = QtWidgets.QRadioButton(a_time[0])
            #self.time_buttons[a_time[0]].setCheckable(True)
            self.time_buttons[a_time[0]].setObjectName(str(a_time[1]))
            self.time_buttons[a_time[0]].clicked.connect(self.set_plot_duration)
            button_layout.addWidget(self.time_buttons[a_time[0]])
            #button_group.addButton(self.time_buttons[a_time[0]])


        button_box.setLayout(button_layout)
        self.plot_layout.addWidget(button_box)
        #pdb.set_trace()

        for plot_key, plot_params in self.PLOTS.items():
            self.plots[plot_key] = widgets.Plot(**plot_params)
            self.plot_layout.addWidget(self.plots[plot_key])

        #self.main_layout.addLayout(self.plot_layout,5)
        monitor_layout.addLayout(self.plot_layout, self.plot_width)

        self.main_layout.addWidget(monitor_box, self.plot_width+self.display_width)


        # connect displays to plots
        # FIXME: Link in gui.defaults
        self.monitor['vte'].limits_changed.connect(self.plots['pressure'].set_safe_limits)
        self.plots['pressure'].limits_changed.connect(self.monitor['vte'].update_limits)


        ####################
        # Controls
        controls_box = QtWidgets.QGroupBox("Ventilator Controls")
        controls_box.setStyleSheet(styles.CONTROL_BOX)
        controls_box.setContentsMargins(0,0,0,0)



        self.controls_layout = QtWidgets.QVBoxLayout()
        self.controls_layout.setContentsMargins(0,0,0,0)
        for control_name, control_params in self.CONTROL.items():
            self.controls[control_name] = widgets.Control(control_params)
            self.controls[control_name].setObjectName(control_name)
            self.controls[control_name].value_changed.connect(self.set_value)
            self.controls_layout.addWidget(self.controls[control_name])
            self.controls_layout.addWidget(widgets.components.QHLine())

        self.controls_layout.addStretch()
        controls_box.setLayout(self.controls_layout)

        self.main_layout.addWidget(controls_box, self.control_width)

        self.layout.addLayout(self.main_layout, self.main_height)


        ######################
        # set the default view as 30s
        self.time_buttons[times[2][0]].click()

        # TODO: Set more defaults


        self.show()

    def set_plot_duration(self, dur):
        dur = int(self.sender().objectName())

        for plot in self.plots.values():
            plot.set_duration(dur)

    def closeEvent(self, event):
        """
        Emit :attr:`.gui_closing` and close!
        """
        globals()['_GUI_INSTANCE'] = None
        self.gui_closing.emit()

        if self.coordinator:
            try:
                self.coordinator.stop()
            except:
                raise Warning('had a thread object, but the thread object couldnt be stopped')

        event.accept()

def launch_gui(coordinator):

    # just for testing, should be run from main
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(styles.GLOBAL)
    gui = Vent_Gui(coordinator)

    return app, gui