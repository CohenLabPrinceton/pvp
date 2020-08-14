import copy
import pdb
import typing

import numpy as np
from PySide2 import QtWidgets, QtCore, QtGui

from pvp.gui import styles, mono_font

class DoubleSlider(QtWidgets.QSlider):
    """
    Slider capable of representing floats

    Ripped off from
    and https://stackoverflow.com/a/50300848 ,

    Thank you!!!
    """

    # override the default valueChanged signal
    doubleValueChanged = QtCore.Signal(float)

    def __init__(self, decimals=1, *args, **kargs):
        super(DoubleSlider, self).__init__(*args, **kargs)
        self._multi = 10 ** decimals
        self.decimals = decimals

        self.valueChanged.connect(self.emitDoubleValueChanged)

    def setDecimals(self, decimals):
        self._multi = 10 ** decimals

    def emitDoubleValueChanged(self):
        self.doubleValueChanged.emit(self.value())

    def value(self):
        return float(super(DoubleSlider, self).value()) / self._multi

    def setMinimum(self, value):
        return super(DoubleSlider, self).setMinimum(round(value * self._multi))

    def setMaximum(self, value):
        return super(DoubleSlider, self).setMaximum(round(value * self._multi))

    def minimum(self):
        return super(DoubleSlider, self).minimum() / self._multi

    def _minimum(self):
        return super(DoubleSlider, self).minimum()

    def maximum(self):
        return super(DoubleSlider, self).maximum() / self._multi

    def _maximum(self):
        return super(DoubleSlider, self).maximum()

    def setSingleStep(self, value):
        return super(DoubleSlider, self).setSingleStep(round(value * self._multi))

    def singleStep(self):
        return float(super(DoubleSlider, self).singleStep()) / self._multi

    def _singleStep(self):
        return super(DoubleSlider, self).singleStep()

    def setValue(self, value):
        # pdb.set_trace()
        super(DoubleSlider, self).setValue(int(round(value * self._multi)))

class KeyPressHandler(QtCore.QObject):
    """Custom key press handler
    https://gist.github.com/mfessenden/baa2b87b8addb0b60e54a11c1da48046"""
    escapePressed = QtCore.Signal(bool)
    returnPressed = QtCore.Signal(bool)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            event_key = event.key()
            if event_key == QtCore.Qt.Key_Escape:
                self.escapePressed.emit(True)
                return True
            if event_key == QtCore.Qt.Key_Return or event_key == QtCore.Qt.Key_Enter:
                self.returnPressed.emit(True)
                return True

        return QtCore.QObject.eventFilter(self, obj, event)


