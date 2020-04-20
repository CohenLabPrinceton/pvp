import numpy as np
from PySide2 import QtWidgets, QtCore

from vent.gui import styles, mono_font
from vent.gui.widgets.components import RangeSlider


class Monitor_Value(QtWidgets.QWidget):
    alarm = QtCore.Signal()
    limits_changed = QtCore.Signal(tuple)

    def __init__(self, name, units, abs_range, safe_range, decimals, update_period=0.1):
        super(Monitor_Value, self).__init__()

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
        new_value = np.clip(new_value, self.abs_range[0], self.abs_range[1])
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