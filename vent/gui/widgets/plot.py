import time
from collections import deque
import pdb
import typing

import numpy as np
from PySide2 import QtCore
import PySide2 # import so pyqtgraph recognizes as what we're using
import pyqtgraph as pg


from vent.gui import styles
from vent.gui import mono_font
from vent.gui import get_gui_instance
from vent.common import unit_conversion
from vent.common.message import SensorValues, ControlSetting
from vent.common.values import ValueName
from vent.common.logging import init_logger
from vent.alarm import AlarmSeverity

PLOT_TIMER = None
"""
A :class:`~PySide2.QtCore.QTimer` that updates :class:`.TimedPlotCurveItem`s
"""

PLOT_FREQ = 5
"""
Update frequency of :class:`.Plot` s in Hz
"""

class Pressure_Waveform(pg.PlotWidget):
    """
    Display the ideal piecewise function parameterized by the controls and a history of traces
    """
    control_changed = QtCore.Signal(ControlSetting)

    controlling_plot = QtCore.Signal(bool)

    PARAMETERIZING_VALUES = (
        ValueName.PIP_TIME,
        ValueName.PIP,
        ValueName.PEEP_TIME,
        ValueName.PEEP,
        ValueName.INSPIRATION_TIME_SEC,
        ValueName.BREATHS_PER_MINUTE
    )

    def __init__(self, n_waveforms = 10, **kwargs):
        super(Pressure_Waveform, self).__init__(background=styles.TEXT_COLOR)

        self.getPlotItem().titleLabel.item.setHtml(
            f"<span style='{styles.PRESSURE_PLOT_TITLE_STYLE}'>Pressure Control Waveform</span>"
        )
        self.getPlotItem().titleLabel.setAttr('justify', 'left')

        # create a dq of plot items to hold waveforms
        self.n_waveforms = n_waveforms
        self.waveforms = deque(maxlen=self.n_waveforms)

        for i in range(self.n_waveforms):
            self.waveforms.append(self.plot())

        self.colors = np.linspace(0, 128, self.n_waveforms)

        # store last values, see param_changed
        self._pip = None
        self._pip_min = None
        self._pip_max = None
        self._peep = None
        self._peep_min = None
        self._peep_max = None
        self._pipt = None
        self._peept = None
        self._inspt = None
        self._rr = None

        self._convert_in = None
        self._convert_out = None
        self.units = 'cmH2O'


        self._last_target = np.array(())
        self._last_cycle = None
        self._last_cycle_timestamp = 0
        self._current_timestamps = []
        self._current_values = []
        self.__controlling_plot = False
        self.enableAutoRange(y=True)

        self.init_plot()

    def init_plot(self):

        # self.getViewBox().setMouseEnabled(False, False)

        self.setStyleSheet(styles.PRESSURE_PLOT_BOX)

        # draw lines
        # upward line
        self.segment_inhale = self.plot(width=3, symbolPen='w')
        self.segment_pip = NamedLine(ValueName.PIP, movable=True, angle=0, pos=0)
        self.segment_exhale = self.plot(width=3, symbolPen='w')
        self.segment_peep = NamedLine(ValueName.PEEP, movable=True, angle=0, pos=0)

        self.addItem(self.segment_pip)
        self.addItem(self.segment_peep)

        self.segment_inhale.setPen(color=styles.SUBWAY_COLORS['blue'], width=10)
        self.segment_pip.setPen(color=styles.SUBWAY_COLORS['blue'], width=10)
        self.segment_exhale.setPen(color=styles.SUBWAY_COLORS['blue'], width=10)
        self.segment_peep.setPen(color=styles.SUBWAY_COLORS['blue'], width=10)

        # draw points
        self.point_pipt = ScatterDrag(value_name=ValueName.PIP_TIME, width=3, symbolBrush=(255, 0, 0), symbolPen='w')
        self.point_inspt = ScatterDrag(value_name=ValueName.INSPIRATION_TIME_SEC, width=3, symbolBrush=(255, 0, 0), symbolPen='w')
        self.point_peept = ScatterDrag(value_name=ValueName.PEEP_TIME, width=3, symbolBrush=(255, 0, 0), symbolPen='w')

        self.addItem(self.point_pipt)
        self.addItem(self.point_inspt)
        self.addItem(self.point_peept)

        # draw regions showing error tolerances
        region_pen_kwargs = {'color':styles.SUBWAY_COLORS['red'],
                             'width': 3}
        self.region_pip = pg.LinearRegionItem((0,0), orientation='horizontal', movable=False,
                                              pen=region_pen_kwargs)
        self.region_peep = pg.LinearRegionItem((0,0), orientation='horizontal',movable=False,
                                               pen=region_pen_kwargs)

        self.addItem(self.region_pip)
        self.addItem(self.region_peep)
        self.region_pip.setBrush((0,0,0,0.1))
        self.region_peep.setBrush((0,0,0,0.1))

        # connect signals to a general update method
        #self.segment_pip.sigPositionChanged.connect(self.param_changed)
        #self.segment_peep.sigPositionChanged.connect(self.param_changed)

        self.segment_pip.value_changed.connect(self.param_changed)
        self.segment_peep.value_changed.connect(self.param_changed)
        self.point_pipt.value_changed.connect(self.param_changed)
        self.point_inspt.value_changed.connect(self.param_changed)
        self.point_peept.value_changed.connect(self.param_changed)

        self.point_pipt.controlling_plot.connect(self._controlling_plot)
        self.point_peept.controlling_plot.connect(self._controlling_plot)
        self.point_inspt.controlling_plot.connect(self._controlling_plot)
        #self.target = self.plot(width=3, symbolBrush=(255,0,0), symbolPen='w')
        #self.target.setPen(color=styles.SUBWAY_COLORS['yellow'], width=3)

    @QtCore.Slot(bool)
    def _controlling_plot(self, controlling_plot: bool):
        if self.__controlling_plot != controlling_plot:
            self.__controlling_plot = controlling_plot
            self.controlling_plot.emit(controlling_plot)
            if controlling_plot:
                self.segment_pip.setMovable(False)
                self.segment_peep.setMovable(False)
            else:
                self.segment_pip.setMovable(True)
                self.segment_peep.setMovable(True)



    @QtCore.Slot(tuple)
    def param_changed(self, param: typing.Tuple[ValueName, typing.Union[tuple, float]]):
        """
        Emit parameter that is changed by the plot

        Args:
            param:

        Returns:
        """
        # fuck it just going to hardcode
        value_name = param[0]
        new_val = param[1]
        if value_name in (ValueName.PIP, ValueName.PEEP):
            # convert back to cmH2O if needed
            if self._convert_out:
                new_val = self._convert_out(new_val)
        elif value_name in (ValueName.PIP_TIME, ValueName.INSPIRATION_TIME_SEC, ValueName.PEEP_TIME):
            # points
            # these need to be subtracted back inta shape
            #pdb.set_trace()
            new_val, _ = new_val
            if value_name == ValueName.PEEP_TIME:
                new_val = new_val-self._inspt
        else:
            raise ValueError(f"parameter sent from waveform plot not understood: {param}")

        if value_name == ValueName.PIP:
            self._pip = new_val
        elif value_name == ValueName.PEEP:
            self._peep = new_val
        elif value_name == ValueName.PIP_TIME:
            self._pipt = new_val
        elif value_name == ValueName.PEEP_TIME:
            self._peept = new_val
        elif value_name == ValueName.INSPIRATION_TIME_SEC:
            self._inspt = new_val

        control = ControlSetting(
            name=value_name,
            value=new_val
        )
        self.control_changed.emit(control)
        self.draw_target()


    def update_target(self, control_setting: ControlSetting):
        """
        Receive an update the target waveform as a :class:`.ControlSetting`

        Args:
            control_setting (:class:`.ControlSetting`): one of :attr:`.PARAMETERIZING_VALUES`

        Returns:

        """

        value_name = control_setting.name
        value = control_setting.value

        # if value is none, may be setting limits.
        if value_name == ValueName.PIP:
            if control_setting.min_value and control_setting.range_severity == AlarmSeverity.LOW:
                self._pip_min = control_setting.min_value
            if control_setting.max_value:
                self._pip_max = control_setting.max_value
        elif value_name == ValueName.PEEP:
            if control_setting.min_value:
                self._peep_min = control_setting.min_value
            if control_setting.max_value:
                self._peep_max = control_setting.max_value

        if control_setting.value is not None:

            if value_name == ValueName.PIP_TIME:
                self._pipt = value
            elif value_name == ValueName.PIP:
                self._pip = value
            elif value_name == ValueName.PEEP_TIME:
                self._peept = value
            elif value_name == ValueName.PEEP:
                self._peep = value
            elif value_name == ValueName.INSPIRATION_TIME_SEC:
                self._inspt = value
            elif value_name == ValueName.BREATHS_PER_MINUTE:
                self._rr = value
            else:
                init_logger(__name__).exception(f'Tried to set waveform plot with {value_name}, but no plot element corresponds')
                return

        self.draw_target()



    def update_target_array(self, target):
        """
        Update the target waveform with an array from the ``controller``

        Args:
            target:

        Returns:

        """
        # pdb.set_trace()
        if not np.array_equal(target, self._last_target):
            # calculate values from array
            self._pipt = target[1,0]-target[0,0]
            self._pip = target[1,1]
            self._peept = target[3,0]-target[2,0]
            self._peep = target[3,1]
            self._inspt = target[2,0]-target[1,0]
            self._rr = (1/(target[4,0]-target[0,0]))/60
            self._last_target = target
            self.draw_target()

    def draw_target(self):
        #     view_range = np.min(target[:, 0]), np.max(target[:, 0])


        # find the x range and set first!!
        # if no values are populated, set to 0 and 1
        x_points = [0, 1]
        if self._pipt:
            x_points.append(self._pipt)
            if self._inspt:
                x_points.append(self._pipt+self._inspt)
                if self._peept:
                    x_points.append(self._pipt + self._inspt+self._peept)
        if self._rr:
            x_points.append(1/(self._rr/60))

        x_min, x_max = np.min(x_points), np.max(x_points)
        self.setXRange(x_min, x_max)

        ############
        # get new view range and use to calc lines
        view_range = self.getViewBox().state['viewRange'][0]
        x_range = view_range[1] - view_range[0]

        # try to draw each segment depending on which values are set
        ### pipt line and pipt point
        if self._pip and self._pipt and self._peep:
            if self._convert_in:
                self.segment_inhale.setData(
                    np.array([0, self._pipt]),
                    np.array([self._convert_in(self._peep), self._convert_in(self._pip)])
                )
                self.point_pipt.setData([self._pipt], [self._convert_in(self._pip)])
            else:
                self.segment_inhale.setData(
                    np.array([0, self._pipt]),
                    np.array([self._peep, self._pip])
                )
                self.point_pipt.setData([self._pipt], [self._pip])


        ### pip line and inspt
        if self._pip and self._pipt and self._inspt:
            if self._convert_in:
                self.segment_pip.setValue(self._convert_in(self._pip))
                self.point_inspt.setData([self._inspt], [self._convert_in(self._pip)])
            else:
                self.segment_pip.setValue(self._pip)
                self.point_inspt.setData([self._inspt], [self._pip])
            # if self._pipt and self._inspt:
            #
            pip_bounds = ((self._pipt-view_range[0])/ x_range,
                          (self._inspt-view_range[0])/ x_range)

            self.segment_pip.setSpan(mn=pip_bounds[0], mx=pip_bounds[1])
            self.region_pip.setSpan(mn=pip_bounds[0], mx=pip_bounds[1])
            #

        if self._pip_min and self._pip_max:
            if self._convert_in:
                self.region_pip.setRegion((self._convert_in(self._pip_min),
                                           self._convert_in(self._pip_max)))
            else:
                self.region_pip.setRegion((self._pip_min, self._pip_max))


        ### exhale slope
        if self._inspt and self._pip and self._peept and self._peep:
            if self._convert_in:
                self.segment_exhale.setData(
                    np.array([self._inspt,
                              self._inspt + self._peept]),
                    np.array([self._convert_in(self._pip),
                              self._convert_in(self._peep)])
                )

                self.point_peept.setData([self._inspt + self._peept],
                                         [self._convert_in(self._peep)])
            else:
                self.segment_exhale.setData(
                    np.array([self._inspt,
                              self._inspt + self._peept]),
                    np.array([self._pip, self._peep])
                )

                self.point_peept.setData([self._inspt + self._peept],
                                         [self._peep])



        ### peep line
        if self._peep and self._inspt and self._peept and self._rr:
            if self._convert_in:
                self.segment_peep.setValue(self._convert_in(self._peep))
            else:
                self.segment_peep.setValue(self._peep)

            # peep_bounds = (0,1)
            # if self._pipt and self._inspt and self._peept and self._rr:
            peep_bounds = ((self._inspt + self._peept-view_range[0])/x_range,
                           (1/(self._rr/60)-view_range[0])/x_range)

            #
            # elif self._pipt and self._inspt and self._peept:
            #     peep_bounds = ((self._pipt + self._inspt + self._peept)/x_range,
            #                    1)
            #     x_points.append(self._pipt + self._inspt + self._peept)
            # elif self._rr:
            #     peep_bounds = (0, 1/(self._rr/60)/x_range)
            #     x_points.append(1/(self._rr/60))
            #
            self.segment_peep.setSpan(peep_bounds[0], peep_bounds[1])
            self.region_peep.setSpan(*peep_bounds)

        if self._peep_min and self._peep_max:
            if self._convert_in:
                self.region_peep.setRegion((self._convert_in(self._peep_min),
                                            self._convert_in(self._peep_max)))
            else:
                self.region_peep.setRegion((self._peep_min, self._peep_max))



    def update_waveform(self, sensors: SensorValues):
        if self._last_cycle is None or sensors.breath_count > self._last_cycle:
            self._last_cycle = sensors.breath_count
            self._last_cycle_timestamp = sensors.timestamp

            self.waveforms.rotate()
            for i, wave in enumerate(self.waveforms):
                wave.setPen(color=(self.colors[i],self.colors[i],self.colors[i]))

            self._current_timestamps = []
            self._current_values = []

        self._current_values.append(sensors.PRESSURE)
        if self._convert_in:
            current_values = self._convert_in(np.array(self._current_values))
        else:
            current_values = np.array(self._current_values)
        self._current_timestamps.append(sensors.timestamp - self._last_cycle_timestamp)
        self.waveforms[0].setData(np.array(self._current_timestamps),
                                  current_values)

    def set_units(self, units):

        try:
            self.blockSignals(True)
            if units == 'cmH2O':
                self.units = units
                # self.units_label.setText(units)
                self._convert_in = None
                self._convert_out = None
            elif units == 'hPa':
                self.units = units
                # self.units_label.setText(units)
                self._convert_in = unit_conversion.cmH2O_to_hPa
                self._convert_out = unit_conversion.hPa_to_cmH2O

            for wave in self.waveforms:
                wave.setData([0], [0])

            self.draw_target()
        finally:
            self.blockSignals(False)


