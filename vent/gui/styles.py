from PySide2 import QtGui

SUBWAY_COLORS = {
    'blue': "#0039A6",
    'lime': "#6CBE45",
    'gray': "A7A9AC",
    'orange': "#FF6319",
    'yellow': "#FCCC0A",
    'red': "#EE352E",
    'green': "#00933C",
    'purple': "#B933AD"
}

BACKGROUND_COLOR = "#111111"
BOX_BACKGROUND = "#333333"
TEXT_COLOR = "#EEEEEE"
CONTROL_BACKGROUND = "#EEEEEE"
CONTROL_TEXT = BACKGROUND_COLOR
HANDLE_HEIGHT = 10
SLIDER_WIDTH = 80
SLIDER_HEIGHT = 50
INDICATOR_WIDTH = SLIDER_WIDTH/3
SLIDER_COLOR = TEXT_COLOR
INDICATOR_COLOR = SUBWAY_COLORS['blue']
ALARM_COLOR = "#FF0000"

DIVIDER_COLOR = "#FFFFFF"
DIVIDER_COLOR_DARK = BOX_BACKGROUND

VALUE_SIZE = 72
NAME_SIZE = 36
UNIT_SIZE = 18
TICK_SIZE = 12

MONITOR_UPDATE_INTERVAL = 0.5
"""
(float): inter-update interval (seconds) for :class:`~vent.gui.widgets.monitor.Monitor`
"""

GLOBAL = f"""
QWidget {{
    font-size: 20pt;
    color: {TEXT_COLOR};
}}
"""

RANGE_SLIDER = f"""
QSlider {{
    font-size : {TICK_SIZE}px;
}}

QSlider::groove:vertical {{
    border: 1px solid #FFFFFF;
    width: {SLIDER_WIDTH}px;
}}

QSlider::handle:vertical {{
    height: {HANDLE_HEIGHT}px;
    width: 20px;
    margin: 0px -20px 0px px;
    background-color: {SLIDER_COLOR};
}}

QSlider::groove:horizontal {{
    margin: 0px, 0px, 30px, 0px;
}}

QSlider::handle:horizontal {{

}}

"""


# RANGE_SLIDER = """
# QSlider {{
#     font-size: 12px;
# }}
# QSlider::groove:vertical {{
# border: 1px solid #FFFFFF;
# width: {slider_width}px;
# }}
# QSlider::handle:vertical {{
# height: {height}px;
# width: 20px;
# margin: 0px -20px 0px px;
# background-color: {slider_color};
# }}
#
# """.format(slider_width=INDICATOR_WIDTH,
#     height=HANDLE_HEIGHT,
#            slider_color=SLIDER_COLOR)



DISPLAY_VALUE =  """
QLabel {{ 
    color: {textcolor}; 
    font-size: {value_size}pt;
}}""".format(textcolor=TEXT_COLOR,
             value_size=VALUE_SIZE)

DISPLAY_VALUE_ALARM =  """
QLabel { 
    color: #ff0000; 
    font-size: 72pt; 
    font-weight: bold;
}"""

DISPLAY_NAME = """
QLabel {{ 
    color: {textcolor}; 
    font-size: {name_size}pt;
}}""".format(textcolor=TEXT_COLOR,
             name_size=NAME_SIZE)

DISPLAY_NAME_ALARM = """
QLabel {{ 
    color: #ff0000; 
    font-size: {name_size}pt;
}}""".format(name_size=NAME_SIZE)

DISPLAY_UNITS = """
QLabel {{ 
    color: {textcolor}; 
    font-size: {unit_size}pt;
}}""".format(textcolor=TEXT_COLOR,
             unit_size=UNIT_SIZE)

DISPLAY_UNITS_ALARM = f"""
QLabel {{ 
    color: #ff0000; 
    font-size: {UNIT_SIZE}pt;
}}"""

DISPLAY_WIDGET = """
border-bottom: 2px solid white;
"""

CONTROL_LABEL = f"""
QLabel {{
    font-size: 12px;
    color: {BACKGROUND_COLOR};
}}
"""

CONTROL_VALUE =  f"""
QLabel {{ 
    color: {BACKGROUND_COLOR}; 
    font-size: {VALUE_SIZE}pt;
}}
QLineEdit {{ 
    color: {TEXT_COLOR}; 
    font-size: {VALUE_SIZE}pt;
}}

"""

CONTROL_BOX = f"""
QGroupBox {{
    background-color: {TEXT_COLOR};
    border: 1px solid #000000;
    border-radius: 4px;
    margin-top: 20px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top left;
  left: 3px;
  top: -5px;
}}
"""

CONTROL_NAME = f"""
QLabel {{ 
    color: {BACKGROUND_COLOR}; 
    font-size: {NAME_SIZE}pt;
}}"""

CONTROL_UNITS = f"""
QLabel {{ 
    color: {BACKGROUND_COLOR}; 
    font-size: {UNIT_SIZE}pt;
}}"""

TITLE_STYLE = """
font-size: 32pt;
color: {text_color};
text-align: left;
""".format(text_color=TEXT_COLOR)



STATUS_NORMAL = f"""
QFrame {{
    background-color: {BACKGROUND_COLOR};
    color: {TEXT_COLOR};
}}
"""

STATUS_WARN = f"""
QFrame {{
    background-color: {SUBWAY_COLORS['orange']};
    color: {TEXT_COLOR};
}}
"""

STATUS_ALARM = f"""
QFrame {{
    background-color: {SUBWAY_COLORS['red']};
    color: {TEXT_COLOR};
}}
"""

