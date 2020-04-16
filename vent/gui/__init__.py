
#########################
# Imports

# python standard libraries
from collections import OrderedDict as odict
import sys
import os
import time
import pdb
# add to path
PACKAGE_PARENT = '../..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
#pdb.set_trace()
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))


# other required libraries
import numpy as np

# Using PySide (Qt) to build GUI
from PySide2 import QtCore, QtGui, QtWidgets

# import whole module so pyqtgraph recognizes we're using it
# using pyqtgraph for data visualization

# import styles
from vent.gui import widgets
from vent.gui import defaults
from vent.gui import styles


##########################
# GUI Class

try:
    mono_font = QtGui.QFont('Fira Code')
except:
    mono_font = QtGui.QFont()
    mono_font.setStyleHint(QtGui.QFont.Monospace)


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
        * O2
        * Temperature
        * Humidity
        - (VTE) End-Tidal volume: the volume of air entering the lung, derived from flow through t_exp
        - PIP: peak inspiratory pressure, set by user in software
        - Mean plateau pressure: derived from pressure sensor during inspiration cycle hold (no flow)
        - PEEP: positive end-expiratory pressure, set by manual valve
        * fTotal (total respiratory frequency) - breaths delivered by vent & patients natural breaths


    **Alarms**
        - Oxygen out of range
        - High pressure (tube/airway occlusion)
        - Low-pressure (disconnect)
        - Temperature out of range
        - Low voltage alarm (if using battery power)
        - Tidal volume (expiratory) out of range


    Graphs:
        * Flow
        * Pressure

    """

    DISPLAY = defaults.DISPLAY

    CONTROL = defaults.CONTROL

    PLOTS = defaults.PLOTS

    display_width = 2
    plot_width = 2
    control_width = 2
    total_width = display_width+plot_width+control_width

    status_height = 1
    main_height = 5
    total_height = status_height+main_height

    def __init__(self, update_period = 0.1):
        super(Vent_Gui, self).__init__()

        self.display_values = {}
        self.plots = {}
        self.controls = {}

        self.update_period = update_period

        self.init_ui()
        self.start_time = time.time()

        self.test()


    def test(self):

        ox = ((np.sin(time.time()/10)+1)*5)+80
        self.display_values['oxygen'].update_value(ox)

        temp = ((np.sin(time.time()/20)+1)*2.5)+22
        self.display_values['temperature'].update_value(temp)

        humid = ((np.sin(time.time()/50)+1)*5)+50
        self.display_values['humidity'].update_value(humid)

        press = (np.sin(time.time())+1)*25
        self.display_values['vte'].update_value(press)
        self.plots['pressure'].update_value((time.time(), press))
        # for num, widget in enumerate(self.display_values.values()):
        #     yval = (np.sin(time.time()+num) + 1) * 50
        #     widget.update_value(yval)
        self.plots['flow'].update_value((time.time(),(np.sin(time.time()) + 1) * 50))


        # if (time.time()-self.start_time) < 60:
        QtCore.QTimer.singleShot(0.02, self.test)


    def update_value(self, value_name, new_value):
            if value_name in self.display_values.keys():
                self.display_values[value_name].update_value(new_value)
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

        # layout - three columns
        # left: readout values
        # left: readout values
        # center: plotted values
        # right: controls & limits
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

        for display_key, display_params in self.DISPLAY.items():
            self.display_values[display_key] = widgets.Display_Value(update_period = self.update_period, **display_params)
            self.display_layout.addWidget(self.display_values[display_key])
            self.display_layout.addWidget(widgets.QHLine())
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
        self.display_values['vte'].limits_changed.connect(self.plots['pressure'].set_safe_limits)
        self.plots['pressure'].limits_changed.connect(self.display_values['vte'].update_limits)


        ####################
        # Controls

        self.controls_layout = QtWidgets.QVBoxLayout()
        for control_name, control_params in self.CONTROL.items():
            self.controls[control_name] = widgets.Control(**control_params)
            self.controls_layout.addWidget(self.controls[control_name])
            self.controls_layout.addWidget(widgets.QHLine())

        self.controls_layout.addStretch()

        self.main_layout.addLayout(self.controls_layout, 1)

        self.layout.addLayout(self.main_layout, self.main_height)
        self.show()

    def set_plot_duration(self, dur):
        dur = int(self.sender().objectName())

        for plot in self.plots.values():
            plot.set_duration(dur)


if __name__ == "__main__":
    # just for testing, should be run from main
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(styles.GLOBAL)
    gui = Vent_Gui()
    sys.exit(app.exec_())