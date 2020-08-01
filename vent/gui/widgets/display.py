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

from vent.gui import styles, mono_font
from vent.common import message, unit_conversion
from vent.common.values import ValueName, Value
from vent.common.message import ControlSetting
from vent.common import unit_conversion, prefs
from vent.gui.widgets.components import EditableLabel, DoubleSlider
from vent.gui.widgets.dialog import pop_dialog



class Display(QtWidgets.QWidget):
    limits_changed = QtCore.Signal(tuple)
    value_changed = QtCore.Signal(float)

    def __init__(self,
                 value: Value,
                 update_period: float = styles.MONITOR_UPDATE_INTERVAL,
                 enum_name: ValueName = None,
                 button_orientation: str = "left",
                 control: typing.Union[None, str] = None,
                 style: str="dark",
                 *args, **kwargs):
        """

        Args:
            value (:class:`.Value`): Value Object to display
            update_period (float): time to wait in between updating displayed value
            enum_name (:class:`.ValueName`): Value name (not in Value objects)
            button_orientation (str: 'left' or 'right'): whether the button should be on the left or right
            control_type (None, str: 'slider', 'record'): whether a slider, a button to record recent values, or ``None`` control should be used with this object
            style (str: 'light', 'dark', or a QtStylesheet string): style for the display
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
            self.style:
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

        # store parameters
        self.update_period = update_period
        self.enum_name = enum_name
        self.orientation = button_orientation
        self.control = control
        self.style = style
        self._styles = {}

        ## initialize stateful attributes
        # re: unit conversion for Pressure
        self._convert_in = None
        self._convert_out = None
        # for drawing alarm state
        self._alarm = False
        # for setting control values by recording recent values
        self._log_values = False
        self._logged_values = []
        # for storing set and sensed values
        self.set_value = None
        self.sensor_value = None
        # for sensor value display
        self._yrange = ()
        # for confirming dangerous values
        self._dialog_open = False
        self._confirmed_unsafe = False
        # for locking controls
        self._locked = False

        # become identifiable
        if self.enum_name:
            self.setObjectName(self.enum_name)

        # create graphical objects
        self.init_ui()

    def init_ui(self):
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Maximum)

        # choose stylesheets
        if self.style == "dark":
            self._styles['label_value'] = styles.DISPLAY_VALUE
            self._styles['label_name'] = styles.DISPLAY_NAME
            self._styles['label_units'] = styles.DISPLAY_UNITS
            self._styles['control_label'] = styles.CONTROL_VALUE
            self._styles['slider_label'] = styles.CONTROL_LABEL
            # self._styles['sensor_frame'] = styles.CONTROL_SENSOR_FRAME
        elif self.style == "light":
            self._styles['label_value'] = styles.CONTROL_VALUE
            self._styles['label_name'] = styles.CONTROL_NAME
            self._styles['label_units'] = styles.CONTROL_UNITS
            self._styles['control_label'] = styles.CONTROL_VALUE
            self._styles['slider_label'] = styles.CONTROL_LABEL
            # self._styles['sensor_frame'] = styles.CONTROL_SENSOR_FRAME
        else:
            raise NotImplementedError('Need to use "light" or "dark" for style')

        # -----------------------
        # first create all the widgets that we need
        # widgets common to all display objects
        self.init_ui_labels()
        # a toggle button for controls is created whether we control or not
        # (if self.control == None, button is invisible but keeps space for alignment purposes)
        self.init_ui_toggle_button()

        # graphical elements true of all controls
        if self.control:
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
        self.sensor_label.setAlignment(QtCore.Qt.AlignRight)
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
        self.name_label.setAlignment(QtCore.Qt.AlignRight)
        self.name_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
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
        # frame to enclose all elements
        # self.sensor_frame = QtWidgets.QFrame()
        # self.sensor_frame.setStyleSheet(self._styles['sensor_frame'])
        # self.sensor_frame.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
        #                                 QtWidgets.QSizePolicy.Maximum)
        #self.sensor_layout = QtWidgets.QHBoxLayout()
        # self.sensor_layout.setContentsMargins(0,0,0,0)

        # label to display and edit set value
        self.control_label = EditableLabel()
        self.control_label.setStyleSheet(self._styles['control_label'])
        self.control_label.label.setFont(mono_font())
        self.control_label.lineEdit.setFont(mono_font())
        self.control_label.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.control_label.setMinimumWidth(4 * styles.VALUE_MINOR_SIZE * .6)
        self.control_label.setContentsMargins(0,0,0,0)

        # bar graph that indicates current value and limits
        self.sensor_plot = Limits_Plot()



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
        self.label_layout.setContentsMargins(0,0,0,0)

        # labels are always laid out the same becuse numbers have to be aligned right...
        self.label_layout.addWidget(self.sensor_label, 0, 0, 2, 1, alignment=QtCore.Qt.AlignRight)
        self.label_layout.addWidget(self.name_label, 0, 1, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.label_layout.addWidget(self.units_label, 1, 1, 1, 1, alignment=QtCore.Qt.AlignRight)

        if self.orientation == "left":
            # control objects
            self.main_layout.addWidget(self.toggle_button)
            if self.control:
                self.main_layout.addWidget(self.sensor_plot)
                self.main_layout.addWidget(self.control_label)
            else:
                self.main_layout.addStretch()

            self.main_layout.addLayout(self.label_layout)
        elif self.orientation == "right":
            self.main_layout.addLayout(self.label_layout)

            # control objects
            if self.control:
                self.main_layout.addWidget(self.sensor_plot)
                self.main_layout.addWidget(self.control_label)
            else:
                self.main_layout.addStretch()
            self.main_layout.addWidget(self.toggle_button)

        self.layout.addLayout(self.main_layout)



    def init_ui_signals(self):

        if self.control:
            self.control_label.textChanged.connect(self._value_changed)

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
        if state == True:
            self.log_values = True
            self.logged_values = []

            self.toggle_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))
            self.sensor_label.setStyleSheet(styles.CONTROL_VALUE_REC)
            self.name_label.setStyleSheet(styles.CONTROL_NAME_REC)
            self.units_label.setStyleSheet(styles.CONTROL_UNITS_REC)

        else:
            if len(self.logged_values)>0:
                # get the mean logged value
                mean_val = np.mean(self.logged_values)
                # convert to displayed range if necessary (_value_changed) expects it
                if self._convert_in:
                    mean_val = self._convert_in(mean_val)

                self._value_changed(mean_val)

            self.toggle_button.setIcon(self.rec_icon)
            self.sensor_label.setStyleSheet(styles.CONTROL_VALUE)
            self.name_label.setStyleSheet(styles.CONTROL_NAME)
            self.units_label.setStyleSheet(styles.CONTROL_UNITS)


    def _value_changed(self, new_value: float):
        """
        Control value changed by components

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
            if self._dialog_open:
                # if we're already opening a dialogue, don't try to set value or emit
                return

            if (not self._confirmed_unsafe) and ('pytest' not in sys.modules) and prefs.get_pref('ENABLE_WARNINGS'):

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
                    new_value = self.value
                else:
                    # don't prompt again
                    self._confirmed_unsafe = True


        else:
            # reset _confirmed_unsafe if back in range
            if self._confirmed_unsafe:
                self._confirmed_unsafe = False




        changed = self.update_value(new_value)
        if changed:
            self.value_changed.emit(self.value)







