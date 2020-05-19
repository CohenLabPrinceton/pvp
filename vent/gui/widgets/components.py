import copy

import numpy as np
from PySide2 import QtWidgets, QtCore, QtGui

from vent.gui import styles, mono_font

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

        super(DoubleSlider, self).setValue(int(round(value * self._multi)))


class RangeSlider(DoubleSlider):

    valueChanged = QtCore.Signal(tuple)
    """
    (tuple): (low, high) set range of floats
    """

    def __init__(self, abs_range, safe_range, decimals=1, *args, **kwargs):
        """
        Slider with two handles that sets a range

        Args:
            abs_range (tuple): absolute range of slider
            safe_range (tuple): default set values for handles of slider
            decimals (int): number of decimals of precision
            *args:
            **kwargs:
        """
        super(RangeSlider, self).__init__(decimals=decimals, *args, **kwargs)
        self.setStyleSheet(styles.RANGE_SLIDER)

        self.decimals = decimals
        self.setSingleStep(10 ** -self.decimals)

        # abs range is the min/max theoretically allowable values
        self.abs_range = abs_range
        self.setMinimum(abs_range[0])
        self.setMaximum(abs_range[1])

        # safe range are the levels outside of which we trigger an alarm
        # initialize high and low to full range first so they have acceptable values
        self._low = int(round(abs_range[0] * self._multi))
        self._high = int(round(abs_range[1] * self._multi))
        # then set the initial value
        self.safe_range = safe_range
        self.setValue(self.safe_range)

        self.pressed_control = QtWidgets.QStyle.SC_None
        self.hover_control = QtWidgets.QStyle.SC_None
        self.click_offset = 0

        # 0 for the low, 1 for the high, -1 for both
        self.active_slider = 0

        # cache tick levels and labels so they're not redrawn constantly
        self.levels = None
        self.level_labels = None

        if self.orientation() == QtCore.Qt.Orientation.Horizontal:
            self.setMinimumHeight(styles.SLIDER_HEIGHT)
        else:
            self.setMinimumWidth(styles.SLIDER_WIDTH)


    @property
    def low(self):
        return self._low / self._multi

    @low.setter
    def low(self, low):
        old_low = self._low

        low = int(round(low * self._multi))

        # if the low value is above the minimum...
        if low >= self._minimum():
            # if the low value is higher than the high value,
            # and there is at least one step of headroom,
            # set the high value as well
            if low > self._high:
                if low <= self._maximum() - self._singleStep():
                    self._high = low + self._singleStep()
                else:
                    return
            self._low = low

        elif low < self._minimum():
            self._low = self._minimum()

        if old_low != self._low:
            self.valueChanged.emit((self.low, self.high))
        self.update()

    @property
    def high(self):
        return self._high / self._multi

    @high.setter
    def high(self, high):
        old_high = self._high

        high = int(round(high * self._multi))

        # if the low value is above the minimum...
        if high <= self._maximum():
            # if the high value is lower than the low value,
            # and there is at least one step of headroom,
            # set the high value as well
            if high < self._low:
                if high >= self._minimum() + self._singleStep():
                    self._low = high - self._singleStep()
                else:
                    return
            self._high = high

        elif high > self._maximum():
            self._high = self._maximum()

        if old_high != self._high:
            self.valueChanged.emit((self.low, self.high))

        self.update()

    # make methods just so the can accept signals
    def setLow(self, low):
        self.low = low

    def setHigh(self, high):
        self.high = high

    def setValue(self, value):
        """
        Args:
            value (tuple): (low, high) to set
        """

        # if our signals were not blocked before now,
        # we want to turn them on again afterwards

        old_state = self.signalsBlocked()

        # block signals so we don't double-emit the change
        self.blockSignals(True)
        self.low = value[0]
        self.high = value[1]
        self.blockSignals(old_state)

        self.valueChanged.emit((self.low, self.high))

    def value(self):
        return (self.low, self.high)

    def generate_labels(self):
        """
        Generate the text labels for the slider.

        Called on init and on resizeEvent
        """


        self.levels = np.linspace(self.minimum(), self.maximum(), 5)
        self.level_labels = []

        painter = QtGui.QPainter(self)
        painter.setFont(mono_font())

        style = self.style()
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        length = style.pixelMetric(QtWidgets.QStyle.PM_SliderLength, opt, self)
        available = style.pixelMetric(QtWidgets.QStyle.PM_SliderSpaceAvailable, opt, self)

        for v in self.levels:
            label_str = str(int(round(v)))
            # label_str = "{0:d}".format(v)
            rect = painter.drawText(QtCore.QRect(), QtCore.Qt.TextDontPrint, label_str)

            if self.orientation() == QtCore.Qt.Horizontal:

                x_loc = QtWidgets.QStyle.sliderPositionFromValue(self.minimum(),
                                                                 self.maximum(), v, available, opt.upsideDown)

                left = x_loc + length // 2 - rect.width() // 2
                # there is a 3 px offset that I can't attribute to any metric
                # left = (self.width())-(rect.width())-10
                bottom = (self.height() / 2) + rect.height() //2 + 3

            else:

                y_loc= QtWidgets.QStyle.sliderPositionFromValue(self.minimum(),
                        self.maximum(), v, available, opt.upsideDown)

                bottom=y_loc+length//2+rect.height()//2-3
                # there is a 3 px offset that I can't attribute to any metric
                #left = (self.width())-(rect.width())-10
                left = (self.width()/2)-(styles.INDICATOR_WIDTH/2)-rect.width()-3

            pos=QtCore.QPoint(left, bottom)
            self.level_labels.append((pos, QtGui.QStaticText(label_str)))

            #painter.drawText(pos, label_str)

        self.setTickInterval(self.levels[1]-self.levels[0])
        self.redraw_labels = False


    def paintEvent(self, event):
        # based on http://qt.gitorious.org/qt/qt/blobs/master/src/gui/widgets/qslider.cpp

        painter = QtGui.QPainter(self)
        #style = QtWidgets.QApplication.style()
        style = self.style()

        for i, value in enumerate([self._high, self._low]):
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)
            # pdb.set_trace()
            # Only draw the groove for the first slider so it doesn't get drawn
            # on top of the existing ones every time
            if i == 0:
                opt.subControls = style.SC_SliderGroove | style.SC_SliderHandle
            else:
                # opt.subControls = QtWidgets.QStyle.SC_SliderHandle
                opt.subControls = style.SC_SliderHandle

            #
            # if self.tickPosition() != self.NoTicks:
            #     opt.subControls |= QtWidgets.QStyle.SC_SliderTickmarks

            if self.pressed_control:
                opt.activeSubControls = self.pressed_control
                opt.state |= QtWidgets.QStyle.State_Sunken
            else:
                opt.activeSubControls = self.hover_control

            # opt.rect.setX(-self.width()/2)
            opt.sliderPosition = value
            opt.sliderValue = value
            style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)

        if not self.level_labels or self.redraw_labels:
            painter.end()
            self.generate_labels()
            painter = QtGui.QPainter(self)

        painter.setFont(mono_font())

        for label in self.level_labels:
            painter.drawStaticText(label[0], label[1])

        #self.setTickInterval(self.levels[1]-self.levels[0])

    def get_handle_rect(self, which=0):
        """

        Args:
            which (int): 0 = low, 1 = high

        Returns:
            :class:`QtCore.QRect` of handle
        """

        painter = QtGui.QPainter(self)
        #style = QtWidgets.QApplication.style()
        style = self.style()

        if which == 0 or which is False:
            value = self._low
        elif which == 1 or which is True:
            value = self._high
        else:
            raise ValueError(f'needs to be 0 for low handle or 1 for high handle, got {which}')


        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.subControls = style.SC_SliderHandle
        opt.sliderPosition = value
        opt.sliderValue = value

        return style.subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self)






    def mousePressEvent(self, event):
        event.accept()

        style = QtWidgets.QApplication.style()
        button = event.button()

        # In a normal slider control, when the user clicks on a point in the
        # slider's total range, but not on the slider part of the control the
        # control would jump the slider value to where the user clicked.
        # For this control, clicks which are not direct hits will slide both
        # slider parts

        if button:
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)

            self.active_slider = -1

            for i, value in enumerate([self._low, self._high]):
                opt.sliderPosition = value
                hit = style.hitTestComplexControl(style.CC_Slider, opt, event.pos(), self)
                if hit == style.SC_SliderHandle:
                    self.active_slider = i
                    self.pressed_control = hit

                    self.triggerAction(self.SliderMove)
                    self.setRepeatAction(self.SliderNoAction)
                    self.setSliderDown(True)
                    break

            if self.active_slider < 0:
                self.pressed_control = QtWidgets.QStyle.SC_SliderHandle
                self.click_offset = self.__pixelPosToRangeValue(self.__pick(event.pos()))
                self.triggerAction(self.SliderMove)
                self.setRepeatAction(self.SliderNoAction)
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.pressed_control != QtWidgets.QStyle.SC_SliderHandle:
            event.ignore()
            return

        event.accept()

        # get old values
        old_low = copy.copy(self.low)
        old_high = copy.copy(self.high)

        new_pos = self.__pixelPosToRangeValue(self.__pick(event.pos()))
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        if self.active_slider < 0:
            offset = new_pos - self.click_offset
            self.high += offset
            self.low += offset
            if self.low < self.minimum():
                diff = self.minimum() - self.low
                self.low += diff
                self.high += diff
            if self.high > self.maximum():
                diff = self.maximum() - self.high
                self.low += diff
                self.high += diff
        elif self.active_slider == 0:
            if new_pos >= self.high:
                #new_pos = self._high - 1
                new_pos = self.low
            self.low = new_pos
        else:
            if new_pos <= self.low:
                #new_pos = self._low + 1
                new_pos = self.high
            self.high = new_pos
        self.click_offset = new_pos
        self.update()
        self.emit(QtCore.SIGNAL('sliderMoved(int)'), new_pos)

        # emit valuechanged signal
        if (old_low != self.low) or (old_high != self.high):
            self.valueChanged.emit((self.low, self.high))

    def __pick(self, pt):
        if self.orientation() == QtCore.Qt.Horizontal:
            return pt.x()
        else:
            return pt.y()

    def __pixelPosToRangeValue(self, pos):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        style = QtWidgets.QApplication.style()

        gr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)
        sr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderHandle, self)

        if self.orientation() == QtCore.Qt.Horizontal:
            slider_length = sr.width()
            slider_min = gr.x()
            slider_max = gr.right() - slider_length + 1
        else:
            slider_length = sr.height()
            slider_min = gr.y()
            slider_max = gr.bottom() - slider_length + 1
        return style.sliderValueFromPosition(self.minimum()*self._multi, self.maximum()*self._multi, pos - slider_min, slider_max - \
            slider_min, opt.upsideDown)/self._multi

    def resizeEvent(self, event):
        self.redraw_labels = True



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