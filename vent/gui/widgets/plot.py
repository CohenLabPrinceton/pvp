import time
from collections import deque

import numpy as np
from PySide2 import QtCore
import PySide2 # import so pyqtgraph recognizes as what we're using
import pyqtgraph as pg


from vent.gui import styles
from vent.gui import mono_font
from vent.gui import get_gui_instance

PLOT_TIMER = None
"""
A :class:`~PySide2.QtCore.QTimer` that updates :class:`.TimedPlotCurveItem`s
"""

PLOT_FREQ = 5
"""
Update frequency of :class:`.Plot` s in Hz
"""


class Plot(pg.PlotWidget):

    limits_changed = QtCore.Signal(tuple)

    def __init__(self, name, buffer_size = 4092, plot_duration = 5, abs_range = None, safe_range = None, color=None, units='', **kwargs):
        #super(Plot, self).__init__(axisItems={'bottom':TimeAxis(orientation='bottom')})
        # construct title html string
        titlestr = "<h1 style=\"{title_style}\">{title_text} ({units})</h1>".format(title_style=styles.TITLE_STYLE,
                                                                      title_text=name,
                                                                        units =units)


        super(Plot, self).__init__(background=styles.BACKGROUND_COLOR,
                                   title=titlestr)
        self.timestamps = deque(maxlen=buffer_size)
        self.history = deque(maxlen=buffer_size)
        # TODO: Make @property to update buffer_size, preserving history
        self.plot_duration = plot_duration

        self.units = units


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
            print('error plotting value: {}, timestamp: {}'.format(new_value[1], new_value[0]))

        #self._last_time = this_time

    def _safe_limits_changed(self, val):
        # ignore input val, just emit the current value of the lines
        self.limits_changed.emit((self.min_safe.value(),
                                       self.max_safe.value()))

    @QtCore.Slot(tuple)
    def set_safe_limits(self, limits):
        self.max_safe.setPos(limits[1])
        self.min_safe.setPos(limits[0])
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

