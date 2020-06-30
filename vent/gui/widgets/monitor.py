import numpy as np
import time
from PySide2 import QtWidgets, QtCore, QtGui
import os

from vent.gui import styles, mono_font
from vent.gui.widgets.components import RangeSlider
from vent.common import message, unit_conversion
from vent.common.values import ValueName, Value


class Monitor(QtWidgets.QWidget):
    alarm = QtCore.Signal(tuple)
    limits_changed = QtCore.Signal(tuple)
    set_value_changed = QtCore.Signal(float)

    def __init__(self, value: Value,
                 update_period=styles.MONITOR_UPDATE_INTERVAL,
                 enum_name = None,
                 alarm_limits = False):
        """

        Args:
            value (:class:`~vent.values.Value`):
            update_period (float): update period of monitor in s
            range_slider (bool): whether this monitor should have a :class:`.RangeSlider` to set alarm limits
        """
        super(Monitor, self).__init__()

        self.name = value.name
        self.units = value.units
        self.abs_range = value.abs_range
        self.safe_range = value.safe_range
        self.decimals = value.decimals
        self.update_period = update_period
        self.enum_name = enum_name
        self.has_alarm_limits = alarm_limits

        self.setObjectName(self.enum_name.name)

        self.value = None

        self._convert_in = None
        self._convert_out = None

        # whether we are currently styled as being in an alarm state
        self._alarm = False

        #############
        # handling setting VTE/FIO2 which has to be recorded and logged rather than parametricalyl set
        self.log_values = False
        self.logged_values = []

        self.init_ui()

        self.timed_update()

    def init_ui(self):
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        #########
        # create widgets


        # labels to display values
        self.value_label = QtWidgets.QLabel()
        self.value_label.setStyleSheet(styles.DISPLAY_VALUE)
        self.value_label.setFont(mono_font())
        self.value_label.setAlignment(QtCore.Qt.AlignRight)
        self.value_label.setMargin(0)
        self.value_label.setContentsMargins(0,0,0,0)
        # at minimum make space for 4 digits
        self.value_label.setMinimumWidth(4 * styles.VALUE_SIZE * .6)
        self.value_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                       QtWidgets.QSizePolicy.Minimum)

        self.name_label = QtWidgets.QLabel()
        self.name_label.setStyleSheet(styles.DISPLAY_NAME)
        self.name_label.setText(self.name)
        self.name_label.setAlignment(QtCore.Qt.AlignRight)
        self.name_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                      QtWidgets.QSizePolicy.Expanding)


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
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonIconOnly
        )
        self.toggle_button.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                         QtWidgets.QSizePolicy.Expanding)

        # make range slider
        if self.has_alarm_limits:
            # first connect button
            self.toggle_button.toggled.connect(self.toggle_record)

            # load record icon
            gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rec_path = os.path.join(gui_dir, 'images', 'record.png')
            image = QtGui.QPixmap(rec_path)
            self.rec_icon = QtGui.QIcon(image)
            self.toggle_button.setIcon(self.rec_icon)
        else:
            # make toggle button invisible but retain space if no rangeslider
            button_size_policy = self.toggle_button.sizePolicy()
            button_size_policy.setRetainSizeWhenHidden(True)
            self.toggle_button.setSizePolicy(button_size_policy)
            self.toggle_button.setHidden(True)


        # #########
        # # layout widgets
        #
        # first make label layout
        label_layout = QtWidgets.QGridLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)
        # if self.has_alarm_limits:
        label_layout.addWidget(self.toggle_button, 0, 0, 2, 1)
        label_layout.addWidget(self.value_label, 0, 1, 2, 1, alignment=QtCore.Qt.AlignRight)
        label_layout.addWidget(self.name_label, 0, 2, 1, 1, alignment=QtCore.Qt.AlignRight)
        label_layout.addWidget(self.units_label, 1, 2, 1, 1, alignment=QtCore.Qt.AlignRight)
        # label_layout.addStretch()
        self.layout.addLayout(label_layout, 5)






    @QtCore.Slot(bool)
    def toggle_control(self, state):
        if self.has_alarm_limits:
            return
        if state == True:
            self.toggle_button.setArrowType(QtCore.Qt.DownArrow)
            self.layout.addWidget(self.slider_frame)
            self.slider_frame.setVisible(True)
            self.adjustSize()
        else:
            self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
            self.layout.removeWidget(self.slider_frame)
            self.slider_frame.setVisible(False)
            self.adjustSize()

    def toggle_record(self, state):
        if state == True:
            self.log_values = True
            self.logged_values = []

            self.alarm_state = True
            self.toggle_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))


        else:
            if len(self.logged_values)>0:
                # get the mean logged value
                mean_val = np.mean(self.logged_values)
                self.set_value_changed.emit((mean_val))

            self.toggle_button.setIcon(self.rec_icon)
            self.alarm_state = False


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
        if self.log_values:
            self.logged_values.append(new_value)
        #self.check_alarm()

    @QtCore.Slot(tuple)
    def update_limits(self, new_limits):
        self.range_slider.setLow(new_limits[0])
        self.range_slider.setHigh(new_limits[1])
        self.update_boxes(new_limits)

    def timed_update(self):
        # format value based on decimals
        if self.value:
            if self._convert_in:
                set_value = self._convert_in(self.value)
            else:
                set_value = self.value
            value_str = unit_conversion.rounded_string(set_value, self.decimals)
            self.value_label.setText(value_str)

        QtCore.QTimer.singleShot(round(self.update_period*1000), self.timed_update)

    def _limits_changed(self, val):
        # ignore value, just emit changes and check alarm
        #self.check_alarm()
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

    def set_units(self, units):
        if self.name in ('Pressure',):
            if units == 'cmH2O':
                self.decimals = 1
                self.units = units
                self.units_label.setText(units)
                self._convert_in = None
                self._convert_out = None
            elif units == 'hPa':
                self.decimals = 0
                self.units = units
                self.units_label.setText(units)
                self._convert_in = unit_conversion.cmH2O_to_hPa
                self._convert_out = unit_conversion.hPa_to_cmH2O
        else:
            print(
                f'error setting units {units}'
            )
            return


    # def check_alarm(self, value=None):
    #     if value is None:
    #         value = self.value
    #
    #     if value:
    #         if (value > self.max_safe.value()) or (value < self.min_safe.value()):
    #             self.alarm.emit((self.enum_name, value, time.time()))
    #
    #             if self.alarm == False:
    #                 self.toggle_alarm_state(True)
    #         else:
    #             if self.alarm == True:
    #                 self.toggle_alarm_state(False)