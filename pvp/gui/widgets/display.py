"""
Unified monitor & control widgets

Display sensor values, control control values, turns out it's all the same
"""

import numpy as np
import time
from PySide2 import QtWidgets, QtCore, QtGui
import PySide2
import pyqtgraph as pg
import os
import sys
import typing

from pvp.gui import styles, mono_font
from pvp.common import message, unit_conversion
from pvp.common.values import ValueName, Value
from pvp.common.message import ControlSetting
from pvp.common.loggers import init_logger
from pvp.common import unit_conversion, prefs
from pvp.gui.widgets.components import EditableLabel, DoubleSlider, QVLine
from pvp.gui.widgets.dialog import pop_dialog

class Display(QtWidgets.QWidget):
    limits_changed = QtCore.Signal(tuple)
    value_changed = QtCore.Signal(float)

    def __init__(self,
                 value: Value,
                 update_period: float = styles.MONITOR_UPDATE_INTERVAL,
                 enum_name: ValueName = None,
                 button_orientation: str = "left",
                 control_type: typing.Union[None, str] = None,
                 style: str="dark",
                 *args, **kwargs):
        """

        Args:
            value (:class:`.Value`): Value Object to display
            update_period (float): time to wait in between updating displayed value
            enum_name (:class:`.ValueName`): Value name (not in Value objects)
            button_orientation (str: 'left' or 'right'): whether the button should be on the left or right
            control_type (None, str: 'slider', 'record'): whether a slider, a button to record recent values, or ``None`` control should be used with this object
            style (str: 'light', 'dark', or a QtStylesheet string): _style for the display
            *args, **kwargs: passed to :class:`PySide2.QtWidgets.QWidget`

        Attributes:
            self.name:
            self.units:
            self.abs_range:
            self.safe_range:
            self.decimals:
            self.update_period:
            self.enum_name:
            self.orientation:
            self.control:
            self._style:
            self.set_value:
            self.sensor_value:
        """

        super(Display, self).__init__(*args, **kwargs)

        # unpack value object
        self.name = value.name
        self.units = value.units
        self.abs_range = value.abs_range
        if not value.safe_range:
            self.safe_range = (0, 0)
        else:
            self.safe_range = value.safe_range
        self.alarm_range = self.safe_range
        self.decimals = value.decimals

        self.logger = init_logger(__name__)

        # store parameters
        self.update_period = update_period
        self.enum_name = enum_name
        self.orientation = button_orientation
        self.control = control_type
        self._style = style
        self._styles = {}

        ## initialize stateful attributes
        # re: unit conversion for Pressure
        self._convert_in = None
        self._convert_out = None
        # for drawing alarm state
        self._alarm_state = False
        # for setting control values by recording recent values
        self._log_values = False
        self._logged_values = []
        # for storing set and sensed values
        self.set_value = None
        self.sensor_value = None
        self._firstset = False # don't pop dialog boxes until the control is brought within the safe range one time
        # for sensor value display
        self._yrange = ()
        # for confirming dangerous values
        self._dialog_open = False
        self._confirmed_unsafe = False
        # for locking controls
        self._locked = False

        # become identifiable
        if self.enum_name:
            self.setObjectName(self.enum_name.name)

        # create graphical objects
        self.init_ui()

        self.timed_update()

    def init_ui(self):
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Minimum)
        self.setMinimumHeight(styles.DISPLAY_MIN_HEIGHT)

        # choose stylesheets
        if self._style == "dark":
            self._styles['main'] = styles.DISPLAY_DARK
            self._styles['label_value'] = styles.DISPLAY_VALUE_DARK
            self._styles['label_name'] = styles.DISPLAY_NAME
            self._styles['label_units'] = styles.DISPLAY_UNITS_DARK
            self._styles['set_value_label'] = styles.CONTROL_VALUE_DARK
            self._styles['slider_label'] = styles.CONTROL_LABEL
            self._styles['line_color'] = styles.DIVIDER_COLOR
            # self._styles['sensor_frame'] = styles.CONTROL_SENSOR_FRAME
        elif self._style == "light":
            self._styles['main'] = styles.DISPLAY_LIGHT
            self._styles['label_value'] = styles.DISPLAY_VALUE_LIGHT
            self._styles['label_name'] = styles.CONTROL_NAME
            self._styles['label_units'] = styles.DISPLAY_UNITS_LIGHT
            self._styles['set_value_label'] = styles.CONTROL_VALUE_LIGHT
            self._styles['slider_label'] = styles.CONTROL_LABEL
            self._styles['line_color'] = styles.DIVIDER_COLOR_DARK
            # self._styles['sensor_frame'] = styles.CONTROL_SENSOR_FRAME
        else:
            raise NotImplementedError('Need to use "light" or "dark" for _style')

        self._styles['label_alarm'] = styles.DISPLAY_VALUE_ALARM

        self.setProperty('widgetClass', 'Display')
        self.setStyleSheet(self._styles['main'])

        # self.setStyleSheet("border: 1px solid black")
        # -----------------------
        # first create all the widgets that we need
        # widgets common to all display objects
        self.init_ui_labels()
        # a toggle button for controls is created whether we control or not
        # (if self.control == None, button is invisible but keeps space for alignment purposes)
        self.init_ui_toggle_button()

        # graphical elements true of all controls
        # if self.control:
        self.init_ui_limits()

        # graphical element specific to control type
        if self.control == "slider":
            self.init_ui_slider()
        elif self.control == "record":
            self.init_ui_record()

        #----------------
        # then lay them out and connect signals
        self.init_ui_layout()
        self.init_ui_signals()

        #--------------
        # and then connect internal signals

    def init_ui_labels(self):
        # label to display measured/sensed values
        self.sensor_label = QtWidgets.QLabel()
        self.sensor_label.setStyleSheet(self._styles['label_value'])
        self.sensor_label.setFont(mono_font())
        self.sensor_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)
        self.sensor_label.setMargin(0)
        self.sensor_label.setContentsMargins(0, 0, 0, 0)
        # at minimum make space for 4 digits
        self.sensor_label.setMinimumWidth(4 * styles.VALUE_SIZE * .6)
        self.sensor_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Minimum)

        # label display value name
        self.name_label = QtWidgets.QLabel()
        self.name_label.setStyleSheet(self._styles['label_name'])
        self.name_label.setText(self.name)
        self.name_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom )
        self.name_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                      QtWidgets.QSizePolicy.Expanding)

        # label to display units
        self.units_label = QtWidgets.QLabel()
        self.units_label.setStyleSheet(self._styles['label_units'])
        self.units_label.setText(self.units)
        self.units_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self.units_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                         QtWidgets.QSizePolicy.Expanding)

    def init_ui_toggle_button(self):
        self.toggle_button = QtWidgets.QToolButton(checkable=True, checked=False)
        self.toggle_button.setStyleSheet(self._styles['label_name'])
        self.toggle_button.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum,
            QtWidgets.QSizePolicy.Expanding)
        self.toggle_button.setMaximumWidth(styles.TOGGLE_MAX_WIDTH)
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonIconOnly
        )

        # make button invisible if no control is set
        if self.control is None:
            button_size_policy = self.toggle_button.sizePolicy()
            button_size_policy.setRetainSizeWhenHidden(True)
            self.toggle_button.setSizePolicy(button_size_policy)
            self.toggle_button.setHidden(True)

    def init_ui_limits(self):
        """
        Create widgets to display sensed value alongside set value
        """

        self.control_vline = QVLine(color=self._styles['line_color'])

        # label to display and edit set value
        self.set_value_label = EditableLabel()
        self.set_value_label.setStyleSheet(self._styles['set_value_label'])
        self.set_value_label.label.setFont(mono_font())
        self.set_value_label.lineEdit.setFont(mono_font())
        self.set_value_label.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.set_value_label.setMinimumWidth(4 * styles.VALUE_MINOR_SIZE * .6)
        self.set_value_label.setContentsMargins(0, 0, 0, 0)
        self.set_value_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                      QtWidgets.QSizePolicy.Maximum)

        # bar graph that indicates current value and limits
        self.sensor_plot = Limits_Plot(style=self._style)

        if self.control is None:
            label_size_policy = self.set_value_label.sizePolicy()
            label_size_policy.setRetainSizeWhenHidden(True)
            self.set_value_label.setSizePolicy(label_size_policy)
            self.set_value_label.setHidden(True)

            plot_size_policy = self.sensor_plot.sizePolicy()
            plot_size_policy.setRetainSizeWhenHidden(True)
            self.sensor_plot.setSizePolicy(plot_size_policy)
            self.sensor_plot.setHidden(True)


    def init_ui_slider(self):
        # -------
        # create toggle button
        # ------
        self.toggle_button.setArrowType(QtCore.Qt.LeftArrow)

        # --------
        # create (initially hidden) slider objects)
        # ---------
        # Min value - slider - max value

        self.slider_layout = QtWidgets.QHBoxLayout()

        self.slider_min = QtWidgets.QLabel()
        self.slider_min.setText(unit_conversion.rounded_string(self.abs_range[0], self.decimals))
        self.slider_min.setAlignment(QtCore.Qt.AlignLeft)
        self.slider_min.setFont(mono_font())
        self.slider_min.setStyleSheet(self._styles['slider_label'])
        self.slider_min.setMargin(0)
        self.slider_min.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                      QtWidgets.QSizePolicy.Maximum)

        self.slider_max = QtWidgets.QLabel()
        self.slider_max.setText(unit_conversion.rounded_string(self.abs_range[1], self.decimals))
        self.slider_max.setAlignment(QtCore.Qt.AlignRight)
        self.slider_max.setFont(mono_font())
        self.slider_max.setStyleSheet(self._styles['slider_label'])
        self.slider_max.setMargin(0)
        self.slider_max.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                      QtWidgets.QSizePolicy.Maximum)

        self.slider = DoubleSlider(decimals=self.decimals, orientation=QtCore.Qt.Orientation.Horizontal)
        self.slider.setMinimum(self.abs_range[0])
        self.slider.setMaximum(self.abs_range[1])
        # self.slider.setContentsMargins(0,0,0,0)
        self.slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Maximum)

        self.slider_layout.addWidget(self.slider_min)
        self.slider_layout.addWidget(self.slider)
        self.slider_layout.addWidget(self.slider_max)

        self.slider_frame = QtWidgets.QFrame()
        self.slider_frame.setLayout(self.slider_layout)
        self.slider_frame.setVisible(False)

    def init_ui_record(self):
        # load record icon
        gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rec_path = os.path.join(gui_dir, 'images', 'record.png')
        image = QtGui.QPixmap(rec_path)
        self.rec_icon = QtGui.QIcon(image)
        self.toggle_button.setIcon(self.rec_icon)

    def init_ui_layout(self):
        """
        Basically two methods... lay objects out depending on whether we're oriented with our button to the left or right
        """
        # main layout is the visible part -- widgets laid out horizontally
        self.main_layout = QtWidgets.QHBoxLayout()
        self.label_layout = QtWidgets.QGridLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        self.label_layout.setContentsMargins(10,0,10,0)


        if self.orientation == "left":

            self.label_layout.addWidget(self.sensor_label, 0, 0, 2, 1, alignment=QtCore.Qt.AlignRight)
            self.label_layout.addWidget(self.name_label, 0, 1, 1, 1, alignment=QtCore.Qt.AlignRight)
            self.label_layout.addWidget(self.units_label, 1, 1, 1, 1, alignment=QtCore.Qt.AlignRight)

            # control objects
            self.main_layout.addWidget(self.toggle_button)
            # if self.control:

            self.main_layout.addWidget(self.sensor_plot)
            self.main_layout.addWidget(self.set_value_label)
            self.main_layout.addWidget(self.control_vline)
            # else:
            #     self.main_layout.addStretch()

            self.main_layout.addLayout(self.label_layout)
        elif self.orientation == "right":

            # labels are always laid out the same becuse numbers have to be aligned right...
            self.label_layout.addWidget(self.sensor_label, 0, 1, 2, 1, alignment=QtCore.Qt.AlignRight)
            self.label_layout.addWidget(self.name_label, 0, 0, 1, 1, alignment=QtCore.Qt.AlignLeft)
            self.label_layout.addWidget(self.units_label, 1, 0, 1, 1, alignment=QtCore.Qt.AlignLeft)

            self.main_layout.addLayout(self.label_layout)

            # control objects
            # if self.control:
            self.main_layout.addWidget(self.control_vline)
            self.main_layout.addWidget(self.set_value_label)
            self.main_layout.addWidget(self.sensor_plot)
            # else:
            #     self.main_layout.addStretch()
            self.main_layout.addWidget(self.toggle_button)

        self.layout.addLayout(self.main_layout)



    def init_ui_signals(self):

        if self.control:
            self.set_value_label.textChanged.connect(self._value_changed)

        if self.control == "slider":
            self.toggle_button.toggled.connect(self.toggle_control)
            self.slider.doubleValueChanged.connect(self._value_changed)
        elif self.control == "record":
            self.toggle_button.toggled.connect(self.toggle_record)

    @QtCore.Slot(bool)
    def toggle_control(self, state):
        if self.control != 'slider':
            return
        if state == True:
            self.toggle_button.setArrowType(QtCore.Qt.DownArrow)
            # self.layout.addWidget(self.slider_frame, 3, 0, 1, 3)
            self.layout.addWidget(self.slider_frame)
            self.slider_frame.setVisible(True)
            # self.adjustSize()
        else:
            self.toggle_button.setArrowType(QtCore.Qt.LeftArrow)
            self.layout.removeWidget(self.slider_frame)
            self.slider_frame.setVisible(False)
            self.adjustSize()

    def toggle_record(self, state):
        if self.control != 'record':
            return
        if state:
            self._log_values = True
            self._logged_values = []

            self.toggle_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))
            self.sensor_label.setStyleSheet(styles.CONTROL_VALUE_REC)
            self.name_label.setStyleSheet(styles.CONTROL_NAME_REC)
            self.units_label.setStyleSheet(styles.CONTROL_UNITS_REC)

        else:
            if len(self._logged_values)>0:
                # get the mean logged value
                mean_val = np.mean(self._logged_values)
                # convert to displayed range if necessary (_value_changed) expects it
                if self._convert_in:
                    mean_val = self._convert_in(mean_val)

                self._value_changed(mean_val)

            self.toggle_button.setIcon(self.rec_icon)
            self.sensor_label.setStyleSheet(self._styles['label_value'])
            self.name_label.setStyleSheet(self._styles['label_name'])
            self.units_label.setStyleSheet(self._styles['label_units'])

    def _value_changed(self, new_value: float):
        """
        "outward-directed" Control value changed by components

        Args:
            new_value (float):
            emit (bool): whether to emit the `value_changed` signal (default True) -- in the case that our value is being changed by someone other than us
        """
        # pdb.set_trace()
        if isinstance(new_value, str):
            new_value = float(new_value)

        # stash unconverted value for use in dialog messages
        orig_value = new_value

        if self._convert_out:
            # convert from display value to internal value
            new_value = self._convert_out(new_value)

        if (new_value > self.safe_range[1]) or (new_value < self.safe_range[0]):
            if self._dialog_open: # pragma: no cover
                # if we're already opening a dialogue, don't try to set value or emit
                return

            if (not self._confirmed_unsafe) and \
               ('pytest' not in sys.modules) and \
                prefs.get_pref('ENABLE_WARNINGS') and \
                self._firstset: # pragma: no cover

                self._dialog_open = True
                safe_range = self.safe_range
                if self._convert_in:
                    safe_range = (self._convert_in(safe_range[0]), self._convert_in(safe_range[1]))

                dialog = pop_dialog(
                    message = f'Confirm setting potentially unsafe {self.name} value',
                    sub_message= f'Values of {self.name} outside of {self.safe_range[0]}-{self.safe_range[1]} {self.units} are usually unsafe.\n\nAre you sure you want to set {self.name} to {orig_value} {self.units}',
                    buttons =  QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Ok,
                    default_button =  QtWidgets.QMessageBox.Cancel
                )
                ret = dialog.exec_()
                self._dialog_open = False
                if ret != QtWidgets.QMessageBox.Ok:
                    # if canceled, set value to current value
                    new_value = self.set_value
                else:
                    # don't prompt again
                    self._confirmed_unsafe = True

        else:
            # reset _confirmed_unsafe if back in range
            if self._confirmed_unsafe:
                self._confirmed_unsafe = False

            # set firstset flag if we're going in safe range for the first time
            if not self._firstset:
                self._firstset = True

        changed = self.update_set_value(new_value)
        if changed:
            self.value_changed.emit(self.set_value)

    def update_set_value(self, new_value: float):
        """inward value setting (set from elsewhere)"""

        if isinstance(new_value, str):
            new_value = float(new_value)

        # don't convert value here,
        # assume the only hPa values would come from the widget itself since it's display only

        changed = False
        if (new_value <= self.abs_range[1]) and (new_value >= self.abs_range[0]):
            if (new_value != self.set_value):
                self.set_value = new_value
                changed = True
        else:
            self.logger.exception(f'Attempted to set {self.name} out of range ({self.abs_range}) with value {new_value}')

        if changed:

            self.redraw()
        return changed

    def update_sensor_value(self, new_value: float):
        if new_value is None:
            return

        self.sensor_value = new_value

        # store values to set value by averaging sensor values
        if self._log_values:
            self._logged_values.append(new_value)

        if self._convert_in:
            new_value = self._convert_in(new_value)

        value_str = unit_conversion.rounded_string(new_value, self.decimals)
        # self.sensor_label.setText(value_str)
        if self.control:
            self.sensor_plot.update_value(sensor_value = new_value)

    def update_limits(self, control: ControlSetting):
        """
        Update the alarm range and the GUI elements corresponding to it

        Args:
            control (:class:`~.ControlSetting`): control setting with min_value or max_value
        """
        if self.control is None:
            return

        if control.min_value:
            if self._convert_in:
                self.sensor_plot.update_value(min=self._convert_in(control.min_value))
            else:
                self.sensor_plot.update_value(min=control.min_value)
            self.alarm_range = (control.min_value, self.alarm_range[1])

        if control.max_value:
            if self._convert_in:
                self.sensor_plot.update_value(max=self._convert_in(control.max_value))
            else:
                self.sensor_plot.update_value(max=control.max_value)
            self.alarm_range = (self.alarm_range[0], control.max_value)

    def redraw(self):
        """
        Redraw all graphical elements to ensure internal model matches view
        """
        # convert some guaranteed values
        abs_range = self.abs_range
        if self._convert_in:
            abs_range = (self._convert_in(x) for x in abs_range)

        # sensor value
        if self.sensor_value:
            sensor_value = self.sensor_value
            if self._convert_in:
                sensor_value = self._convert_in(sensor_value)

            # don't update sensor value label, it should be on timed update
            # just make sure the sensor bar is correct
            if self.control:
                self.sensor_plot.update_value(sensor_value=sensor_value)

        # set value
        if self.set_value:
            set_value = self.set_value
            if self._convert_in:
                set_value = self._convert_in(set_value)

            # update label and plot
            if self.control:
                set_value_str = unit_conversion.rounded_string(set_value, self.decimals)
                self.set_value_label.setText(set_value_str)

                self.sensor_plot.update_value(set_value=set_value)

                if self.control == "slider":
                    try:
                        self.slider.blockSignals(True)
                        self.slider.setValue(set_value)
                        self.slider.setMinimum(abs_range[0])
                        self.slider.setMaximum(abs_range[1])
                        self.slider.setDecimals(self.decimals)
                        self.slider_min.setText(unit_conversion.rounded_string(abs_range[0], self.decimals))
                        self.slider_max.setText(unit_conversion.rounded_string(abs_range[1], self.decimals))
                    finally:
                        self.slider.blockSignals(False)

        # alarm limits
        if self.alarm_range:
            alarm_range = self.alarm_range
            if self._convert_in:
                alarm_range = (self._convert_in(x) for x in alarm_range)
            self.sensor_plot.update_value(min=alarm_range[0], max=alarm_range[1])


    def timed_update(self):
        # format value based on decimals
        try:
            if self.sensor_value:
                if self._convert_in:
                    sensor_value = self._convert_in(self.sensor_value)
                else:
                    sensor_value = self.sensor_value
                value_str = unit_conversion.rounded_string(sensor_value, self.decimals)
                self.sensor_label.setText(value_str)
        except Exception as e:
            self.logger.exception(f"{self.name} - error in timed update - {e}")
        finally:
            QtCore.QTimer.singleShot(round(self.update_period*1000), self.timed_update)



    def set_units(self, units: str):
        """
        Set pressure units to display as cmH2O or hPa

        Args:
            units ('cmH2O', 'hPa'):
        """
        if self.name in (ValueName.PIP.name, ValueName.PEEP.name):
            if units == 'cmH2O':
                self.decimals = 1
                self._convert_in = None
                self._convert_out = None
                self.sensor_plot._convert_in = None
                self.sensor_plot._convert_out = None

            elif units == 'hPa':
                self.decimals = 0
                self._convert_in = unit_conversion.cmH2O_to_hPa
                self._convert_out = unit_conversion.hPa_to_cmH2O
                self.sensor_plot._convert_in = unit_conversion.cmH2O_to_hPa
                self.sensor_plot._convert_out = unit_conversion.hPa_to_cmH2O

            else:
                self.logger.exception(f'couldnt set units {units}')
                return

            self.units = units
            self.units_label.setText(units)
            self.redraw()

        else:
            self.logger.exception(f'error setting units {self.name} - {units}')


    def set_locked(self, locked: bool):
        if locked:
            self.locked = True
            if self.control:
                if self.control == "slider":
                    self.toggle_control(False)
                self.toggle_button.setEnabled(False)
                self.set_value_label.setEditable(False)
            # self.setStyleSheet()
        else:
            self.locked = False
            if self.control:
                self.toggle_button.setEnabled(True)
                self.set_value_label.setEditable(True)
    # ---------------------------------
    # Properties
    # ---------------------------------
    @property
    def is_set(self):
        if self.set_value is None:
            return False
        else:
            return True

    @property
    def alarm_state(self):
        return self._alarm_state

    @alarm_state.setter
    def alarm_state(self, alarm_state):
        if alarm_state:
            self.sensor_label.setStyleSheet(self._styles['label_alarm'])
        else:
            self.sensor_label.setStyleSheet(self._styles['label_value'])

        self._alarm_state = alarm_state




