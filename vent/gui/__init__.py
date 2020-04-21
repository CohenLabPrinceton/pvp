
#########################
# Imports

# python standard libraries
import sys
import os
import time
import argparse
import pdb
# add to path
# FIXME: Do packaging
# PACKAGE_PARENT = '../..'
# SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
# #pdb.set_trace()
# sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))


# other required libraries
import numpy as np

# Using PySide (Qt) to build GUI
from PySide2 import QtCore, QtGui, QtWidgets


_GUI_INSTANCE = None

def get_instance():
    return globals()['_GUI_INSTANCE']

###########
# Load a monospace font for displaying numbers
# Want to load an explicit font because computing the hint to find the default mono font is expensive

_MONO_FONT = None
def mono_font():
    """
    module function to return a :class:`PySide2.QtGui.QFont` to use as the mono font.

    use this instead of just making because :class:`PySide2.QtGui.QFontDatabase` can't be instantiated before the
    :class:`PySide2.QtWidgets.QApplication` is instantiated, so we load the font after the app
    """
    return globals()['_MONO_FONT']

def load_mono():
    """
    Load the monospaced font and set the module-global :data:`_MONO_FONT` object.

    .. note::

        Must be called after :class:`PySide2.QtWidgets.QApplication` is instantiated!

    """
    try:
        # first try to load fira code for monospace font
        external_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'external')
        font_db = QtGui.QFontDatabase()
        font_db.addApplicationFont(os.path.join(external_dir, 'FiraCode-Regular.otf'))
        font_db.addApplicationFont(os.path.join(external_dir, 'FiraCode-Bold.otf'))
        mono_font = QtGui.QFont('Fira Code')
    except:
        # if that fails, try to load liberation mono
        # TODO: Log this
        try:
            mono_font = QtGui.QFont('Liberation Mono')

        except:
            # otherwise get the system default mono font
            mono_font = QtGui.QFont()
            mono_font.setStyleHint(QtGui.QFont.Monospace)

    globals()['_MONO_FONT'] = mono_font


# import styles
from vent.gui import widgets
from vent import values
from vent.gui import styles

# for testing
from vent.coordinator.control_module import get_control_module, ControllerThread   # this is the file to change
from vent.coordinator.common.message import SensorValues, ControlSettings, Alarm, ControlSettingName



