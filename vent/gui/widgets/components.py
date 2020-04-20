import copy

import numpy as np
from PySide2 import QtWidgets, QtCore, QtGui

from vent.gui import styles, mono_font


class RangeSlider(QtWidgets.QSlider):
    """
    A slider for ranges.
    This class provides a dual-slider for ranges, where there is a defined
    maximum and minimum, as is a normal slider, but instead of having a
    single slider value, there are 2 slider values.
    This class emits the same signals as the QSlider base class, with the
    exception of valueChanged

    Adapted from `<https://bitbucket.org/genuine_/idascope-local/src/master/idascope/widgets/RangeSlider.py>`_
    (Thank you!!!)

    With code from https://stackoverflow.com/a/54819051
    for labels!
    """

    valueChanged = QtCore.Signal(tuple)

    def __init__(self, abs_range, safe_range, *args):
        super(RangeSlider, self).__init__(*args)
        self.setStyleSheet(styles.RANGE_SLIDER)

        self.abs_range = abs_range
        self.setMinimum(abs_range[0])
        self.setMaximum(abs_range[1])

        self.levels = np.linspace(self.minimum(), self.maximum(), 5)
        # TODO: recalculate when minimum or maximum are set
        #self.setTickInterval(round((abs_range[1]-abs_range[0])/5))
        #self.setTickPosition(QtWidgets.QSlider.TicksLeft)

        self.safe_range = safe_range
        self.low = safe_range[0]
        self.high = safe_range[1]

        #self._low = self.minimum()
        #self._high = self.maximum()

        self._alarm = False

        self.pressed_control = QtWidgets.QStyle.SC_None
        self.hover_control = QtWidgets.QStyle.SC_None
        self.click_offset = 0

        # 0 for the low, 1 for the high, -1 for both
        self.active_slider = 0

        # ticks
        self.setTickPosition(QtWidgets.QSlider.TicksLeft)
        # gives some space to print labels
        self.left_margin=10
        self.top_margin=10
        self.right_margin=0
        self.bottom_margin=10
        self.setContentsMargins(self.left_margin,
                                self.top_margin,
                                self.right_margin,
                                self.bottom_margin)
        self.setMinimumWidth(styles.SLIDER_WIDTH)

        # indicator
        self._indicator = 0


    @property
    def low(self):
        return self._low

    @low.setter
    def low(self, low):
        self._low = low
        self.update()

    @property
    def high(self):
        return self._high

    @high.setter
    def high(self, high):
        self._high = high
        self.update()

    # make methods just so the can accept signals
    def setLow(self, low):
        self.low = low

    def setHigh(self, high):
        self.high = high

    def update_indicator(self, new_val):
        self._indicator = new_val
        self.update()

    @property
    def alarm(self):
        return self._alarm

    @alarm.setter
    def alarm(self, alarm):
        self._alarm = alarm
        self.update()


    def paintEvent(self, event):
        # based on http://qt.gitorious.org/qt/qt/blobs/master/src/gui/widgets/qslider.cpp

        painter = QtGui.QPainter(self)
        #style = QtWidgets.QApplication.style()
        style = self.style()

        ### Draw current value indicator
        if self._indicator != 0:
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)
            length = style.pixelMetric(QtWidgets.QStyle.PM_SliderLength, opt, self)
            available = style.pixelMetric(QtWidgets.QStyle.PM_SliderSpaceAvailable, opt, self)


            y_loc= QtWidgets.QStyle.sliderPositionFromValue(self.minimum(),
                    self.maximum(), self._indicator, self.height(), opt.upsideDown)


            # draw indicator first, so underneath max and min
            indicator_color = QtGui.QColor(0,0,0)
            if not self.alarm:
                indicator_color.setNamedColor(styles.INDICATOR_COLOR)
            else:
                indicator_color.setNamedColor(styles.ALARM_COLOR)

            x_begin = (self.width()-styles.INDICATOR_WIDTH)/2

            painter.setBrush(indicator_color)
            pen_bak = copy.copy(painter.pen())
            painter.setPen(painter.pen().setWidth(0))
            painter.drawRect(x_begin,y_loc,styles.INDICATOR_WIDTH,self.height()-y_loc)

            painter.setPen(pen_bak)

        for i, value in enumerate([self._high, self._low]):
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)
            # pdb.set_trace()
            # Only draw the groove for the first slider so it doesn't get drawn
            # on top of the existing ones every time
            if i == 0:
                opt.subControls = style.SC_SliderGroove | style.SC_SliderHandle
            else:
                #opt.subControls = QtWidgets.QStyle.SC_SliderHandle
                opt.subControls = style.SC_SliderHandle


            if self.tickPosition() != self.NoTicks:
                opt.subControls |= QtWidgets.QStyle.SC_SliderTickmarks

            if self.pressed_control:
                opt.activeSubControls = self.pressed_control
                opt.state |= QtWidgets.QStyle.State_Sunken
            else:
                opt.activeSubControls = self.hover_control

            # opt.rect.setX(-self.width()/2)
            opt.sliderPosition = value
            opt.sliderValue = value
            style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)

        # draw ticks
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        length = style.pixelMetric(QtWidgets.QStyle.PM_SliderLength, opt, self)
        available = style.pixelMetric(QtWidgets.QStyle.PM_SliderSpaceAvailable, opt, self)
        border_offset = 5
        available -= border_offset


        painter.setFont(mono_font)

        for v in self.levels:
            label_str = str(int(round(v)))
            # label_str = "{0:d}".format(v)
            rect = painter.drawText(QtCore.QRect(), QtCore.Qt.TextDontPrint, label_str)

            y_loc= QtWidgets.QStyle.sliderPositionFromValue(self.minimum(),
                    self.maximum(), v, available, opt.upsideDown)

            bottom=y_loc+length//2+rect.height()//2+(border_offset/2)-3
            # there is a 3 px offset that I can't attribute to any metric
            #left = (self.width())-(rect.width())-10
            left = (self.width()/2)-(styles.INDICATOR_WIDTH/2)-rect.width()-3

            pos=QtCore.QPoint(left, bottom)
            painter.drawText(pos, label_str)

        self.setTickInterval(self.levels[1]-self.levels[0])




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
        old_low = copy.copy(self._low)
        old_high = copy.copy(self._high)

        new_pos = self.__pixelPosToRangeValue(self.__pick(event.pos()))
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        if self.active_slider < 0:
            offset = new_pos - self.click_offset
            self._high += offset
            self._low += offset
            if self._low < self.minimum():
                diff = self.minimum() - self._low
                self._low += diff
                self._high += diff
            if self._high > self.maximum():
                diff = self.maximum() - self._high
                self._low += diff
                self._high += diff
        elif self.active_slider == 0:
            if new_pos >= self._high:
                #new_pos = self._high - 1
                new_pos = self._low
            self._low = new_pos
        else:
            if new_pos <= self._low:
                #new_pos = self._low + 1
                new_pos = self._high
            self._high = new_pos
        self.click_offset = new_pos
        self.update()
        self.emit(QtCore.SIGNAL('sliderMoved(int)'), new_pos)

        # emit valuechanged signal
        if (old_low != self._low) or (old_high != self._high):
            self.valueChanged.emit((self._low, self._high))

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
        return style.sliderValueFromPosition(self.minimum(), self.maximum(), pos - slider_min, slider_max - \
            slider_min, opt.upsideDown)


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

        self.setStyleSheet(styles.CONTROL_VALUE)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setObjectName("mainLayout")

        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName("label")
        # self.label.setStyleSheet(styles.CONTROL_VALUE)
        self.label.setMinimumHeight(styles.VALUE_SIZE)


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
    def __init__(self, parent=None, color=QtGui.QColor(styles.DIVIDER_COLOR)):
        super(QHLine, self).__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setLineWidth(0)
        self.setMidLineWidth(3)
        self.setContentsMargins(0, 0, 0, 0)
        self.setColor(color)

    def setColor(self, color):
        pal = self.palette()
        pal.setColor(QtGui.QPalette.WindowText, color)
        self.setPalette(pal)