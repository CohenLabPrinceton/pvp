
#########################
# Imports

# python standard libraries
from collections import deque
import copy
import time

# other required libraries
import numpy as np

# Using PySide (Qt) to build GUI
from PySide2 import QtCore, QtGui, QtWidgets

# import whole module so pyqtgraph recognizes we're using it
# using pyqtgraph for data visualization
import pyqtgraph as pg


# import styles
from vent.gui import defaults
from vent.gui import styles

##########################
# GUI Class

try:
    mono_font = QtGui.QFont('Fira Code')
except:
    mono_font = QtGui.QFont()
    mono_font.setStyleHint(QtGui.QFont.Monospace)



class Display_Value(QtWidgets.QWidget):
    alarm = QtCore.Signal()
    limits_changed = QtCore.Signal(tuple)

    def __init__(self, name, units, abs_range, safe_range, decimals, update_period=0.1):
        super(Display_Value, self).__init__()

        self.name = name
        self.units = units
        self.abs_range = abs_range
        self.safe_range = safe_range
        self.decimals = decimals
        self.update_period = update_period

        self.value = None

        self.init_ui()

        self.timed_update()

    def init_ui(self):
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        #########
        # create widgets
        # make range slider
        self.range_slider = RangeSlider(self.abs_range, self.safe_range)

        # make comboboxes to display numerical value
        self.max_safe = QtWidgets.QSpinBox()
        self.max_safe.setRange(self.abs_range[0], self.abs_range[1])
        self.max_safe.setSingleStep(10 ** (self.decimals * -1))
        self.max_safe.setValue(self.safe_range[1])

        self.min_safe = QtWidgets.QSpinBox()
        self.min_safe.setRange(self.abs_range[0], self.abs_range[1])
        self.min_safe.setSingleStep(10 ** (self.decimals * -1))
        self.min_safe.setValue(self.safe_range[0])

        # labels to display values
        self.value_label = QtWidgets.QLabel()
        self.value_label.setStyleSheet(styles.DISPLAY_VALUE)
        self.value_label.setFont(mono_font)
        self.value_label.setAlignment(QtCore.Qt.AlignRight)
        self.value_label.setMargin(0)
        self.value_label.setContentsMargins(0,0,0,0)

        self.name_label = QtWidgets.QLabel()
        self.name_label.setStyleSheet(styles.DISPLAY_NAME)
        self.name_label.setText(self.name)
        self.name_label.setAlignment(QtCore.Qt.AlignRight)

        self.units_label = QtWidgets.QLabel()
        self.units_label.setStyleSheet(styles.DISPLAY_UNITS)
        self.units_label.setText(self.units)
        self.units_label.setAlignment(QtCore.Qt.AlignRight)

        #########
        # connect widgets

        # update boxes when slider changed
        self.range_slider.valueChanged.connect(self.update_boxes)

        # and vice versa
        self.min_safe.valueChanged.connect(self.range_slider.setLow)
        self.max_safe.valueChanged.connect(self.range_slider.setHigh)

        # and connect them all to a general limits_changed method
        # that also checks the alarm
        self.range_slider.valueChanged.connect(self._limits_changed)
        self.min_safe.valueChanged.connect(self._limits_changed)
        self.max_safe.valueChanged.connect(self._limits_changed)

        #########
        # layout widgets
        self.layout.addWidget(self.range_slider, 2)

        box_layout = QtWidgets.QVBoxLayout()
        box_layout.addWidget(QtWidgets.QLabel('Max:'))
        box_layout.addWidget(self.max_safe)
        box_layout.addStretch()
        box_layout.addWidget(QtWidgets.QLabel('Min:'))
        box_layout.addWidget(self.min_safe)
        self.layout.addLayout(box_layout, 1)

        label_layout = QtWidgets.QVBoxLayout()
        label_layout.setContentsMargins(0,0,0,0)
        label_layout.addWidget(self.value_label)
        label_layout.addWidget(self.name_label)
        label_layout.addWidget(self.units_label)
        label_layout.addStretch()
        self.layout.addLayout(label_layout, 5)


    def update_boxes(self, new_values):
        self.min_safe.setValue(new_values[0])
        self.max_safe.setValue(new_values[1])

    @QtCore.Slot(int)
    @QtCore.Slot(float)
    def update_value(self, new_value):

        # stash numerical value
        self.value = new_value
        self.check_alarm()
        self.range_slider.update_indicator(new_value)

    @QtCore.Slot(tuple)
    def update_limits(self, new_limits):
        self.range_slider.setLow(new_limits[0])
        self.range_slider.setHigh(new_limits[1])
        self.update_boxes(new_limits)

    def timed_update(self):
        # format value based on decimals
        if self.value:
            value_str = str(np.round(self.value, self.decimals))
            self.value_label.setText(value_str)

        QtCore.QTimer.singleShot(round(self.update_period*1000), self.timed_update)

    def _limits_changed(self, val):
        # ignore value, just emit changes and check alarm
        self.check_alarm()
        self.limits_changed.emit((self.min_safe.value(), self.max_safe.value()))

    def check_alarm(self, signal=None):
        if self.value:
            if (self.value >= self.max_safe.value()) or (self.value <= self.min_safe.value()):
                self.alarm.emit()
                self.value_label.setStyleSheet(styles.DISPLAY_VALUE_ALARM)
                self.range_slider.alarm = True
            else:
                self.value_label.setStyleSheet(styles.DISPLAY_VALUE)
                self.range_slider.alarm = False

