from PySide2 import QtGui
from vent.alarm import AlarmSeverity

SUBWAY_COLORS = {
    'blue': "#0039A6",
    'ltblue': "#00A1DE",
    'lime': "#6CBE45",
    'gray': "A7A9AC",
    'orange': "#FF6319",
    'orange_darker': "#CC4E14",
    'yellow': "#FCCC0A",
    'yellow_darker': "#CCA408",
    'red': "#EE352E",
    'red_darker': "#B72722",
    'green': "#00933C",
    'purple': "#B933AD"
}

BACKGROUND_COLOR = "#111111"
BOX_BACKGROUND = "#333333"
TEXT_COLOR = "#EEEEEE"
BORDER_COLOR = "palette(midlight)"
BOX_BORDERS = f"2px solid palette(midlight);"
BOX_BORDERS_LOCKED = f"3px solid {SUBWAY_COLORS['lime']}"
BOX_BORDERS_UNLOCKED = f"3px solid {SUBWAY_COLORS['red']}"
BOX_MARGINS = 4
GRAY_TEXT = BOX_BACKGROUND

CONTROL_BACKGROUND = "#DDDDDD"
CONTROL_BACKGROUND_LOCKED = "#DDDDDD"
CONTROL_SUBBOX_BACKGROUND = "#FFFFFF"
CONTROL_SUBBOX_BACKGROUND_LOCKED = "#DDDDDD"
CONTROL_TEXT = BACKGROUND_COLOR
CONTROL_TEXT_SECONDARY = "#333333"
CONTROL_TEXT_SECONDARY_SIZE = 10
CONTROL_SENSOR_BACKGROUND = "#CCCCCC"
CONTROL_SENSOR_BAR_WIDTH = 50
HANDLE_HEIGHT = 10
SLIDER_WIDTH = 80
SLIDER_HEIGHT = 20 #50
INDICATOR_WIDTH = SLIDER_WIDTH/3
SLIDER_COLOR = TEXT_COLOR
INDICATOR_COLOR = SUBWAY_COLORS['blue']
ALARM_COLOR = "#FF0000"

TOGGLE_MAX_WIDTH = 50

DIVIDER_COLOR = "#FFFFFF"
DIVIDER_COLOR_DARK = BOX_BACKGROUND

VALUE_SIZE = 72 #30
VALUE_MINOR_SIZE = 40
NAME_SIZE = 36 #10
UNIT_SIZE = 18
TICK_SIZE = 12

CARD_TITLE_SIZE = 24
CARD_TIMESTAMP_SIZE = 12

ALARM_BAR_HEIGHT = 100
MIDLINE_MARGIN = 30
START_BUTTON_HEIGHT=80
BUTTON_MAX_HEIGHT = 100

LEFT_COLUMN_MAX_WIDTH = 400

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

MONITOR_BOX = f"""
QGroupBox {{
    margin-top: {MIDLINE_MARGIN}px;
    border-top-right-radius: 5px;
    
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top left;
  color: {TEXT_COLOR};
  left: 3px;
  top: 5px;
}}
"""

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


PRESSURE_PLOT_BOX = f"""
QGroupBox {{
    background-color: {CONTROL_BACKGROUND};
    border: 0px solid #000000;
    border-left: {BOX_BORDERS};
    border-top: {BOX_BORDERS};
    border-bottom: {BOX_BORDERS};
    margin-left: {BOX_MARGINS}px;
    margin-bottom: {BOX_MARGINS}px;

    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
    margin-top: {MIDLINE_MARGIN}px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top left;
  color: {TEXT_COLOR};
  left: 3px;
  top: 5px;
}}
"""

PRESSURE_PLOT_BOX_LOCKED = f"""
QGroupBox {{
    background-color: {CONTROL_BACKGROUND_LOCKED};
    border: 0px solid #000000;
    border-left: {BOX_BORDERS_LOCKED};
    border-top: {BOX_BORDERS_LOCKED};
    border-bottom: {BOX_BORDERS_LOCKED};
    margin-left: {BOX_MARGINS}px;
    margin-bottom: {BOX_MARGINS}px;

    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
    margin-top: {MIDLINE_MARGIN}px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top left;
  color: {TEXT_COLOR};
  left: 3px;
  top: 5px;
}}
"""

PRESSURE_PLOT_BOX_UNLOCKED = f"""
QGroupBox {{
    background-color: {CONTROL_BACKGROUND};
    border: 0px solid #000000;
    border-left: {BOX_BORDERS_UNLOCKED};
    border-top: {BOX_BORDERS_UNLOCKED};
    border-bottom: {BOX_BORDERS_UNLOCKED};
    margin-left: {BOX_MARGINS}px;
    margin-bottom: {BOX_MARGINS}px;

    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
    margin-top: {MIDLINE_MARGIN}px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top left;
  color: {TEXT_COLOR};
  left: 3px;
  top: 5px;
}}
"""

