import time
from collections import deque
import pdb
import typing

import numpy as np
from PySide2 import QtCore, QtWidgets, QtGui
import PySide2 # import so pyqtgraph recognizes as what we're using
import pyqtgraph as pg
# pg.setConfigOptions(antialias=True)




from pvp.gui import styles
from pvp.gui import mono_font
from pvp.gui import get_gui_instance
from pvp.common import unit_conversion
from pvp.common.message import SensorValues, ControlSetting
from pvp.common.values import ValueName, Value
from pvp.common.loggers import init_logger
from pvp.alarm import AlarmSeverity

PLOT_TIMER = None
"""
A :class:`~PySide2.QtCore.QTimer` that updates :class:`.TimedPlotCurveItem`s
"""

PLOT_FREQ = 5
"""
Update frequency of :class:`.Plot` s in Hz
"""

# TODO: add NamedLine back in order to label limit lines in plots with ValueNames

# class NamedLine(pg.InfiniteLine):
#     value_changed = QtCore.Signal(tuple)
#
#     def __init__(self, name: ValueName, *args, **kwargs):
#         super(NamedLine, self).__init__(*args, **kwargs)
#         self.name = name
#         self.sigPositionChanged.connect(self._value_changed)
#
#         self.setHoverPen(color=styles.SUBWAY_COLORS['lime'],
#                          width=self.pen.width())
#
#     def _value_changed(self):
#         self.value_changed.emit((self.name, self.value()))
#
#     def setSpan(self, mn, mx):
#         if self.span != (mn, mx):
#             self.span = (mn, mx)
#             self._invalidateCache()
#             self.update()


