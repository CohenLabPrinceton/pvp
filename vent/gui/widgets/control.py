import numpy as np
from PySide2 import QtWidgets, QtCore, QtGui
import PySide2
import pyqtgraph as pg
import pdb
import sys
import os

from vent.gui import styles, mono_font
from vent.gui.widgets.components import EditableLabel, DoubleSlider
from vent.gui.widgets.dialog import pop_dialog
from vent.common.message import ControlSetting
from vent.common.values import Value, ValueName
from vent.common import unit_conversion


class Control(QtWidgets.QWidget):
    """
    Attributes:
        sensor (int, float): Value from the sensor
        _confirmed_unsafe (bool): the user is prompted to confirm setting values outside of ``safe_range``
            once the user confirms, the user is not prompted again until value is set back inside the safe range.
            stores whether the user has confirmed.
    """

    value_changed = QtCore.Signal(float)
    limits_changed = QtCore.Signal(tuple)

    def __init__(self, value: Value, set_default: bool = False):
        super(Control, self).__init__()

        self.name = value.name
        self.units = value.units
        self.abs_range = value.abs_range
        if not value.safe_range:
            self.safe_range = (0, 0)
        else:
            self.safe_range = value.safe_range
        self.alarm_range = self.safe_range
        if set_default:
            self.value = value.default
        else:
            self.value = None
        self.decimals = value.decimals
        self.sensor = None
        self.sensor_value = None
        self.yrange = ()

        self._convert_in = None
        self._convert_out = None

        self._dialog_open = False
        self._confirmed_unsafe = False

        self._locked = False

        #############
        # handling setting PEEP which has to be recorded and logged rather than parametricalyl set
        self.log_values = False
        self.logged_values = []

        self.init_ui()


    def init_ui(self):
        # self.layout = QtWidgets.QGridLayout()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(5,0,5,0)
        self.setLayout(self.layout)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                           QtWidgets.QSizePolicy.Maximum)


        # Value, Controller
        #        min,   max
        # Name
        # Units

        # # set max size based on range
        # #n_ints = len(str(self.abs_range[1]))
        # n_ints = 3
        if self.decimals > 0:
            # don't just add decimals b/c we add another for the decimal itself
            # but don't want to +1 if decimals = 0!
            n_ints = int(len(str(self.abs_range[1]))+self.decimals+1)
        else:
            n_ints = int(len(str(self.abs_range[1])))

        # to simplify things for now, if we're supposed to display _more_
        # than the 5 we assume (eg. 100.0), then use the n_ints
        # otherwise just use 5
        if n_ints <= 4:
            n_ints = 4

        ###########
        # if we were not initialized with a default value, set value *visually* to not be displayed
        if self.value is None:
            init_value = 0
            init_low = 0
            init_high = 0
        else:
            init_value = self.value
            init_low = self.value - self.alarm_range[0]
            init_high = self.alarm_range[1] - self.value

        ########
        # Sensor box
        self.sensor_frame = QtWidgets.QFrame()
        self.sensor_frame.setStyleSheet(styles.CONTROL_SENSOR_FRAME)
        self.sensor_frame.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                        QtWidgets.QSizePolicy.Maximum)
        self.sensor_layout = QtWidgets.QHBoxLayout()
        # self.sensor_layout.setContentsMargins(0,0,0,0)


        self.sensor_label = QtWidgets.QLabel()
        self.sensor_label.setStyleSheet(styles.CONTROL_SENSOR_LABEL)
        self.sensor_label.setFont(mono_font())
        self.sensor_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.sensor_label.setFixedWidth(n_ints * styles.VALUE_MINOR_SIZE * .6)

        # bar graph that's an indicator of current value
        self.sensor_plot = pg.PlotWidget(background=styles.CONTROL_SENSOR_BACKGROUND)
        # self.sensor_plot = pg.PlotWidget()
        self.sensor_plot.getPlotItem().hideAxis('bottom')
        self.sensor_plot.getPlotItem().hideAxis('left')
        self.sensor_plot.setRange(xRange=(-0.5, 0.5))
        #self.sensor_plot.enableAutoRange(y=True)
        #self.sensor_plot.autoRange(padding=.001)
        # self.sensor_plot.enableAutoRange()

        # bar itself
        self.sensor_bar = pg.BarGraphItem(x=np.array([0]), y1=np.array([0]), width=np.array([1]), brush=styles.GRAY_TEXT)

        # error bars for limit indicators
        self.sensor_limits = pg.ErrorBarItem(beam=1, x=np.array([0]), y=np.array([init_value]),
                                             top=init_high,
                                             bottom=init_low,
                                             pen={
                                                 'color':styles.SUBWAY_COLORS['red'],
                                                 'width':2
                                             })

        # the set value
        self.sensor_set = pg.InfiniteLine(movable=False, angle=0, pos=init_value,
                                          pen={'color':styles.BACKGROUND_COLOR, 'width':5})


        self.sensor_plot.addItem(self.sensor_bar)
        self.sensor_plot.addItem(self.sensor_limits)
        self.sensor_plot.addItem(self.sensor_set)
        self.sensor_plot.setFixedWidth(styles.CONTROL_SENSOR_BAR_WIDTH)

        self.sensor_layout.addWidget(self.sensor_label)
        self.sensor_layout.addWidget(self.sensor_plot)
        self.sensor_frame.setLayout(self.sensor_layout)



        self.value_label = EditableLabel()
        self.value_label.setStyleSheet(styles.CONTROL_VALUE)
        self.value_label.label.setFont(mono_font())
        self.value_label.lineEdit.setFont(mono_font())
        self.value_label.label.setAlignment(QtCore.Qt.AlignRight)
        #self.value_label.setMargin(0)
        self.value_label.setContentsMargins(0,0,0,0)


        self.value_label.setMinimumWidth(n_ints*styles.VALUE_SIZE*.6)
        self.value_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                         QtWidgets.QSizePolicy.Maximum)



        self.name_label = QtWidgets.QLabel()
        self.name_label.setStyleSheet(styles.CONTROL_NAME)
        self.name_label.setText(self.name)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.name_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                    QtWidgets.QSizePolicy.Expanding)


        self.units_label = QtWidgets.QLabel()
        self.units_label.setStyleSheet(styles.CONTROL_UNITS)
        self.units_label.setText(self.units)
        self.units_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self.units_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                    QtWidgets.QSizePolicy.Expanding)

        # Expand drawer button or 'record' button

        self.toggle_button = QtWidgets.QToolButton(checkable=True,
                                                   checked=False)
        self.toggle_button.setStyleSheet(styles.DISPLAY_NAME)
        self.toggle_button.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum,
            QtWidgets.QSizePolicy.Expanding)
        self.toggle_button.setMaximumWidth(styles.TOGGLE_MAX_WIDTH)
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonIconOnly
        )

        if self.name != ValueName.PEEP.name:
            self.toggle_button.toggled.connect(self.toggle_control)
            self.toggle_button.setArrowType(QtCore.Qt.LeftArrow)

        else:
            self.toggle_button.toggled.connect(self.toggle_record)

            # load record icon
            gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rec_path = os.path.join(gui_dir, 'images', 'record.png')
            image = QtGui.QPixmap(rec_path)
            self.rec_icon = QtGui.QIcon(image)
            self.toggle_button.setIcon(self.rec_icon)
            # self.toggle_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))


        ###
        # layout
        self.label_layout = QtWidgets.QGridLayout()
        self.label_layout.setContentsMargins(0,0,0,0)
        self.label_layout.addWidget(self.sensor_frame, 0, 0, 2, 1)
        self.label_layout.addWidget(self.value_label, 0, 1, 2, 1, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
        self.label_layout.addWidget(self.name_label, 0, 2, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.label_layout.addWidget(self.units_label, 1, 2, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.label_layout.addWidget(self.toggle_button, 0, 3, 2, 1, alignment=QtCore.Qt.AlignRight)
        # pdb.set_trace()

        self.label_layout.setColumnMinimumWidth(3, styles.TOGGLE_MAX_WIDTH)
        self.label_layout.setColumnStretch(0, 2)
        self.label_layout.setColumnStretch(1, 3)
        self.label_layout.setColumnStretch(2, 2)
        self.label_layout.setColumnStretch(3, 0)

        self.label_layout.setRowStretch(0,2)
        self.label_layout.setRowStretch(1, 1)

        # self.setLayout(self.layout)
        self.layout.addLayout(self.label_layout)

        ################
        # Create initially hidden widgets

        # Min value - slider - max value

        self.slider_layout = QtWidgets.QHBoxLayout()

        self.slider_min = QtWidgets.QLabel()
        self.slider_min.setText(unit_conversion.rounded_string(self.abs_range[0], self.decimals))
        self.slider_min.setAlignment(QtCore.Qt.AlignLeft)
        self.slider_min.setFont(mono_font())
        self.slider_min.setStyleSheet(styles.CONTROL_LABEL)
        self.slider_min.setMargin(0)
        self.slider_min.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                    QtWidgets.QSizePolicy.Maximum)


        self.slider_max = QtWidgets.QLabel()
        self.slider_max.setText(unit_conversion.rounded_string(self.abs_range[1], self.decimals))
        self.slider_max.setAlignment(QtCore.Qt.AlignRight)
        self.slider_max.setFont(mono_font())
        self.slider_max.setStyleSheet(styles.CONTROL_LABEL)
        self.slider_max.setMargin(0)
        self.slider_max.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                    QtWidgets.QSizePolicy.Maximum)

        self.slider = DoubleSlider(decimals=self.decimals, orientation=QtCore.Qt.Orientation.Horizontal)
        self.slider.setMinimum(self.abs_range[0])
        self.slider.setMaximum(self.abs_range[1])
        #self.slider.setContentsMargins(0,0,0,0)
        self.slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Maximum)
        
        self.slider_layout.addWidget(self.slider_min)
        self.slider_layout.addWidget(self.slider)
        self.slider_layout.addWidget(self.slider_max)

        self.slider_frame = QtWidgets.QFrame()
        self.slider_frame.setLayout(self.slider_layout)
        self.slider_frame.setVisible(False)

        ###
        # set signals
        self.value_label.textChanged.connect(self._value_changed)
        self.slider.doubleValueChanged.connect(self._value_changed)


        if self.value:
            self._value_changed(self.value)

    @QtCore.Slot(bool)
    def toggle_control(self, state):
        if self.name == ValueName.PEEP.name:
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
            self.value_label.setStyleSheet(styles.CONTROL_VALUE_REC)
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
            self.value_label.setStyleSheet(styles.CONTROL_VALUE)
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

            if (not self._confirmed_unsafe) and ('pytest' not in sys.modules):

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


    def update_value(self, new_value: float):
        """
        Updates the controlled value. Emits :attr:`.value_changed` if value within :attr:`.abs_range` and different than previous :attr:`.value`

        Also updates the slider and sensor bar in the UI.

        Args:
            new_value (float):
        """
        # pdb.set_trace()
        if isinstance(new_value, str):
            new_value = float(new_value)

        # if self._convert_out:
        #     # convert from display value to internal value
        #     new_value = self._convert_out(new_value)
        # don't convert here, assume the only hPa values would come from the widget itself since it's display only

        changed = False
        if (new_value <= self.abs_range[1]) and (new_value >= self.abs_range[0]) and (new_value != self.value):
            self.value = new_value
            changed = True


        else:
            # TODO: Log this
            pass

        self.redraw()
        return changed

    def redraw(self):

        # still draw regardless in case an invalid value was given
        if self._convert_in:
            # pdb.set_trace()
            set_value = self._convert_in(self.value)
            alarm_range = (self._convert_in(self.alarm_range[0]), self._convert_in(self.alarm_range[1]))
            abs_range = (self._convert_in(self.abs_range[0]), self._convert_in(self.abs_range[1]))
        else:
            set_value = self.value
            alarm_range = self.alarm_range
            abs_range = self.abs_range


        #disable signals while we're changing things internally
        try:
            self.value_label.blockSignals(True)
            self.slider.blockSignals(True)

            value_str = unit_conversion.rounded_string(set_value, self.decimals)
            self.value_label.setText(value_str)

            self.slider.setMinimum(abs_range[0])
            self.slider.setMaximum(abs_range[1])
            self.slider.setValue(set_value)
            self.sensor_set.setValue(set_value)
            self.sensor_limits.setData(**{'y': np.array([set_value])})
            self.sensor_limits.setData(**{'bottom': set_value-alarm_range[0],
                                          'top': alarm_range[1]-set_value})

            self.slider_min.setText(unit_conversion.rounded_string(abs_range[0], self.decimals))
            self.slider_max.setText(unit_conversion.rounded_string(abs_range[1], self.decimals))

            self.slider.setDecimals(self.decimals)

            self.update_yrange()
        except Exception as e:
            print(e)

        finally:
            self.value_label.blockSignals(False)
            self.slider.blockSignals(False)

    def update_limits(self, control: ControlSetting):
        if self.value is None:
            return

        #self.update_value(control.value)
        if control.min_value and control.min_value != self.alarm_range[0]:
            if self._convert_in:
                self.sensor_limits.setData(**{'bottom': self._convert_in(self.value - control.min_value)})
            else:
                self.sensor_limits.setData(**{'bottom': self.value-control.min_value})
            self.alarm_range = (control.min_value, self.alarm_range[1])

        if control.max_value and control.max_value != self.alarm_range[1]:
            if self._convert_in:
                self.sensor_limits.setData(**{'top': self._convert_in(control.max_value - self.value)})
            else:
                self.sensor_limits.setData(**{'top': control.max_value-self.value})
            self.alarm_range = (self.alarm_range[0], control.max_value)

        self.update_yrange()

    def update_sensor(self, new_value):
        if new_value is None:
            return
        self.sensor_value = new_value

        # store values to set value by averaging sensor values
        if self.log_values:
            self.logged_values.append(new_value)

        if self._convert_in:
            new_value = self._convert_in(new_value)


        value_str = unit_conversion.rounded_string(new_value, self.decimals)
        self.sensor_label.setText(value_str)
        self.sensor_bar.setOpts(y1=np.array([new_value]))
        # self.sensor_plot.autoRange(padding=.001)
        self.update_yrange()

    def update_yrange(self):
        """
        set y range to include max and min and value

        Returns:

        """
        if self.sensor_value is None:
            new_yrange = self.alarm_range
        else:
            y_min = np.min([self.sensor_value, self.alarm_range[0]])
            y_max = np.max([self.sensor_value, self.alarm_range[1]])
            new_yrange = (y_min, y_max)

        if self._convert_in:
            new_yrange = (self._convert_in(new_yrange[0]),
                          self._convert_in(new_yrange[1]))

        if self.yrange != new_yrange:
            self.sensor_plot.setYRange(*new_yrange)
            self.yrange = new_yrange



    @property
    def is_set(self):
        if self.value is None:
            return False
        else:
            return True

    def set_units(self, units):
        if self.name in (ValueName.PIP.name, ValueName.PEEP.name):
            if units == 'cmH2O':
                self.decimals = 1
                self.slider.setDecimals(self.decimals)
                self.units = units
                self.units_label.setText(units)
                self._convert_in = None
                self._convert_out = None
                self.redraw()
            elif units == 'hPa':
                self.decimals = 0
                self.slider.setDecimals(self.decimals)
                self.units = units
                self.units_label.setText(units)
                self._convert_in = unit_conversion.cmH2O_to_hPa
                self._convert_out = unit_conversion.hPa_to_cmH2O
                self.redraw()
        else:
            print(
                f'error setting units {units}'
            )
            return

    def set_locked(self, locked: bool):
        if locked:
            self.locked = True
            self.toggle_control(False)
            self.toggle_button.setEnabled(False)
            self.value_label.setEditable(False)
            # self.setStyleSheet()
        else:
            self.locked = False
            self.toggle_button.setEnabled(True)
            self.value_label.setEditable(True)