PLOT_BOX = f"""
QGroupBox {{
    background-color: {BOX_BACKGROUND};
    border: 0px solid #000000;
    border-right: 1px solid {BORDER_COLOR};
    border-top: 1px solid {BORDER_COLOR};
    border-bottom: 1px solid {BORDER_COLOR};
    margin-right: {BOX_MARGINS}px;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top left;
  color: {TEXT_COLOR};
  left: 3px;
  top: 3px;
}}
"""

MONITOR_PLOT = f"""
QWidget {{
    margin-right: {BOX_MARGINS}px;
}}
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

CONTROL_VALUE_REC = f"""
QLabel {{ 
    color: {SUBWAY_COLORS['red']}; 
    font-size: {VALUE_SIZE}pt;
}}
QLineEdit {{ 
    color: {TEXT_COLOR}; 
    font-size: {VALUE_SIZE}pt;
}}

"""

CONTROL_SENSOR_LABEL = f"""
QLabel {{
    color: {GRAY_TEXT};
    font-size: {VALUE_MINOR_SIZE}pt;
    background-color: {CONTROL_SENSOR_BACKGROUND};
}}
"""

CONTROL_SENSOR_FRAME = f"""
QFrame {{
    background-color: {CONTROL_SENSOR_BACKGROUND};
    border-radius: 10px;
    border-color: palette(midlight);
    border-style: outset;
    border-width: 1px;
}}

QFrame QWidget {{
    border-radius: 0px;
    border-color: palette(midlight);
    border-style: outset;
    border-width: 0px;
}}
"""


CONTROL_BOX = f"""
QGroupBox {{
    background-color: {CONTROL_BACKGROUND};
    border: 0px solid #000000;
    border-top: {BOX_BORDERS};
    border-right: {BOX_BORDERS};
    border-bottom: {BOX_BORDERS};
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    border-bottom-left-radius: 5px;
    margin-top: {MIDLINE_MARGIN}px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top right;
  color: {TEXT_COLOR};
  right: 7px;
  top: 5px;
}}
"""

CONTROL_BOX_LOCKED = f"""
QGroupBox {{
    background-color: {CONTROL_BACKGROUND_LOCKED};
    border: 0px solid {SUBWAY_COLORS['lime']};
    border-top: {BOX_BORDERS_LOCKED};
    border-right: {BOX_BORDERS_LOCKED};
    border-bottom: {BOX_BORDERS_LOCKED};
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    border-bottom-left-radius: 5px;
    margin-top: {MIDLINE_MARGIN}px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top right;
  color: {TEXT_COLOR};
  right: 7px;
  top: 5px;
}}
"""

CONTROL_BOX_UNLOCKED = f"""
QGroupBox {{
    background-color: {CONTROL_BACKGROUND};
    border: 0px solid {SUBWAY_COLORS['red']};
    border-top: {BOX_BORDERS_UNLOCKED};
    border-right: {BOX_BORDERS_UNLOCKED};
    border-bottom: {BOX_BORDERS_UNLOCKED};
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    border-bottom-left-radius: 5px;
    margin-top: {MIDLINE_MARGIN}px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top right;
  color: {TEXT_COLOR};
  right: 7px;
  top: 5px;
}}
"""

CONTROL_SUBBOX = f"""
QGroupBox {{
    background-color: {CONTROL_SUBBOX_BACKGROUND};
    border: 0px solid #000000;
    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
    border-top-right-radius: 0px;
    border-bottom-right-radius: 0px;
    margin-left: 5px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top right;
  right: 5px;
  top: 5px;
  color: {CONTROL_TEXT};
}}

QRadioButton {{
    color: {CONTROL_TEXT_SECONDARY};
    font-size: {CONTROL_TEXT_SECONDARY_SIZE}
}}

QLabel {{
    color: {CONTROL_TEXT_SECONDARY};
}}
"""

CONTROL_SUBBOX_LOCKED = f"""
QGroupBox {{
    background-color: {CONTROL_SUBBOX_BACKGROUND_LOCKED};
    border: 0px solid #000000;
    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
    border-top-right-radius: 0px;
    border-bottom-right-radius: 0px;
    margin-left: 5px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top right;
  right: 5px;
  top: 5px;
  color: {CONTROL_TEXT};
}}

QRadioButton {{
    color: {CONTROL_TEXT_SECONDARY};
    font-size: {CONTROL_TEXT_SECONDARY_SIZE}
}}

