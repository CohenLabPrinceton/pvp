import numpy as np
from PySide2 import QtWidgets, QtCore

from vent.gui import styles, mono_font
from vent.gui.widgets.components import RangeSlider


class Monitor_Value(QtWidgets.QWidget):
    alarm = QtCore.Signal()
    limits_changed = QtCore.Signal(tuple)

    def __init__(self, value, update_period=0.1):
        """

        Args:
            value (:class:`~vent.values.Value`):
            update_period (float): update period of monitor in s
        """
        super(Monitor_Value, self).__init__()

        self.name = value.name
        self.units = value.units
        self.abs_range = value.abs_range
        self.safe_range = value.safe_range
        self.decimals = value.decimals
        self.update_period = update_period

        self.value = None

        self.init_ui()

        self.timed_update()

    def init_ui(self):
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        #########
        # create widgets
        # make range slider
        self.range_slider = RangeSlider(self.abs_range, self.safe_range,
                                        orientation=QtCore.Qt.Orientation.Horizontal)

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
        self.value_label.setFont(mono_font())
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
        self.toggle_button.setArrowType(QtCore.Qt.LeftArrow)

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
        minmax_layout.addWidget(QtWidgets.QLabel('Max:'))
        minmax_layout.addWidget(self.max_safe)
        minmax_layout.addStretch()
        minmax_layout.addWidget(QtWidgets.QLabel('Min:'))
        minmax_layout.addWidget(self.min_safe)
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

        self.value = new_value
        self.check_alarm()
        new_value = np.clip(new_value, self.abs_range[0], self.abs_range[1])
        #self.range_slider.update_indicator(new_value)

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