class Control(QtWidgets.QWidget):

    value_changed = QtCore.Signal(float)

    def __init__(self, name, units, abs_range, value, decimals):
        super(Control, self).__init__()

        self.name = name
        self.units = units
        self.abs_range = abs_range
        self.value = value
        self.decimals = decimals

        self.init_ui()


    def init_ui(self):
        self.layout = QtWidgets.QGridLayout()

        # Value, Controller
        #        min,   max
        # Name
        # Units

        self.value_label = EditableLabel()
        self.value_label.setStyleSheet(styles.CONTROL_VALUE)
        self.value_label.label.setFont(mono_font)
        self.value_label.lineEdit.setFont(mono_font)
        self.value_label.label.setAlignment(QtCore.Qt.AlignRight)
        #self.value_label.setMargin(0)
        self.value_label.setContentsMargins(0,0,0,0)

        # set max size based on range
        # FIXME: TEMPORARY HACK - get sizing to work intelligibly with the dial
        #n_ints = len(str(self.abs_range[1]))
        n_ints = 3
        self.value_label.setFixedWidth(n_ints*styles.VALUE_SIZE*.6)

        self.dial = QtWidgets.QDial()
        self.dial.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.dial.setMinimum(self.abs_range[0])
        self.dial.setMaximum(self.abs_range[1])
        self.dial.setNotchesVisible(True)
        self.dial.setContentsMargins(0,0,0,0)
        self.dial.setFixedHeight(styles.VALUE_SIZE)
        self.dial.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                QtWidgets.QSizePolicy.Fixed)

        self.dial_min = QtWidgets.QLabel()
        self.dial_min.setText(str(np.round(self.abs_range[0], self.decimals)))
        self.dial_min.setAlignment(QtCore.Qt.AlignLeft)
        self.dial_min.setFont(mono_font)
        self.dial_min.setStyleSheet(styles.CONTROL_LABEL)
        self.dial_min.setMargin(0)
        self.dial_min.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                    QtWidgets.QSizePolicy.Maximum)


        self.dial_max = QtWidgets.QLabel()
        self.dial_max.setText(str(np.round(self.abs_range[1], self.decimals)))
        self.dial_max.setAlignment(QtCore.Qt.AlignRight)
        self.dial_max.setFont(mono_font)
        self.dial_max.setStyleSheet(styles.CONTROL_LABEL)
        self.dial_max.setMargin(0)
        self.dial_max.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                    QtWidgets.QSizePolicy.Maximum)

        self.name_label = QtWidgets.QLabel()
        self.name_label.setStyleSheet(styles.DISPLAY_NAME)
        self.name_label.setText(self.name)
        self.name_label.setAlignment(QtCore.Qt.AlignRight)
        self.name_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                    QtWidgets.QSizePolicy.Maximum)

        self.units_label = QtWidgets.QLabel()
        self.units_label.setStyleSheet(styles.DISPLAY_UNITS)
        self.units_label.setText(self.units)
        self.units_label.setAlignment(QtCore.Qt.AlignRight)
        self.units_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                    QtWidgets.QSizePolicy.Maximum)


        ###
        # layout
        self.layout.addWidget(self.value_label, 0, 0, 3, 1, alignment=QtGui.Qt.AlignVCenter | QtGui.Qt.AlignRight)
        self.layout.addWidget(self.dial, 0, 1, 2, 2, alignment=QtGui.Qt.AlignVCenter)
        self.layout.addWidget(self.dial_min, 2, 1, 1, 1)
        self.layout.addWidget(self.dial_max, 2, 2, 1, 1)
        self.layout.addWidget(self.name_label, 3, 0, 1, 3, alignment=QtGui.Qt.AlignRight)
        self.layout.addWidget(self.units_label, 4, 0, 1, 3, alignment=QtGui.Qt.AlignRight)

        self.setLayout(self.layout)


        ###
        # set signals
        self.value_label.textChanged.connect(self.update_value)
        self.dial.valueChanged.connect(self.update_value)


        self.update_value(self.value)

    def update_value(self, new_value):
        if isinstance(new_value, str):
            new_value = float(new_value)

        if (new_value <= self.abs_range[1]) and (new_value >= self.abs_range[0]):
            self.value = new_value

            self.value_changed.emit(self.value)

        # still draw regardless in case an invalid value was given
        value_str = str(np.round(self.value, self.decimals))
        self.value_label.setText(value_str)

        self.dial.setValue(self.value)

