HEARTBEAT_NORMAL = f"""
QRadioButton::indicator {{
    background: qradialgradient(cx:0, cy:0, radius:1, fx:0.5, fy:0.5, stop:0 white, stop:1 {SUBWAY_COLORS['blue']});
    border-radius: 5px;
}}

QLabel {{
    color: {TEXT_COLOR};
}}
"""

HEARTBEAT_ALARM = f"""
QRadioButton::indicator {{
    background: qradialgradient(cx:0, cy:0, radius:1, fx:0.5, fy:0.5, stop:0 white, stop:1 {SUBWAY_COLORS['red']});
    border-radius: 5px;
}}

QLabel {{
    color: {SUBWAY_COLORS['red']};
}}
"""

STATUS_BOX = f"""
QWidget {{
    background-color: {BACKGROUND_COLOR};
}}
"""

DARK_THEME =  f"""
/*
adapted from https://github.com/gmarull/qtmodern/blob/master/qtmodern/resources/style.qss
*/

/*
 * QGroupBox
 */


QGroupBox {{
  background-color: palette(alternate-base);
  border: 1px solid palette(midlight);
  margin-top: 25px;
}}

QGroupBox::title {{
    background-color: transparent;
}}

QGroupBox#CONTROLBOX {{
    background-color: {CONTROL_BACKGROUND};
}}

/*
 * QToolBar
 */

QToolBar {{
  border: none;
}}

/*
 * QTabBar
 */

QTabBar{{
  background-color: transparent;
}}

QTabBar::tab{{
  padding: 4px 6px;
  background-color: transparent;
  border-bottom: 2px solid transparent;
}}

QTabBar::tab:selected, QTabBar::tab:hover {{
  color: palette(text);
  border-bottom: 2px solid palette(highlight);
}}

QTabBar::tab:selected:disabled {{
  border-bottom: 2px solid palette(light);
}}

/*
 * QScrollBar
 */

QScrollBar:vertical {{
  background: palette(base);
  border-top-right-radius: 2px;
  border-bottom-right-radius: 2px;
  width: 16px;
  margin: 0px;
}}

QScrollBar::handle:vertical {{
  background-color: palette(alternate-base);
  border-radius: 2px;
  min-height: 20px;
  margin: 2px 4px 2px 4px;
}}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover, QScrollBar::handle:vertical:pressed, QScrollBar::handle:horizontal:pressed {{
  background-color:palette(midlight);
}}

QScrollBar::add-line:vertical {{
  background: none;
  height: 0px;
  subcontrol-position: right;
  subcontrol-origin: margin;
}}

QScrollBar::sub-line:vertical {{
  background: none;
  height: 0px;
  subcontrol-position: left;
  subcontrol-origin: margin;
}}

QScrollBar:horizontal{{
  background: palette(base);
  height: 16px;
  margin: 0px;
}}

QScrollBar::handle:horizontal {{
  background-color: palette(alternate-base);
  border-radius: 2px;
  min-width: 20px;
  margin: 4px 2px 4px 2px;
}}


QScrollBar::add-line:horizontal {{
  background: none;
  width: 0px;
  subcontrol-position: bottom;
  subcontrol-origin: margin;
}}

QScrollBar::sub-line:horizontal {{
  background: none;
  width: 0px;
  subcontrol-position: top;
  subcontrol-origin: margin;
}}

/*
 * QScrollArea
 */

QScrollArea {{
  border-style: none;
}}

QScrollArea > QWidget > QWidget {{
  background-color: palette(alternate-base);
}}

/*
 * QSlider
 */

QSlider::handle:horizontal {{
  border-radius: 5px;
  background-color: palette(light);
  max-height: 20px;
}}

QSlider::add-page:horizontal {{
  background: palette(base);
}}

QSlider::sub-page:horizontal {{
  background: palette(highlight);
}}

QSlider::sub-page:horizontal:disabled {{
  background-color: palette(light);
}}

QTableView {{
  background-color: palette(link-visited);
  alternate-background-color: palette(midlight);
}}

QWidget {{
    font-size: 20pt;
}}"""


def set_dark_palette(app):
    """ Apply Dark Theme to the Qt application instance.

    borrowed from https://github.com/gmarull/qtmodern/blob/master/qtmodern/styles.py
        Args:
            app (QApplication): QApplication instance.
    """

    darkPalette = QtGui.QPalette()

    # base
    darkPalette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(TEXT_COLOR))
    darkPalette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    darkPalette.setColor(QtGui.QPalette.Light, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.Midlight, QtGui.QColor(90, 90, 90))
    darkPalette.setColor(QtGui.QPalette.Dark, QtGui.QColor(35, 35, 35))
    darkPalette.setColor(QtGui.QPalette.Text, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.Base, QtGui.QColor(42, 42, 42))
    darkPalette.setColor(QtGui.QPalette.Window, QtGui.QColor(BACKGROUND_COLOR))
    darkPalette.setColor(QtGui.QPalette.Shadow, QtGui.QColor(20, 20, 20))
    darkPalette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    darkPalette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.Link, QtGui.QColor(56, 252, 196))
    darkPalette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(BOX_BACKGROUND))
    darkPalette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(53, 53, 53))
    darkPalette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(180, 180, 180))
    darkPalette.setColor(QtGui.QPalette.LinkVisited, QtGui.QColor(80, 80, 80))

    # disabled
    darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText,
                         QtGui.QColor(127, 127, 127))
    darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text,
                         QtGui.QColor(127, 127, 127))
    darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText,
                         QtGui.QColor(127, 127, 127))
    darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight,
                         QtGui.QColor(80, 80, 80))
    darkPalette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.HighlightedText,
                         QtGui.QColor(127, 127, 127))

    app.setPalette(darkPalette)

    return app