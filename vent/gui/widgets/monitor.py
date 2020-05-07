import numpy as np
import time
from PySide2 import QtWidgets, QtCore

from vent.gui import styles, mono_font
from vent.gui.widgets.components import RangeSlider
from vent.common import message


class Monitor(QtWidgets.QWidget):
    alarm = QtCore.Signal(tuple)
    limits_changed = QtCore.Signal(tuple)

    def __init__(self, value, update_period=styles.MONITOR_UPDATE_INTERVAL, enum_name = None):
        """

        Args:
            value (:class:`~vent.values.Value`):
            update_period (float): update period of monitor in s
        """
        super(Monitor, self).__init__()

        self.name = value.name
        self.units = value.units
        self.abs_range = value.abs_range
        self.safe_range = value.safe_range
        self.decimals = value.decimals
        self.update_period = update_period
        self.enum_name = enum_name

        self.value = None

        # whether we are currently styled as being in an alarm state
        self._alarm = False

        self.init_ui()

        self.timed_update()

    def init_ui(self):
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        #########
        # create widgets
        # make range slider
        self.range_slider = RangeSlider(self.abs_range, self.safe_range,
                                        decimals=self.decimals,
                                        orientation=QtCore.Qt.Orientation.Horizontal)

        # make comboboxes to display numerical value
        self.max_safe = QtWidgets.QDoubleSpinBox()
        self.max_safe.setDecimals(self.decimals)
        self.max_safe.setRange(self.abs_range[0], self.abs_range[1])
        self.max_safe.setSingleStep(10 ** (self.decimals * -1))
        self.max_safe.setValue(self.safe_range[1])

        self.min_safe = QtWidgets.QDoubleSpinBox()
        self.min_safe.setDecimals(self.decimals)
        self.min_safe.setRange(self.abs_range[0], self.abs_range[1])
        self.min_safe.setSingleStep(10 ** (self.decimals * -1))
        self.min_safe.setValue(self.safe_range[0])

        # labels to display values
        self.value_label = QtWidgets.QLabel()
        self.value_label.setStyleSheet(styles.DISPLAY_VALUE)
        self.value_label.setFont(mono_font())
        self.value_label.setAlignment(QtCore.Qt.AlignRight)
        self.value_label.setMargin(0)
        self.value_label.setContentsMargins(0,0,0,0)
        self.value_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                       QtWidgets.QSizePolicy.Expanding)

        self.name_label = QtWidgets.QLabel()
        self.name_label.setStyleSheet(styles.DISPLAY_NAME)
        self.name_label.setText(self.name)
        self.name_label.setAlignment(QtCore.Qt.AlignRight)


        self.units_label = QtWidgets.QLabel()
        self.units_label.setStyleSheet(styles.DISPLAY_UNITS)
        self.units_label.setText(self.units)
        self.units_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self.units_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                         QtWidgets.QSizePolicy.Expanding)

        # toggle button to expand control
        self.toggle_button = QtWidgets.QToolButton(checkable=True,
                                                   checked=False)
        self.toggle_button.setStyleSheet(styles.DISPLAY_NAME)

        self.toggle_button.toggled.connect(self.toggle_control)
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonIconOnly
        )
        self.toggle_button.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                         QtWidgets.QSizePolicy.Expanding)
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)

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

        # first make label layout
        label_layout = QtWidgets.QGridLayout()
        label_layout.setContentsMargins(0,0,0,0)
        label_layout.addWidget(self.toggle_button, 0,0,2,1)
        label_layout.addWidget(self.value_label, 0,1,2,1)
        label_layout.addWidget(self.name_label, 0,2,1,1)
        label_layout.addWidget(self.units_label, 1,2,1,1)
        # label_layout.addStretch()
        self.layout.addLayout(label_layout, 5)

        # then combine sliders and boxes
        self.slider_layout = QtWidgets.QVBoxLayout()

        minmax_layout = QtWidgets.QHBoxLayout()
        minmax_layout.addWidget(QtWidgets.QLabel('Min:'))
        minmax_layout.addWidget(self.min_safe)
        minmax_layout.addStretch()
        minmax_layout.addWidget(QtWidgets.QLabel('Max:'))
        minmax_layout.addWidget(self.max_safe)
        self.slider_layout.addLayout(minmax_layout)

        self.slider_layout.addWidget(self.range_slider)

        # and wrap them in a widget so we can show/hide more robustly
        self.slider_frame = QtWidgets.QFrame()
        self.slider_frame.setLayout(self.slider_layout)
        self.slider_frame.setVisible(False)


        #self.layout.addLayout(self.slider_layout)



    @QtCore.Slot(bool)
    def toggle_control(self, state):
        if state == True:
            self.toggle_button.setArrowType(QtCore.Qt.DownArrow)
            self.layout.addWidget(self.slider_frame)
            self.slider_frame.setVisible(True)
            self.adjustSize()
        else:
            self.toggle_button.setArrowType(QtCore.Qt.LeftArrow)
            self.layout.removeWidget(self.slider_frame)
            self.slider_frame.setVisible(False)
            self.adjustSize()


    def update_boxes(self, new_values):
        self.min_safe.setValue(new_values[0])
        self.max_safe.setValue(new_values[1])

    @QtCore.Slot(int)
    @QtCore.Slot(float)
    def update_value(self, new_value):

        # stash numerical value
        try:
            new_value = np.clip(new_value, self.abs_range[0], self.abs_range[1])
        except TypeError:
            # if given None, can't clip it.
            # just return
            # TODO: Should this raise an alarm?
            return
        self.value = new_value
        self.check_alarm()

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

    @property
    def alarm_state(self):
        return self._alarm

    @alarm_state.setter
    def alarm_state(self, alarm):
        if alarm == True:
            self.value_label.setStyleSheet(styles.DISPLAY_VALUE_ALARM)
            self.name_label.setStyleSheet(styles.DISPLAY_NAME_ALARM)
            self.units_label.setStyleSheet(styles.DISPLAY_UNITS_ALARM)
            self._alarm = True
        elif alarm == False:
            self.value_label.setStyleSheet(styles.DISPLAY_VALUE)
            self.name_label.setStyleSheet(styles.DISPLAY_NAME)
            self.units_label.setStyleSheet(styles.DISPLAY_UNITS)
            self._alarm = False

    @QtCore.Slot(bool)
    def set_alarm(self, alarm):
        """
        Simple wrapper to set alarm state from a qt signal

        Args:
            alarm (bool): Whether to set as alarm state or not
        """
        self.alarm_state = alarm

    def toggle_alarm(self):

        if self.alarm_state == False:
            self.alarm_state = True
        else:
            self.alarm_state = False

    def check_alarm(self, value=None):
        if value is None:
            value = self.value

        if value:
            if (value > self.max_safe.value()) or (value < self.min_safe.value()):
                self.alarm.emit((self.enum_name, value, time.time()))

                if self.alarm == False:
                    self.toggle_alarm_state(True)
            else:
                if self.alarm == True:
                    self.toggle_alarm_state(False)