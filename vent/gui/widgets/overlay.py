# from PySide2.QtWidgets import *
# from PySide2.QtGui import *
# from PySide2.QtCore import *
#
# class Overlay(QWidget):
#     def __init__(self, parent=None):
#         super(Overlay, self).__init__(parent)
#
#         palette = QPalette(self.palette())
#         palette.setColor(palette.Background, Qt.transparent)
#
#         self.setPalette(palette)
#
#     def paintEvent(self, event):
#         painter = QPainter()
#         painter.begin(self)
#         painter.setRenderHint(QPainter.Antialiasing)
#         painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, 127)))
#         # painter.drawLine(self.width() / 8, self.height() / 8, 7 * self.width() / 8, 7 * self.height() / 8)
#         # painter.drawLine(self.width() / 8, 7 * self.height() / 8, 7 * self.width() / 8, self.height() / 8)
#         # painter.setPen(QPen(Qt.NoPen))


import sys
from PySide2 import QtWidgets, QtCore, QtGui

# class TranslucentWidgetSignals(QtCore.QObject):
#     # SIGNALS
#     CLOSE = QtCore.Signal()

class Overlay(QtWidgets.QWidget):
    """
    adapted from https://stackoverflow.com/a/44280935/13113166
    """
    def __init__(self, parent=None):
        super(Overlay, self).__init__(parent)

        # make the window frameless
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.fillColor = QtGui.QColor(30, 30, 30, 120)
        self.penColor = QtGui.QColor("#333333")

        self.popup_fillColor = QtGui.QColor(240, 240, 240, 255)
        self.popup_penColor = QtGui.QColor(200, 200, 200, 255)

        self.close_btn = QtWidgets.QPushButton(self)
        self.close_btn.setText("x")
        font = QtGui.QFont()
        font.setPixelSize(18)
        font.setBold(True)
        self.close_btn.setFont(font)
        self.close_btn.setStyleSheet("background-color: rgb(0, 0, 0, 0)")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self._onclose)

        # self.SIGNALS = TranslucentWidgetSignals()

    def resizeEvent(self, event):
        s = self.size()
        popup_width = 300
        popup_height = 120
        ow = int(s.width() / 2 - popup_width / 2)
        oh = int(s.height() / 2 - popup_height / 2)
        self.close_btn.move(ow + 265, oh + 5)

    def paintEvent(self, event):
        # This method is, in practice, drawing the contents of
        # your window.

        # get current window size
        s = self.size()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        qp.setPen(self.penColor)
        qp.setBrush(self.fillColor)
        qp.drawRect(0, 0, s.width(), s.height())

        # drawpopup
        qp.setPen(self.popup_penColor)
        qp.setBrush(self.popup_fillColor)
        popup_width = 300
        popup_height = 120
        ow = int(s.width()/2-popup_width/2)
        oh = int(s.height()/2-popup_height/2)
        qp.drawRoundedRect(ow, oh, popup_width, popup_height, 5, 5)

        font = QtGui.QFont()
        font.setPixelSize(18)
        font.setBold(True)
        qp.setFont(font)
        qp.setPen(QtGui.QColor(70, 70, 70))
        tolw, tolh = 80, -5
        qp.drawText(ow + int(popup_width/2) - tolw, oh + int(popup_height/2) - tolh, "Yep, I'm a pop up.")

        qp.end()

    def _onclose(self):
        print("Close")
        self.close()
        # self.SIGNALS.CLOSE.emit()

#
# class ParentWidget(QtWidgets.QWidget):
#     def __init__(self, parent=None):
#         super(ParentWidget, self).__init__(parent)
#
#         self._popup = QtWidgets.QPushButton("Gimme Popup!!!")
#         self._popup.setFixedSize(150, 40)
#         self._popup.clicked.connect(self._onpopup)
#
#         self._other1 = QtWidgets.QPushButton("A button")
#         self._other2 = QtWidgets.QPushButton("A button")
#         self._other3 = QtWidgets.QPushButton("A button")
#         self._other4 = QtWidgets.QPushButton("A button")
#
#         hbox = QtWidgets.QHBoxLayout()
#         hbox.addWidget(self._popup)
#         hbox.addWidget(self._other1)
#         hbox.addWidget(self._other2)
#         hbox.addWidget(self._other3)
#         hbox.addWidget(self._other4)
#         self.setLayout(hbox)
#
#         self._popframe = None
#         self._popflag = False
#
#     def resizeEvent(self, event):
#         if self._popflag:
#             self._popframe.move(0, 0)
#             self._popframe.resize(self.width(), self.height())
#
#     def _onpopup(self):
#         self._popframe = TranslucentWidget(self)
#         self._popframe.move(0, 0)
#         self._popframe.resize(self.width(), self.height())
#         self._popframe.SIGNALS.CLOSE.connect(self._closepopup)
#         self._popflag = True
#         self._popframe.show()
#
#     def _closepopup(self):
#         self._popframe.close()
#         self._popflag = False
#
#
# if __name__ == '__main__':
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     main = ParentWidget()
#     main.resize(500, 500)
#     main.show()
#     sys.exit(app.exec_())