class RangeSlider(QtWidgets.QSlider):
    """
    A slider for ranges.
    This class provides a dual-slider for ranges, where there is a defined
    maximum and minimum, as is a normal slider, but instead of having a
    single slider value, there are 2 slider values.
    This class emits the same signals as the QSlider base class, with the
    exception of valueChanged

    Adapted from https://bitbucket.org/genuine_/idascope-local/src/master/idascope/widgets/RangeSlider.py
    (Thank you!!!)

    With code from https://stackoverflow.com/a/54819051
    for labels!
    """

    valueChanged = QtCore.Signal(tuple)

    def __init__(self, abs_range, safe_range, *args):
        super(RangeSlider, self).__init__(*args)
        self.setStyleSheet(styles.RANGE_SLIDER)

        self.abs_range = abs_range
        self.setMinimum(abs_range[0])
        self.setMaximum(abs_range[1])
        #self.setTickInterval(round((abs_range[1]-abs_range[0])/5))
        #self.setTickPosition(QtWidgets.QSlider.TicksLeft)

        self.safe_range = safe_range
        self.low = safe_range[0]
        self.high = safe_range[1]

        #self._low = self.minimum()
        #self._high = self.maximum()

        self._alarm = False

        self.pressed_control = QtWidgets.QStyle.SC_None
        self.hover_control = QtWidgets.QStyle.SC_None
        self.click_offset = 0

        # 0 for the low, 1 for the high, -1 for both
        self.active_slider = 0

        # ticks
        self.setTickPosition(QtWidgets.QSlider.TicksLeft)
        # gives some space to print labels
        self.left_margin=10
        self.top_margin=10
        self.right_margin=0
        self.bottom_margin=10
        self.setContentsMargins(self.left_margin,
                                self.top_margin,
                                self.right_margin,
                                self.bottom_margin)
        self.setMinimumWidth(styles.SLIDER_WIDTH)

        # indicator
        self._indicator = 0


    @property
    def low(self):
        return self._low

    @low.setter
    def low(self, low):
        self._low = low
        self.update()

    @property
    def high(self):
        return self._high

    @high.setter
    def high(self, high):
        self._high = high
        self.update()

    # make methods just so the can accept signals
    def setLow(self, low):
        self.low = low

    def setHigh(self, high):
        self.high = high

    def update_indicator(self, new_val):
        self._indicator = new_val
        self.update()

    @property
    def alarm(self):
        return self._alarm

    @alarm.setter
    def alarm(self, alarm):
        self._alarm = alarm
        self.update()


    def paintEvent(self, event):
        # based on http://qt.gitorious.org/qt/qt/blobs/master/src/gui/widgets/qslider.cpp

        painter = QtGui.QPainter(self)
        #style = QtWidgets.QApplication.style()
        style = self.style()

        ### Draw current value indicator
        if self._indicator != 0:
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)
            length = style.pixelMetric(QtWidgets.QStyle.PM_SliderLength, opt, self)
            available = style.pixelMetric(QtWidgets.QStyle.PM_SliderSpaceAvailable, opt, self)


            y_loc= QtWidgets.QStyle.sliderPositionFromValue(self.minimum(),
                    self.maximum(), self._indicator, self.height(), opt.upsideDown)


            # draw indicator first, so underneath max and min
            indicator_color = QtGui.QColor(0,0,0)
            if not self.alarm:
                indicator_color.setNamedColor(styles.INDICATOR_COLOR)
            else:
                indicator_color.setNamedColor(styles.ALARM_COLOR)

            x_begin = (self.width()-styles.INDICATOR_WIDTH)/2

            painter.setBrush(indicator_color)
            pen_bak = copy.copy(painter.pen())
            painter.setPen(painter.pen().setWidth(0))
            painter.drawRect(x_begin,y_loc,styles.INDICATOR_WIDTH,self.height()-y_loc)

            painter.setPen(pen_bak)

        for i, value in enumerate([self._high, self._low]):
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)
            # pdb.set_trace()
            # Only draw the groove for the first slider so it doesn't get drawn
            # on top of the existing ones every time
            if i == 0:
                opt.subControls = style.SC_SliderGroove | style.SC_SliderHandle
            else:
                #opt.subControls = QtWidgets.QStyle.SC_SliderHandle
                opt.subControls = style.SC_SliderHandle


            if self.tickPosition() != self.NoTicks:
                opt.subControls |= QtWidgets.QStyle.SC_SliderTickmarks

            if self.pressed_control:
                opt.activeSubControls = self.pressed_control
                opt.state |= QtWidgets.QStyle.State_Sunken
            else:
                opt.activeSubControls = self.hover_control

            # opt.rect.setX(-self.width()/2)
            opt.sliderPosition = value
            opt.sliderValue = value
            style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)

        # draw ticks
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        length = style.pixelMetric(QtWidgets.QStyle.PM_SliderLength, opt, self)
        available = style.pixelMetric(QtWidgets.QStyle.PM_SliderSpaceAvailable, opt, self)
        border_offset = 5
        available -= border_offset

        levels = np.linspace(self.minimum(), self.maximum(), 5)

        painter.setFont(mono_font)

        for v in levels:
            label_str = str(int(round(v)))
            # label_str = "{0:d}".format(v)
            rect = painter.drawText(QtCore.QRect(), QtCore.Qt.TextDontPrint, label_str)

            y_loc= QtWidgets.QStyle.sliderPositionFromValue(self.minimum(),
                    self.maximum(), v, available, opt.upsideDown)

            bottom=y_loc+length//2+rect.height()//2+(border_offset/2)-3
            # there is a 3 px offset that I can't attribute to any metric
            #left = (self.width())-(rect.width())-10
            left = (self.width()/2)-(styles.INDICATOR_WIDTH/2)-rect.width()-3

            pos=QtCore.QPoint(left, bottom)
            painter.drawText(pos, label_str)

        self.setTickInterval(levels[1]-levels[0])




    def mousePressEvent(self, event):
        event.accept()

        style = QtWidgets.QApplication.style()
        button = event.button()

        # In a normal slider control, when the user clicks on a point in the
        # slider's total range, but not on the slider part of the control the
        # control would jump the slider value to where the user clicked.
        # For this control, clicks which are not direct hits will slide both
        # slider parts

        if button:
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)

            self.active_slider = -1

            for i, value in enumerate([self._low, self._high]):
                opt.sliderPosition = value
                hit = style.hitTestComplexControl(style.CC_Slider, opt, event.pos(), self)
                if hit == style.SC_SliderHandle:
                    self.active_slider = i
                    self.pressed_control = hit

                    self.triggerAction(self.SliderMove)
                    self.setRepeatAction(self.SliderNoAction)
                    self.setSliderDown(True)
                    break

            if self.active_slider < 0:
                self.pressed_control = QtWidgets.QStyle.SC_SliderHandle
                self.click_offset = self.__pixelPosToRangeValue(self.__pick(event.pos()))
                self.triggerAction(self.SliderMove)
                self.setRepeatAction(self.SliderNoAction)
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.pressed_control != QtWidgets.QStyle.SC_SliderHandle:
            event.ignore()
            return

        event.accept()

        # get old values
        old_low = copy.copy(self._low)
        old_high = copy.copy(self._high)

        new_pos = self.__pixelPosToRangeValue(self.__pick(event.pos()))
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        if self.active_slider < 0:
            offset = new_pos - self.click_offset
            self._high += offset
            self._low += offset
            if self._low < self.minimum():
                diff = self.minimum() - self._low
                self._low += diff
                self._high += diff
            if self._high > self.maximum():
                diff = self.maximum() - self._high
                self._low += diff
                self._high += diff
        elif self.active_slider == 0:
            if new_pos >= self._high:
                #new_pos = self._high - 1
                new_pos = self._low
            self._low = new_pos
        else:
            if new_pos <= self._low:
                #new_pos = self._low + 1
                new_pos = self._high
            self._high = new_pos
        self.click_offset = new_pos
        self.update()
        self.emit(QtCore.SIGNAL('sliderMoved(int)'), new_pos)

        # emit valuechanged signal
        if (old_low != self._low) or (old_high != self._high):
            self.valueChanged.emit((self._low, self._high))

    def __pick(self, pt):
        if self.orientation() == QtCore.Qt.Horizontal:
            return pt.x()
        else:
            return pt.y()

    def __pixelPosToRangeValue(self, pos):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        style = QtWidgets.QApplication.style()

        gr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)
        sr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderHandle, self)

        if self.orientation() == QtCore.Qt.Horizontal:
            slider_length = sr.width()
            slider_min = gr.x()
            slider_max = gr.right() - slider_length + 1
        else:
            slider_length = sr.height()
            slider_min = gr.y()
            slider_max = gr.bottom() - slider_length + 1
        return style.sliderValueFromPosition(self.minimum(), self.maximum(), pos - slider_min, slider_max - \
            slider_min, opt.upsideDown)


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

        #self._last_time = this_time

    def _safe_limits_changed(self, val):
        # ignore input val, just emit the current value of the lines
        self.limits_changed.emit((self.min_safe.value(),
                                       self.max_safe.value()))

    @QtCore.Slot(tuple)
    def set_safe_limits(self, limits):
        self.max_safe.setPos(limits[1])
        self.min_safe.setPos(limits[0])