class Plot(pg.PlotWidget):

    limits_changed = QtCore.Signal(tuple)

    def __init__(self, name, buffer_size = 4092,
                 plot_duration = 10,
                 abs_range = None,
                 plot_limits: tuple = None,
                 color=None,
                 units='',
                 **kwargs):
        """

        Args:
            name:
            buffer_size:
            plot_duration:
            abs_range:
            plot_limits (tuple): tuple of (ValueName)s for which to make pairs of min and max range lines
            color:
            units:
            **kwargs:
        """
        #super(Plot, self).__init__(axisItems={'bottom':TimeAxis(orientation='bottom')})
        # construct title html string
        titlestr = "{title_text} ({units})".format(
                                                   title_text=name,
                                                   units =units)




        super(Plot, self).__init__(background=styles.BOX_BACKGROUND,
                                   title=titlestr)

        self.getPlotItem().titleLabel.item.setHtml(
            f"<span style='{styles.PLOT_TITLE_STYLE}'>{titlestr}</span>"
        )
        self.getPlotItem().titleLabel.setAttr('justify', 'left')

        self.name = name

        # pdb.set_trace()

        # self.setViewportMargins(0,0,styles.BOX_MARGINS,0)
        self.timestamps = deque(maxlen=buffer_size)
        self.history = deque(maxlen=buffer_size)
        self.cycles = deque(maxlen=buffer_size)
        # TODO: Make @property to update buffer_size, preserving history
        self.plot_duration = plot_duration

        self.units = units

        self._convert_in = None
        self._convert_out = None


        self._start_time = time.time()
        self._last_time = time.time()
        self._last_relative_time = 0

        self.abs_range = None
        if abs_range:
            self.abs_range = abs_range
            #self.setYRange(self.abs_range[0], self.abs_range[1])

        #self.enableAutoRange(y=True)

        self._plot_limits = {}
        if plot_limits:
            for value in plot_limits:
                self._plot_limits[value] = (
                    pg.InfiniteLine(movable=False, angle=0, pos=0, pen=styles.SUBWAY_COLORS['red'],
                                    label=f'{value.name}:{{value:0.2f}}',
                                    labelOpts={
                                        'color': styles.SUBWAY_COLORS['red'],
                                        'position': 0.75
                                    }),
                    pg.InfiniteLine(movable=False, angle=0, pos=0, pen=styles.SUBWAY_COLORS['red'],
                                    label=f'{value.name}:{{value:0.2f}}',
                                    labelOpts={
                                        'color': styles.SUBWAY_COLORS['red'],
                                        'position': 0.9
                                    })
                )
                # self.min_safe.sigPositionChanged.connect(self._safe_limits_changed)
                # self.max_safe.sigPositionChanged.connect(self._safe_limits_changed)
                self.addItem(self._plot_limits[value][0])
                self.addItem(self._plot_limits[value][1])


        self.setXRange(0, plot_duration)

        # split plot curve into two so that the endpoint doesn't get connected to the start point
        self.early_curve = self.plot(width=3)
        self.late_curve = self.plot(width=3)
        self.time_marker = pg.InfiniteLine(movable=False, angle=90, pos=0)
        self.time_marker.setPen(color="#FFFFFF", width=1)
        self.addItem(self.time_marker)





        if color:
            self.early_curve.setPen(color=color, width=3)
            self.late_curve.setPen(color=color, width=3)


    def set_duration(self, dur):
        self.plot_duration = int(round(dur))
        self.setXRange(0, self.plot_duration)


    def update_value(self, new_value: tuple):
        """
        new_value (tuple): (timestamp from time.time(), breath_cycle, value)
        """
        try:
            this_time = time.time()
            #time_diff = this_time-self._last_time
            # limits = self.getPlotItem().viewRange()
            current_relative_time = (this_time-self._start_time) % self.plot_duration
            # self.time_marker.setData([current_relative_time, current_relative_time],
            #                          [limits[1][0], limits[1][1]])
            self.time_marker.setValue(current_relative_time)

            self.timestamps.append(new_value[0])
            self.cycles.append(new_value[1])
            self.history.append(new_value[2])

            # filter values based on timestamps
            ts_array = np.array(self.timestamps)
            end_ind = len(self.history)
            start_ind = np.where(ts_array > (this_time - self.plot_duration))[0][0]

            # subtract start time and take modulus of duration to get wrapped timestamps
            plot_timestamps = np.mod(ts_array[start_ind:end_ind]-self._start_time, self.plot_duration)
            plot_values = np.array([self.history[i] for i in range(start_ind, end_ind)])
            if self._convert_in:
                plot_values = self._convert_in(plot_values)

            # find the point where the time resets
            try:
                reset_ind = np.where(np.diff(plot_timestamps)<0)[0][0]

                # plot early and late
                self.early_curve.setData(plot_timestamps[0:reset_ind+1],plot_values[0:reset_ind+1] )
                self.late_curve.setData(plot_timestamps[reset_ind+1:], plot_values[reset_ind+1:])

            except IndexError:
                self.early_curve.setData(plot_timestamps, plot_values)
                self.late_curve.clear()
        except:
            # FIXME: Log this lol
            print('error plotting value: {}, timestamp: {}'.format(new_value[1], new_value[0]))

        #self._last_time = this_time

    def _safe_limits_changed(self, val):
        # ignore input val, just emit the current value of the lines
        self.limits_changed.emit((self.min_safe.value(),
                                       self.max_safe.value()))

    # @QtCore.Slot(tuple)
    def set_safe_limits(self, limits: ControlSetting):
        if self._plot_limits is None:
            return

        if limits.name in self._plot_limits.keys():

            if limits.min_value:
                if self._convert_out:
                    self._plot_limits[limits.name][0].setPos(self._convert_out(limits.min_value))
                else:
                    self._plot_limits[limits.name][0].setPos(limits.min_value)
            if limits.max_value:
                if self._convert_out:
                    self._plot_limits[limits.name][1].setPos(self._convert_out(limits.max_value))
                else:
                    self._plot_limits[limits.name][1].setPos(limits.max_value)


    def reset_start_time(self):
        self._start_time = time.time()
        self._last_time = time.time()
        self._last_relative_time = 0

    def set_units(self, units):
        if self.name in ('Pressure',):
            if units == 'cmH2O':
                self.decimals = 1
                self.units = units
                self._convert_in = None
                self._convert_out = None

                for range_pairs in self._plot_limits.values():
                    for a_line in range_pairs:
                        a_line.setPos(unit_conversion.hPa_to_cmH2O(a_line.getPos()[1]))

            elif units == 'hPa':
                self.decimals = 0
                self.units = units
                self._convert_in = unit_conversion.cmH2O_to_hPa
                self._convert_out = unit_conversion.hPa_to_cmH2O

                for range_pairs in self._plot_limits.values():
                    for a_line in range_pairs:
                        a_line.setPos(unit_conversion.cmH2O_to_hPa(a_line.getPos()[1]))

            titlestr = "{title_text} ({units})".format(
                title_text=self.name,
                units=self.units)
            self.getPlotItem().titleLabel.item.setHtml(
                f"<span style='{styles.PLOT_TITLE_STYLE}'>{titlestr}</span>"
            )