class NamedLine(pg.InfiniteLine):
    value_changed = QtCore.Signal(tuple)

    def __init__(self, name: ValueName, *args, **kwargs):
        super(NamedLine, self).__init__(*args, **kwargs)
        self.name = name
        self.sigPositionChanged.connect(self._value_changed)

    def _value_changed(self):
        self.value_changed.emit((self.name, self.value()))

    def setSpan(self, mn, mx):
        if self.span != (mn, mx):
            self.span = (mn, mx)
            self._invalidateCache()
            self.update()

class ScatterDrag(pg.ScatterPlotItem):
    """
    A scatterplot but u can drag the points horizontally and they uh tell u.

    """
    value_changed = QtCore.Signal(tuple)
    controlling_plot = QtCore.Signal(bool)

    def __init__(self, value_name: ValueName, pos=(0, 0), *args, **kwargs):
        self.mouseHovering = False
        self.mouseDragging = False
        super(ScatterDrag, self).__init__(*args, **kwargs)
        self.setSize(10)
        self._name = value_name
        self._pos = pos

        self.setAcceptHoverEvents(True)
        self.setData([pos[0]], [pos[1]])
        # self.normal_brush = self.opts['brush']
        # self.hover_brush = pg.mkBrush(#)

    def mouseDragEvent(self, ev):
        """
        from the CustomGraphItem example

        Args:
            ev:

        Returns:

        """
        if ev.button() != QtCore.Qt.LeftButton:
            ev.ignore()
            return

        if ev.isStart():
            # We are already one step into the drag.
            # Find the point(s) at the mouse cursor when the button was first
            # pressed:
            pos = ev.buttonDownPos()
            #pts = self.pointsAt(pos)
            if not self.mouseHovering:
                ev.ignore()
                return
            # if len(pts) == 0:

            pts = self.points()

            self.mouseDragging = True
            self.dragPoint = pts[0]
            #self.drag_offset_x = self.dragPoint.pos().x() - pos.x()
            #pdb.set_trace()
            #ind = pts[0].data()[0]
            #self.dragOffset = self.dragPoint.pos() - pos
        elif ev.isFinish():
            #self.value_changed.emit((self._name, (drag_pos_x, self.dragPoint.pos().y())))
            self.dragPoint = None
            self.mouseDragging = False

            return
        else:
            if self.dragPoint is None:
                ev.ignore()
                return

        #self.drag_pos_x -= ev.pos().x()

        #ind = self.dragPoint.data()[0]
        #self.data['pos'][ind] = ev.pos() + self.dragOffset
        #self.updateGraph()
        self.setData([ev.pos().x()], [self.dragPoint.pos().y()])
        self.value_changed.emit((self._name, (ev.pos().x(), self.dragPoint.pos().y())))

        ev.accept()

    def hoverEvent(self, ev):
        if (not ev.isExit()):
            self.setMouseHover(True)

        else:
            #if not self.mouseDragging:
            self.setMouseHover(False)

    def setMouseHover(self, hover):
        if self.mouseHovering == hover:
            return
        self.mouseHovering = hover
        if hover:
            self.controlling_plot.emit(True)
            self.setSize(30, update=True)
        else:
            self.controlling_plot.emit(False)
            self.setSize(10,update=True)
        self.update()

    def setData(self, *args, **kwargs):
        if not self.mouseHovering:
            super(ScatterDrag, self).setData(*args, **kwargs)







