import numpy as np
from PySide2 import QtWidgets, QtCore

from vent.gui import styles, mono_font
from vent.gui.widgets.components import EditableLabel, DoubleSlider


class Control(QtWidgets.QWidget):

    value_changed = QtCore.Signal(float)

    def __init__(self, value):
        super(Control, self).__init__()

        self.name = value.name
        self.units = value.units
        self.abs_range = value.abs_range
        self.safe_range = value.safe_range
        self.value = value.default
        self.decimals = value.decimals

        self.init_ui()


    def init_ui(self):
        self.layout = QtWidgets.QGridLayout()
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                           QtWidgets.QSizePolicy.Expanding)

        # Value, Controller
        #        min,   max
        # Name
        # Units

        self.value_label = EditableLabel()
        self.value_label.setStyleSheet(styles.CONTROL_VALUE)
        self.value_label.label.setFont(mono_font())
        self.value_label.lineEdit.setFont(mono_font())
        self.value_label.label.setAlignment(QtCore.Qt.AlignRight)
        #self.value_label.setMargin(0)
        self.value_label.setContentsMargins(0,0,0,0)

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
        if n_ints <= 5:
            n_ints = 5
        self.value_label.setFixedWidth(n_ints*styles.VALUE_SIZE*.6)
        # self.value_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                             QtWidgets.QSizePolicy.Maximum)



        self.name_label = QtWidgets.QLabel()
        self.name_label.setStyleSheet(styles.CONTROL_NAME)
        self.name_label.setText(self.name)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(QtCore.Qt.AlignRight)
        # self.name_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                             QtWidgets.QSizePolicy.Expanding)


        self.units_label = QtWidgets.QLabel()
        self.units_label.setStyleSheet(styles.CONTROL_UNITS)
        self.units_label.setText(self.units)
        self.units_label.setAlignment(QtCore.Qt.AlignRight)
        self.units_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                    QtWidgets.QSizePolicy.Expanding)

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
        self.layout.addWidget(self.value_label, 0, 0, 2, 1, alignment=QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        #self.layout.addWidget(self.dial, 0, 1, 2, 2, alignment=QtCore.Qt.AlignVCenter)
        #self.layout.addWidget(self.slider_min, 2, 1, 1, 1)
        #self.layout.addWidget(self.slider_max, 2, 2, 1, 1)
        self.layout.addWidget(self.name_label, 0, 1, 1, 1)
        self.layout.addWidget(self.units_label, 1, 1, 1, 1)
        self.layout.addWidget(self.toggle_button, 0, 2, 2, 1, alignment=QtCore.Qt.AlignRight)

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


    def update_value(self, new_value):
        if isinstance(new_value, str):
            new_value = float(new_value)

        if (new_value <= self.abs_range[1]) and (new_value >= self.abs_range[0]):
            self.value = new_value

            self.value_changed.emit(self.value)
        else:
            # TODO: Log this
            pass

        # still draw regardless in case an invalid value was given
        value_str = str(np.round(self.value, self.decimals))
        self.value_label.setText(value_str)

        self.slider.setValue(self.value)