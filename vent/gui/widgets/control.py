import numpy as np
from PySide2 import QtWidgets, QtCore
import PySide2
import pyqtgraph as pg

from vent.gui import styles, mono_font
from vent.gui.widgets.components import EditableLabel, DoubleSlider
from vent.common.message import ControlSetting
from vent.common.values import Value


class Control(QtWidgets.QWidget):
    """
    Attributes:
        sensor (int, float): Value from the sensor
    """

    value_changed = QtCore.Signal(float)
    limits_changed = QtCore.Signal(tuple)

    def __init__(self, value: Value):
        super(Control, self).__init__()

        self.name = value.name
        self.units = value.units
        self.abs_range = value.abs_range
        if not value.safe_range:
            self.safe_range = (0, 0)
        else:
            self.safe_range = value.safe_range
        self.value = value.default
        self.decimals = value.decimals
        self.sensor = None

        self.init_ui()


    def init_ui(self):
        self.layout = QtWidgets.QGridLayout()
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                           QtWidgets.QSizePolicy.Expanding)

        # Value, Controller
        #        min,   max
        # Name
        # Units

        # # set max size based on range
        # # FIXME: TEMPORARY HACK - get sizing to work intelligibly with the dial
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

        ########
        # Sensor box
        self.sensor_frame = QtWidgets.QFrame()
        self.sensor_frame.setStyleSheet(styles.CONTROL_SENSOR_FRAME)
        self.sensor_frame.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                        QtWidgets.QSizePolicy.Maximum)
        self.sensor_layout = QtWidgets.QHBoxLayout()
        #self.sensor_layout.setContentsMargins(0,0,0,0)


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
        self.sensor_plot.enableAutoRange(y=True)
        #self.sensor_plot.autoRange(padding=.001)
        # self.sensor_plot.enableAutoRange()

        # bar itself
        self.sensor_bar = pg.BarGraphItem(x=np.array([0]), y1=np.array([0]), width=np.array([1]), brush=styles.GRAY_TEXT)

        # error bars for limit indicators
        self.sensor_limits = pg.ErrorBarItem(beam=1, x=np.array([0]), y=np.array([self.value]),
                                             top=self.safe_range[1]-self.value,
                                             bottom=self.value-self.safe_range[0],
                                             pen={
                                                 'color':styles.SUBWAY_COLORS['red'],
                                                 'width':2
                                             })

        # the set value
        self.sensor_set = pg.InfiniteLine(movable=False, angle=0, pos=self.value,
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


        self.value_label.setFixedWidth(n_ints*styles.VALUE_SIZE*.6)
        self.value_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                         QtWidgets.QSizePolicy.Maximum)



        self.name_label = QtWidgets.QLabel()
        self.name_label.setStyleSheet(styles.CONTROL_NAME)
        self.name_label.setText(self.name)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.name_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                    QtWidgets.QSizePolicy.Expanding)


        self.units_label = QtWidgets.QLabel()
        self.units_label.setStyleSheet(styles.CONTROL_UNITS)
        self.units_label.setText(self.units)
        self.units_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.units_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                    QtWidgets.QSizePolicy.Maximum)

        # Expand drawer button
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

        ###
        # layout
        self.layout.addWidget(self.sensor_frame, 0, 0, 2, 1)
        self.layout.addWidget(self.value_label, 0, 1, 2, 1, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
        #self.layout.addWidget(self.dial, 0, 1, 2, 2, alignment=QtCore.Qt.AlignVCenter)
        #self.layout.addWidget(self.slider_min, 2, 1, 1, 1)
        #self.layout.addWidget(self.slider_max, 2, 2, 1, 1)
        self.layout.addWidget(self.name_label, 0, 2, 1, 1, alignment=QtCore.Qt.AlignLeft)
        self.layout.addWidget(self.units_label, 1, 2, 1, 1, alignment=QtCore.Qt.AlignLeft)
        self.layout.addWidget(self.toggle_button, 0, 3, 2, 1, alignment=QtCore.Qt.AlignRight)

        self.setLayout(self.layout)


        ################
        # Create initially hidden widgets

        # Min value - slider - max value

        self.slider_layout = QtWidgets.QHBoxLayout()

        self.slider_min = QtWidgets.QLabel()
        self.slider_min.setText(str(np.round(self.abs_range[0], self.decimals)))
        self.slider_min.setAlignment(QtCore.Qt.AlignLeft)
        self.slider_min.setFont(mono_font())
        self.slider_min.setStyleSheet(styles.CONTROL_LABEL)
        self.slider_min.setMargin(0)
        self.slider_min.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                    QtWidgets.QSizePolicy.Maximum)


        self.slider_max = QtWidgets.QLabel()
        self.slider_max.setText(str(np.round(self.abs_range[1], self.decimals)))
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
        self.value_label.textChanged.connect(self.update_value)
        self.slider.doubleValueChanged.connect(self.update_value)


        self.update_value(self.value)

    @QtCore.Slot(bool)
    def toggle_control(self, state):
        if state == True:
            self.toggle_button.setArrowType(QtCore.Qt.DownArrow)
            self.layout.addWidget(self.slider_frame, 3, 0, 1, 3)
            self.slider_frame.setVisible(True)
            #self.adjustSize()
        else:
            self.toggle_button.setArrowType(QtCore.Qt.LeftArrow)
            self.layout.removeWidget(self.slider_frame)
            self.slider_frame.setVisible(False)
            #self.adjustSize()


    def update_value(self, new_value: float):
        """
        Updates the controlled value. Emits :attr:`.value_changed` if value within :attr:`.abs_range` and different than previous :attr:`.value`

        Also updates the slider and sensor bar in the UI.

        Args:
            new_value (float):
        """
        if isinstance(new_value, str):
            new_value = float(new_value)

        if (new_value <= self.abs_range[1]) and (new_value >= self.abs_range[0]) and (new_value != self.value):
            self.value = new_value

            self.value_changed.emit(self.value)
        else:
            # TODO: Log this
            pass

        # still draw regardless in case an invalid value was given
        value_str = str(np.round(self.value, self.decimals))
        self.value_label.setText(value_str)

        self.slider.setValue(self.value)
        self.sensor_set.setValue(self.value)

    def update_limits(self, control: ControlSetting):

        self.update_value(control.value)
        if control.min_value and control.min_value != self.safe_range[0]:
            self.sensor_limits.setData(**{'bottom': self.value-control.min_value})
            self.safe_range = (control.min_value, self.safe_range[1])

        if control.max_value and control.max_value != self.safe_range[1]:
            self.sensor_limits.setData(**{'top': control.max_value-self.value})
            self.safe_range = (self.safe_range[0], control.max_value)

        # update the error bar center value
        self.sensor_limits.setData(**{'y': np.array([control.value])})





    def update_sensor(self, new_value):
        if new_value is None:
            return
        value_str = str(np.round(new_value, self.decimals))
        self.sensor_label.setText(value_str)
        self.sensor_bar.setOpts(y1=np.array([new_value]))
        # self.sensor_plot.autoRange(padding=.001)