class Limits_Plot(pg.PlotWidget):
    """
    Widget to display current value in a bar graph along with alarm limits
    """

    def __init__(self, background = styles.CONTROL_SENSOR_BACKGROUND, *args, **kwaargs):
        super(Limits_Plot, self).__init__(background=background, *args, **kwargs)

        self.init_ui()

    def init_ui(self):
        # bar graph that's an indicator of current value

        self.getPlotItem().hideAxis('bottom')
        self.getPlotItem().hideAxis('left')
        self.setRange(xRange=(-0.5, 0.5))

        # bar itself
        self.sensor_bar = pg.BarGraphItem(x=np.array([0]), y1=np.array([0]), width=np.array([1]),
                                          brush=styles.GRAY_TEXT)

        # error bars for limit indicators
        self.top_limit = pg.InfiniteLine(movable=False, angle=0, pos=1,
                                         pen={
                                                 'color': styles.SUBWAY_COLORS['red'],
                                                 'width': 2
                                             })
        self.bottom_limit = pg.InfiniteLine(movable=False, angle=0, pos=0,
                                            pen={
                                                 'color': styles.SUBWAY_COLORS['red'],
                                                 'width': 2
                                             })

        # the set value
        self.sensor_set = pg.InfiniteLine(movable=False, angle=0, pos=0.5,
                                          pen={'color': styles.BACKGROUND_COLOR, 'width': 5})

        self.addItem(self.sensor_bar)
        self.addItem(self.sensor_limits)
        self.addItem(self.sensor_set)
        self.setFixedWidth(styles.CONTROL_SENSOR_BAR_WIDTH)