class Plot(pg.PlotWidget):

    limits_changed = QtCore.Signal(tuple)

    def __init__(self, name, buffer_size = 4092,
                 plot_duration = 5,
                 abs_range = None,
                 range_limits: tuple = None,
                 color=None,
                 units='',
                 **kwargs):
        """

        Args:
            name:
            buffer_size:
            plot_duration:
            abs_range:
            range_limits (tuple): tuple of (ValueName)s for which to make pairs of min and max range lines
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

        self._range_limits = {}
        if range_limits:
            for value in range_limits:
                self._range_limits[value] = (
                    pg.InfiniteLine(movable=False, angle=0, pos=0),
                    pg.InfiniteLine(movable=False, angle=0, pos=0)
                )
                # self.min_safe.sigPositionChanged.connect(self._safe_limits_changed)
                # self.max_safe.sigPositionChanged.connect(self._safe_limits_changed)
                self.addItem(self._range_limits[value][0])
                self.addItem(self._range_limits[value][1])


        self.setXRange(0, plot_duration)

        # split plot curve into two so that the endpoint doesn't get connected to the start point
        self.early_curve = self.plot(width=3)
        self.late_curve = self.plot(width=3)
        self.time_marker = pg.InfiniteLine(movable=False, angle=90, pos=0)





        if color:
            self.early_curve.setPen(color=color, width=3)
            self.late_curve.setPen(color=color, width=3)


    def set_duration(self, dur):
        self.plot_duration = int(round(dur))
        self.setXRange(0, self.plot_duration)


    def update_value(self, new_value):
        """
        new_value: (timestamp from time.time(), value)
        """
        try:
            this_time = time.time()
            #time_diff = this_time-self._last_time
            limits = self.getPlotItem().viewRange()
            current_relative_time = (this_time-self._start_time) % self.plot_duration
            # self.time_marker.setData([current_relative_time, current_relative_time],
            #                          [limits[1][0], limits[1][1]])
            self.time_marker.setValue(current_relative_time)

            self.timestamps.append(new_value[0])
            self.history.append(new_value[1])

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
        if self._range_limits is None:
            return

        if limits.name in self._range_limits.keys():

            if limits.min_value:
                if self._convert_out:
                    self._range_limits[limits.name][0].setPos(self._convert_out(limits.min_value))
                else:
                    self._range_limits[limits.name][0].setPos(limits.min_value)
            if limits.max_value:
                if self._convert_out:
                    self._range_limits[limits.name][1].setPos(self._convert_out(limits.max_value))
                else:
                    self._range_limits[limits.name][1].setPos(limits.max_value)


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

                for range_pairs in self._range_limits.values():
                    for a_line in range_pairs:
                        a_line.setPos(unit_conversion.hPa_to_cmH2O(a_line.getPos()[1]))

            elif units == 'hPa':
                self.decimals = 0
                self.units = units
                self._convert_in = unit_conversion.cmH2O_to_hPa
                self._convert_out = unit_conversion.hPa_to_cmH2O

                for range_pairs in self._range_limits.values():
                    for a_line in range_pairs:
                        a_line.setPos(unit_conversion.cmH2O_to_hPa(a_line.getPos()[1]))

            titlestr = "{title_text} ({units})".format(
                title_text=self.name,
                units=self.units)
            self.getPlotItem().titleLabel.item.setHtml(
                f"<span style='{styles.PLOT_TITLE_STYLE}'>{titlestr}</span>"
            )



    #
    # def plot(self, *args, **kargs):
    #     """
    #     Override method :meth:`pyqtgraph.graphicsItems.PlotItem.plot` to return :class:`TimedPlotDataItem`
    #
    #     Add and return a new plot.
    #     See :func:`PlotDataItem.__init__ <pyqtgraph.PlotDataItem.__init__>` for data arguments
    #
    #     Extra allowed arguments are:
    #         clear    - clear all plots before displaying new data
    #         params   - meta-parameters to associate with this data
    #     """
    #     clear = kargs.get('clear', False)
    #     params = kargs.get('params', None)
    #
    #     if clear:
    #         self.clear()
    #
    #     item = TimedPlotDataItem(*args, **kargs)
    #
    #     if params is None:
    #         params = {}
    #     self.addItem(item, params=params)
    #
    #     return item