##########################
# GUI Class



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

    MONITOR = values.MONITOR
    """
    see :data:`.gui.defaults.MONITOR`
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
    plot_width = 2
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

    def __init__(self, update_period = 0.1, test=False):
        """

        Attributes:
            monitor (dict): Dictionary mapping :data:`.default.MONITOR` keys to :class:`.widgets.Monitor_Value` objects
            plots (dict): Dictionary mapping :data:`.default.PLOT` keys to :class:`.widgets.Plot` objects
            controls (dict): Dictionary mapping :data:`.default.CONTROL` keys to :class:`.widgets.Control` objects
            start_time (float): Start time as returned by :func:`time.time`
            update_period (float): The global delay between redraws of the GUI (seconds)



        Arguments:
            update_period (float): The global delay between redraws of the GUI (seconds)
            test (bool): Whether the monitored values and plots should be fed sine waves for visual testing.


        """
        if globals()['_GUI_INSTANCE'] is not None:
            raise Exception('Instance of gui already running!')
        else:
            globals()['_GUI_INSTANCE'] = self

        super(Vent_Gui, self).__init__()

        # first off, load the monospaced font
        load_mono()

        self.monitor = {}
        self.plots = {}
        self.controls = {}

        self.update_period = update_period

        self.init_ui()
        self.start_time = time.time()

        self.thread = None

        if test:
            self.test()

    def test(self):
        """
        Use a controller simulator returned by :func:`~vent.coordinator.control_module.get_control_module` to test the GUI

        Following the example in /sandbox/testPIDControllerClass

        """

        c1 = ControlSettings(name=ControlSettingName.PIP,
                             value=values.CONTROL['PIP']['value'],
                             min_value=values.CONTROL['PIP']['abs_range'][0],
                             max_value=values.CONTROL['PIP']['abs_range'][1],
                             timestamp=time.time())

        c2 = ControlSettings(
                            name=ControlSettingName.PIP_TIME,
                            value=values.CONTROL['PIP_TIME']['value'],
                            min_value=values.CONTROL['PIP_TIME']['abs_range'][0],
                            max_value=values.CONTROL['PIP_TIME']['abs_range'][1],
                            timestamp=time.time())

        c3 = ControlSettings(name=ControlSettingName.PEEP,
                            value=values.CONTROL['PEEP']['value'],
                            min_value=values.CONTROL['PEEP']['abs_range'][0],
                            max_value=values.CONTROL['PEEP']['abs_range'][1],
                            timestamp=time.time())

        c4 = ControlSettings(name=ControlSettingName.BREATHS_PER_MINUTE,
                            value=values.CONTROL['BREATHS_PER_MINUTE']['value'],
                            min_value=values.CONTROL['BREATHS_PER_MINUTE']['abs_range'][0],
                            max_value=values.CONTROL['BREATHS_PER_MINUTE']['abs_range'][1],
                            timestamp=time.time())

        c5 = ControlSettings(name=ControlSettingName.INSPIRATION_TIME_SEC,
                            value=values.CONTROL['INSPIRATION_TIME_SEC']['value'],
                            min_value=values.CONTROL['INSPIRATION_TIME_SEC']['abs_range'][0],
                            max_value=values.CONTROL['INSPIRATION_TIME_SEC']['abs_range'][1],
                            timestamp=time.time())

        runtime = 300  # run this for 30 seconds
        self.thread = ControllerThread(1, "Controller-1", runtime / 0.01)  # 5sec in 10ms steps

        for command in [c1, c2, c3, c4, c5]:
            self.thread.set_controls(command)

        self.thread.start()

        self.read_sensors()

    def set_value(self, new_value):
        """
        set value in the test thread
        """
        # get sender ID
        value_name = self.sender().objectName()
        control_object = ControlSettings(name=getattr(ControlSettingName, value_name),
                                         value=new_value,
                                         min_value = self.CONTROL[value_name]['safe_range'][0],
                                         max_value = self.CONTROL[value_name]['safe_range'][1],
                                         timestamp = time.time())
        self.thread.set_controls(control_object)

    def read_sensors(self):

        vals = self.thread.get_sensor_values()
        #pdb.set_trace()

        # for monitor_key, monitor_obj in self.monitor.items():
        #     if hasattr(vals, monitor_key):
        #         monitor_obj.update_value(getattr(vals, monitor_key))

        for plot_key, plot_obj in self.plots.items():
            if hasattr(vals, plot_key):
                plot_obj.update_value((time.time(), getattr(vals, plot_key)))


        QtCore.QTimer.singleShot(1, self.read_sensors)



    def test_old(self):
        """
        Testing method that uses a bunch of hardcoded variable names and
        manually generated values instead of the simulator.
        """

        ox = ((np.sin(time.time()/10)+1)*5)+80
        self.monitor['oxygen'].update_value(ox)

        temp = ((np.sin(time.time()/20)+1)*2.5)+22
        self.monitor['temperature'].update_value(temp)

        humid = ((np.sin(time.time()/50)+1)*5)+50
        self.monitor['humidity'].update_value(humid)

        press = (np.sin(time.time())+1)*25
        self.monitor['vte'].update_value(press)
        self.plots['pressure'].update_value((time.time(), press))
        # for num, widget in enumerate(self.monitor.values()):
        #     yval = (np.sin(time.time()+num) + 1) * 50
        #     widget.update_value(yval)
        self.plots['flow'].update_value((time.time(),(np.sin(time.time()) + 1) * 50))


        # if (time.time()-self.start_time) < 60:
        QtCore.QTimer.singleShot(0.02, self.test)


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

        ##########
        # Status Bar
        self.status_bar = widgets.Status_Bar()
        self.layout.addWidget(self.status_bar, self.status_height)

        #########
        # display values
        self.display_layout = QtWidgets.QVBoxLayout()

        for display_key, display_params in self.MONITOR.items():
            self.monitor[display_key] = widgets.Monitor_Value(update_period = self.update_period, **display_params)
            self.display_layout.addWidget(self.monitor[display_key])
            self.display_layout.addWidget(widgets.components.QHLine())
        self.main_layout.addLayout(self.display_layout, self.display_width)

        ###########
        # plots
        self.plot_layout = QtWidgets.QVBoxLayout()

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


        for plot_key, plot_params in self.PLOTS.items():
            self.plots[plot_key] = widgets.Plot(**plot_params)
            self.plot_layout.addWidget(self.plots[plot_key])

        self.main_layout.addLayout(self.plot_layout,5)


        # connect displays to plots
        # FIXME: Link in gui.defaults
        self.monitor['vte'].limits_changed.connect(self.plots['pressure'].set_safe_limits)
        self.plots['pressure'].limits_changed.connect(self.monitor['vte'].update_limits)


        ####################
        # Controls

        self.controls_layout = QtWidgets.QVBoxLayout()
        for control_name, control_params in self.CONTROL.items():
            self.controls[control_name] = widgets.Control(**control_params)
            self.controls[control_name].setObjectName(control_name)
            self.controls[control_name].value_changed.connect(self.set_value)
            self.controls_layout.addWidget(self.controls[control_name])
            self.controls_layout.addWidget(widgets.components.QHLine())

        self.controls_layout.addStretch()

        self.main_layout.addLayout(self.controls_layout, 1)

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

        if self.thread:
            try:
                self.thread.stop()
            except:
                raise Warning('had a thread object, but the thread object couldnt be stopped')

        event.accept()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch the Ventilator GUI")
    parser.add_argument('--test',
                        dest='test',
                        help="Run in test mode? (y=1/n=0, default=0)",
                        choices=('y','n'),
                        default=0)



    args = parser.parse_args()

    gui_test = False
    if args.test in (1, True, 'y'):
        gui_test = True

    # just for testing, should be run from main
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(styles.GLOBAL)
    gui = Vent_Gui(test=gui_test)
    sys.exit(app.exec_())