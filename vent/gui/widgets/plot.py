import time
from collections import deque

import numpy as np
from PySide2 import QtCore
import PySide2 # import so pyqtgraph recognizes as what we're using
import pyqtgraph as pg


from vent.gui import styles
from vent.gui import mono_font


class Plot(pg.PlotWidget):

    limits_changed = QtCore.Signal(tuple)

    def __init__(self, name, buffer_size = 4092, plot_duration = 5, abs_range = None, safe_range = None, color=None):
        #super(Plot, self).__init__(axisItems={'bottom':TimeAxis(orientation='bottom')})
        # construct title html string
        titlestr = "<h1 style=\"{title_style}\">{title_text}</h1>".format(title_style=styles.TITLE_STYLE,
                                                                      title_text=name)


        super(Plot, self).__init__(background=styles.BACKGROUND_COLOR,
                                   title=titlestr)
        self.timestamps = deque(maxlen=buffer_size)
        self.history = deque(maxlen=buffer_size)
        # TODO: Make @property to update buffer_size, preserving history
        self.plot_duration = plot_duration



        self._start_time = time.time()
        self._last_time = time.time()
        self._last_relative_time = 0

        self.abs_range = None
        if abs_range:
            self.abs_range = abs_range
            self.setYRange(self.abs_range[0], self.abs_range[1])

        self.safe_range = (0,0)
        if safe_range:
            self.safe_range = safe_range


        self.setXRange(0, plot_duration)

        # split plot curve into two so that the endpoint doesn't get connected to the start point
        self.early_curve = self.plot(width=3)
        self.late_curve = self.plot(width=3)
        self.time_marker = self.plot()

        self.min_safe = pg.InfiniteLine(movable=True, angle=0, pos=self.safe_range[0])
        self.max_safe = pg.InfiniteLine(movable=True, angle=0, pos=self.safe_range[1])
        self.min_safe.sigPositionChanged.connect(self._safe_limits_changed)
        self.max_safe.sigPositionChanged.connect(self._safe_limits_changed)

        self.addItem(self.min_safe)
        self.addItem(self.max_safe)

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
            self.time_marker.setData([current_relative_time, current_relative_time],
                                     [limits[1][0], limits[1][1]])

            self.timestamps.append(new_value[0])
            self.history.append(new_value[1])

            # filter values based on timestamps
            ts_array = np.array(self.timestamps)
            end_ind = len(self.history)
            start_ind = np.where(ts_array > (this_time - self.plot_duration))[0][0]

            # subtract start time and take modulus of duration to get wrapped timestamps
            plot_timestamps = np.mod(ts_array[start_ind:end_ind]-self._start_time, self.plot_duration)
            plot_values = np.array([self.history[i] for i in range(start_ind, end_ind)])

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
            print('error with value: {}, timestamp: {}'.format(new_value[1], new_value[0]))

        #self._last_time = this_time

    def _safe_limits_changed(self, val):
        # ignore input val, just emit the current value of the lines
        self.limits_changed.emit((self.min_safe.value(),
                                       self.max_safe.value()))

    @QtCore.Slot(tuple)
    def set_safe_limits(self, limits):
        self.max_safe.setPos(limits[1])
        self.min_safe.setPos(limits[0])