class Limits_Plot(pg.PlotWidget):
    """
    Widget to display current value in a bar graph along with alarm limits
    """

    def __init__(self, style:str="light", *args, **kwargs):
        self.set_value = None
        self.sensor_value = None
        self._minimum = None
        self._maximum = None
        self._style = style
        self.yrange = (0, 1)

        self._convert_in = None
        self._convert_out = None

        if self._style == "light":
            super(Limits_Plot, self).__init__(background=styles.CONTROL_SENSOR_BACKGROUND_LIGHT, *args, **kwargs)
        elif self._style == "dark":
            super(Limits_Plot, self).__init__(background=styles.CONTROL_SENSOR_BACKGROUND_DARK, *args, **kwargs)


        self.init_ui()

    def init_ui(self):
        # bar graph that's an indicator of current value

        self.getPlotItem().hideAxis('bottom')
        self.getPlotItem().hideAxis('left')
        self.setRange(xRange=(-0.5, 0.5))

        # bar itself
        # if self._style == "light:"
        self.sensor_bar = pg.BarGraphItem(x=np.array([0]), y1=np.array([0]), width=np.array([1]),
                                          brush=styles.SENSOR_BAR_COLOR)

        # error bars for limit indicators
        self.top_limit = pg.InfiniteLine(movable=False, angle=0, pos=0,
                                         pen={
                                                 'color': styles.SUBWAY_COLORS['red'],
                                                 'width': 2
                                             },
                                         label='{value:0.1f}',
                                         labelOpts = {
                                            'color': styles.SUBWAY_COLORS['red']
                                        })
        self.bottom_limit = pg.InfiniteLine(movable=False, angle=0, pos=0,
                                            pen={
                                                 'color': styles.SUBWAY_COLORS['red'],
                                                 'width': 2
                                             },
                                            label='{value:0.1f}',
                                            labelOpts={
                                                'color': styles.SUBWAY_COLORS['red']
                                            })

        # the set value
        if self._style == "light":
            self.sensor_set = pg.InfiniteLine(movable=False, angle=0, pos=0,
                                              pen={'color': styles.BACKGROUND_COLOR, 'width': 5})
        elif self._style == "dark":
            self.sensor_set = pg.InfiniteLine(movable=False, angle=0, pos=0,
                                              pen={'color': styles.TEXT_COLOR, 'width': 5})


        self.addItem(self.sensor_bar)
        self.addItem(self.top_limit)
        self.addItem(self.bottom_limit)
        self.addItem(self.sensor_set)
        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                           QtWidgets.QSizePolicy.Minimum)
        self.plotItem.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                      QtWidgets.QSizePolicy.Minimum)
        # self.set
        self.setFixedWidth(styles.CONTROL_SENSOR_BAR_WIDTH)
        # self.setFixedHeight(styles.CONTROL_SENSOR_BAR_WIDTH)

        # self.enableAutoRange(y=True)
        self.update_yrange()

    def update_value(self,
                     min: float = None,
                     max: float = None,
                     sensor_value: float = None,
                     set_value: float = None):
        """
        Move the lines! Pass any of the represented values

        Args:
            min (float): new alarm minimum
            max (float): new alarm _maximum
            sensor_value (float): new value for the sensor bar plot
            set_value (float): new value for the set value line

        """
        if min:
            self.bottom_limit.setValue(float(min))
            self._minimum = float(min)

        if max:
            self.top_limit.setValue(float(max))
            self._maximum = float(max)

        if sensor_value:
            self.sensor_bar.setOpts(y1=np.array([float(sensor_value)]))
            self.sensor_value = float(sensor_value)

        if set_value:
            self.sensor_set.setValue(float(set_value))
            self.set_value = float(set_value)


        self.update_yrange()

    def update_yrange(self):
        if self.set_value:
            # put set_value in the middle, add space above and below to fit alarms
            min_dist = 0
            max_dist = 0
            sensor_dist = 0
            if self._minimum:
                min_dist = np.abs(self.set_value-self._minimum)
            if self._maximum:
                max_dist = np.abs(self.set_value-self._maximum)
            if self.sensor_value:
                sensor_dist = np.abs(self.set_value-self.sensor_value)

            dist = np.max([min_dist, max_dist])
            self.setYRange(self.set_value-dist, self.set_value+dist)
        else:
            self.setYRange(0,0)