#
# class TimedPlotDataItem(pg.PlotDataItem):
#     """
#     Subclass of :class:`pyqtgraph.PlotDataItem` that uses :class:`.TimedPlotCurveItem`
#
#     """
#
#     def __init__(self, *args, **kwargs):
#         super(TimedPlotDataItem, self).__init__(*args, **kwargs)
#
#         # replace self.curve with timed version
#         # mimic __init__ from parent
#         # https://github.com/pyqtgraph/pyqtgraph/blob/a2053b13d0234e210561a73fa044625fd972e910/pyqtgraph/graphicsItems/PlotDataItem.py#L37
#         self.curve = TimedPlotCurveItem()
#         self.curve.setParentItem(self)
#         self.curve.sigClicked.connect(self.curveClicked)
#
#         self.setData(*args, **kwargs)
#
# class TimedPlotCurveItem(pg.PlotCurveItem):
#     """
#     Subclass :class:`pyqtgraph.PlotCurveItem` to update with a fixed frequency instead of whenever new data pushed
#
#     Either creates or gets :data:`PLOT_TIMER` and connects it to :meth:`TimedPlotCurveItem.update`
#     """
#
#
#     def __init__(self, *args, **kwargs):
#         super(TimedPlotCurveItem, self).__init__(*args, **kwargs)
#
#         if globals()['PLOT_TIMER'] is None:
#             globals()['PLOT_TIMER'] = QtCore.QTimer()
#
#             get_gui_instance().gui_closing.connect(globals()['PLOT_TIMER'].stop)
#
#         self.timer = globals()['PLOT_TIMER']
#         # stop timer, add ourselves, restart
#         self.timer.timeout.connect(self.update)
#
#         try:
#             self.fps = float(globals()['PLOT_FREQ'])
#         except (ValueError, KeyError):
#             self.fps = 15.
#
#         self.timer.start(1./self.fps)
#
#
#
#     def __del__(self):
#         """
#         On object deletion, remove from :data:`.PLOT_TIMER` 's signals
#         """
#         #self.timer.disconnect(self.update)
#         #super(TimedPlotCurveItem, self).__del__()
#
#
#     def updateData(self, *args, **kargs):
#         """
#         Override :meth:`pyqtgraph.PlotCurveItem.updateData` to omit call to :meth:`.update`
#         which is done by :data:`.PLOT_TIMER`
#
#         """
#         profiler = pg.debug.Profiler()
#
#         if 'compositionMode' in kargs:
#             self.setCompositionMode(kargs['compositionMode'])
#
#         if len(args) == 1:
#             kargs['y'] = args[0]
#         elif len(args) == 2:
#             kargs['x'] = args[0]
#             kargs['y'] = args[1]
#
#         if 'y' not in kargs or kargs['y'] is None:
#             kargs['y'] = np.array([])
#         if 'x' not in kargs or kargs['x'] is None:
#             kargs['x'] = np.arange(len(kargs['y']))
#
#         for k in ['x', 'y']:
#             data = kargs[k]
#             if isinstance(data, list):
#                 data = np.array(data)
#                 kargs[k] = data
#             if not isinstance(data, np.ndarray) or data.ndim > 1:
#                 raise Exception("Plot data must be 1D ndarray.")
#             if data.dtype.kind == 'c':
#                 raise Exception("Can not plot complex data types.")
#
#         profiler("data checks")
#
#         # self.setCacheMode(QtGui.QGraphicsItem.NoCache)  ## Disabling and re-enabling the cache works around a bug in Qt 4.6 causing the cached results to display incorrectly
#         ##    Test this bug with test_PlotWidget and zoom in on the animated plot
#         self.yData = kargs['y'].view(np.ndarray)
#         self.xData = kargs['x'].view(np.ndarray)
#
#         self.invalidateBounds()
#         self.prepareGeometryChange()
#         self.informViewBoundsChanged()
#
#         profiler('copy')
#
#         if 'stepMode' in kargs:
#             self.opts['stepMode'] = kargs['stepMode']
#
#         if self.opts['stepMode'] is True:
#             if len(self.xData) != len(self.yData) + 1:  ## allow difference of 1 for step mode plots
#                 raise Exception("len(X) must be len(Y)+1 since stepMode=True (got %s and %s)" % (
#                 self.xData.shape, self.yData.shape))
#         else:
#             if self.xData.shape != self.yData.shape:  ## allow difference of 1 for step mode plots
#                 raise Exception(
#                     "X and Y arrays must be the same shape--got %s and %s." % (self.xData.shape, self.yData.shape))
#
#         self.path = None
#         self.fillPath = None
#         self._mouseShape = None
#         # self.xDisp = self.yDisp = None
#
#         if 'name' in kargs:
#             self.opts['name'] = kargs['name']
#         if 'connect' in kargs:
#             self.opts['connect'] = kargs['connect']
#         if 'pen' in kargs:
#             self.setPen(kargs['pen'])
#         if 'shadowPen' in kargs:
#             self.setShadowPen(kargs['shadowPen'])
#         if 'fillLevel' in kargs:
#             self.setFillLevel(kargs['fillLevel'])
#         if 'fillOutline' in kargs:
#             self.opts['fillOutline'] = kargs['fillOutline']
#         if 'brush' in kargs:
#             self.setBrush(kargs['brush'])
#         if 'antialias' in kargs:
#             self.opts['antialias'] = kargs['antialias']
#
#         profiler('set')
#         #self.update()
#         profiler('update')
#         #self.sigPlotChanged.emit(self)
#         profiler('emit')

