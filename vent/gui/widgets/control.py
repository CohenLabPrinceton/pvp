import numpy as np
from PySide2 import QtWidgets, QtCore

from vent.gui import styles, mono_font
from vent.gui.widgets.components import EditableLabel


class Control(QtWidgets.QWidget):

    value_changed = QtCore.Signal(float)

    def __init__(self, name, units, abs_range, safe_range, value, decimals):
        super(Control, self).__init__()

        self.name = name
        self.units = units
        self.abs_range = abs_range
        self.safe_range = safe_range
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
        self.layout.addWidget(self.value_label, 0, 0, 3, 1, alignment=QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.layout.addWidget(self.dial, 0, 1, 2, 2, alignment=QtCore.Qt.AlignVCenter)
        self.layout.addWidget(self.dial_min, 2, 1, 1, 1)
        self.layout.addWidget(self.dial_max, 2, 2, 1, 1)
        self.layout.addWidget(self.name_label, 3, 0, 1, 3, alignment=QtCore.Qt.AlignRight)
        self.layout.addWidget(self.units_label, 4, 0, 1, 3, alignment=QtCore.Qt.AlignRight)

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