class Plot_Container(QtWidgets.QGroupBox):

    def __init__(self, plot_descriptors: typing.Dict[ValueName, Value],
                 *args, **kwargs):

        super(Plot_Container, self).__init__('Monitored Waveforms', *args, **kwargs)

        self.plot_descriptors = plot_descriptors
        self.plots = {}
        self.visible = list(plot_descriptors.keys())

        self.setStyleSheet(styles.PLOT_BOX)
        self.setContentsMargins(0,0,0,0)

        self.logger = init_logger(__name__)

        self.init_ui()
        self.set_duration(10)

    def init_ui(self):
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        self.layout = QtWidgets.QVBoxLayout()

        # initialize the buttons first!!!
        self.button_layout = QtWidgets.QHBoxLayout()

        # plot selection buttons
        # self.selection_button_group = QtWidgets.QButtonGroup()
        self.selection_buttons = {}
        for plot_key, plot_params in self.plot_descriptors.items():
            new_button = QtWidgets.QPushButton(plot_params.name)
            new_button.setCheckable(True)
            new_button.setChecked(True)
            new_button.setObjectName(plot_key.name)
            new_button.setStyleSheet(styles.TOGGLE_BUTTON)
            new_button.toggled.connect(self.toggle_plot)
            self.button_layout.addWidget(new_button, 2)
            self.selection_buttons[plot_key.name] = new_button

        self.button_layout.addStretch(5)

        # time box and slider
        self.button_layout.addWidget(QtWidgets.QLabel('Plot Zoom'))

        self.time_box = QtWidgets.QLineEdit()
        self.time_box.setValidator(QtGui.QIntValidator())
        self.time_box.textEdited.connect(self.set_duration)
        self.button_layout.addWidget(self.time_box, 1)


        self.slider = QtWidgets.QSlider()
        self.slider.setMinimum(5)
        self.slider.setMaximum(60)
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.slider.valueChanged.connect(self.set_duration)
        self.button_layout.addWidget(self.slider, 2)



        self.layout.addLayout(self.button_layout)




        for i, (plot_key, plot_params) in enumerate(self.plot_descriptors.items()):
            if i % 2 == 0:
                plot_color = styles.SUBWAY_COLORS['orange']
            else:
                plot_color = styles.SUBWAY_COLORS['ltblue']
            self.plots[plot_key.name] = Plot(color=plot_color, **plot_params.to_dict())
            self.layout.addWidget(self.plots[plot_key.name], 1)

        self.setLayout(self.layout)

    def update_value(self, vals: SensorValues):
        for plot_key, plot in self.plots.items():
            if hasattr(vals, plot_key):
                try:
                    plot.update_value((time.time(), getattr(vals, 'breath_count'), getattr(vals, plot_key)))
                except Exception as e:
                    self.logger.exception(f'Couldnt update plot with {plot_key}, got error {e}')

    def toggle_plot(self, state: bool):

        sender_name = self.sender().objectName()
        if sender_name in self.plots.keys():
            if state:
                self.plots[sender_name].setVisible(True)
            else:
                self.plots[sender_name].setVisible(False)

    def set_safe_limits(self, control: ControlSetting):
        for plot in self.plots.values():
            plot.set_safe_limits(control)

    def set_duration(self, duration: float):
        if isinstance(duration, str):
            duration = float(duration)

        self.time_box.setText(str(duration))
        self.slider.setValue(duration)

        for plot in self.plots.values():
            plot.set_duration(duration)

    def reset_start_time(self):
        for plot in self.plots.values():
            plot.reset_start_time()