class EditableLabel(QtWidgets.QWidget):
    """Editable label
    https://gist.github.com/mfessenden/baa2b87b8addb0b60e54a11c1da48046"""
    textChanged = QtCore.Signal(str)

    def __init__(self, parent=None, **kwargs):
        super(EditableLabel, self).__init__(parent=parent, **kwargs)

        self.is_editable = kwargs.get("editable", True)
        self.keyPressHandler = KeyPressHandler(self)

        # self.setStyleSheet(styles.CONTROL_VALUE)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setObjectName("mainLayout")

        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName("label")
        # self.label.setStyleSheet(styles.CONTROL_VALUE)
        # self.label.setMinimumHeight(styles.VALUE_SIZE)


        self.mainLayout.addWidget(self.label)
        self.lineEdit = QtWidgets.QLineEdit(self)
        # self.lineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                             QtWidgets.QSizePolicy.Expanding)
        # self.lineEdit.setMinimumHeight(styles.VALUE_SIZE)
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setValidator(QtGui.QDoubleValidator())
        self.mainLayout.addWidget(self.lineEdit)
        # hide the line edit initially
        self.lineEdit.setHidden(True)


        # setup signals
        self.create_signals()

    def create_signals(self):
        self.lineEdit.installEventFilter(self.keyPressHandler)
        self.label.mousePressEvent = self.labelPressedEvent

        # give the lineEdit both a `returnPressed` and `escapedPressed` action
        self.keyPressHandler.escapePressed.connect(self.escapePressedAction)
        self.keyPressHandler.returnPressed.connect(self.returnPressedAction)

    def text(self):
        """Standard QLabel text getter"""
        return self.label.text()

    def setText(self, text):
        """Standard QLabel text setter"""
        self.label.blockSignals(True)
        self.label.setText(text)
        self.label.blockSignals(False)

    def labelPressedEvent(self, event):
        """Set editable if the left mouse button is clicked"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setLabelEditableAction()

    def setLabelEditableAction(self):
        """Action to make the widget editable"""
        if not self.is_editable:
            return

        self.label.setHidden(True)
        self.label.blockSignals(True)
        self.lineEdit.setHidden(False)
        self.lineEdit.setText(self.label.text())
        self.lineEdit.blockSignals(False)
        self.lineEdit.setFocus(QtCore.Qt.MouseFocusReason)
        self.lineEdit.selectAll()

    def setEditable(self, editable: bool):
        self.is_editable = editable

    def labelUpdatedAction(self):
        """Indicates the widget text has been updated"""
        text_to_update = self.lineEdit.text()

        if text_to_update != self.label.text():
            self.label.setText(text_to_update)
            self.textChanged.emit(text_to_update)

        self.label.setHidden(False)
        self.lineEdit.setHidden(True)
        self.lineEdit.blockSignals(True)
        self.label.blockSignals(False)

    def returnPressedAction(self):
        """Return/enter event handler"""
        self.labelUpdatedAction()

    def escapePressedAction(self):
        """Escape event handler"""
        self.label.setHidden(False)
        self.lineEdit.setHidden(True)
        self.lineEdit.blockSignals(True)
        self.label.blockSignals(False)


class QHLine(QtWidgets.QFrame):
    """
    with respct to https://stackoverflow.com/a/51057516
    """
    def __init__(self, parent=None, color=styles.DIVIDER_COLOR):
        super(QHLine, self).__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setLineWidth(0)
        self.setMidLineWidth(3)
        self.setContentsMargins(0, 0, 0, 0)

        color = QtGui.QColor(color)

        self.setColor(color)

    def setColor(self, color):
        pal = self.palette()
        pal.setColor(QtGui.QPalette.WindowText, color)
        self.setPalette(pal)

class QVLine(QtWidgets.QFrame):
    def __init__(self, parent=None, color=styles.DIVIDER_COLOR):
        super(QVLine, self).__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setLineWidth(0)
        self.setMidLineWidth(3)
        self.setContentsMargins(0, 0, 0, 0)

        color = QtGui.QColor(color)

        self.setColor(color)

    def setColor(self, color):
        pal = self.palette()
        pal.setColor(QtGui.QPalette.WindowText, color)
        self.setPalette(pal)


class OnOffButton(QtWidgets.QPushButton):
    """
    Simple extension of toggle button with styling for clearer 'ON' vs 'OFF'
    """

    def __init__(self, state_labels: typing.Tuple[str, str] = ('ON', 'OFF'), toggled:bool=False, *args, **kwargs):
        """

        Args:
            state_labels (tuple): tuple of strings to set when toggled and untoggled
            toggled (bool): initialize the button as toggled
            *args: passed to :class:`~PySide2.QtWidgets.QPushButton`
            **kwargs: passed to :class:`~PySide2.QtWidgets.QPushButton`
        """
        super(OnOffButton, self).__init__(*args, **kwargs)

        self.state_labels = state_labels

        self.setCheckable(True)
        self.toggled.connect(self.set_state)
        self.setChecked(toggled)

        self.setStyleSheet(styles.TOGGLE_BUTTON)

    @QtCore.Slot(bool)
    def set_state(self, state: bool):
        if state:
            # button is pressed down
            self.setText(self.state_labels[0])
        else:
            self.setText(self.state_labels[1])

