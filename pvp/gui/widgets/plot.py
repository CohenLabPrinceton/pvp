"""
Widgets to plot waveforms of sensor values

The :class:`.PVP_Gui` creates a :class:`.Plot_Container` that allows the user to select

* which plots (of those in :data:`.values.PLOT` ) are displayed
* the timescale (x range) of the displayed waveforms

Plots display alarm limits as red horizontal bars
"""

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


class Plot(pg.PlotWidget):
    """
    Waveform plot of single sensor value.

    Plots values continuously, wrapping at zero rather than shifting x axis.

    Args:
        name (str): String version of :class:`.ValueName` used to set title
        buffer_size (int): number of samples to store
        plot_duration (float): default x-axis range
        plot_limits (tuple): tuple of (ValueName)s for which to make pairs of min and max range lines
        color (None, str): color of lines
        units (str): Unit label to display along title
        **kwargs:

    Attributes:
        timestamps (:class:`collections.deque`): deque of timestamps
        history (:class:`collections.deque`): deque of sensor values
        cycles (:class:`collections.deque`): deque of breath cycles

    """

    limits_changed = QtCore.Signal(tuple)

    def __init__(self, name: str, buffer_size: int = 4092,
                 plot_duration: float = 10,
                 plot_limits: tuple = None,
                 color=None,
                 units='',
                 **kwargs):

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

        self.logger = init_logger(__name__)

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

        #self.enableAutoRange(y=True)

        # split plot curve into two so that the endpoint doesn't get connected to the start point
        self.early_curve = self.plot(width=3)
        self.late_curve = self.plot(width=3)

        self._plot_limits = {}
        if plot_limits:
            for value in plot_limits:
                self._plot_limits[value] = (
                    pg.InfiniteLine(movable=False, angle=0, pos=0, pen=styles.SUBWAY_COLORS['red'],
                                    label=f'{value.name}:{{value:0.1f}}',
                                    labelOpts={
                                        'color': styles.TEXT_COLOR,
                                        'fill': styles.SUBWAY_COLORS['red'],
                                        'position': 0.1
                                    }),
                    pg.InfiniteLine(movable=False, angle=0, pos=0, pen=styles.SUBWAY_COLORS['red'],
                                    label=f'{value.name}:{{value:0.1f}}',
                                    labelOpts={
                                        'color': styles.TEXT_COLOR,
                                        'fill': styles.SUBWAY_COLORS['red'],
                                        'position': 0.9
                                    })
                )
                # self.min_safe.sigPositionChanged.connect(self._safe_limits_changed)
                # self.max_safe.sigPositionChanged.connect(self._safe_limits_changed)
                self.addItem(self._plot_limits[value][0])
                self.addItem(self._plot_limits[value][1])

        # vline to indicate current time
        self.time_marker = pg.InfiniteLine(movable=False, angle=90, pos=0)
        self.time_marker.setPen(color="#FFFFFF", width=1)
        self.addItem(self.time_marker)

        self.setXRange(0, plot_duration)

        if color:
            self.early_curve.setPen(color=color, width=3)
            self.late_curve.setPen(color=color, width=3)


    def set_duration(self, dur: float):
        """
        Set duration, or span of x axis.

        Args:
            dur (float): span of x axis (in seconds)
        """
        self.plot_duration = int(round(dur))
        self.setXRange(0, self.plot_duration)


    def update_value(self, new_value: tuple):
        """
        Update with new sensor value

        Args:
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
        except Exception as e:  # pragma: no cover
            self.logger.exception('{}: error plotting value: {}, {}'.format(self.name, new_value[1], e))

    # @QtCore.Slot(tuple)
    def set_safe_limits(self, limits: ControlSetting):
        """
        Set the position of the max and min lines for a given value

        Args:
            limits ( :class:`.ControlSetting` ): Controlsetting that has either a ``min_value`` or ``max_value`` defined
        """
        if self._plot_limits is None: # pragma: no cover
            return

        if limits.name in self._plot_limits.keys():

            if limits.min_value:
                if self._convert_in:
                    self._plot_limits[limits.name][0].setPos(self._convert_in(limits.min_value))
                else:
                    self._plot_limits[limits.name][0].setPos(limits.min_value)
            if limits.max_value:
                if self._convert_in:
                    self._plot_limits[limits.name][1].setPos(self._convert_in(limits.max_value))
                else:
                    self._plot_limits[limits.name][1].setPos(limits.max_value)


    def reset_start_time(self):
        """
        Reset start time -- return the scrolling time bar to position 0
        """
        self._start_time = time.time()
        self._last_time = time.time()
        self._last_relative_time = 0

    def set_units(self, units):
        """
        Set displayed units

        Currently only implemented for Pressure, display either in cmH2O or hPa

        Args:
            units ('cmH2O', 'hPa'): unit to display pressure as
        """
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
    """
    Container for multiple :class;`.Plot` objects

    Allows user to show/hide different plots and adjust x-span (time zoom)

    .. note::

        Currently, the only unfortunately hardcoded parameter in the whole GUI is the instruction
        to initially hide FIO2, there should be an additional parameter in ``Value`` that says whether a plot should initialize as hidden or not

    .. todo::

        Currently, colors are set to alternate between orange and light blue on initialization, but they don't
        update when plots are shown/hidden, so the alternating can be lost and colors can look random depending on what's selcted.

    Args:
        plot_descriptors (typing.Dict[ValueName, Value]): dict of :class:`.Value` items to plot

    Attributes:
        plots (dict): Dict mapping :class:`.ValueName` s to :class:`.Plot` s
        slider (:class:`PySide2.QtWidgets.QSlider`): slider used to set x span

    """

    def __init__(self, plot_descriptors: typing.Dict[ValueName, Value],
                 *args, **kwargs):

        super(Plot_Container, self).__init__('Monitored Waveforms', *args, **kwargs)

        self.plot_descriptors = plot_descriptors
        self.plots = {}

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
            if plot_key == ValueName.FIO2:
                new_button.setChecked(False)

        self.button_layout.addStretch(2)

        # # select display mode
        # self.plot_mode_buttons = [
        #     QtWidgets.QPushButton('Waveform'),
        #     QtWidgets.QPushButton('Cycle')
        # ]
        #
        # self.plot_mode_button_group = QtWidgets.QButtonGroup()
        # self.plot_mode_button_group.setExclusive(True)
        # self.plot_mode_layout = QtWidgets.QHBoxLayout()
        #
        # for button in self.plot_mode_buttons:
        #     button.setObjectName(button.text())
        #     button.setCheckable(True)
        #     self.plot_mode_button_group.addButton(button)
        #     button.setStyleSheet(styles.TOGGLE_BUTTON)
        #     self.plot_mode_layout.addWidget(button)
        #
        # self.plot_mode_buttons[0].setChecked(True)
        # self.plot_mode_button_group.buttonClicked.connect(self.set_plot_mode)
        #
        # self.button_layout.addLayout(self.plot_mode_layout)

        # time box and slider

        self.time_box = QtWidgets.QLineEdit()
        self.time_box.setValidator(QtGui.QIntValidator())
        self.time_box.textEdited.connect(self.set_duration)
        self.button_layout.addWidget(self.time_box, 1)


        self.slider = QtWidgets.QSlider()
        self.slider.setMinimum(5)
        self.slider.setMaximum(60)
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        # self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
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
            if plot_key == ValueName.FIO2:
                self.plots[plot_key.name].setVisible(False)

        self.setLayout(self.layout)

    def update_value(self, vals: SensorValues):
        """
        Try to update all plots who have new sensorvalues

        Args:
            vals (:class:`.SensorValues`): Sensor Values to update plots with

        """

        for plot_key, plot in self.plots.items():
            if hasattr(vals, plot_key):
                try:
                    plot.update_value((time.time(), getattr(vals, 'breath_count'), getattr(vals, plot_key)))
                except Exception as e: # pragma: no cover
                    self.logger.exception(f'Couldnt update plot with {plot_key}, got error {e}')

    def toggle_plot(self, state: bool):
        """
        Toggle the visibility of a plot.

        get the name of the plot from the ``sender``'s ``objectName``

        Args:
            state (bool): Whether the plot should be visible (True) or not (False)

        """

        sender_name = self.sender().objectName()
        if sender_name in self.plots.keys():
            if state:
                self.plots[sender_name].setVisible(True)
            else:
                self.plots[sender_name].setVisible(False)

    def set_safe_limits(self, control: ControlSetting):
        """
        Try to set horizontal alarm limits on all relevant plots

        Args:
            control (:class:`.ControlSetting` ): with either ``min_value`` or ``max_value`` set

        Returns:

        """
        for plot in self.plots.values():
            plot.set_safe_limits(control)

    def set_duration(self, duration: float):
        """
        Set the current duration (span of the x axis) of all plots

        Also make sure that the text box and slider reflect this duration

        Args:
            duration (float): new duration to set

        Returns:

        """
        if isinstance(duration, str): # pragma: no cover
            duration = float(duration)

        self.time_box.setText(str(duration))
        self.slider.setValue(duration)

        for plot in self.plots.values():
            plot.set_duration(duration)

    def reset_start_time(self):
        """
        Call :meth:`.Plot.reset_start_time` on all plots
        """
        for plot in self.plots.values():
            plot.reset_start_time()

    def set_units(self, units: str):
        """
        Call :meth:`.Plot.set_units` for all contained plots
        """
        for plot in self.plots.values():
            plot.set_units(units)


    def set_plot_mode(self):
        """
        .. todo::

            switch between longitudinal timeseries and overlaid by breath cycle!!!
        """
        raise NotImplementedError('PVP 2!!!')