class KeyPressHandler(QtCore.QObject):
    """Custom key press handler
    https://gist.github.com/mfessenden/baa2b87b8addb0b60e54a11c1da48046"""
    escapePressed = QtCore.Signal(bool)
    returnPressed = QtCore.Signal(bool)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            event_key = event.key()
            if event_key == QtCore.Qt.Key_Escape:
                self.escapePressed.emit(True)
                return True
            if event_key == QtCore.Qt.Key_Return or event_key == QtCore.Qt.Key_Enter:
                self.returnPressed.emit(True)
                return True

        return QtCore.QObject.eventFilter(self, obj, event)



class EditableLabel(QtWidgets.QWidget):
    """Editable label
    https://gist.github.com/mfessenden/baa2b87b8addb0b60e54a11c1da48046"""
    textChanged = QtCore.Signal(str)

    def __init__(self, parent=None, **kwargs):
        super(EditableLabel, self).__init__(parent=parent, **kwargs)

        self.is_editable = kwargs.get("editable", True)
        self.keyPressHandler = KeyPressHandler(self)

        self.setStyleSheet(styles.CONTROL_VALUE)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setObjectName("mainLayout")

        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName("label")
        # self.label.setStyleSheet(styles.CONTROL_VALUE)
        self.label.setMinimumHeight(styles.VALUE_SIZE)


        self.mainLayout.addWidget(self.label)
        self.lineEdit = QtWidgets.QLineEdit(self)
        # self.lineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                             QtWidgets.QSizePolicy.Expanding)
        # self.lineEdit.setMinimumHeight(styles.VALUE_SIZE)
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setValidator(QtGui.QDoubleValidator())
        self.mainLayout.addWidget(self.lineEdit)
        # hide the line edit initially
        self.lineEdit.setHidden(True)


        # setup signals
        self.create_signals()

    def create_signals(self):
        self.lineEdit.installEventFilter(self.keyPressHandler)
        self.label.mousePressEvent = self.labelPressedEvent

        # give the lineEdit both a `returnPressed` and `escapedPressed` action
        self.keyPressHandler.escapePressed.connect(self.escapePressedAction)
        self.keyPressHandler.returnPressed.connect(self.returnPressedAction)

    def text(self):
        """Standard QLabel text getter"""
        return self.label.text()

    def setText(self, text):
        """Standard QLabel text setter"""
        self.label.blockSignals(True)
        self.label.setText(text)
        self.label.blockSignals(False)

    def labelPressedEvent(self, event):
        """Set editable if the left mouse button is clicked"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setLabelEditableAction()

    def setLabelEditableAction(self):
        """Action to make the widget editable"""
        if not self.is_editable:
            return

        self.label.setHidden(True)
        self.label.blockSignals(True)
        self.lineEdit.setHidden(False)
        self.lineEdit.setText(self.label.text())
        self.lineEdit.blockSignals(False)
        self.lineEdit.setFocus(QtCore.Qt.MouseFocusReason)
        self.lineEdit.selectAll()

    def labelUpdatedAction(self):
        """Indicates the widget text has been updated"""
        text_to_update = self.lineEdit.text()

        if text_to_update != self.label.text():
            self.label.setText(text_to_update)
            self.textChanged.emit(text_to_update)

        self.label.setHidden(False)
        self.lineEdit.setHidden(True)
        self.lineEdit.blockSignals(True)
        self.label.blockSignals(False)

    def returnPressedAction(self):
        """Return/enter event handler"""
        self.labelUpdatedAction()

    def escapePressedAction(self):
        """Escape event handler"""
        self.label.setHidden(False)
        self.lineEdit.setHidden(True)
        self.lineEdit.blockSignals(True)
        self.label.blockSignals(False)

class QHLine(QtWidgets.QFrame):
    """
    with respct to https://stackoverflow.com/a/51057516
    """
    def __init__(self, parent=None, color=QtGui.QColor(styles.DIVIDER_COLOR)):
        super(QHLine, self).__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setLineWidth(0)
        self.setMidLineWidth(3)
        self.setContentsMargins(0, 0, 0, 0)
        self.setColor(color)

    def setColor(self, color):
        pal = self.palette()
        pal.setColor(QtGui.QPalette.WindowText, color)
        self.setPalette(pal)

class TimeAxis(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLabel(text='Time', units=None)
        self.enableAutoSIPrefix(False)

    def tickStrings(self, values, scale, spacing):
        return [datetime.fromtimestamp(value).strftime('%H:%M:%S') for value in values]