QLabel {{
    color: {CONTROL_TEXT_SECONDARY};
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

CONTROL_NAME_REC = f"""
QLabel {{ 
    color: {SUBWAY_COLORS['red']}; 
    font-size: {NAME_SIZE}pt;
}}"""

CONTROL_UNITS_REC = f"""
QLabel {{ 
    color: {SUBWAY_COLORS['red']}; 
    font-size: {UNIT_SIZE}pt;
}}"""

CONTROL_CYCLE_BOX = f"""
QGroupBox {{
    color: {BACKGROUND_COLOR};
}}

QGroupBox QRadioButton {{
    color: {BACKGROUND_COLOR};
}}

QRadioButton::indicator {{
    width:                  10px;
    height:                 10px;
    border-radius:          7px;
}}

QRadioButton::indicator:checked {{
    background-color:       black;
    border:                 2px solid black;
}}

QRadioButton::indicator:unchecked {{
    background-color:       white;
    border:                 2px solid black;
}}
"""

PLOT_TITLE_STYLE = """
font-size: 16pt;
color: {text_color};
justify: left;
""".format(text_color=TEXT_COLOR)

PRESSURE_PLOT_TITLE_STYLE = f"""
font-size: 16pt;
color: {GRAY_TEXT};
justify: left;
"""



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

ALARM_CARD_LOW = f"""
QFrame {{
    border: 3px solid {SUBWAY_COLORS['yellow_darker']};
    border-radius: 4px;
    background-color: {SUBWAY_COLORS['yellow']};
}}

QFrame > QLabel {{
    border: 0px;
    border-radius: 0px;
    color: {BACKGROUND_COLOR};
}}
"""

ALARM_CARD_MEDIUM = f"""
QFrame {{
    border: 3px solid {SUBWAY_COLORS['orange_darker']};
    border-radius: 4px;
    background-color: {SUBWAY_COLORS['orange']};
}}

QFrame > QLabel {{
    border: 0px;
    border-radius: 0px;
    color: {BACKGROUND_COLOR};
}}
"""

ALARM_CARD_HIGH = f"""
QFrame {{
    border: 3px solid {SUBWAY_COLORS['red_darker']};
    border-radius: 4px;
    background-color: {SUBWAY_COLORS['red']};
}}

QFrame > QLabel {{
    border: 0px;
    border-radius: 0px;
    color: {TEXT_COLOR};
}}
"""

ALARM_CARD_TITLE = f"""
QLabel {{
    font-size: {CARD_TITLE_SIZE}pt;
    font-weight: bold;
}}
"""

ALARM_CARD_TIMESTAMP = f"""
QLabel {{
    font-size: {CARD_TIMESTAMP_SIZE}pt;
}}
"""

ALARM_CARD_BUTTON = f"""
QPushButton {{
    font-size: 42pt;
    color: {TEXT_COLOR};
}}
"""

ALARM_CARD_BUTTON_INACTIVE = f"""
QPushButton {{
    font-size: 42pt;
    color: {GRAY_TEXT};
}}
"""

ALARM_CARD_STYLES = {
    AlarmSeverity.LOW: ALARM_CARD_LOW,
    AlarmSeverity.MEDIUM: ALARM_CARD_MEDIUM,
    AlarmSeverity.HIGH: ALARM_CARD_HIGH
}

HEARTBEAT_NORMAL = f"""
QRadioButton::indicator {{
    background: qradialgradient(cx:0, cy:0, radius:1, fx:0.5, fy:0.5, stop:0 white, stop:1 {SUBWAY_COLORS['green']});
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

HEARTBEAT_OFF = f"""
QRadioButton::indicator {{
    background: qradialgradient(cx:0, cy:0, radius:1, fx:0.5, fy:0.5, stop:0 white, stop:1 #DDDDDD);
    border-radius: 5px;
}}

QLabel {{
    color: {TEXT_COLOR};
}}
"""

CONTROL_PANEL = f"""
QGroupBox {{
    background-color: {BACKGROUND_COLOR};
    border-radius: 5px;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top left;
  color: {TEXT_COLOR};
  left: 3px;
  top: 2px;
}}
"""

START_BUTTON_OFF = f"""
QToolButton {{
    font-size: 48px;
    font-style: bold;
    color: {TEXT_COLOR};
    text-align: center center;
}}
"""

START_BUTTON_ON = f"""
QToolButton {{
font-size: 48px;
    font-style: bold;
    color: {TEXT_COLOR};
}}
"""

START_BUTTON_ALARM = f"""
QToolButton {{
font-size: 48px;
    font-style: bold;
    color: {SUBWAY_COLORS['red']};
}}
"""

TOGGLE_BUTTON = f"""
QPushButton:checked {{
    color: {SUBWAY_COLORS['lime']}
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
    darkPalette.setColor(QtGui.QPalette.Button, QtGui.QColor(50, 50, 50))
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

    # active
    # darkPalette.setColor(QtGui.QPalette.Highlight, QtGui.QPalette.Button,
    #                      QtGui.QColor(BOX_BACKGROUND))
    # darkPalette.setColor(QtGui.QPalette.Active, QtGui.QPalette.ButtonText,
    #                      QtGui.QColor(SUBWAY_COLORS['green']))

    app.setPalette(darkPalette)

    return app